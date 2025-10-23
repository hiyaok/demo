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
from datetime import datetime
import time
import re

CONFIG_FILE = 'userbot_config.json'
API_ID = None
API_HASH = None

class ConversationPersonality:
    """Personality system untuk setiap bot - biar unik"""
    
    PERSONALITIES = {
        'trader': {
            'style': ['analitis', 'suka angka', 'sering sebut profit/loss'],
            'phrases': ['ROI gue', 'flip ini', 'entry point', 'TP/SL', 'chart lagi', 'cuan'],
            'topics': ['price', 'trading', 'tokenomics', 'market cap'],
            'emoji_rate': 0.1,
        },
        'gamer': {
            'style': ['fokus gameplay', 'ngomongin meta', 'skill'],
            'phrases': ['grinding', 'clutch banget', 'OP nih', 'nerf', 'buff', 'meta berubah'],
            'topics': ['gameplay', 'tournament', 'ranking', 'skill'],
            'emoji_rate': 0.2,
        },
        'casual': {
            'style': ['santai', 'banyak typo', 'singkatan'],
            'phrases': ['wkwk', 'asli', 'bro', 'anjir', 'ga si', 'kok gitu', 'lah'],
            'topics': ['general', 'random', 'off-topic'],
            'emoji_rate': 0.15,
        },
        'researcher': {
            'style': ['detail', 'suka jelasin', 'kasih context'],
            'phrases': ['soalnya', 'basically', 'kalo dipikir', 'menurut gue', 'konteksnya'],
            'topics': ['tech', 'blockchain', 'development'],
            'emoji_rate': 0.05,
        },
        'degen': {
            'style': ['risk taker', 'YOLO', 'bold'],
            'phrases': ['all in', 'moon', 'wen lambo', 'ngape', 'hodl', 'diamond hands'],
            'topics': ['risky plays', 'new projects', 'hype'],
            'emoji_rate': 0.3,
        }
    }
    
    @staticmethod
    def assign_personality(user_id):
        """Assign personality based on user_id"""
        personalities = list(ConversationPersonality.PERSONALITIES.keys())
        idx = user_id % len(personalities)
        return personalities[idx]
    
    @staticmethod
    def get_phrase(personality_type):
        """Get random phrase from personality"""
        p = ConversationPersonality.PERSONALITIES.get(personality_type, ConversationPersonality.PERSONALITIES['casual'])
        if random.random() < 0.3:  # 30% chance inject personality phrase
            return random.choice(p['phrases'])
        return None


