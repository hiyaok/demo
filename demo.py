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
    """Enhanced personality system - BENER-BENER UNIK"""
    
    PERSONALITIES = {
        'trader': {
            'style': 'analitis, suka angka, fokus profit',
            'phrases': ['ROI gue', 'flip ini', 'entry point bagus', 'TP/SL', 'chart lagi bullish', 'cuan nih'],
            'speaking_pattern': 'singkat, to the point, sering sebut angka/persen',
            'emoji_rate': 0.1,
            'response_style': 'data-driven, kasih angka kalo bisa',
            'fallback_phrases': ['hmm profit nya gimana', 'perlu riset dulu', 'liat dulu trend nya']
        },
        'gamer': {
            'style': 'fokus gameplay, skill, meta',
            'phrases': ['grinding seharian', 'clutch banget tadi', 'OP nih build', 'nerf pls', 'buff dong', 'meta berubah'],
            'speaking_pattern': 'semangat, sering pake gaming terms',
            'emoji_rate': 0.2,
            'response_style': 'fokus mechanics, skill, gameplay feel',
            'fallback_phrases': ['gimana gameplay nya', 'skill ceiling tinggi ga', 'balance nya oke ga']
        },
        'casual': {
            'style': 'santai banget, banyak typo, singkatan',
            'phrases': ['wkwk', 'asli sih', 'bro', 'anjir', 'ga si', 'kok gitu', 'lah kok'],
            'speaking_pattern': 'super casual, typo natural, banyak filler words',
            'emoji_rate': 0.15,
            'response_style': 'santai, ga terlalu detail, sering nanya balik',
            'fallback_phrases': ['wkwk bingung', 'lah serius', 'anjir iya juga']
        },
        'researcher': {
            'style': 'detail, suka jelasin panjang, kasih context',
            'phrases': ['soalnya gini', 'basically', 'kalo dipikir-pikir', 'menurut gue ya', 'konteksnya'],
            'speaking_pattern': 'lengkap, suka kasih reasoning, educate',
            'emoji_rate': 0.05,
            'response_style': 'explain dengan detail, kasih pros/cons',
            'fallback_phrases': ['perlu dipahami dulu', 'ada beberapa faktor', 'tergantung konteks']
        },
        'degen': {
            'style': 'risk taker, YOLO, bold moves',
            'phrases': ['all in aja', 'moon incoming', 'wen lambo', 'ngape sih', 'hodl strong', 'diamond hands'],
            'speaking_pattern': 'hype, optimis banget, bold',
            'emoji_rate': 0.3,
            'response_style': 'bullish, fokus upside, risk = opportunity',
            'fallback_phrases': ['yolo aja', 'lambo soon', 'bullish banget']
        }
    }
    
    @staticmethod
    def assign_personality(user_id):
        """Assign consistent personality based on user_id"""
        personalities = list(ConversationPersonality.PERSONALITIES.keys())
        idx = user_id % len(personalities)
        return personalities[idx]
    
    @staticmethod
    def get_phrase(personality_type):
        """Get random phrase with weight"""
        p = ConversationPersonality.PERSONALITIES.get(personality_type)
        if not p:
            return None
        
        if random.random() < 0.4:
            return random.choice(p['phrases'])
        return None
    
    @staticmethod
    def get_fallback(personality_type, context_type='neutral'):
        """Get personality-specific fallback"""
        p = ConversationPersonality.PERSONALITIES.get(personality_type)
        if not p:
            return "hmm iya sih"
        
        base_fallbacks = p['fallback_phrases']
        
        if context_type == 'question':
            return f"{random.choice(base_fallbacks)} ya, {random.choice(['kurang tau juga', 'coba cek dulu', 'gue ga begitu paham'])}"
        elif context_type == 'agree':
            return f"{random.choice(['bener', 'iya', 'setuju'])}, {random.choice(base_fallbacks)}"
        else:
            return random.choice(base_fallbacks)


