import asyncio
import json
import os
import random
import requests
from telethon import TelegramClient, events
from telethon.errors import (SessionPasswordNeededError, PhoneCodeInvalidError, 
                              AuthKeyUnregisteredError, FloodWaitError, 
                              InviteHashExpiredError, UserAlreadyParticipantError)
from telethon.sessions import StringSession
from telethon.tl.functions.messages import ImportChatInviteRequest
from telethon.tl.functions.channels import JoinChannelRequest
from telethon.tl.types import MessageEntityMentionName
import sys
from datetime import datetime
import time
import re

# Konfigurasi
CONFIG_FILE = 'userbot_config.json'
API_ID = None
API_HASH = None

class GameFiConversationEngine:
    """Engine percakapan GameFi 2025 dengan data REAL dan nyambung"""
    
    # Data REAL GameFi 2025 berdasarkan riset
    GAMEFI_REAL_DATA = {
        "top_games_2025": [
            "Axie Infinity", "Illuvium", "Big Time", "Off The Grid", "Pixels",
            "The Sandbox", "Star Atlas", "Gods Unchained", "Gala Games",
            "Heroes of Mavia", "Guild of Guardians", "Artyfact", "Splinterlands",
            "Ragnarok Monster World", "Alien Worlds", "DeFi Kingdoms",
            "Champions Ascension", "Wild Forest", "Apeiron"
        ],
        "top_blockchains_2025": [
            "Ronin", "Polygon", "Immutable X", "Immutable zkEVM", "Arbitrum Nova",
            "Solana", "BNB Chain", "Avalanche", "Ethereum Layer-2", "Beam",
            "Sui", "Flow", "WAX", "GalaChain"
        ],
        "hot_tokens_2025": [
            "AXS", "RON", "IMX", "ILV", "BIGTIME", "SAND", "MANA", "GALA",
            "PIXEL", "MAVIA", "ATLAS", "POLIS", "GODS", "BEAM", "ARTY",
            "SLP", "PRIME", "MAGIC", "POL"
        ],
        "nft_categories": [
            "land NFT", "character NFT", "Axie NFT", "Illuvial NFT",
            "weapon NFT", "pet NFT", "skin NFT", "equipment NFT",
            "LAND parcel", "collectible NFT", "badge NFT"
        ]
    }
    
    # Real trends & issues 2025
    REAL_TRENDS_2025 = [
        "93% GameFi games udah mati guys, cuma yang solid aja survive",
        "Ronin migration Pixels NFT bikin floor price naik 40%",
        "Immutable zkEVM sekarang gas-free buat Passport holders",
        "Axie Infinity Land Quests Q3 bakal route fees ke AXS stakers",
        "Big Time esports push + modder tools tahun ini gokil",
        "Illuvium mobile release + Leviathan raids coming soon",
        "Polygon AggLayer 2025 unify chains buat cross-game liquidity",
        "Ronin zkEVM L2 chains pake Polygon CDK udah live Q1",
        "Beam validator nodes + staking functionality launching soon",
        "Star Atlas ATLAS token earning mechanics improved banget",
        "Gala Games 13 live games + 5 coming soon ambitious",
        "Heroes of Mavia 2.6 juta active users di Ronin",
        "Artyfact AI-powered gaming + NFT revenue sharing model unik",
        "Off The Grid free-to-play shooter model breaking records",
        "Gods Unchained weekly tournament prize pool naik 50%"
    ]
    
    # Real discussion topics
    REAL_DISCUSSIONS = [
        # Market & Economics
        "floor price {game} {direction} {percent}% minggu ini",
        "ROI {game} masih worth it ga di 2025 kondisi market gini",
        "whales accumulate {token} volume naik {percent}%",
        "gas fee {blockchain} sekarang cuma ${amount}, murah banget",
        "tokenomics {token} sustainable ga sih long term",
        
        # Gameplay Real Issues
        "meta {game} berubah total after latest patch",
        "grinding {game} daily quest masih worth time ga",
        "scholarship rate {game} turun jadi {percent}%",
        "bot trading marketplace {game} makin ganggu",
        "server lag {game} parah sejak update kemarin",
        
        # Real Partnerships & Updates  
        "{game} partnership dengan {brand} baru diannounce",
        "{blockchain} integrate {game} migration completed",
        "{game} airdrop buat {token} stakers confirmed",
        "update: {game} Season Pass rewards buffed",
        "{game} mobile version launching {timeframe}",
        
        # Strategy & Tips
        "strategy farming {token} paling efisien 2025",
        "build terbaik PvP {game} after meta shift",
        "timing terbaik flip {nft} based on market cycle",
        "guild war {game} tactics yang lagi dominan",
        "breed vs buy {game} creatures mana profitable",
        
        # Community Drama
        "drama komunitas {game} soal tokenomics change",
        "developer {game} jarang update bikin frustasi",
        "turnamen {game} controversy prize distribution",
        "scholarship {game} rate cut backlash parah"
    ]
    
    # Response patterns dengan nama untuk REPLY
    REPLY_PATTERNS = {
        "agree_with_name": [
            "nah {name} bener banget tuh",
            "exactly {name}, gue setuju 100%",
            "{name} on point dah, apalagi {context}",
            "betul kata {name}, {additional_point}",
            "iya {name}, pengalaman gue juga sama",
            "{name} ga salah, {supporting_fact}"
        ],
        "disagree_with_name": [
            "hmm {name}, kurang setuju sih karena {reason}",
            "{name}, debatable menurutku soalnya {counterpoint}",
            "wait {name}, tapi {contradiction} kan?",
            "{name}, agak skeptis gue {reason}",
            "beda perspektif nih {name}, gue rasa {opinion}"
        ],
        "ask_name": [
            "{name}, emang {detail} gimana pengalaman lu?",
            "nanya ke {name} nih, lu udah coba {action} belom?",
            "{name}, serius? terus {followup}?",
            "{name}, maksudnya {clarification}?",
            "menarik point {name}, kalau {scenario} gimana?"
        ],
        "add_info_to_discussion": [
            "tambahin dikit, based on riset {info}",
            "btw yang belom tau, {fact}",
            "oh iya, ada update: {news}",
            "fun fact soal {topic}: {trivia}",
            "FYI guys, {important_info}"
        ]
    }
    
    @staticmethod
    def fill_real_data(template):
        """Fill template dengan data REAL 2025"""
        text = template
        
        data = GameFiConversationEngine.GAMEFI_REAL_DATA
        
        replacements = {
            "{game}": random.choice(data["top_games_2025"]),
            "{blockchain}": random.choice(data["top_blockchains_2025"]),
            "{token}": random.choice(data["hot_tokens_2025"]),
            "{nft}": random.choice(data["nft_categories"]),
            "{direction}": random.choice(["pump", "naik", "dump", "turun"]),
            "{percent}": random.randint(10, 80),
            "{amount}": random.choice(["0.0001", "0.001", "0.01"]),
            "{brand}": random.choice(["Ubisoft", "Epic Games", "Samsung", "Sony"]),
            "{timeframe}": random.choice(["Q2", "Q3", "next month", "soon"]),
        }
        
        for key, value in replacements.items():
            text = text.replace(key, str(value))
        
        return text
    
    @staticmethod
    def get_starter_message():
        """Generate starter message dengan data REAL"""
        # 30% chance ambil dari real trends
        if random.random() < 0.3:
            return random.choice(GameFiConversationEngine.REAL_TRENDS_2025)
        
        # 70% generate dari discussion topics
        discussion = random.choice(GameFiConversationEngine.REAL_DISCUSSIONS)
        return GameFiConversationEngine.fill_real_data(discussion)
    
    @staticmethod
    def build_contextual_prompt(conversation_history, replying_to=None):
        """Build prompt dengan konteks penuh + info siapa yang direply"""
        
        # Ambil context messages (max 5 terakhir)
        recent = conversation_history[-5:] if len(conversation_history) > 5 else conversation_history
        
        context_text = "PERCAKAPAN SEBELUMNYA:\n"
        for msg in recent:
            context_text += f"{msg['speaker']}: {msg['message']}\n"
        
        # Info siapa yang direply
        reply_context = ""
        if replying_to:
            reply_context = f"\nKAMU LAGI REPLY KE: {replying_to['name']}\nPESAN NYA: {replying_to['message']}\n"
        
        # Determine conversation phase
        if len(conversation_history) < 3:
            phase = "awal percakapan - engage dengan antusias"
        elif len(conversation_history) < 8:
            phase = "tengah percakapan - maintain topik dan develop diskusi"
        else:
            phase = "percakapan udah panjang - bisa conclude atau introduce subtopik baru"
        
        return context_text, reply_context, phase
    
    @staticmethod
    def create_reply_prompt(context_text, reply_context, phase, response_type, reply_to_name):
        """Create prompt untuk reply yang BENAR-BENAR nyambung"""
        
        base_rules = """ATURAN WAJIB:
1. Kamu HANYA bahas GameFi 2025: NFT gaming, blockchain games, P2E, tokenomics
2. Pakai data REAL: Axie, Illuvium, Big Time, Ronin, Immutable, dll (2025 actual projects)
3. Bahasa: Indonesia gaul natural + typo ok, singkatan ok
4. WAJIB nyambung dengan pesan yang lu reply
5. Panjang: 1-2 kalimat (max 120 karakter)
6. Emoji: 0-1 aja, jangan lebay

"""
        
        response_guides = {
            "agree": f"Setuju dengan {reply_to_name}, tambahin insight atau data supporting",
            "disagree": f"Kasih perspektif beda dengan {reply_to_name} tapi respectful + alasan",
            "question": f"Tanya hal spesifik ke {reply_to_name} yang relevant ke topik",
            "add_info": f"Tambahin informasi baru yang relate ke poin {reply_to_name}",
            "personal_exp": f"Share pengalaman pribadi yang relate ke topik {reply_to_name}"
        }
        
        prompt = f"""{base_rules}

{context_text}
{reply_context}

FASE: {phase}
RESPONSE TYPE: {response_type} - {response_guides[response_type]}

DATA GAMEFI 2025 VALID:
- Games: Axie, Illuvium, Big Time, Pixels, Heroes of Mavia, Artyfact
- Chains: Ronin, Polygon, Immutable X, Arbitrum Nova, Beam, Sui  
- Tokens: AXS, RON, IMX, ILV, BIGTIME, PIXEL, MAVIA
- Real issues: 93% GameFi dead, Ronin zkEVM, Immutable gas-free

TUGAS: Reply pesan {reply_to_name} dengan natural, nyambung 100%, tema GameFi 2025.

CONTOH GOOD REPLIES:
- "{reply_to_name} bener, apalagi sejak Ronin integrate Pixels floor naik 40%"
- "wait {reply_to_name}, ROI Axie Land Quest masih worth kalau stake AXS"
- "setuju {reply_to_name}, Big Time modder tools bakal game changer"

RESPOND SEKARANG (nyambung + GameFi 2025 only):"""
        
        return prompt


