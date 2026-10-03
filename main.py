# ═══════════════════════════════════════════════════════════════════
#  💧 KATRE BOT v6.1 — BÖLÜM 1/2 • GELİŞMİŞ TİCKET • SELECT PANEL • PREMIUM KART • V2 YARDIM
#  ENV: BOT_TOKEN, OWNER_ID, SUPPORT_URL, BACKUP_CHANNEL_ID, OPENAI_API_KEY, OPENAI_IMAGE_MODEL, HF_TOKEN, HF_IMAGE_MODEL, AI_PROVIDER
#  requirements.txt: discord.py>=2.6.0, aiohttp>=3.9.0, huggingface_hub>=1.1.2
# ═══════════════════════════════════════════════════════════════════
import discord
from discord.ext import commands, tasks
from discord.ui import View, Button, Select, Modal, TextInput
import time, sqlite3, os, sys, json, random, asyncio, datetime, traceback, textwrap, io, re, inspect, urllib.parse, base64
import aiohttp
try:
    from huggingface_hub import InferenceClient
except Exception:
    InferenceClient = None
from collections import deque
from contextlib import redirect_stdout
try:
    from discord.ui import Container, TextDisplay, LayoutView
except Exception:
    try:
        from discord.ui import Container, TextDisplay
        LayoutView = None
    except Exception:
        Container = None; TextDisplay = None; LayoutView = None
try:
    from discord.ui import Separator
except Exception:
    Separator = None
HAS_V2 = bool(Container) and bool(LayoutView)
try:
    from discord.ui import ActionRow
except Exception:
    ActionRow = None
try:
    from discord.ui import Section, Thumbnail
except Exception:
    Section = None; Thumbnail = None
V2_OK = HAS_V2 and ActionRow is not None
BOT_TOKEN = os.getenv("BOT_TOKEN", "BURAYA_TOKEN")
OWNER_ID = int(os.getenv("OWNER_ID", "0"))
SUPPORT_URL = os.getenv("SUPPORT_URL", "https://discord.gg/katre")
DB_PATH = os.getenv("DB_PATH", "katre.db")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip()
OPENAI_IMAGE_MODEL = os.getenv("OPENAI_IMAGE_MODEL", "gpt-image-2").strip() or "gpt-image-2"
HF_TOKEN = os.getenv("HF_TOKEN", "").strip()
HF_IMAGE_MODEL = os.getenv("HF_IMAGE_MODEL", "black-forest-labs/FLUX.1-schnell").strip() or "black-forest-labs/FLUX.1-schnell"
AI_PROVIDER = os.getenv("AI_PROVIDER", "auto").strip().lower() or "auto"
AI_FREE_DAILY_LIMIT = 7
BACKUP_CH = int(os.getenv("BACKUP_CHANNEL_ID", "0"))
MARKER = "#KATRE_YEDEK"
DIV = "──────────────────────────────"
PAGE_SIZE = 15
BOT_VERSION = "6.4"
CHANGELOG = {
    "6.3": [
        "📚 Full log kapsamı genişletildi: ban/unban, timeout, üye rol/nick değişimi, kanal/rol, davet, webhook, thread, emoji/sticker ve komut olayları",
        "🧪 `k!logtest`, `k!logkapat`, `k!logtemizle` ve `k!logdetay` eklendi",
        "👋 Hoş geldin/ayrılma mesajları Components V2 kartları olarak gönderiliyor",
        "🎨 Hoş geldin/ayrılma mesajları için özel şablon, değişkenler, test ve bilgi komutları eklendi",
        "⚙️ Log türleri ayrı ayrı kanallara yönlendirilebiliyor; `hepsi` ile tek kanala bağlanabiliyor",
    ],
    "6.1": [
        "👋 Hoş geldin ve ayrılma mesajları ayrı ayrı kanal seçilebilir hale getirildi",
        "🎭 Select rol paneli geliştirildi; `k!rolpanel` ve `k!selectrol` ile kullanılabilir",
        "🔁 Reaction Role sistemi eklendi: emoji ile rol verme/alma",
        "📚 Tam log sistemi eklendi: üye, mesaj, moderasyon, rol, kanal, ses, ticket ve sunucu olayları ayrı kanallara yönlendirilebilir",
        "⚙️ `k!logayarla` ve `k!loglar` ile log kanalları tamamen ayarlanabilir",
    ],
    "5.9": [
        "🐛 Ticket panelindeki Components V2 `view parameter must be View not Container` hatası düzeltildi",
        "🎫 Ticket paneli artık LayoutView içinde güvenli şekilde gönderiliyor",
        "👑 Owner için `ownerbilgi`, `sunucusay` ve `guildbilgi` komutları eklendi",
        "🛡️ Half Owner için `halfownerbilgi`, `protopluver` ve `protoplual` komutları eklendi",
        "🔐 Half Owner/Owner komutlarında hedef rol ve yetki kontrolleri sıkılaştırıldı",
    ],
    "5.8": [
        "🧹 `k!resim` kaldırıldı",
        "🎫 Ticket paneli select menüye geçti; formda öncelik seçimi eklendi",
        "👮 Ticket üstlenildikten sonra Administrator olmayan diğer yetkililer yazamaz",
        "⚙️ Ticket yetkili rolleri `k!ticketayar` ile ayarlanabilir",
        "📢 Ticket açılışında ve üstlenildiğinde bilgilendirme mesajları doğrudan kanala gönderilir",
    ],
    "5.7": [
        "🆓 Free AI görsel sağlayıcısı eklendi: Hugging Face Inference Providers + FLUX.1-schnell",
        "🤖 `k!resim` artık AI_PROVIDER ile Hugging Face/OpenAI arasında seçim yapabiliyor",
        "📊 Free günlük **7** kullanım korunuyor; başarısız üretimde hak otomatik iade ediliyor",
        "💎 Pro kullanıcılarında OpenAI anahtarı varsa premium sağlayıcı önceliklendiriliyor",
        "🎛️ `k!butonrol` sistemi geliştirildi: rol hiyerarşisi, bot yetkisi, bozuk rol temizliği ve daha güvenli toggle",
        "🧹 `k!butonrolsil` ve `k!butonrollist` komutları eklendi",
        "🧩 Rol butonları yeniden başlatmadan sonra kalıcı olarak geri yükleniyor",
        "🛡️ Buton etkileşimlerinde Discord rol yönetme hataları kullanıcıya açıklanıyor",
    ],
    "5.6": [
        "🤖 `k!resim <prompt>` eklendi: OpenAI görsel üretimi ile AI resim oluşturur",
        "📊 AI resim kullanım limiti eklendi: Free günlük **7**, Pro **sınırsız**",
        "🛡️ Limit sistemi başarısız üretimlerde hakkı geri verir ve gün bazlı sıfırlanır",
        "🎁 Çekiliş panelindeki yönetim butonları kaldırıldı; panel yalnızca katılım için kullanılıyor",
        "📝 Çekilişler oluşturan kişi veya sunucu yöneticileri tarafından `k!çekilişdüzenle` ile düzenlenebiliyor",
        "🔧 `k!çekilişbitir`, `k!çekilişiptal` ve `k!çekilişyenile` artık çekiliş sahibi veya yöneticiler tarafından kullanılabiliyor",
        "🐛 Çekiliş yeniden çekiliş etkileşimindeki çift-response hatası giderildi",
        "💎 `k!pro` panelinde AI resim Free/Pro limitleri açıkça gösteriliyor",
    ],
    "5.5": [
        "🛠️ Yardım menüsünde kategori seçimi düzeltildi: menüden seçince kategori artık açılıyor",
        "📌 Yardım menüsünde seçili kategori işaretleniyor, ana menüde rastgele ipucu gösteriliyor",
        "✨ Rank, profil ve sunucu kartları avatar/ikonlu yeni tasarıma geçti; rank'a sıralama ve kalan XP eklendi",
        "👋 Hoş geldin mesajı avatarlı kart oldu, hesap yaşı gösteriliyor",
        "🏓 `k!ping` artık websocket ve mesaj gecikmesini kalite çubuğuyla gösteriyor",
        "🆕 Yeni komutlar: `k!kullanıcıbilgi`, `k!kanalbilgi`, `k!botbilgi`, `k!hesapla`, `k!sarıl`, `k!ipucu`",
    ],
    "5.4": [
        "🎨 Tüm cevaplar yeni premium kart tasarımında: büyük başlık, ayırıcı, içerik ve duruma göre alt bilgi",
        "🌈 Cevap türüne göre özel renk şeridi: başarılı, hata, uyarı, ekonomi, ticket, eğlence ve daha fazlası",
        "✅ Başarılı işlem ve buton cevapları artık ne olduğunu açıkça anlatıyor",
        "🎫 Ticket paneli V2'ye geçti: Destek, Şikayet, Öneri ve Ortaklık türleri, numaralı talepler",
        "🧾 Ticket içinde Üstlen, Transkript ve Kapat butonları; kapanışta kayıt log kanalına ve talep sahibine DM olarak gider",
        "👥 `k!ticket ekle` / `k!ticket çıkar` ile talebe üye ekleyip çıkarabilirsin",
        "📖 `k!yardım` V2 kart oldu: kategoriye özel renk, sayfa gezinme ve hızlı linkler",
        "🆕 Sürüm güncelleme duyurusu yeni kart tasarımıyla geliyor",
    ],
    "5.3": [
        "🎨 Tüm cevaplar yeni kart stilinde: renkli şerit (yeşil/kırmızı/sarı) + başlık + ayırıcı + açıklama",
        "💬 Hata mesajları açıklayıcı: eksik argüman, geçersiz üye/rol/kanal ve bekleme süresi artık net anlatılıyor",
        "📖 Kelime oyunu artık TDK sözlüğüyle doğrulanıyor (özel isimler kabul edilmez)",
        "⏱️ Kelime oyununa cooldown sistemi eklendi",
        "📩 Hatalı kelime kanalda silinir, açıklama DM'den gelir",
    ],
    "5.2": ["📣 k!duyuru: Owner+HalfOwner → tüm sunucu sahiplerine DM", "🎨 Cevaplar gri alıntı kartı stilinde", "🧩 V2 yardım + v2test yetenek raporu", "📖 Kelime türetme oyunu"],
}

class DB:
    def __init__(self, path):
        self.conn = sqlite3.connect(path, check_same_thread=False); self.conn.row_factory = sqlite3.Row
        c = self.conn.cursor()
        c.executescript("""
        CREATE TABLE IF NOT EXISTS servers(guild_id INTEGER PRIMARY KEY, prefix TEXT DEFAULT 'k!', welcome_ch INTEGER, leave_ch INTEGER, auto_role INTEGER, rank_on INTEGER DEFAULT 1, joined_at TEXT, welcome_message TEXT, leave_message TEXT);
        CREATE TABLE IF NOT EXISTS users(user_id INTEGER PRIMARY KEY, name TEXT, xp INTEGER DEFAULT 0, level INTEGER DEFAULT 1, coins INTEGER DEFAULT 0, messages INTEGER DEFAULT 0, warnings INTEGER DEFAULT 0, pro INTEGER DEFAULT 0, pro_expiry TEXT, pro_color TEXT, pro_tag TEXT, xp2 INTEGER DEFAULT 0, birthday TEXT, notes TEXT DEFAULT '[]', rep INTEGER DEFAULT 0);
        CREATE TABLE IF NOT EXISTS owner_settings(id INTEGER PRIMARY KEY DEFAULT 1, maintenance INTEGER DEFAULT 0);
        CREATE TABLE IF NOT EXISTS bot_meta(key TEXT PRIMARY KEY, value TEXT);
        CREATE TABLE IF NOT EXISTS half_owners(user_id INTEGER PRIMARY KEY, since TEXT, added_by INTEGER);
        CREATE TABLE IF NOT EXISTS giveaways(message_id INTEGER PRIMARY KEY, guild_id INTEGER, channel_id INTEGER, prize TEXT, winners INTEGER, end_time REAL, participants TEXT DEFAULT '[]', status TEXT DEFAULT 'active', host INTEGER);\n        CREATE TABLE IF NOT EXISTS ai_usage(user_id INTEGER NOT NULL, usage_day TEXT NOT NULL, uses INTEGER DEFAULT 0, PRIMARY KEY(user_id, usage_day));
        CREATE TABLE IF NOT EXISTS tickets(channel_id INTEGER PRIMARY KEY, guild_id INTEGER, user_id INTEGER, claimed_by INTEGER, status TEXT DEFAULT 'open');
        CREATE TABLE IF NOT EXISTS ticket_settings(guild_id INTEGER PRIMARY KEY, staff_roles TEXT DEFAULT '[]', panel_channel INTEGER);
        CREATE TABLE IF NOT EXISTS role_menus(menu_id TEXT PRIMARY KEY, guild_id INTEGER, channel_id INTEGER, message_id INTEGER, title TEXT, role_ids TEXT);
        CREATE TABLE IF NOT EXISTS blacklist(user_id INTEGER PRIMARY KEY, reason TEXT);
        CREATE TABLE IF NOT EXISTS cmd_stats(cmd TEXT PRIMARY KEY, uses INTEGER DEFAULT 0);
        CREATE TABLE IF NOT EXISTS protections(guild_id INTEGER PRIMARY KEY, anti_spam INTEGER DEFAULT 0, anti_flood INTEGER DEFAULT 0, anti_raid INTEGER DEFAULT 0, anti_link INTEGER DEFAULT 0, badword INTEGER DEFAULT 0, log_ch INTEGER, raid_until REAL DEFAULT 0);
        CREATE TABLE IF NOT EXISTS badwords(guild_id INTEGER, word TEXT, PRIMARY KEY(guild_id, word));
        CREATE TABLE IF NOT EXISTS pro_logs(id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, action TEXT, days INTEGER DEFAULT 0, by_id INTEGER, ts TEXT);
        CREATE TABLE IF NOT EXISTS afk(user_id INTEGER PRIMARY KEY, reason TEXT, since TEXT, mentions INTEGER DEFAULT 0);
        CREATE TABLE IF NOT EXISTS snipe(channel_id INTEGER PRIMARY KEY, author_id INTEGER, content TEXT, attachment TEXT, ts TEXT);
        CREATE TABLE IF NOT EXISTS marriages(id INTEGER PRIMARY KEY AUTOINCREMENT, user1 INTEGER, user2 INTEGER, since TEXT);
        CREATE TABLE IF NOT EXISTS applications(id INTEGER PRIMARY KEY AUTOINCREMENT, guild_id INTEGER, user_id INTEGER, message_id INTEGER, status TEXT DEFAULT 'pending', answers TEXT, ts TEXT);
        CREATE TABLE IF NOT EXISTS app_settings(guild_id INTEGER PRIMARY KEY, log_ch INTEGER, staff_role INTEGER);
        CREATE TABLE IF NOT EXISTS auto_replies(guild_id INTEGER, trigger TEXT, response TEXT, PRIMARY KEY(guild_id, trigger));
        CREATE TABLE IF NOT EXISTS counters(guild_id INTEGER PRIMARY KEY, target INTEGER, channel_id INTEGER, reached INTEGER DEFAULT 0);
        CREATE TABLE IF NOT EXISTS level_roles(id INTEGER PRIMARY KEY AUTOINCREMENT, guild_id INTEGER, level INTEGER, role_id INTEGER);
        CREATE TABLE IF NOT EXISTS guild_logs(guild_id INTEGER PRIMARY KEY, channel_id INTEGER);
        CREATE TABLE IF NOT EXISTS log_channels(guild_id INTEGER NOT NULL, event TEXT NOT NULL, channel_id INTEGER, PRIMARY KEY(guild_id,event));
        CREATE TABLE IF NOT EXISTS reaction_roles(message_id INTEGER NOT NULL, guild_id INTEGER NOT NULL, channel_id INTEGER NOT NULL, emoji TEXT NOT NULL, role_id INTEGER NOT NULL, PRIMARY KEY(message_id,emoji));
        CREATE TABLE IF NOT EXISTS emojis(slot TEXT PRIMARY KEY, emoji TEXT);
        CREATE TABLE IF NOT EXISTS tempvoice(guild_id INTEGER PRIMARY KEY, trigger_ch INTEGER, category_id INTEGER);
        CREATE TABLE IF NOT EXISTS temp_channels(channel_id INTEGER PRIMARY KEY, owner_id INTEGER, guild_id INTEGER);
        CREATE TABLE IF NOT EXISTS punishments(id INTEGER PRIMARY KEY AUTOINCREMENT, guild_id INTEGER, user_id INTEGER, type TEXT, reason TEXT, by_id INTEGER, ts TEXT, duration INTEGER);
        CREATE TABLE IF NOT EXISTS punish_config(guild_id INTEGER PRIMARY KEY, mute_at INTEGER DEFAULT 3, ban_at INTEGER DEFAULT 5);
        CREATE TABLE IF NOT EXISTS polls(id INTEGER PRIMARY KEY AUTOINCREMENT, guild_id INTEGER, channel_id INTEGER, message_id INTEGER DEFAULT 0, question TEXT, options TEXT, votes TEXT DEFAULT '{}', status TEXT DEFAULT 'active', creator INTEGER, ts TEXT);
        CREATE TABLE IF NOT EXISTS wordgame(guild_id INTEGER PRIMARY KEY, channel_id INTEGER, last_word TEXT, last_user INTEGER, streak INTEGER DEFAULT 0);
        INSERT OR IGNORE INTO owner_settings(id) VALUES (1);""")
        for t, col, ty in (("servers","leave_ch","INTEGER"),("servers","welcome_message","TEXT"),("servers","leave_message","TEXT"),("users","pro_tag","TEXT"),("users","xp2","INTEGER DEFAULT 0"),("tickets","claimed_by","INTEGER"),("afk","mentions","INTEGER DEFAULT 0"),("tickets","subject","TEXT"),("tickets","category","TEXT"),("tickets","created_at","TEXT"),("tickets","number","INTEGER"),("tickets","description","TEXT"),("tickets","priority","TEXT DEFAULT 'normal'"),("role_menus","channel_id","INTEGER"),("role_menus","message_id","INTEGER"),("role_menus","title","TEXT")):
            try: c.execute("ALTER TABLE " + t + " ADD COLUMN " + col + " " + ty)
            except sqlite3.OperationalError: pass
        self.conn.commit()
    def q(self, sql, p=()):
        c = self.conn.cursor(); c.execute(sql, p); self.conn.commit(); return c
    def one(self, sql, p=()):
        r = self.q(sql, p).fetchone(); return dict(r) if r else None
    def all(self, sql, p=()): return [dict(r) for r in self.q(sql, p).fetchall()]

db = DB(DB_PATH)
def ensure_user(u, n): db.q("INSERT OR IGNORE INTO users(user_id,name) VALUES(?,?)", (u, n))
def ensure_server(g): db.q("INSERT OR IGNORE INTO servers(guild_id) VALUES(?)", (g,))
def pro_log(u, a, d=0, b=0): db.q("INSERT INTO pro_logs(user_id,action,days,by_id,ts) VALUES(?,?,?,?,?)", (u, a, d, b, datetime.datetime.now().isoformat()))
def punish_log(g, u, t, r, b, d=None): db.q("INSERT INTO punishments(guild_id,user_id,type,reason,by_id,ts,duration) VALUES(?,?,?,?,?,?,?)", (g, u, t, r, b, datetime.datetime.now().isoformat(), d))
def is_half_owner(u): return db.one("SELECT 1 FROM half_owners WHERE user_id=?", (u,)) is not None
def is_maintenance():
    r = db.one("SELECT maintenance FROM owner_settings WHERE id=1"); return bool(r and r["maintenance"])
def mod_guard(ctx, t, v):
    if t.id == ctx.author.id: return "Kendini " + v + " edemezsin!"
    if t.id == OWNER_ID: return "Bot sahibine işlem yapamazsın!"
    if is_half_owner(t.id): return "Half Owner'a işlem yapamazsın!"
    if t.id == ctx.bot.user.id: return "Bota işlem yapamazsın!"
    if t.id == ctx.guild.owner_id: return "Sunucu sahibine işlem yapamazsın!"
    if ctx.author.top_role <= t.top_role: return "Aynı/üst yetkiliye işlem yapamazsın!"
    return None

SLOTS = {"logo":"💧","check":"✅","cross":"❌","warn":"⚠️","info":"ℹ️","dot":"•","arrow":"»","star":"🌟","spark":"✨","crown":"👑","diamond":"💎","coin":"🪙","money":"💰","gift":"🎁","party":"🎉","shield":"🛡️","hammer":"🔨","kick":"👢","lock":"🔒","unlock":"🔓","gear":"⚙️","chart":"📊","chartup":"📈","heart":"❤️","broken":"💔","ring":"💍","game":"🎮","dice":"🎲","slot":"🎰","fish":"🎣","pick":"⛏️","ticket":"🎫","clip":"📋","pen":"📝","cam":"📸","sleep":"😴","wave":"👋","cake":"🎂","alarm":"⏰","fire":"🔥","bolt":"⚡","mic":"🎙️","palette":"🎨","tag":"🏷️","robot":"🤖","target":"🎯","log":"📜","search":"🔍","time":"⏳","home":"🏠","trash":"🗑️","link":"🔗","genel":"🌐","mod":"🛡️","sys":"📋","eco":"💰","fun":"🎮","give":"🎉","pro":"💎","owner":"👑"}
EMO_MAP = {"check":["check","tick","tik","onay","yes"],"cross":["cross","carp","iptal","hata","error"],"warn":["warn","uyari","alert"],"info":["info","bilgi"],"star":["star","yildiz"],"spark":["spark","parlak"],"crown":["crown","tac","king"],"diamond":["diamond","elmas","gem"],"coin":["coin","para","money"],"gift":["gift","hediye"],"party":["party","parti","tada"],"shield":["shield","kalkan","guard"],"hammer":["hammer","cekic","ban"],"kick":["kick","boot"],"lock":["lock","kilit"],"gear":["gear","ayar","settings"],"chart":["chart","grafik","stats"],"chartup":["chartup","yukselis","level"],"heart":["heart","kalp","love"],"ring":["ring","yuzuk"],"game":["game","oyun"],"dice":["dice","zar"],"slot":["slot","casino"],"fish":["fish","balik"],"pick":["pick","kazma","mine"],"ticket":["ticket","bilet"],"clip":["clip","pano","basvuru"],"pen":["pen","kalem"],"cam":["cam","kamera"],"sleep":["sleep","afk","uyku"],"wave":["wave","el","hello"],"cake":["cake","kek","dogum"],"alarm":["alarm","saat","clock"],"fire":["fire","ates"],"bolt":["bolt","simsek","boost"],"mic":["mic","mikrofon","ses"],"palette":["palette","palet","renk"],"tag":["tag","rozet"],"robot":["robot","bot"],"target":["target","hedef","sayac"],"log":["log","kayit"],"search":["search","ara"],"time":["time","sure"],"home":["home","ana"],"trash":["trash","cop","sil"],"link":["link","baglanti"]}
EMO_CACHE = {}
def refresh_emojis():
    global EMO_CACHE; EMO_CACHE = {r["slot"]: r["emoji"] for r in db.all("SELECT * FROM emojis")}
def e(s): return EMO_CACHE.get(s, SLOTS.get(s, "•"))
refresh_emojis()
def auto_map_emojis(guild):
    mp = {}
    for em in guild.emojis:
        nm = em.name.lower()
        for slot, keys in EMO_MAP.items():
            if slot not in mp and any(k in nm for k in keys): mp[slot] = str(em)
    for s, v in mp.items(): db.q("INSERT OR REPLACE INTO emojis(slot,emoji) VALUES(?,?)", (s, v))
    if mp: refresh_emojis()
    return mp

_HASH = {"emoji": None, "pro": None, "set": None}
SET_TABLES = ["servers","punish_config","protections","app_settings","counters","level_roles","guild_logs","auto_replies","badwords","tempvoice","half_owners"]
def pro_snapshot(): return {"pros": db.all("SELECT user_id,pro_expiry,pro_color,pro_tag,xp2 FROM users WHERE pro=1"), "logs": db.all("SELECT user_id,action,days,by_id,ts FROM pro_logs ORDER BY id")}
def settings_snapshot(): return {t: db.all("SELECT * FROM " + t) for t in SET_TABLES}
def emoji_restore(d):
    for k, v in d.items(): db.q("INSERT OR REPLACE INTO emojis(slot,emoji) VALUES(?,?)", (k, v))
    refresh_emojis(); return len(d)
def pro_restore(d):
    n = 0
    for p in d.get("pros", []):
        db.q("INSERT INTO users(user_id) VALUES(?) ON CONFLICT(user_id) DO UPDATE SET pro=1,pro_expiry=?,pro_color=?,pro_tag=?,xp2=?", (p["user_id"], p["pro_expiry"], p["pro_color"], p["pro_tag"], p["xp2"])); n += 1
    if not db.all("SELECT 1 FROM pro_logs"):
        for l in d.get("logs", []): db.q("INSERT INTO pro_logs(user_id,action,days,by_id,ts) VALUES(?,?,?,?,?)", (l["user_id"], l["action"], l["days"], l["by_id"], l["ts"]))
    return n
def settings_restore(d):
    n = 0
    for t, rows in d.items():
        if t not in SET_TABLES: continue
        for r in rows:
            try:
                db.q("INSERT OR REPLACE INTO " + t + " (" + ", ".join(r.keys()) + ") VALUES (" + ", ".join("?" * len(r)) + ")", tuple(r.values())); n += 1
            except Exception: pass
    return n
async def push_backup(bot, kind, data):
    if not BACKUP_CH: return False
    try:
        ch = bot.get_channel(BACKUP_CH) or await bot.fetch_channel(BACKUP_CH)
        raw = json.dumps(data, separators=(",", ":"), default=str); gen = str(int(datetime.datetime.now().timestamp()))
        chunks = [raw[i:i+1800] for i in range(0, len(raw), 1800)] or ["{}"]
        async for m in ch.history(limit=400):
            if m.author.id == bot.user.id and m.content.startswith(MARKER + " " + kind):
                try: await m.delete()
                except Exception: pass
        for i, c in enumerate(chunks): await ch.send(MARKER + " " + kind + " g" + gen + " [" + str(i) + "/" + str(len(chunks)) + "]\n" + c)
        return True
    except Exception:
        traceback.print_exc(); return False
async def pull_backup(bot, kind):
    if not BACKUP_CH: return None
    try:
        ch = bot.get_channel(BACKUP_CH) or await bot.fetch_channel(BACKUP_CH); gens = {}
        async for m in ch.history(limit=400):
            if m.author.id == bot.user.id and m.content.startswith(MARKER + " " + kind):
                try:
                    hd, body = m.content.split("\n", 1); tk = hd.split()
                    g = tk[2][1:]; i, n = tk[3][1:-1].split("/")
                    gens.setdefault(g, {"n": int(n), "p": {}})["p"][int(i)] = body
                except Exception: pass
        if not gens: return None
        g = max(gens.keys()); rec = gens[g]
        if len(rec["p"]) != rec["n"]: return None
        return json.loads("".join(rec["p"][i] for i in range(rec["n"])))
    except Exception:
        traceback.print_exc(); return None

# ═══════════════════════════════════════════════════════════════════
# 🎨 KART STİLİ (gri alıntı = klasik mod • renkli şeritli kart = V2 mod)
# ═══════════════════════════════════════════════════════════════════
def _q(s): return "\n".join("> " + l for l in str(s).split("\n"))
def head(i, t): return _q(e(i) + " **" + t + "**\n" + DIV)
def OK(t, b=None): return head("check", t) + ("\n" + _q(b) if b else "")
def ER(t, b=None): return head("cross", t) + ("\n" + _q(b) if b else "")
def WN(t, b=None): return head("warn", t) + ("\n" + _q(b) if b else "")
_KFIX = re.compile(r"^(<a?:\w+:\d+>|[^\x00-\x7FçğıöşüÇĞİÖŞÜ]+?)(?=[A-Za-z0-9çğıöşüÇĞİÖŞÜ])")
def _kfix(k): return _KFIX.sub(lambda m: m.group(1) + " ", str(k))
def KV(ps): return _q("\n".join(_kfix(k) + " › **" + str(v) + "**" for k, v in ps))
def bar(p, ln=14):
    p = max(0, min(100, int(p))); f = round(p / 100 * ln); return "`[" + "█" * f + "░" * (ln - f) + "] %" + str(p) + "`"
def parse_sure(t):
    t = str(t).lower().strip()
    for s, m in {"m":1,"dk":1,"h":60,"s":60,"d":1440,"g":1440,"w":10080}.items():
        if t.endswith(s): return int(float(t[:-len(s)]) * m)
    return int(float(t))
def fancy(t):
    o = []
    for ch in t:
        c = ord(ch)
        o.append(chr(c - 97 + 0xFF41) if 97 <= c <= 122 else chr(c - 65 + 0xFF21) if 65 <= c <= 90 else chr(c - 48 + 0xFF10) if 48 <= c <= 57 else ch)
    return "".join(o)