class GameFiConversationEngine:
    """Engine percakapan yang BENER-BENER NATURAL"""
    
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
        ]
    }
    
    STARTER_TOPICS = [
        "gue liat {token} pump {percent}% dari tadi pagi",
        "floor {game} NFT turun {percent}% guys, kesempatan nih",
        "{token} lagi consolidate ya, prediksi kalian gimana",
        "patch {game} kemarin gimana? worth balik main ga",
        "{game} nambah map baru katanya, udah ada yg coba?",
        "baru flip NFT {game} profit {percent}%",
        "grinding {game} dapet {amount} token hari ini",
        "ada yang main {game}? pengen tau reviewnya",
        "{game} vs {game2}, mendingan mana sih?",
        "denger-denger {game} mau launching season baru",
        "tournament {game} hadiahnya {amount}K, gila",
        "capek juga grinding 8 jam non stop",
        "baru dapet rare drop, jual atau hold ya",
    ]
    
    OFF_TOPICS = [
        "btw ada yang nonton tournament kemarin?",
        "guys internet gue lemot parah hari ini",
        "udah makan siang belom? gue laper nih",
        "capek juga grinding 5 jam straight wkwk",
        "ada recommend VPN yang bagus ga?",
        "gue butuh coffee break dulu kayaknya",
        "laptop gue mulai panas nih, worry",
        "lagi males login game hari ini entah kenapa",
    ]
    
    @staticmethod
    def fill_template(text):
        games = GameFiConversationEngine.REAL_DATA["games"]
        replacements = {
            "{game}": random.choice(games),
            "{game2}": random.choice([g for g in games]),
            "{chain}": random.choice(GameFiConversationEngine.REAL_DATA["chains"]),
            "{token}": random.choice(GameFiConversationEngine.REAL_DATA["tokens"]),
            "{percent}": random.randint(5, 50),
            "{amount}": random.choice([10, 50, 100, 500, "1", "5"]),
        }
        for key, val in replacements.items():
            text = text.replace(key, str(val))
        return text
    
    @staticmethod
    def get_starter():
        if random.random() < 0.15:
            return random.choice(GameFiConversationEngine.OFF_TOPICS)
        topic = random.choice(GameFiConversationEngine.STARTER_TOPICS)
        return GameFiConversationEngine.fill_template(topic)
    
    @staticmethod
    def inject_typo(text):
        if random.random() > 0.25:
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
            except Exception:
                failed.append(f"{group['name']}")
        return {'joined': joined, 'already_in': already, 'failed': failed}