class GroupManager:
    """Manager untuk handle grup list dan auto-join"""
    
    def __init__(self, config_file):
        self.config_file = config_file
        self.groups = []
        self.load_groups()
    
    def load_groups(self):
        """Load daftar grup dari config"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    data = json.load(f)
                    self.groups = data.get('groups', [])
            except:
                self.groups = []
    
    def save_groups(self):
        """Save daftar grup"""
        try:
            data = {}
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    data = json.load(f)
            
            data['groups'] = self.groups
            
            with open(self.config_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"✗ Error saving groups: {e}")
    
    def add_group(self, group_link, group_name=None):
        """Tambah grup ke list"""
        # Check if already exists
        if any(g['link'] == group_link for g in self.groups):
            print(f"✗ Grup {group_link} sudah ada dalam list!")
            return False
        
        self.groups.append({
            'link': group_link,
            'name': group_name or group_link,
            'added_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })
        self.save_groups()
        return True
    
    def remove_group(self, index):
        """Hapus grup dari list"""
        if 0 <= index < len(self.groups):
            removed = self.groups.pop(index)
            self.save_groups()
            return removed
        return None
    
    def get_groups(self):
        """Get semua grup"""
        return self.groups
    
    async def auto_join_groups(self, client, client_name):
        """Auto join semua grup dalam list"""
        joined = []
        already_in = []
        failed = []
        
        for group in self.groups:
            try:
                link = group['link'].strip()
                
                # Parse link
                if 'joinchat/' in link or '+' in link:
                    # Invite link
                    hash_match = re.search(r'joinchat/([a-zA-Z0-9_-]+)', link) or re.search(r'\+([a-zA-Z0-9_-]+)', link)
                    if hash_match:
                        hash_code = hash_match.group(1)
                        try:
                            await client(ImportChatInviteRequest(hash_code))
                            joined.append(group['name'])
                            await asyncio.sleep(random.uniform(2, 4))
                        except UserAlreadyParticipantError:
                            already_in.append(group['name'])
                        except InviteHashExpiredError:
                            failed.append(f"{group['name']} (link expired)")
                else:
                    # Username/ID
                    username = link.replace('@', '').replace('https://t.me/', '')
                    try:
                        await client(JoinChannelRequest(username))
                        joined.append(group['name'])
                        await asyncio.sleep(random.uniform(2, 4))
                    except UserAlreadyParticipantError:
                        already_in.append(group['name'])
                
            except FloodWaitError as e:
                print(f"⏳ FloodWait {e.seconds}s, waiting...")
                await asyncio.sleep(e.seconds)
            except Exception as e:
                failed.append(f"{group['name']} ({str(e)[:30]})")
        
        return {
            'joined': joined,
            'already_in': already_in,
            'failed': failed
        }


class UserbotManager:
    def __init__(self):
        self.userbots = []
        self.clients = {}
        self.running = False
        self.conversation_history = []
        self.session_id = self.generate_session_id()
        self.engine = GameFiConversationEngine()
        self.group_manager = GroupManager(CONFIG_FILE)
    
    def generate_session_id(self):
        """Generate unique session ID"""
        return f"gamefi_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{random.randint(1000, 9999)}"
    
    def load_config(self):
        """Load konfigurasi dari file"""
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r') as f:
                    data = json.load(f)
                    self.userbots = data.get('userbots', [])
                    print(f"✓ Berhasil load {len(self.userbots)} userbot")
            except Exception as e:
                print(f"✗ Error loading config: {e}")
                self.userbots = []
        else:
            self.userbots = []
    
    def save_config(self):
        """Save konfigurasi ke file"""
        try:
            data = {'userbots': self.userbots}
            if os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE, 'r') as f:
                    existing = json.load(f)
                    if 'groups' in existing:
                        data['groups'] = existing['groups']
            
            with open(CONFIG_FILE, 'w') as f:
                json.dump(data, f, indent=2)
            print("✓ Konfigurasi tersimpan")
        except Exception as e:
            print(f"✗ Error saving config: {e}")
    
    def remove_invalid_userbot(self, phone):
        """Hapus userbot yang invalid"""
        self.userbots = [u for u in self.userbots if u['phone'] != phone]
        self.save_config()
        print(f"✗ Userbot {phone} dihapus (session invalid)")
    
    async def add_userbot(self):
        """Tambah userbot baru"""
        print("\n=== TAMBAH USERBOT BARU ===")
        
        if not API_ID or not API_HASH:
            print("✗ API_ID dan API_HASH belum diset!")
            return
        
        phone = input("Nomor telepon (dengan kode negara, contoh: +6281234567890): ").strip()
        
        if any(u['phone'] == phone for u in self.userbots):
            print("✗ Nomor ini sudah terdaftar!")
            return
        
        try:
            client = TelegramClient(StringSession(), API_ID, API_HASH)
            await client.connect()
            
            if not await client.is_user_authorized():
                await client.send_code_request(phone)
                code = input("Masukkan kode verifikasi: ").strip()
                
                try:
                    await client.sign_in(phone, code)
                except SessionPasswordNeededError:
                    password = input("Masukkan password 2FA: ").strip()
                    await client.sign_in(password=password)
            
            me = await client.get_me()
            session_string = client.session.save()
            
            userbot_data = {
                'phone': phone,
                'session': session_string,
                'name': me.first_name,
                'username': me.username or "No username"
            }
            
            self.userbots.append(userbot_data)
            self.save_config()
            
            print(f"✓ Berhasil menambahkan: {me.first_name} (@{me.username})")
            
            await client.disconnect()
            
        except Exception as e:
            print(f"✗ Error: {e}")
    
    async def call_ai_api(self, text, prompt, session):
        """Call AI API dengan retry"""
        max_retries = 2
        
        for attempt in range(max_retries):
            try:
                url = f"https://api.ryzumi.vip/api/ai/deepseek?text={requests.utils.quote(text)}&prompt={requests.utils.quote(prompt)}&session={session}"
                response = requests.get(url, timeout=12)
                
                if response.status_code == 200:
                    data = response.json()
                    result = data.get('result', data.get('response', ''))
                    
                    if result and len(result) > 10 and len(result) < 200:
                        return result
                    
            except Exception as e:
                if attempt == max_retries - 1:
                    print(f"✗ API timeout/error")
        
        return None
    
    def get_fallback_response(self, reply_to_name, response_type, context):
        """Fallback response yang tetap nyambung"""
        
        fallbacks = {
            "agree": [
                f"setuju {reply_to_name}, apalagi kondisi market 2025",
                f"{reply_to_name} bener, based on data juga gitu",
                f"exactly {reply_to_name}, pengalaman gue sama"
            ],
            "disagree": [
                f"hmm {reply_to_name}, kurang sreg soalnya tokenomics risky",
                f"{reply_to_name}, skeptis gue karena 93% GameFi udah dead",
                f"beda view nih {reply_to_name}, prefer long term"
            ],
            "question": [
                f"{reply_to_name}, emang lu main di blockchain mana?",
                f"{reply_to_name}, ROI lu berapa di game itu?",
                f"{reply_to_name}, strategy lu gimana?"
            ],
            "add_info": [
                f"tambahin, Ronin zkEVM udah live Q1 ini",
                f"btw, Immutable sekarang gas-free loh",
                f"FYI, {random.choice(self.engine.GAMEFI_REAL_DATA['top_games_2025'])} baru update"
            ],
            "personal_exp": [
                f"pengalaman gue di {random.choice(self.engine.GAMEFI_REAL_DATA['top_games_2025'])} lumayan profitable",
                f"gue pernah flip NFT profit 2x minggu lalu",
                f"grinding daily masih worth kalau konsisten"
            ]
        }
        
        return random.choice(fallbacks.get(response_type, fallbacks["agree"]))
    
    async def send_with_typing(self, client, chat, message, reply_to=None):
        """Kirim pesan dengan typing animation dan reply"""
        try:
            # Realistic typing duration
            words = len(message.split())
            typing_duration = min(words * 0.25 * random.uniform(0.8, 1.2), 6)
            
            async with client.action(chat, 'typing'):
                await asyncio.sleep(typing_duration)
            
            # Send with or without reply
            await client.send_message(chat, message, reply_to=reply_to)
            return True
            
        except Exception as e:
            print(f"✗ Error sending: {e}")
            return False
    
    async def generate_natural_conversation(self, chat_id):
        """Generate percakapan yang BENAR-BENAR nyambung dengan reply"""
        
        bot_names = list(self.clients.keys())
        starter_name = random.choice(bot_names)
        starter_client = self.clients[starter_name]
        
        print(f"\n{'='*60}")
        print(f"🎬 PERCAKAPAN BARU - TEMA GAMEFI 2025")
        print(f"{'='*60}")
        print(f"💬 {starter_name} memulai topik...\n")
        
        # Starter message
        starter_message = self.engine.get_starter_message()
        
        self.conversation_history.append({
            'speaker': starter_name,
            'message': starter_message,
            'message_obj': None
        })
        
        print(f"📤 {starter_name}: {starter_message}")
        
        # Send starter
        sent = await self.send_with_typing(starter_client, chat_id, starter_message)
        if sent:
            # Save message object untuk reply nanti
            messages = await starter_client.get_messages(chat_id, limit=1)
            if messages:
                self.conversation_history[-1]['message_obj'] = messages[0]
        
        await asyncio.sleep(random.uniform(3, 7))
        
        # Conversation loop dengan REPLY
        num_messages = random.randint(10, 20)
        previous_speaker = starter_name
        
        for i in range(num_messages):
            # Pilih responder
            available = [n for n in bot_names if n != previous_speaker]
            if not available:
                available = bot_names
            
            # 20% chance sama bot reply lagi (natural)
            if random.random() < 0.2 and len(bot_names) > 2:
                responder_name = previous_speaker
            else:
                responder_name = random.choice(available)
            
            responder_client = self.clients[responder_name]
            
            # 70% chance untuk REPLY message sebelumnya (sisanya standalone)
            will_reply = random.random() < 0.7 and len(self.conversation_history) > 0
            
            reply_to_msg = None
            reply_to_info = None
            
            if will_reply:
                # Pilih message untuk direply (biasanya 1-2 terakhir)
                reply_target_idx = random.choice([-1, -2]) if len(self.conversation_history) > 1 else -1
                reply_target = self.conversation_history[reply_target_idx]
                
                reply_to_msg = reply_target.get('message_obj')
                reply_to_info = {
                    'name': reply_target['speaker'],
                    'message': reply_target['message']
                }
            
            # Build context
            context_text, reply_context, phase = self.engine.build_contextual_prompt(
                self.conversation_history, 
                reply_to_info
            )
            
            # Determine response type
            response_types = ["agree", "question", "add_info", "personal_exp", "disagree"]
            weights = [0.30, 0.25, 0.20, 0.15, 0.10]
            response_type = random.choices(response_types, weights=weights)[0]
            
            # Create prompt
            reply_name = reply_to_info['name'] if reply_to_info else "someone"
            prompt = self.engine.create_reply_prompt(
                context_text, reply_context, phase, response_type, reply_name
            )
            
            # Get last message
            last_msg = self.conversation_history[-1]['message']
            
            # Call AI
            ai_response = await self.call_ai_api(last_msg, prompt, self.session_id)
            
            # Fallback if needed
            if not ai_response or len(ai_response) < 10:
                response_message = self.get_fallback_response(reply_name, response_type, context_text)
            else:
                response_message = ai_response
            
            # Indicator reply
            reply_indicator = f"↩️ @{reply_name}" if will_reply else ""
            
            # Save to history
            self.conversation_history.append({
                'speaker': responder_name,
                'message': response_message,
                'message_obj': None
            })
            
            print(f"📤 {responder_name} {reply_indicator}: {response_message}")
            
            # Send dengan reply
            sent = await self.send_with_typing(
                responder_client, 
                chat_id, 
                response_message, 
                reply_to=reply_to_msg
            )
            
            if sent:
                # Save message object
                messages = await responder_client.get_messages(chat_id, limit=1)
                if messages:
                    self.conversation_history[-1]['message_obj'] = messages[0]
            
            previous_speaker = responder_name
            
            # Natural delay
            delay_patterns = {
                'instant': (0.5, 2),
                'quick': (2, 6),
                'thinking': (6, 12),
                'slow': (12, 25)
            }
            
            pattern = random.choices(
                list(delay_patterns.keys()),
                weights=[0.15, 0.45, 0.30, 0.10]
            )[0]
            
            delay = random.uniform(*delay_patterns[pattern])
            await asyncio.sleep(delay)
        
        print(f"\n{'='*60}")
        print(f"✅ Percakapan selesai ({num_messages} pesan, {sum(1 for h in self.conversation_history[-num_messages:] if h.get('message_obj'))} dengan reply)")
        print(f"{'='*60}\n")
    
    async def run_continuous_conversation(self, chat_id):
        """Run percakapan terus menerus dengan break natural"""
        
        conversation_count = 0
        
        try:
            while self.running:
                conversation_count += 1
                
                print(f"\n🔥 SESI PERCAKAPAN #{conversation_count}")
                
                # Generate conversation
                await self.generate_natural_conversation(chat_id)
                
                # Break time antara percakapan
                break_patterns = {
                    'short': (40, 90),       # Break pendek
                    'medium': (90, 180),     # Break sedang
                    'long': (180, 400),      # Break lama
                    'very_long': (400, 700)  # Break sangat lama
                }
                
                pattern = random.choices(
                    list(break_patterns.keys()),
                    weights=[0.30, 0.40, 0.25, 0.05]
                )[0]
                
                break_time = random.uniform(*break_patterns[pattern])
                
                print(f"⏸️  Break {int(break_time)}s ({int(break_time/60)} menit) sebelum sesi berikutnya...")
                print(f"💤 Biarkan chat natural dulu\n")
                
                await asyncio.sleep(break_time)
                
                # Session reset untuk variasi (15% chance)
                if random.random() < 0.15:
                    old_session = self.session_id
                    self.session_id = self.generate_session_id()
                    print(f"🔄 Session direset untuk variasi AI response")
                    print(f"   {old_session[:25]}... → {self.session_id[:25]}...\n")
                
                # Keep history manageable (last 15 messages)
                if len(self.conversation_history) > 15:
                    self.conversation_history = self.conversation_history[-15:]
                
        except KeyboardInterrupt:
            print("\n\n⏹️  Dihentikan oleh user")
        except Exception as e:
            print(f"\n✗ Error dalam conversation loop: {e}")
            import traceback
            traceback.print_exc()
        finally:
            self.running = False
    
    async def start_all_userbots(self):
        """Start semua userbot dengan auto-join"""
        if len(self.userbots) < 2:
            print("✗ Minimal butuh 2 userbot untuk percakapan!")
            return
        
        # Show available groups
        groups = self.group_manager.get_groups()
        if not groups:
            print("✗ Belum ada grup yang ditambahkan!")
            print("   Silakan tambah grup dulu di menu 'Kelola Grup'")
            return
        
        print(f"\n{'='*60}")
        print("📋 DAFTAR GRUP TERSEDIA")
        print(f"{'='*60}")
        for idx, group in enumerate(groups, 1):
            print(f"{idx}. {group['name']}")
            print(f"   Link: {group['link']}")
            print(f"   Added: {group['added_at']}\n")
        
        choice = input("Pilih nomor grup target (atau 0 untuk input manual): ").strip()
        
        try:
            choice_num = int(choice)
            if choice_num == 0:
                chat = input("Masukkan username/ID grup (contoh: @grupgame atau -1001234567890): ").strip()
            elif 1 <= choice_num <= len(groups):
                selected_group = groups[choice_num - 1]
                chat = selected_group['link']
                print(f"✓ Dipilih: {selected_group['name']}")
            else:
                print("✗ Pilihan tidak valid!")
                return
        except ValueError:
            print("✗ Input harus angka!")
            return
        
        if not chat:
            print("✗ Chat target tidak boleh kosong!")
            return
        
        print(f"\n{'='*60}")
        print("🔌 MENGHUBUNGKAN & AUTO-JOIN USERBOT...")
        print(f"{'='*60}")
        
        # Connect all userbots
        valid_userbots = []
        
        for idx, userbot in enumerate(self.userbots, 1):
            try:
                print(f"\n[{idx}/{len(self.userbots)}] Connecting {userbot['phone']}...")
                
                client = TelegramClient(
                    StringSession(userbot['session']),
                    API_ID,
                    API_HASH
                )
                
                await client.connect()
                
                if await client.is_user_authorized():
                    me = await client.get_me()
                    self.clients[me.first_name] = client
                    valid_userbots.append(userbot)
                    print(f"✓ {me.first_name} (@{me.username}) terhubung")
                    
                    # Auto-join groups
                    print(f"  🔗 Auto-join ke grup...")
                    result = await self.group_manager.auto_join_groups(client, me.first_name)
                    
                    if result['joined']:
                        print(f"  ✓ Joined: {', '.join(result['joined'])}")
                    if result['already_in']:
                        print(f"  ℹ️  Already in: {', '.join(result['already_in'])}")
                    if result['failed']:
                        print(f"  ✗ Failed: {', '.join(result['failed'])}")
                    
                else:
                    print(f"✗ {userbot['phone']} tidak terotorisasi")
                    self.remove_invalid_userbot(userbot['phone'])
                
            except AuthKeyUnregisteredError:
                print(f"✗ Session {userbot['phone']} sudah tidak valid")
                self.remove_invalid_userbot(userbot['phone'])
            except Exception as e:
                print(f"✗ Error pada {userbot['phone']}: {e}")
        
        if len(self.clients) < 2:
            print("\n✗ Tidak cukup userbot valid! Minimal butuh 2 userbot aktif")
            return
        
        print(f"\n{'='*60}")
        print(f"✅ {len(self.clients)} USERBOT SIAP")
        print(f"{'='*60}")
        
        for name in self.clients.keys():
            print(f"   • {name}")
        
        self.target_chat = chat
        self.running = True
        
        print(f"\n🎯 Target: {chat}")
        print("🤖 Mode: Percakapan Natural dengan Reply System")
        print("📊 Data: GameFi Real 2025 (Axie, Illuvium, Ronin, etc)")
        print("🚀 Memulai percakapan otomatis...")
        print("⚠️  Tekan Ctrl+C untuk berhenti\n")
        
        try:
            await self.run_continuous_conversation(chat)
        finally:
            await self.stop_all_userbots()
    
    async def stop_all_userbots(self):
        """Stop dan disconnect semua userbot"""
        print("\n🔌 Memutuskan koneksi userbot...")
        
        for name, client in self.clients.items():
            try:
                await client.disconnect()
                print(f"✓ {name} disconnected")
            except Exception as e:
                print(f"✗ Error disconnecting {name}: {e}")
        
        self.clients.clear()
        self.running = False
        print("✅ Semua userbot telah diputuskan\n")
    
    def show_userbots(self):
        """Tampilkan daftar userbot"""
        if not self.userbots:
            print("\n📋 Belum ada userbot terdaftar")
            return
        
        print(f"\n{'='*60}")
        print("📋 DAFTAR USERBOT")
        print(f"{'='*60}")
        
        for idx, userbot in enumerate(self.userbots, 1):
            print(f"{idx}. {userbot['name']} (@{userbot['username']})")
            print(f"   📞 {userbot['phone']}")
            print()
    
    async def delete_userbot(self):
        """Hapus userbot"""
        self.show_userbots()
        
        if not self.userbots:
            return
        
        try:
            choice = int(input("Pilih nomor userbot yang ingin dihapus: "))
            
            if 1 <= choice <= len(self.userbots):
                userbot = self.userbots[choice - 1]
                confirm = input(f"Yakin hapus {userbot['name']}? (y/n): ").lower()
                
                if confirm == 'y':
                    self.userbots.pop(choice - 1)
                    self.save_config()
                    print(f"✓ {userbot['name']} berhasil dihapus")
            else:
                print("✗ Pilihan tidak valid")
        except ValueError:
            print("✗ Input harus berupa angka")
        except Exception as e:
            print(f"✗ Error: {e}")
    
    def manage_groups_menu(self):
        """Menu kelola grup"""
        while True:
            groups = self.group_manager.get_groups()
            
            print(f"\n{'='*60}")
            print("📋 KELOLA GRUP TARGET")
            print(f"{'='*60}")
            print(f"Total grup: {len(groups)}\n")
            print("1. ➕ Tambah Grup")
            print("2. 📜 Lihat Daftar Grup")
            print("3. 🗑️  Hapus Grup")
            print("4. 🔙 Kembali")
            print(f"{'='*60}")
            
            choice = input("Pilih menu: ").strip()
            
            if choice == '1':
                self.add_group()
            elif choice == '2':
                self.show_groups()
            elif choice == '3':
                self.delete_group()
            elif choice == '4':
                break
            else:
                print("✗ Pilihan tidak valid!")
    
    def add_group(self):
        """Tambah grup baru"""
        print("\n=== TAMBAH GRUP TARGET ===")
        print("Format link yang didukung:")
        print("  - Username: @namagrup atau namagrup")
        print("  - Invite link: https://t.me/joinchat/xxxxx")
        print("  - Join link: https://t.me/+xxxxx")
        print("  - ID numerik: -1001234567890\n")
        
        link = input("Masukkan link/username grup: ").strip()
        
        if not link:
            print("✗ Link tidak boleh kosong!")
            return
        
        name = input("Nama grup (opsional, tekan Enter untuk skip): ").strip()
        
        if self.group_manager.add_group(link, name):
            print(f"✓ Grup berhasil ditambahkan!")
        else:
            print("✗ Gagal menambahkan grup")
    
    def show_groups(self):
        """Tampilkan daftar grup"""
        groups = self.group_manager.get_groups()
        
        if not groups:
            print("\n📋 Belum ada grup yang ditambahkan")
            return
        
        print(f"\n{'='*60}")
        print("📋 DAFTAR GRUP TARGET")
        print(f"{'='*60}")
        
        for idx, group in enumerate(groups, 1):
            print(f"\n{idx}. {group['name']}")
            print(f"   Link: {group['link']}")
            print(f"   Ditambahkan: {group['added_at']}")
    
    def delete_group(self):
        """Hapus grup"""
        self.show_groups()
        
        groups = self.group_manager.get_groups()
        if not groups:
            return
        
        try:
            choice = int(input("\nPilih nomor grup yang ingin dihapus: "))
            
            if 1 <= choice <= len(groups):
                group = self.group_manager.remove_group(choice - 1)
                if group:
                    print(f"✓ Grup '{group['name']}' berhasil dihapus")
            else:
                print("✗ Pilihan tidak valid")
        except ValueError:
            print("✗ Input harus berupa angka")
        except Exception as e:
            print(f"✗ Error: {e}")


async def main():
    """Main function"""
    global API_ID, API_HASH
    
    print("""