class GameFiConversationEngine:
    """Engine percakapan ULTRA NATURAL"""
    
    # Data GameFi 2025 - DIPERBANYAK
    REAL_DATA = {
        "games": [
            "Axie Infinity", "Illuvium", "Big Time", "Off The Grid", "Pixels",
            "Heroes of Mavia", "Gods Unchained", "Star Atlas", "Gala Games", 
            "Artyfact", "Guild of Guardians", "Splinterlands", "Ember Sword",
            "Phantom Galaxies", "Blast Royale", "Thetan Arena", "MOBOX",
            "My Neighbor Alice", "Town Star", "Nyan Heroes", "Shrapnel"
        ],
        "chains": [
            "Ronin", "Polygon", "Immutable X", "Immutable zkEVM", "Arbitrum",
            "Solana", "BNB Chain", "Sui", "Beam", "Flow", "Avalanche",
            "Optimism", "zkSync", "Starknet", "Base"
        ],
        "tokens": [
            "AXS", "RON", "IMX", "ILV", "BIGTIME", "SAND", "MANA", "GALA",
            "PIXEL", "MAVIA", "GODS", "ATLAS", "BEAM", "PRIME", "ALICE",
            "SLP", "GHST", "YGG", "NAKA", "UFO"
        ],
        "topics": [
            "floor price", "mint", "breeding", "scholarship", "guild war",
            "tournament", "airdrop", "staking", "liquidity", "gas fee",
            "whitelist", "presale", "roadmap", "partnership", "update patch"
        ]
    }
    
    # VARIED STARTERS - 50+ template
    STARTER_TOPICS = [
        # Price/Market
        "gue liat {token} pump {percent}% dari tadi pagi",
        "floor {game} NFT turun {percent}% guys, kesempatan nih",
        "{token} lagi consolidate ya, prediksi kalian gimana",
        "whales {token} mulai accumulate kayaknya, volume naik",
        "market cap {game} udah {amount}M sekarang",
        
        # Game Updates
        "patch {game} kemarin gimana? worth balik main ga",
        "{game} nambah map baru katanya, udah ada yg coba?",
        "meta {game} berubah total abis update ini",
        "breeding cost {game} turun, mayan buat newbie",
        "{game} collab sama {brand} baru diumumin",
        
        # Personal Experience
        "baru flip NFT {game} profit {percent}%",
        "grinding {game} dapet {amount} token hari ini",
        "gue ranked up di {game}, meta sekarang beda banget",
        "scholarship gue di {game} ROI nya udah balik modal",
        "baru join guild baru, sistem bagi hasilnya menarik",
        
        # Questions/Discussions
        "ada yang main {game}? pengen tau reviewnya",
        "{game} vs {game2}, mendingan mana sih?",
        "gas fee {chain} mahal banget hari ini kenapa ya",
        "recommend game baru dong, yang udah bisa cuan",
        "cara stake {token} yang paling profitable gimana",
        
        # News/Rumors
        "denger-denger {game} mau launching season baru",
        "ada insider info {game} partnership gede soon",
        "{chain} bakalan integrate {game} katanya",
        "tournament {game} hadiahnya {amount}K, gila",
        "presale {game} besok pagi, WL dapet ga kalian?",
        
        # Technical
        "smart contract {game} kena audit belom ya?",
        "tokenomics {token} sustainable ga sih long term",
        "{chain} TPS nya cocok buat gaming ga si",
        "NFT {game} utility nya apa aja sebenernya",
        "liquidity pool {token} APY nya berapa sekarang",
        
        # Casual/Organic
        "capek juga grinding 8 jam non stop",
        "tim gue di {game} akhirnya menang tournament",
        "baru dapet rare drop, jual atau hold ya",
        "energy system {game} annoying banget anjir",
        "RNG gue hari ini ancur total wkwk",
    ]
    
    # RESPONSE TEMPLATES - biar AI lebih varied
    RESPONSE_TYPES = {
        'agree': [
            "iya bener {phrase}",
            "setuju {phrase}",
            "yoi {phrase}",
            "betul banget {phrase}",
            "exactly {phrase}",
            "nah itu dia {phrase}",
        ],
        'disagree': [
            "hmm ga yakin gue {phrase}",
            "kurang setuju {phrase}",
            "menurut gue beda {phrase}",
            "wait, {phrase}",
            "kok bisa {phrase}",
        ],
        'question': [
            "emang {phrase}?",
            "serius {phrase}?",
            "{phrase} gimana caranya?",
            "wait {phrase}?",
            "maksud lo {phrase}?",
        ],
        'info': [
            "btw {phrase}",
            "oh iya {phrase}",
            "tambahan {phrase}",
            "fun fact {phrase}",
            "gue baca {phrase}",
        ],
        'casual': [
            "wkwk {phrase}",
            "anjir {phrase}",
            "asli {phrase}",
            "gila {phrase}",
            "lah {phrase}",
        ]
    }
    
    # OFF-TOPIC - diperbanyak
    OFF_TOPICS = [
        "btw ada yang nonton tournament kemarin? seru banget",
        "guys internet gue lemot parah hari ini",
        "udah makan siang belom? gue laper nih",
        "capek juga grinding 5 jam straight wkwk",
        "ada recommend VPN yang bagus ga?",
        "weekend kalian ngapain biasanya?",
        "gue butuh coffee break dulu kayaknya",
        "laptop gue mulai panas nih, worry",
        "ada yang tau discord server bagus?",
        "lagi males login game hari ini entah kenapa",
        "cuaca lagi enak buat gaming sih",
        "setup gaming kalian gimana?",
        "mouse gue kayaknya mau rusak anjir",
        "gue tinggal sebentar ya, ada urusan dikit",
        "headset gue batre nya abis, hold",
    ]
    
    @staticmethod
    def fill_template(text):
        """Fill template dengan data random"""
        games = GameFiConversationEngine.REAL_DATA["games"]
        
        replacements = {
            "{game}": random.choice(games),
            "{game2}": random.choice([g for g in games if g != text]),  # beda game
            "{chain}": random.choice(GameFiConversationEngine.REAL_DATA["chains"]),
            "{token}": random.choice(GameFiConversationEngine.REAL_DATA["tokens"]),
            "{percent}": random.randint(5, 50),
            "{amount}": random.choice([10, 50, 100, 500, "1", "5"]),
            "{brand}": random.choice(["Ubisoft", "Epic Games", "Samsung", "Sony", "Nvidia", "Coinbase"]),
            "{phrase}": "",  # akan diisi personality
        }
        
        for key, val in replacements.items():
            text = text.replace(key, str(val))
        return text
    
    @staticmethod
    def get_starter():
        """Get starter dengan weighted random"""
        # 85% topik GameFi, 15% off-topic
        if random.random() < 0.15:
            return random.choice(GameFiConversationEngine.OFF_TOPICS)
        
        topic = random.choice(GameFiConversationEngine.STARTER_TOPICS)
        return GameFiConversationEngine.fill_template(topic)
    
    @staticmethod
    def inject_typo(text):
        """Inject natural typo (20% chance)"""
        if random.random() > 0.2:
            return text
        
        typo_map = {
            'kok': 'ko', 'gimana': 'gmn', 'banget': 'bgt', 'sama': 'sm',
            'gue': 'gw', 'juga': 'jg', 'yang': 'yg', 'dengan': 'dgn',
            'tidak': 'ga', 'emang': 'emg', 'kenapa': 'knp', 'bisa': 'bs',
            'sekarang': 'skrg', 'kayak': 'kyk', 'nanti': 'ntr'
        }
        
        words = text.split()
        if len(words) > 3:
            idx = random.randint(0, len(words)-1)
            word = words[idx].lower()
            if word in typo_map:
                words[idx] = typo_map[word]
        
        return ' '.join(words)
    
    @staticmethod
    def inject_personality(text, personality):
        """Inject personality phrase"""
        phrase = ConversationPersonality.get_phrase(personality)
        if phrase and len(text) < 80:  # hanya untuk short message
            # Insert di random position
            words = text.split()
            if len(words) > 2:
                pos = random.randint(1, len(words)-1)
                words.insert(pos, phrase)
                return ' '.join(words)
        return text
    
    @staticmethod
    def build_context(history, max_msgs=10):
        """Build context dengan lebih rich info"""
        recent = history[-max_msgs:] if len(history) > max_msgs else history
        
        if not recent:
            return "GRUP BARU SEPI"
        
        context = "PERCAKAPAN TERAKHIR:\n"
        for msg in recent:
            context += f"- {msg['name']}: {msg['text']}\n"
        
        # Extract topics yang lagi dibahas
        all_text = ' '.join([m['text'] for m in recent])
        topics_mentioned = []
        
        for game in GameFiConversationEngine.REAL_DATA['games']:
            if game.lower() in all_text.lower():
                topics_mentioned.append(game)
        
        if topics_mentioned:
            context += f"\nTOPIK AKTIF: {', '.join(set(topics_mentioned[:3]))}\n"
        
        return context
    
    @staticmethod
    def create_prompt(context, responder_name, personality, is_reply, target_msg=None):
        """Create AI prompt dengan personality injection"""
        
        p_data = ConversationPersonality.PERSONALITIES[personality]
        
        base = f"""Kamu adalah {responder_name}, personality: {personality.upper()}
Style: {', '.join(p_data['style'])}
Sering bilang: {', '.join(p_data['phrases'][:3])}

ATURAN KETAT:
- Bahasa Indonesia SANGAT CASUAL (typo ok, singkatan ok, gaul banget)
- Topik: GameFi/Web3 Gaming (games, NFT, tokens, blockchain gaming)
- JANGAN formal, JANGAN kaku, JANGAN terlalu educate
- JANGAN sebut nama orang kecuali perlu
- JANGAN ulang kata yang baru disebutin orang lain
- MAX 100 karakter (1-2 kalimat pendek)
- Emoji: JARANG (max 1, mostly ga pake)
- Bervariasi: kadang setuju, kadang nanya, kadang info baru, kadang bercanda

{context}

"""
        
        if is_reply and target_msg:
            base += f"\nMAU REPLY: {target_msg['name']} bilang: \"{target_msg['text']}\"\n\n"
            base += "OPTIONS:\n"
            base += "- Setuju + alasan singkat\n"
            base += "- Nanya follow-up\n"
            base += "- Kasih info tambahan\n"
            base += "- Beda pendapat (sopan)\n"
            base += "- Bercanda/casual response\n"
        else:
            base += "\nMAU NAMBAH TOPIK BARU atau expand topik yang lagi dibahas.\n"
            base += "Pilih: kasih info baru / nanya hal lain / share pengalaman / off-topic ringan\n"
        
        base += f"\nRESPON AS {responder_name.upper()} ({personality}):"
        
        return base