def sure_txt(dk):
    if dk >= 1440: return str(dk // 1440) + " gün " + str((dk % 1440) // 60) + " saat"
    if dk >= 60: return str(dk // 60) + " saat " + str(dk % 60) + " dakika"
    return str(dk) + " dakika"
def sn_txt(sn):
    sn = int(sn) + (1 if sn - int(sn) > 0 else 0)
    if sn >= 3600: return str(sn // 3600) + " saat " + str((sn % 3600) // 60) + " dk"
    if sn >= 60: return str(sn // 60) + " dk " + str(sn % 60) + " sn"
    return str(sn) + " sn"

# ─────────────── Açıklayıcı hata yardımcıları ───────────────
ARG_TR = {"u":"üye","s":"sebep","m":"metin","i":"işlem","ch":"kanal","a":"değer","b":"değer","g":"gün","dk":"dakika","k":"değer","h":"hedef","t2":"sayı","md":"modül","d":"aç/kapat","uid":"kullanıcı-id","role":"rol","ms":"üyeler","rs":"roller","cat":"kategori","süre":"süre","ö":"ödül","arg":"değer","y":"yeni-önek","name":"komut","t":"metin","hedef":"hedef","mod":"aç/kapat","code":"kod","slot":"slot","val":"değer"}
ARG_OVR = {("çekiliş","s"):"süre",("çekiliş","k"):"kazanan-sayısı",("oylama","s"):"soru | seçenek1 | seçenek2",("8ball","s"):"soru",("seç","s"):"seçenekler",("tahmin","s"):"sayı(1-10)",("yavaşmod","s"):"saniye",("seviyerol","s"):"seviye",("transfer","m"):"miktar",("bahis","m"):"miktar",("çekilişbitir","m"):"mesaj-id",("raidmodu","m"):"aç/kapat",("temizle","a"):"adet",("ceza-sistemi","a"):"mute-uyarı-sayısı",("ceza-sistemi","b"):"ban-uyarı-sayısı",("proembed","a"):"başlık | mesaj | renk",("otocevap","a"):"tetik | cevap",("doğumgünü","a"):"ay",("sayaç","h"):"hedef-üye",("prorenk","h"):"hex-renk",("badword","k"):"kelime",("şanslı","t2"):"sayı(1-100)",("koruma","d"):"aç/kapat",("ticket","i"):"kapat/bilgi/listele",("hatırlat","m"):"mesaj",("çekilişdüzenle","s"):"süre",("çekilişdüzenle","k"):"kazanan-sayısı",("çekilişdüzenle","ö"):"ödül",("çekilişbitir","m"):"mesaj-id",("çekilişiptal","m"):"mesaj-id",("çekilişyenile","m"):"mesaj-id"}
def pf(ctx):
    try: return ctx.clean_prefix or "k!"
    except Exception: return "k!"
def arg_label(c, n): return ARG_OVR.get((c.name, n)) or ARG_TR.get(n, n)
def usage_of(ctx):
    c = ctx.command; ps = []
    for n, p in c.clean_params.items():
        lb = arg_label(c, n)
        ps.append(("<" + lb + ">") if p.default is inspect.Parameter.empty else ("[" + lb + "]"))
    return pf(ctx) + c.name + ((" " + " ".join(ps)) if ps else "")
def desc_line(c):
    h = (c.help or "").strip()
    return ("\nAçıklama: " + h) if h and not h.startswith(("<", "[")) else ""

# ─────────────── V2 kart üretici: renkli şerit + başlık + ayırıcı + açıklama ───────────────
ACCENT_SLOTS = [("check",0x57F287),("cross",0xED4245),("warn",0xFEE75C),("party",0xEB459E),("gift",0xEB459E),("give",0xEB459E),
    ("coin",0xF1C40F),("money",0xF1C40F),("eco",0xF1C40F),("crown",0xF1C40F),("owner",0xF1C40F),("diamond",0x00D9FF),("pro",0x00D9FF),
    ("heart",0xFF6B9D),("ring",0xFF6B9D),("broken",0xFF6B9D),("fire",0xFF7A1A),("bolt",0x3498DB),("shield",0xE67E22),("mod",0xE67E22),
    ("hammer",0xE67E22),("kick",0xE67E22),("lock",0xE67E22),("unlock",0x2ECC71),("ticket",0x1ABC9C),("clip",0x1ABC9C),("chart",0x3498DB),
    ("chartup",0x3498DB),("game",0x9B59B6),("dice",0x9B59B6),("slot",0x9B59B6),("fun",0x9B59B6),("fish",0x2ECC71),("pick",0x95A5A6),
    ("star",0xF1C40F),("spark",0xF1C40F),("gear",0x95A5A6),("log",0x95A5A6),("cake",0xEB459E),("alarm",0x3498DB)]
def _accent(title):
    t = str(title).lstrip("#*_> ")
    for slot, col in ACCENT_SLOTS:
        em = e(slot)
        if em and em != "•" and t.startswith(em): return col
    for ch, col in (("✅", 0x57F287), ("❌", 0xED4245), ("⚠", 0xFEE75C)):
        if ch in t[:6]: return col
    return 0x5865F2
def _kind(title):
    t = str(title).lstrip("#*_> ")
    if t.startswith(e("check")) or t.startswith("✅"): return "ok"
    if t.startswith(e("cross")) or t.startswith("❌"): return "er"
    if t.startswith(e("warn")) or t.startswith("⚠"): return "wn"
    return "x"
def _foot(kind):
    base = {"ok": e("check") + " İşlem başarılı", "er": e("cross") + " İşlem tamamlanamadı", "wn": e("warn") + " Dikkat"}.get(kind, e("logo") + " Katre")
    return "-# " + base + " • Katre Bot v" + BOT_VERSION
_KV_RE = re.compile(r"^> (.+ › \*\*.*)$")
def _card_parts(text):
    lines = str(text).split("\n"); out = []; i = 0
    while i < len(lines) and lines[i].startswith(">"):
        l = lines[i][1:]; out.append(l[1:] if l.startswith(" ") else l); i += 1
    out += lines[i:]
    out = [l for l in out if l.strip() != DIV]
    while out and not out[0].strip(): out.pop(0)
    if not out: return " ", ""
    body = [_KV_RE.sub(r"\1", l) for l in out[1:]]
    return out[0], "\n".join(body).strip("\n")
def _sep(con, visible=True):
    if not Separator: return
    try: con.add_item(Separator(visible=visible))
    except Exception: pass
def _new_con(col):
    c = discord.Colour(col)
    try: return Container(accent_colour=c)
    except TypeError:
        try: return Container(accent_color=c)
        except Exception: return Container()
    except Exception: return Container()
def _make_con(text, accent=None, footer=True, rows=()):
    title, rest = _card_parts(text); kind = _kind(title)
    con = _new_con(accent if accent is not None else _accent(title))
    if "**" in title and not title.lstrip().startswith("#"):
        con.add_item(TextDisplay(("## " + title.replace("**", "").strip())[:300]))
        if rest:
            _sep(con); con.add_item(TextDisplay(rest[:3400]))
    else:
        con.add_item(TextDisplay((title + (("\n" + rest) if rest else ""))[:3800]))
    for r in rows: con.add_item(r)
    if footer:
        _sep(con, False); con.add_item(TextDisplay(_foot(kind)))
    return con
def _make_lv(text):
    try: lv = LayoutView(timeout=None)
    except TypeError: lv = LayoutView()
    lv.add_item(_make_con(text)); return lv

def _row(*items):
    r = ActionRow()
    for it in items: r.add_item(it)
    return r
def mkbtn(label, cb=None, style=discord.ButtonStyle.secondary, emoji=None, cid=None, url=None):
    if url: return Button(label=label[:80], style=discord.ButtonStyle.link, url=url, emoji=emoji)
    b = Button(label=label[:80], style=style, emoji=emoji, custom_id=cid); b.callback = cb; return b
def card_view(text, rows=(), accent=None, footer=True):
    try: lv = LayoutView(timeout=None)
    except TypeError: lv = LayoutView()
    lv.add_item(_make_con(text, accent=accent, footer=footer, rows=rows)); return lv
async def sendf_eph(it, text):
    if HAS_V2:
        try: return await it.followup.send(view=_make_lv(text), ephemeral=True)
        except Exception: pass
    try: return await it.followup.send(text, ephemeral=True)
    except Exception: return None

def card_thumb(text, url, accent=None, rows=()):
    title, rest = _card_parts(text); kind = _kind(title)
    con = _new_con(accent if accent is not None else _accent(title))
    ht = ("## " + title.replace("**", "").strip())[:300]
    item = None
    if Section is not None and Thumbnail is not None and url:
        try: item = Section(TextDisplay(ht), accessory=Thumbnail(str(url)))
        except Exception: item = None
    con.add_item(item or TextDisplay(ht))
    if rest:
        _sep(con); con.add_item(TextDisplay(rest[:3400]))
    for r in rows: con.add_item(r)
    _sep(con, False); con.add_item(TextDisplay(_foot(kind)))
    try: lv = LayoutView(timeout=None)
    except TypeError: lv = LayoutView()
    lv.add_item(con); return lv
async def send_thumb(sendable, text, url, accent=None, rows=()):
    if V2_OK:
        try: return await sendable.send(view=card_thumb(text, url, accent, rows))
        except Exception: traceback.print_exc()
    return await v2_text(sendable, text)

async def v2_text(sendable, text, eph=False):
    if HAS_V2:
        try:
            if eph: return await sendable.send(view=_make_lv(text), ephemeral=True)
            return await sendable.send(view=_make_lv(text))
        except Exception: pass
        try:
            if eph: return await sendable.send(view=_make_con(text), ephemeral=True)
            return await sendable.send(view=_make_con(text))
        except Exception: pass
    try:
        if eph: return await sendable.send(text, ephemeral=True)
        return await sendable.send(text)
    except Exception: return None

class Panel(View):
    def __init__(self, text, timeout=None):
        super().__init__(timeout=timeout); self.text = text
    def btn(self, label, cb, style=discord.ButtonStyle.primary, emoji=None, cid=None, row=None):
        b = Button(label=label[:80], style=style, emoji=emoji, custom_id=cid, row=row); b.callback = cb; self.add_item(b); return b
    def btn_url(self, label, url, emoji=None, row=None):
        b = Button(label=label[:80], style=discord.ButtonStyle.link, url=url, emoji=emoji, row=row); self.add_item(b); return b

async def rp(ctx, text, view=None):
    if view is None: return await v2_text(ctx, text)
    try: return await ctx.send(text, view=view)
    except Exception:
        try: return await ctx.send(text)
        except Exception: return None
async def rp_ch(ch, text, view=None):
    if view is None: return await v2_text(ch, text)
    try: return await ch.send(text, view=view)
    except Exception:
        try: return await ch.send(text)
        except Exception: return None
async def editv(it, view):
    return await it.response.edit_message(content=view.text, view=view)
async def editv_def(it, view):
    return await it.edit_original_response(content=view.text, view=view)
async def sendv_eph(it, text):
    if HAS_V2:
        try: return await it.response.send_message(view=_make_lv(text), ephemeral=True)
        except Exception: pass
        try: return await it.response.send_message(view=_make_con(text), ephemeral=True)
        except Exception: pass
    try: return await it.response.send_message(text, ephemeral=True)
    except Exception:
        try: return await it.followup.send(text, ephemeral=True)
        except Exception: return None
def get_msg_text(m):
    outs = []
    def walk(c):
        if c.__class__.__name__ == "TextDisplay" and getattr(c, "content", None): outs.append(c.content)
        for attr in ("children", "components"):
            for ch in (getattr(c, attr, None) or []): walk(ch)
    try:
        for comp in m.components: walk(comp)
    except Exception: pass
    return "\n".join(outs) if outs else (m.content or "")
LOG_EVENTS = {
    "sunucu": "server", "uye": "member", "üye": "member", "mesaj": "message", "moderasyon": "moderation",
    "rol": "role", "kanal": "channel", "ses": "voice", "ticket": "ticket", "koruma": "moderation",
    "davet": "invite", "webhook": "webhook", "thread": "thread", "emoji": "emoji", "sticker": "sticker",
    "komut": "command", "bot": "bot", "hepsi": "all", "server": "server"
}
LOG_LABELS = {
    "server": "Sunucu", "member": "Üye", "message": "Mesaj", "moderation": "Moderasyon",
    "role": "Rol", "channel": "Kanal", "voice": "Ses", "ticket": "Ticket", "invite": "Davet",
    "webhook": "Webhook", "thread": "Thread", "emoji": "Emoji", "sticker": "Sticker", "command": "Komut", "bot": "Bot"
}
async def guild_log_send(g, t, event="server"):
    event = LOG_EVENTS.get(str(event).lower(), str(event).lower())
    targets = []
    r = db.one("SELECT channel_id FROM log_channels WHERE guild_id=? AND event=?", (g.id, event))
    if r and r["channel_id"]: targets.append(r["channel_id"])
    if event == "moderation":
        p = db.one("SELECT log_ch FROM protections WHERE guild_id=?", (g.id,))
        if p and p["log_ch"] and p["log_ch"] not in targets: targets.append(p["log_ch"])
    legacy = db.one("SELECT channel_id FROM guild_logs WHERE guild_id=?", (g.id,))
    if legacy and legacy["channel_id"] and legacy["channel_id"] not in targets: targets.append(legacy["channel_id"])
    sent = False
    for cid in targets:
        ch = g.get_channel(cid)
        if ch:
            try:
                await rp_ch(ch, t); sent = True
            except Exception: pass
    return sent

def _format_greeting(template, member, kind="welcome"):
    if not template:
        template = ("## 👋 HOŞ GELDİN!\n\n{mention} **{server}** sunucusuna hoş geldin!\n\n"
                    "🎉 Sen bizim **{count}.** üyemizsin.\n🕐 Hesabın {account_age} önce oluşturulmuş.\n"
                    "📌 Kurallara göz atmayı ve topluluğa katılmayı unutma!") if kind == "welcome" else                    ("## 👋 GÜLE GÜLE!\n\n{mention} sunucudan ayrıldı.\n\n"
                    "👥 Sunucuda **{count}** kişi kaldı.\n🕐 Üyelik süresi: {joined_for}\n"
                    "💙 Seni tekrar görmek isteriz!")
    now = datetime.datetime.now(datetime.timezone.utc)
    created = getattr(member, "created_at", now)
    joined = getattr(member, "joined_at", None)
    account_age = _human_delta(created, now)
    joined_for = _human_delta(joined, now) if joined else "bilinmiyor"
    vals = {
        "user": str(member), "mention": member.mention, "name": member.display_name,
        "server": member.guild.name, "count": str(member.guild.member_count or 0),
        "id": str(member.id), "account_age": account_age, "joined_for": joined_for,
        "created": discord.utils.format_dt(created, "R") if created else "-",
        "joined": discord.utils.format_dt(joined, "R") if joined else "-"
    }
    try: return template.format(**vals)[:3800]
    except Exception: return template[:3800]

def _human_delta(start, end):
    if not start: return "bilinmiyor"
    sec = max(0, int((end - start).total_seconds()))
    if sec < 60: return str(sec) + " saniye"
    if sec < 3600: return str(sec // 60) + " dakika"
    if sec < 86400: return str(sec // 3600) + " saat"
    if sec < 2592000: return str(sec // 86400) + " gün"
    if sec < 31536000: return str(sec // 2592000) + " ay"
    return str(sec // 31536000) + " yıl"

def _greeting_view(text, member, accent):
    con = _new_con(accent)
    heading = "## " + ("👋 HOŞ GELDİN!" if accent == 0x57F287 else "👋 GÜLE GÜLE!")
    if Section is not None and Thumbnail is not None:
        try: con.add_item(Section(TextDisplay(heading), accessory=Thumbnail(str(member.display_avatar.url))))
        except Exception: con.add_item(TextDisplay(heading))
    else: con.add_item(TextDisplay(heading))
    _sep(con); con.add_item(TextDisplay(text[:3800])); _sep(con, False)
    con.add_item(TextDisplay("-# Katre Bot v" + BOT_VERSION + " • Components V2"))
    try: lv = LayoutView(timeout=None)
    except TypeError: lv = LayoutView()
    lv.add_item(con); return lv

VERSION_TAGLINE = {"6.3": "Components V2 karşılama • genişletilmiş full log • ayarlanabilir mesaj şablonları", "6.0": "Çalışan ticket butonları • ticket'a git • kalıcı select panel • öncelik akışı", "5.8": "Gelişmiş ticket • select panel • öncelik • yetkili kilidi", "5.7": "Free AI API • gelişmiş butonrol sistemi • kalıcı rol panelleri", "5.6": "AI resim • Free 7/gün • Pro sınırsız • gelişmiş çekiliş yönetimi", "5.5": "Yardım menüsü düzeltmesi • avatarlı kartlar • 6 yeni komut", "5.4": "Premium kartlar • V2 ticket • yeni yardım menüsü", "5.3": "Açıklayıcı hatalar • TDK kelime oyunu", "5.2": "Duyuru sistemi • V2 yardım"}
def update_text(ver, prev=None):
    L = [e("party") + " **KATRE v" + ver + " YAYINDA!**", DIV, e("spark") + " " + VERSION_TAGLINE.get(ver, "Yeni sürüm yayında")]
    ns = CHANGELOG.get(ver, [])
    if ns: L += ["", e("star") + " **YENİLİKLER**"] + [e("arrow") + " " + n for n in ns]
    L += ["", e("logo") + " Katre Bot • `k!yardım`"]
    return "\n".join(L)
def update_view(bot, ver, prev=None):
    con = _new_con(0xEB459E)
    heading = "## " + e("party") + " KATRE v" + ver + " YAYINDA!\n" + e("spark") + " **" + VERSION_TAGLINE.get(ver, "Yeni sürüm yayında") + "**\n-# " + ((("v" + prev + " → ") if prev else "") + "v" + ver + " • " + datetime.datetime.now().strftime("%d.%m.%Y"))
    item = None
    if Section is not None and Thumbnail is not None and getattr(bot, "user", None):
        try: item = Section(TextDisplay(heading), accessory=Thumbnail(str(bot.user.display_avatar.url)))
        except Exception: item = None
    con.add_item(item or TextDisplay(heading))
    ns = CHANGELOG.get(ver, [])
    if ns:
        _sep(con); con.add_item(TextDisplay(("### " + e("star") + " Yenilikler\n" + "\n".join(ns))[:3200]))
    _sep(con)
    con.add_item(TextDisplay(e("info") + " Tüm komutlar için `k!yardım` • Destek için `k!destek`"))
    try: con.add_item(_row(mkbtn("Destek Sunucusu", url=SUPPORT_URL, emoji=e("link"))))
    except Exception: pass
    _sep(con, False); con.add_item(TextDisplay("-# " + e("logo") + " Katre Bot v" + ver))
    try: lv = LayoutView(timeout=None)
    except TypeError: lv = LayoutView()
    lv.add_item(con); return lv
async def check_update(bot):
    try:
        row = db.one("SELECT value FROM bot_meta WHERE key='update_ch'")
        cid = int(row["value"]) if row else int(os.getenv("UPDATE_CHANNEL_ID", "0") or 0)
        if not cid: return
        ch = bot.get_channel(cid) or await bot.fetch_channel(cid)
        last = db.one("SELECT value FROM bot_meta WHERE key='version'"); lv = last["value"] if last else None
        if lv == BOT_VERSION: return
        sent = False
        if V2_OK:
            try: await ch.send(view=update_view(bot, BOT_VERSION, lv)); sent = True
            except Exception: traceback.print_exc()
        if not sent: await rp_ch(ch, update_text(BOT_VERSION, lv))
        db.q("INSERT OR REPLACE INTO bot_meta(key,value) VALUES('version',?)", (BOT_VERSION,))
    except Exception: traceback.print_exc()

class OwnerOnly(commands.CheckFailure): pass
class ProOnly(commands.CheckFailure): pass

AI_IMAGE_LOCK = asyncio.Lock()

def ai_is_pro(user_id):
    u = db.one("SELECT pro,pro_expiry FROM users WHERE user_id=?", (user_id,))
    if not u or not u["pro"]:
        return False
    if u["pro_expiry"]:
        try:
            if datetime.datetime.now() >= datetime.datetime.fromisoformat(u["pro_expiry"]):
                db.q("UPDATE users SET pro=0, pro_expiry=NULL WHERE user_id=?", (user_id,))
                pro_log(user_id, "SÜRESİ DOLDU")
                return False
        except Exception:
            db.q("UPDATE users SET pro=0, pro_expiry=NULL WHERE user_id=?", (user_id,))
            return False
    return True

async def ai_image_reserve(user_id):
    """Başarılı üretim sonrası geri alınabilmesi için hakkı üretimden önce rezerve eder."""
    if ai_is_pro(user_id):
        return True, None, True
    day = datetime.datetime.now().date().isoformat()
    async with AI_IMAGE_LOCK:
        row = db.one("SELECT uses FROM ai_usage WHERE user_id=? AND usage_day=?", (user_id, day))
        used = int(row["uses"]) if row else 0
        if used >= AI_FREE_DAILY_LIMIT:
            return False, used, False
        if row:
            db.q("UPDATE ai_usage SET uses=uses+1 WHERE user_id=? AND usage_day=?", (user_id, day))
        else:
            db.q("INSERT INTO ai_usage(user_id,usage_day,uses) VALUES(?,?,1)", (user_id, day))
        return True, used + 1, False

async def ai_image_refund(user_id):
    if ai_is_pro(user_id):
        return
    day = datetime.datetime.now().date().isoformat()
    async with AI_IMAGE_LOCK:
        row = db.one("SELECT uses FROM ai_usage WHERE user_id=? AND usage_day=?", (user_id, day))
        if not row:
            return
        new_uses = max(0, int(row["uses"]) - 1)
        if new_uses:
            db.q("UPDATE ai_usage SET uses=? WHERE user_id=? AND usage_day=?", (new_uses, user_id, day))
        else:
            db.q("DELETE FROM ai_usage WHERE user_id=? AND usage_day=?", (user_id, day))

def ai_image_remaining(user_id):
    if ai_is_pro(user_id):
        return "Sınırsız"
    day = datetime.datetime.now().date().isoformat()
    row = db.one("SELECT uses FROM ai_usage WHERE user_id=? AND usage_day=?", (user_id, day))
    used = int(row["uses"]) if row else 0
    return str(max(0, AI_FREE_DAILY_LIMIT - used))

async def _http_image(url, headers=None, payload=None, timeout_total=180):
    timeout = aiohttp.ClientTimeout(total=timeout_total)
    async with aiohttp.ClientSession(timeout=timeout) as ses:
        async with ses.post(url, json=payload, headers=headers or {}) as r:
            raw = await r.read()
            if r.status >= 400:
                try:
                    err = json.loads(raw.decode("utf-8", errors="replace"))
                    msg = err.get("error", {}).get("message") or err.get("message") or raw.decode("utf-8", errors="replace")
                except Exception:
                    msg = raw.decode("utf-8", errors="replace")
                raise RuntimeError("HTTP " + str(r.status) + ": " + str(msg)[:500])
            return raw, r.headers.get("Content-Type", "")

async def huggingface_generate_image(prompt):
    if not HF_TOKEN:
        raise RuntimeError("HF_TOKEN ayarlanmamış.")
    if InferenceClient is None:
        raise RuntimeError("huggingface_hub kurulu değil. `pip install -U huggingface_hub>=1.1.2` çalıştır.")
    try:
        client = InferenceClient(api_key=HF_TOKEN, provider="auto")
        image = await asyncio.to_thread(
            client.text_to_image,
            prompt[:4000],
            model=HF_IMAGE_MODEL,
            width=1024,
            height=1024,
        )
        buf = io.BytesIO()
        image.save(buf, format="PNG")
        return buf.getvalue()
    except Exception as ex:
        raise RuntimeError("Hugging Face: " + str(ex)[:500])

async def openai_generate_image(prompt):
    if not OPENAI_API_KEY:
        raise RuntimeError("OPENAI_API_KEY ayarlanmamış.")
    payload = {"model": OPENAI_IMAGE_MODEL, "prompt": prompt[:4000], "size": "1024x1024", "n": 1}
    headers = {"Authorization": "Bearer " + OPENAI_API_KEY, "Content-Type": "application/json"}
    raw, _ = await _http_image("https://api.openai.com/v1/images/generations", headers=headers, payload=payload)
    try:
        data = json.loads(raw)
    except Exception as ex:
        raise RuntimeError("OpenAI yanıtı okunamadı: " + str(ex))
    items = data.get("data") or []
    if not items: raise RuntimeError("OpenAI görsel yanıtı boş döndü.")
    item = items[0]
    if item.get("b64_json"):
        try: return base64.b64decode(item["b64_json"])
        except Exception as ex: raise RuntimeError("Görsel verisi çözülemedi: " + str(ex))
    url = item.get("url")
    if url:
        timeout = aiohttp.ClientTimeout(total=120)
        async with aiohttp.ClientSession(timeout=timeout) as ses:
            async with ses.get(url) as r:
                if r.status != 200: raise RuntimeError("Üretilen görsel indirilemedi (HTTP " + str(r.status) + ").")
                return await r.read()
    raise RuntimeError("OpenAI yanıtında b64_json veya url bulunamadı.")

async def generate_ai_image(prompt, pro_user=False):
    providers = []
    if AI_PROVIDER == "huggingface": providers = ["huggingface"]
    elif AI_PROVIDER == "openai": providers = ["openai"]
    elif AI_PROVIDER == "auto":
        if pro_user and OPENAI_API_KEY: providers.append("openai")
        if HF_TOKEN: providers.append("huggingface")
        if OPENAI_API_KEY and "openai" not in providers: providers.append("openai")
    else:
        providers = [x for x in ("huggingface", "openai") if x == AI_PROVIDER]
    if not providers:
        raise RuntimeError("AI sağlayıcısı ayarlanmadı. `HF_TOKEN` veya `OPENAI_API_KEY` ekle.")
    errors = []
    for provider in providers:
        try:
            if provider == "huggingface": return await huggingface_generate_image(prompt), "Hugging Face • " + HF_IMAGE_MODEL
            return await openai_generate_image(prompt), "OpenAI • " + OPENAI_IMAGE_MODEL
        except Exception as ex:
            errors.append(provider.upper() + ": " + str(ex)[:300])
    raise RuntimeError(" / ".join(errors))

def is_owner():
    async def p(ctx):
        if ctx.author.id != OWNER_ID: raise OwnerOnly()
        return True
    return commands.check(p)
def is_half():
    async def p(ctx):
        if ctx.author.id == OWNER_ID or is_half_owner(ctx.author.id): return True
        raise OwnerOnly()
    return commands.check(p)
def is_pro():
    async def p(ctx):
        u = db.one("SELECT pro,pro_expiry FROM users WHERE user_id=?", (ctx.author.id,))
        if u and u["pro"]:
            if u["pro_expiry"]:
                if datetime.datetime.now() < datetime.datetime.fromisoformat(u["pro_expiry"]): return True
                db.q("UPDATE users SET pro=0 WHERE user_id=?", (ctx.author.id,)); pro_log(ctx.author.id, "SÜRESİ DOLDU")
        raise ProOnly()
    return commands.check(p)
def kategori(a):
    def d(c): c.kategori = a; return c
    return d

CATS = {"genel":("genel","Genel & Sistem"),"mod":("mod","Moderasyon & Koruma"),"sys":("sys","Başvuru & Otomasyon"),"eco":("eco","Ekonomi"),"fun":("fun","Eğlence"),"give":("give","Çekiliş"),"pro":("pro","Pro"),"owner":("owner","Owner")}
CAT_DESC = {"genel":"Rank, profil, avatar, snipe, AFK, oda","mod":"Ban, kick, unban, mute, uyarı, oto-ceza, koruma, butonrol","sys":"Başvuru, ticket, temp voice, kelime oyunu, log","eco":"Coin, günlük, çalışma, balık, maden, market","fun":"Quiz, slot, aşk, anket ve oyunlar","give":"Butonlu çekiliş, reroll, sonuç paneli","pro":"Pro oda, rol, bonus, banner, şans","owner":"Owner + Half Owner paneli, duyuru"}
def cat_count(b, k): return len([c for c in b.commands if getattr(c, "kategori", None) == k])
HELP_COLORS = {"genel":0x5865F2,"mod":0xE67E22,"sys":0x1ABC9C,"eco":0xF1C40F,"fun":0x9B59B6,"give":0xEB459E,"pro":0x00D9FF,"owner":0xFEE75C}
HELP_TIPS = ["`k!günlük` ile her gün ücretsiz coin topla.", "`k!rank` ile seviyeni ve sıralamanı gör.", "`k!destek` paneliyle sunucunda ticket sistemi kurabilirsin.",
    "`k!afk <sebep>` yazınca seni etiketleyenlere sebebi gösteririm.", "`k!oylama soru | seçenek1 | seçenek2` ile hızlı anket aç.", "`k!hesapla 12*(3+4)` ile hızlı hesap yap.",
    "`k!komutbilgi <komut>` ile bir komutun kullanımını öğren.", "`k!çekiliş` ile butonlu çekiliş başlatabilirsin.", "`k!kullanıcıbilgi @üye` ile üye hakkında detaylı bilgi al.",
    "`k!sarıl @üye` ile birine sıcak bir sarılma gönder.", "`k!butonrol` ile rol butonları oluştur. `k!destek` ile ticket panelini aç."]
def help_content(bot):
    L = ["## " + e("logo") + " " + bot.user.name.upper() + " • YARDIM MERKEZİ", DIV,
         "Selam! Ben **" + bot.user.name + "** " + e("spark") + " — moderasyon, ekonomi, eğlence, ticket ve çok daha fazlası tek botta.", "",
         e("chart") + " **" + str(len(bot.commands)) + "** komut  •  " + e("genel") + " **" + str(len(bot.guilds)) + "** sunucu  •  " + e("tag") + " önek `k!`", "",
         e("star") + " **KATEGORİLER**"]
    for k in CATS: L += [e(k) + " **" + CATS[k][1] + "** `" + str(cat_count(bot, k)) + "`", "-# " + CAT_DESC[k]]
    L += ["", e("spark") + " **İpucu:** " + random.choice(HELP_TIPS), "", "-# " + e("arrow") + " Menüden bir kategori seç  •  Detay: `k!komutbilgi <komut>`", e("link") + " Destek: " + SUPPORT_URL]
    return "\n".join(L)
def cat_content(bot, key, page=1):
    cmds = sorted([c for c in bot.commands if getattr(c, "kategori", None) == key], key=lambda x: x.name)
    pages = [cmds[i:i+PAGE_SIZE] for i in range(0, len(cmds), PAGE_SIZE)] or [[]]
    page = max(1, min(page, len(pages)))
    base = ["## " + e(key) + " " + CATS[key][1].upper(), "-# " + CAT_DESC[key], DIV, "**" + str(len(cmds)) + "** komut  •  **Sayfa " + str(page) + "/" + str(len(pages)) + "**", ""]
    body = "\n".join(base + [e("arrow") + " `k!" + c.name + "` ─ " + (c.help or "") for c in pages[page-1]])
    if len(body) > 1900: body = "\n".join(base + ["`k!" + c.name + "`" for c in pages[page-1]])
    return (body + "\n\n-# " + e("info") + " ◀ ▶ ile sayfa değiştir • " + e("home") + " ana menüye dön")[:1990]

# ─────────────── 🧩 V2 YARDIM KARTI ───────────────
async def _pg2(bot, it, d):
    try:
        txt = get_msg_text(it.message); key = None
        for k in CATS:
            if "## " + e(k) + " " + CATS[k][1].upper() in txt: key = k; break
        if not key: return await sendv_eph(it, WN("ÖNCE KATEGORİ SEÇ", "Sayfa değiştirmek için önce menüden bir kategori seçmelisin."))
        mm = re.search(r"Sayfa (\d+)/(\d+)", txt); p = int(mm.group(1)) if mm else 1
        await it.response.edit_message(view=help_v2(bot, cat_content(bot, key, p + d)))
    except Exception as ex:
        await sendv_eph(it, ER("SAYFA HATASI", str(ex)[:200]))

def _help_accent(title):
    for k in CATS:
        if e(k) in title and CATS[k][1].upper() in title: return HELP_COLORS.get(k, 0x5865F2)
    if "YARDIM MERKEZİ" in title: return 0x5865F2
    return _accent(title)

def help_v2(bot, text):
    title, rest = _card_parts(text)
    home = "YARDIM MERKEZİ" in title
    heading = title if title.startswith("#") else "## " + title.replace("**", "")
    con = _new_con(_help_accent(title))
    item = None
    if home and Section is not None and Thumbnail is not None and getattr(bot, "user", None):
        try: item = Section(TextDisplay(heading[:300]), accessory=Thumbnail(str(bot.user.display_avatar.url)))
        except Exception: item = None
    con.add_item(item or TextDisplay(heading[:300]))
    if rest:
        _sep(con); con.add_item(TextDisplay(rest[:3400]))
    cur = None
    for k in CATS:
        if e(k) in title and CATS[k][1].upper() in title: cur = k; break
    sel = Select(placeholder="📂 Kategori seç...", min_values=1, max_values=1, custom_id="kv_sel",
                 options=[discord.SelectOption(label=CATS[k][1], value=k, emoji=SLOTS.get(k, "•"), description=CAT_DESC[k][:90], default=(k == cur)) for k in CATS])
    async def sel_cb(it):
        try:
            key = sel.values[0]
            if key == "owner" and it.user.id != OWNER_ID and not is_half_owner(it.user.id):
                return await sendv_eph(it, ER("YETKİ YOK", "Owner kategorisi sadece bot sahibine ve yardımcılarına açık."))
            await it.response.edit_message(view=help_v2(bot, cat_content(bot, key, 1)))
        except Exception as ex:
            traceback.print_exc()
            try: await sendv_eph(it, ER("MENÜ HATASI", "Kategori açılamadı.\n`" + str(ex)[:150] + "`"))
            except Exception: pass
    sel.callback = sel_cb
    _sep(con, False); con.add_item(_row(sel))
    async def prev(it): await _pg2(bot, it, -1)
    async def nxt(it): await _pg2(bot, it, 1)
    async def home_cb(it): await it.response.edit_message(view=help_v2(bot, help_content(bot)))
    async def stats(it):
        up = str(datetime.datetime.now() - bot.start_time).split(".")[0]
        await sendv_eph(it, head("chart", "BOT İSTATİSTİKLERİ") + "\n\n" + KV([(e("dot")+"Sunucu", len(bot.guilds)), (e("dot")+"Kullanıcı", sum(g.member_count or 0 for g in bot.guilds)), (e("dot")+"Komut", len(bot.commands)), (e("dot")+"Çalışma süresi", up), (e("dot")+"Ping", str(round(bot.latency*1000))+" ms")]))
    async def close(it): await it.message.delete()
    con.add_item(_row(
        mkbtn("Önceki", prev, discord.ButtonStyle.secondary, "◀", "kv_prev"),
        mkbtn("Sonraki", nxt, discord.ButtonStyle.secondary, "▶", "kv_next"),
        mkbtn("Ana Menü", home_cb, discord.ButtonStyle.success, SLOTS["home"], "kv_home"),
        mkbtn("İstatistik", stats, discord.ButtonStyle.secondary, SLOTS["chart"], "kv_stats"),
        mkbtn("Kapat", close, discord.ButtonStyle.danger, SLOTS["trash"], "kv_close")))
    try:
        inv = "https://discord.com/oauth2/authorize?client_id=" + str(bot.user.id) + "&permissions=8&scope=bot%20applications.commands"
        con.add_item(_row(mkbtn("Destek Sunucusu", url=SUPPORT_URL, emoji=e("link")), mkbtn("Botu Ekle", url=inv, emoji="➕")))
    except Exception: pass
    _sep(con, False); con.add_item(TextDisplay("-# " + e("logo") + " Katre Bot v" + BOT_VERSION + " • `k!komutbilgi <komut>` ile detay"))
    lv = LayoutView(timeout=None); lv.add_item(con)
    return lv

class HelpSelect(Select):
    def __init__(self, bot):
        super().__init__(placeholder="📂 Kategori seç...", min_values=1, max_values=1, row=0, custom_id="kh_sel",
                         options=[discord.SelectOption(label=CATS[k][1], value=k, emoji=SLOTS.get(k, "•"), description=CAT_DESC[k][:60]) for k in CATS])
        self.bot = bot
    async def callback(self, it):
        await it.response.defer()
        try:
            key = self.values[0]
            if key == "owner" and it.user.id != OWNER_ID and not is_half_owner(it.user.id):
                return await editv_def(it, Panel(ER("YETKİ YOK", "Owner paneli sadece sahibine açık.")))
            await editv_def(it, HelpPanel(self.bot, cat_content(self.bot, key, 1)))
        except Exception as ex:
            try: await editv_def(it, Panel(ER("MENÜ HATASI", str(ex)[:250])))
            except Exception: pass

class HelpPanel(Panel):
    def __init__(self, bot, text):
        super().__init__(text, timeout=None); self.bot = bot
        self.add_item(HelpSelect(bot))
        async def prev(it): await self._pg(it, -1)
        async def nxt(it): await self._pg(it, 1)
        async def home(it): await editv(it, HelpPanel(self.bot, help_content(self.bot)))
        async def stats(it):
            up = str(datetime.datetime.now() - self.bot.start_time).split(".")[0]
            await sendv_eph(it, head("chart", "İSTATİSTİK") + "\n\n" + KV([("Sunucu", len(self.bot.guilds)), ("Kullanıcı", sum(g.member_count or 0 for g in self.bot.guilds)), ("Komut", len(self.bot.commands)), ("Uptime", up), ("Ping", str(round(self.bot.latency*1000))+"ms")]))
        async def close(it): await it.message.delete()
        self.btn("◀ Önceki", prev, style=discord.ButtonStyle.secondary, cid="kh_prev", row=1)
        self.btn("Sonraki ▶", nxt, style=discord.ButtonStyle.secondary, cid="kh_next", row=1)
        self.btn("Ana Menü", home, style=discord.ButtonStyle.success, emoji=e("home"), cid="kh_home", row=1)
        self.btn("İstatistik", stats, style=discord.ButtonStyle.secondary, emoji=e("chart"), cid="kh_stats", row=1)
        self.btn("Kapat", close, style=discord.ButtonStyle.danger, emoji=e("trash"), cid="kh_close", row=1)
        self.btn_url("Destek", SUPPORT_URL, emoji=e("link"), row=2)
    async def _pg(self, it, d):
        try:
            txt = it.message.content or ""
            key = None
            for k in CATS:
                if "## " + e(k) + " " + CATS[k][1].upper() in txt: key = k; break
            if not key: return await sendv_eph(it, WN("MENÜ", "Önce menüden kategori seç."))
            m = re.search(r"Sayfa (\d+)/(\d+)", txt); p = int(m.group(1)) if m else 1
            await editv(it, HelpPanel(self.bot, cat_content(self.bot, key, p + d)))
        except Exception as ex: await sendv_eph(it, ER("SAYFA", str(ex)[:200]))

class ConfirmPanel(Panel):
    def __init__(self, text, t=30):
        super().__init__(text, timeout=t); self.value = None
        async def y(it):
            self.value = True; self.stop(); await editv(it, Panel(WN("İŞLENİYOR...", "Bekle.")))
        async def n(it):
            self.value = False; self.stop(); await editv(it, Panel(ER("İŞLEM İPTAL EDİLDİ", "Hiçbir değişiklik yapılmadı.")))
        self.btn("Onayla", y, style=discord.ButtonStyle.success, emoji=e("check"))
        self.btn("Vazgeç", n, style=discord.ButtonStyle.secondary, emoji=e("cross"))

class OwnerPanel(Panel):
    def __init__(self, bot, text):
        super().__init__(text, timeout=None); self.bot = bot
        async def g(it):
            if it.user.id != OWNER_ID: await sendv_eph(it, ER("YETKİ YOK", "Bu işlemi yapmak için gerekli yetkiye sahip değilsin.")); return False
            return True
        async def bk(it):
            if not await g(it): return
            cur = db.one("SELECT maintenance FROM owner_settings WHERE id=1")["maintenance"]
            db.q("UPDATE owner_settings SET maintenance=? WHERE id=1", (0 if cur else 1,))
            await sendv_eph(it, head("gear", "BAKIM") + "\n\n**" + ("AÇIK" if not cur else "KAPALI") + "**")
        async def st(it):
            if not await g(it): return
            await sendv_eph(it, head("chart", "OWNER") + "\n\n" + KV([("Sunucu", len(self.bot.guilds)), ("Pro", len(db.all("SELECT 1 FROM users WHERE pro=1"))), ("Half", len(db.all("SELECT 1 FROM half_owners"))), ("Bakım", "AÇIK" if is_maintenance() else "KAPALI")]))
        async def gl(it):
            if not await g(it): return
            await sendv_eph(it, head("owner", "SUNUCULAR") + "\n\n" + "\n".join(e("arrow") + " **" + x.name + "** " + str(x.member_count) for x in sorted(self.bot.guilds, key=lambda y: -(y.member_count or 0))[:10]))
        async def dy(it):
            if await g(it): await it.response.send_modal(BroadcastModal())
        async def cl(it):
            if await g(it): await it.message.delete()
        self.btn("Bakım", bk, style=discord.ButtonStyle.secondary, emoji=e("gear"), cid="op_bak", row=0)
        self.btn("İstatistik", st, style=discord.ButtonStyle.success, emoji=e("chart"), cid="op_stats", row=0)
        self.btn("Sunucular", gl, emoji="🖥️", cid="op_guilds", row=0)
        self.btn("Duyuru", dy, emoji="📢", cid="op_duy", row=0)
        self.btn("Kapat", cl, style=discord.ButtonStyle.danger, emoji=e("trash"), cid="op_close", row=0)
class BroadcastModal(Modal, title="Genel Duyuru"):
    txt = TextInput(label="Duyuru metni", style=discord.TextStyle.paragraph)
    async def on_submit(self, it):
        ok = 0
        for g in it.client.guilds:
            ch = g.system_channel or next((c for c in g.text_channels if c.permissions_for(g.me).send_messages), None)
            if ch:
                try: await rp_ch(ch, head("owner", "DUYURU") + "\n\n" + self.txt.value); ok += 1
                except Exception: pass
        await it.response.send_message(OK("DUYURU GÖNDERİLDİ", "Mesaj **" + str(ok) + "/" + str(len(it.client.guilds)) + "** sunucuya başarıyla iletildi. 📢"), ephemeral=True)

def gw_start(gw):
    return ("## " + e("give") + " ÇEKİLİŞ: " + gw["prize"] + "\n" + DIV + "\n" + KV([(e("star")+"Kazanan", str(gw["winners"]) + " kişi"), (e("dot")+"Katılım", str(len(json.loads(gw["participants"]))) + " kişi"), (e("time")+"Bitiş", "<t:" + str(int(gw["end_time"])) + ":R>"), (e("dot")+"Düzenleyen", "<@" + str(gw["host"]) + ">")]) + "\n\n" + e("spark") + " **KATIL** butonuna bas!")
def gw_end(gw, men, parts):
    return ("## " + e("star") + " " + gw["prize"] + "\n" + DIV + "\n**ÇEKİLİŞ BİTTİ**\n\n" + KV([(e("star")+"Kazanan", men), (e("dot")+"Katılım", str(len(parts)) + " kişi"), (e("dot")+"Düzenleyen", "<@" + str(gw["host"]) + ">"), (e("alarm")+"Bitti", "<t:" + str(int(datetime.datetime.now().timestamp())) + ":F>")]) + "\n\n" + e("party") + " Kazananlar duyuruda.")
class GiveawayPanel(Panel):
    """Kalıcı çekiliş katılım paneli.

    Yönetim işlemleri artık butonlarla yapılmaz; çekiliş sahibi veya yöneticiler
    komutlarla düzenleme/bitirme/iptal/yeniden çekme işlemlerini yapar.
    """
    def __init__(self, bot, text):
        super().__init__(text, timeout=None); self.bot = bot

        async def join(it):
            gw = db.one("SELECT * FROM giveaways WHERE message_id=?", (it.message.id,))
            if not gw or gw["status"] != "active":
                return await sendv_eph(it, ER("ÇEKİLİŞ AKTİF DEĞİL", "Bu çekiliş sona ermiş veya iptal edilmiş."))
            p = json.loads(gw["participants"])
            if str(it.user.id) in p:
                return await sendv_eph(it, WN("ZATEN KATILDIN", "Bu çekilişe zaten katılmışsın, tekrar katılmana gerek yok."))
            p.append(str(it.user.id))
            db.q("UPDATE giveaways SET participants=? WHERE message_id=?", (json.dumps(p), it.message.id))
            nt = gw_start(dict(gw, participants=json.dumps(p)))
            try:
                await it.message.edit(content=nt, view=GiveawayPanel(self.bot, nt))
            except Exception:
                pass
            await sendv_eph(it, OK("ÇEKİLİŞE KATILDIN", "Ödül: **" + gw["prize"] + "**\nBol şans! 🍀"))

        async def leave(it):
            gw = db.one("SELECT * FROM giveaways WHERE message_id=?", (it.message.id,))
            if not gw or gw["status"] != "active":
                return await sendv_eph(it, ER("ÇEKİLİŞ AKTİF DEĞİL", "Bu çekiliş sona ermiş veya iptal edilmiş."))
            p = json.loads(gw["participants"])
            if str(it.user.id) not in p:
                return await sendv_eph(it, WN("KATILMAMIŞSIN", "Bu çekilişte kayıtlı görünmüyorsun."))
            p.remove(str(it.user.id))
            db.q("UPDATE giveaways SET participants=? WHERE message_id=?", (json.dumps(p), it.message.id))
            nt = gw_start(dict(gw, participants=json.dumps(p)))
            try:
                await it.message.edit(content=nt, view=GiveawayPanel(self.bot, nt))
            except Exception:
                pass
            await sendv_eph(it, WN("ÇEKİLİŞTEN AYRILDIN", "Katılımın silindi. İstersen **Katıl** butonuyla tekrar girebilirsin."))

        self.btn("Katıl", join, style=discord.ButtonStyle.success, emoji=e("party"), cid="kg_join", row=0)
        self.btn("Ayrıl", leave, style=discord.ButtonStyle.secondary, cid="kg_leave", row=0)


class GwJumpPanel(Panel):

    def __init__(self, text, url):
        super().__init__(text, timeout=None); self.btn_url("Çekilişe Git", url, emoji=e("link"))

def poll_content(p):
    opts = json.loads(p["options"]); votes = json.loads(p["votes"]); total = sum(len(v) for v in votes.values())
    L = ["## " + e("chart") + " ANKET: " + p["question"], DIV]
    if p["status"] != "active": L.append(e("lock") + " **KAPANDI**")
    L.append("")
    for i, op in enumerate(opts):
        n = len(votes.get(str(i), [])); pc = (n / total * 100) if total else 0
        L.append(e("arrow") + " **" + op + "** ─ `" + str(n) + "` oy " + bar(pc, 10))
    L += ["", e("dot") + " Toplam **" + str(total) + "** oy • " + (e("party") + " Bitti!" if p["status"] != "active" else "tek oy, değişmez")]
    return "\n".join(L)
class PollPanel(Panel):
    def __init__(self, pid, opts, text):
        super().__init__(text, timeout=None); self.pid = pid
        for i, op in enumerate(opts[:5]):
            async def cb(it, idx=i):
                p = db.one("SELECT * FROM polls WHERE id=?", (self.pid,))
                if not p or p["status"] != "active": return await sendv_eph(it, ER("ANKET KAPALI", "Bu anket sonlandırıldı, artık oy verilemez."))
                v = json.loads(p["votes"])
                for lst in v.values():
                    if str(it.user.id) in lst: return await sendv_eph(it, WN("ZATEN OY VERDİN", "Bu ankette oyunu kullandın. Oylar değiştirilemez."))
                v.setdefault(str(idx), []).append(str(it.user.id)); db.q("UPDATE polls SET votes=? WHERE id=?", (json.dumps(v), self.pid))
                p2 = db.one("SELECT * FROM polls WHERE id=?", (self.pid,))
                try: await it.message.edit(content=poll_content(p2), view=PollPanel(self.pid, json.loads(p2["options"]), poll_content(p2)))
                except Exception: pass
                await sendv_eph(it, OK("OYUN KAYDEDİLDİ", "Seçimin: **" + json.loads(p["options"])[idx] + "**\nOylar tek seferliktir ve değiştirilemez. 🗳️"))
            self.btn(op[:60], cb, emoji=e("dot"), cid="poll_" + str(pid) + "_" + str(i), row=0)
        async def close(it):
            p = db.one("SELECT * FROM polls WHERE id=?", (self.pid,))
            if not p: return
            if not (it.user.id == p["creator"] or (it.guild and it.guild.permissions_for(it.user).administrator)): return await sendv_eph(it, ER("YETKİ YOK", "Bu işlemi yapmak için gerekli yetkiye sahip değilsin."))
            if p["status"] != "active": return await sendv_eph(it, WN("ANKET ZATEN KAPALI", "Bu anket daha önce sonlandırılmış."))
            db.q("UPDATE polls SET status='closed' WHERE id=?", (self.pid,))
            p2 = db.one("SELECT * FROM polls WHERE id=?", (self.pid,))
            try: await it.message.edit(content=poll_content(p2), view=PollPanel(self.pid, json.loads(p2["options"]), poll_content(p2)))
            except Exception: pass
            await sendv_eph(it, OK("ANKET KAPATILDI", "Oylama sonlandırıldı, güncel sonuçlar mesajda gösteriliyor. 📊"))
        self.btn("Anketi Kapat", close, style=discord.ButtonStyle.danger, emoji=e("lock"), cid="pollc_" + str(pid), row=1)

class RoleMenuPanel(View):
    def __init__(self, mid, roles, text=" "):
        super().__init__(timeout=None)
        self.mid = str(mid); self.text = text
        opts = []
        for rid, nm in roles[:25]:
            opts.append(discord.SelectOption(label=str(nm)[:100], value=str(rid), emoji="🎭", description="Rolü al / kaldır"))
        if not opts:
            return
        sel = Select(placeholder="🎭 Rollerinden seçim yap...", min_values=0, max_values=1, options=opts, custom_id="kr_select_" + self.mid)
        async def cb(it):
            await it.response.defer(ephemeral=True)
            if not it.guild: return
            rid = int(sel.values[0]) if sel.values else 0
            r = it.guild.get_role(rid)
            if not r:
                return await it.followup.send(ER("ROL BULUNAMADI", "Bu rol silinmiş. Yönetici `k!butonrollist` ile menüyü kontrol edebilir."), ephemeral=True)
            me = it.guild.me
            if not me or not me.guild_permissions.manage_roles:
                return await it.followup.send(ER("BOT YETKİSİ EKSİK", "Botun **Rolleri Yönet** yetkisi yok."), ephemeral=True)
            if r.is_default() or r.managed or r >= me.top_role:
                return await it.followup.send(ER("ROL UYGUN DEĞİL", "Bu rol bot tarafından yönetilemez. Bot rolünü hedef rolün üstüne taşı."), ephemeral=True)
            try:
                if r in it.user.roles:
                    await it.user.remove_roles(r, reason="Katre Select Rol")
                    msg = e("cross") + " **" + r.name + "** rolü kaldırıldı."
                    await guild_log_send(it.guild, head("shield", "ROL KALDIRILDI") + "\n\n" + it.user.mention + " → " + r.mention, "role")
                else:
                    await it.user.add_roles(r, reason="Katre Select Rol")
                    msg = e("check") + " **" + r.name + "** rolü verildi."
                    await guild_log_send(it.guild, head("shield", "ROL VERİLDİ") + "\n\n" + it.user.mention + " → " + r.mention, "role")
                await it.followup.send(head("shield", "ROL GÜNCELLENDİ") + "\n\n" + msg, ephemeral=True)
            except discord.Forbidden:
                await it.followup.send(ER("ROL VERİLEMEDİ", "Discord botun bu role erişmesine izin vermedi."), ephemeral=True)
            except Exception as ex:
                await it.followup.send(ER("ROL İŞLEMİ HATASI", str(ex)[:500]), ephemeral=True)
        sel.callback = cb
        self.add_item(sel)


# ═══════════════════════════════════════════════════════════════════
# 🎫 TİCKET SİSTEMİ v5.9 (select panel • öncelik • üstlenen yetkili kilidi)
# ═══════════════════════════════════════════════════════════════════
TICKET_CATS = {"destek": ("🛠️", "Genel Destek", 0x5865F2), "sikayet": ("🚨", "Şikayet", 0xED4245), "oneri": ("💡", "Öneri", 0xFEE75C), "ortaklik": ("🤝", "Ortaklık", 0x57F287)}
TICKET_PRIORITIES = {"dusuk": ("🟢", "Düşük"), "normal": ("🔵", "Normal"), "yuksek": ("🟠", "Yüksek"), "acil": ("🔴", "Acil")}
def _tcat(k): return TICKET_CATS.get(k or "destek", TICKET_CATS["destek"])
def _safe(s): return str(s).replace("@", "@\u200b")
def _priority_key(v):
    x = (v or "normal").lower().strip().replace("ü","u").replace("ş","s").replace("ı","i").replace("ö","o").replace("ç","c").replace("ğ","g")
    return x if x in TICKET_PRIORITIES else "normal"
def _priority_text(v):
    k = _priority_key(v); em, nm = TICKET_PRIORITIES[k]; return em + " " + nm
def _ticket_staff_roles(guild):
    st = db.one("SELECT staff_roles FROM ticket_settings WHERE guild_id=?", (guild.id,))
    ids = json.loads(st["staff_roles"] or "[]") if st else []
    return [guild.get_role(int(x)) for x in ids if guild.get_role(int(x))]
def _ticket_is_admin(m):
    return bool(m and (m.id == OWNER_ID or m.guild_permissions.administrator))
def _ticket_is_staff(it):
    m = it.user
    if _ticket_is_admin(m): return True
    roles = _ticket_staff_roles(it.guild)
    return any(r.id in [x.id for x in m.roles] for r in roles)
def _ticket_can_manage(t, m):
    if _ticket_is_admin(m): return True
    return bool(t and t.get("claimed_by") == m.id)
def ticket_text(t):
    em, nm, _ = _tcat(t.get("category"))
    if t["status"] != "open": durum = "🔴 Kapalı"
    elif t.get("claimed_by"): durum = "🟡 Üstlenildi"
    else: durum = "🟢 Açık • yetkili bekleniyor"
    try: ts = int(datetime.datetime.fromisoformat(t["created_at"]).timestamp())
    except Exception: ts = int(time.time())
    num = str(t.get("number") or 0).zfill(4) if t.get("number") else "—"
    ps = [(e("dot") + "Açan", "<@" + str(t["user_id"]) + ">"), (em + " Tür", nm), (e("alarm") + "Öncelik", _priority_text(t.get("priority"))),
          (e("clip") + "Konu", _safe(t.get("subject") or "—")), (e("alarm") + "Açılış", "<t:" + str(ts) + ":R>"),
          (e("shield") + "Yetkili", ("<@" + str(t["claimed_by"]) + ">") if t.get("claimed_by") else "Henüz üstlenilmedi"), (e("info") + "Durum", durum)]
    return head("ticket", "TALEP #" + num + " • " + nm.upper()) + "\n\n" + KV(ps) + "\n\n**" + e("pen") + " Açıklama**\n" + _q(_safe(t.get("description") or "—")[:900])
async def ticket_transcript(ch, t):
    L = ["KATRE BOT • TALEP KAYDI", "Talep: #" + str(t.get("number") or "?") + " • Kanal: " + ch.name, "Konu: " + str(t.get("subject") or "—"), "Öncelik: " + _priority_text(t.get("priority")), "=" * 50, ""]
    try:
        async for m in ch.history(limit=1000, oldest_first=True):
            if m.author.bot and not m.content: continue
            ek = (" [ek: " + ", ".join(a.url for a in m.attachments) + "]") if m.attachments else ""
            L.append("[" + m.created_at.strftime("%d.%m.%Y %H:%M") + "] " + str(m.author) + ": " + (m.content or "") + ek)
    except Exception as ex: L.append("(kayıt okunurken hata: " + str(ex)[:100] + ")")
    return "\n".join(L).encode("utf-8")
async def ticket_finish(guild, ch, t, closer):
    db.q("UPDATE tickets SET status='closed' WHERE channel_id=?", (ch.id,)); t["status"] = "closed"
    data = await ticket_transcript(ch, t); num = str(t.get("number") or ch.id); fn = "talep-" + num + ".txt"
    await guild_log_send(guild, "🎫 **Talep #" + num + " kapandı** • Açan: <@" + str(t["user_id"]) + "> • Kapatan: " + closer.mention, "ticket")
    u = guild.get_member(t["user_id"])
    if u:
        try: await u.send(OK("TALEBİN KAPATILDI", "**" + guild.name + "** sunucusundaki talebin (#" + num + ") kapatıldı.\nKonuşma kaydı ekte."), file=discord.File(io.BytesIO(data), filename=fn))
        except Exception: pass
async def _ticket_apply_permissions(ch, t, guild):
    roles = _ticket_staff_roles(guild)
    claimed = int(t.get("claimed_by") or 0)
    for r in roles:
        try:
            await ch.set_permissions(r, view_channel=True, send_messages=(not claimed), attach_files=(not claimed), read_message_history=True)
        except Exception:
            pass
    if claimed:
        m = guild.get_member(claimed)
        if m:
            try:
                await ch.set_permissions(m, view_channel=True, send_messages=True, attach_files=True, read_message_history=True)
            except Exception:
                pass

async def tk_claim(it):
    t = db.one("SELECT * FROM tickets WHERE channel_id=?", (it.channel.id,))
    if not t: return await sendv_eph(it, ER("TALEP BULUNAMADI", "Bu kanal kayıtlı bir destek talebi değil."))
    if t["status"] != "open": return await sendv_eph(it, WN("TICKET KAPALI", "Bu ticket artık aktif değil."))
    if not _ticket_is_staff(it): return await sendv_eph(it, ER("YETKİN YOK", "Bu ticketı yalnızca ayarlanmış destek yetkilileri üstlenebilir."))
    if t.get("claimed_by"):
        if t["claimed_by"] == it.user.id: return await sendv_eph(it, WN("ZATEN ÜSTLENDİN", "Bu ticket zaten senin üzerinde."))
        return await sendv_eph(it, WN("ZATEN ÜSTLENİLMİŞ", "Bu ticketı <@" + str(t["claimed_by"]) + "> üstlenmiş."))
    db.q("UPDATE tickets SET claimed_by=? WHERE channel_id=?", (it.user.id, it.channel.id))
    t = db.one("SELECT * FROM tickets WHERE channel_id=?", (it.channel.id,))
    await _ticket_apply_permissions(it.channel, t, it.guild)
    try: await it.response.edit_message(content=ticket_text(t), view=TicketActionView())
    except Exception:
        try: await it.response.defer()
        except Exception: pass
    await rp_ch(it.channel, OK("🎫 TICKET ÜSTLENİLDİ", it.user.mention + " bu ticketı **üstlendi**.\n🔒 Administrator olmayan diğer yetkililer artık mesaj gönderemez.\n👮 Üstlenen yetkili ve Administrator müdahale edebilir."))
    await guild_log_send(it.guild, head("ticket", "TICKET ÜSTLENİLDİ") + "\n\nTicket: <#" + str(it.channel.id) + ">\nYetkili: " + it.user.mention, "ticket")

async def tk_trans(it):
    t = db.one("SELECT * FROM tickets WHERE channel_id=?", (it.channel.id,))
    if not t: return await sendv_eph(it, ER("TALEP BULUNAMADI", "Bu kanal kayıtlı bir destek talebi değil."))
    if not (_ticket_is_admin(it.user) or _ticket_can_manage(t, it.user) or it.user.id == t["user_id"]): return await sendv_eph(it, ER("YETKİN YOK", "Transkripti ticket sahibi, üstlenen yetkili veya Administrator alabilir."))
    await it.response.defer(ephemeral=True)
    data = await ticket_transcript(it.channel, t)
    try: await it.followup.send("🧾 **Transkript hazır**", file=discord.File(io.BytesIO(data), filename="talep-" + str(t.get("number") or it.channel.id) + ".txt"), ephemeral=True)
    except Exception as ex: await sendf_eph(it, ER("TRANSKRİPT HATASI", str(ex)[:150]))

async def tk_close(it):
    t = db.one("SELECT * FROM tickets WHERE channel_id=?", (it.channel.id,))
    if not t: return await sendv_eph(it, ER("TALEP BULUNAMADI", "Bu kanal kayıtlı bir destek talebi değil."))
    if not (_ticket_is_admin(it.user) or _ticket_can_manage(t, it.user) or it.user.id == t["user_id"]): return await sendv_eph(it, ER("YETKİN YOK", "Talebi sadece ticket sahibi, üstlenen yetkili veya Administrator kapatabilir."))
    await sendv_eph(it, WN("TALEP KAPATILIYOR", "Transkript hazırlanıyor, kanal **10 saniye** içinde silinecek."))
    try: await it.message.edit(content=ticket_text(dict(t, status="closed")), view=None)
    except Exception: pass
    await ticket_finish(it.guild, it.channel, t, it.user)
    await asyncio.sleep(10)
    try: await it.channel.delete(reason="Talep kapatıldı")
    except Exception: pass

async def tk_mine(it):
    t = db.one("SELECT * FROM tickets WHERE guild_id=? AND user_id=? AND status='open'", (it.guild.id, it.user.id,))
    if t: await sendv_eph(it, OK("AÇIK TİCKETIN VAR", "Ticket kanalın: <#" + str(t["channel_id"]) + ">\nDurum: " + ("🟡 Üstlenildi" if t.get("claimed_by") else "🟢 Yetkili bekleniyor")))
    else: await sendv_eph(it, WN("AÇIK TİCKETIN YOK", "Şu an açık destek ticketın bulunmuyor."))

class TicketCategorySelect(Select):
    def __init__(self):
        super().__init__(placeholder="🎫 Ticket türünü seç...", min_values=1, max_values=1, custom_id="katre_ticket_category_v6", options=[discord.SelectOption(label=nm, value=k, emoji=em, description="Yeni " + nm.lower() + " talebi oluştur") for k,(em,nm,_) in TICKET_CATS.items()])
    async def callback(self, it):
        await it.response.send_message("⚡ **Ticket önceliğini seç:**", view=TicketPriorityView(self.values[0]), ephemeral=True)

class TicketOpenView(View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(TicketCategorySelect())

class TicketPriorityView(View):
    def __init__(self, cat):
        super().__init__(timeout=180)
        self.add_item(TicketPrioritySelect(cat))

class TicketPrioritySelect(Select):
    def __init__(self, cat):
        self.cat = cat
        super().__init__(placeholder="⚡ Öncelik seç...", min_values=1, max_values=1, custom_id="katre_ticket_priority_" + cat, options=[discord.SelectOption(label=nm, value=k, emoji=em) for k,(em,nm) in TICKET_PRIORITIES.items()])
    async def callback(self, it):
        await it.response.send_modal(TicketModal(self.cat, self.values[0]))

class TicketActionView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Üstlen", style=discord.ButtonStyle.success, emoji="👮", custom_id="katre_ticket_claim_v6")
    async def claim(self, it, button): await tk_claim(it)

    @discord.ui.button(label="Transkript", style=discord.ButtonStyle.secondary, emoji="🧾", custom_id="katre_ticket_transcript_v6")
    async def transcript(self, it, button): await tk_trans(it)

    @discord.ui.button(label="Kapat", style=discord.ButtonStyle.danger, emoji="🔒", custom_id="katre_ticket_close_v6")
    async def close(self, it, button): await tk_close(it)

def ticket_view_v2(t=None, closed=False):
    return None if closed else TicketActionView()

def ticket_open_v2(guild=None): return TicketOpenView()

def ticket_open_v2_text():
    return head("ticket", "DESTEK MERKEZİ") + "\n\nAşağıdaki menüden ticket türünü seç. Ardından **öncelik** seçip formu doldur. Form tamamlanınca sana özel ticket kanalı açılır.\n\n" + e("info") + " Aynı anda yalnızca **1 açık** ticket açabilirsin."

class TicketGoView(View):
    def __init__(self, url):
        super().__init__(timeout=300)
        self.add_item(Button(label="🎫 Tickete Git", style=discord.ButtonStyle.link, url=url))

class TicketModal(Modal, title="Destek Talebi"):
    konu = TextInput(label="Konu", max_length=100, placeholder="Sorununu kısaca yaz")
    acik = TextInput(label="Açıklama", style=discord.TextStyle.paragraph, max_length=900, placeholder="Detayları ve ne beklediğini anlat...")
    def __init__(self, cat="destek", priority="normal"):
        super().__init__(title=(_tcat(cat)[1] + " Talebi")[:45]); self.cat = cat; self.priority = _priority_key(priority)
    async def on_submit(self, it):
        g = it.guild
        if not g: return
        await it.response.defer(ephemeral=True)
        ex = db.one("SELECT channel_id FROM tickets WHERE guild_id=? AND user_id=? AND status='open'", (g.id, it.user.id))
        if ex:
            ch0 = g.get_channel(ex["channel_id"])
            return await sendf_eph(it, ER("AÇIK TİCKETIN VAR", "Zaten açık ticketın var: " + (ch0.mention if ch0 else "#" + str(ex["channel_id"]))))
        em, nm, _ = _tcat(self.cat); priority = self.priority
        num = int(db.one("SELECT COALESCE(MAX(number),0) c FROM tickets WHERE guild_id=?", (g.id,))["c"] or 0) + 1
        cat = discord.utils.get(g.categories, name="DESTEK")
        if not cat:
            try: cat = await g.create_category("DESTEK")
            except Exception as e2: return await sendf_eph(it, ER("KATEGORİ OLUŞTURULAMADI", "Botun Kanalları Yönet yetkisi olmalı.\n`" + str(e2)[:120] + "`"))
        roles = _ticket_staff_roles(g)
        if not roles: return await sendf_eph(it, ER("TICKET YETKİLİLERİ AYARLANMADI", "Önce Administrator `k!ticketayar @YetkiliRol` ile ticket yetkili rolünü ayarlamalı."))
        ow = {g.default_role: discord.PermissionOverwrite(view_channel=False), it.user: discord.PermissionOverwrite(view_channel=True, send_messages=True, attach_files=True, read_message_history=True), g.me: discord.PermissionOverwrite(view_channel=True, send_messages=True, manage_channels=True, manage_messages=True, read_message_history=True)}
        for role in roles: ow[role] = discord.PermissionOverwrite(view_channel=True, send_messages=True, attach_files=True, read_message_history=True)
        try: ch = await g.create_text_channel(self.cat + "-" + str(num).zfill(4), category=cat, overwrites=ow, topic=nm + " • " + str(it.user) + " • #" + str(num), reason="Destek talebi")
        except Exception as e2: return await sendf_eph(it, ER("KANAL AÇILAMADI", "Talep kanalı oluşturulamadı.\n`" + str(e2)[:150] + "`"))
        db.q("INSERT INTO tickets(channel_id,guild_id,user_id,subject,category,created_at,number,description,priority) VALUES(?,?,?,?,?,?,?,?,?)", (ch.id, g.id, it.user.id, self.konu.value[:100], self.cat, datetime.datetime.now().isoformat(), num, self.acik.value[:900], priority))
        t = db.one("SELECT * FROM tickets WHERE channel_id=?", (ch.id,))
        await ch.send(it.user.mention + " " + " ".join(r.mention for r in roles), allowed_mentions=discord.AllowedMentions(users=True, roles=True))
        await ch.send(OK("🎫 YENİ TICKET", it.user.mention + " tarafından yeni bir **" + nm + "** ticket açıldı.\n" + _priority_text(priority) + " **Öncelik**\n\nYetkili ekipten bir kişi **Üstlen** butonuna basmalıdır.\nÜstlenildikten sonra Administrator olmayan diğer yetkililer yazamaz."), allowed_mentions=discord.AllowedMentions(users=True, roles=True))
        await ch.send(ticket_text(t), view=TicketActionView())
        await ch.send("-# `k!ticket bilgi` • `k!ticket ekle @üye` • `k!ticket çıkar @üye` • `k!ticket kapat`")
        await guild_log_send(g, head("ticket", "TICKET AÇILDI") + "\n\nTicket: " + ch.mention + "\nAçan: " + it.user.mention + "\nTür: **" + nm + "**\n" + _priority_text(priority) + " **Öncelik**", "ticket")
        await it.followup.send(OK("TİCKET OLUŞTURULDU", "Özel ticket kanalın hazır: " + ch.mention + "\nÖncelik: **" + TICKET_PRIORITIES[priority][1] + "**"), view=TicketGoView(ch.jump_url), ephemeral=True)

class TicketPanel(TicketOpenView): pass

class AppOpenPanel(Panel):
    def __init__(self, text):
        super().__init__(text, timeout=None)
        async def a(it): await it.response.send_modal(AppModal())
        self.btn("Yetkili Başvurusu Yap", a, emoji=e("clip"), cid="ka_open")
class AppModal(Modal, title="Yetkili Başvurusu"):
    yas = TextInput(label="Yaş", max_length=2); den = TextInput(label="Deneyimin", style=discord.TextStyle.paragraph, max_length=500)
    ned = TextInput(label="Neden yetkili olmak istiyorsun?", style=discord.TextStyle.paragraph, max_length=500); akt = TextInput(label="Aktif saatlerin", max_length=100)
    async def on_submit(self, it):
        st = db.one("SELECT * FROM app_settings WHERE guild_id=?", (it.guild.id,))
        if not st or not st["log_ch"]: return await it.response.send_message(ER("KURULU DEĞİL", "`k!başvuru-ayarla`"), ephemeral=True)
        if db.one("SELECT 1 FROM applications WHERE guild_id=? AND user_id=? AND status='pending'", (it.guild.id, it.user.id)): return await it.response.send_message(WN("BEKLEYEN BAŞVURUN VAR", "Önceki başvurun hâlâ inceleniyor. Sonuçlanınca sana haber verilecek. ⏳"), ephemeral=True)
        cur = db.q("INSERT INTO applications(guild_id,user_id,answers,ts) VALUES(?,?,?,?)", (it.guild.id, it.user.id, json.dumps({"y":self.yas.value,"d":self.den.value,"n":self.ned.value,"a":self.akt.value}), datetime.datetime.now().isoformat()))
        aid = cur.lastrowid; ch = it.guild.get_channel(st["log_ch"])
        if ch:
            m = await rp_ch(ch, head("clip", "BAŞVURU #" + str(aid)) + "\n\n" + KV([(e("dot")+"Kim", it.user.mention), (e("cake")+"Yaş", self.yas.value), (e("shield")+"Deneyim", self.den.value[:250]), (e("heart")+"Neden", self.ned.value[:250])]), AppReviewPanel(aid, " "))
            db.q("UPDATE applications SET message_id=? WHERE id=?", (m.id, aid))
        await it.response.send_message(OK("BAŞVURUN ALINDI", "Başvuru numaran: **#" + str(aid) + "**\nYetkililer inceleyince sana DM ile haber verilecek. 📬"), ephemeral=True)
class AppReviewPanel(Panel):
    def __init__(self, aid, text):
        super().__init__(text, timeout=None); self.aid = aid
        async def yk(it):
            ok = it.user.guild_permissions.administrator
            st = db.one("SELECT * FROM app_settings WHERE guild_id=?", (it.guild.id,))
            if st and st["staff_role"]:
                r = it.guild.get_role(st["staff_role"])
                if r and r in it.user.roles: ok = True
            if not ok: await sendv_eph(it, ER("YETKİ YOK", "Bu işlemi yapmak için gerekli yetkiye sahip değilsin.")); return False
            return True
        async def acc(it):
            if not await yk(it): return
            a = db.one("SELECT * FROM applications WHERE id=?", (self.aid,))
            if not a or a["status"] != "pending": return await sendv_eph(it, WN("BAŞVURU ZATEN İŞLENDİ", "Bu başvuru için daha önce karar verilmiş."))
            db.q("UPDATE applications SET status='accepted' WHERE id=?", (self.aid,))
            st = db.one("SELECT * FROM app_settings WHERE guild_id=?", (it.guild.id,))
            r = it.guild.get_role(st["staff_role"]) if st and st["staff_role"] else None
            mb = it.guild.get_member(a["user_id"])
            if r and mb:
                try: await mb.add_roles(r, reason="Başvuru")
                except Exception: pass
            try: await it.message.edit(content=OK("BAŞVURU KABUL EDİLDİ", "Bu başvuru yetkili ekibi tarafından **kabul** edildi. 🎊"), view=None)
            except Exception: pass
            u = it.client.get_user(a["user_id"])
            if u:
                try: await u.send(OK("BAŞVURUN KABUL EDİLDİ!", "**" + it.guild.name + "** sunucusundaki yetkili başvurun kabul edildi.\nEkibe hoş geldin! 🎉"))
                except Exception: pass
            await sendv_eph(it, OK("BAŞVURU KABUL EDİLDİ", "<@" + str(a["user_id"]) + "> artık yetkili ekibinde. ✅"))
        async def rej(it):
            if not await yk(it): return
            a = db.one("SELECT * FROM applications WHERE id=?", (self.aid,))
            if not a or a["status"] != "pending": return await sendv_eph(it, WN("BAŞVURU ZATEN İŞLENDİ", "Bu başvuru için daha önce karar verilmiş."))
            db.q("UPDATE applications SET status='rejected' WHERE id=?", (self.aid,))
            try: await it.message.edit(content=ER("BAŞVURU REDDEDİLDİ", "Bu başvuru yetkili ekibi tarafından **reddedildi**."), view=None)
            except Exception: pass
            await sendv_eph(it, ER("BAŞVURU REDDEDİLDİ", "<@" + str(a["user_id"]) + "> kullanıcısının başvurusu reddedildi."))
        self.btn("Kabul", acc, style=discord.ButtonStyle.success, emoji=e("check"), cid="ka_acc_" + str(aid))
        self.btn("Red", rej, style=discord.ButtonStyle.danger, emoji=e("cross"), cid="ka_rej_" + str(aid))

class TVNameModal(Modal, title="Oda İsmi"):
    def __init__(self, cid):
        super().__init__(); self.cid = cid; self.ni = TextInput(label="Yeni isim", max_length=50); self.add_item(self.ni)
    async def on_submit(self, it):
        ch = it.client.get_channel(self.cid)
        if not ch: return await it.response.send_message(ER("ODA BULUNAMADI", "Bu özel oda artık mevcut değil."), ephemeral=True)
        await ch.edit(name=self.ni.value[:50]); await it.response.send_message(OK("ODA ADI DEĞİŞTİ", "Odanın yeni adı: **" + ch.name + "**"), ephemeral=True)
class TVLimitModal(Modal, title="Oda Limiti"):
    def __init__(self, cid):
        super().__init__(); self.cid = cid; self.li = TextInput(label="Limit 0-99", max_length=2); self.add_item(self.li)
    async def on_submit(self, it):
        ch = it.client.get_channel(self.cid)
        if not ch: return await it.response.send_message(ER("ODA BULUNAMADI", "Bu özel oda artık mevcut değil."), ephemeral=True)
        try: n = max(0, min(99, int(self.li.value)))
        except ValueError: n = 0
        await ch.edit(user_limit=n or None); await it.response.send_message(OK("ODA LİMİTİ AYARLANDI", "Yeni kişi limiti: **" + str(n or "sınırsız") + "** 👥"), ephemeral=True)
class TVPanel(Panel):
    def __init__(self, cid, text):
        super().__init__(text, timeout=None); self.cid = cid
        async def oc(it):
            row = db.one("SELECT * FROM temp_channels WHERE channel_id=?", (self.cid,))
            if not row or row["owner_id"] != it.user.id: await sendv_eph(it, ER("YETKİN YOK", "Bu odanın sahibi sen değilsin, sadece oda sahibi yönetebilir.")); return None
            ch = it.client.get_channel(self.cid)
            if not ch: await sendv_eph(it, ER("ODA BULUNAMADI", "Bu özel oda artık mevcut değil.")); return None
            return ch
        async def lock(it):
            ch = await oc(it)
            if not ch: return
            lk = ch.overwrites_for(ch.guild.default_role).connect is False
            await ch.set_permissions(ch.guild.default_role, connect=None if lk else False, view_channel=None if lk else False)
            await sendv_eph(it, OK("ODA KİLİDİ", "Odan artık herkese **açık**. 🔓" if lk else "Odan **kilitlendi**, kimse giremez. 🔒"))
        async def nm(it):
            if await oc(it): await it.response.send_modal(TVNameModal(self.cid))
        async def lm(it):
            if await oc(it): await it.response.send_modal(TVLimitModal(self.cid))
        async def iv(it):
            ch = await oc(it)
            if ch: await sendv_eph(it, OK("ODA DAVETİ HAZIR", "Tek kullanımlık, **1 saat** geçerli bağlantı:\n" + (await ch.create_invite(max_uses=1, max_age=3600)).url))
        async def dl(it):
            ch = await oc(it)
            if not ch: return
            db.q("DELETE FROM temp_channels WHERE channel_id=?", (self.cid,)); await ch.delete(reason="Sahibi sildi"); await sendv_eph(it, OK("ODA SİLİNDİ", "Özel ses odan kalıcı olarak silindi. 🗑️"))
        self.btn("Kilitle/Aç", lock, style=discord.ButtonStyle.secondary, emoji=e("lock"), cid="tv_lock_" + str(cid))
        self.btn("İsim", nm, emoji="✏️", cid="tv_name_" + str(cid))
        self.btn("Limit", lm, emoji="👥", cid="tv_limit_" + str(cid))
        self.btn("Davet", iv, style=discord.ButtonStyle.success, cid="tv_inv_" + str(cid))
        self.btn("Sil", dl, style=discord.ButtonStyle.danger, emoji=e("trash"), cid="tv_del_" + str(cid))

# ═══════════════════════════════════════════════════════════════════
# 📖 KELİME OYUNU YARDIMCILARI (TDK doğrulama + cooldown)
# ═══════════════════════════════════════════════════════════════════
WG_COOLDOWN = 4          # saniye: aynı kişi iki kelime arasında en az bu kadar beklemeli
WG_CD = {}; WG_WARN = {}; TDK_CACHE = {}
_CIRC = str.maketrans("âîûêô", "aiueo")
def tr_lower(s): return str(s).replace("İ", "i").replace("I", "ı").lower()
def wg_norm(s): return tr_lower(s).translate(_CIRC)
def wg_need(w):
    w = wg_norm(w)
    for ch in reversed(w):
        if ch != "ğ": return ch
    return w[-1:] if w else ""
async def tdk_check(word):
    """'ok' = sözlükte var • 'yok' = yok • 'ozel' = sadece özel isim • None = TDK'ya ulaşılamadı"""
    if word in TDK_CACHE: return TDK_CACHE[word]
    try:
        url = "https://sozluk.gov.tr/gts?ara=" + urllib.parse.quote(word)
        async with aiohttp.ClientSession(headers={"User-Agent": "Mozilla/5.0"}) as ses:
            async with ses.get(url, timeout=aiohttp.ClientTimeout(total=6)) as r:
                if r.status != 200: return None
                data = await r.json(content_type=None)
    except Exception:
        return None
    res = "yok"
    if isinstance(data, list):
        ex = [x for x in data if isinstance(x, dict) and wg_norm(str(x.get("madde", ""))).strip() == word]
        if ex: res = "ok" if any(str(x.get("ozel_mi", "0")) != "1" for x in ex) else "ozel"
    if len(TDK_CACHE) > 5000: TDK_CACHE.clear()
    TDK_CACHE[word] = res
    return res

MAINT_CD = {}
class KatreBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.all()
        intents.message_content = True
        intents.guild_messages = True
        intents.guilds = True
        super().__init__(command_prefix=self.get_prefix, intents=intents, case_insensitive=True, help_command=None, allowed_mentions=discord.AllowedMentions(users=True, roles=False, everyone=False))
        self.start_time = datetime.datetime.now(); self.xp_cd = {}; self.ar_cd = {}; self._si = 0; self.spam = {}; self.flood = {}; self.joins = {}
    async def get_prefix(self, m):
        # k! daima geçerli kalsın; sunucu özel prefixi bunun üzerine ekle.
        prefixes = {"k!", "K!"}
        if m.guild:
            try:
                row = db.one("SELECT prefix FROM servers WHERE guild_id=?", (m.guild.id,))
                custom = (row["prefix"] if row else "") or ""
                custom = str(custom).strip()
                if custom:
                    prefixes.update({custom, custom.lower(), custom.upper()})
            except Exception:
                pass
        if self.user:
            prefixes.add("<@" + str(self.user.id) + "> ")
            prefixes.add("<@!" + str(self.user.id) + "> ")
        return list(prefixes)
    async def setup_hook(self):
        self.gwv = GiveawayPanel(self, " ")
        for v in (self.gwv, TicketOpenView(), TicketActionView(), AppOpenPanel(" "), HelpPanel(self, " "), OwnerPanel(self, " ")): self.add_view(v)
        if V2_OK:
            for mk in (lambda: help_v2(self, " "),):
                try: self.add_view(mk())
                except Exception: traceback.print_exc()
        self.status_loop.start(); self.gw_checker.start(); self.pro_checker.start(); self.backup_loop.start(); self.stats_loop.start()
    async def on_ready(self):
        try:
            for r in db.all("SELECT * FROM role_menus"):
                g = self.get_guild(r["guild_id"])
                if not g: continue
                roles = [(rid, g.get_role(rid).name) for rid in json.loads(r["role_ids"]) if g.get_role(rid)]
                if roles: self.add_view(RoleMenuPanel(r["menu_id"], roles, " "))
            for r in db.all("SELECT id FROM applications WHERE status='pending'"): self.add_view(AppReviewPanel(r["id"], " "))
            for r in db.all("SELECT channel_id FROM temp_channels"): self.add_view(TVPanel(r["channel_id"], " "))
            for r in db.all("SELECT id,options FROM polls WHERE status='active'"):
                p = db.one("SELECT * FROM polls WHERE id=?", (r["id"],)); self.add_view(PollPanel(r["id"], json.loads(r["options"]), poll_content(p)))
            if not EMO_CACHE:
                for g in self.guilds:
                    if auto_map_emojis(g): break
        except Exception: traceback.print_exc()
        if BACKUP_CH:
            try:
                if not EMO_CACHE:
                    d = await pull_backup(self, "emoji")
                    if d: print("☁️ emoji:", emoji_restore(d))
                if not db.all("SELECT 1 FROM users WHERE pro=1") and not db.all("SELECT 1 FROM pro_logs"):
                    d = await pull_backup(self, "pro")
                    if d: print("☁️ pro:", pro_restore(d))
                if not db.all("SELECT 1 FROM servers"):
                    d = await pull_backup(self, "settings")
                    if d: print("☁️ ayar+half:", settings_restore(d))
            except Exception: traceback.print_exc()
            _HASH["emoji"] = json.dumps(EMO_CACHE, sort_keys=True); _HASH["pro"] = json.dumps(pro_snapshot(), sort_keys=True, default=str); _HASH["set"] = json.dumps(settings_snapshot(), sort_keys=True, default=str)
        refresh_emojis(); await check_update(self)
        print("💧 KATRE v" + BOT_VERSION + " | " + str(self.user) + " | " + str(len(self.guilds)) + " sunucu | " + str(len(self.commands)) + " komut")
        print("🩺 TEŞHİS | V2(Layout): " + ("AÇIK" if HAS_V2 else "KAPALI→legacy") + " | OWNER: " + str(OWNER_ID) + " | BAKIM: " + ("AÇIK!" if is_maintenance() else "kapalı"))
        await self.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="k!yardım | Katre Bot"))
    @tasks.loop(seconds=12)
    async def status_loop(self):
        o = self.get_user(OWNER_ID); on = o.display_name if o else "Owner"
        ms = [(discord.ActivityType.watching, "k!yardım | Katre Bot"), (discord.ActivityType.playing, str(len(self.guilds)) + " sunucuda"), (discord.ActivityType.listening, str(sum(g.member_count or 0 for g in self.guilds)) + " kullanıcıya"), (discord.ActivityType.competing, "k!quiz"), (discord.ActivityType.watching, "Owner: " + on), (discord.ActivityType.playing, "k!pro"), (discord.ActivityType.listening, "k!duyuru 📣")]
        t, m = ms[self._si % len(ms)]; self._si += 1
        try: await self.change_presence(activity=discord.Activity(type=t, name=m))
        except Exception: pass
    @tasks.loop(seconds=15)
    async def gw_checker(self):
        nw = datetime.datetime.now().timestamp()
        for g in db.all("SELECT * FROM giveaways WHERE status='active' AND end_time<=?", (nw,)): await finalize_giveaway(self, g["message_id"])
    @tasks.loop(minutes=5)
    async def pro_checker(self):
        nw = datetime.datetime.now()
        for r in db.all("SELECT user_id FROM users WHERE pro=1 AND pro_expiry IS NOT NULL AND pro_expiry<?", (nw.isoformat(),)):
            db.q("UPDATE users SET pro=0 WHERE user_id=?", (r["user_id"],)); pro_log(r["user_id"], "SÜRESİ DOLDU")
    @tasks.loop(minutes=1)
    async def backup_loop(self):
        if not BACKUP_CH: return
        eh = json.dumps(EMO_CACHE, sort_keys=True); ph = json.dumps(pro_snapshot(), sort_keys=True, default=str); sh = json.dumps(settings_snapshot(), sort_keys=True, default=str)
        if _HASH["emoji"] is None: _HASH["emoji"] = eh
        if _HASH["pro"] is None: _HASH["pro"] = ph
        if _HASH["set"] is None: _HASH["set"] = sh
        if eh != _HASH["emoji"]: _HASH["emoji"] = eh; await push_backup(self, "emoji", EMO_CACHE)
        if ph != _HASH["pro"]: _HASH["pro"] = ph; await push_backup(self, "pro", pro_snapshot())
        if sh != _HASH["set"]: _HASH["set"] = sh; await push_backup(self, "settings", settings_snapshot())
    @tasks.loop(minutes=10)
    async def stats_loop(self):
        try:
            row = db.one("SELECT value FROM bot_meta WHERE key='stats_ch'")
            if not row: return
            ch = self.get_channel(int(row["value"]))
            if not ch: return
            up = str(datetime.datetime.now() - self.start_time).split(".")[0]
            top = db.all("SELECT cmd FROM cmd_stats ORDER BY uses DESC LIMIT 3")
            txt = head("chart", "CANLI İSTATİSTİK") + "\n\n" + KV([(e("dot")+"Sunucu", len(self.guilds)), (e("dot")+"Kullanıcı", sum(g.member_count or 0 for g in self.guilds)), (e("dot")+"Komut", len(self.commands)), (e("dot")+"Uptime", up), (e("dot")+"Ping", str(round(self.latency*1000))+"ms"), (e("fire")+"Top", ", ".join("k!"+t["cmd"] for t in top) or "—")])
            old = db.one("SELECT value FROM bot_meta WHERE key='stats_msg'")
            if old:
                try: await (await ch.fetch_message(int(old["value"]))).delete()
                except Exception: pass
            m = await rp_ch(ch, txt)
            if m: db.q("INSERT OR REPLACE INTO bot_meta(key,value) VALUES('stats_msg',?)", (str(m.id),))
        except Exception: traceback.print_exc()
    async def punish(self, m, mn, r):
        try: await m.timeout(datetime.timedelta(minutes=mn), reason=r); return True
        except Exception: return False
    async def mod_log(self, g, t):
        await guild_log_send(g, t, "moderation")
    async def wg_reject(self, m, title, body, short, dm_card=True):
        """Hatalı mesajı kanaldan siler, açıklamayı DM'den gönderir. DM kapalıysa kanalda kısa süreli not bırakır."""
        try: await m.delete()
        except Exception: pass
        if not dm_card: return
        txt = ER(title, body + "\n\n" + e("info") + " Mesajın **" + m.guild.name + " › #" + m.channel.name + "** kanalından silindi.")
        dm = None
        try: dm = await rp_ch(m.author, txt)
        except Exception: dm = None
        if dm is None:
            try:
                t = await rp_ch(m.channel, WN("MESAJ SİLİNDİ", m.author.mention + " " + short + " (DM'in kapalı olduğu için buraya yazdım)"))
                if t: await t.delete(delay=6)
            except Exception: pass
    async def word_game(self, m, wg):
        try:
            raw = (m.content or "").strip(); w = wg_norm(raw)
            valid_fmt = bool(w) and " " not in w and w.isalpha() and len(w) >= 3
            if not valid_fmt and m.author.guild_permissions.manage_messages: return
            nw = datetime.datetime.now().timestamp(); key = (m.guild.id, m.author.id)
            # ⏱️ COOLDOWN
            left = WG_COOLDOWN - (nw - WG_CD.get(key, 0))
            if left > 0:
                send_dm = (nw - WG_WARN.get(key, 0)) > 10
                if send_dm: WG_WARN[key] = nw
                return await self.wg_reject(m, "ÇOK HIZLISIN", "Kelime oyununda kelimeler arasında **" + str(WG_COOLDOWN) + " saniye** beklemelisin.\nYaklaşık **" + sn_txt(left) + "** sonra tekrar yaz.", "çok hızlı yazıyor, mesaj silindi.", dm_card=send_dm)
            WG_CD[key] = nw
            # 🔤 BİÇİM
            if not valid_fmt:
                shown = "`" + (raw[:40] or "boş/ek mesaj") + "`"
                return await self.wg_reject(m, "GEÇERSİZ MESAJ", shown + " kelime oyunu kanalına uygun değil.\nBu kanala yalnızca **tek bir Türkçe kelime** yazılabilir (en az 3 harf; boşluk, sayı ve sembol olmaz).\nSohbet için başka bir kanalı kullanabilirsin.", "kanala yalnızca tek kelime yazılabilir.")
            def rule_fail(wgr):
                lw = wgr["last_word"]; lu = wgr["last_user"]
                if lw and w == wg_norm(lw): return ("TEKRAR KELİME", "**" + w + "** kelimesi az önce yazıldı; farklı bir kelime bulmalısın.", "aynı kelimeyi yazdı.")
                if lw and w[0] != wg_need(lw): return ("YANLIŞ HARF", "Kelime **«" + wg_need(lw).upper() + "»** harfiyle başlamalıydı.\nSon kelime: **" + lw + "**" + ("\n(ğ ile biten kelimelerde bir önceki harf esas alınır.)" if wg_norm(lw).endswith("ğ") else ""), "yanlış harfle başlayan kelime yazdı.")
                if lu == m.author.id: return ("SIRA SENDE DEĞİL", "Ardışık iki kelimeyi aynı kişi yazamaz.\nBaşka bir üyenin kelime yazmasını bekle.", "art arda kelime yazdı.")
                return None
            f = rule_fail(wg)
            if f: return await self.wg_reject(m, f[0], f[1], f[2])
            # 📖 TDK DOĞRULAMA
            st = await tdk_check(w)
            if st == "yok":
                return await self.wg_reject(m, "TDK'DA BULUNAMADI", "**" + w + "** kelimesi TDK Güncel Türkçe Sözlük'te bulunamadı.\nYazımı kontrol edip geçerli bir Türkçe kelime dene.", "geçersiz kelime yazdı (TDK'da yok).")
            if st == "ozel":
                return await self.wg_reject(m, "ÖZEL İSİM", "**" + w + "** sözlükte yalnızca özel isim olarak geçiyor.\nKelime oyununda özel isimler kullanılamaz; cins isim, fiil vb. dene.", "özel isim yazdı.")
            # TDK'ya ulaşılamazsa (st=None) oyun bozulmasın diye kelime kabul edilir.
            wg2 = db.one("SELECT * FROM wordgame WHERE guild_id=?", (m.guild.id,))
            if not wg2: return
            f = rule_fail(wg2)
            if f: return await self.wg_reject(m, f[0], f[1], f[2])
            try: await m.add_reaction(e("check"))
            except Exception: pass
            sk = (wg2["streak"] or 0) + 1; bonus = 15 + (50 if sk % 5 == 0 else 0)
            ensure_user(m.author.id, str(m.author))
            db.q("UPDATE users SET coins=coins+? WHERE user_id=?", (bonus, m.author.id))
            db.q("UPDATE wordgame SET last_word=?, last_user=?, streak=? WHERE guild_id=?", (w, m.author.id, sk, m.guild.id))
            if sk % 5 == 0:
                await rp_ch(m.channel, head("fire", "SERİ " + str(sk) + "!") + "\n\n" + m.author.mention + " → **+50 bonus coin**\nSıradaki kelime **«" + wg_need(w).upper() + "»** harfiyle başlamalı!")
        except Exception:
            traceback.print_exc()
    async def protections(self, m):
        try:
            if not m.guild or m.author.guild_permissions.administrator: return
            if not m.guild.me.guild_permissions.moderate_members: return
            p = db.one("SELECT * FROM protections WHERE guild_id=?", (m.guild.id,))
            if not p: return
            nw = datetime.datetime.now().timestamp(); c = m.content or ""
            if p["anti_link"] and re.search(r"(https?://|discord\.gg/|www\.)", c, re.I):
                try: await m.delete()
                except Exception: pass
                await self.mod_log(m.guild, e("link") + " ANTİ-LİNK: " + m.author.mention)
            elif p["badword"]:
                ws = [w["word"] for w in db.all("SELECT word FROM badwords WHERE guild_id=?", (m.guild.id,))]
                if any(w and w in c.lower() for w in ws):
                    try: await m.delete()
                    except Exception: pass
                    await self.punish(m.author, 1, "Küfür"); await self.mod_log(m.guild, e("warn") + " KÜFÜR: " + m.author.mention)
            if p["anti_spam"]:
                dq = self.spam.setdefault(m.guild.id, {}).setdefault(m.author.id, deque()); dq.append(nw)
                while dq and nw - dq[0] > 5: dq.popleft()
                if len(dq) >= 7:
                    dq.clear(); await self.punish(m.author, 5, "Spam")
                    try: await m.channel.purge(limit=6, check=lambda x: x.author.id == m.author.id)
                    except Exception: pass
                    await self.mod_log(m.guild, e("cross") + " SPAM: " + m.author.mention)
            if p["anti_flood"]:
                k = (m.guild.id, m.author.id); pv = self.flood.get(k)
                cn = (pv[1] + 1) if (pv and pv[0] == c and nw - pv[2] < 10) else 1
                self.flood[k] = (c, cn, nw)
                if cn >= 3:
                    self.flood[k] = (c, 0, nw)
                    try: await m.delete()
                    except Exception: pass
                    await self.mod_log(m.guild, e("warn") + " FLOOD: " + m.author.mention)
        except Exception: traceback.print_exc()
    async def on_message(self, m):
        if m.author.bot: return
        try:
            prefs = await self.get_prefix(m)
            is_command_message = bool(m.content and any(m.content.startswith(p) for p in prefs))
            if is_maintenance() and m.author.id != OWNER_ID:
                if is_command_message:
                    nw = datetime.datetime.now().timestamp()
                    if nw - MAINT_CD.get(m.author.id, 0) > 30:
                        MAINT_CD[m.author.id] = nw
                        try: await rp_ch(m.channel, head("warn", "BAKIMDAYIZ") + "\n\nŞu anda bakım modundayız; komutlar geçici olarak kapalı.")
                        except Exception: pass
                return
            if db.one("SELECT 1 FROM blacklist WHERE user_id=?", (m.author.id,)): return
        except Exception: pass
        try:
            a = db.one("SELECT * FROM afk WHERE user_id=?", (m.author.id,))
            if a:
                dk = int((datetime.datetime.now() - datetime.datetime.fromisoformat(a["since"])).total_seconds() // 60)
                db.q("DELETE FROM afk WHERE user_id=?", (m.author.id,))
                msg = await rp_ch(m.channel, head("wave", "DÖNDÜ") + "\n\n" + m.author.mention + " • **" + sure_txt(dk) + "** • **" + str(a["mentions"] or 0) + "** mention")
                try: await msg.delete(delay=20)
                except Exception: pass
            if m.guild:
                for mm in m.mentions:
                    a = db.one("SELECT * FROM afk WHERE user_id=?", (mm.id,))
                    if a:
                        db.q("UPDATE afk SET mentions=mentions+1 WHERE user_id=?", (mm.id,))
                        await rp_ch(m.channel, head("sleep", mm.display_name + " AFK") + "\n\n**" + (a["reason"] or "—") + "**"); break
        except Exception: pass
        try:
            await self.protections(m)
            if m.guild and not is_command_message:
                wg = db.one("SELECT * FROM wordgame WHERE guild_id=?", (m.guild.id,))
                if wg and wg["channel_id"] == m.channel.id:
                    await self.word_game(m, wg)
            if m.guild and not is_command_message:
                nw = datetime.datetime.now().timestamp()
                if nw - self.ar_cd.get(m.guild.id, 0) > 3:
                    low = (m.content or "").lower()
                    for r in db.all("SELECT * FROM auto_replies WHERE guild_id=?", (m.guild.id,)):
                        if r["trigger"] and r["trigger"] in low:
                            self.ar_cd[m.guild.id] = nw; await rp_ch(m.channel, r["response"][:1900]); break
            ensure_user(m.author.id, str(m.author))
            if m.guild:
                db.q("UPDATE users SET messages=messages+1, name=? WHERE user_id=?", (str(m.author), m.author.id))
                nw = datetime.datetime.now().timestamp()
                s = db.one("SELECT rank_on FROM servers WHERE guild_id=?", (m.guild.id,))
                if (not s or s["rank_on"]) and nw - self.xp_cd.get(m.author.id, 0) > 60:
                    self.xp_cd[m.author.id] = nw
                    u = db.one("SELECT xp,level,xp2 FROM users WHERE user_id=?", (m.author.id,))
                    g = random.randint(5, 15) * (2 if u["xp2"] else 1); xp, lv = u["xp"] + g, u["level"]; nd = lv * 100
                    if xp >= nd:
                        xp -= nd; lv += 1; cn = random.randint(50, 150)
                        db.q("UPDATE users SET coins=coins+? WHERE user_id=?", (cn, m.author.id))
                        for lr in db.all("SELECT * FROM level_roles WHERE guild_id=? AND level<=?", (m.guild.id, lv)):
                            rr = m.guild.get_role(lr["role_id"])
                            if rr and rr not in m.author.roles:
                                try: await m.author.add_roles(rr, reason="Seviye")
                                except Exception: pass
                        await rp_ch(m.channel, head("chartup", "SEVİYE") + "\n\n" + m.author.mention + " → **Lv " + str(lv) + "**")
                    db.q("UPDATE users SET xp=?,level=? WHERE user_id=?", (xp, lv, m.author.id))
        except Exception: traceback.print_exc()
        finally:
            await self.process_commands(m)
    async def on_voice_state_update(self, member, before, after):
        try:
            g = member.guild
            if before.channel != after.channel:
                old = before.channel.mention if before.channel else "—"; new = after.channel.mention if after.channel else "—"
                await guild_log_send(g, head("mic", "SES DEĞİŞİKLİĞİ") + "\n\n" + member.mention + "\n> " + old + " → " + new, "voice")
            tv = db.one("SELECT * FROM tempvoice WHERE guild_id=?", (g.id,))
            if tv and after.channel and after.channel.id == tv["trigger_ch"]:
                cat = g.get_channel(tv["category_id"]) if tv["category_id"] else after.channel.category
                ow = {g.default_role: discord.PermissionOverwrite(view_channel=False, connect=False), member: discord.PermissionOverwrite(view_channel=True, connect=True, manage_channels=True, mute_members=True, move_members=True), g.me: discord.PermissionOverwrite(view_channel=True, connect=True, manage_channels=True, move_members=True)}
                ch = await g.create_voice_channel("🔊 " + member.display_name, category=cat, overwrites=ow)
                db.q("INSERT OR REPLACE INTO temp_channels(channel_id,owner_id,guild_id) VALUES(?,?,?)", (ch.id, member.id, g.id))
                self.add_view(TVPanel(ch.id, " ")); await member.move_to(ch, reason="Temp voice")
                try: await member.send(head("mic", "ODAN HAZIR") + "\n\n**" + ch.name + "**", view=TVPanel(ch.id, head("mic", "ODAN HAZIR") + "\n\n**" + ch.name + "**"))
                except Exception: pass
            for chn in (before.channel, after.channel):
                if not chn: continue
                row = db.one("SELECT * FROM temp_channels WHERE channel_id=?", (chn.id,))
                if row and len(chn.members) == 0:
                    db.q("DELETE FROM temp_channels WHERE channel_id=?", (chn.id,))
                    try: await chn.delete(reason="Boş")
                    except Exception: pass
        except Exception: traceback.print_exc()
    async def _reaction_role(self, payload, add=True):
        if not payload.guild_id or payload.user_id == self.user.id: return
        row = db.one("SELECT * FROM reaction_roles WHERE guild_id=? AND message_id=? AND emoji=?", (payload.guild_id, payload.message_id, str(payload.emoji)))
        if not row: return
        g=self.get_guild(payload.guild_id)
        if not g: return
        m=g.get_member(payload.user_id)
        r=g.get_role(row["role_id"])
        if not m or not r: return
        me=g.me
        try:
            if add:
                if me and me.guild_permissions.manage_roles and r < me.top_role: await m.add_roles(r, reason="Katre Reaction Role")
            else:
                if me and me.guild_permissions.manage_roles and r < me.top_role: await m.remove_roles(r, reason="Katre Reaction Role")
            await guild_log_send(g, head("shield", "REACTION ROL") + "\n\n" + m.mention + (" → " if add else " ← ") + r.mention + "\nEmoji: " + str(payload.emoji), "role")
        except Exception: pass
    async def on_raw_reaction_add(self, payload):
        await self._reaction_role(payload, True)
    async def on_raw_reaction_remove(self, payload):
        await self._reaction_role(payload, False)

    async def on_guild_channel_create(self, ch):
        if ch.guild: await guild_log_send(ch.guild, head("gear", "KANAL OLUŞTURULDU") + "\n\n" + ch.mention + " • " + str(ch.type) + " • Oluşturan: Discord/entegrasyon", "channel")
    async def on_guild_channel_delete(self, ch):
        if ch.guild: await guild_log_send(ch.guild, head("trash", "KANAL SİLİNDİ") + "\n\n**#" + ch.name + "** • " + str(ch.type), "channel")
    async def on_guild_channel_update(self, before, after):
        changes = []
        if before.name != after.name: changes.append("Ad: `" + before.name + "` → `" + after.name + "`")
        if getattr(before, "category_id", None) != getattr(after, "category_id", None): changes.append("Kategori değişti")
        if getattr(before, "topic", None) != getattr(after, "topic", None): changes.append("Konu değişti")
        if getattr(before, "slowmode_delay", None) != getattr(after, "slowmode_delay", None): changes.append("Yavaş mod: `" + str(getattr(before, "slowmode_delay", 0)) + "` → `" + str(getattr(after, "slowmode_delay", 0)) + "` sn")
        if getattr(before, "nsfw", None) != getattr(after, "nsfw", None): changes.append("NSFW: `" + str(getattr(after, "nsfw", False)) + "`")
        if getattr(before, "default_auto_archive_duration", None) != getattr(after, "default_auto_archive_duration", None): changes.append("Otomatik arşiv süresi değişti")
        if changes: await guild_log_send(after.guild, head("gear", "KANAL GÜNCELLENDİ") + "\n\n" + after.mention + "\n" + "\n".join(changes), "channel")
    async def on_guild_channel_pins_update(self, channel, last_pin):
        await guild_log_send(channel.guild, head("pin", "KANAL SABİTLERİ DEĞİŞTİ") + "\n\nKanal: " + channel.mention + "\nSon sabit: " + (discord.utils.format_dt(last_pin, "R") if last_pin else "Yok"), "channel")

    async def on_guild_integrations_update(self, guild):
        await guild_log_send(guild, head("gear", "ENTEGRASYONLAR GÜNCELLENDİ") + "\n\nSunucunun entegrasyon ayarları değişti.", "server")

    async def on_guild_role_create(self, role):
        await guild_log_send(role.guild, head("shield", "ROL OLUŞTURULDU") + "\n\n" + role.mention + " • ID: `" + str(role.id) + "`", "role")
    async def on_guild_role_delete(self, role):
        await guild_log_send(role.guild, head("shield", "ROL SİLİNDİ") + "\n\n**" + role.name + "** • ID: `" + str(role.id) + "`", "role")
    async def on_guild_role_update(self, before, after):
        changes=[]
        if before.name != after.name: changes.append("Ad: `" + before.name + "` → `" + after.name + "`")
        if before.permissions != after.permissions: changes.append("İzinler değişti")
        if before.hoist != after.hoist: changes.append("Ayrı gösterim değişti")
        if changes: await guild_log_send(after.guild, head("shield", "ROL GÜNCELLENDİ") + "\n\n" + after.mention + "\n" + "\n".join(changes), "role")
    async def on_message_edit(self, b, a):
        if b.author.bot or not b.guild or b.content == a.content: return
        await guild_log_send(b.guild, head("pen", "MESAJ DÜZENLENDİ") + "\n\nKanal: " + b.channel.mention + "\nYazar: " + b.author.mention + "\nEski: `" + ((b.content or "")[:700] or "_boş_") + "`\nYeni: `" + ((a.content or "")[:700] or "_boş_") + "`\nMesaj: " + a.jump_url, "message")
    async def on_message_delete(self, m):
        try:
            if m.author.bot or not m.guild: return
            db.q("INSERT OR REPLACE INTO snipe(channel_id,author_id,content,attachment,ts) VALUES(?,?,?,?,?)", (m.channel.id, m.author.id, (m.content or "")[:1000], m.attachments[0].url if m.attachments else None, datetime.datetime.now().isoformat()))
            atts = "\nEkler: " + ", ".join(x.url for x in m.attachments[:5]) if m.attachments else ""
            await guild_log_send(m.guild, head("trash", "MESAJ SİLİNDİ") + "\n\nKanal: " + m.channel.mention + "\nYazar: " + m.author.mention + "\nİçerik: `" + ((m.content or "")[:900] or "_ek/boş_") + "`" + atts, "message")
        except Exception: pass
    async def on_member_remove(self, m):
        try:
            s = db.one("SELECT * FROM servers WHERE guild_id=?", (m.guild.id,)) or {}
            if s.get("leave_ch"):
                ch = m.guild.get_channel(s["leave_ch"])
                if ch:
                    text = _format_greeting(s.get("leave_message"), m, "leave")
                    if HAS_V2:
                        await ch.send(view=_greeting_view(text, m, 0xED4245))
                    else:
                        await ch.send(text)
        except Exception: pass
        await guild_log_send(m.guild, e("wave") + " **AYRILDI** › " + str(m) + " • ID: `" + str(m.id) + "`", "member")
    async def on_member_update(self, b, a):
        changes = []
        if b.nick != a.nick: changes.append("🏷️ Nick: `" + str(b.nick or a.name) + "` → `" + str(a.nick or a.name) + "`")
        br = {r.id: r for r in b.roles}; ar = {r.id: r for r in a.roles}
        added = [ar[x].mention for x in ar.keys() - br.keys() if not ar[x].is_default()]
        removed = [br[x].mention for x in br.keys() - ar.keys() if not br[x].is_default()]
        if added: changes.append("➕ Roller: " + ", ".join(added[:15]))
        if removed: changes.append("➖ Roller: " + ", ".join(removed[:15]))
        if b.timed_out_until != a.timed_out_until:
            changes.append("⏱️ Timeout: " + (discord.utils.format_dt(a.timed_out_until, "R") if a.timed_out_until else "kaldırıldı"))
        if changes:
            await guild_log_send(a.guild, head("shield", "ÜYE GÜNCELLENDİ") + "\n\n" + a.mention + " • ID: `" + str(a.id) + "`\n" + "\n".join(changes), "member")

    async def on_member_ban(self, guild, user):
        await guild_log_send(guild, head("hammer", "BAN") + "\n\nÜye: <@" + str(user.id) + "> • ID: `" + str(user.id) + "`", "moderation")

    async def on_member_unban(self, guild, user):
        await guild_log_send(guild, head("unlock", "UNBAN") + "\n\nKullanıcı: <@" + str(user.id) + "> • ID: `" + str(user.id) + "`", "moderation")

    async def on_bulk_message_delete(self, messages):
        if not messages: return
        g = messages[0].guild
        if not g: return
        await guild_log_send(g, head("trash", "TOPLU MESAJ SİLİNDİ") + "\n\nKanal: " + messages[0].channel.mention + "\nMesaj sayısı: **" + str(len(messages)) + "**", "message")

    async def on_guild_update(self, before, after):
        changes = []
        if before.name != after.name: changes.append("Ad: `" + before.name + "` → `" + after.name + "`")
        if before.icon != after.icon: changes.append("Sunucu ikonu değişti")
        if before.banner != after.banner: changes.append("Sunucu bannerı değişti")
        if before.description != after.description: changes.append("Açıklama değişti")
        if before.verification_level != after.verification_level: changes.append("Doğrulama seviyesi değişti")
        if before.default_notifications != after.default_notifications: changes.append("Varsayılan bildirim ayarı değişti")
        if changes: await guild_log_send(after, head("gear", "SUNUCU GÜNCELLENDİ") + "\n\n" + "\n".join(changes), "server")

    async def on_invite_create(self, invite):
        if invite.guild: await guild_log_send(invite.guild, head("link", "DAVET OLUŞTURULDU") + "\n\nKanal: " + (invite.channel.mention if invite.channel else "-") + "\nKod: `" + str(invite.code) + "`\nOluşturan: " + (invite.inviter.mention if invite.inviter else "Bilinmiyor"), "invite")

    async def on_invite_delete(self, invite):
        if invite.guild: await guild_log_send(invite.guild, head("link", "DAVET SİLİNDİ") + "\n\nKanal: " + (invite.channel.mention if invite.channel else "-") + "\nKod: `" + str(invite.code) + "`", "invite")

    async def on_webhooks_update(self, channel):
        await guild_log_send(channel.guild, head("gear", "WEBHOOK GÜNCELLENDİ") + "\n\nKanal: " + channel.mention, "webhook")

    async def on_thread_create(self, thread):
        await guild_log_send(thread.guild, head("chat", "THREAD OLUŞTURULDU") + "\n\nThread: <#" + str(thread.id) + ">\nAd: **" + thread.name + "**", "thread")

    async def on_thread_update(self, before, after):
        changes = []
        if before.name != after.name: changes.append("Ad: `" + before.name + "` → `" + after.name + "`")
        if before.archived != after.archived: changes.append("Arşiv: " + str(after.archived))
        if before.locked != after.locked: changes.append("Kilit: " + str(after.locked))
        if changes: await guild_log_send(after.guild, head("chat", "THREAD GÜNCELLENDİ") + "\n\n<#" + str(after.id) + ">\n" + "\n".join(changes), "thread")

    async def on_thread_delete(self, thread):
        await guild_log_send(thread.guild, head("trash", "THREAD SİLİNDİ") + "\n\n**" + thread.name + "** • ID: `" + str(thread.id) + "`", "thread")

    async def on_guild_emojis_update(self, guild, before, after):
        b = {x.id: x for x in before}; a = {x.id: x for x in after}
        added = [x.name for i,x in a.items() if i not in b]; removed = [x.name for i,x in b.items() if i not in a]
        if added or removed: await guild_log_send(guild, head("spark", "EMOJİLER GÜNCELLENDİ") + "\n\n➕ " + (", ".join(added) or "-") + "\n➖ " + (", ".join(removed) or "-"), "emoji")

    async def on_guild_stickers_update(self, guild, before, after):
        b = {x.id: x for x in before}; a = {x.id: x for x in after}
        added = [x.name for i,x in a.items() if i not in b]; removed = [x.name for i,x in b.items() if i not in a]
        if added or removed: await guild_log_send(guild, head("spark", "STICKERLAR GÜNCELLENDİ") + "\n\n➕ " + (", ".join(added) or "-") + "\n➖ " + (", ".join(removed) or "-"), "sticker")
    async def on_command_completion(self, ctx):
        db.q("INSERT INTO cmd_stats(cmd,uses) VALUES(?,1) ON CONFLICT(cmd) DO UPDATE SET uses=uses+1", (ctx.command.name,))
        if ctx.guild:
            await guild_log_send(ctx.guild, head("terminal", "KOMUT KULLANILDI") + "\n\nKullanıcı: " + ctx.author.mention + " • ID: `" + str(ctx.author.id) + "`\nKanal: " + ctx.channel.mention + "\nKomut: `" + ctx.message.content[:500].replace("`", "ˋ") + "`", "command")
    async def on_command_error(self, ctx, er):
        if isinstance(er, OwnerOnly): return
        if isinstance(er, ProOnly):
            v = Panel(head("pro", "PRO GEREKLİ") + "\n\nBu komut sadece PRO üyelere özel.\n📋 `k!pro` • 💎 `k!probonus`")
            v.btn_url("Pro Destek", SUPPORT_URL, emoji=e("diamond"))
            await rp(ctx, v.text, v); return
        if isinstance(er, commands.CommandNotFound):
            await rp(ctx, WN("KOMUT BULUNAMADI", "Böyle bir komut yok.\nTüm komutları görmek için `" + pf(ctx) + "yardım` yaz.")); return
        if isinstance(er, commands.MissingRequiredArgument):
            await rp(ctx, ER("EKSİK ARGÜMAN", "**" + arg_label(ctx.command, er.param.name) + "** bilgisi eksik.\nKullanım: `" + usage_of(ctx) + "`" + desc_line(ctx.command))); return
        if isinstance(er, commands.BadArgument):
            arg = str(getattr(er, "argument", "") or "")[:60]
            if isinstance(er, commands.MemberNotFound): why = "**" + arg + "** adlı üye bulunamadı.\nÜyeyi etiketle (@üye) veya ID'sini yaz."
            elif isinstance(er, commands.UserNotFound): why = "**" + arg + "** adlı kullanıcı bulunamadı.\nKullanıcıyı etiketle veya ID'sini yaz."
            elif isinstance(er, commands.RoleNotFound): why = "**" + arg + "** adlı rol bulunamadı.\nRolü etiketle (@rol) veya ID'sini yaz."
            elif isinstance(er, commands.ChannelNotFound): why = "**" + arg + "** adlı kanal bulunamadı.\nKanalı etiketle (#kanal) veya ID'sini yaz."
            else: why = "Girdiğin değer geçersiz.\nSayı beklenen yere yazı yazmadığından veya doğru türde değer girdiğinden emin ol."
            await rp(ctx, ER("GEÇERSİZ DEĞER", why + "\nKullanım: `" + usage_of(ctx) + "`")); return
        if isinstance(er, commands.CommandOnCooldown):
            await rp(ctx, WN("BİRAZ BEKLE", "Bu komutu tekrar kullanabilmek için **" + sn_txt(er.retry_after) + "** beklemelisin.\nKomut: `" + pf(ctx) + ctx.command.name + "`")); return
        if isinstance(er, commands.BotMissingPermissions):
            await rp(ctx, ER("BOT YETKİSİ EKSİK", "Bu işlem için bende şu yetki(ler) eksik: `" + ", ".join(er.missing_permissions) + "`\nKatre rolüne **Yönetici** ver ve rolü listenin en üstüne taşı.")); return
        if isinstance(er, commands.MissingPermissions): await rp(ctx, ER("YETKİN YOK", "Bu komutu kullanmak için şu yetki(ler) gerekli: `" + ", ".join(er.missing_permissions) + "`")); return
        if isinstance(er, commands.CheckFailure): await rp(ctx, ER("YETKİ YOK", "Bu komutu kullanma iznin yok.")); return
        if isinstance(er, commands.CommandInvokeError):
            o = er.original
            if isinstance(o, discord.Forbidden):
                try: await ctx.author.send(ER("YETKİ YOK", "#" + str(ctx.channel) + " kanalında işlem yapma yetkim yok.\nKanal izinlerini veya Katre rolünü kontrol et."))
                except Exception: pass
                return
            er = o
        await rp(ctx, WN("BEKLENMEYEN HATA", "Komut çalışırken bir sorun oluştu. Tekrar dene; sürerse yetkiliye bildir.") + "\n```\n" + str(er)[:700] + "\n```"); traceback.print_exc()
    async def on_member_join(self, mb):
        ensure_user(mb.id, str(mb))
        try:
            p = db.one("SELECT * FROM protections WHERE guild_id=?", (mb.guild.id,))
            if p and p["anti_raid"]:
                nw = datetime.datetime.now().timestamp(); dq = self.joins.setdefault(mb.guild.id, deque()); dq.append(nw)
                while dq and nw - dq[0] > 10: dq.popleft()
                if len(dq) >= 8 and nw > (p["raid_until"] or 0):
                    db.q("UPDATE protections SET raid_until=? WHERE guild_id=?", (nw + 600, mb.guild.id)); await self.mod_log(mb.guild, head("shield", "RAID") + "\n\n10dk kilit!")
                if (p["raid_until"] or 0) > nw:
                    try: await mb.kick(reason="Anti-raid")
                    except Exception: pass
                    return
        except Exception: traceback.print_exc()
        s = db.one("SELECT * FROM servers WHERE guild_id=?", (mb.guild.id,))
        if s:
            if s["auto_role"]:
                r = mb.guild.get_role(s["auto_role"])
                if r:
                    try: await mb.add_roles(r, reason="Otorol")
                    except Exception: pass
            if s["welcome_ch"]:
                ch = mb.guild.get_channel(s["welcome_ch"])
                if ch:
                    try:
                        text = _format_greeting(s.get("welcome_message"), mb, "welcome")
                        if HAS_V2: await ch.send(view=_greeting_view(text, mb, 0x57F287))
                        else: await ch.send(text)
                    except Exception: pass
            await guild_log_send(mb.guild, head("wave", "ÜYE KATILDI") + "\n\n" + mb.mention + " • " + str(mb) + "\nHesap: <t:" + str(int(mb.created_at.timestamp())) + ":R>", "member")
        try:
            c = db.one("SELECT * FROM counters WHERE guild_id=?", (mb.guild.id,))
            if c and not c["reached"]:
                ch = mb.guild.get_channel(c["channel_id"])
                if ch:
                    cu = mb.guild.member_count
                    if cu >= c["target"]:
                        db.q("UPDATE counters SET reached=1 WHERE guild_id=?", (mb.guild.id,)); await rp_ch(ch, head("party", "HEDEF") + "\n\n**" + str(c["target"]) + "** üye!")
                    else: await rp_ch(ch, head("target", "SAYAÇ") + "\n\n**" + str(cu) + "/" + str(c["target"]) + "**\n" + bar(cu / c["target"] * 100))
        except Exception: pass
    async def on_guild_join(self, g):
        ensure_server(g.id); db.q("INSERT OR IGNORE INTO protections(guild_id) VALUES(?)", (g.id,))
        if g.system_channel:
            await guild_log_send(g, head("logo", "BOT SUNUCUYA KATILDI") + "\n\nSunucu: **" + g.name + "** • ID: `" + str(g.id) + "`\nÜye: **" + str(g.member_count or 0) + "**", "bot")
        if not EMO_CACHE: auto_map_emojis(g)
        ch = g.system_channel or next((c for c in g.text_channels if c.permissions_for(g.me).send_messages), None)
        if ch:
            v = Panel(head("logo", "KATRE ARANIZDA") + "\n\n`k!yardım` • `k!kurulum` • `k!kelimekur`"); v.btn_url("Destek", SUPPORT_URL, emoji=e("link"))
            await rp_ch(ch, v.text, v)

    async def on_guild_remove(self, g):
        try:
            await guild_log_send(g, head("cross", "BOT SUNUCUDAN AYRILDI") + "\n\nSunucu: **" + g.name + "** • ID: `" + str(g.id) + "`", "bot")
        except Exception: pass

async def finalize_giveaway(bot, mid):
    gw = db.one("SELECT * FROM giveaways WHERE message_id=?", (mid,))
    if not gw or gw["status"] != "active": return
    p = json.loads(gw["participants"]); db.q("UPDATE giveaways SET status='ended' WHERE message_id=?", (mid,))
    ch = bot.get_channel(gw["channel_id"])
    if not ch: return
    if not p:
        try: await rp_ch(ch, head("warn", "BİTTİ") + "\n\n**" + gw["prize"] + "** katılımcı yok.")
        except Exception: pass
        return
    n = min(gw["winners"], len(p)); ws = [bot.get_user(int(w)) for w in random.sample(p, n)]
    men = "\n".join(w.mention if w else "?" for w in ws); jump = None
    try:
        msg = await ch.fetch_message(mid); jump = msg.jump_url
        await msg.edit(content=gw_end(gw, men, p), view=GwJumpPanel(gw_end(gw, men, p), jump))
    except Exception: pass
    await rp_ch(ch, head("party", "SONUÇ") + "\n\n" + men + " kazandı!")
    for w in ws:
        if w:
            try: await w.send(head("star", "KAZANDIN") + "\n\n**" + gw["prize"] + "** • " + ch.guild.name, view=GwJumpPanel(" ", jump) if jump else None)
            except Exception: pass

bot = KatreBot()

# ═══════════════════════════════════════════════════════════════════
#  💧 BÖLÜM 2/2 — KOMUTLAR (v5.8 • gelişmiş ticket • çekiliş yönetimi • dengeli, açıklayıcı cevaplar)
# ═══════════════════════════════════════════════════════════════════
def tip(t): return "\n💡 *" + t + "*"
def medal(i): return ["🥇", "🥈", "🥉"][i] if i < 3 else "**" + str(i + 1) + ".**"
def usage_cmd(c, p="k!"):
    ps = []
    for n, pr in c.clean_params.items():
        lb = arg_label(c, n)
        ps.append(("<" + lb + ">") if pr.default is inspect.Parameter.empty else ("[" + lb + "]"))
    return p + c.name + ((" " + " ".join(ps)) if ps else "")

@kategori("genel")
@bot.command(name="yardım", aliases=["yardim","help","komutlar"], help="Yardım menüsü")
@commands.cooldown(1, 5, commands.BucketType.user)
async def yardim(ctx):
    if V2_OK:
        try:
            await ctx.send(view=help_v2(bot, help_content(bot))); return
        except Exception: traceback.print_exc()
    await rp(ctx, help_content(bot), HelpPanel(bot, help_content(bot)))
@kategori("genel")
@bot.command(name="komutbilgi", aliases=["cmd"], help="<komut> — detay")
async def komutbilgi(ctx, *, name: str):
    c = bot.get_command(name.lower().replace("k!", "").strip())
    if not c: return await rp(ctx, ER("KOMUT BULUNAMADI", "`" + name[:30] + "` adında bir komut yok.\nTüm komutlar için `k!yardım` yaz."))
    al = ", ".join("`" + a + "`" for a in c.aliases) or "—"
    await rp(ctx, head("info", "k!" + c.name + " HAKKINDA") + "\n\n**Açıklama:** " + (c.help or "—") + "\n**Kullanım:** `" + usage_cmd(c) + "`\n**Takma adlar:** " + al + "\n**Kategori:** " + CATS.get(getattr(c, "kategori", ""), ("", "—"))[1])
@kategori("genel")
@bot.command(name="ping", help="Gecikme")
async def ping(ctx):
    ms = round(bot.latency * 1000); t0 = time.perf_counter(); m = await ctx.send("🏓")
    rt = round((time.perf_counter() - t0) * 1000)
    try: await m.delete()
    except Exception: pass
    q = max(0, min(100, int(100 - ms / 4)))
    dr = "harika, çok hızlıyım! 🚀" if ms < 100 else "normal seviyede ✅" if ms < 200 else "biraz yoğunum ama çalışıyorum ⚠️"
    await rp(ctx, head("bolt", "PONG!") + "\n\n" + KV([(e("dot")+"Websocket", str(ms) + " ms"), (e("dot")+"Mesaj gecikmesi", str(rt) + " ms")]) + "\n\n**Bağlantı kalitesi**\n" + bar(q) + "\nDurum: " + dr)
@kategori("genel")
@bot.command(name="istatistik", aliases=["stats"], help="Bot istatistiği")
async def istatistik(ctx):
    up = str(datetime.datetime.now() - bot.start_time).split(".")[0]; ms = round(bot.latency * 1000)
    await rp(ctx, head("chart", "BOT İSTATİSTİKLERİ") + "\n\nKatre'nin anlık durumu:\n" + KV([(e("dot")+"Sunucu", len(bot.guilds)), (e("dot")+"Kullanıcı", sum(g.member_count or 0 for g in bot.guilds)), (e("dot")+"Komut", len(bot.commands)), (e("dot")+"Çalışma süresi", up), (e("dot")+"Ping", str(ms) + " ms"), (e("dot")+"V2 kart", "Açık" if HAS_V2 else "Kapalı")]))
@kategori("genel")
@bot.command(name="mesajtop", help="Mesaj sıralaması")
async def mesajtop(ctx):
    rs = db.all("SELECT * FROM users ORDER BY messages DESC LIMIT 10")
    if not rs: return await rp(ctx, WN("HENÜZ VERİ YOK", "Mesaj istatistiği henüz oluşmadı.\nSohbet ettikçe liste dolacak." ))
    await rp(ctx, head("pen", "MESAJ SIRALAMASI") + "\n\nEn çok mesaj yazan ilk 10 üye:\n" + "\n".join(medal(i) + " <@" + str(r["user_id"]) + "> ─ **" + str(r["messages"]) + "** mesaj" for i, r in enumerate(rs)))
@kategori("genel")
@bot.command(name="davet", aliases=["invite"], help="Davet")
async def davet(ctx):
    u = "https://discord.com/oauth2/authorize?client_id=" + str(bot.user.id) + "&permissions=8&scope=bot%20applications.commands"
    v = Panel(head("logo", "KATRE'Yİ SUNUCUNA EKLE") + "\n\nAşağıdaki butonla botu kendi sunucuna ekleyebilir, takıldığın yerde destek sunucusundan yardım alabilirsin.")
    v.btn_url("Botu Ekle", u, emoji="➕"); v.btn_url("Destek", SUPPORT_URL, emoji=e("link"))
    await rp(ctx, v.text, v)
@kategori("genel")
@bot.command(name="avatar", aliases=["av","pfp"], help="Avatar")
async def avatar(ctx, u: discord.Member = None):
    u = u or ctx.author
    v = Panel(head("cam", u.display_name + " • PROFİL FOTOĞRAFI") + "\n\nFotoğrafı tam boyutta görmek için butona bas.")
    v.btn_url("Tam Boyutta Aç", u.display_avatar.url, emoji=e("link"))
    await rp(ctx, v.text, v)
@kategori("genel")
@bot.command(name="oda", help="<isim/limit/kilit/davet/sil> — odanı yönet")
async def oda(ctx, i: str = "bilgi", *, arg=None):
    row = db.one("SELECT * FROM temp_channels WHERE owner_id=? AND guild_id=?", (ctx.author.id, ctx.guild.id))
    if not row: return await rp(ctx, ER("ODAN YOK", "Şu an sahibi olduğun bir özel oda yok." + tip("Temp voice kanalına girerek kendi odanı kurabilirsin.")))
    ch = ctx.guild.get_channel(row["channel_id"])
    if not ch:
        db.q("DELETE FROM temp_channels WHERE channel_id=?", (row["channel_id"],)); return await rp(ctx, WN("ODAN SİLİNMİŞ", "Kayıtlı odan artık yok." + tip("Temp voice kanalına girerek yenisini kurabilirsin.")))
    i = i.lower()
    if i == "isim" and arg: await ch.edit(name=arg[:50]); await rp(ctx, OK("ODA ADI DEĞİŞTİ", "Odanın yeni adı: **" + ch.name + "**"))
    elif i == "limit" and arg:
        try: n = max(0, min(99, int(arg)))
        except ValueError: return await rp(ctx, ER("GEÇERSİZ LİMİT", "Limit için **0-99** arası bir sayı yazmalısın.\nÖrnek: `k!oda limit 5`"))
        await ch.edit(user_limit=n or None); await rp(ctx, OK("LİMİT AYARLANDI", "Odana en fazla **" + (str(n) if n else "sınırsız") + "** kişi girebilir."))
    elif i == "kilit":
        lk = ch.overwrites_for(ctx.guild.default_role).connect is False
        await ch.set_permissions(ctx.guild.default_role, connect=None if lk else False, view_channel=None if lk else False)
        await rp(ctx, OK("ODA AÇILDI" if lk else "ODA KİLİTLENDİ", "Odan artık herkese açık." if lk else "Odana artık sadece izinli üyeler girebilir.\nAçmak için tekrar `k!oda kilit` yaz."))
    elif i == "davet": await rp(ctx, OK("DAVET LİNKİ HAZIR", "Tek kullanımlık ve **1 saat** geçerli:\n" + (await ch.create_invite(max_uses=1, max_age=3600)).url))
    elif i == "sil":
        db.q("DELETE FROM temp_channels WHERE channel_id=?", (ch.id,)); await ch.delete(); await rp(ctx, OK("ODA SİLİNDİ", "Özel odan kapatıldı ve kayıtlardan temizlendi."))
    else: await rp(ctx, head("mic", "ODAN: " + ch.name) + "\n\n" + e("arrow") + " `k!oda isim <yeni ad>` ─ adı değiştirir\n" + e("arrow") + " `k!oda limit <0-99>` ─ kişi sınırı koyar\n" + e("arrow") + " `k!oda kilit` ─ kilitler / açar\n" + e("arrow") + " `k!oda davet` ─ tek kullanımlık link\n" + e("arrow") + " `k!oda sil` ─ odayı kapatır" + tip("Aynı işlemleri voice panelindeki butonlarla da yapabilirsin."))
@kategori("genel")
@bot.command(name="rank", aliases=["seviye","level"], help="Seviye kartı")
@commands.cooldown(1, 3, commands.BucketType.user)
async def rank(ctx, u: discord.Member = None):
    u = u or ctx.author; ensure_user(u.id, str(u)); d = db.one("SELECT * FROM users WHERE user_id=?", (u.id,)); nd = max(1, d["level"] * 100)
    pos = db.one("SELECT COUNT(*)+1 AS p FROM users WHERE level>? OR (level=? AND xp>?)", (d["level"], d["level"], d["xp"]))["p"]
    pct = int(d["xp"] / nd * 100)
    txt = (head("chartup", u.display_name + " • SEVİYE KARTI") + "\n\n" + KV([(e("star")+"Seviye", d["level"]), (e("crown")+"Sıralama", "#" + str(pos)), (e("bolt")+"XP", str(d["xp"]) + " / " + str(nd)), (e("pen")+"Mesaj", d["messages"])])
           + "\n\n**Sonraki seviyeye**\n" + bar(pct) + "\n-# Kalan XP: **" + str(max(0, nd - d["xp"])) + "**" + tip("Sohbet ederek XP kazanırsın; seviye atlayınca coin ödülü alırsın."))
    await send_thumb(ctx, txt, u.display_avatar.url, accent=0x3498DB)
@kategori("genel")
@bot.command(name="sıralama", aliases=["sirala","top","lb"], help="Seviye top10")
async def sıralama(ctx):
    rs = db.all("SELECT * FROM users ORDER BY level DESC, xp DESC LIMIT 10")
    if not rs: return await rp(ctx, WN("HENÜZ VERİ YOK", "Seviye sıralaması için henüz yeterli veri yok."))
    await rp(ctx, head("star", "SEVİYE SIRALAMASI") + "\n\nEn yüksek seviyeli ilk 10 üye:\n" + "\n".join(medal(i) + " <@" + str(r["user_id"]) + "> ─ Lv.**" + str(r["level"]) + "**" for i, r in enumerate(rs)))
@kategori("genel")
@bot.command(name="profil", aliases=["profile"], help="Profil")
async def profil(ctx, u: discord.Member = None):
    u = u or ctx.author; ensure_user(u.id, str(u)); d = db.one("SELECT * FROM users WHERE user_id=?", (u.id,)); a = db.one("SELECT * FROM afk WHERE user_id=?", (u.id,))
    col = None
    try:
        if d["pro"] and d["pro_color"]: col = int(str(d["pro_color"]).lstrip("#"), 16)
    except Exception: col = None
    jn = int(u.joined_at.timestamp()) if u.joined_at else int(u.created_at.timestamp())
    txt = (head("logo", u.display_name + " • PROFİL") + "\n\n" + KV([(e("star")+"Seviye", d["level"]), (e("coin")+"Coin", d["coins"]), (e("heart")+"İtibar", d["rep"]), (e("pen")+"Mesaj", d["messages"]),
           (e("diamond")+"Pro", "Evet ✅" if d["pro"] else "Hayır"), (e("sleep")+"AFK", "Evet 💤" if a else "Hayır"), (e("wave")+"Sunucuya katılım", "<t:" + str(jn) + ":D>"), (e("crown")+"En yüksek rol", u.top_role.mention if u.top_role.id != ctx.guild.id else "—")]))
    await send_thumb(ctx, txt, u.display_avatar.url, accent=(col or 0x5865F2))
@kategori("genel")
@bot.command(name="sunucubilgi", aliases=["serverinfo"], help="Sunucu")
async def sunucubilgi(ctx):
    g = ctx.guild; bots = sum(1 for m in g.members if m.bot); mc = g.member_count or len(g.members)
    txt = (head("logo", g.name + " • SUNUCU BİLGİSİ") + "\n\n" + KV([(e("crown")+"Kurucu", "<@" + str(g.owner_id) + ">"), (e("genel")+"Üye", str(mc) + " (" + str(max(0, mc - bots)) + " kişi • " + str(bots) + " bot)"),
           (e("pen")+"Kanal", str(len(g.text_channels)) + " metin • " + str(len(g.voice_channels)) + " ses"), (e("tag")+"Rol", len(g.roles)), (e("spark")+"Emoji", len(g.emojis)),
           (e("bolt")+"Boost", "Seviye " + str(g.premium_tier) + " • " + str(g.premium_subscription_count or 0) + " takviye"), (e("alarm")+"Kuruluş", "<t:" + str(int(g.created_at.timestamp())) + ":D>")]) + "\n-# ID: " + str(g.id))
    await send_thumb(ctx, txt, g.icon.url if g.icon else None, accent=0x5865F2)
@kategori("genel")
@bot.command(name="snipe", help="Silinen son mesaj")
@commands.cooldown(1, 3, commands.BucketType.user)
async def snipe(ctx):
    s = db.one("SELECT * FROM snipe WHERE channel_id=?", (ctx.channel.id,))
    if not s: return await rp(ctx, WN("SİLİNEN MESAJ YOK", "Bu kanalda yakın zamanda silinmiş bir mesaj kaydı bulunmuyor."))
    await rp(ctx, head("cam", "SON SİLİNEN MESAJ") + "\n\nYazan: <@" + str(s["author_id"]) + ">\nZaman: " + str(s["ts"])[:16].replace("T", " ") + "\n> " + ((s["content"] or "_ek dosya_")[:700]))
@kategori("genel")
@bot.command(name="afk", help="[sebep] — AFK")
async def afk(ctx, *, s=None):
    cur = db.one("SELECT * FROM afk WHERE user_id=?", (ctx.author.id,))
    if cur and not s:
        db.q("DELETE FROM afk WHERE user_id=?", (ctx.author.id,)); return await rp(ctx, OK("AFK BİTTİ", "Tekrar aramıza döndün, hoş geldin! 👋"))
    db.q("INSERT OR REPLACE INTO afk(user_id,reason,since,mentions) VALUES(?,?,?,0)", (ctx.author.id, (s or "—")[:100], datetime.datetime.now().isoformat()))
    await rp(ctx, OK("AFK MODU AÇIK", "Sebep: **" + (s or "—")[:100] + "**\nSeni etiketleyenlere sebebi gösteririm; bir mesaj yazınca AFK otomatik kapanır."))
@kategori("genel")
@bot.command(name="rep", help="<@üye> — itibar")
@commands.cooldown(1, 43200, commands.BucketType.user)
async def rep(ctx, u: discord.Member):
    if u.id == ctx.author.id: return await rp(ctx, ER("OLMAZ", "Kendine itibar puanı veremezsin."))
    ensure_user(u.id, str(u)); db.q("UPDATE users SET rep=rep+1 WHERE user_id=?", (u.id,))
    await rp(ctx, OK("İTİBAR VERİLDİ", u.mention + " üyesine **+1 itibar** verdin." + tip("12 saatte bir itibar verebilirsin.")))
@kategori("genel")
@bot.command(name="destek", aliases=["ticketpanel"], help="Select menülü ticket paneli")
@commands.has_permissions(administrator=True)
async def destek(ctx):
    await ctx.send(ticket_open_v2_text(), view=ticket_open_v2(ctx.guild))
    try: await ctx.message.delete()
    except Exception: pass
@kategori("sys")
@bot.command(name="ticketayar", aliases=["ticket-yetkili"], help="[@rol...] — Ticket yetkili rollerini ayarla")
@commands.has_permissions(administrator=True)
async def ticketayar(ctx, *roles: discord.Role):
    if not roles:
        return await rp(ctx, ER("ROL EKSİK", "En az bir yetkili rolü belirtmelisin.\nÖrnek: `k!ticketayar @Destek @Mod`"))
    roles = list({r.id:r for r in roles}.values())[:10]
    me = ctx.guild.me
    bad = [r for r in roles if r.is_default() or r.managed or (me and r >= me.top_role)]
    if bad: return await rp(ctx, ER("ROL HİYERARŞİSİ", "Botun yönetemeyeceği roller: " + ", ".join(r.name for r in bad[:10]) + "."))
    db.q("INSERT OR REPLACE INTO ticket_settings(guild_id,staff_roles,panel_channel) VALUES(?,?,COALESCE((SELECT panel_channel FROM ticket_settings WHERE guild_id=?),NULL))", (ctx.guild.id, json.dumps([r.id for r in roles]), ctx.guild.id))
    await rp(ctx, OK("TICKET YETKİLİLERİ AYARLANDI", "Ticketlara bakabilecek roller:\n" + " ".join(r.mention for r in roles) + "\n\nÜstlenilmiş ticketlarda Administrator olmayan diğer yetkililer mesaj yazamaz."))
@kategori("sys")
@bot.command(name="ticketdurum", help="Ticket yetkili ayarını göster")
async def ticketdurum(ctx):
    roles = _ticket_staff_roles(ctx.guild)
    await rp(ctx, head("ticket", "TICKET AYARLARI") + "\n\nYetkili roller: " + (", ".join(r.mention for r in roles) if roles else "Ayarlanmadı") + "\n\nKural: Ticket üstlenilince sadece **üstlenen yetkili** ve **Administrator** mesaj yazabilir.")
@kategori("genel")
@bot.command(name="not", help="<metin>")
async def not_(ctx, *, m):
    ensure_user(ctx.author.id, str(ctx.author)); u = db.one("SELECT notes FROM users WHERE user_id=?", (ctx.author.id,))
    n = json.loads(u["notes"]); n.append({"t": m, "d": datetime.datetime.now().isoformat()})
    db.q("UPDATE users SET notes=? WHERE user_id=?", (json.dumps(n), ctx.author.id)); await rp(ctx, OK("NOT KAYDEDİLDİ", "Toplam **" + str(len(n)) + "** notun var." + tip("Hepsini görmek için `k!notlar` yaz.")))
@kategori("genel")
@bot.command(name="notlar", help="Notların")
async def notlar(ctx):
    u = db.one("SELECT notes FROM users WHERE user_id=?", (ctx.author.id,)); n = json.loads(u["notes"]) if u else []
    if not n: return await rp(ctx, WN("NOTUN YOK", "Henüz kayıtlı notun yok." + tip("`k!not <metin>` ile ilk notunu ekleyebilirsin.")))
    await rp(ctx, head("pen", "NOTLARIN") + "\n\nSon " + str(min(8, len(n))) + " notun:\n" + "\n".join(e("arrow") + " `" + x["d"][:10] + "` " + x["t"][:60] for x in n[-8:]))
@kategori("genel")
@bot.command(name="doğumgünü", aliases=["dogumgunu"], help="<gün> <ay>")
async def doğumgünü(ctx, g: int, a: int):
    if not (1 <= g <= 31 and 1 <= a <= 12): return await rp(ctx, ER("GEÇERSİZ TARİH", "Gün **1-31**, ay **1-12** arasında olmalı.\nÖrnek: `k!doğumgünü 24 8`"))
    ensure_user(ctx.author.id, str(ctx.author)); db.q("UPDATE users SET birthday=? WHERE user_id=?", (str(g) + "." + str(a), ctx.author.id)); await rp(ctx, OK("DOĞUM GÜNÜ KAYDEDİLDİ", "Doğum günün **" + str(g) + "." + str(a) + "** olarak ayarlandı. 🎂"))
@kategori("genel")
@bot.command(name="hatırlat", aliases=["hatirlat"], help="<dk> <metin>")
async def hatırlat(ctx, dk: int, *, m):
    if dk < 1 or dk > 1440: return await rp(ctx, ER("GEÇERSİZ SÜRE", "Süre **1-1440 dakika** arasında olmalı.\nÖrnek: `k!hatırlat 30 Ders çalış`"))
    await rp(ctx, OK("HATIRLATICI KURULDU", "**" + sure_txt(dk) + "** sonra bu kanalda seni etiketleyeceğim.\nHatırlatma: " + m[:80])); await asyncio.sleep(dk * 60); await ctx.send(ctx.author.mention + " " + e("alarm") + " **Hatırlatma:** " + m)
@kategori("genel")
@bot.command(name="botkontrol", aliases=["check"], help="Yetki teşhisi")
@commands.has_permissions(administrator=True)
async def botkontrol(ctx):
    p = ctx.channel.permissions_for(ctx.guild.me)
    cs = [("Kanalı görme",p.view_channel),("Mesaj gönderme",p.send_messages),("Bağlantı yerleştirme",p.embed_links),("Mesaj yönetme",p.manage_messages),("Timeout atma",p.moderate_members),("Rol yönetme",p.manage_roles),("Kanal yönetme",p.manage_channels),("Üye yasaklama",p.ban_members)]
    eksik = [n for n, ok in cs if not ok]
    await rp(ctx, head("gear", "BOT YETKİ KONTROLÜ") + "\n\nBu kanaldaki yetkilerim:\n" + "\n".join((e("check") if ok else e("cross")) + " " + n for n, ok in cs) + "\n\n" + ("Her şey yolunda, tüm yetkilerim var! 🎉" if not eksik else "Eksik yetki var. Katre rolüne **Yönetici** ver ve rolü en üste taşı."))

@kategori("mod")
@bot.command(name="yasakla", aliases=["ban"], help="<@üye> [sebep]")
@commands.has_permissions(ban_members=True)
@commands.bot_has_permissions(ban_members=True)
async def yasakla(ctx, u: discord.Member, *, s="—"):
    g = mod_guard(ctx, u, "yasakla")
    if g: return await rp(ctx, ER("İŞLEM YAPILAMADI", g))
    t = head("warn", "BAN ONAYI") + "\n\n**" + str(u) + "** sunucudan **kalıcı olarak** yasaklanacak.\nSebep: " + s[:150] + "\n\nOnaylıyor musun?"; v = ConfirmPanel(t); await rp(ctx, t, v); await v.wait()
    if v.value is None: return await rp(ctx, WN("İŞLEM İPTAL", "Süre içinde onay verilmediği için kimse yasaklanmadı."))
    if v.value:
        try: await u.send(ER("YASAKLANDIN", "**" + ctx.guild.name + "** sunucusundan yasaklandın.\nSebep: " + s[:150]))
        except Exception: pass
        await u.ban(reason=str(ctx.author) + ": " + s[:100]); punish_log(ctx.guild.id, u.id, "BAN", s, ctx.author.id)
        await guild_log_send(ctx.guild, head("hammer", "BAN") + "\n\n" + u.mention + " • Sebep: " + s[:150] + " • Yetkili: " + ctx.author.mention, "moderation")
        await rp(ctx, OK("ÜYE YASAKLANDI", u.mention + " sunucudan banlandı.\nSebep: " + s[:150] + "\nİşlem siciline kaydedildi." + tip("Yasağı kaldırmak için `k!unban <id>` kullan.")))
@kategori("mod")
@bot.command(name="at", aliases=["kick"], help="<@üye> [sebep]")
@commands.has_permissions(kick_members=True)
@commands.bot_has_permissions(kick_members=True)
async def at(ctx, u: discord.Member, *, s="—"):
    g = mod_guard(ctx, u, "at")
    if g: return await rp(ctx, ER("İŞLEM YAPILAMADI", g))
    t = head("warn", "KICK ONAYI") + "\n\n**" + str(u) + "** sunucudan atılacak.\nSebep: " + s[:150] + "\n\nOnaylıyor musun?"; v = ConfirmPanel(t); await rp(ctx, t, v); await v.wait()
    if v.value is None: return await rp(ctx, WN("İŞLEM İPTAL", "Süre içinde onay verilmediği için kimse atılmadı."))
    if v.value:
        await u.kick(reason=str(ctx.author) + ": " + s[:100]); punish_log(ctx.guild.id, u.id, "KICK", s, ctx.author.id)
        await guild_log_send(ctx.guild, head("kick", "KICK") + "\n\n" + u.mention + " • Sebep: " + s[:150] + " • Yetkili: " + ctx.author.mention, "moderation")
        await rp(ctx, OK("ÜYE ATILDI", u.mention + " sunucudan çıkarıldı.\nSebep: " + s[:150] + "\nDavet linkiyle tekrar girebilir."))
@kategori("mod")
@bot.command(name="mute", aliases=["sustur"], help="<@üye> <süre> [sebep]")
@commands.has_permissions(moderate_members=True)
@commands.bot_has_permissions(moderate_members=True)
async def mute(ctx, u: discord.Member, süre: str, *, s="—"):
    g = mod_guard(ctx, u, "sustur")
    if g: return await rp(ctx, ER("İŞLEM YAPILAMADI", g))
    try: dk = parse_sure(süre)
    except Exception: return await rp(ctx, ER("GEÇERSİZ SÜRE", "Süreyi şöyle yaz: `30m`, `1h`, `2d`.\nÖrnek: `k!mute @üye 30m spam`"))
    if dk < 1 or dk > 40320: return await rp(ctx, ER("GEÇERSİZ SÜRE", "Susturma süresi **1 dakika ile 28 gün** arasında olmalı."))
    await u.timeout(datetime.timedelta(minutes=dk), reason=str(ctx.author) + ": " + s[:100]); punish_log(ctx.guild.id, u.id, "MUTE", s, ctx.author.id, dk)
    await guild_log_send(ctx.guild, head("lock", "MUTE") + "\n\n" + u.mention + " • **" + sure_txt(dk) + "** • Yetkili: " + ctx.author.mention, "moderation")
    await rp(ctx, OK("ÜYE SUSTURULDU", u.mention + " **" + sure_txt(dk) + "** boyunca susturuldu.\nSebep: " + s[:150] + tip("Süre bitince otomatik açılır; erken açmak için `k!unmute`.")))
@kategori("mod")
@bot.command(name="unmute", help="<@üye>")
@commands.has_permissions(moderate_members=True)
@commands.bot_has_permissions(moderate_members=True)
async def unmute(ctx, u: discord.Member):
    await u.timeout(None); punish_log(ctx.guild.id, u.id, "UNMUTE", "-", ctx.author.id)
    await rp(ctx, OK("SUSTURMA KALDIRILDI", u.mention + " artık tekrar yazıp konuşabilir."))
@kategori("mod")
@bot.command(name="ceza-sistemi", help="<ayarla a b|kapat|bilgi>")
@commands.has_permissions(administrator=True)
async def ceza_sistemi(ctx, i: str = "bilgi", a: int = 3, b: int = 5):
    i = i.lower()
    if i in ("ayarla","aç"):
        db.q("INSERT OR REPLACE INTO punish_config(guild_id,mute_at,ban_at) VALUES(?,?,?)", (ctx.guild.id, a, b))
        await rp(ctx, OK("OTOMATİK CEZA SİSTEMİ AÇIK", e("arrow") + " **" + str(a) + ". uyarıda** → 1 saat mute\n" + e("arrow") + " **" + str(b) + ". uyarıda** → otomatik ban"))
    elif i in ("kapat","off"):
        db.q("DELETE FROM punish_config WHERE guild_id=?", (ctx.guild.id,)); await rp(ctx, OK("CEZA SİSTEMİ KAPATILDI", "Uyarı sayısına bağlı otomatik cezalar artık uygulanmayacak."))
    else:
        c = db.one("SELECT * FROM punish_config WHERE guild_id=?", (ctx.guild.id,))
        await rp(ctx, head("shield", "OTOMATİK CEZA SİSTEMİ") + "\n\n" + ((e("arrow") + " **" + str(c["mute_at"]) + ". uyarıda** → 1 saat mute\n" + e("arrow") + " **" + str(c["ban_at"]) + ". uyarıda** → otomatik ban") if c else "Şu an **kapalı**." + tip("Açmak için: `k!ceza-sistemi ayarla 3 5`")))
@kategori("mod")
@bot.command(name="ceza-geçmişi", aliases=["cezalar","sicil"], help="[<@üye>]")
@commands.has_permissions(manage_messages=True)
async def ceza_geçmişi(ctx, u: discord.Member = None):
    u = u or ctx.author
    rs = db.all("SELECT * FROM punishments WHERE guild_id=? AND user_id=? ORDER BY id DESC LIMIT 10", (ctx.guild.id, u.id))
    if not rs: return await rp(ctx, OK("SABIKA TEMİZ", u.mention + " üyesinin kayıtlı bir cezası yok. ✨"))
    await rp(ctx, head("log", u.display_name + " • CEZA GEÇMİŞİ") + "\n\nSon " + str(len(rs)) + " kayıt:\n" + "\n".join(e("arrow") + " **" + r["type"] + "** ─ " + r["ts"][:10] + (" ─ " + str(r["reason"])[:40] if r["reason"] and r["reason"] != "—" else "") for r in rs))
@kategori("mod")
@bot.command(name="unban", help="<id> [sebep]")
@commands.has_permissions(ban_members=True)
@commands.bot_has_permissions(ban_members=True)
async def unban(ctx, uid: int, *, s="—"):
    try: b = await ctx.guild.fetch_ban(discord.Object(id=uid))
    except discord.NotFound: return await rp(ctx, ER("BAN BULUNAMADI", "Bu ID yasaklılar listesinde yok.\nListeyi görmek için `k!banlist` yaz."))
    except Exception: return await rp(ctx, ER("LİSTE OKUNAMADI", "Yasaklı listesine erişemedim; **Üye Yasaklama** yetkimi kontrol et."))
    await ctx.guild.unban(b.user, reason=str(ctx.author) + ": " + s[:100]); await rp(ctx, OK("YASAK KALDIRILDI", "**" + str(b.user) + "** artık sunucuya tekrar girebilir."))
@kategori("mod")
@bot.command(name="banlist", help="Banlılar")
@commands.has_permissions(ban_members=True)
async def banlist(ctx):
    bs = [b async for b in ctx.guild.bans()]
    if not bs: return await rp(ctx, OK("YASAKLI YOK", "Bu sunucuda yasaklı kullanıcı bulunmuyor."))
    await rp(ctx, head("hammer", "YASAKLI LİSTESİ") + "\n\nToplam **" + str(len(bs)) + "** yasaklı (ilk 15 gösteriliyor):\n" + "\n".join(e("arrow") + " " + str(b.user) + " ─ `" + str(b.user.id) + "`" for b in bs[:15]) + tip("Kaldırmak için `k!unban <id>`"))
@kategori("mod")
@bot.command(name="nick", help="<@üye> <nick>")
@commands.has_permissions(manage_nicknames=True)
@commands.bot_has_permissions(manage_nicknames=True)
async def nick(ctx, u: discord.Member, *, n):
    g = mod_guard(ctx, u, "nick")
    if g: return await rp(ctx, ER("İŞLEM YAPILAMADI", g))
    await u.edit(nick=n[:32]); await rp(ctx, OK("TAKMA AD DEĞİŞTİ", u.mention + " üyesinin yeni adı: **" + n[:32] + "**"))
@kategori("mod")
@bot.command(name="nicksıfırla", help="<@üye>")
@commands.has_permissions(manage_nicknames=True)
async def nicksıfırla(ctx, u: discord.Member):
    g = mod_guard(ctx, u, "işlem")
    if g: return await rp(ctx, ER("İŞLEM YAPILAMADI", g))
    await u.edit(nick=None); await rp(ctx, OK("TAKMA AD SIFIRLANDI", u.mention + " üyesinin adı orijinal haline döndü."))
@kategori("mod")
@bot.command(name="rolbilgi", help="<@rol>")
async def rolbilgi(ctx, role: discord.Role):
    await rp(ctx, head("shield", role.name + " • ROL BİLGİSİ") + "\n\n" + KV([(e("dot")+"Üye sayısı", len(role.members)), (e("dot")+"Renk", str(role.color)), (e("dot")+"Ayrı gösterim", "Evet" if role.hoist else "Hayır"), (e("dot")+"ID", role.id)]))
@kategori("mod")
@bot.command(name="uyar", aliases=["warn"], help="<@üye> [sebep]")
@commands.has_permissions(manage_messages=True)
async def uyar(ctx, u: discord.Member, *, s="—"):
    if u.id == ctx.author.id: return await rp(ctx, ER("OLMAZ", "Kendini uyaramazsın."))
    ensure_user(u.id, str(u)); db.q("UPDATE users SET warnings=warnings+1 WHERE user_id=?", (u.id,))
    w = db.one("SELECT warnings FROM users WHERE user_id=?", (u.id,))["warnings"]; punish_log(ctx.guild.id, u.id, "WARN", s, ctx.author.id)
    ex = ""; cfg = db.one("SELECT * FROM punish_config WHERE guild_id=?", (ctx.guild.id,))
    if cfg:
        if w == cfg["ban_at"]:
            try:
                await u.ban(reason="Oto " + str(w) + " uyarı"); punish_log(ctx.guild.id, u.id, "AUTO-BAN", str(w), ctx.bot.user.id); ex = "\n\n" + e("hammer") + " Uyarı limitine ulaştı → **otomatik ban** uygulandı."
            except Exception: pass
        elif w == cfg["mute_at"]:
            try:
                await u.timeout(datetime.timedelta(minutes=60), reason="Oto"); punish_log(ctx.guild.id, u.id, "AUTO-MUTE", str(w), ctx.bot.user.id, 60); ex = "\n\n" + e("lock") + " Uyarı limitine ulaştı → **1 saat mute** uygulandı."
            except Exception: pass
    await rp(ctx, WN("ÜYE UYARILDI", u.mention + " uyarıldı. Toplam uyarı: **" + str(w) + "**\nSebep: " + s[:150] + ex))
@kategori("mod")
@bot.command(name="uyarılar", aliases=["warns"], help="[<@üye>]")
async def uyarılar(ctx, u: discord.Member = None):
    u = u or ctx.author; ensure_user(u.id, str(u)); w = db.one("SELECT warnings FROM users WHERE user_id=?", (u.id,))["warnings"]
    await rp(ctx, head("warn", u.display_name + " • UYARILAR") + "\n\n" + u.mention + " üyesinin toplam **" + str(w) + "** uyarısı var." + tip("Ayrıntılar için `k!sicil @üye`"))
@kategori("mod")
@bot.command(name="temizle", aliases=["purge","sil"], help="<adet>")
@commands.has_permissions(manage_messages=True)
@commands.bot_has_permissions(manage_messages=True)
async def temizle(ctx, a: int):
    if not 1 <= a <= 500: return await rp(ctx, ER("GEÇERSİZ ADET", "Silinecek mesaj sayısı **1-500** arasında olmalı.\nÖrnek: `k!temizle 20`"))
    await ctx.channel.purge(limit=a + 1); m = await rp(ctx, OK("MESAJLAR TEMİZLENDİ", "**" + str(a) + "** mesaj silindi.\nBu bilgi 5 saniye sonra kaybolacak."))
    if m: await m.delete(delay=5)
@kategori("mod")
@bot.command(name="say", help="<metin>")
@commands.has_permissions(manage_messages=True)
async def say(ctx, *, m):
    try: await ctx.message.delete()
    except Exception: pass
    await rp(ctx, m[:1900])
@kategori("mod")
@bot.command(name="yavaşmod", aliases=["slowmode"], help="<sn>")
@commands.has_permissions(manage_channels=True)
async def yavaşmod(ctx, s: int):
    s = max(0, min(21600, s)); await ctx.channel.edit(slowmode_delay=s)
    await rp(ctx, OK("YAVAŞ MOD " + ("AÇILDI" if s else "KAPANDI"), ("Üyeler bu kanalda **" + str(s) + " saniyede** bir mesaj yazabilir." if s else "Bu kanalda yavaş mod kaldırıldı.")))
@kategori("mod")
@bot.command(name="kilit", help="Kilitle")
@commands.has_permissions(manage_channels=True)
async def kilit(ctx):
    await ctx.channel.set_permissions(ctx.guild.default_role, send_messages=False); await rp(ctx, OK("KANAL KİLİTLENDİ", "Üyeler bu kanala artık yazamaz." + tip("Açmak için `k!kilitaç` yaz.")))
@kategori("mod")
@bot.command(name="kilitaç", aliases=["unlock"], help="Aç")
@commands.has_permissions(manage_channels=True)
async def kilitaç(ctx):
    await ctx.channel.set_permissions(ctx.guild.default_role, send_messages=None); await rp(ctx, OK("KANAL AÇILDI", "Üyeler bu kanala tekrar yazabilir."))
@kategori("mod")
@bot.command(name="rolver", help="<@rol> <@üye...>")
@commands.has_permissions(manage_roles=True)
@commands.bot_has_permissions(manage_roles=True)
async def rolver(ctx, role: discord.Role, ms: commands.Greedy[discord.Member]):
    if not ms: return await rp(ctx, ER("ÜYE BELİRTMEDİN", "Rolü verilecek üyeleri etiketlemelisin.\nÖrnek: `k!rolver @Rol @ali @veli`"))
    d = 0
    for m in ms:
        try: await m.add_roles(role); d += 1
        except Exception: pass
    await rp(ctx, OK("ROL VERİLDİ", role.mention + " rolü **" + str(d) + "/" + str(len(ms)) + "** üyeye verildi." + ("" if d == len(ms) else tip("Bazı üyelere verilemedi; rolümün onların rolünden üstte olduğundan emin ol."))))
@kategori("mod")
@bot.command(name="rolal", help="<@rol> <@üye...>")
@commands.has_permissions(manage_roles=True)
@commands.bot_has_permissions(manage_roles=True)
async def rolal(ctx, role: discord.Role, ms: commands.Greedy[discord.Member]):
    if not ms: return await rp(ctx, ER("ÜYE BELİRTMEDİN", "Rolü alınacak üyeleri etiketlemelisin.\nÖrnek: `k!rolal @Rol @ali`"))
    d = 0
    for m in ms:
        try: await m.remove_roles(role); d += 1
        except Exception: pass
    await rp(ctx, OK("ROL ALINDI", role.mention + " rolü **" + str(d) + "/" + str(len(ms)) + "** üyeden alındı."))
@kategori("mod")
@bot.command(name="herkeserol", help="<@rol>")
@commands.has_permissions(administrator=True)
@commands.bot_has_permissions(manage_roles=True)
async def herkeserol(ctx, role: discord.Role):
    t = head("warn", "TOPLU ROL ONAYI") + "\n\n**" + str(len(ctx.guild.members)) + "** üyeye " + role.mention + " rolü verilecek.\nBu işlem birkaç dakika sürebilir. Emin misin?"; v = ConfirmPanel(t, 60); await rp(ctx, t, v); await v.wait()
    if not v.value: return await rp(ctx, WN("İŞLEM İPTAL", "Toplu rol dağıtımı yapılmadı."))
    d = 0
    for m in ctx.guild.members:
        if m.bot: continue
        try: await m.add_roles(role); d += 1
        except Exception: pass
    await rp(ctx, OK("TOPLU ROL TAMAMLANDI", "**" + str(d) + "** üyeye " + role.mention + " rolü verildi."))
@kategori("mod")
@bot.command(name="otorol", help="<@rol|kapat>")
@commands.has_permissions(administrator=True)
async def otorol(ctx, *, arg):
    ensure_server(ctx.guild.id)
    if arg.lower() in ("kapat","off","0"):
        db.q("UPDATE servers SET auto_role=NULL WHERE guild_id=?", (ctx.guild.id,)); return await rp(ctx, OK("OTOROL KAPATILDI", "Yeni gelen üyelere artık otomatik rol verilmeyecek."))
    role = await commands.RoleConverter().convert(ctx, arg)
    db.q("UPDATE servers SET auto_role=? WHERE guild_id=?", (role.id, ctx.guild.id)); await rp(ctx, OK("OTOROL AYARLANDI", "Sunucuya giren her yeni üye otomatik olarak " + role.mention + " rolünü alacak."))
@kategori("mod")
@bot.command(name="hoşgeldin", aliases=["hosgeldin"], help="<#kanal|kapat> — hoş geldin kanalını ayarla")
@commands.has_permissions(administrator=True)
async def hoşgeldin(ctx, ch: discord.TextChannel = None):
    ensure_server(ctx.guild.id)
    if ch is None:
        db.q("UPDATE servers SET welcome_ch=NULL WHERE guild_id=?", (ctx.guild.id,)); return await rp(ctx, OK("HOŞ GELDİN KAPATILDI", "Yeni üyeler için karşılama mesajı artık gönderilmeyecek."))
    db.q("UPDATE servers SET welcome_ch=? WHERE guild_id=?", (ch.id, ctx.guild.id))
    await rp(ctx, OK("HOŞ GELDİN AYARLANDI", "Karşılama mesajları artık " + ch.mention + " kanalına Components V2 kartı olarak gönderilecek.\nŞablon: `k!hoşgeldinmesaj`"))

@kategori("mod")
@bot.command(name="ayrilma", aliases=["ayrılma","goodbye"], help="<#kanal|kapat> — ayrılma kanalını ayarla")
@commands.has_permissions(administrator=True)
async def ayrilma(ctx, ch: discord.TextChannel = None):
    ensure_server(ctx.guild.id)
    if ch is None:
        db.q("UPDATE servers SET leave_ch=NULL WHERE guild_id=?", (ctx.guild.id,)); return await rp(ctx, OK("AYRILMA KAPATILDI", "Ayrılan üyeler için mesaj gönderilmeyecek."))
    db.q("UPDATE servers SET leave_ch=? WHERE guild_id=?", (ch.id, ctx.guild.id))
    await rp(ctx, OK("AYRILMA AYARLANDI", "Ayrılma mesajları artık " + ch.mention + " kanalına Components V2 kartı olarak gönderilecek.\nŞablon: `k!ayrilmamesaj`"))

@kategori("mod")
@bot.command(name="hoşgeldinmesaj", aliases=["hosgeldinmesaj"], help="[mesaj|sıfırla] — karşılama şablonunu ayarla")
@commands.has_permissions(administrator=True)
async def hoşgeldinmesaj(ctx, *, mesaj: str = None):
    ensure_server(ctx.guild.id)
    if not mesaj or mesaj.lower() in ("sıfırla","sifirla","reset"):
        db.q("UPDATE servers SET welcome_message=NULL WHERE guild_id=?", (ctx.guild.id,))
        return await rp(ctx, OK("HOŞ GELDİN ŞABLONU SIFIRLANDI", "Varsayılan Components V2 karşılama kartı kullanılacak.\nDeğişkenler: `{mention}` `{user}` `{name}` `{server}` `{count}` `{id}` `{account_age}` `{created}` `{joined}`"))
    if len(mesaj) > 3500: return await rp(ctx, ER("MESAJ ÇOK UZUN", "Karşılama şablonu en fazla **3500** karakter olabilir."))
    db.q("UPDATE servers SET welcome_message=? WHERE guild_id=?", (mesaj, ctx.guild.id))
    await rp(ctx, OK("HOŞ GELDİN ŞABLONU AYARLANDI", "Yeni üyelerde bu Components V2 mesajı kullanılacak.\nDeğişkenler: `{mention}` `{user}` `{name}` `{server}` `{count}` `{id}` `{account_age}` `{created}` `{joined}`"))

@kategori("mod")
@bot.command(name="ayrilmamesaj", aliases=["ayrılmamesaj"], help="[mesaj|sıfırla] — ayrılma şablonunu ayarla")
@commands.has_permissions(administrator=True)
async def ayrilmamesaj(ctx, *, mesaj: str = None):
    ensure_server(ctx.guild.id)
    if not mesaj or mesaj.lower() in ("sıfırla","sifirla","reset"):
        db.q("UPDATE servers SET leave_message=NULL WHERE guild_id=?", (ctx.guild.id,))
        return await rp(ctx, OK("AYRILMA ŞABLONU SIFIRLANDI", "Varsayılan Components V2 ayrılma kartı kullanılacak.\nDeğişkenler: `{mention}` `{user}` `{name}` `{server}` `{count}` `{id}` `{account_age}` `{joined_for}` `{created}` `{joined}`"))
    if len(mesaj) > 3500: return await rp(ctx, ER("MESAJ ÇOK UZUN", "Ayrılma şablonu en fazla **3500** karakter olabilir."))
    db.q("UPDATE servers SET leave_message=? WHERE guild_id=?", (mesaj, ctx.guild.id))
    await rp(ctx, OK("AYRILMA ŞABLONU AYARLANDI", "Yeni ayrılışlarda bu Components V2 mesajı kullanılacak.\nDeğişkenler: `{mention}` `{user}` `{name}` `{server}` `{count}` `{id}` `{account_age}` `{joined_for}` `{created}` `{joined}`"))

@kategori("mod")
@bot.command(name="hoşgeldinbilgi", aliases=["hosgeldinbilgi"], help="Karşılama ayarlarını gösterir")
@commands.has_permissions(administrator=True)
async def hoşgeldinbilgi(ctx):
    s = db.one("SELECT * FROM servers WHERE guild_id=?", (ctx.guild.id,)) or {}
    await rp(ctx, head("wave", "HOŞ GELDİN AYARLARI") + "\n\n" + KV([
        (e("dot")+"Kanal", "<#"+str(s.get("welcome_ch"))+">" if s.get("welcome_ch") else "Kapalı"),
        (e("dot")+"Şablon", "Özel" if s.get("welcome_message") else "Varsayılan"),
        (e("dot")+"V2", "Components V2")
    ]) + tip("Kanal: `k!hoşgeldin #kanal` • Mesaj: `k!hoşgeldinmesaj <mesaj>` • Test: `k!hoşgeldintest`"))

@kategori("mod")
@bot.command(name="ayrilmabilgi", aliases=["ayrılmabilgi"], help="Ayrılma ayarlarını gösterir")
@commands.has_permissions(administrator=True)
async def ayrilmabilgi(ctx):
    s = db.one("SELECT * FROM servers WHERE guild_id=?", (ctx.guild.id,)) or {}
    await rp(ctx, head("wave", "AYRILMA AYARLARI") + "\n\n" + KV([
        (e("dot")+"Kanal", "<#"+str(s.get("leave_ch"))+">" if s.get("leave_ch") else "Kapalı"),
        (e("dot")+"Şablon", "Özel" if s.get("leave_message") else "Varsayılan"),
        (e("dot")+"V2", "Components V2")
    ]) + tip("Kanal: `k!ayrilma #kanal` • Mesaj: `k!ayrilmamesaj <mesaj>` • Test: `k!ayrilmatest`"))

@kategori("mod")
@bot.command(name="hoşgeldintest", aliases=["hosgeldintest"], help="Hoş geldin mesajını test eder")
@commands.has_permissions(administrator=True)
async def hoşgeldintest(ctx):
    s = db.one("SELECT * FROM servers WHERE guild_id=?", (ctx.guild.id,)) or {}
    text = _format_greeting(s.get("welcome_message"), ctx.author, "welcome")
    if HAS_V2: return await ctx.send(view=_greeting_view(text, ctx.author, 0x57F287))
    await rp(ctx, text)

@kategori("mod")
@bot.command(name="ayrilmatest", aliases=["ayrılmatest"], help="Ayrılma mesajını test eder")
@commands.has_permissions(administrator=True)
async def ayrilmatest(ctx):
    s = db.one("SELECT * FROM servers WHERE guild_id=?", (ctx.guild.id,)) or {}
    text = _format_greeting(s.get("leave_message"), ctx.author, "leave")
    if HAS_V2: return await ctx.send(view=_greeting_view(text, ctx.author, 0xED4245))
    await rp(ctx, text)

@kategori("mod")
@bot.command(name="butonrol", aliases=["rolmenü","rolpanel","selectrol"], help="<@rol...> [| başlık] — Select menü ile rol sistemi")
@commands.has_permissions(administrator=True)
@commands.bot_has_permissions(manage_roles=True)
async def butonrol(ctx, *, raw):
    parts = [x.strip() for x in raw.split("|", 1)]
    role_text = parts[0]
    title = parts[1].strip() if len(parts) > 1 else "Rolünü seç!"
    converter = commands.RoleConverter()
    roles = []
    for token in role_text.split():
        try:
            role = await converter.convert(ctx, token)
        except commands.BadArgument:
            continue
        if role.id not in [r.id for r in roles]: roles.append(role)
    if not roles or len(roles) > 25:
        return await rp(ctx, ER("GEÇERSİZ ROL SAYISI", "**1-25** arası geçerli rol eklemelisin. Örnek: `k!butonrol @Oyuncu @Renkli | Sunucunun rollerini seç!`"))
    me = ctx.guild.me
    bad = [r for r in roles if r.is_default() or r.managed or r >= me.top_role]
    if bad:
        return await rp(ctx, ER("ROL HİYERARŞİSİ", "Botun veremeyeceği roller var: " + ", ".join(r.name for r in bad[:10]) + ". Bot rolünü bu rollerin üstüne taşı."))
    mid = str(random.randint(10**11, 10**12 - 1))
    t = head("shield", "SELECT ROL MENÜSÜ") + "\n\n" + title[:500] + "\n\n" + e("dot") + " Aşağıdaki Select menüden bir rol seç; tekrar seçersen rol kaldırılır."
    v = RoleMenuPanel(mid, [(r.id, r.name) for r in roles], t)
    msg = await rp(ctx, t, v)
    if not msg: return
    db.q("INSERT OR REPLACE INTO role_menus(menu_id,guild_id,channel_id,message_id,title,role_ids) VALUES(?,?,?,?,?,?)", (mid, ctx.guild.id, ctx.channel.id, msg.id, title[:500], json.dumps([r.id for r in roles])))
    bot.add_view(v)
    await rp(ctx, OK("BUTONROL OLUŞTURULDU", "Menü ID: `" + mid + "`\nRoller: **" + str(len(roles)) + "**\nSilmek için: `k!butonrolsil " + mid + "`"))

@kategori("mod")
@bot.command(name="butonrollist", aliases=["rolmenüler"], help="Sunucudaki butonrol menülerini listeler")
@commands.has_permissions(administrator=True)
async def butonrollist(ctx):
    rows = db.all("SELECT * FROM role_menus WHERE guild_id=?", (ctx.guild.id,))
    if not rows: return await rp(ctx, WN("BUTONROL YOK", "Bu sunucuda kayıtlı butonrol menüsü bulunmuyor."))
    out=[]
    for r in rows:
        out.append(e("arrow") + " `" + str(r["menu_id"]) + "` • **" + (r["title"] or "Rol menüsü")[:60] + "** • " + str(len(json.loads(r["role_ids"] or "[]"))) + " rol")
    await rp(ctx, head("shield", "BUTONROL MENÜLERİ") + "\n\n" + "\n".join(out) + "\n\n`k!butonrolsil <id>` ile kaldırabilirsin.")

@kategori("mod")
@bot.command(name="butonrolsil", aliases=["rolmenüsil"], help="<menü-id>")
@commands.has_permissions(administrator=True)
async def butonrolsil(ctx, mid: str):
    row = db.one("SELECT * FROM role_menus WHERE menu_id=? AND guild_id=?", (mid, ctx.guild.id))
    if not row: return await rp(ctx, ER("MENÜ BULUNAMADI", "Bu sunucuda böyle bir butonrol menüsü yok."))
    db.q("DELETE FROM role_menus WHERE menu_id=? AND guild_id=?", (mid, ctx.guild.id))
    ch = ctx.guild.get_channel(row["channel_id"]) if row["channel_id"] else None
    if ch and row["message_id"]:
        try:
            msg = await ch.fetch_message(row["message_id"])
            await msg.edit(view=None)
        except Exception: pass
    await rp(ctx, OK("BUTONROL SİLİNDİ", "`" + mid + "` menüsü kaldırıldı ve kayıt silindi."))

@kategori("mod")
@bot.command(name="tepkırol", aliases=["tepkı-rol","reactionrol"], help="<mesaj-id> <emoji> @rol")
@commands.has_permissions(administrator=True)
@commands.bot_has_permissions(manage_roles=True, add_reactions=True, read_message_history=True)
async def tepkırol(ctx, message_id: int, emoji: str, role: discord.Role):
    me=ctx.guild.me
    if role.is_default() or role.managed or role >= me.top_role: return await rp(ctx,ER("ROL HİYERARŞİSİ","Botun veremeyeceği bir rol seçtin."))
    try:
        ch=ctx.channel; msg=await ch.fetch_message(message_id); await msg.add_reaction(emoji)
    except Exception as ex: return await rp(ctx,ER("REACTION AYARLANAMADI","Mesaj bulunamadı veya emoji eklenemedi.\n`"+str(ex)[:180]+"`"))
    db.q("INSERT OR REPLACE INTO reaction_roles(message_id,guild_id,channel_id,emoji,role_id) VALUES(?,?,?,?,?)",(message_id,ctx.guild.id,ch.id,emoji,str(role.id)))
    await guild_log_send(ctx.guild,head("shield","REACTION ROL AYARLANDI")+"\n\nMesaj: `"+str(message_id)+"`\nEmoji: "+emoji+"\nRol: "+role.mention+"\nYetkili: "+ctx.author.mention,"role")
    await rp(ctx,OK("REACTION ROL AYARLANDI",emoji+" tepkisine basanlara "+role.mention+" verilecek. Tekrar basınca rol kaldırılır."))

@kategori("mod")
@bot.command(name="tepkırollist", aliases=["reactionrollist"], help="Reaction rol listesini gösterir")
@commands.has_permissions(administrator=True)
async def tepkırollist(ctx):
    rows=db.all("SELECT * FROM reaction_roles WHERE guild_id=? ORDER BY message_id",(ctx.guild.id,))
    if not rows: return await rp(ctx,WN("REACTION ROL YOK","Bu sunucuda reaction rol ayarı bulunmuyor."))
    await rp(ctx,head("shield","REACTION ROLLER")+"\n\n"+"\n".join(e("arrow")+" Mesaj `"+str(r["message_id"])+"` • "+r["emoji"]+" → <@&"+str(r["role_id"])+">" for r in rows[:30]))

@kategori("mod")
@bot.command(name="tepkırolsil", aliases=["reactionrolsil"], help="<mesaj-id> <emoji>")
@commands.has_permissions(administrator=True)
async def tepkırolsil(ctx, message_id: int, emoji: str):
    db.q("DELETE FROM reaction_roles WHERE guild_id=? AND message_id=? AND emoji=?",(ctx.guild.id,message_id,emoji)); await rp(ctx,OK("REACTION ROL SİLİNDİ","Bu emoji-rol bağlantısı kaldırıldı."))

@kategori("mod")
@bot.command(name="koruma", help="<mod> <aç/kapat>")
@commands.has_permissions(administrator=True)
async def koruma(ctx, md: str, d: str):
    md = md.lower().replace("-","").replace("_","")
    col = {"antispam":"anti_spam","antiflood":"anti_flood","antiraid":"anti_raid","antilink":"anti_link","badword":"badword","küfür":"badword"}.get(md)
    if not col: return await rp(ctx, ER("GEÇERSİZ MODÜL", "Geçerli koruma modülleri:\n`antispam` `antiflood` `antiraid` `antilink` `badword`\nÖrnek: `k!koruma antilink aç`"))
    db.q("INSERT OR IGNORE INTO protections(guild_id) VALUES(?)", (ctx.guild.id,))
    v = 1 if d.lower() in ("aç","ac","on","1") else 0
    db.q("UPDATE protections SET " + col + "=? WHERE guild_id=?", (v, ctx.guild.id))
    await rp(ctx, OK("KORUMA " + ("AÇILDI" if v else "KAPATILDI") + ": " + md.upper(), ("Bu modül artık ihlalleri otomatik engelliyor." if v else "Bu modül devre dışı bırakıldı.") + tip("Olayları görmek için `k!korumalog #kanal` ayarla.")))
@kategori("mod")
@bot.command(name="korumadurum", help="Durum")
async def korumadurum(ctx):
    p = db.one("SELECT * FROM protections WHERE guild_id=?", (ctx.guild.id,)) or {}
    f = lambda v: e("check") if v else e("cross")
    await rp(ctx, head("shield", "KORUMA DURUMU") + "\n\nHangi korumalar aktif?\n" + KV([(f(p.get("anti_spam"))+" Spam koruması", "Açık" if p.get("anti_spam") else "Kapalı"), (f(p.get("anti_flood"))+" Flood koruması", "Açık" if p.get("anti_flood") else "Kapalı"), (f(p.get("anti_raid"))+" Raid koruması", "Açık" if p.get("anti_raid") else "Kapalı"), (f(p.get("anti_link"))+" Link engeli", "Açık" if p.get("anti_link") else "Kapalı"), (f(p.get("badword"))+" Küfür filtresi", "Açık" if p.get("badword") else "Kapalı")]) + tip("Değiştirmek için `k!koruma <modül> <aç/kapat>`"))
@kategori("mod")
@bot.command(name="korumalog", help="<#kanal>")
@commands.has_permissions(administrator=True)
async def korumalog(ctx, ch: discord.TextChannel):
    db.q("INSERT OR IGNORE INTO protections(guild_id) VALUES(?)", (ctx.guild.id,)); db.q("UPDATE protections SET log_ch=? WHERE guild_id=?", (ch.id, ctx.guild.id)); await rp(ctx, OK("KORUMA LOGU AYARLANDI", "Spam, link ve küfür gibi koruma olayları " + ch.mention + " kanalına yazılacak."))
@kategori("mod")
@bot.command(name="badword", help="<ekle/sil/liste> [kelime]")
@commands.has_permissions(administrator=True)
async def badword(ctx, i: str, *, k=None):
    g = ctx.guild.id
    if i.lower() in ("ekle","add"):
        if not k: return await rp(ctx, ER("KELİME YAZMADIN", "Eklenecek kelimeyi yazmalısın.\nÖrnek: `k!badword ekle aptal`"))
        db.q("INSERT OR IGNORE INTO badwords(guild_id,word) VALUES(?,?)", (g, k.lower())); await rp(ctx, OK("YASAKLI KELİME EKLENDİ", "`" + k.lower() + "` içeren mesajlar artık silinecek." + tip("Filtrenin çalışması için `k!koruma badword aç` olmalı.")))
    elif i.lower() in ("sil","remove"):
        db.q("DELETE FROM badwords WHERE guild_id=? AND word=?", (g, (k or "").lower())); await rp(ctx, OK("YASAKLI KELİME SİLİNDİ", "Kelime filtre listesinden çıkarıldı."))
    else:
        ws = [w["word"] for w in db.all("SELECT word FROM badwords WHERE guild_id=?", (g,))]
        await rp(ctx, head("warn", "YASAKLI KELİMELER") + "\n\n" + ("Toplam **" + str(len(ws)) + "** kelime:\n`" + "`, `".join(ws) + "`" if ws else "Liste boş." + tip("Eklemek için `k!badword ekle <kelime>`")))
@kategori("mod")
@bot.command(name="raidmodu", help="<aç/kapat>")
@commands.has_permissions(administrator=True)
async def raidmodu(ctx, m: str):
    db.q("INSERT OR IGNORE INTO protections(guild_id) VALUES(?)", (ctx.guild.id,))
    if m.lower() in ("aç","ac","on"):
        db.q("UPDATE protections SET raid_until=? WHERE guild_id=?", (datetime.datetime.now().timestamp() + 600, ctx.guild.id)); await rp(ctx, WN("RAID MODU AÇILDI", "**10 dakika** boyunca sunucuya giren yeni üyeler otomatik atılacak." + tip("Erken kapatmak için `k!raidmodu kapat`")))
    else:
        db.q("UPDATE protections SET raid_until=0 WHERE guild_id=?", (ctx.guild.id,)); await rp(ctx, OK("RAID MODU KAPANDI", "Yeni üye girişleri tekrar serbest."))
@kategori("mod")
@bot.command(name="kurulum", aliases=["sunucukur","setup"], help="Sunucu kur")
@commands.has_permissions(administrator=True)
@commands.bot_has_permissions(manage_channels=True, manage_roles=True)
async def kurulum(ctx):
    t = head("gear", "SUNUCU KURULUMU") + "\n\nOtomatik olarak şunlar oluşturulacak:\n" + e("arrow") + " **4 kategori** ve **12 kanal**\n" + e("arrow") + " **4 rol** (Yönetici, Moderatör, Üye, Bot)\n\nOnaylıyor musun?"; v = ConfirmPanel(t, 60); await rp(ctx, t, v); await v.wait()
    if not v.value: return await rp(ctx, WN("KURULUM İPTAL", "Sunucuda hiçbir değişiklik yapılmadı."))
    g = ctx.guild; ck = 0
    try:
        ry = await g.create_role(name="Yönetici", color=discord.Color(0xE74C3C), permissions=discord.Permissions(administrator=True))
        rm = await g.create_role(name="Moderatör", color=discord.Color(0x3498DB), permissions=discord.Permissions(kick_members=True, manage_messages=True, moderate_members=True))
        await g.create_role(name="Üye", color=discord.Color(0x2ECC71)); rb = await g.create_role(name="Bot", color=discord.Color(0xFFD700), hoist=True)
        try: await g.me.add_roles(rb)
        except Exception: pass
        k1 = await g.create_category("BİLGİ"); k2 = await g.create_category("SOHBET"); k3 = await g.create_category("SES"); k4 = await g.create_category("YÖNETİM")
        ow = {g.default_role: discord.PermissionOverwrite(view_channel=True, send_messages=False)}
        for n in ("duyurular","kurallar","etkinlik"): await g.create_text_channel(n, category=k1, overwrites=ow); ck += 1
        hg = await g.create_text_channel("hoşgeldin", category=k1, overwrites=ow); ck += 1
        for n in ("genel","sohbet","medya","bot-komut"): await g.create_text_channel(n, category=k2); ck += 1
        for n in ("Sohbet 1","Sohbet 2","Müzik"): await g.create_voice_channel(n, category=k3); ck += 1
        owy = {g.default_role: discord.PermissionOverwrite(view_channel=False), ry: discord.PermissionOverwrite(view_channel=True), rm: discord.PermissionOverwrite(view_channel=True)}
        await g.create_text_channel("yetkili-sohbet", category=k4, overwrites=owy); ck += 1
        ensure_server(g.id); db.q("UPDATE servers SET welcome_ch=? WHERE guild_id=?", (hg.id, g.id))
        await rp(ctx, OK("KURULUM TAMAMLANDI", "**" + str(ck) + "** kanal ve **4** rol hazır. 🎉\nHoş geldin kanalı: " + hg.mention))
    except discord.Forbidden: await rp(ctx, ER("YETKİM YETMEDİ", "Kanal veya rol oluşturma yetkim eksik.\nKatre rolüne **Yönetici** ver ve tekrar dene."))
    except Exception as ex: await rp(ctx, ER("KURULUM HATASI", str(ex)[:250]))

@kategori("sys")
@bot.command(name="kelimekur", help="<#kategori> — Kelime türetme oyunu kurar")
@commands.has_permissions(administrator=True)
@commands.bot_has_permissions(manage_channels=True)
async def kelimekur(ctx, cat: discord.CategoryChannel):
    ch = discord.utils.get(ctx.guild.text_channels, name="kelime-oyunu")
    if not ch:
        try: ch = await ctx.guild.create_text_channel("kelime-oyunu", category=cat)
        except Exception: return await rp(ctx, ER("KANAL OLUŞTURULAMADI", "Seçtiğin kategoride kanal açma yetkim yok."))
    db.q("INSERT OR REPLACE INTO wordgame(guild_id,channel_id,last_word,last_user,streak) VALUES(?,?,?,?,0)", (ctx.guild.id, ch.id, None, None))
    await rp_ch(ch, head("game", "KELİME TÜRETME OYUNU") + "\n\nÖnceki kelimenin **son harfiyle** başlayan yeni bir kelime yaz!\n\n" + e("check") + " Doğru kelime = tik + **15 coin**\n" + e("fire") + " Her 5. seri = **+50 bonus coin**\n📖 Kelimeler **TDK sözlüğünden** kontrol edilir; özel isim geçmez\n⏱️ Kelimeler arası **" + str(WG_COOLDOWN) + " sn** bekleme var\n📩 Hatalı mesaj silinir, nedeni **DM'den** bildirilir\n\n" + e("arrow") + " Örnek: dünya → arı → ırmak" + tip("ğ ile biten kelimeden sonra bir önceki harf esas alınır."))
    await rp(ctx, OK("KELİME OYUNU KURULDU", ch.mention + " kanalında oyun başladı!\nKapatmak için `k!kelimekapat`, durumu görmek için `k!kelimedurum` yaz."))
@kategori("sys")
@bot.command(name="kelimekapat", help="Kelime oyununu kapatır")
@commands.has_permissions(administrator=True)
async def kelimekapat(ctx):
    db.q("DELETE FROM wordgame WHERE guild_id=?", (ctx.guild.id,))
    await rp(ctx, OK("KELİME OYUNU KAPATILDI", "Oyun devre dışı bırakıldı; kanalı isterseniz elle silebilirsiniz."))
@kategori("sys")
@bot.command(name="kelimedurum", help="Oyun durumu")
async def kelimedurum(ctx):
    wg = db.one("SELECT * FROM wordgame WHERE guild_id=?", (ctx.guild.id,))
    if not wg: return await rp(ctx, WN("OYUN KURULU DEĞİL", "Bu sunucuda kelime oyunu yok." + tip("Kurmak için `k!kelimekur #kategori` yaz.")))
    need = wg_need(wg["last_word"]).upper() if wg["last_word"] else None
    await rp(ctx, head("game", "KELİME OYUNU DURUMU") + "\n\n" + KV([(e("dot")+"Kanal", "<#" + str(wg["channel_id"]) + ">"), (e("dot")+"Son kelime", wg["last_word"] or "—"), (e("dot")+"Sıradaki harf", need or "serbest"), (e("dot")+"Seri", wg["streak"] or 0)]))
@kategori("sys")
@bot.command(name="tempvoice", help="[kur|#kanal|kapat]")
@commands.has_permissions(administrator=True)
@commands.bot_has_permissions(manage_channels=True, move_members=True)
async def tempvoice(ctx, *, arg=None):
    if arg and arg.lower() in ("kapat","off","0"):
        db.q("DELETE FROM tempvoice WHERE guild_id=?", (ctx.guild.id,)); return await rp(ctx, OK("TEMP VOICE KAPANDI", "Özel oda sistemi durduruldu; mevcut odalar boşalınca silinir."))
    if arg:
        ch = await commands.VoiceChannelConverter().convert(ctx, arg)
        db.q("INSERT OR REPLACE INTO tempvoice(guild_id,trigger_ch,category_id) VALUES(?,?,?)", (ctx.guild.id, ch.id, ch.category.id if ch.category else None))
        await rp(ctx, OK("TEMP VOICE AYARLANDI", ch.mention + " kanalına giren üye kendine özel bir oda alır."))
    else:
        cat = await ctx.guild.create_category("ÖZEL ODALAR"); trig = await cat.create_voice_channel("➕ Katıl & Oda Kur")
        await trig.set_permissions(ctx.guild.default_role, view_channel=True, connect=True, speak=False)
        db.q("INSERT OR REPLACE INTO tempvoice(guild_id,trigger_ch,category_id) VALUES(?,?,?)", (ctx.guild.id, trig.id, cat.id))
        await rp(ctx, OK("TEMP VOICE KURULDU", trig.mention + " kanalına giren herkes kendi odasını alır.\nOda boşalınca otomatik silinir."))
@kategori("sys")
@bot.command(name="ticket", help="<kapat/bilgi/listele/ekle/çıkar>")
async def ticket(ctx, i: str = "bilgi", u: discord.Member = None):
    i = i.lower(); t = db.one("SELECT * FROM tickets WHERE channel_id=?", (ctx.channel.id,))
    if i in ("kapat", "close"):
        if not t: return await rp(ctx, ER("BURASI BİR TİCKET DEĞİL", "Bu komut sadece destek talebi kanalında çalışır."))
        if not (_ticket_is_admin(ctx.author) or _ticket_can_manage(t, ctx.author) or ctx.author.id == t["user_id"]): return await rp(ctx, ER("YETKİN YOK", "Talebi sadece ticket sahibi, üstlenen yetkili veya Administrator kapatabilir."))
        await rp(ctx, WN("TALEP KAPATILIYOR", "Transkript hazırlanıyor, bu kanal **10 saniye** içinde silinecek.")); await ticket_finish(ctx.guild, ctx.channel, t, ctx.author); await asyncio.sleep(10)
        try: await ctx.channel.delete(reason="Talep kapatıldı")
        except Exception: pass
    elif i in ("bilgi", "info"):
        if not t: return await rp(ctx, ER("BURASI BİR TİCKET DEĞİL", "Bu kanal bir destek talebi kanalı değil."))
        await rp(ctx, ticket_text(t))
    elif i in ("listele", "list"):
        if not (_ticket_is_admin(ctx.author) or _ticket_is_staff(type("X", (), {"user":ctx.author,"guild":ctx.guild})())): return await rp(ctx, ER("YETKİN YOK", "Talepleri sadece ticket yetkilileri listeleyebilir."))
        rs = db.all("SELECT * FROM tickets WHERE guild_id=? AND status='open' ORDER BY number", (ctx.guild.id,))
        if not rs: return await rp(ctx, OK("AÇIK TICKET YOK", "Şu an açık destek talebi yok."))
        await rp(ctx, head("ticket", "AÇIK TICKETLAR") + "\n\n" + "\n".join(e("arrow") + " <#" + str(r["channel_id"]) + "> ─ " + _tcat(r.get("category"))[0] + " " + _priority_text(r.get("priority")) + " <@" + str(r["user_id"]) + "> ─ " + ("🟡 <@" + str(r["claimed_by"]) + ">" if r.get("claimed_by") else "🟢 bekliyor") for r in rs[:20]))
    elif i in ("ekle", "add", "çıkar", "cikar", "remove"):
        if not t: return await rp(ctx, ER("BURASI BİR TİCKET DEĞİL", "Bu komut sadece destek talebi kanalında çalışır."))
        if not (_ticket_is_admin(ctx.author) or _ticket_can_manage(t, ctx.author)): return await rp(ctx, ER("YETKİN YOK", "`ekle/çıkar` işlemlerini yalnızca ticketı üstlenen yetkili veya Administrator yapabilir."))
        if not u: return await rp(ctx, ER("ÜYE YAZMADIN", "Kullanım: `k!ticket ekle @üye` veya `k!ticket çıkar @üye`"))
        add = i in ("ekle", "add")
        if not add and u.id == t["user_id"]: return await rp(ctx, WN("TALEP SAHİBİ ÇIKARILAMAZ", "Talebi açan kişiyi kanaldan çıkaramazsın."))
        try: await ctx.channel.set_permissions(u, overwrite=discord.PermissionOverwrite(view_channel=True, send_messages=True, attach_files=True, read_message_history=True) if add else None)
        except Exception as ex: return await rp(ctx, ER("İŞLEM BAŞARISIZ", "İzinler değiştirilemedi.\n`" + str(ex)[:120] + "`"))
        await rp(ctx, OK("ÜYE EKLENDİ" if add else "ÜYE ÇIKARILDI", u.mention + (" artık bu ticketı görebilir ve yazabilir." if add else " bu ticketa erişimini kaybetti.")))
    else: await rp(ctx, ER("GEÇERSİZ İŞLEM", "Kullanım: `k!ticket kapat` • `bilgi` • `listele` • `ekle @üye` • `çıkar @üye`"))
@kategori("sys")
@bot.command(name="başvuru-ayarla", help="<#log> [@rol]")
@commands.has_permissions(administrator=True)
async def başvuru_ayarla(ctx, ch: discord.TextChannel, role: discord.Role = None):
    db.q("INSERT OR REPLACE INTO app_settings(guild_id,log_ch,staff_role) VALUES(?,?,?)", (ctx.guild.id, ch.id, role.id if role else None))
    await rp(ctx, OK("BAŞVURU SİSTEMİ AYARLANDI", "Başvurular " + ch.mention + " kanalına düşecek." + (("\nKabul edilenler " + role.mention + " rolünü alacak.") if role else "\nKabul edilenlere rol verilmeyecek.") + tip("Paneli kurmak için `k!başvuru-panel` yaz.")))
@kategori("sys")
@bot.command(name="başvuru-panel", help="Panel")
@commands.has_permissions(administrator=True)
async def başvuru_panel(ctx):
    t = head("clip", "YETKİLİ BAŞVURUSU") + "\n\nEkibimize katılmak mı istiyorsun? Aşağıdaki butona bas ve formu doldur; başvurun yetkililere iletilir ve sonucu sana bildirilir."; await rp(ctx, t, AppOpenPanel(t))
    try: await ctx.message.delete()
    except Exception: pass
@kategori("sys")
@bot.command(name="başvurular", help="Bekleyenler")
@commands.has_permissions(administrator=True)
async def başvurular(ctx):
    rs = db.all("SELECT * FROM applications WHERE guild_id=? AND status='pending'", (ctx.guild.id,))
    if not rs: return await rp(ctx, OK("BEKLEYEN BAŞVURU YOK", "Şu an değerlendirilmeyi bekleyen başvuru bulunmuyor."))
    await rp(ctx, head("clip", "BEKLEYEN BAŞVURULAR (" + str(len(rs)) + ")") + "\n\n" + "\n".join(e("arrow") + " **#" + str(r["id"]) + "** ─ <@" + str(r["user_id"]) + ">" for r in rs[:10]) + tip("Başvurular log kanalındaki butonlarla kabul/red edilir."))
@kategori("sys")
@bot.command(name="başvurum", help="Durumun")
async def başvurum(ctx):
    r = db.one("SELECT * FROM applications WHERE guild_id=? AND user_id=? ORDER BY id DESC", (ctx.guild.id, ctx.author.id))
    if not r: return await rp(ctx, WN("BAŞVURUN YOK", "Bu sunucuda henüz başvuru yapmamışsın." + tip("Başvuru panelindeki butonu kullanabilirsin.")))
    dm = {"pending": "⏳ Bekliyor", "accepted": "✅ Kabul edildi", "rejected": "❌ Reddedildi"}.get(r["status"], r["status"])
    await rp(ctx, head("clip", "BAŞVURU #" + str(r["id"])) + "\n\nSon başvurunun durumu: **" + dm + "**")
@kategori("sys")
@bot.command(name="otocevap", help="<ekle/sil/liste>")
@commands.has_permissions(administrator=True)
async def otocevap(ctx, i: str, *, a=None):
    g = ctx.guild.id
    if i.lower() in ("ekle","add"):
        if not a or "|" not in a: return await rp(ctx, ER("FORMAT HATALI", "Tetikleyici ile cevabı `|` ile ayırmalısın.\nÖrnek: `k!otocevap ekle selam | Merhaba!`"))
        t, r = [p.strip() for p in a.split("|", 1)]
        db.q("INSERT OR REPLACE INTO auto_replies(guild_id,trigger,response) VALUES(?,?,?)", (g, t.lower(), r[:500])); await rp(ctx, OK("OTO CEVAP EKLENDİ", "Mesajda `" + t.lower() + "` geçerse bot otomatik cevap verecek."))
    elif i.lower() in ("sil","remove"):
        db.q("DELETE FROM auto_replies WHERE guild_id=? AND trigger=?", (g, (a or "").lower())); await rp(ctx, OK("OTO CEVAP SİLİNDİ", "Bu tetikleyici artık cevap vermeyecek."))
    else:
        rs = db.all("SELECT * FROM auto_replies WHERE guild_id=?", (g,))
        await rp(ctx, head("robot", "OTO CEVAPLAR") + "\n\n" + (("Toplam **" + str(len(rs)) + "** tetikleyici:\n" + "\n".join(e("arrow") + " `" + r["trigger"] + "`" for r in rs[:15])) if rs else "Henüz oto cevap yok." + tip("Eklemek için `k!otocevap ekle tetik | cevap`")))
@kategori("sys")
@bot.command(name="sayaç", help="<hedef> <#kanal|kapat>")
@commands.has_permissions(administrator=True)
async def sayaç(ctx, h: int, ch: discord.TextChannel = None):
    if ch is None or h <= 0:
        db.q("DELETE FROM counters WHERE guild_id=?", (ctx.guild.id,)); return await rp(ctx, OK("SAYAÇ KAPATILDI", "Üye hedefi sayacı durduruldu."))
    db.q("INSERT OR REPLACE INTO counters(guild_id,target,channel_id,reached) VALUES(?,?,?,0)", (ctx.guild.id, h, ch.id)); await rp(ctx, OK("ÜYE SAYACI AYARLANDI", "Hedef: **" + str(h) + "** üye.\nHer yeni girişte " + ch.mention + " kanalında ilerleme gösterilecek."))
@kategori("sys")
@bot.command(name="seviyerol", help="<ekle/sil/liste> [lv] [@rol]")
@commands.has_permissions(administrator=True)
async def seviyerol(ctx, i: str, s: int = 0, role: discord.Role = None):
    g = ctx.guild.id
    if i.lower() in ("ekle","add"):
        if not role: return await rp(ctx, ER("ROL BELİRTMEDİN", "Seviye ve rolü birlikte yazmalısın.\nÖrnek: `k!seviyerol ekle 5 @Rol`"))
        db.q("INSERT INTO level_roles(guild_id,level,role_id) VALUES(?,?,?)", (g, s, role.id)); await rp(ctx, OK("SEVİYE ÖDÜLÜ EKLENDİ", "Seviye **" + str(s) + "** olan üyeler otomatik " + role.mention + " rolünü alacak."))
    elif i.lower() in ("sil","remove"):
        db.q("DELETE FROM level_roles WHERE guild_id=? AND level=?", (g, s)); await rp(ctx, OK("SEVİYE ÖDÜLÜ SİLİNDİ", "Seviye **" + str(s) + "** rol ödülü kaldırıldı."))
    else:
        rs = db.all("SELECT * FROM level_roles WHERE guild_id=? ORDER BY level", (g,))
        await rp(ctx, head("chartup", "SEVİYE ROL ÖDÜLLERİ") + "\n\n" + (("\n".join(e("arrow") + " Seviye **" + str(r["level"]) + "** → <@&" + str(r["role_id"]) + ">" for r in rs)) if rs else "Henüz seviye ödülü yok." + tip("Eklemek için `k!seviyerol ekle 5 @Rol`")))
LOG_EVENT_KEYS = {"sunucu":"server","uye":"member","üye":"member","mesaj":"message","moderasyon":"moderation","rol":"role","kanal":"channel","ses":"voice","ticket":"ticket","davet":"invite","webhook":"webhook","thread":"thread","emoji":"emoji","sticker":"sticker","komut":"command","bot":"bot","hepsi":"all"}
@kategori("sys")
@bot.command(name="logayarla", help="<tür> <#kanal|kapat>")
@commands.has_permissions(administrator=True)
async def logayarla(ctx, tur: str, *, hedef: str = None):
    key=LOG_EVENT_KEYS.get(tur.lower().replace("ı","i"), LOG_EVENT_KEYS.get(tur.lower()))
    if not key: return await rp(ctx,ER("GEÇERSİZ LOG TÜRÜ","Türler: `sunucu`, `uye`, `mesaj`, `moderasyon`, `rol`, `kanal`, `ses`, `ticket`, `davet`, `webhook`, `thread`, `emoji`, `sticker`, `komut`, `bot`, `hepsi`"))
    hedef=(hedef or "").strip()
    if hedef.lower() in ("kapat","off","kapa","0"):
        ch=None
    else:
        try: ch=await commands.TextChannelConverter().convert(ctx,hedef)
        except commands.ChannelNotFound: return await rp(ctx,ER("KANAL BULUNAMADI","Geçerli bir metin kanalı belirt veya `kapat` yaz."))
    if key == "all":
        if ch is None:
            db.q("DELETE FROM log_channels WHERE guild_id=?",(ctx.guild.id,)); return await rp(ctx,OK("TÜM AYRI LOG KANALLARI KAPATILDI","Detaylı log yönlendirmeleri sıfırlandı."))
        for ev in ("server","member","message","moderation","role","channel","voice","ticket","invite","webhook","thread","emoji","sticker","command","bot"):
            db.q("INSERT OR REPLACE INTO log_channels(guild_id,event,channel_id) VALUES(?,?,?)",(ctx.guild.id,ev,ch.id))
        return await rp(ctx,OK("TÜM LOGLAR AYARLANDI","Tüm log türleri "+ch.mention+" kanalına gönderilecek."))
    if ch is None:
        db.q("DELETE FROM log_channels WHERE guild_id=? AND event=?",(ctx.guild.id,key)); return await rp(ctx,OK(LOG_LABELS.get(key,"Log").upper()+" LOGU KAPATILDI","Bu tür için özel log kanalı kaldırıldı."))
    db.q("INSERT OR REPLACE INTO log_channels(guild_id,event,channel_id) VALUES(?,?,?)",(ctx.guild.id,key,ch.id)); await rp(ctx,OK(LOG_LABELS.get(key,"Log").upper()+" LOGU AYARLANDI",LOG_LABELS.get(key,"Log")+" olayları artık "+ch.mention+" kanalına gönderilecek."))
@kategori("sys")
@bot.command(name="loglar", aliases=["logdurum"], help="Ayarlı log kanallarını gösterir")
@commands.has_permissions(administrator=True)
async def loglar(ctx):
    rows=db.all("SELECT * FROM log_channels WHERE guild_id=? ORDER BY event",(ctx.guild.id,)); lines=[]
    for ev in ("server","member","message","moderation","role","channel","voice","ticket","invite","webhook","thread","emoji","sticker","command","bot"):
        r=next((x for x in rows if x["event"]==ev),None); lines.append((e("check") if r and r["channel_id"] else e("cross"))+" **"+LOG_LABELS[ev]+"** → "+("<#"+str(r["channel_id"])+">" if r and r["channel_id"] else "Ayarlanmadı"))
    await rp(ctx,head("log","LOG AYARLARI")+"\n\n"+"\n".join(lines)+tip("Ayarlamak için `k!logayarla <tür> #kanal` • Hepsi için `k!logayarla hepsi #kanal`"))

@kategori("sys")
@bot.command(name="logtest", aliases=["logtesti"], help="<tür> — seçilen log kanalını test eder")
@commands.has_permissions(administrator=True)
async def logtest(ctx, tur: str = "hepsi"):
    key = LOG_EVENT_KEYS.get(tur.lower(), tur.lower())
    if key == "all":
        ok = 0
        for ev in LOG_LABELS:
            if await guild_log_send(ctx.guild, head("log", "LOG TEST") + "\n\n" + e("check") + " **" + LOG_LABELS[ev] + "** log kanalı çalışıyor.\nTest eden: " + ctx.author.mention, ev): ok += 1
        return await rp(ctx, OK("LOG TESTİ TAMAMLANDI", "**" + str(ok) + "** log hedefi test edildi."))
    if key not in LOG_LABELS: return await rp(ctx, ER("GEÇERSİZ LOG TÜRÜ", "`k!loglar` ile ayarlı türleri görebilirsin."))
    if await guild_log_send(ctx.guild, head("log", "LOG TEST") + "\n\n" + e("check") + " **" + LOG_LABELS[key] + "** log kanalı çalışıyor.\nTest eden: " + ctx.author.mention, key):
        return await rp(ctx, OK("LOG ÇALIŞIYOR", LOG_LABELS[key] + " log kanalına test mesajı gönderildi."))
    await rp(ctx, ER("LOG AYARLI DEĞİL", LOG_LABELS[key] + " için bir kanal ayarlanmamış veya kanala mesaj gönderilemiyor."))

@kategori("sys")
@bot.command(name="logkapat", help="<tür> — bir log türünü kapatır")
@commands.has_permissions(administrator=True)
async def logkapat(ctx, tur: str):
    key = LOG_EVENT_KEYS.get(tur.lower(), tur.lower())
    if key not in LOG_LABELS: return await rp(ctx, ER("GEÇERSİZ LOG TÜRÜ", "`k!loglar` ile türleri görebilirsin."))
    db.q("DELETE FROM log_channels WHERE guild_id=? AND event=?", (ctx.guild.id, key))
    await rp(ctx, OK("LOG KAPATILDI", LOG_LABELS[key] + " log yönlendirmesi kapatıldı."))

@kategori("sys")
@bot.command(name="logtemizle", aliases=["logreset"], help="Tüm ayrıntılı log kanallarını sıfırlar")
@commands.has_permissions(administrator=True)
async def logtemizle(ctx):
    db.q("DELETE FROM log_channels WHERE guild_id=?", (ctx.guild.id,))
    await rp(ctx, OK("LOGLAR SIFIRLANDI", "Ayrıntılı log kanal eşleştirmelerinin tamamı kaldırıldı."))

@kategori("sys")
@bot.command(name="logdetay", aliases=["logolaylar"], help="Loglanan olayları gösterir")
@commands.has_permissions(administrator=True)
async def logdetay(ctx):
    await rp(ctx, head("log", "FULL LOG KAPSAMI") + "\n\n" +
             "\n".join(e("check") + " " + x for x in [
                 "Üye giriş/çıkış, nickname ve rol değişimleri", "Ban / unban / timeout / kick / uyarı / koruma olayları",
                 "Mesaj silme, düzenleme ve toplu silme", "Rol oluşturma/silme/değiştirme",
                 "Kanal oluşturma/silme/değiştirme", "Ses kanalına giriş/çıkış/değişim",
                 "Ticket açma/üstlenme/kapatma", "Davet oluşturma/silme", "Webhook güncellemeleri",
                 "Thread oluşturma/güncelleme/silme", "Emoji ve sticker değişimleri", "Komut kullanımları",
                 "Botun sunucuya katılması/ayrılması ve sunucu ayar değişimleri"
             ]) + tip("Normal sohbet mesajlarının tamamı varsayılan olarak loglanmaz; mesaj silme/düzenleme/toplu silme loglanır."))

@kategori("sys")
@bot.command(name="sunuculog", help="<#kanal|kapat>")
@commands.has_permissions(administrator=True)
async def sunuculog(ctx, ch: discord.TextChannel = None):
    if ch is None:
        db.q("DELETE FROM guild_logs WHERE guild_id=?", (ctx.guild.id,)); return await rp(ctx, OK("SUNUCU LOGU KAPANDI", "Sunucu olayları artık kaydedilmeyecek."))
    db.q("INSERT OR REPLACE INTO guild_logs(guild_id,channel_id) VALUES(?,?)", (ctx.guild.id, ch.id)); await rp(ctx, OK("SUNUCU LOGU AYARLANDI", "Mesaj silme/düzenleme, giriş-çıkış ve takma ad değişiklikleri " + ch.mention + " kanalına yazılacak."))

@kategori("eco")
@bot.command(name="cüzdan", aliases=["balance","para"], help="Cüzdan")
async def cüzdan(ctx, u: discord.Member = None):
    u = u or ctx.author; ensure_user(u.id, str(u)); d = db.one("SELECT * FROM users WHERE user_id=?", (u.id,))
    await rp(ctx, head("money", u.display_name + " • CÜZDAN") + "\n\n" + KV([(e("coin")+"Bakiye", str(d["coins"]) + " coin"), (e("dot")+"İtibar", d["rep"])]) + tip("Coinleri `k!market`'te harcayabilirsin."))
@kategori("eco")
@bot.command(name="zenginler", aliases=["coinlb"], help="Coin top")
async def zenginler(ctx):
    rs = db.all("SELECT * FROM users ORDER BY coins DESC LIMIT 10")
    if not rs: return await rp(ctx, WN("HENÜZ VERİ YOK", "Sıralama için henüz yeterli veri yok."))
    await rp(ctx, head("coin", "EN ZENGİNLER") + "\n\nEn çok coine sahip ilk 10 üye:\n" + "\n".join(medal(i) + " <@" + str(r["user_id"]) + "> ─ **" + str(r["coins"]) + "** coin" for i, r in enumerate(rs)))
@kategori("eco")
@bot.command(name="günlük", aliases=["gunluk","daily"], help="Günlük")
@commands.cooldown(1, 86400, commands.BucketType.user)
async def günlük(ctx):
    ensure_user(ctx.author.id, str(ctx.author)); u = db.one("SELECT * FROM users WHERE user_id=?", (ctx.author.id,))
    b = random.randint(150, 400) + (250 if u["pro"] else 0); db.q("UPDATE users SET coins=coins+? WHERE user_id=?", (b, ctx.author.id))
    await rp(ctx, OK("GÜNLÜK ÖDÜL ALINDI", "Hesabına **+" + str(b) + " coin** eklendi. 🎁" + ("\nPro bonusu dahil!" if u["pro"] else "") + tip("Yarın tekrar alabilirsin.")))
@kategori("eco")
@bot.command(name="çalış", aliases=["calis","work"], help="Çalış")
@commands.cooldown(1, 1800, commands.BucketType.user)
async def çalış(ctx):
    ensure_user(ctx.author.id, str(ctx.author))
    j, a, b = random.choice([("Yazılımcı",200,400),("Tasarımcı",150,300),("İçerik üreticisi",180,350),("Pizzacı",100,220),("Şoför",120,260)])
    p = random.randint(a, b); db.q("UPDATE users SET coins=coins+? WHERE user_id=?", (p, ctx.author.id))
    await rp(ctx, OK("MESAİ BİTTİ", "**" + j + "** olarak çalıştın ve **" + str(p) + " coin** kazandın. 💼" + tip("30 dakika sonra tekrar çalışabilirsin.")))
@kategori("eco")
@bot.command(name="balık", aliases=["fish"], help="5dk")
@commands.cooldown(1, 300, commands.BucketType.user)
async def balık(ctx):
    ensure_user(ctx.author.id, str(ctx.author))
    n, v = random.choice([("Levrek",40),("Nemo",90),("Köpekbalığı",200),("Ahtapot",120),("Eski çizme",5)])
    db.q("UPDATE users SET coins=coins+? WHERE user_id=?", (v, ctx.author.id)); await rp(ctx, OK("OLTA ÇEKİLDİ", "🎣 **" + n + "** yakaladın ve **" + str(v) + " coin** kazandın!" + tip("5 dakika sonra tekrar olta atabilirsin.")))
@kategori("eco")
@bot.command(name="maden", aliases=["mine"], help="5dk")
@commands.cooldown(1, 300, commands.BucketType.user)
async def maden(ctx):
    ensure_user(ctx.author.id, str(ctx.author))
    n, v = random.choice([("Kömür",30),("Gümüş",110),("Altın",200),("Elmas",400),("Sıradan taş",5)])
    db.q("UPDATE users SET coins=coins+? WHERE user_id=?", (v, ctx.author.id)); await rp(ctx, OK("MADEN KAZILDI", "⛏️ **" + n + "** çıkardın ve **" + str(v) + " coin** kazandın!" + tip("5 dakika sonra tekrar kazabilirsin.")))
@kategori("eco")
@bot.command(name="soy", aliases=["rob"], help="<@üye>")
@commands.cooldown(1, 600, commands.BucketType.user)
async def soy(ctx, u: discord.Member):
    if u.id == ctx.author.id or u.bot: return await rp(ctx, ER("GEÇERSİZ HEDEF", "Kendini veya botları soyamazsın."))
    ensure_user(u.id, str(u)); ensure_user(ctx.author.id, str(ctx.author))
    t = db.one("SELECT coins FROM users WHERE user_id=?", (u.id,)); me = db.one("SELECT coins FROM users WHERE user_id=?", (ctx.author.id,))
    if t["coins"] < 200: return await rp(ctx, WN("HEDEF ÇOK FAKİR", u.mention + " üyesinde soymaya değecek kadar coin yok." + tip("Hedefte en az 200 coin olmalı.")))
    if random.random() < 0.45:
        s = random.randint(50, min(500, t["coins"]))
        db.q("UPDATE users SET coins=coins-? WHERE user_id=?", (s, u.id)); db.q("UPDATE users SET coins=coins+? WHERE user_id=?", (s, ctx.author.id))
        await rp(ctx, OK("SOYGUN BAŞARILI", u.mention + " üyesinden **" + str(s) + " coin** çaldın! 🥷" + tip("10 dakika sonra tekrar deneyebilirsin.")))
    else:
        f = min(me["coins"], random.randint(50, 200)); db.q("UPDATE users SET coins=coins-? WHERE user_id=?", (f, ctx.author.id))
        await rp(ctx, ER("YAKALANDIN", "Soygun başarısız oldu, ceza olarak **" + str(f) + " coin** kaybettin. 🚔"))
@kategori("eco")
@bot.command(name="transfer", help="<@üye> <miktar>")
async def transfer(ctx, u: discord.Member, m: int):
    if m <= 0 or u.id == ctx.author.id or u.bot: return await rp(ctx, ER("GEÇERSİZ TRANSFER", "Pozitif bir miktar yazmalı ve kendin/bot dışında bir üye seçmelisin.\nÖrnek: `k!transfer @üye 100`"))
    ensure_user(u.id, str(u)); ensure_user(ctx.author.id, str(ctx.author)); me = db.one("SELECT coins FROM users WHERE user_id=?", (ctx.author.id,))
    if me["coins"] < m: return await rp(ctx, ER("BAKİYE YETERSİZ", "Hesabında **" + str(me["coins"]) + " coin** var, **" + str(m) + "** gönderemezsin."))
    db.q("UPDATE users SET coins=coins-? WHERE user_id=?", (m, ctx.author.id)); db.q("UPDATE users SET coins=coins+? WHERE user_id=?", (m, u.id))
    await rp(ctx, OK("TRANSFER TAMAMLANDI", u.mention + " üyesine **" + str(m) + " coin** gönderdin.\nKalan bakiyen: **" + str(me["coins"] - m) + " coin**"))
@kategori("eco")
@bot.command(name="bahis", aliases=["bet"], help="<miktar>")
@commands.cooldown(1, 10, commands.BucketType.user)
async def bahis(ctx, m: int):
    if m <= 0: return await rp(ctx, ER("GEÇERSİZ MİKTAR", "Bahis miktarı **0'dan büyük** olmalı.\nÖrnek: `k!bahis 100`"))
    ensure_user(ctx.author.id, str(ctx.author)); me = db.one("SELECT coins FROM users WHERE user_id=?", (ctx.author.id,))
    if me["coins"] < m: return await rp(ctx, ER("BAKİYE YETERSİZ", "Hesabında **" + str(me["coins"]) + " coin** var, **" + str(m) + "** bahis oynayamazsın."))
    w = random.random() < 0.5; db.q("UPDATE users SET coins=coins+? WHERE user_id=?", (m if w else -m, ctx.author.id))
    await rp(ctx, (OK("BAHSİ KAZANDIN", "Şansın yaver gitti! **+" + str(m) + " coin** kazandın. 🎉") if w else ER("BAHSİ KAYBETTİN", "Bu sefer olmadı, **-" + str(m) + " coin** kaybettin." + tip("Kazanma şansı %50."))))
@kategori("eco")
@bot.command(name="market", aliases=["shop"], help="Market")
async def market(ctx):
    v = Panel(head("gift", "KATRE MARKET") + "\n\nCoinlerini harcayabileceğin ürünler:")
    v.btn_url("Satın Al", SUPPORT_URL, emoji="🛒")
    await rp(ctx, v.text + "\n" + KV([(e("pro")+"Pro (30 gün)", "50.000 coin"), (e("palette")+"Rank rengi", "5.000 coin"), (e("tag")+"Özel rozet", "7.500 coin")]) + tip("Satın almak için butona basıp destek sunucusuna gel."), v)

@kategori("fun")
@bot.command(name="8ball", help="<soru>")
async def eightball(ctx, *, s): await rp(ctx, head("search", "SİHİRLİ 8 TOP") + "\n\n**Sorun:** " + s[:80] + "\n**Cevabım:** " + random.choice(["Evet! ✅", "Büyük ihtimalle 👍", "Belki... 🤔", "Hayır ❌", "Asla! 🚫", "Kesinlikle! 💯"]))
@kategori("fun")
@bot.command(name="yazıtura", help="At")
async def yazıtura(ctx):
    await rp(ctx, head("dice", "YAZI TURA") + "\n\nPara havaya atıldı... 🪙\nSonuç: **" + random.choice(["YAZI", "TURA"]) + "**")
@kategori("fun")
@bot.command(name="zar", help="1-6")
async def zar(ctx):
    r = random.randint(1, 6); await rp(ctx, head("dice", "ZAR ATILDI") + "\n\nGelen sayı: **" + str(r) + "** " + ["⚀","⚁","⚂","⚃","⚄","⚅"][r - 1])
@kategori("fun")
@bot.command(name="aşk", aliases=["ask","love"], help="<@üye>")
async def aşk(ctx, u: discord.Member):
    p = random.randint(0, 100); m = "Pek olmamış... 💔" if p < 30 else ("Fena değil! 🙂" if p < 60 else ("Güzel bir çift! 💕" if p < 85 else "RUH İKİZİ! 💘"))
    await rp(ctx, head("heart", "AŞK ÖLÇER") + "\n\n" + ctx.author.mention + " ❤️ " + u.mention + "\nUyum oranı: **%" + str(p) + "**\n" + bar(p) + "\n" + m)
@kategori("fun")
@bot.command(name="slot", help="Çevir")
async def slot(ctx):
    s = ["🍒","🍋","🍇","💎","7️⃣","⭐"]; r = [random.choice(s) for _ in range(3)]; w = len(set(r)) == 1
    await rp(ctx, head("slot", "SLOT MAKİNESİ") + "\n\n┃ " + " ┃ ".join(r) + " ┃\n\n" + ("🎉 **JACKPOT!** Üçü de aynı geldi!" if w else "Olmadı, bir daha dene! 🍀"))
@kategori("fun")
@bot.command(name="seç", aliases=["sec"], help="<a> <b>")
async def seç(ctx, *, s):
    o = s.split()
    if len(o) < 2: return await rp(ctx, ER("YETERSİZ SEÇENEK", "En az **2 seçenek** yazmalısın.\nÖrnek: `k!seç pizza hamburger`"))
    await rp(ctx, head("target", "BENİM SEÇİMİM") + "\n\nSeçenekler: " + ", ".join(o[:10]) + "\nSeçtiğim: **" + random.choice(o) + "** ✅")
@kategori("fun")
@bot.command(name="şanslı", aliases=["sansli"], help="<1-100>")
@commands.cooldown(1, 30, commands.BucketType.user)
async def şanslı(ctx, t2: int):
    if not 1 <= t2 <= 100: return await rp(ctx, ER("GEÇERSİZ SAYI", "**1-100** arası bir sayı seçmelisin.\nÖrnek: `k!şanslı 42`"))
    ensure_user(ctx.author.id, str(ctx.author)); t = random.randint(1, 100)
    if t2 == t: w, msg = 500, "Tam isabet! JACKPOT! 🎉"
    elif abs(t2 - t) <= 5: w, msg = 50, "Çok yaklaştın! 🔥"
    else: w, msg = 0, "Olmadı, tekrar dene! 🍀"
    if w: db.q("UPDATE users SET coins=coins+? WHERE user_id=?", (w, ctx.author.id))
    await rp(ctx, head("dice", "ŞANSLI NUMARA") + "\n\nTutulan sayı: **" + str(t) + "**\nSenin tahminin: **" + str(t2) + "**\n" + msg + ((" **+" + str(w) + " coin**") if w else ""))
@kategori("fun")
@bot.command(name="oylama", aliases=["anket"], help="<soru> [| A | B]")
@commands.cooldown(1, 5, commands.BucketType.user)
async def oylama(ctx, *, s):
    try:
        parts = [x.strip() for x in s.split("|")]; q = parts[0][:200] or "Anket"
        opts = [x[:60] for x in parts[1:6] if x] if len(parts) > 1 else ["Evet", "Hayır", "Çekimser"]
        if len(opts) < 2: return await rp(ctx, ER("YETERSİZ SEÇENEK", "Anket için en az **2 seçenek** gerekli.\nÖrnek: `k!oylama Pizza mı? | Evet | Hayır`"))
        cur = db.q("INSERT INTO polls(guild_id,channel_id,message_id,question,options,votes,status,creator,ts) VALUES(?,?,0,?,?,'{}','active',?,?)", (ctx.guild.id, ctx.channel.id, q, json.dumps(opts, ensure_ascii=False), ctx.author.id, datetime.datetime.now().isoformat()))
        pid = cur.lastrowid; p = db.one("SELECT * FROM polls WHERE id=?", (pid,))
        v = PollPanel(pid, opts, poll_content(p)); msg = await rp(ctx, poll_content(p), v)
        db.q("UPDATE polls SET message_id=? WHERE id=?", (msg.id, pid)); bot.add_view(v)
    except Exception as ex:
        traceback.print_exc(); await rp(ctx, ER("ANKET OLUŞTURULAMADI", str(ex)[:250]))
@kategori("fun")
@bot.command(name="ppboyu", aliases=["pp"], help="Ölçüm")
@commands.cooldown(1, 5, commands.BucketType.user)
async def ppboyu(ctx, u: discord.Member = None):
    u = u or ctx.author; n = (u.id % 18) + 3
    await rp(ctx, head("game", "PP ÖLÇER") + "\n\n" + u.mention + "\n`8" + "=" * n + "D` ─ **" + str(n + 2) + " cm**\nEfsanevi bir sonuç! 😄")
@kategori("fun")
@bot.command(name="quiz", aliases=["bilgi"], help="+75 coin")
@commands.cooldown(1, 10, commands.BucketType.user)
async def quiz(ctx):
    Q = [("Türkiye'nin başkenti neresidir?",["İstanbul","Ankara","İzmir","Bursa"],1),("Güneş sisteminin en büyük gezegeni hangisidir?",["Dünya","Mars","Jüpiter","Satürn"],2),("discord.py hangi dille yazılır?",["Java","Python","C++","Go"],1),("Suyun kimyasal formülü nedir?",["H2O","CO2","O2","NaCl"],0)]
    q, o, a = random.choice(Q)
    txt = head("game", "BİLGİ YARIŞMASI") + "\n\n**" + q + "**\n\nDoğru cevap: **+75 coin** ve **+20 XP**\nSüren: 30 saniye ⏳"
    view = Panel(txt, timeout=30); emj = ["1️⃣","2️⃣","3️⃣","4️⃣"]
    def cb(i):
        async def _c(it):
            if i == a:
                ensure_user(it.user.id, str(it.user)); db.q("UPDATE users SET coins=coins+75, xp=xp+20 WHERE user_id=?", (it.user.id,))
                await sendv_eph(it, OK("DOĞRU CEVAP!", "Tebrikler! **+75 coin** ve **+20 XP** kazandın. 🎉"))
            else: await sendv_eph(it, ER("YANLIŞ CEVAP", "Doğru cevap: **" + o[a] + "**"))
            for b in view.children:
                if isinstance(b, Button): b.disabled = True
            try: await it.message.edit(content=txt, view=view)
            except Exception: pass
        return _c
    for i, op in enumerate(o): view.btn(op[:78], cb(i), emoji=emj[i], row=0)
    await rp(ctx, txt, view)
@kategori("fun")
@bot.command(name="tahmin", help="<1-10>")
@commands.cooldown(1, 15, commands.BucketType.user)
async def tahmin(ctx, s: int):
    if not 1 <= s <= 10: return await rp(ctx, ER("GEÇERSİZ SAYI", "**1-10** arası bir sayı tahmin etmelisin.\nÖrnek: `k!tahmin 7`"))
    ensure_user(ctx.author.id, str(ctx.author)); t = random.randint(1, 10)
    if s == t:
        db.q("UPDATE users SET coins=coins+100 WHERE user_id=?", (ctx.author.id,)); await rp(ctx, OK("DOĞRU TAHMİN!", "Tutulan sayı **" + str(t) + "** idi. **+100 coin** kazandın! 🎯"))
    else: await rp(ctx, ER("BİLEMEDİN", "Tutulan sayı **" + str(t) + "** idi, senin tahminin **" + str(s) + "**." + tip("15 saniye sonra tekrar deneyebilirsin.")))
@kategori("fun")
@bot.command(name="evlen", help="<@üye>")
async def evlen(ctx, u: discord.Member):
    if u.id == ctx.author.id or u.bot: return await rp(ctx, ER("GEÇERSİZ TEKLİF", "Kendinle veya bir botla evlenemezsin."))
    if db.one("SELECT 1 FROM marriages WHERE user1=? OR user2=? OR user1=? OR user2=?", (ctx.author.id,ctx.author.id,u.id,u.id)): return await rp(ctx, ER("ZATEN EVLİ", "İkinizden biri zaten evli." + tip("Ayrılmak için `k!boşan`")))
    db.q("INSERT INTO marriages(user1,user2,since) VALUES(?,?,?)", (ctx.author.id, u.id, datetime.datetime.now().isoformat()))
    await rp(ctx, OK("EVLENDİNİZ!", ctx.author.mention + " 💍 " + u.mention + "\nMutluluklar dileriz! 🎉"))
@kategori("fun")
@bot.command(name="boşan", help="Boşan")
async def boşan(ctx):
    if not db.one("SELECT 1 FROM marriages WHERE user1=? OR user2=?", (ctx.author.id, ctx.author.id)): return await rp(ctx, WN("ZATEN BEKARSIN", "Kayıtlı bir evliliğin yok."))
    db.q("DELETE FROM marriages WHERE user1=? OR user2=?", (ctx.author.id, ctx.author.id)); await rp(ctx, WN("BOŞANDIN", "Evlilik kaydın silindi. 💔"))
@kategori("fun")
@bot.command(name="eş", help="[<@üye>]")
async def eş(ctx, u: discord.Member = None):
    u = u or ctx.author; m = db.one("SELECT * FROM marriages WHERE user1=? OR user2=?", (u.id, u.id))
    if not m: return await rp(ctx, WN("BEKAR", u.mention + " şu an evli değil." + tip("Evlenmek için `k!evlen @üye`")))
    await rp(ctx, head("ring", "EVLİLİK DURUMU") + "\n\n" + u.mention + " 💍 <@" + str(m["user2"] if m["user1"] == u.id else m["user1"]) + ">\nEvlilik tarihi: " + str(m["since"])[:10])

def giveaway_can_manage(ctx, gw):
    return bool(gw and (gw["host"] == ctx.author.id or ctx.author.guild_permissions.administrator))


@kategori("give")
@bot.command(name="çekiliş", aliases=["cekilis"], help="<süre> <kazanan> <ödül>")
@commands.has_permissions(administrator=True)
async def çekiliş(ctx, s: str, k: int, *, ö):
    try:
        dk = parse_sure(s)
    except Exception:
        return await rp(ctx, ER("GEÇERSİZ SÜRE", "Süreyi şöyle yaz: `30m`, `1h`, `2d`.\nÖrnek: `k!çekiliş 60m 1 Nitro`"))
    if dk < 1 or k < 1:
        return await rp(ctx, ER("GEÇERSİZ DEĞER", "Süre ve kazanan sayısı en az **1** olmalı."))
    ö = ö.strip()
    if not ö:
        return await rp(ctx, ER("ÖDÜL EKSİK", "Çekiliş için bir ödül yazmalısın."))
    end = datetime.datetime.now() + datetime.timedelta(minutes=dk)
    gw = {"prize": ö, "winners": k, "end_time": end.timestamp(), "host": ctx.author.id, "participants": "[]"}
    t = gw_start(gw)
    msg = await rp(ctx, t, GiveawayPanel(bot, t))
    if not msg:
        return
    db.q(
        "INSERT INTO giveaways(message_id,guild_id,channel_id,prize,winners,end_time,host) VALUES(?,?,?,?,?,?,?)",
        (msg.id, ctx.guild.id, ctx.channel.id, ö, k, end.timestamp(), ctx.author.id)
    )
    await rp(ctx, OK("ÇEKİLİŞ OLUŞTURULDU", "Çekiliş mesajı oluşturuldu. Yönetim için `k!çekilişdüzenle`, `k!çekilişbitir`, `k!çekilişiptal` ve `k!çekilişyenile` komutlarını kullanabilirsin."))


@kategori("give")
@bot.command(name="çekilişler", help="Aktifler")
async def çekilişler(ctx):
    rs = db.all("SELECT * FROM giveaways WHERE guild_id=? AND status='active'", (ctx.guild.id,))
    if not rs:
        return await rp(ctx, WN("AKTİF ÇEKİLİŞ YOK", "Şu an devam eden bir çekiliş bulunmuyor."))
    await rp(ctx, head("give", "AKTİF ÇEKİLİŞLER") + "\n\n" + "\n".join(
        e("arrow") + " **" + g["prize"] + "** ─ bitiş <t:" + str(int(g["end_time"])) + ":R> ─ ID `" + str(g["message_id"]) + "`"
        for g in rs
    ))


@kategori("give")
@bot.command(name="çekilişdüzenle", aliases=["cekilisdüzenle"], help="<id> <süre> <kazanan> <ödül>")
async def çekilişdüzenle(ctx, m: int, s: str, k: int, *, ö):
    g = db.one("SELECT * FROM giveaways WHERE message_id=? AND guild_id=?", (m, ctx.guild.id))
    if not g:
        return await rp(ctx, ER("ÇEKİLİŞ BULUNAMADI", "Bu ID ile bu sunucuda çekiliş bulunamadı."))
    if not giveaway_can_manage(ctx, g):
        return await rp(ctx, ER("YETKİ YOK", "Bu çekilişi yalnızca **oluşturan kişi** veya **sunucu yöneticileri** düzenleyebilir."))
    if g["status"] != "active":
        return await rp(ctx, ER("ÇEKİLİŞ AKTİF DEĞİL", "Sadece devam eden çekilişler düzenlenebilir."))
    try:
        dk = parse_sure(s)
    except Exception:
        return await rp(ctx, ER("GEÇERSİZ SÜRE", "Süre örnekleri: `30m`, `1h`, `2d`."))
    if dk < 1 or k < 1:
        return await rp(ctx, ER("GEÇERSİZ DEĞER", "Süre ve kazanan sayısı en az **1** olmalı."))
    ö = ö.strip()
    if not ö:
        return await rp(ctx, ER("ÖDÜL EKSİK", "Yeni ödülü yazmalısın."))
    end = datetime.datetime.now() + datetime.timedelta(minutes=dk)
    db.q("UPDATE giveaways SET prize=?, winners=?, end_time=? WHERE message_id=?", (ö, k, end.timestamp(), m))
    ng = db.one("SELECT * FROM giveaways WHERE message_id=?", (m,))
    try:
        msg = await ctx.channel.fetch_message(m)
        await msg.edit(content=gw_start(ng), view=GiveawayPanel(bot, gw_start(ng)))
    except Exception as ex:
        return await rp(ctx, WN("VERİ GÜNCELLENDİ", "Çekiliş veritabanında güncellendi fakat mesaj düzenlenemedi.\n`" + str(ex)[:120] + "`"))
    await rp(ctx, OK("ÇEKİLİŞ DÜZENLENDİ", "**Ödül:** " + ö + "\n**Kazanan:** " + str(k) + " kişi\n**Yeni bitiş:** <t:" + str(int(end.timestamp())) + ":F>"))


@kategori("give")
@bot.command(name="çekilişbitir", help="<id>")
async def çekilişbitir(ctx, m: int):
    g = db.one("SELECT * FROM giveaways WHERE message_id=? AND guild_id=?", (m, ctx.guild.id))
    if not g or g["status"] != "active":
        return await rp(ctx, ER("ÇEKİLİŞ BULUNAMADI", "Bu ID ile aktif bir çekiliş yok."))
    if not giveaway_can_manage(ctx, g):
        return await rp(ctx, ER("YETKİ YOK", "Bu çekilişi yalnızca **oluşturan kişi** veya **sunucu yöneticileri** bitirebilir."))
    await finalize_giveaway(bot, m)
    await rp(ctx, OK("ÇEKİLİŞ BİTİRİLDİ", "Kazananlar belirlendi ve duyuruldu. 🎉"))


@kategori("give")
@bot.command(name="çekilişiptal", aliases=["cekilisiptal"], help="<id>")
async def çekilişiptal(ctx, m: int):
    g = db.one("SELECT * FROM giveaways WHERE message_id=? AND guild_id=?", (m, ctx.guild.id))
    if not g or g["status"] != "active":
        return await rp(ctx, ER("ÇEKİLİŞ BULUNAMADI", "Bu ID ile aktif bir çekiliş yok."))
    if not giveaway_can_manage(ctx, g):
        return await rp(ctx, ER("YETKİ YOK", "Bu çekilişi yalnızca **oluşturan kişi** veya **sunucu yöneticileri** iptal edebilir."))
    db.q("UPDATE giveaways SET status='cancelled' WHERE message_id=?", (m,))
    try:
        msg = await ctx.channel.fetch_message(m)
        await msg.edit(content=ER("ÇEKİLİŞ İPTAL EDİLDİ", "**" + g["prize"] + "**\nBu çekiliş iptal edildi; artık katılım alınmıyor."), view=None)
    except Exception:
        pass
    await rp(ctx, WN("ÇEKİLİŞ İPTAL EDİLDİ", "Çekiliş iptal edildi ve kazanan seçilmeyecek."))


@kategori("give")
@bot.command(name="çekilişyenile", aliases=["cekilisyenile"], help="<id>")
async def çekilişyenile(ctx, m: int):
    g = db.one("SELECT * FROM giveaways WHERE message_id=? AND guild_id=?", (m, ctx.guild.id))
    if not g or g["status"] != "ended":
        return await rp(ctx, ER("YENİDEN ÇEKİLEMEZ", "Bu komut yalnızca tamamlanmış çekilişlerde kullanılabilir."))
    if not giveaway_can_manage(ctx, g):
        return await rp(ctx, ER("YETKİ YOK", "Bu çekilişi yalnızca **oluşturan kişi** veya **sunucu yöneticileri** yeniden çekebilir."))
    p = json.loads(g["participants"])
    if not p:
        return await rp(ctx, ER("KATILIMCI YOK", "Yeniden çekiliş için kayıtlı katılımcı bulunmuyor."))
    winner_id = random.choice(p)
    w = bot.get_user(int(winner_id))
    mention = w.mention if w else "<@" + str(winner_id) + ">"
    await rp_ch(ctx.channel, head("dice", "YENİDEN ÇEKİLİŞ") + "\n\n" + e("party") + " Yeni kazanan: " + mention + "\nTebrikler! 🎉")
    await rp(ctx, OK("YENİ KAZANAN BELİRLENDİ", mention + " yeni kazanan olarak seçildi."))

@kategori("pro")
@bot.command(name="pro", help="Durum + ayrıcalıklar")
async def pro(ctx, u: discord.Member = None):
    u = u or ctx.author; ensure_user(u.id, str(u)); d = db.one("SELECT * FROM users WHERE user_id=?", (u.id,))
    await rp(ctx, head("pro", "KATRE PRO") + "\n\nDurum: **" + ("PRO ÜYE ✅" if d["pro"] else "Pro değil") + "**\n\n" + e("arrow") + " Özel ses odası\n" + e("arrow") + " Renkli PRO rolü\n" + e("arrow") + " 12 saatte bir **+500 coin**\n" + e("arrow") + " Saatlik şans oyunu ve **2x XP**\n\nKomutlar: `prooda` `prorol` `probonus` `proşans` `probanner` `prorenk` `protag` `proxp`")
@kategori("pro")
@bot.command(name="prooda", help="Özel oda")
@is_pro()
async def prooda(ctx):
    c = discord.utils.get(ctx.guild.categories, name="PRO ODALAR") or await ctx.guild.create_category("PRO ODALAR")
    try: await c.set_permissions(ctx.guild.default_role, view_channel=False)
    except Exception: pass
    ch = await ctx.guild.create_voice_channel(ctx.author.display_name, category=c)
    await ch.set_permissions(ctx.author, connect=True, manage_channels=True, move_members=True)
    await rp(ctx, OK("PRO ODAN HAZIR", ch.mention + " sadece sana açık özel ses odandır. 💎"))
@kategori("pro")
@bot.command(name="prorol", help="Sunucuda renkli PRO rolü al")
@is_pro()
async def prorol(ctx):
    u = db.one("SELECT * FROM users WHERE user_id=?", (ctx.author.id,))
    try: color = discord.Color(int(u["pro_color"] or "FFD700", 16))
    except Exception: color = discord.Color.gold()
    r = discord.utils.get(ctx.guild.roles, name="KATRE PRO")
    if not r:
        try: r = await ctx.guild.create_role(name="KATRE PRO", color=color, hoist=True, reason="Pro rol")
        except Exception: return await rp(ctx, ER("YETKİM YETMEDİ", "Rol oluşturma yetkim yok."))
    else:
        try: await r.edit(color=color)
        except Exception: pass
    if r in ctx.author.roles: return await rp(ctx, WN("ROLÜN ZATEN VAR", r.mention + " rolüne zaten sahipsin."))
    await ctx.author.add_roles(r, reason="Pro üye")
    await rp(ctx, OK("PRO ROL VERİLDİ", r.mention + " rolü eklendi; rengi pro rengine göre ayarlandı." + tip("Rengi değiştirmek için `k!prorenk <hex>`")))
@kategori("pro")
@bot.command(name="probonus", help="12 saatte bir +500 coin (PRO)")
@is_pro()
@commands.cooldown(1, 43200, commands.BucketType.user)
async def probonus(ctx):
    db.q("UPDATE users SET coins=coins+500 WHERE user_id=?", (ctx.author.id,))
    await rp(ctx, OK("PRO BONUS ALINDI", "Hesabına **+500 coin** eklendi. 💎\nBir sonraki bonus: <t:" + str(int(datetime.datetime.now().timestamp()) + 43200) + ":R>"))
@kategori("pro")
@bot.command(name="probanner", help="<metin> — Havalı PRO banner")
@is_pro()
async def probanner(ctx, *, m):
    t = m[:38].upper().center(38); n = ("@" + ctx.author.display_name)[:38].center(38)
    await rp(ctx, "```╔══════════════════════════════════════════╗\n║" + t + "║\n║" + n + "║\n║            [ KATRE PRO ÜYESİ ]           ║\n╚══════════════════════════════════════════╝```")
@kategori("pro")
@bot.command(name="proşans", aliases=["prosans"], help="Saatlik şans: 1000 coin (PRO)")
@is_pro()
@commands.cooldown(1, 3600, commands.BucketType.user)
async def proşans(ctx):
    n = random.randint(1, 50); win = n <= 10
    if win:
        db.q("UPDATE users SET coins=coins+1000 WHERE user_id=?", (ctx.author.id,))
        await rp(ctx, OK("PRO ŞANS KAZANDIN!", "Çekilen sayı **" + str(n) + "** ─ **+1000 coin** kazandın! 🎉"))
    else:
        await rp(ctx, ER("PRO ŞANS OLMADI", "Çekilen sayı **" + str(n) + "** ─ bu sefer olmadı." + tip("1-10 arası gelirse kazanırsın. 1 saat sonra tekrar dene.")))
@kategori("pro")
@bot.command(name="prorenk", help="<hex>")
@is_pro()
async def prorenk(ctx, h: str):
    h = h.lstrip("#")
    if len(h) != 6: return await rp(ctx, ER("GEÇERSİZ RENK", "Renk **6 haneli hex** olmalı.\nÖrnek: `k!prorenk ff0000`"))
    try: int(h, 16)
    except ValueError: return await rp(ctx, ER("GEÇERSİZ HEX KODU", "Sadece `0-9` ve `a-f` karakterleri kullan.\nÖrnek: `k!prorenk 00ff88`"))
    db.q("UPDATE users SET pro_color=? WHERE user_id=?", (h, ctx.author.id)); await rp(ctx, OK("PRO RENK KAYDEDİLDİ", "Yeni rengin: **#" + h.upper() + "**" + tip("Rolüne uygulamak için `k!prorol` yaz.")))
@kategori("pro")
@bot.command(name="prostats", help="Detay")
@is_pro()
async def prostats(ctx):
    d = db.one("SELECT * FROM users WHERE user_id=?", (ctx.author.id,))
    await rp(ctx, head("chart", "PRO İSTATİSTİKLERİN") + "\n\n" + KV([(e("dot")+"Mesaj", d["messages"]), (e("dot")+"Seviye", d["level"]), (e("dot")+"Coin", d["coins"]), (e("dot")+"2x XP", "Açık ✅" if d["xp2"] else "Kapalı")]))
@kategori("pro")
@bot.command(name="proyazı", help="<metin>")
@is_pro()
async def proyazı(ctx, *, m): await rp(ctx, head("pen", "PRO YAZI") + "\n\n" + fancy(m[:200]))
@kategori("pro")
@bot.command(name="proembed", help="<b> | <m> | <hex>")
@is_pro()
async def proembed(ctx, *, a):
    p = [x.strip() for x in a.split("|")]
    if len(p) < 2: return await rp(ctx, ER("FORMAT HATALI", "Başlık ile mesajı `|` ile ayırmalısın.\nÖrnek: `k!proembed Duyuru | Merhaba herkese!`"))
    await rp(ctx, "### " + p[0][:100] + "\n" + DIV + "\n" + p[1][:1500] + "\n\n" + e("pro") + " " + ctx.author.display_name)
@kategori("pro")
@bot.command(name="protag", help="<metin>")
@is_pro()
async def protag(ctx, *, t):
    db.q("UPDATE users SET pro_tag=? WHERE user_id=?", (t[:12], ctx.author.id)); await rp(ctx, OK("PRO ROZET KAYDEDİLDİ", "Rozetin: **" + t[:12] + "**\nRank kartında görünecek."))
@kategori("pro")
@bot.command(name="proxp", help="2x")
@is_pro()
async def proxp(ctx):
    u = db.one("SELECT xp2 FROM users WHERE user_id=?", (ctx.author.id,)); n = 0 if u["xp2"] else 1
    db.q("UPDATE users SET xp2=? WHERE user_id=?", (n, ctx.author.id)); await rp(ctx, OK("2x XP " + ("AÇILDI" if n else "KAPANDI"), "Artık sohbet ederken **" + ("iki kat" if n else "normal") + "** XP kazanıyorsun."))

@kategori("owner")
@bot.command(name="duyuru", aliases=["duyur","announce"], help="<metin> — Tüm sunucu sahiplerine DM (Owner+Half)")
@is_half()
@commands.cooldown(1, 120, commands.BucketType.user)
async def duyuru(ctx, *, m):
    t = head("warn", "DUYURU ONAYI") + "\n\n**" + str(len(bot.guilds)) + "** sunucunun sahibine DM gönderilecek.\n\n**Duyuru metni:**\n" + _q(m[:400]) + "\n\nOnaylıyor musun?"
    v = ConfirmPanel(t, 60); await rp(ctx, t, v); await v.wait()
    if not v.value: return await rp(ctx, WN("DUYURU İPTAL", "Hiçbir sunucu sahibine mesaj gönderilmedi."))
    txt = head("owner", "KATRE DUYURU") + "\n\n" + m[:1500] + "\n\n" + e("dot") + " Gönderen: " + ctx.author.mention + "\n" + e("link") + " Destek: " + SUPPORT_URL
    ok = 0; fail = 0; seen = set()
    for g in list(bot.guilds):
        if g.owner_id in seen: continue
        seen.add(g.owner_id)
        try:
            u = bot.get_user(g.owner_id) or await bot.fetch_user(g.owner_id)
            await u.send(txt); ok += 1
        except Exception: fail += 1
        await asyncio.sleep(0.4)
    await rp(ctx, OK("DUYURU GÖNDERİLDİ", "**" + str(ok) + "** sunucu sahibine ulaştı.\n**" + str(fail) + "** kişide DM kapalıydı."))
@kategori("owner")
@bot.command(name="halfownerbilgi", aliases=["hob", "coownerinfo"], help="[<@üye>] — Half Owner bilgisi")
@is_half()
async def halfownerbilgi(ctx, u: discord.Member = None):
    u = u or ctx.author
    row = db.one("SELECT * FROM half_owners WHERE user_id=?", (u.id,))
    if not row:
        return await rp(ctx, WN("HALF OWNER DEĞİL", u.mention + " şu anda Half Owner değil."))
    added = "<@" + str(row["added_by"]) + ">" if row.get("added_by") else "—"
    since = str(row.get("since") or "—")[:19].replace("T", " ")
    await rp(ctx, head("owner", "HALF OWNER BİLGİSİ") + "\n\n" + KV([
        (e("shield") + "Üye", u.mention),
        (e("alarm") + "Atanma", since),
        (e("crown") + "Atayan", added),
        (e("diamond") + "Pro yönetimi", "Açık"),
        (e("log") + "Pro logları", "Açık"),
        (e("warn") + "Bakım yönetimi", "Kapalı"),
        (e("gear") + "Owner komutları", "Kapalı")
    ]))

@kategori("owner")
@bot.command(name="protopluver", help="<@rol> [gün] — Role toplu Pro")
@is_half()
async def protopluver(ctx, role: discord.Role, g: int = 30):
    if g < 1 or g > 3650:
        return await rp(ctx, ER("GEÇERSİZ SÜRE", "Pro süresi **1-3650 gün** arasında olmalı."))
    me = ctx.guild.me
    if role.is_default() or role.managed or (me and role >= me.top_role):
        return await rp(ctx, ER("ROL HİYERARŞİSİ", "Bu rol botun yönetebileceği seviyede değil."))
    members = [m for m in role.members if not m.bot and m.id != OWNER_ID and not is_half_owner(m.id)]
    if not members:
        return await rp(ctx, WN("ÜYE YOK", "Bu rolde Pro verilebilecek üye bulunamadı."))
    ex = (datetime.datetime.now() + datetime.timedelta(days=g)).isoformat()
    for m in members:
        ensure_user(m.id, str(m)); db.q("UPDATE users SET pro=1, pro_expiry=? WHERE user_id=?", (ex, m.id)); pro_log(m.id, "TOPLU_VERİLDİ", g, ctx.author.id)
    await rp(ctx, OK("TOPLU PRO VERİLDİ", role.mention + " rolündeki **" + str(len(members)) + "** üyeye **" + str(g) + " gün** Pro verildi."))

@kategori("owner")
@bot.command(name="protoplual", help="<@rol> — Role toplu Pro kaldır")
@is_half()
async def protoplual(ctx, role: discord.Role):
    members = [m for m in role.members if not m.bot and m.id != OWNER_ID and not is_half_owner(m.id)]
    changed = 0
    for m in members:
        row = db.one("SELECT pro FROM users WHERE user_id=?", (m.id,))
        if row and row["pro"]:
            db.q("UPDATE users SET pro=0, pro_expiry=NULL WHERE user_id=?", (m.id,)); pro_log(m.id, "TOPLU_ALINDI", 0, ctx.author.id); changed += 1
    await rp(ctx, WN("TOPLU PRO ALINDI", role.mention + " rolündeki **" + str(changed) + "** üyeden Pro kaldırıldı."))

@kategori("owner")
@bot.command(name="halfowner", aliases=["coowner"], help="<ayarla/kaldır/bilgi/liste>")
async def halfowner(ctx, i: str = "bilgi", u: discord.Member = None):
    i = i.lower()
    if i in ("ayarla","ekle"):
        if ctx.author.id != OWNER_ID: return
        if not u: return await rp(ctx, ER("ÜYE BELİRTMEDİN", "Kimi atayacağını yazmalısın.\nÖrnek: `k!halfowner ayarla @üye`"))
        db.q("INSERT OR REPLACE INTO half_owners(user_id,since,added_by) VALUES(?,?,?)", (u.id, datetime.datetime.now().isoformat(), ctx.author.id))
        await rp(ctx, OK("HALF OWNER ATANDI", u.mention + " artık Half Owner.\nPro verme/alma, pro logları ve duyuru komutlarını kullanabilir."))
    elif i in ("kaldır","remove"):
        if ctx.author.id != OWNER_ID: return
        db.q("DELETE FROM half_owners WHERE user_id=?", ((u or ctx.author).id,)); await rp(ctx, WN("HALF OWNER KALDIRILDI", "Üyenin Half Owner yetkisi geri alındı."))
    elif i == "liste":
        rs = db.all("SELECT * FROM half_owners")
        await rp(ctx, head("owner", "HALF OWNER LİSTESİ") + "\n\n" + (("\n".join(e("arrow") + " <@" + str(r["user_id"]) + ">" for r in rs)) if rs else "Henüz kimse atanmamış."))
    else:
        me = db.one("SELECT * FROM half_owners WHERE user_id=?", (ctx.author.id,))
        await rp(ctx, head("owner", "HALF OWNER") + "\n\nYetkileri: `prover` `proal` `prologlar` `duyuru`\nDiğer owner komutları kapalıdır.\n\n" + (e("check") + " Sen bir Half Owner'sın." if me else e("info") + " Sen Half Owner değilsin."))
@kategori("owner")
@bot.command(name="ownerbilgi", aliases=["ownerinfo", "botdurum"], help="Owner sistem bilgileri")
@is_half()
async def ownerbilgi(ctx):
    up = str(datetime.datetime.now() - bot.start_time).split(".")[0] if hasattr(bot, "start_time") else "—"
    db_size = "—"
    try:
        db_size = str(round(os.path.getsize(DB_PATH) / 1024 / 1024, 2)) + " MB"
    except Exception:
        pass
    await rp(ctx, head("owner", "OWNER SİSTEM BİLGİSİ") + "\n\n" + KV([
        (e("robot") + "Bot", bot.user.name if bot.user else "—"),
        (e("tag") + "Sürüm", "v" + BOT_VERSION),
        (e("genel") + "Sunucu", str(len(bot.guilds))),
        (e("dot") + "Kullanıcı", str(sum(g.member_count or 0 for g in bot.guilds))),
        (e("gear") + "Komut", str(len(bot.commands))),
        (e("bolt") + "Ping", str(round(bot.latency * 1000)) + " ms"),
        (e("alarm") + "Uptime", up),
        (e("shield") + "Half Owner", str(len(db.all("SELECT 1 FROM half_owners")))),
        (e("database") + "DB", db_size),
        (e("warn") + "Bakım", "AÇIK" if is_maintenance() else "KAPALI")
    ]) + tip("Owner ve Half Owner bu paneli görebilir; bakım açma/kapama yalnızca Owner'dadır."))

@kategori("owner")
@bot.command(name="sunucusay", aliases=["guildcount"], help="Botun bağlı olduğu sunucu sayısı")
@is_half()
async def sunucusay(ctx):
    total_members = sum(g.member_count or 0 for g in bot.guilds)
    await rp(ctx, OK("SUNUCU SAYISI", "Bot şu anda **" + str(len(bot.guilds)) + "** sunucuda.\nToplam yaklaşık üye sayısı: **" + str(total_members) + "**."))

@kategori("owner")
@bot.command(name="guildbilgi", aliases=["sunucubul"], help="<sunucu_id> — Sunucu bilgisi")
@is_half()
async def guildbilgi(ctx, guild_id: int):
    g = bot.get_guild(guild_id)
    if not g:
        return await rp(ctx, ER("SUNUCU BULUNAMADI", "Bot bu ID ile bir sunucuda bulunmuyor."))
    owner = "<@" + str(g.owner_id) + ">" if g.owner_id else "—"
    await rp(ctx, head("owner", "SUNUCU BİLGİSİ") + "\n\n" + KV([
        (e("crown") + "Sunucu", g.name),
        (e("tag") + "ID", str(g.id)),
        (e("dot") + "Üye", str(g.member_count or 0)),
        (e("genel") + "Kanal", str(len(g.channels))),
        (e("shield") + "Rol", str(len(g.roles))),
        (e("crown") + "Sahip", owner),
        (e("spark") + "Boost", "Seviye " + str(g.premium_tier) + " • " + str(g.premium_subscription_count or 0))
    ]))

@kategori("owner")
@bot.command(name="sahip", aliases=["owner","panel"], help="Panel")
@is_owner()
async def sahip(ctx):
    t = head("owner", "OWNER PANELİ") + "\n\nBakım modu, istatistik, sunucu listesi ve genel duyuru için butonları kullan."; await rp(ctx, t + "\n\n" + KV([(e("dot")+"Sunucu", len(bot.guilds)), (e("dot")+"Bakım", "AÇIK" if is_maintenance() else "KAPALI"), (e("dot")+"Sürüm", "v" + BOT_VERSION)]), OwnerPanel(bot, t))
@kategori("owner")
@bot.command(name="bakım", aliases=["bakim"], help="<aç/kapat>")
@is_owner()
async def bakım(ctx, mod: str = None):
    if mod is None or mod.lower() in ("kapat","off","0"):
        db.q("UPDATE owner_settings SET maintenance=0 WHERE id=1"); await rp(ctx, OK("BAKIM MODU KAPALI", "Tüm kullanıcılar komutları tekrar kullanabilir."))
    else:
        db.q("UPDATE owner_settings SET maintenance=1 WHERE id=1"); await rp(ctx, WN("BAKIM MODU AÇIK", "Sadece sen komut kullanabilirsin; diğer üyeler 'Bakımdayız' mesajı görür."))
@kategori("owner")
@bot.command(name="restart", aliases=["rb"], help="Yeniden başlat")
@is_owner()
async def restart(ctx):
    await rp(ctx, WN("YENİDEN BAŞLATILIYOR", "Bot **2 saniye** içinde yeniden başlayacak.\nButonlar ve ayarlar korunur."))
    await asyncio.sleep(2)
    try: os.execv(sys.executable, [sys.executable] + sys.argv)
    except Exception: sys.exit(0)
@kategori("owner")
@bot.command(name="yedek", help="<durum/kaydet/yükle> [emoji/pro/settings]")
@is_owner()
async def yedek(ctx, i: str = "durum", hedef: str = None):
    if not BACKUP_CH: return await rp(ctx, ER("YEDEK KANALI YOK", "Ortam değişkenlerine `BACKUP_CHANNEL_ID` eklemelisin."))
    i = i.lower()
    if i == "kaydet":
        await push_backup(bot, "emoji", EMO_CACHE); await push_backup(bot, "pro", pro_snapshot()); await push_backup(bot, "settings", settings_snapshot())
        _HASH["emoji"] = json.dumps(EMO_CACHE, sort_keys=True); _HASH["pro"] = json.dumps(pro_snapshot(), sort_keys=True, default=str); _HASH["set"] = json.dumps(settings_snapshot(), sort_keys=True, default=str)
        await rp(ctx, OK("YEDEK ALINDI", "Emoji, pro, ayarlar ve Half Owner verileri bulut kanalına yazıldı. ☁️"))
    elif i == "yükle":
        h = (hedef or "hepsi").lower(); msg = []
        if h in ("emoji","hepsi"):
            d = await pull_backup(bot, "emoji")
            if d: msg.append("emoji: " + str(emoji_restore(d)))
        if h in ("pro","hepsi"):
            d = await pull_backup(bot, "pro")
            if d: msg.append("pro: " + str(pro_restore(d)))
        if h in ("settings","ayarlar","hepsi"):
            d = await pull_backup(bot, "settings")
            if d: msg.append("ayar+half: " + str(settings_restore(d)))
        await rp(ctx, OK("YEDEK YÜKLENDİ", ", ".join(msg)) if msg else WN("YEDEK BULUNAMADI", "Yüklenecek uygun bir yedek bulunamadı."))
    else:
        await rp(ctx, head("log", "YEDEK DURUMU") + "\n\n" + KV([(e("dot")+"Emoji", len(EMO_CACHE)), (e("dot")+"Pro üye", len(db.all("SELECT 1 FROM users WHERE pro=1"))), (e("dot")+"Half Owner", len(db.all("SELECT 1 FROM half_owners"))), (e("dot")+"Ayar kaydı", sum(len(v) for v in settings_snapshot().values()))]) + tip("Otomatik yedek her dakika kontrol edilir."))
@kategori("owner")
@bot.command(name="istatistik-kanal", help="<#kanal|kapat>")
@is_owner()
async def istatistik_kanal(ctx, ch: discord.TextChannel = None):
    if ch is None:
        db.q("DELETE FROM bot_meta WHERE key='stats_ch'"); await rp(ctx, OK("İSTATİSTİK PANOSU KAPANDI", "Canlı istatistik mesajı artık gönderilmeyecek."))
    else:
        db.q("INSERT OR REPLACE INTO bot_meta(key,value) VALUES('stats_ch',?)", (str(ch.id),)); await rp(ctx, OK("İSTATİSTİK PANOSU AYARLANDI", ch.mention + " kanalına **10 dakikada bir** canlı istatistik gönderilecek."))
@kategori("owner")
@bot.command(name="güncelleme-kanal", aliases=["guncelleme-kanal"], help="<#kanal|kapat>")
@is_owner()
async def güncelleme_kanal(ctx, ch: discord.TextChannel = None):
    if ch is None:
        db.q("DELETE FROM bot_meta WHERE key='update_ch'"); await rp(ctx, OK("GÜNCELLEME DUYURUSU KAPANDI", "Yeni sürüm notları artık paylaşılmayacak."))
    else:
        db.q("INSERT OR REPLACE INTO bot_meta(key,value) VALUES('update_ch',?)", (str(ch.id),)); await rp(ctx, OK("GÜNCELLEME KANALI AYARLANDI", "Yeni sürüm notları " + ch.mention + " kanalında paylaşılacak.\nBot bir sonraki açılışta yeni sürümü duyurur."))
@kategori("owner")
@bot.command(name="sürüm", aliases=["surum"], help="Sürüm")
async def sürüm(ctx):
    if V2_OK:
        try: return await ctx.send(view=update_view(bot, BOT_VERSION))
        except Exception: traceback.print_exc()
    await rp(ctx, update_text(BOT_VERSION))
@kategori("owner")
@bot.command(name="v2test", help="Components V2 testi + rapor")
@is_owner()
async def v2test(ctx):
    info = ["discord.py " + discord.__version__]
    for nm in ("LayoutView", "Container", "TextDisplay", "ActionRow", "Section", "Separator"):
        info.append(nm + ": " + ("✅ var" if hasattr(discord.ui, nm) else "❌ yok"))
    if HAS_V2:
        try:
            await ctx.send(view=_make_lv(head("spark", "V2 TEST") + "\nBu mesaj renkli şeritli kart olarak görünüyorsa V2 çalışıyor!"))
            info.append("LayoutView gönderim: ✅")
        except Exception as ex:
            info.append("LayoutView gönderim: ❌ " + str(ex)[:60])
    else:
        info.append("HAS_V2: ❌ → mesajlar klasik modda")
    await rp(ctx, head("gear", "V2 RAPORU") + "\n\n" + "\n".join(e("arrow") + " " + i for i in info))
@kategori("owner")
@bot.command(name="emoji", help="<ayarla/yakala/oto/liste/sıfırla/slotlar>")
@is_owner()
async def emoji_cmd(ctx, i: str = "slotlar", slot: str = None, *, val=None):
    i = i.lower()
    if i in ("ayarla","set"):
        if not slot or not val or "<" not in val: return await rp(ctx, ER("FORMAT HATALI", "Slot adı ve özel emoji yazmalısın.\nÖrnek: `k!emoji ayarla check <:tik:123...>`"))
        slot = slot.lower()
        if slot not in SLOTS: return await rp(ctx, ER("GEÇERSİZ SLOT", "Geçerli slotları görmek için `k!emoji slotlar` yaz."))
        db.q("INSERT OR REPLACE INTO emojis(slot,emoji) VALUES(?,?)", (slot, val)); refresh_emojis(); await rp(ctx, OK("EMOJİ AYARLANDI", "`" + slot + "` slotu artık " + val + " emojisini kullanacak."))
    elif i == "yakala":
        if not slot: return await rp(ctx, ER("SLOT YAZMADIN", "Emojili bir mesajı yanıtlayıp `k!emoji yakala check` yaz."))
        ref = ctx.message.reference; mg = ref.resolved if ref else None
        if not mg: return await rp(ctx, ER("MESAJI YANITLA", "Özel emoji içeren bir mesaja yanıt vererek komutu yazmalısın."))
        f = str(mg.emojis[0]) if getattr(mg, "emojis", None) else None
        if not f:
            mm = re.search(r"<a?:[a-zA-Z0-9_]+:\d+>", mg.content or ""); f = mm.group(0) if mm else None
        if not f: return await rp(ctx, ER("EMOJİ BULUNAMADI", "Yanıtladığın mesajda özel emoji yok."))
        db.q("INSERT OR REPLACE INTO emojis(slot,emoji) VALUES(?,?)", (slot.lower(), f)); refresh_emojis(); await rp(ctx, OK("EMOJİ YAKALANDI", "`" + slot.lower() + "` → " + f))
    elif i == "oto":
        mp = auto_map_emojis(ctx.guild)
        if not mp: return await rp(ctx, WN("EŞLEŞME BULUNAMADI", "Sunucundaki emoji isimleri bilinen slotlarla eşleşmedi." + tip("`k!emoji yakala <slot>` ile elle ekleyebilirsin.")))
        await rp(ctx, OK("OTOMATİK EŞLEŞTİRME", "**" + str(len(mp)) + "** slot sunucu emojilerinle eşleşti."))
    elif i in ("liste","list"):
        rs = db.all("SELECT * FROM emojis")
        await rp(ctx, head("star", "AYARLI EMOJİLER") + "\n\n" + (("\n".join(e("arrow") + " `" + r["slot"] + "` " + r["emoji"] for r in rs)) if rs else "Henüz özel emoji ayarlanmamış."))
    elif i in ("sıfırla","reset"):
        if slot in (None,"tümü","all"): db.q("DELETE FROM emojis")
        else: db.q("DELETE FROM emojis WHERE slot=?", (slot.lower(),))
        refresh_emojis(); await rp(ctx, OK("EMOJİLER SIFIRLANDI", "Slotlar varsayılan emojilere döndü."))
    else:
        await rp(ctx, head("info", "EMOJİ SLOTLARI") + "\n\nAyarlayabileceğin slotlar:\n`" + "`, `".join(SLOTS.keys()) + "`")
@kategori("owner")
@bot.command(name="prover", help="<@üye> [gün]")
@is_half()
async def prover(ctx, u: discord.Member, g: int = 30):
    ensure_user(u.id, str(u)); ex = (datetime.datetime.now() + datetime.timedelta(days=g)).isoformat()
    db.q("UPDATE users SET pro=1, pro_expiry=? WHERE user_id=?", (ex, u.id)); pro_log(u.id, "VERİLDİ", g, ctx.author.id)
    await rp(ctx, OK("PRO VERİLDİ", u.mention + " için **" + str(g) + " gün** boyunca Pro ayrıcalıkları aktif. 💎"))
    try: await u.send(OK("PRO ÜYE OLDUN!", "**" + str(g) + " günlük** Pro üyeliğin başladı. Komutlar için `k!pro` yaz."))
    except Exception: pass
@kategori("owner")
@bot.command(name="proal", help="<@üye>")
@is_half()
async def proal(ctx, u: discord.Member):
    db.q("UPDATE users SET pro=0, pro_expiry=NULL WHERE user_id=?", (u.id,)); pro_log(u.id, "ALINDI", 0, ctx.author.id)
    await rp(ctx, WN("PRO ALINDI", u.mention + " üyesinin Pro üyeliği sonlandırıldı."))
@kategori("owner")
@bot.command(name="prologlar", help="Log")
@is_half()
async def prologlar(ctx, u: discord.User = None):
    rs = db.all("SELECT * FROM pro_logs WHERE user_id=? ORDER BY id DESC LIMIT 15", (u.id,)) if u else db.all("SELECT * FROM pro_logs ORDER BY id DESC LIMIT 15")
    if not rs: return await rp(ctx, WN("KAYIT YOK", "Henüz Pro işlem kaydı bulunmuyor."))
    await rp(ctx, head("log", "PRO İŞLEM KAYITLARI") + "\n\nSon " + str(len(rs)) + " işlem:\n" + "\n".join(e("arrow") + " **" + r["action"] + "** ─ <@" + str(r["user_id"]) + "> ─ " + r["ts"][:10] for r in rs))
@kategori("owner")
@bot.command(name="prefix", help="<yeni>")
@is_owner()
async def prefix(ctx, y: str):
    ensure_server(ctx.guild.id); db.q("UPDATE servers SET prefix=? WHERE guild_id=?", (y, ctx.guild.id)); await rp(ctx, OK("ÖNEK DEĞİŞTİ", "Bu sunucuda yeni komut öneki: `" + y + "`\nÖrnek: `" + y + "yardım`"))
@kategori("owner")
@bot.command(name="blacklist", aliases=["bl"], help="<ekle/çıkar> <@üye>")
@is_owner()
async def blacklist(ctx, i: str, u: discord.User, *, s="—"):
    if i.lower() in ("ekle","add"):
        db.q("INSERT OR REPLACE INTO blacklist(user_id,reason) VALUES(?,?)", (u.id, s)); await rp(ctx, OK("KARA LİSTEYE EKLENDİ", u.mention + " artık botu kullanamaz.\nSebep: " + s[:150]))
    elif i.lower() in ("çıkar","remove"):
        db.q("DELETE FROM blacklist WHERE user_id=?", (u.id,)); await rp(ctx, OK("KARA LİSTEDEN ÇIKARILDI", u.mention + " botu tekrar kullanabilir."))
    else: await rp(ctx, ER("GEÇERSİZ İŞLEM", "Kullanım: `k!blacklist ekle @üye [sebep]` veya `k!blacklist çıkar @üye`"))
@kategori("owner")
@bot.command(name="durum", aliases=["status"], help="<metin>")
@is_owner()
async def durum(ctx, *, m):
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name=m)); await rp(ctx, OK("BOT DURUMU DEĞİŞTİ", "Yeni durum: **" + m[:60] + "**" + tip("Durum döngüsü kısa süre sonra kendi mesajlarını göstermeye devam eder.")))
@kategori("owner")
@bot.command(name="sunucular", aliases=["guilds"], help="Liste")
@is_owner()
async def sunucular(ctx):
    rs = sorted(bot.guilds, key=lambda g: -(g.member_count or 0))
    await rp(ctx, head("owner", "SUNUCULAR") + "\n\nToplam **" + str(len(rs)) + "** sunucu • en kalabalık 15:\n" + "\n".join(e("arrow") + " **" + g.name + "** ─ " + str(g.member_count) + " üye" for g in rs[:15]))
@kategori("owner")
@bot.command(name="eval", aliases=["py"], help="<kod>")
@is_owner()
async def eval_cmd(ctx, *, code):
    env = {"bot": bot, "ctx": ctx, "db": db, "discord": discord, "guild": ctx.guild, "author": ctx.author}
    buf = io.StringIO(); fn = "async def __f():\n" + textwrap.indent(code, "    ")
    try:
        exec(compile(fn, "<e>", "exec"), env)
        with redirect_stdout(buf): await env["__f"]()
        await ctx.send("```py\n" + (buf.getvalue()[:1900] or "OK") + "\n```")
    except Exception as ex: await ctx.send("```py\n" + str(ex)[:1900] + "\n```")

# ═══════════════════════════════════════════════════════════════════
# 🆕 v5.6 YENİ KOMUTLAR
# ═══════════════════════════════════════════════════════════════════
import ast, operator
_CALC_OPS = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul, ast.Div: operator.truediv, ast.FloorDiv: operator.floordiv, ast.Mod: operator.mod, ast.Pow: operator.pow, ast.USub: operator.neg, ast.UAdd: operator.pos}
def _calc(n):
    if isinstance(n, ast.Expression): return _calc(n.body)
    if isinstance(n, ast.Constant) and isinstance(n.value, (int, float)) and not isinstance(n.value, bool): return n.value
    if isinstance(n, ast.BinOp) and type(n.op) in _CALC_OPS:
        a, b = _calc(n.left), _calc(n.right)
        if isinstance(n.op, ast.Pow) and (abs(b) > 100 or abs(a) > 1000000): raise ValueError("Üs çok büyük")
        return _CALC_OPS[type(n.op)](a, b)
    if isinstance(n, ast.UnaryOp) and type(n.op) in _CALC_OPS: return _CALC_OPS[type(n.op)](_calc(n.operand))
    raise ValueError("Desteklenmeyen ifade")
@kategori("genel")
@bot.command(name="komuttest", aliases=["testkomut"], help="Komut sistemini teşhis eder")
async def komuttest(ctx):
    prefs = await bot.get_prefix(ctx.message)
    p = ", ".join("`" + str(x) + "`" for x in prefs[:8])
    await rp(ctx, OK("KOMUT SİSTEMİ ÇALIŞIYOR", "Prefixler: " + p + "\nMesaj: `" + ctx.message.content[:120].replace("`", "ˋ") + "`\nKayıtlı komut: **" + str(len(bot.commands)) + "**"))
@kategori("genel")
@bot.command(name="prefixgoster", aliases=["önek", "onek", "prefixbilgi"], help="Sunucu prefixini gösterir")
async def prefix_show(ctx):
    prefs = await bot.get_prefix(ctx.message)
    custom = [x for x in prefs if x not in {"k!", "K!"} and not x.startswith("<@")]
    await rp(ctx, head("gear", "PREFIX") + "\n\nVarsayılan: `k!`\nSunucu prefixi: `" + (custom[0] if custom else "k!") + "`")
@kategori("genel")
@bot.command(name="hesapla", aliases=["calc", "hesap"], help="<işlem> — hesap makinesi")
@commands.cooldown(1, 2, commands.BucketType.user)
async def hesapla(ctx, *, ifade: str):
    raw = ifade.strip()[:100]; ex = raw.replace(",", ".").replace("×", "*").replace("÷", "/").replace("^", "**").replace("x", "*") if re.fullmatch(r"[\d\s.,+\-*/%()^x×÷]+", raw) else raw
    try:
        v = _calc(ast.parse(ex, mode="eval"))
        if isinstance(v, float): v = int(v) if v == int(v) and abs(v) < 1e15 else round(v, 10)
        await rp(ctx, OK("HESAPLANDI", "`" + raw + "` = **" + str(v) + "** 🧮"))
    except ZeroDivisionError:
        await rp(ctx, ER("SIFIRA BÖLÜNEMEZ", "Bir sayıyı sıfıra bölemezsin. 🙃"))
    except Exception as ex2:
        await rp(ctx, ER("HESAPLANAMADI", "İfadeyi anlayamadım: `" + str(ex2)[:60] + "`\nÖrnek: `k!hesapla 12*(3+4)`\nDesteklenenler: `+ - * / // % ** ( )`"))
@kategori("genel")
@bot.command(name="kullanıcıbilgi", aliases=["userinfo", "ui", "kb"], help="[@üye] — detaylı üye bilgisi")
@commands.cooldown(1, 3, commands.BucketType.user)
async def kullanicibilgi(ctx, u: discord.Member = None):
    u = u or ctx.author; cr = int(u.created_at.timestamp()); jn = int(u.joined_at.timestamp()) if u.joined_at else cr
    roller = [r for r in reversed(u.roles) if r.id != ctx.guild.id]
    txt = (head("search", u.display_name + " • KULLANICI BİLGİSİ") + "\n\n" + KV([(e("dot")+"Kullanıcı", str(u)), (e("dot")+"ID", u.id), (e("alarm")+"Hesap açılışı", "<t:" + str(cr) + ":D>"), (e("wave")+"Sunucuya katılım", "<t:" + str(jn) + ":R>"),
           (e("crown")+"En yüksek rol", roller[0].mention if roller else "—"), (e("tag")+"Rol sayısı", len(roller)), (e("robot")+"Tür", "Bot" if u.bot else "Üye")]))
    if roller: txt += "\n\n**Roller**\n" + " ".join(r.mention for r in roller[:12]) + (("  +" + str(len(roller) - 12) + " rol daha") if len(roller) > 12 else "")
    await send_thumb(ctx, txt, u.display_avatar.url, accent=(u.colour.value or None))
@kategori("genel")
@bot.command(name="kanalbilgi", aliases=["channelinfo", "kanal"], help="[#kanal] — kanal bilgisi")
@commands.cooldown(1, 3, commands.BucketType.user)
async def kanalbilgi(ctx, ch: discord.TextChannel = None):
    ch = ch or ctx.channel; sm = getattr(ch, "slowmode_delay", 0) or 0
    await rp(ctx, head("pen", "#" + str(ch.name) + " • KANAL BİLGİSİ") + "\n\n" + KV([(e("dot")+"Kanal", ch.mention), (e("dot")+"ID", ch.id), (e("clip")+"Kategori", ch.category.name if getattr(ch, "category", None) else "—"),
        (e("pen")+"Konu", ((getattr(ch, "topic", None) or "—")[:100])), (e("time")+"Yavaş mod", sn_txt(sm) if sm else "Kapalı"), (e("lock")+"NSFW", "Evet 🔞" if getattr(ch, "nsfw", False) else "Hayır"),
        (e("alarm")+"Oluşturulma", "<t:" + str(int(ch.created_at.timestamp())) + ":D>")]))
@kategori("genel")
@bot.command(name="botbilgi", aliases=["about", "hakkında"], help="Bot hakkında")
@commands.cooldown(1, 5, commands.BucketType.user)
async def botbilgi(ctx):
    up = str(datetime.datetime.now() - bot.start_time).split(".")[0]
    inv = "https://discord.com/oauth2/authorize?client_id=" + str(bot.user.id) + "&permissions=8&scope=bot%20applications.commands"
    txt = (head("robot", bot.user.name.upper() + " • HAKKINDA") + "\n\nModerasyon, ekonomi, eğlence, ticket ve çekilişleri tek botta toplayan Türkçe Discord botu. 💧\n\n" + KV([(e("tag")+"Sürüm", "v" + BOT_VERSION), (e("genel")+"Sunucu", len(bot.guilds)),
           (e("dot")+"Kullanıcı", sum(g.member_count or 0 for g in bot.guilds)), (e("gear")+"Komut", len(bot.commands)), (e("alarm")+"Çalışma süresi", up), (e("bolt")+"Ping", str(round(bot.latency * 1000)) + " ms"),
           (e("robot")+"Altyapı", "discord.py " + discord.__version__ + " • Python " + ".".join(str(x) for x in sys.version_info[:3])), (e("spark")+"V2 kart", "Açık" if V2_OK else "Kapalı")]))
    rows = [_row(mkbtn("Destek Sunucusu", url=SUPPORT_URL, emoji=e("link")), mkbtn("Botu Ekle", url=inv, emoji="➕"))] if V2_OK else []
    await send_thumb(ctx, txt, bot.user.display_avatar.url, accent=0x5865F2, rows=rows)
@kategori("genel")
@bot.command(name="ipucu", aliases=["tip", "öneri"], help="Rastgele ipucu")
async def ipucu(ctx):
    await rp(ctx, head("spark", "RASTGELE İPUCU") + "\n\n" + random.choice(HELP_TIPS) + tip("Daha fazlası için `k!yardım` yaz."))
SARIL = ["sana kocaman bir sarılma gönderdi! 🤗", "seni sımsıkı sardı! 💞", "sıcacık bir sarılmayla gününü güzelleştirdi! ☀️", "sana ayı gibi sarıldı! 🧸"]
@kategori("fun")
@bot.command(name="sarıl", aliases=["hug", "sarilma"], help="<@üye> — sarılma gönder")
@commands.cooldown(1, 5, commands.BucketType.user)
async def saril(ctx, u: discord.Member):
    if u.id == ctx.author.id: return await rp(ctx, WN("KENDİNE SARILMAK", "Kendine sarılmak biraz zor... İstersen ben sarılayım! 🤗"))
    if u.bot: return await rp(ctx, OK("BOT SARILMASI", "Teşekkürler, çok naziksin ama ben sadece kodum! 💧🤖"))
    await rp(ctx, head("heart", "SARILMA!") + "\n\n" + ctx.author.mention + ", " + u.mention + " " + random.choice(SARIL))

# ═══════════════════════════════════════════════════════════════════
# 🚀 BAŞLAT
# ═══════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    bot.run(BOT_TOKEN