class UserbotManager:
    def __init__(self):
        self.userbots = []
        self.clients = {}
        self.running = False
        self.conversation_history = []
        self.bot_response_history = {}
        self.recent_speakers = []
        self.session_id = f"gf_{int(time.time())}_{random.randint(1000,9999)}"
        self.engine = GameFiConversationEngine()
        self.group_manager = GroupManager(CONFIG_FILE)
        self.external_users = {}
        self.last_external_time = 0
    
    def get_display_name(self, user):
        if hasattr(user, 'first_name') and user.first_name:
            if hasattr(user, 'last_name') and user.last_name:
                return f"{user.first_name} {user.last_name}"
            return user.first_name
        elif hasattr(user, 'username') and user.username:
            return user.username
        return f"User{user.id}"
    
    def load_config(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r') as f:
                    data = json.load(f)
                    self.userbots = data.get('userbots', [])
            except:
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
    
    def build_unique_prompt(self, responder_id, responder_name, personality, context, is_reply, target_msg=None):
        """Build prompt yang BENER-BENER UNIK per bot"""
        p_data = ConversationPersonality.PERSONALITIES[personality]
        
        bot_history = self.bot_response_history.get(responder_id, [])
        recent_responses = bot_history[-5:] if len(bot_history) > 5 else bot_history
        
        prompt = f"""Kamu: {responder_name}
User ID: {responder_id}
Personality: {personality.upper()}

KARAKTERISTIK KAMU:
- Style: {p_data['style']}
- Cara bicara: {p_data['speaking_pattern']}
- Response style: {p_data['response_style']}
- Sering bilang: {', '.join(p_data['phrases'][:3])}

ATURAN KETAT:
1. Bahasa Indonesia SUPER CASUAL (gaul, typo ok, singkatan)
2. Topik: GameFi/Web3 Gaming (games, NFT, tokens)
3. MAX 80 karakter (1-2 kalimat pendek aja)
4. Emoji JARANG (max 1, mostly ga pake)
5. JANGAN formal/kaku
6. JANGAN ulang kata yang baru disebutkan
7. JANGAN sebut nama orang kecuali perlu
8. Harus BEDA dari responses kamu sebelumnya

"""
        
        if recent_responses:
            prompt += f"RESPONSES KAMU SEBELUMNYA (JANGAN MIRIP!):\n"
            for resp in recent_responses:
                prompt += f"- {resp}\n"
            prompt += "\n"
        
        prompt += f"PERCAKAPAN TERAKHIR:\n{context}\n\n"
        
        if is_reply and target_msg:
            prompt += f"""TUGAS: Reply ke {target_msg['name']} yang bilang "{target_msg['text']}"

Sebagai {personality.upper()}, kamu harus respond dengan cara yang SESUAI personality:
- Trader: fokus angka/profit angle
- Gamer: fokus gameplay/mechanics
- Casual: santai, ga terlalu deep
- Researcher: kasih context/explain
- Degen: optimis/bullish

Response HARUS:
✓ Sesuai personality {personality}
✓ Nyambung dengan "{target_msg['text']}"
✓ BEDA dari response kamu sebelumnya
✓ Natural dan casual

RESPOND SEKARANG:"""
        else:
            prompt += f"""TUGAS: Mulai topik baru ATAU expand topik yang lagi dibahas

Sebagai {personality.upper()}, pilih yang sesuai personality:
- Trader: kasih market insight/analysis
- Gamer: share gameplay experience
- Casual: nanya atau comment santai
- Researcher: kasih info/fun fact
- Degen: hype something up

Response HARUS:
✓ Sesuai personality {personality}
✓ BEDA dari response kamu sebelumnya
✓ Natural dan nyambung

RESPOND SEKARANG:"""
        
        return prompt
    
    async def call_ai(self, prompt, responder_id):
        """Call AI dengan tracking dan retry"""
        max_retries = 2
        for attempt in range(max_retries):
            try:
                url = "https://api.ryzumi.vip/api/ai/deepseek"
                params = {
                    'text': prompt,
                    'prompt': 'Respond VERY casually in Indonesian. Be brief, natural, match the personality.',
                    'session': f"{self.session_id}_{responder_id}"
                }
                response = requests.get(url, params=params, timeout=12)
                if response.status_code == 200:
                    data = response.json()
                    result = data.get('result', data.get('response', ''))
                    if result:
                        result = result.strip().strip('"\'')
                        result = re.sub(r'\*\*?', '', result)
                        if 10 < len(result) < 120:
                            if responder_id not in self.bot_response_history:
                                self.bot_response_history[responder_id] = []
                            self.bot_response_history[responder_id].append(result)
                            if len(self.bot_response_history[responder_id]) > 10:
                                self.bot_response_history[responder_id] = self.bot_response_history[responder_id][-10:]
                            return result
                if attempt < max_retries - 1:
                    await asyncio.sleep(1)
            except Exception:
                if attempt < max_retries - 1:
                    await asyncio.sleep(1)
        return None
    
    def get_smart_fallback(self, personality, context_type, target_text=None):
        """Smart fallback dengan personality injection"""
        base = ConversationPersonality.get_fallback(personality, context_type)
        
        phrase = ConversationPersonality.get_phrase(personality)
        if phrase and random.random() < 0.5:
            return f"{base}, {phrase}"
        
        return base
    
    async def send_typing(self, client, chat, msg, reply_to=None):
        try:
            words = len(msg.split())
            chars = len(msg)
            base_time = (chars / 5) / random.uniform(40, 60) * 60
            typing_time = min(base_time * random.uniform(0.8, 1.2), 5)
            async with client.action(chat, 'typing'):
                await asyncio.sleep(typing_time)
            sent_msg = await client.send_message(chat, msg, reply_to=reply_to)
            return sent_msg
        except Exception as e:
            print(f"✗ Send error: {e}")
            return None
    
    async def check_external_messages(self, chat_id):
        current_time = time.time()
        if current_time - self.last_external_time < 30:
            return []
        self.last_external_time = current_time
        try:
            bot_id = random.choice(list(self.clients.keys()))
            client = self.clients[bot_id]['client']
            messages = await client.get_messages(chat_id, limit=10)
            external = []
            bot_ids = set(self.clients.keys())
            for msg in messages:
                if msg.sender_id in bot_ids:
                    continue
                if msg.text and (current_time - msg.date.timestamp()) < 120:
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
                    if msg.sender_id not in self.external_users:
                        self.external_users[msg.sender_id] = {
                            'name': sender_name,
                            'first_seen': current_time,
                            'message_count': 1
                        }
                    else:
                        self.external_users[msg.sender_id]['message_count'] += 1
            return external
        except:
            return []
    
    def select_responder(self, bot_ids, exclude_ids=None):
        if exclude_ids is None:
            exclude_ids = []
        exclude_ids.extend(self.recent_speakers[-3:])
        available = [bid for bid in bot_ids if bid not in exclude_ids]
        if not available:
            available = bot_ids
        return random.choice(available)
    
    def build_context(self, max_msgs=8):
        recent = self.conversation_history[-max_msgs:] if len(self.conversation_history) > max_msgs else self.conversation_history
        if not recent:
            return "GRUP BARU SEPI"
        context = ""
        for msg in recent:
            context += f"{msg['name']}: {msg['text']}\n"
        return context.strip()
    
    async def generate_conversation(self, chat_id):
        bot_ids = list(self.clients.keys())
        if len(bot_ids) < 2:
            return
        
        print(f"\n{'='*60}")
        print(f"🎬 NEW SESSION - PERSONALITY-DRIVEN")
        print(f"{'='*60}\n")
        
        # STARTER
        starter_id = random.choice(bot_ids)
        starter_client = self.clients[starter_id]['client']
        starter_name = self.clients[starter_id]['name']
        starter_personality = self.clients[starter_id]['personality']
        
        starter_msg = self.engine.get_starter()
        starter_msg = self.engine.inject_typo(starter_msg)
        
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
        
        if starter_id not in self.bot_response_history:
            self.bot_response_history[starter_id] = []
        self.bot_response_history[starter_id].append(starter_msg)
        
        await asyncio.sleep(random.uniform(2, 6))
        
        # CONVERSATION FLOW
        num_messages = random.randint(18, 30)
        
        for turn in range(num_messages):
            # Check external messages
            if turn % random.randint(4, 6) == 0:
                external = await self.check_external_messages(chat_id)
                if external:
                    ext_msg = external[0]
                    print(f"\n🔔 External: {ext_msg['sender_name']}: {ext_msg['text']}")
                    
                    responder_id = self.select_responder(bot_ids, [self.recent_speakers[-1]] if self.recent_speakers else [])
                    responder_client = self.clients[responder_id]['client']
                    responder_name = self.clients[responder_id]['name']
                    responder_personality = self.clients[responder_id]['personality']
                    
                    context = self.build_context()
                    context += f"\n\nUSER EXTERNAL: {ext_msg['sender_name']} bilang: \"{ext_msg['text']}\""
                    
                    prompt = self.build_unique_prompt(
                        responder_id,
                        responder_name,
                        responder_personality,
                        context,
                        True,
                        {'name': ext_msg['sender_name'], 'text': ext_msg['text']}
                    )
                    
                    ai_response = await self.call_ai(prompt, responder_id)
                    
                    if not ai_response:
                        if '?' in ext_msg['text']:
                            response_text = self.get_smart_fallback(responder_personality, 'question', ext_msg['text'])
                        else:
                            response_text = self.get_smart_fallback(responder_personality, 'neutral')
                    else:
                        response_text = ai_response
                    
                    response_text = self.engine.inject_typo(response_text)
                    print(f"📤 {responder_name} [{responder_personality}] ↩️ {ext_msg['sender_name']}: {response_text}")
                    
                    sent = await self.send_typing(responder_client, chat_id, response_text, reply_to=ext_msg.get('msg_obj'))
                    
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
                    
                    await asyncio.sleep(random.uniform(2, 5))
                    continue
            
            # SELECT RESPONDER
            responder_id = self.select_responder(bot_ids)
            responder_client = self.clients[responder_id]['client']
            responder_name = self.clients[responder_id]['name']
            responder_personality = self.clients[responder_id]['personality']
            
            # Decision logic
            decision = random.choices(
                ['reply', 'standalone', 'off_topic'],
                weights=[0.65, 0.25, 0.10]
            )[0]
            
            context = self.build_context()
            response_text = None
            reply_to = None
            
            if decision == 'off_topic':
                response_text = random.choice(self.engine.OFF_TOPICS)
                print(f"📤 {responder_name} [{responder_personality}] [OFF-TOPIC]: {response_text}")
                
            elif decision == 'reply':
                possible_targets = [
                    h for h in self.conversation_history[-6:] 
                    if h['user_id'] != responder_id
                ]
                
                if not possible_targets:
                    decision = 'standalone'
                else:
                    weights = [i+1 for i in range(len(possible_targets))]
                    target = random.choices(possible_targets, weights=weights)[0]
                    
                    prompt = self.build_unique_prompt(
                        responder_id,
                        responder_name,
                        responder_personality,
                        context,
                        True,
                        target
                    )
                    
                    ai_response = await self.call_ai(prompt, responder_id)
                    if ai_response:
                        response_text = ai_response
                    else:
                        if '?' in target['text']:
                            response_text = self.get_smart_fallback(responder_personality, 'question', target['text'])
                        else:
                            response_text = self.get_smart_fallback(responder_personality, 'neutral')
                    
                    response_text = self.engine.inject_typo(response_text)
                    reply_to = target['msg_obj']
                    print(f"📤 {responder_name} [{responder_personality}] ↩️ {target['name']}: {response_text}")
            
            if decision == 'standalone':
                prompt = self.build_unique_prompt(
                    responder_id,
                    responder_name,
                    responder_personality,
                    context,
                    False
                )
                
                ai_response = await self.call_ai(prompt, responder_id)
                if ai_response:
                    response_text = ai_response
                else:
                    templates = [
                        f"btw gue baru coba {random.choice(self.engine.REAL_DATA['games'])}",
                        f"{random.choice(self.engine.REAL_DATA['tokens'])} movement nya aneh hari ini",
                        f"ada yang grinding {random.choice(self.engine.REAL_DATA['games'])}?",
                    ]
                    response_text = random.choice(templates)
                
                response_text = self.engine.inject_typo(response_text)
                print(f"📤 {responder_name} [{responder_personality}]: {response_text}")
            
            # SEND message
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
            
            # DYNAMIC DELAY
            delay_patterns = {
                'instant': (0.5, 1.5),
                'quick': (2, 4),
                'normal': (4, 8),
                'thinking': (8, 12),
                'slow': (12, 20),
            }
            
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
        """Run continuously dengan maintenance"""
        session_count = 0
        
        try:
            while self.running:
                session_count += 1
                print(f"\n{'🔥'*3} SESSION #{session_count} {'🔥'*3}")
                
                await self.generate_conversation(chat_id)
                
                # BREAK
                break_patterns = {
                    'micro': (20, 60),
                    'short': (60, 180),
                    'medium': (180, 300),
                    'long': (300, 600),
                }
                
                pattern = random.choices(
                    list(break_patterns.keys()),
                    weights=[0.25, 0.45, 0.20, 0.10]
                )[0]
                
                break_time = random.uniform(*break_patterns[pattern])
                mins = int(break_time // 60)
                secs = int(break_time % 60)
                print(f"⏸️  Break: {mins}m {secs}s ({pattern})\n")
                
                await asyncio.sleep(break_time)
                
                # MAINTENANCE
                if session_count % 5 == 0:
                    print(f"🔧 Maintenance...")
                    self.session_id = f"gf_{int(time.time())}_{random.randint(1000,9999)}"
                    
                    if len(self.conversation_history) > 30:
                        self.conversation_history = self.conversation_history[-20:]
                    
                    for bot_id in self.bot_response_history:
                        if len(self.bot_response_history[bot_id]) > 10:
                            self.bot_response_history[bot_id] = self.bot_response_history[bot_id][-10:]
                    
                    current_time = time.time()
                    self.external_users = {
                        uid: data for uid, data in self.external_users.items()
                        if current_time - data['first_seen'] < 3600
                    }
                    
                    print(f"✓ Maintenance complete\n")
                
        except KeyboardInterrupt:
            print("\n\n⏹️  Stopped by user")
        except Exception as e:
            print(f"\n✗ Error: {e}")
            import traceback
            traceback.print_exc()
        finally:
            self.running = False
    
    async def start_all(self):
        """Start all bots"""
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
                    personality = ConversationPersonality.assign_personality(me.id)
                    
                    self.clients[me.id] = {
                        'client': client,
                        'name': name,
                        'username': me.username or "no_username",
                        'personality': personality
                    }
                    
                    self.bot_response_history[me.id] = []
                    
                    print(f"✓ {name} (@{me.username}) - Personality: {personality.upper()}")
                    
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
        print(f"🤖 Mode: PERSONALITY-DRIVEN v3.0")
        print(f"{'='*60}")
        print("✅ Unique personality per bot")
        print("✅ AI dengan prompt berbeda per bot")
        print("✅ Response history tracking")
        print("✅ NO self-reply (strict)")
        print("✅ NO repetition (tracked)")
        print("✅ Context-aware fallbacks")
        print("✅ Auto-respond external users")
        print("✅ Natural typos & delays")
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
║     🎮 GAMEFI USERBOT ULTIMATE v3.0 🎮                   ║
║                                                           ║
║     ✅ Unique Personality System (5 types)               ║
║     ✅ AI dengan Prompt Berbeda Per Bot                  ║
║     ✅ Response History Tracking                         ║
║     ✅ 100% NO Self-Reply                                ║
║     ✅ NO Repetition (Smart Tracking)                    ║
║     ✅ Context-Aware Fallbacks                           ║
║     ✅ Auto-Respond External Users                       ║
║     ✅ Natural Typos & Delays                            ║
║                                                           ║
║     🚀 PERFECT UNIQUE CONVERSATIONS 🚀                   ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝
""")
    
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
        
        with open('.env', 'w') as f:
            f.write(f"API_ID={API_ID}\n")
            f.write(f"API_HASH={API_HASH}\n")
        
        print("✓ Credentials saved to .env\n")
    
    try:
        API_ID = int(API_ID)
    except ValueError:
        print("✗ API_ID must be a number!")
        return
    
    manager = UserbotManager()
    manager.load_config()
    
    while True:
        print(f"\n{'='*60}")
        print("📋 MAIN MENU")
        print(f"{'='*60}")
        print("1. 🤖 Add Userbot")
        print("2. 📜 View Userbots")
        print("3. 🗑️  Delete Userbot")
        print("4. 📂 Manage Groups")
        print("5. 🚀 Start Bot (Personality-Driven)")
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