class GroupManager:
    def __init__(self, config_file):
        self.config_file = config_file
        self.groups = []
        self.load_groups()
    
    def load_groups(self):
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    data = json.load(f)
                    self.groups = data.get('groups', [])
            except:
                self.groups = []
    
    def save_groups(self):
        try:
            data = {}
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    data = json.load(f)
            data['groups'] = self.groups
            with open(self.config_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"✗ Save error: {e}")
    
    def add_group(self, link, name=None):
        if any(g['link'] == link for g in self.groups):
            return False
        self.groups.append({
            'link': link,
            'name': name or link,
            'added_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })
        self.save_groups()
        return True
    
    def remove_group(self, idx):
        if 0 <= idx < len(self.groups):
            removed = self.groups.pop(idx)
            self.save_groups()
            return removed
        return None
    
    def get_groups(self):
        return self.groups
    
    async def auto_join_groups(self, client, name):
        joined, already, failed = [], [], []
        
        for group in self.groups:
            try:
                link = group['link'].strip()
                
                if 'joinchat/' in link or '+' in link:
                    hash_match = re.search(r'joinchat/([a-zA-Z0-9_-]+)', link) or re.search(r'\+([a-zA-Z0-9_-]+)', link)
                    if hash_match:
                        try:
                            await client(ImportChatInviteRequest(hash_match.group(1)))
                            joined.append(group['name'])
                            await asyncio.sleep(random.uniform(2, 4))
                        except UserAlreadyParticipantError:
                            already.append(group['name'])
                        except InviteHashExpiredError:
                            failed.append(f"{group['name']} (expired)")
                else:
                    username = link.replace('@', '').replace('https://t.me/', '')
                    try:
                        await client(JoinChannelRequest(username))
                        joined.append(group['name'])
                        await asyncio.sleep(random.uniform(2, 4))
                    except UserAlreadyParticipantError:
                        already.append(group['name'])
                
            except FloodWaitError as e:
                print(f"⏳ FloodWait {e.seconds}s...")
                await asyncio.sleep(e.seconds)
            except Exception as e:
                failed.append(f"{group['name']}")
        
        return {'joined': joined, 'already_in': already, 'failed': failed}


class UserbotManager:
    def __init__(self):
        self.userbots = []
        self.clients = {}  # {user_id: {'client': ..., 'name': ..., 'username': ..., 'personality': ...}}
        self.running = False
        self.conversation_history = []
        self.used_topics = set()
        self.recent_speakers = []  # Track 3 pembicara terakhir
        self.session_id = f"gf_{int(time.time())}_{random.randint(1000,9999)}"
        self.engine = GameFiConversationEngine()
        self.group_manager = GroupManager(CONFIG_FILE)
        self.external_users = {}  # Track external users
        self.last_external_time = 0
    
    def get_display_name(self, user):
        """Get proper display name"""
        if hasattr(user, 'first_name') and user.first_name:
            if hasattr(user, 'last_name') and user.last_name:
                return f"{user.first_name} {user.last_name}"
            return user.first_name
        elif hasattr(user, 'username') and user.username:
            return user.username
        else:
            return f"User{user.id}"
    
    def load_config(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r') as f:
                    data = json.load(f)
                    self.userbots = data.get('userbots', [])
                    print(f"✓ Loaded {len(self.userbots)} userbots")
            except Exception as e:
                print(f"✗ Load error: {e}")
                self.userbots = []
        else:
            self.userbots = []
    
    def save_config(self):
        try:
            data = {'userbots': self.userbots}
            if os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE, 'r') as f:
                    existing = json.load(f)
                    if 'groups' in existing:
                        data['groups'] = existing['groups']
            with open(CONFIG_FILE, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"✗ Save error: {e}")
    
    def remove_invalid_userbot(self, phone):
        self.userbots = [u for u in self.userbots if u['phone'] != phone]
        self.save_config()
    
    async def add_userbot(self):
        print("\n=== TAMBAH USERBOT ===")
        
        if not API_ID or not API_HASH:
            print("✗ API_ID dan API_HASH belum diset!")
            return
        
        phone = input("Nomor (contoh: +6281234567890): ").strip()
        
        if any(u['phone'] == phone for u in self.userbots):
            print("✗ Nomor sudah terdaftar!")
            return
        
        try:
            client = TelegramClient(StringSession(), API_ID, API_HASH)
            await client.connect()
            
            if not await client.is_user_authorized():
                await client.send_code_request(phone)
                code = input("Kode verifikasi: ").strip()
                
                try:
                    await client.sign_in(phone, code)
                except SessionPasswordNeededError:
                    password = input("Password 2FA: ").strip()
                    await client.sign_in(password=password)
            
            me = await client.get_me()
            session_string = client.session.save()
            
            self.userbots.append({
                'phone': phone,
                'session': session_string,
                'name': me.first_name,
                'username': me.username or "no_username",
                'user_id': me.id
            })
            self.save_config()
            
            display = self.get_display_name(me)
            print(f"✓ Sukses: {display} (@{me.username})")
            
            await client.disconnect()
            
        except Exception as e:
            print(f"✗ Error: {e}")
    
    async def call_ai(self, prompt):
        """Call AI dengan retry dan cleanup"""
        max_retries = 2
        
        for attempt in range(max_retries):
            try:
                url = "https://api.ryzumi.vip/api/ai/deepseek"
                params = {
                    'text': prompt,
                    'prompt': 'Respond VERY casually in Indonesian about GameFi. Be brief, natural, use slang.',
                    'session': self.session_id
                }
                
                response = requests.get(url, params=params, timeout=12)
                
                if response.status_code == 200:
                    data = response.json()
                    result = data.get('result', data.get('response', ''))
                    
                    if result:
                        # Cleanup
                        result = result.strip()
                        # Remove quotes
                        result = result.strip('"\'')
                        # Remove markdown
                        result = re.sub(r'\*\*?', '', result)
                        
                        # Validasi length
                        if 10 < len(result) < 150:
                            return result
                
                # Jika gagal, retry dengan delay
                if attempt < max_retries - 1:
                    await asyncio.sleep(1)
                    
            except Exception as e:
                if attempt < max_retries - 1:
                    await asyncio.sleep(1)
                    continue
        
        return None
    
    def get_fallback(self, context_type='neutral'):
        """Smart fallback based on context"""
        fallbacks = {
            'agree': ["iya juga sih", "bener", "yoi", "setuju", "makes sense"],
            'question': ["oh gitu?", "serius?", "wait gimana?", "maksudnya?"],
            'info': ["oh iya ya", "TIL", "baru tau gue", "nice info"],
            'casual': ["wkwk", "lah", "anjir", "asli", "gila juga"],
            'neutral': ["hmm", "oke", "ic", "noted", "interesting"]
        }
        
        return random.choice(fallbacks.get(context_type, fallbacks['neutral']))
    
    async def send_typing(self, client, chat, msg, reply_to=None):
        """Send dengan realistic typing simulation"""
        try:
            # Calculate realistic typing time
            words = len(msg.split())
            chars = len(msg)
            
            # WPM 40-60 untuk casual typing
            base_time = (chars / 5) / random.uniform(40, 60) * 60  # in seconds
            typing_time = min(base_time * random.uniform(0.8, 1.2), 5)  # max 5s
            
            # Typing action
            async with client.action(chat, 'typing'):
                await asyncio.sleep(typing_time)
            
            # Send
            sent_msg = await client.send_message(chat, msg, reply_to=reply_to)
            return sent_msg
            
        except Exception as e:
            print(f"✗ Send error: {e}")
            return None
    
    async def check_external_messages(self, chat_id):
        """Check dan respond ke external users"""
        current_time = time.time()
        
        # Cek setiap 30 detik
        if current_time - self.last_external_time < 30:
            return []
        
        self.last_external_time = current_time
        
        try:
            # Pilih random bot untuk cek
            bot_id = random.choice(list(self.clients.keys()))
            client = self.clients[bot_id]['client']
            
            messages = await client.get_messages(chat_id, limit=10)
            
            external = []
            bot_ids = set(self.clients.keys())
            
            for msg in messages:
                # Skip jika dari bot kita
                if msg.sender_id in bot_ids:
                    continue
                
                # Cek waktu (dalam 2 menit terakhir)
                if msg.text and (current_time - msg.date.timestamp()) < 120:
                    
                    # Get sender info
                    try:
                        sender = await msg.get_sender()
                        sender_name = self.get_display_name(sender)
                    except:
                        sender_name = "User"
                    
                    external.append({
                        'sender_id': msg.sender_id,
                        'sender_name': sender_name,
                        'text': msg.text,
                        'msg_obj': msg,
                        'timestamp': msg.date.timestamp()
                    })
                    
                    # Track external user
                    if msg.sender_id not in self.external_users:
                        self.external_users[msg.sender_id] = {
                            'name': sender_name,
                            'first_seen': current_time,
                            'message_count': 1
                        }
                    else:
                        self.external_users[msg.sender_id]['message_count'] += 1
            
            return external
            
        except Exception as e:
            return []
    
    def select_responder(self, bot_ids, exclude_ids=None):
        """Smart responder selection"""
        if exclude_ids is None:
            exclude_ids = []
        
        # Exclude recent speakers (last 3)
        exclude_ids.extend(self.recent_speakers[-3:])
        
        available = [bid for bid in bot_ids if bid not in exclude_ids]
        
        if not available:
            available = bot_ids
        
        return random.choice(available)
    
    async def generate_conversation(self, chat_id):
        """Generate PERFECT NATURAL conversation"""
        
        bot_ids = list(self.clients.keys())
        
        if len(bot_ids) < 2:
            print("✗ Need min 2 bots")
            return
            print(f"\n{'='*60}")
        print(f"🎬 NEW SESSION - ULTRA NATURAL")
        print(f"{'='*60}\n")
        
        # PHASE 1: STARTER (random bot)
        starter_id = random.choice(bot_ids)
        starter_client = self.clients[starter_id]['client']
        starter_name = self.clients[starter_id]['name']
        starter_personality = self.clients[starter_id]['personality']
        
        starter_msg = self.engine.get_starter()
        starter_msg = self.engine.inject_typo(starter_msg)
        starter_msg = self.engine.inject_personality(starter_msg, starter_personality)
        
        print(f"💬 {starter_name} [{starter_personality}]: {starter_msg}")
        
        sent = await self.send_typing(starter_client, chat_id, starter_msg)
        
        self.conversation_history.append({
            'user_id': starter_id,
            'name': starter_name,
            'text': starter_msg,
            'msg_obj': sent,
            'personality': starter_personality
        })
        
        self.recent_speakers.append(starter_id)
        
        # Track keywords
        for word in starter_msg.lower().split():
            if len(word) > 5:
                self.used_topics.add(word)
        
        # Initial delay
        await asyncio.sleep(random.uniform(2, 6))
        
        # PHASE 2: CONVERSATION FLOW
        num_messages = random.randint(18, 30)  # Lebih panjang, lebih natural
        
        for turn in range(num_messages):
            
            # CHECK EXTERNAL MESSAGES (every 4-6 turns)
            if turn % random.randint(4, 6) == 0:
                external = await self.check_external_messages(chat_id)
                
                if external:
                    ext_msg = external[0]  # Respond ke yang terbaru
                    
                    print(f"\n🔔 External: {ext_msg['sender_name']}: {ext_msg['text']}")
                    
                    # Select responder (not last speaker)
                    responder_id = self.select_responder(bot_ids, [self.recent_speakers[-1]] if self.recent_speakers else [])
                    responder_client = self.clients[responder_id]['client']
                    responder_name = self.clients[responder_id]['name']
                    responder_personality = self.clients[responder_id]['personality']
                    
                    # Build context
                    context = self.engine.build_context(self.conversation_history)
                    context += f"\n\nUSER LAIN JOIN: {ext_msg['sender_name']} bilang: \"{ext_msg['text']}\"\n"
                    
                    prompt = f"""Kamu {responder_name} (personality: {responder_personality}) di grup GameFi.

{context}

TUGAS: Respond ke {ext_msg['sender_name']} dengan NATURAL dan HELPFUL.
- Jika dia nanya: jawab dengan info berguna
- Jika dia komen: reply yang nyambung (setuju/explain/nanya balik)
- Jika dia sharing: respond positif atau curious
- Bahasa casual banget, 1-2 kalimat, max 100 char
- Sambut dia dengan friendly, jangan kaku!

RESPOND:"""
                    
                    ai_response = await self.call_ai(prompt)
                    
                    if not ai_response:
                        # Smart fallback based on message type
                        if '?' in ext_msg['text']:
                            response_text = f"hmm {ext_msg['text'].split()[0]} ya, gue kurang tau detail nya deh"
                        else:
                            response_text = f"oh {random.choice(['menarik', 'interesting', 'nice', 'asli'])} {random.choice(['juga', 'sih', 'bro', ''])}"
                    else:
                        response_text = ai_response
                    
                    response_text = self.engine.inject_typo(response_text)
                    
                    print(f"📤 {responder_name} ↩️ {ext_msg['sender_name']}: {response_text}")
                    
                    sent = await self.send_typing(responder_client, chat_id, response_text, reply_to=ext_msg['msg_obj'])
                    
                    self.conversation_history.append({
                        'user_id': responder_id,
                        'name': responder_name,
                        'text': response_text,
                        'msg_obj': sent,
                        'personality': responder_personality
                    })
                    
                    self.recent_speakers.append(responder_id)
                    if len(self.recent_speakers) > 5:
                        self.recent_speakers = self.recent_speakers[-5:]
                    
                    await asyncio.sleep(random.uniform(2, 5))
                    continue
            
            # SELECT NEXT RESPONDER (anti consecutive)
            responder_id = self.select_responder(bot_ids)
            responder_client = self.clients[responder_id]['client']
            responder_name = self.clients[responder_id]['name']
            responder_personality = self.clients[responder_id]['personality']
            
            # DECISION TREE: Reply vs Standalone vs Off-topic
            decision = random.choices(
                ['reply', 'standalone', 'off_topic'],
                weights=[0.65, 0.25, 0.10]  # 65% reply, 25% standalone, 10% off-topic
            )[0]
            
            context = self.engine.build_context(self.conversation_history)
            
            if decision == 'off_topic':
                # OFF-TOPIC MESSAGE
                response_text = random.choice(self.engine.OFF_TOPICS)
                reply_to = None
                print(f"📤 {responder_name} [OFF-TOPIC]: {response_text}")
                
            elif decision == 'reply':
                # REPLY TO SOMEONE
                # Get possible targets (exclude self, prioritize recent)
                possible_targets = [
                    h for h in self.conversation_history[-6:] 
                    if h['user_id'] != responder_id
                ]
                
                if not possible_targets:
                    # Fallback ke standalone
                    decision = 'standalone'
                else:
                    # Weight: lebih baru = lebih likely
                    weights = [i+1 for i in range(len(possible_targets))]
                    target = random.choices(possible_targets, weights=weights)[0]
                    
                    prompt = self.engine.create_prompt(
                        context, 
                        responder_name, 
                        responder_personality,
                        True, 
                        target
                    )
                    
                    ai_response = await self.call_ai(prompt)
                    
                    if ai_response:
                        response_text = ai_response
                    else:
                        # Context-aware fallback
                        if '?' in target['text']:
                            response_text = self.get_fallback('question')
                        elif any(word in target['text'].lower() for word in ['setuju', 'iya', 'bener']):
                            response_text = self.get_fallback('agree')
                        else:
                            response_text = self.get_fallback('neutral')
                    
                    response_text = self.engine.inject_typo(response_text)
                    response_text = self.engine.inject_personality(response_text, responder_personality)
                    
                    reply_to = target['msg_obj']
                    print(f"📤 {responder_name} ↩️ {target['name']}: {response_text}")
            
            if decision == 'standalone':
                # STANDALONE MESSAGE
                prompt = self.engine.create_prompt(
                    context,
                    responder_name,
                    responder_personality,
                    False
                )
                
                ai_response = await self.call_ai(prompt)
                
                if ai_response:
                    response_text = ai_response
                else:
                    # Generate fallback standalone
                    templates = [
                        f"btw {random.choice(['gue', 'gw'])} baru coba {random.choice(self.engine.REAL_DATA['games'])}",
                        f"{random.choice(self.engine.REAL_DATA['tokens'])} movement nya aneh hari ini",
                        f"ada yang {random.choice(['grinding', 'main', 'coba'])} {random.choice(self.engine.REAL_DATA['games'])}?",
                    ]
                    response_text = random.choice(templates)
                
                response_text = self.engine.inject_typo(response_text)
                response_text = self.engine.inject_personality(response_text, responder_personality)
                
                reply_to = None
                print(f"📤 {responder_name}: {response_text}")
            
            # SEND MESSAGE
            sent = await self.send_typing(responder_client, chat_id, response_text, reply_to=reply_to)
            
            if sent:
                self.conversation_history.append({
                    'user_id': responder_id,
                    'name': responder_name,
                    'text': response_text,
                    'msg_obj': sent,
                    'personality': responder_personality
                })
                
                self.recent_speakers.append(responder_id)
                if len(self.recent_speakers) > 5:
                    self.recent_speakers = self.recent_speakers[-5:]
            
            # DYNAMIC DELAY (ultra realistic)
            # Patterns: instant, quick, normal, thinking, slow
            delay_patterns = {
                'instant': (0.5, 1.5),      # Quick reaction
                'quick': (2, 4),            # Normal speed
                'normal': (4, 8),           # Casual
                'thinking': (8, 12),        # Typing long/thinking
                'slow': (12, 20),           # Distracted/busy
            }
            
            # Weight based on message complexity
            msg_length = len(response_text)
            if msg_length < 20:
                weights = [0.30, 0.40, 0.20, 0.07, 0.03]
            elif msg_length < 50:
                weights = [0.15, 0.35, 0.30, 0.15, 0.05]
            else:
                weights = [0.05, 0.20, 0.35, 0.30, 0.10]
            
            pattern = random.choices(list(delay_patterns.keys()), weights=weights)[0]
            delay = random.uniform(*delay_patterns[pattern])
            
            await asyncio.sleep(delay)
        
        print(f"\n{'='*60}")
        print(f"✅ Session complete: {num_messages} messages")
        print(f"{'='*60}\n")
    
    async def run_continuous(self, chat_id):
        """Run continuously with smart breaks"""
        
        session_count = 0
        
        try:
            while self.running:
                session_count += 1
                
                print(f"\n{'🔥'*3} SESSION #{session_count} {'🔥'*3}")
                
                await self.generate_conversation(chat_id)
                
                # SMART BREAK SYSTEM
                # Break patterns based on time of day simulation
                break_patterns = {
                    'micro': (20, 60),          # 20s-1m: active hours
                    'short': (60, 180),         # 1-3m: normal
                    'medium': (180, 300),       # 3-5m: casual
                    'long': (300, 600),         # 5-10m: break time
                }
                
                # Weight: mostly short breaks, occasional long
                pattern = random.choices(
                    list(break_patterns.keys()),
                    weights=[0.25, 0.45, 0.20, 0.10]
                )[0]
                
                break_time = random.uniform(*break_patterns[pattern])
                
                mins = int(break_time // 60)
                secs = int(break_time % 60)
                print(f"⏸️  Break: {mins}m {secs}s ({pattern})\n")
                
                await asyncio.sleep(break_time)
                
                # MAINTENANCE every 5 sessions
                if session_count % 5 == 0:
                    print(f"🔧 Maintenance...")
                    
                    # Reset session for AI variety
                    self.session_id = f"gf_{int(time.time())}_{random.randint(1000,9999)}"
                    
                    # Trim history
                    if len(self.conversation_history) > 30:
                        self.conversation_history = self.conversation_history[-20:]
                    
                    # Clear old topics
                    if len(self.used_topics) > 100:
                        self.used_topics = set(list(self.used_topics)[-50:])
                    
                    # Clear old external users
                    current_time = time.time()
                    self.external_users = {
                        uid: data for uid, data in self.external_users.items()
                        if current_time - data['first_seen'] < 3600  # Keep 1 hour
                    }
                    
                    print(f"✓ Session reset, history trimmed\n")
                
        except KeyboardInterrupt:
            print("\n\n⏹️  Stopped by user")
        except Exception as e:
            print(f"\n✗ Error: {e}")
            import traceback
            traceback.print_exc()
        finally:
            self.running = False
    
    async def start_all(self):
        """Start all bots with auto-join"""
        if len(self.userbots) < 2:
            print("✗ Need minimum 2 bots!")
            return
        
        groups = self.group_manager.get_groups()
        if not groups:
            print("✗ No groups found! Add groups first.")
            return
        
        print(f"\n{'='*60}")
        print("📋 AVAILABLE GROUPS")
        print(f"{'='*60}")
        for idx, g in enumerate(groups, 1):
            print(f"{idx}. {g['name']}")
        
        choice = input("\nSelect group (0 for manual): ").strip()
        
        try:
            num = int(choice)
            if num == 0:
                chat = input("Enter username/ID: ").strip()
            elif 1 <= num <= len(groups):
                chat = groups[num-1]['link']
            else:
                print("✗ Invalid choice!")
                return
        except:
            print("✗ Enter a number!")
            return
        
        print(f"\n{'='*60}")
        print("🔌 CONNECTING BOTS...")
        print(f"{'='*60}")
        
        for idx, bot in enumerate(self.userbots, 1):
            try:
                print(f"\n[{idx}/{len(self.userbots)}] {bot['phone']}...")
                
                client = TelegramClient(StringSession(bot['session']), API_ID, API_HASH)
                await client.connect()
                
                if await client.is_user_authorized():
                    me = await client.get_me()
                    name = self.get_display_name(me)
                    
                    # ASSIGN PERSONALITY
                    personality = ConversationPersonality.assign_personality(me.id)
                    
                    self.clients[me.id] = {
                        'client': client,
                        'name': name,
                        'username': me.username or "no_username",
                        'personality': personality
                    }
                    
                    print(f"✓ {name} (@{me.username}) - Personality: {personality.upper()}")
                    
                    # Auto-join groups
                    result = await self.group_manager.auto_join_groups(client, name)
                    if result['joined']:
                        print(f"  ✓ Joined: {', '.join(result['joined'])}")
                    if result['already_in']:
                        print(f"  ℹ️  Already in: {', '.join(result['already_in'])}")
                    if result['failed']:
                        print(f"  ✗ Failed: {', '.join(result['failed'])}")
                    
                else:
                    print(f"✗ Not authorized - removing")
                    self.remove_invalid_userbot(bot['phone'])
                
            except AuthKeyUnregisteredError:
                print(f"✗ Invalid session - removing")
                self.remove_invalid_userbot(bot['phone'])
            except Exception as e:
                print(f"✗ Error: {e}")
        
        if len(self.clients) < 2:
            print("\n✗ Need at least 2 active bots!")
            return
        
        print(f"\n{'='*60}")
        print(f"✅ {len(self.clients)} BOTS READY")
        print(f"{'='*60}")
        for uid, data in self.clients.items():
            print(f"   • {data['name']} ({data['personality']})")
        
        self.running = True
        
        print(f"\n{'='*60}")
        print(f"🎯 Target: {chat}")
        print(f"🤖 Mode: ULTRA NATURAL v2.0")
        print(f"{'='*60}")
        print("✅ Unique personalities per bot")
        print("✅ NO self-reply (strict enforcement)")
        print("✅ NO repetition (smart tracking)")
        print("✅ AI-powered varied responses")
        print("✅ Auto-respond to external users")
        print("✅ Natural typos & slang")
        print("✅ Dynamic delays (0.5s-20s)")
        print("✅ Smart break system (20s-10m)")
        print(f"{'='*60}")
        print("🚀 Starting...\n")
        
        try:
            await self.run_continuous(chat)
        finally:
            await self.stop_all()
    
    async def stop_all(self):
        """Stop all bots"""
        print("\n🔌 Disconnecting all bots...")
        
        for uid, data in self.clients.items():
            try:
                await data['client'].disconnect()
                print(f"✓ {data['name']} disconnected")
            except Exception as e:
                print(f"✗ Error disconnecting {data['name']}: {e}")
        
        self.clients.clear()
        self.running = False
        print("✅ All bots disconnected\n")
    
    def show_userbots(self):
        """Show registered userbots"""
        if not self.userbots:
            print("\n📋 No userbots registered yet")
            return
        
        print(f"\n{'='*60}")
        print("📋 REGISTERED USERBOTS")
        print(f"{'='*60}")
        
        for idx, bot in enumerate(self.userbots, 1):
            print(f"\n{idx}. {bot['name']} (@{bot['username']})")
            print(f"   📞 {bot['phone']}")
            if 'user_id' in bot:
                print(f"   🆔 {bot['user_id']}")
    
    async def delete_userbot(self):
        """Delete a userbot"""
        self.show_userbots()
        
        if not self.userbots:
            return
        
        try:
            choice = int(input("\nSelect number to delete: "))
            
            if 1 <= choice <= len(self.userbots):
                bot = self.userbots[choice - 1]
                confirm = input(f"Delete {bot['name']}? (y/n): ").lower()
                
                if confirm == 'y':
                    self.userbots.pop(choice - 1)
                    self.save_config()
                    print(f"✓ {bot['name']} deleted successfully")
            else:
                print("✗ Invalid number")
        except ValueError:
            print("✗ Please enter a number")
        except Exception as e:
            print(f"✗ Error: {e}")
    
    def manage_groups_menu(self):
        """Manage groups menu"""
        while True:
            groups = self.group_manager.get_groups()
            
            print(f"\n{'='*60}")
            print("📋 MANAGE GROUPS")
            print(f"{'='*60}")
            print(f"Total groups: {len(groups)}\n")
            print("1. ➕ Add Group")
            print("2. 📜 View Groups")
            print("3. 🗑️  Delete Group")
            print("4. 🔙 Back to Main Menu")
            print(f"{'='*60}")
            
            choice = input("Choose: ").strip()
            
            if choice == '1':
                self.add_group()
            elif choice == '2':
                self.show_groups()
            elif choice == '3':
                self.delete_group()
            elif choice == '4':
                break
            else:
                print("✗ Invalid choice!")
    
    def add_group(self):
        """Add a group"""
        print("\n=== ADD GROUP ===")
        print("Supported formats:")
        print("  - @username")
        print("  - https://t.me/joinchat/xxxxx")
        print("  - https://t.me/+xxxxx")
        print("  - -1001234567890\n")
        
        link = input("Group link/username: ").strip()
        
        if not link:
            print("✗ Link cannot be empty!")
            return
        
        name = input("Group name (Enter to skip): ").strip()
        
        if self.group_manager.add_group(link, name):
            print(f"✓ Group added successfully!")
        else:
            print("✗ Group already exists!")
    
    def show_groups(self):
        """Show all groups"""
        groups = self.group_manager.get_groups()
        
        if not groups:
            print("\n📋 No groups added yet")
            return
        
        print(f"\n{'='*60}")
        print("📋 GROUP LIST")
        print(f"{'='*60}")
        
        for idx, g in enumerate(groups, 1):
            print(f"\n{idx}. {g['name']}")
            print(f"   Link: {g['link']}")
            print(f"   Added: {g['added_at']}")
    
    def delete_group(self):
        """Delete a group"""
        self.show_groups()
        
        groups = self.group_manager.get_groups()
        if not groups:
            return
        
        try:
            choice = int(input("\nSelect number to delete: "))
            
            if 1 <= choice <= len(groups):
                g = self.group_manager.remove_group(choice - 1)
                if g:
                    print(f"✓ '{g['name']}' deleted successfully")
            else:
                print("✗ Invalid number")
        except ValueError:
            print("✗ Please enter a number")
        except Exception as e:
            print(f"✗ Error: {e}")


async def main():
    """Main function"""
    global API_ID, API_HASH
    
    print("""
╔═══════════════════════════════════════════════════════════╗
║                                                           ║
║     🎮 GAMEFI USERBOT ULTIMATE v2.0 🎮                   ║
║                                                           ║
║     ✅ Unique Personality per Bot                        ║
║     ✅ 100% NO Self-Reply (Strict)                       ║
║     ✅ NO Repetition (Smart Tracking)                    ║
║     ✅ AI-Powered Natural Responses                      ║
║     ✅ Auto-Respond to External Users                    ║
║     ✅ Natural Typos & Slang                             ║
║     ✅ Context-Aware Conversations                       ║
║     ✅ Dynamic Realistic Delays                          ║
║     ✅ Smart Break System                                ║
║     ✅ 50+ Topic Templates                               ║
║                                                           ║
║     🚀 PERFECT HUMAN-LIKE CONVERSATIONS 🚀               ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝
""")
    
    # Load API credentials
    API_ID = os.getenv('API_ID')
    API_HASH = os.getenv('API_HASH')
    
    if not API_ID or not API_HASH:
        print("⚠️  API credentials not found!")
        print("\n📝 How to get API credentials:")
        print("   1. Visit https://my.telegram.org")
        print("   2. Login with your phone number")
        print("   3. Go to 'API Development Tools'")
        print("   4. Create a new application\n")
        
        API_ID = input("Enter API_ID: ").strip()
        API_HASH = input("Enter API_HASH: ").strip()
        
        if not API_ID or not API_HASH:
            print("✗ Both fields are required!")
            return
        
        # Save to .env
        with open('.env', 'w') as f:
            f.write(f"API_ID={API_ID}\n")
            f.write(f"API_HASH={API_HASH}\n")
        
        print("✓ Credentials saved to .env\n")
    
    # Validate API_ID
    try:
        API_ID = int(API_ID)
    except ValueError:
        print("✗ API_ID must be a number!")
        return
    
    # Initialize manager
    manager = UserbotManager()
    manager.load_config()
    
    # Main menu loop
    while True:
        print(f"\n{'='*60}")
        print("📋 MAIN MENU")
        print(f"{'='*60}")
        print("1. 🤖 Add Userbot")
        print("2. 📜 View Userbots")
        print("3. 🗑️  Delete Userbot")
        print("4. 📂 Manage Groups")
        print("5. 🚀 Start Bot (Ultra Natural)")
        print("6. ❌ Exit")
        print(f"{'='*60}")
        
        choice = input("Choose: ").strip()
        
        if choice == '1':
            await manager.add_userbot()
        elif choice == '2':
            manager.show_userbots()
        elif choice == '3':
            await manager.delete_userbot()
        elif choice == '4':
            manager.manage_groups_menu()
        elif choice == '5':
            await manager.start_all()
        elif choice == '6':
            print("\n👋 Thank you for using GameFi Userbot!")
            print("💡 Make sure to stop all bots before exiting\n")
            break
        else:
            print("✗ Invalid choice!")


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⏹️  Stopped by user")
    except Exception as e:
        print(f"\n✗ Fatal error: {e}")
        import traceback
        traceback.print_exc()