╔═══════════════════════════════════════════════════════════╗
║                                                           ║
║     🎮 GAMEFI USERBOT CONVERSATION MANAGER 2025 🎮       ║
║                                                           ║
║         ✨ Natural Conversation with Reply System        ║
║         📊 Real GameFi Data (Axie, Illuvium, etc)        ║
║         🤖 AI-Powered Context Aware Responses            ║
║         🔗 Auto-Join Groups System                       ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝
""")
    
    # Check API credentials
    API_ID = os.getenv('API_ID')
    API_HASH = os.getenv('API_HASH')
    
    if not API_ID or not API_HASH:
        print("⚠️  API_ID dan API_HASH belum diset!")
        print("📝 Cara mendapatkan:")
        print("   1. Buka https://my.telegram.org")
        print("   2. Login dengan nomor Telegram")
        print("   3. Pilih 'API Development Tools'")
        print("   4. Buat aplikasi baru\n")
        
        API_ID = input("Masukkan API_ID: ").strip()
        API_HASH = input("Masukkan API_HASH: ").strip()
        
        if not API_ID or not API_HASH:
            print("✗ API credentials wajib diisi!")
            return
        
        # Save to .env
        with open('.env', 'w') as f:
            f.write(f"API_ID={API_ID}\n")
            f.write(f"API_HASH={API_HASH}\n")
        
        print("✓ API credentials tersimpan di .env\n")
    
    try:
        API_ID = int(API_ID)
    except ValueError:
        print("✗ API_ID harus berupa angka!")
        return
    
    manager = UserbotManager()
    manager.load_config()
    
    while True:
        print(f"\n{'='*60}")
        print("📋 MENU UTAMA")
        print(f"{'='*60}")
        print("1. 🤖 Tambah Userbot")
        print("2. 📜 Lihat Daftar Userbot")
        print("3. 🗑️  Hapus Userbot")
        print("4. 📂 Kelola Grup Target")
        print("5. 🚀 Start Percakapan Otomatis")
        print("6. ❌ Keluar")
        print(f"{'='*60}")
        
        choice = input("Pilih menu: ").strip()
        
        if choice == '1':
            await manager.add_userbot()
        elif choice == '2':
            manager.show_userbots()
        elif choice == '3':
            await manager.delete_userbot()
        elif choice == '4':
            manager.manage_groups_menu()
        elif choice == '5':
            await manager.start_all_userbots()
        elif choice == '6':
            print("\n👋 Terima kasih telah menggunakan GameFi Userbot Manager!")
            print("💡 Jangan lupa stop bot sebelum keluar untuk clean disconnect\n")
            break
        else:
            print("✗ Pilihan tidak valid!")


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⏹️  Program dihentikan oleh user")
    except Exception as e:
        print(f"\n✗ Fatal error: {e}")
        import traceback
        traceback.print_exc()
