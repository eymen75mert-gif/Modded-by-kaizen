# ═══════════════════════════════════════════════════════════════════════════
#  💧 KATRE BOT v3.5.2 — TEK DOSYA • OYLAMA FIX • GÜZEL AFK • BULUT AYARLAR
#  ─ ENV: BOT_TOKEN, OWNER_ID, SUPPORT_URL, BACKUP_CHANNEL_ID
#  ─ pip install -U discord.py
# ═══════════════════════════════════════════════════════════════════════════
import discord
from discord.ext import commands, tasks
from discord.ui import View, Button, Select, Modal, TextInput
import sqlite3, os, sys, json, random, asyncio, datetime, traceback, textwrap, io, re
from collections import deque
from contextlib import redirect_stdout

BOT_TOKEN   = os.getenv("BOT_TOKEN", "BURAYA_TOKEN")
OWNER_ID    = int(os.getenv("OWNER_ID", "0"))
SUPPORT_URL = os.getenv("SUPPORT_URL", "https://discord.gg/katre")
DB_PATH     = os.getenv("DB_PATH", "katre.db")
BACKUP_CH   = int(os.getenv("BACKUP_CHANNEL_ID", "0"))
MARKER      = "#KATRE_YEDEK"
DIV = "──────────────────────────────"

BOT_VERSION = "3.5.2"
CHANGELOG = {
 "3.5.2": ["🗳️ Oylama düzeltildi (hata olursa sebebi görünür, butonlar garantili)",
           "😴 AFK güzelleştirildi: sebep paneli, mention sayacı, dönüş özeti",
           "☁️ AYARLAR BULUTTA: hoşgeldin, ceza sistemi, koruma, otocevap, sayaç,",
           "    seviye rol, log, badword, tempvoice → restart/redeploy sonrası aynen kalır"],
 "3.5.1": ["🗳️ Butonlu oylama (tek oy, değiştirilemez)"],
}

# ═══════════════════════════════════════════════════════════════════════════
# 🗄️ DB
# ═══════════════════════════════════════════════════════════════════════════
class DB:
    def __init__(self, path):
        self.conn = sqlite3.connect(path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        c = self.conn.cursor()
        c.executescript("""
        CREATE TABLE IF NOT EXISTS servers(guild_id INTEGER PRIMARY KEY, prefix TEXT DEFAULT 'k!',
            welcome_ch INTEGER, auto_role INTEGER, rank_on INTEGER DEFAULT 1, joined_at TEXT);
        CREATE TABLE IF NOT EXISTS users(user_id INTEGER PRIMARY KEY, name TEXT, xp INTEGER DEFAULT 0,
            level INTEGER DEFAULT 1, coins INTEGER DEFAULT 0, messages INTEGER DEFAULT 0,
            warnings INTEGER DEFAULT 0, pro INTEGER DEFAULT 0, pro_expiry TEXT, pro_color TEXT,
            pro_tag TEXT, xp2 INTEGER DEFAULT 0, birthday TEXT, notes TEXT DEFAULT '[]', rep INTEGER DEFAULT 0);
        CREATE TABLE IF NOT EXISTS owner_settings(id INTEGER PRIMARY KEY DEFAULT 1, maintenance INTEGER DEFAULT 0);
        CREATE TABLE IF NOT EXISTS bot_meta(key TEXT PRIMARY KEY, value TEXT);
        CREATE TABLE IF NOT EXISTS half_owners(user_id INTEGER PRIMARY KEY, since TEXT, added_by INTEGER);
        CREATE TABLE IF NOT EXISTS giveaways(message_id INTEGER PRIMARY KEY, guild_id INTEGER, channel_id INTEGER,
            prize TEXT, winners INTEGER, end_time REAL, participants TEXT DEFAULT '[]', status TEXT DEFAULT 'active', host INTEGER);
        CREATE TABLE IF NOT EXISTS tickets(channel_id INTEGER PRIMARY KEY, guild_id INTEGER, user_id INTEGER,
            claimed_by INTEGER, status TEXT DEFAULT 'open');
        CREATE TABLE IF NOT EXISTS role_menus(menu_id TEXT PRIMARY KEY, guild_id INTEGER, role_ids TEXT);
        CREATE TABLE IF NOT EXISTS blacklist(user_id INTEGER PRIMARY KEY, reason TEXT);
        CREATE TABLE IF NOT EXISTS cmd_stats(cmd TEXT PRIMARY KEY, uses INTEGER DEFAULT 0);
        CREATE TABLE IF NOT EXISTS protections(guild_id INTEGER PRIMARY KEY, anti_spam INTEGER DEFAULT 0,
            anti_flood INTEGER DEFAULT 0, anti_raid INTEGER DEFAULT 0, anti_link INTEGER DEFAULT 0,
            badword INTEGER DEFAULT 0, log_ch INTEGER, raid_until REAL DEFAULT 0);
        CREATE TABLE IF NOT EXISTS badwords(guild_id INTEGER, word TEXT, PRIMARY KEY(guild_id, word));
        CREATE TABLE IF NOT EXISTS pro_logs(id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER,
            action TEXT, days INTEGER DEFAULT 0, by_id INTEGER, ts TEXT);
        CREATE TABLE IF NOT EXISTS afk(user_id INTEGER PRIMARY KEY, reason TEXT, since TEXT, mentions INTEGER DEFAULT 0);
        CREATE TABLE IF NOT EXISTS snipe(channel_id INTEGER PRIMARY KEY, author_id INTEGER, content TEXT, attachment TEXT, ts TEXT);
        CREATE TABLE IF NOT EXISTS marriages(id INTEGER PRIMARY KEY AUTOINCREMENT, user1 INTEGER, user2 INTEGER, since TEXT);
        CREATE TABLE IF NOT EXISTS applications(id INTEGER PRIMARY KEY AUTOINCREMENT, guild_id INTEGER, user_id INTEGER,
            message_id INTEGER, status TEXT DEFAULT 'pending', answers TEXT, ts TEXT);
        CREATE TABLE IF NOT EXISTS app_settings(guild_id INTEGER PRIMARY KEY, log_ch INTEGER, staff_role INTEGER);
        CREATE TABLE IF NOT EXISTS auto_replies(guild_id INTEGER, trigger TEXT, response TEXT, PRIMARY KEY(guild_id, trigger));
        CREATE TABLE IF NOT EXISTS counters(guild_id INTEGER PRIMARY KEY, target INTEGER, channel_id INTEGER, reached INTEGER DEFAULT 0);
        CREATE TABLE IF NOT EXISTS level_roles(id INTEGER PRIMARY KEY AUTOINCREMENT, guild_id INTEGER, level INTEGER, role_id INTEGER);
        CREATE TABLE IF NOT EXISTS guild_logs(guild_id INTEGER PRIMARY KEY, channel_id INTEGER);
        CREATE TABLE IF NOT EXISTS emojis(slot TEXT PRIMARY KEY, emoji TEXT);
        CREATE TABLE IF NOT EXISTS tempvoice(guild_id INTEGER PRIMARY KEY, trigger_ch INTEGER, category_id INTEGER);
        CREATE TABLE IF NOT EXISTS temp_channels(channel_id INTEGER PRIMARY KEY, owner_id INTEGER, guild_id INTEGER);
        CREATE TABLE IF NOT EXISTS punishments(id INTEGER PRIMARY KEY AUTOINCREMENT, guild_id INTEGER, user_id INTEGER,
            type TEXT, reason TEXT, by_id INTEGER, ts TEXT, duration INTEGER);
        CREATE TABLE IF NOT EXISTS punish_config(guild_id INTEGER PRIMARY KEY, mute_at INTEGER DEFAULT 3, ban_at INTEGER DEFAULT 5);
        CREATE TABLE IF NOT EXISTS polls(id INTEGER PRIMARY KEY AUTOINCREMENT, guild_id INTEGER, channel_id INTEGER,
            message_id INTEGER DEFAULT 0, question TEXT, options TEXT, votes TEXT DEFAULT '{}',
            status TEXT DEFAULT 'active', creator INTEGER, ts TEXT);
        INSERT OR IGNORE INTO owner_settings(id) VALUES (1);
        """)
        for tbl, col, typ in (("users","pro_tag","TEXT"),("users","xp2","INTEGER DEFAULT 0"),("tickets","claimed_by","INTEGER"),("afk","mentions","INTEGER DEFAULT 0")):
            try: c.execute("ALTER TABLE " + tbl + " ADD COLUMN " + col + " " + typ)
            except sqlite3.OperationalError: pass
        self.conn.commit()
    def q(self, sql, p=()):
        c = self.conn.cursor(); c.execute(sql, p); self.conn.commit(); return c
    def one(self, sql, p=()):
        r = self.q(sql, p).fetchone(); return dict(r) if r else None
    def all(self, sql, p=()):
        return [dict(r) for r in self.q(sql, p).fetchall()]

db = DB(DB_PATH)
def ensure_user(u, n): db.q("INSERT OR IGNORE INTO users(user_id,name) VALUES(?,?)", (u, n))
def ensure_server(g): db.q("INSERT OR IGNORE INTO servers(guild_id) VALUES(?)", (g,))
def pro_log(u, a, d=0, b=0):
    db.q("INSERT INTO pro_logs(user_id,action,days,by_id,ts) VALUES(?,?,?,?,?)", (u, a, d, b, datetime.datetime.now().isoformat()))
def punish_log(gid, uid, typ, reason, by, dur=None):
    db.q("INSERT INTO punishments(guild_id,user_id,type,reason,by_id,ts,duration) VALUES(?,?,?,?,?,?,?)",
         (gid, uid, typ, reason, by, datetime.datetime.now().isoformat(), dur))
def is_half_owner(uid): return db.one("SELECT 1 FROM half_owners WHERE user_id=?", (uid,)) is not None
def is_maintenance():
    r = db.one("SELECT maintenance FROM owner_settings WHERE id=1")
    return bool(r and r["maintenance"])

async def guild_log_send(guild, text):
    r = db.one("SELECT channel_id FROM guild_logs WHERE guild_id=?", (guild.id,))
    if r and r["channel_id"]:
        ch = guild.get_channel(r["channel_id"])
        if ch:
            try: await ch.send(text); return True
            except Exception: pass
    return False

def mod_guard(ctx, t, verb):
    if t.id == ctx.author.id: return "Kendini " + verb + " edemezsin!"
    if t.id == OWNER_ID: return "Bot sahibine işlem yapamazsın!"
    if is_half_owner(t.id): return "Half Owner'a işlem yapamazsın!"
    if t.id == ctx.bot.user.id: return "Bota işlem yapamazsın!"
    if t.id == ctx.guild.owner_id: return "Sunucu sahibine işlem yapamazsın!"
    if ctx.author.top_role <= t.top_role: return "Aynı/üst yetkiliye işlem yapamazsın!"
    return None

# ═══════════════════════════════════════════════════════════════════════════
# 🎭 EMOJİ SLOTLARI + OTO
# ═══════════════════════════════════════════════════════════════════════════
SLOTS = {"logo":"💧","check":"✅","cross":"❌","warn":"⚠️","info":"ℹ️","dot":"•","arrow":"»","star":"🌟","spark":"✨",
"crown":"👑","diamond":"💎","coin":"🪙","money":"💰","gift":"🎁","party":"🎉","shield":"🛡️","hammer":"🔨","kick":"👢",
"lock":"🔒","unlock":"🔓","gear":"⚙️","chart":"📊","chartup":"📈","heart":"❤️","broken":"💔","ring":"💍","game":"🎮",
"dice":"🎲","slot":"🎰","fish":"🎣","pick":"⛏️","ticket":"🎫","clip":"📋","pen":"📝","cam":"📸","sleep":"😴","wave":"👋",
"cake":"🎂","alarm":"⏰","fire":"🔥","bolt":"⚡","mic":"🎙️","palette":"🎨","tag":"🏷️","robot":"🤖","target":"🎯","log":"📜",
"search":"🔍","time":"⏳","home":"🏠","trash":"🗑️","link":"🔗","genel":"🌐","mod":"🛡️","sys":"📋","eco":"💰","fun":"🎮",
"give":"🎉","pro":"💎","owner":"👑"}
EMO_MAP = {"check":["check","tick","tik","onay","yes","success"],"cross":["cross","carp","iptal","hata","error","cancel"],
"warn":["warn","uyari","alert"],"info":["info","bilgi"],"star":["star","yildiz"],"spark":["spark","parlak","shine"],
"crown":["crown","tac","king"],"diamond":["diamond","elmas","gem"],"coin":["coin","para","money","altin"],
"gift":["gift","hediye"],"party":["party","parti","tada","confetti"],"shield":["shield","kalkan","guard","koruma"],
"hammer":["hammer","cekic","ban"],"kick":["kick","boot"],"lock":["lock","kilit"],"gear":["gear","ayar","settings","cark"],
"chart":["chart","grafik","stats"],"chartup":["chartup","yukselis","level"],"heart":["heart","kalp","love"],
"ring":["ring","yuzuk"],"game":["game","oyun"],"dice":["dice","zar"],"slot":["slot","casino"],"fish":["fish","balik"],
"pick":["pick","kazma","mine"],"ticket":["ticket","bilet"],"clip":["clip","pano","basvuru"],"pen":["pen","kalem"],
"cam":["cam","kamera"],"sleep":["sleep","afk","uyku"],"wave":["wave","el","hello"],"cake":["cake","kek","dogum"],
"alarm":["alarm","saat","clock"],"fire":["fire","ates","flame"],"bolt":["bolt","simsek","zap","boost"],
"mic":["mic","mikrofon","ses","voice"],"palette":["palette","palet","renk","color"],"tag":["tag","rozet","badge"],
"robot":["robot","bot"],"target":["target","hedef","sayac"],"log":["log","kayit"],"search":["search","ara"],
"time":["time","sure","hourglass"],"home":["home","ana"],"trash":["trash","cop","sil"],"link":["link","baglanti"]}
SLOT_TR = {"logo":"Bot logosu","check":"Başarı/onay","cross":"Hata/red","warn":"Uyarı","info":"Bilgi","dot":"Nokta",
"arrow":"Liste oku","star":"Başlık","spark":"Parıltı","crown":"Taç","diamond":"Pro","coin":"Coin","money":"Para",
"gift":"Hediye","party":"Kutlama","shield":"Moderasyon","hammer":"Ban","kick":"Atma","lock":"Kilit","unlock":"Kilit aç",
"gear":"Ayar","chart":"İstatistik","chartup":"Seviye","heart":"Aşk","broken":"Boşanma","ring":"Evlilik","game":"Eğlence",
"dice":"Zar","slot":"Slot","fish":"Balık","pick":"Maden","ticket":"Destek","clip":"Başvuru","pen":"Not","cam":"Snipe",
"sleep":"AFK","wave":"Hoşgeldin","cake":"Doğum günü","alarm":"Hatırlatıcı","fire":"Top","bolt":"Boost","mic":"Ses odası",
"palette":"Renk","tag":"Rozet","robot":"Oto cevap","target":"Sayaç","log":"Log","search":"Arama","time":"Süre",
"home":"Ana menü","trash":"Kapat","link":"Link","genel":"Kategori Genel","mod":"Kategori Mod","sys":"Kategori Sistem",
"eco":"Kategori Ekonomi","fun":"Kategori Eğlence","give":"Kategori Çekiliş","pro":"Kategori Pro","owner":"Kategori Owner"}
EMO_CACHE = {}
def refresh_emojis():
    global EMO_CACHE
    EMO_CACHE = {r["slot"]: r["emoji"] for r in db.all("SELECT * FROM emojis")}
def e(s): return EMO_CACHE.get(s, SLOTS.get(s, "•"))
refresh_emojis()
def auto_map_emojis(guild):
    mapped = {}
    for emj in guild.emojis:
        nm = emj.name.lower()
        for slot, keys in EMO_MAP.items():
            if slot in mapped: continue
            if any(k in nm for k in keys): mapped[slot] = str(emj)
    for slot, val in mapped.items():
        db.q("INSERT OR REPLACE INTO emojis(slot,emoji) VALUES(?,?)", (slot, val))
    if mapped: refresh_emojis()
    return mapped

# ═══════════════════════════════════════════════════════════════════════════
# ☁️ BULUT YEDEK (EMOJİ + PRO + ✅ AYARLAR)
# ═══════════════════════════════════════════════════════════════════════════
_HASH = {"emoji": None, "pro": None, "set": None}
SET_TABLES = ["servers","punish_config","protections","app_settings","counters",
              "level_roles","guild_logs","auto_replies","badwords","tempvoice"]
def pro_snapshot():
    return {"pros": db.all("SELECT user_id,pro_expiry,pro_color,pro_tag,xp2 FROM users WHERE pro=1"),
            "logs": db.all("SELECT user_id,action,days,by_id,ts FROM pro_logs ORDER BY id")}
def settings_snapshot():
    return {t: db.all("SELECT * FROM " + t) for t in SET_TABLES}
def emoji_restore(data):
    for k, v in data.items():
        db.q("INSERT OR REPLACE INTO emojis(slot,emoji) VALUES(?,?)", (k, v))
    refresh_emojis(); return len(data)
def pro_restore(data):
    n = 0
    for p in data.get("pros", []):
        db.q("INSERT INTO users(user_id) VALUES(?) ON CONFLICT(user_id) DO UPDATE SET pro=1, pro_expiry=?, pro_color=?, pro_tag=?, xp2=?",
             (p["user_id"], p["pro_expiry"], p["pro_color"], p["pro_tag"], p["xp2"]))
        n += 1
    if not db.all("SELECT 1 FROM pro_logs"):
        for l in data.get("logs", []):
            db.q("INSERT INTO pro_logs(user_id,action,days,by_id,ts) VALUES(?,?,?,?,?)",
                 (l["user_id"], l["action"], l["days"], l["by_id"], l["ts"]))
    return n
def settings_restore(data):
    n = 0
    for t, rows in data.items():
        if t not in SET_TABLES: continue
        for r in rows:
            cols = ", ".join(r.keys()); ph = ", ".join("?" * len(r))
            try:
                db.q("INSERT OR REPLACE INTO " + t + " (" + cols + ") VALUES (" + ph + ")", tuple(r.values()))
                n += 1
            except Exception: pass
    return n
async def push_backup(bot, kind, data):
    if not BACKUP_CH: return False
    try:
        ch = bot.get_channel(BACKUP_CH) or await bot.fetch_channel(BACKUP_CH)
        raw = json.dumps(data, separators=(",", ":"), default=str)
        gen = str(int(datetime.datetime.now().timestamp()))
        chunks = [raw[i:i+1800] for i in range(0, len(raw), 1800)] or ["{}"]
        async for m in ch.history(limit=400):
            if m.author.id == bot.user.id and m.content.startswith(MARKER + " " + kind):
                try: await m.delete()
                except Exception: pass
        for i, c in enumerate(chunks):
            await ch.send(MARKER + " " + kind + " g" + gen + " [" + str(i) + "/" + str(len(chunks)) + "]\n" + c)
        return True
    except Exception:
        traceback.print_exc(); return False
async def pull_backup(bot, kind):
    if not BACKUP_CH: return None
    try:
        ch = bot.get_channel(BACKUP_CH) or await bot.fetch_channel(BACKUP_CH)
        gens = {}
        async for m in ch.history(limit=400):
            if m.author.id == bot.user.id and m.content.startswith(MARKER + " " + kind):
                try:
                    head, body = m.content.split("\n", 1)
                    tk = head.split()
                    g = tk[2][1:]; i, n = tk[3][1:-1].split("/")
                    gens.setdefault(g, {"n": int(n), "p": {}})["p"][int(i)] = body
                except Exception: pass
        if not gens: return None
        g = max(gens.keys()); rec = gens[g]
        if len(rec["p"]) != rec["n"]: return None
        return json.loads("".join(rec["p"][i] for i in range(rec["n"])))
    except Exception:
        traceback.print_exc(); return None

# ═══════════════════════════════════════════════════════════════════════════
# ✍️ MARKDOWN UI + GÜNCELLEME
# ═══════════════════════════════════════════════════════════════════════════
def head(icon, title): return e(icon) + " **" + title + "**\n" + DIV
def OK(t, b=None): return head("check", t) + ("\n" + b if b else "")
def ER(t, b=None): return head("cross", t) + ("\n" + b if b else "")
def WN(t, b=None): return head("warn", t) + ("\n" + b if b else "")
def KV(pairs): return "\n".join("> " + k + " › **" + str(v) + "**" for k, v in pairs)
def bar(pct, ln=14):
    pct = max(0, min(100, int(pct))); f = round(pct / 100 * ln)
    return "`[" + "█" * f + "░" * (ln - f) + "] %" + str(pct) + "`"
async def rp(ctx, text, view=None):
    try: return await ctx.send(text, view=view)
    except Exception:
        try: return await ctx.author.send(text, view=view)
        except Exception: return None
def parse_sure(t):
    t = str(t).lower().strip()
    for s, m in {"m":1,"dk":1,"h":60,"s":60,"d":1440,"g":1440,"w":10080}.items():
        if t.endswith(s): return int(float(t[:-len(s)]) * m)
    return int(float(t))
def fancy(t):
    o = []
    for ch in t:
        c = ord(ch)
        if 97 <= c <= 122: o.append(chr(c - 97 + 0xFF41))
        elif 65 <= c <= 90: o.append(chr(c - 65 + 0xFF21))
        elif 48 <= c <= 57: o.append(chr(c - 48 + 0xFF10))
        else: o.append(ch)
    return "".join(o)
def sure_txt(dk):
    if dk >= 1440: return str(dk // 1440) + " gün " + str((dk % 1440) // 60) + " saat"
    if dk >= 60: return str(dk // 60) + " saat " + str(dk % 60) + " dakika"
    return str(dk) + " dakika"

async def check_update(bot):
    try:
        row = db.one("SELECT value FROM bot_meta WHERE key='update_ch'")
        ch_id = int(row["value"]) if row else int(os.getenv("UPDATE_CHANNEL_ID", "0") or 0)
        if not ch_id: return
        ch = bot.get_channel(ch_id) or await bot.fetch_channel(ch_id)
        last = db.one("SELECT value FROM bot_meta WHERE key='version'")
        last_v = last["value"] if last else None
        if last_v == BOT_VERSION: return
        L = [e("party") + " **KATRE BOT GÜNCELLENDİ!**", DIV,
             e("spark") + " Yeni sürüm: **v" + BOT_VERSION + "**" + (("   (önceki: v" + last_v + ")") if last_v else ""),
             e("time") + " Tarih: <t:" + str(int(datetime.datetime.now().timestamp())) + ":F>", ""]
        notes = CHANGELOG.get(BOT_VERSION, [])
        if notes:
            L.append(e("star") + " **BU SÜRÜMDE GELENLER:**")
            L += [e("arrow") + " " + n for n in notes]
        L += ["", e("logo") + " Katre Bot • `k!yardım`"]
        await ch.send("\n".join(L))
        db.q("INSERT OR REPLACE INTO bot_meta(key,value) VALUES('version',?)", (BOT_VERSION,))
    except Exception:
        traceback.print_exc()

class OwnerOnly(commands.CheckFailure): pass
class ProOnly(commands.CheckFailure): pass
def is_owner():
    async def p(ctx):
        if ctx.author.id != OWNER_ID: raise OwnerOnly()
        return True
    return commands.check(p)
def is_half():
    async def p(ctx):
        if ctx.author.id == OWNER_ID: return True
        if is_half_owner(ctx.author.id): return True
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

CATS = {"genel":("genel","Genel & Sistem"),"mod":("mod","Moderasyon & Koruma"),"sys":("sys","Başvuru & Otomasyon"),
"eco":("eco","Ekonomi"),"fun":("fun","Eğlence"),"give":("give","Çekiliş"),"pro":("pro","Pro"),"owner":("owner","Owner")}
CAT_DESC = {"genel":"Rank, profil, avatar, snipe, AFK, oda ve genel araçlar","mod":"Ban, kick, unban, mute, uyarı, oto-ceza, koruma",
"sys":"Başvuru, ticket, temp voice, oto-cevap, sayaç, log","eco":"Coin, günlük, çalışma, balık, maden, market",
"fun":"Quiz, slot, aşk, butonlu anket ve oyunlar","give":"Butonlu çekiliş, reroll ve sonuç paneli",
"pro":"Pro üyelere özel oda, renk, tag, boost","owner":"Owner + Half Owner yönetim paneli"}
def cat_count(b, k): return len([c for c in b.commands if getattr(c, "kategori", None) == k])
def help_content(bot):
    L = [e("logo") + " **" + bot.user.name.upper() + " YARDIM MENÜSÜ**", DIV,
         "Selam, ben **" + bot.user.name + "!** " + e("spark"),
         "Toplam **" + str(len(bot.commands)) + "** komutum var; hepsi `k!komut` şeklinde çalışır.",
         "Büyük/küçük prefix fark etmez: `K!` da geçerli.", "",
         "Aşağıdaki menüden bir kategori seç.", "", e("star") + " **Kategoriler**", ""]
    for k in CATS:
        L += [e("arrow") + " " + e(k) + " **" + CATS[k][1] + "**  `" + str(cat_count(bot, k)) + "` komut", CAT_DESC[k], ""]
    L.append(e("link") + " Destek: " + SUPPORT_URL)
    return "\n".join(L)
def cat_content(bot, key):
    cmds = sorted([c for c in bot.commands if getattr(c, "kategori", None) == key], key=lambda x: x.name)
    base = [e(key) + " **" + CATS[key][1].upper() + "** (" + str(len(cmds)) + " komut)", DIV, ""]
    body = "\n".join(base + [e("arrow") + " `k!" + c.name + "` ─ " + (c.help or "") for c in cmds])
    if len(body) > 1900:  # ✅ 2000 limitine takılmasın → kompakt liste
        body = "\n".join(base + ["`k!" + c.name + "`" for c in cmds])
        body += "\n\n" + e("info") + " Detay için: `k!komutbilgi <komut>`"
    body += "\n\n" + e("info") + " Ana menü için butonu kullan."
    return body

@kategori("genel")
@bot.command(name="komutbilgi", aliases=["cmd"], help="<komut adı> — Komut detayı")
async def komutbilgi(ctx, *, name: str):
    c = bot.get_command(name.lower().replace("k!", ""))
    if not c: return await rp(ctx, ER("BULUNAMADI", "Örnek: `k!komutbilgi mute`"))
    await rp(ctx, head("info", "k!" + c.name) + "\n" + (c.help or "—") +
             "\n" + e("dot") + " Kullanım: `k!" + c.name + (" " + c.signature if c.signature else "") + "`")
             # ← 352. satır


# ═══════════════════════════════════════════════════════════════════════════
# 🔘 VIEW'LAR (🛡️ KALICI)
# ═══════════════════════════════════════════════════════════════════════════
class HelpSelect(Select):
    def __init__(self, bot):
        super().__init__(placeholder="Kategori seç...", min_values=1, max_values=1, row=0, custom_id="kh_sel",
                         options=[discord.SelectOption(label=CATS[k][1], value=k, emoji=SLOTS.get(k, "•"),
                                 description=CAT_DESC[k][:60]) for k in CATS])
        self.bot = bot
    async def callback(self, it):
        if self.values[0] == "owner" and it.user.id != OWNER_ID and not is_half_owner(it.user.id):
            return await it.response.send_message(ER("YETKİ YOK", "Owner paneli sadece sahibine açık."), ephemeral=True)
        await it.response.edit_message(content=cat_content(self.bot, self.values[0]), view=self.view)
class HelpView(View):
    def __init__(self, bot):
        super().__init__(timeout=None); self.bot = bot
        self.add_item(HelpSelect(bot))
    @discord.ui.button(label="Ana Menü", style=discord.ButtonStyle.success, emoji="❓", row=1, custom_id="kh_home")
    async def home(self, it, b): await it.response.edit_message(content=help_content(self.bot), view=self)
    @discord.ui.button(label="İstatistik", style=discord.ButtonStyle.secondary, emoji="📊", row=1, custom_id="kh_stats")
    async def stats(self, it, b):
        up = str(datetime.datetime.now() - self.bot.start_time).split(".")[0]
        await it.response.send_message(head("chart", "İSTATİSTİK") + "\n" + KV([
            ("Sunucu", len(self.bot.guilds)), ("Kullanıcı", sum(g.member_count or 0 for g in self.bot.guilds)),
            ("Komut", len(self.bot.commands)), ("Uptime", up), ("Ping", str(round(self.bot.latency*1000))+"ms")]), ephemeral=True)
    @discord.ui.button(label="Kapat", style=discord.ButtonStyle.danger, emoji="🗑️", row=1, custom_id="kh_close")
    async def close(self, it, b): await it.message.delete()
    def links(self):
        self.add_item(Button(label="Destek Sunucusu", url=SUPPORT_URL, style=discord.ButtonStyle.link, emoji="🔗", row=2))
        return self

class ConfirmView(View):
    def __init__(self, t=30):
        super().__init__(timeout=t); self.value = None
    @discord.ui.button(label="Onayla", style=discord.ButtonStyle.success, emoji="✅")
    async def y(self, it, b):
        self.value = True; self.stop()
        await it.response.edit_message(content=WN("İŞLENİYOR...", "Lütfen bekle."), view=None)
    @discord.ui.button(label="Vazgeç", style=discord.ButtonStyle.secondary, emoji="❌")
    async def n(self, it, b):
        self.value = False; self.stop()
        await it.response.edit_message(content=ER("İPTAL", "İşlem iptal edildi."), view=None)
class SetupConfirmView(View):
    def __init__(self):
        super().__init__(timeout=60); self.value = None
    @discord.ui.button(label="Kurulumu Başlat", style=discord.ButtonStyle.success, emoji="🏗️")
    async def y(self, it, b):
        self.value = True; self.stop()
        await it.response.edit_message(content=WN("KURULUM", "Sunucu kuruluyor... (≈10 sn)"), view=None)
    @discord.ui.button(label="Vazgeç", style=discord.ButtonStyle.secondary, emoji="❌")
    async def n(self, it, b):
        self.value = False; self.stop()
        await it.response.edit_message(content=ER("İPTAL"), view=None)

class OwnerPanelView(View):
    def __init__(self, bot):
        super().__init__(timeout=None); self.bot = bot
    async def g(self, it):
        if it.user.id != OWNER_ID:
            await it.response.send_message(ER("YETKİ YOK"), ephemeral=True); return False
        return True
    @discord.ui.button(label="Bakım Modu", style=discord.ButtonStyle.secondary, emoji="🔧", custom_id="op_bak")
    async def bk(self, it, b):
        if not await self.g(it): return
        cur = db.one("SELECT maintenance FROM owner_settings WHERE id=1")["maintenance"]
        db.q("UPDATE owner_settings SET maintenance=? WHERE id=1", (0 if cur else 1,))
        await it.response.send_message(head("gear", "BAKIM MODU") + "\n**" + ("AÇIK — kullanıcılar BAKIMDAYIZ mesajı görür" if not cur else "KAPALI — herkese açık") + "**", ephemeral=True)
    @discord.ui.button(label="İstatistik", style=discord.ButtonStyle.success, emoji="📊", custom_id="op_stats")
    async def st(self, it, b):
        if not await self.g(it): return
        await it.response.send_message(head("chart", "OWNER İSTATİSTİK") + "\n" + KV([
            ("Sunucu", len(self.bot.guilds)), ("Kullanıcı", sum(g.member_count or 0 for g in self.bot.guilds)),
            ("Komut kullanımı", db.one("SELECT SUM(uses) u FROM cmd_stats")["u"] or 0),
            ("Pro üye", len(db.all("SELECT 1 FROM users WHERE pro=1"))),
            ("Half Owner", len(db.all("SELECT 1 FROM half_owners"))),
            ("Bakım", "AÇIK" if is_maintenance() else "KAPALI")]), ephemeral=True)
    @discord.ui.button(label="Sunucular", style=discord.ButtonStyle.primary, emoji="🖥️", custom_id="op_guilds")
    async def gl(self, it, b):
        if not await self.g(it): return
        L = [head("owner", "SUNUCULAR (" + str(len(self.bot.guilds)) + ")")]
        for i, g in enumerate(sorted(self.bot.guilds, key=lambda x: -(x.member_count or 0))[:10], 1):
            L.append(e("arrow") + " **" + g.name + "** ─ " + str(g.member_count) + " üye")
        await it.response.send_message("\n".join(L), ephemeral=True)
    @discord.ui.button(label="Duyuru", style=discord.ButtonStyle.primary, emoji="📢", custom_id="op_duy")
    async def dy(self, it, b):
        if not await self.g(it): return
        await it.response.send_modal(BroadcastModal())
    @discord.ui.button(label="Kapat", style=discord.ButtonStyle.danger, emoji="🗑️", custom_id="op_close")
    async def cl(self, it, b):
        if not await self.g(it): return
        await it.message.delete()
class BroadcastModal(Modal, title="Genel Duyuru"):
    txt = TextInput(label="Duyuru metni", style=discord.TextStyle.paragraph)
    async def on_submit(self, it):
        ok = 0
        for g in it.client.guilds:
            ch = g.system_channel or next((c for c in g.text_channels if c.permissions_for(g.me).send_messages), None)
            if ch:
                try: await ch.send(head("owner", "DUYURU") + "\n" + self.txt.value); ok += 1
                except Exception: pass
        await it.response.send_message(OK("DUYURU", str(ok) + "/" + str(len(it.client.guilds)) + " sunucuya iletildi."), ephemeral=True)

def gw_start_text(gw):
    return (e("give") + " **Çekiliş: " + gw["prize"] + "**\n" + DIV + "\n" +
            KV([(e("star")+" Kazanan", str(gw["winners"]) + " kişi"), (e("dot")+" Katılım", "0 kişi"),
                (e("time")+" Bitiş", "<t:" + str(int(gw["end_time"])) + ":R>"), (e("dot")+" Düzenleyen", "<@" + str(gw["host"]) + ">")]) +
            "\n\nKatılmak için aşağıdaki butona bas!")
def gw_end_text(gw, men, parts):
    return (e("star") + " **" + gw["prize"] + "**\n" + DIV + "\n**ÇEKİLİŞ BİTTİ**\n\n" +
            KV([(e("star")+" Kazanan", men), (e("dot")+" Katılım", str(len(parts)) + " kişi"),
                (e("dot")+" Düzenleyen", "<@" + str(gw["host"]) + ">"),
                (e("alarm")+" Bitti", "<t:" + str(int(datetime.datetime.now().timestamp())) + ":F>")]) +
            "\n\nKazananlar aşağıdaki duyuruda etiketlendi.")
class GiveawayView(View):
    def __init__(self, bot):
        super().__init__(timeout=None); self.bot = bot
    @discord.ui.button(label="Katıl", style=discord.ButtonStyle.success, emoji="🎉", custom_id="kg_join", row=0)
    async def join(self, it, b):
        gw = db.one("SELECT * FROM giveaways WHERE message_id=?", (it.message.id,))
        if not gw or gw["status"] != "active": return await it.response.send_message(ER("AKTİF DEĞİL"), ephemeral=True)
        p = json.loads(gw["participants"])
        if str(it.user.id) in p: return await it.response.send_message(WN("ZATEN KATILDIN"), ephemeral=True)
        p.append(str(it.user.id))
        db.q("UPDATE giveaways SET participants=? WHERE message_id=?", (json.dumps(p), it.message.id))
        t = gw_start_text(dict(gw, participants=json.dumps(p)))
        t = t.replace("> " + e("dot") + " Katılım: **0 kişi**", "> " + e("dot") + " Katılım: **" + str(len(p)) + " kişi**")
        try: await it.message.edit(content=t, view=self)
        except Exception: pass
        await it.response.send_message(OK("KATILDIN", "**" + gw["prize"] + "** çekilişindesin!"), ephemeral=True)
    @discord.ui.button(label="Ayrıl", style=discord.ButtonStyle.secondary, emoji="🚪", custom_id="kg_leave", row=0)
    async def leave(self, it, b):
        gw = db.one("SELECT * FROM giveaways WHERE message_id=?", (it.message.id,))
        if not gw or gw["status"] != "active": return await it.response.send_message(ER("AKTİF DEĞİL"), ephemeral=True)
        p = json.loads(gw["participants"])
        if str(it.user.id) not in p: return await it.response.send_message(WN("KATILMAMIŞSIN"), ephemeral=True)
        p.remove(str(it.user.id))
        db.q("UPDATE giveaways SET participants=? WHERE message_id=?", (json.dumps(p), it.message.id))
        await it.response.send_message(WN("AYRILDIN"), ephemeral=True)
    @discord.ui.button(label="Bitir", style=discord.ButtonStyle.primary, emoji="🏁", custom_id="kg_end", row=1)
    async def end(self, it, b):
        if not it.user.guild_permissions.administrator: return await it.response.send_message(ER("YETKİ YOK"), ephemeral=True)
        await finalize_giveaway(self.bot, it.message.id)
        await it.response.send_message(OK("BİTİRİLDİ"), ephemeral=True)
    @discord.ui.button(label="Yeniden Çek", style=discord.ButtonStyle.secondary, emoji="🎲", custom_id="kg_rr", row=1)
    async def rr(self, it, b):
        if not it.user.guild_permissions.administrator: return await it.response.send_message(ER("YETKİ YOK"), ephemeral=True)
        gw = db.one("SELECT * FROM giveaways WHERE message_id=?", (it.message.id,))
        if not gw: return
        p = json.loads(gw["participants"])
        if not p: return await it.response.send_message(ER("KATILIMCI YOK"), ephemeral=True)
        w = self.bot.get_user(int(random.choice(p)))
        await it.channel.send(head("dice", "REROLL") + "\n" + e("star") + " Yeni kazanan: " + (w.mention if w else "?"))
        await it.response.defer()
    @discord.ui.button(label="+1 Saat", style=discord.ButtonStyle.success, emoji="⏳", custom_id="kg_ext", row=1)
    async def ext(self, it, b):
        if not it.user.guild_permissions.administrator: return await it.response.send_message(ER("YETKİ YOK"), ephemeral=True)
        gw = db.one("SELECT * FROM giveaways WHERE message_id=?", (it.message.id,))
        if not gw or gw["status"] != "active": return await it.response.send_message(ER("AKTİF DEĞİL"), ephemeral=True)
        nw = gw["end_time"] + 3600
        db.q("UPDATE giveaways SET end_time=? WHERE message_id=?", (nw, it.message.id))
        await it.response.send_message(OK("UZATILDI", "Yeni bitiş: <t:" + str(int(nw)) + ":R>"), ephemeral=True)
    @discord.ui.button(label="İptal", style=discord.ButtonStyle.danger, emoji="🛑", custom_id="kg_can", row=1)
    async def can(self, it, b):
        if not it.user.guild_permissions.administrator: return await it.response.send_message(ER("YETKİ YOK"), ephemeral=True)
        gw = db.one("SELECT * FROM giveaways WHERE message_id=?", (it.message.id,))
        if not gw: return
        db.q("UPDATE giveaways SET status='cancelled' WHERE message_id=?", (it.message.id,))
        try: await it.message.edit(content=ER("ÇEKİLİŞ İPTAL", gw["prize"]), view=None)
        except Exception: pass
        await it.response.send_message(WN("İPTAL EDİLDİ"), ephemeral=True)
class GwJumpView(View):
    def __init__(self, url):
        super().__init__(timeout=None)
        self.add_item(Button(label="Çekilişe Git", url=url, style=discord.ButtonStyle.link, emoji="🔗"))

# ─────────────── 🗳️ BUTONLU OYLAMA (v3.5.2 — SAĞLAMLAŞTIRILDI) ───────────────
def poll_content(p):
    opts = json.loads(p["options"]); votes = json.loads(p["votes"])
    total = sum(len(v) for v in votes.values())
    L = [e("chart") + " **ANKET: " + p["question"] + "**", DIV]
    if p["status"] != "active":
        L.append(e("lock") + " **ANKET KAPANDI — KESİN SONUÇLAR**")
    L.append("")
    for i, op in enumerate(opts):
        n = len(votes.get(str(i), []))
        pct = (n / total * 100) if total else 0
        L.append(e("arrow") + " **" + op + "** ─ `" + str(n) + "` oy  " + bar(pct, 10))
    L += ["", e("dot") + " Toplam: **" + str(total) + "** oy • " +
          (e("party") + " Katılan herkese teşekkürler!" if p["status"] != "active" else "Butonlara basarak oy ver! (**tek oy — değiştirilemez**)")]
    return "\n".join(L)

async def refresh_poll(client, p):
    ch = client.get_channel(p["channel_id"])
    if not ch: return
    try:
        msg = await ch.fetch_message(p["message_id"])
        view = None if p["status"] != "active" else PollView(p["id"], json.loads(p["options"]))
        await msg.edit(content=poll_content(p), view=view)
    except Exception: pass

class PollView(View):
    def __init__(self, poll_id, options):
        super().__init__(timeout=None)
        self.poll_id = poll_id
        for i, op in enumerate(options[:5]):
            b = Button(label=op[:60], style=discord.ButtonStyle.primary, emoji=e("dot"),
                       custom_id="poll_" + str(poll_id) + "_" + str(i), row=0)
            b.callback = self.make_vote(i)
            self.add_item(b)
        c = Button(label="Anketi Kapat", style=discord.ButtonStyle.danger, emoji=e("lock"),
                   custom_id="pollc_" + str(poll_id), row=1)
        c.callback = self.cb_close
        self.add_item(c)
    def make_vote(self, i):
        async def _vote(it):
            try:
                p = db.one("SELECT * FROM polls WHERE id=?", (self.poll_id,))
                if not p or p["status"] != "active":
                    return await it.response.send_message(ER("ANKET KAPALI", "Bu anket artık oy kabul etmiyor."), ephemeral=True)
                votes = json.loads(p["votes"])
                for lst in votes.values():
                    if str(it.user.id) in lst:
                        return await it.response.send_message(WN("ZATEN OY VERDİN", "Oyun **değiştirilemez**!"), ephemeral=True)
                votes.setdefault(str(i), []).append(str(it.user.id))
                db.q("UPDATE polls SET votes=? WHERE id=?", (json.dumps(votes), self.poll_id))
                await it.response.send_message(OK("OYUN KAYDEDİLDİ", e("arrow") + " **" + json.loads(p["options"])[i] + "**"), ephemeral=True)
                await refresh_poll(it.client, db.one("SELECT * FROM polls WHERE id=?", (self.poll_id,)))
            except Exception as ex:
                traceback.print_exc()
                try: await it.response.send_message(ER("OY HATASI", str(ex)[:200]), ephemeral=True)
                except Exception: pass
        return _vote
    async def cb_close(self, it):
        p = db.one("SELECT * FROM polls WHERE id=?", (self.poll_id,))
        if not p: return
        if not (it.user.id == p["creator"] or (it.guild and it.guild.permissions_for(it.user).administrator)):
            return await it.response.send_message(ER("YETKİ YOK", "Sadece anket sahibi veya yönetici kapatabilir."), ephemeral=True)
        if p["status"] != "active":
            return await it.response.send_message(WN("ZATEN KAPALI"), ephemeral=True)
        db.q("UPDATE polls SET status='closed' WHERE id=?", (self.poll_id,))
        await refresh_poll(it.client, db.one("SELECT * FROM polls WHERE id=?", (self.poll_id,)))
        await it.response.send_message(OK("ANKET KAPATILDI", "Kesin sonuçlar mesajda."), ephemeral=True)

class RoleButton(Button):
    def __init__(self, rid, label, cid, row):
        super().__init__(label=label[:78], style=discord.ButtonStyle.secondary, emoji="🎭", custom_id=cid, row=row)
        self.rid = rid
    async def callback(self, it):
        r = it.guild.get_role(self.rid)
        if not r: return await it.response.send_message(ER("ROL YOK"), ephemeral=True)
        if r in it.user.roles: await it.user.remove_roles(r); m = e("cross") + " **" + r.name + "** alındı."
        else: await it.user.add_roles(r); m = e("check") + " **" + r.name + "** verildi!"
        await it.response.send_message(head("shield", "ROL GÜNCELLENDİ") + "\n" + m, ephemeral=True)
class RoleMenuView(View):
    def __init__(self, mid, roles):
        super().__init__(timeout=None)
        for i, (rid, nm) in enumerate(roles):
            self.add_item(RoleButton(rid, nm, "kr_" + mid + "_" + str(rid), i // 5))

class TicketModal(Modal, title="Destek Talebi"):
    konu = TextInput(label="Konu", max_length=100)
    acik = TextInput(label="Açıklama", style=discord.TextStyle.paragraph)
    async def on_submit(self, it):
        if db.one("SELECT 1 FROM tickets WHERE user_id=? AND status='open'", (it.user.id,)):
            return await it.response.send_message(ER("ZATEN AÇIK TALEBİN VAR"), ephemeral=True)
        g = it.guild
        cat = discord.utils.get(g.categories, name="DESTEK") or await g.create_category("DESTEK")
        ow = {g.default_role: discord.PermissionOverwrite(view_channel=False),
              it.user: discord.PermissionOverwrite(view_channel=True, send_messages=True, attach_files=True),
              g.me: discord.PermissionOverwrite(view_channel=True, send_messages=True, manage_channels=True, manage_messages=True)}
        try:
            ch = await g.create_text_channel("destek-" + it.user.name.lower(), category=cat, overwrites=ow)
        except Exception as ex:
            return await it.response.send_message(ER("KANAL AÇILAMADI", str(ex)[:200]), ephemeral=True)
        db.q("INSERT INTO tickets(channel_id,guild_id,user_id) VALUES(?,?,?)", (ch.id, g.id, it.user.id))
        await ch.send(head("ticket", "DESTEK TALEBİ") + "\n" +
            KV([(e("dot")+" Kullanıcı", it.user.mention), (e("clip")+" Konu", self.konu.value),
                (e("pen")+" Açıklama", self.acik.value[:500]), (e("time")+" Tarih", "<t:" + str(int(datetime.datetime.now().timestamp())) + ":F>")]) +
            "\n\n" + e("info") + " Yetkililer birazdan seninle ilgilenecek.\nKapatmak için: `k!ticket kapat` veya buton.", view=TicketView())
        await it.response.send_message(OK("TALEP OLUŞTURULDU", ch.mention), ephemeral=True)
class TicketOpenView(View):
    def __init__(self): super().__init__(timeout=None)
    @discord.ui.button(label="Destek Talebi Oluştur", style=discord.ButtonStyle.primary, emoji="🎫", custom_id="kt_open", row=0)
    async def o(self, it, b): await it.response.send_modal(TicketModal())
    @discord.ui.button(label="Talebim Var mı?", style=discord.ButtonStyle.secondary, emoji="🔍", custom_id="kt_mine", row=0)
    async def mine(self, it, b):
        t = db.one("SELECT * FROM tickets WHERE user_id=? AND status='open'", (it.user.id,))
        await it.response.send_message((OK("TALEBİN", "<#" + str(t["channel_id"]) + ">") if t else WN("TALEBİN YOK", "Oluşturmak için diğer butona bas.")), ephemeral=True)
class TicketView(View):
    def __init__(self): super().__init__(timeout=None)
    @discord.ui.button(label="Üstlendim", style=discord.ButtonStyle.primary, emoji="👮", custom_id="kt_claim", row=0)
    async def claim(self, it, b):
        if not it.user.guild_permissions.manage_messages: return await it.response.send_message(ER("YETKİ YOK"), ephemeral=True)
        db.q("UPDATE tickets SET claimed_by=? WHERE channel_id=?", (it.user.id, it.channel.id))
        await it.channel.send(head("shield", "TALEP ÜSTLENİLDİ") + "\n" + e("dot") + " Yetkili: " + it.user.mention)
        await it.response.defer()
    @discord.ui.button(label="Talebi Kapat", style=discord.ButtonStyle.danger, emoji="🔒", custom_id="kt_close", row=0)
    async def close(self, it, b):
        t = db.one("SELECT * FROM tickets WHERE channel_id=?", (it.channel.id,))
        if not t: return await it.response.send_message(ER("BULUNAMADI"), ephemeral=True)
        if not (it.user.guild_permissions.administrator or it.user.id == t["user_id"]):
            return await it.response.send_message(ER("YETKİ YOK"), ephemeral=True)
        db.q("UPDATE tickets SET status='closed' WHERE channel_id=?", (it.channel.id,))
        await guild_log_send(it.guild, head("ticket", "TALEP KAPANDI") + "\n" + e("dot") + " Kanal: #" + it.channel.name +
                             "\n" + e("dot") + " Kullanıcı: <@" + str(t["user_id"]) + "> • Kapatan: " + it.user.mention)
        await it.response.send_message(WN("KAPATILIYOR", "Kanal 10 sn içinde silinecek."))
        await asyncio.sleep(10)
        try: await it.channel.delete()
        except Exception: pass

class AppOpenView(View):
    def __init__(self): super().__init__(timeout=None)
    @discord.ui.button(label="Yetkili Başvurusu Yap", style=discord.ButtonStyle.primary, emoji="📋", custom_id="ka_open")
    async def a(self, it, b): await it.response.send_modal(AppModal())
class AppModal(Modal, title="Yetkili Başvurusu"):
    yas = TextInput(label="Yaş", max_length=2)
    den = TextInput(label="Deneyimin", style=discord.TextStyle.paragraph, max_length=500)
    ned = TextInput(label="Neden yetkili olmak istiyorsun?", style=discord.TextStyle.paragraph, max_length=500)
    akt = TextInput(label="Günlük aktif saatlerin", max_length=100)
    async def on_submit(self, it):
        st = db.one("SELECT * FROM app_settings WHERE guild_id=?", (it.guild.id,))
        if not st or not st["log_ch"]:
            return await it.response.send_message(ER("SİSTEM KURULU DEĞİL", "Yönetici: `k!başvuru-ayarla`"), ephemeral=True)
        if db.one("SELECT 1 FROM applications WHERE guild_id=? AND user_id=? AND status='pending'", (it.guild.id, it.user.id)):
            return await it.response.send_message(WN("BEKLEYEN BAŞVURUN VAR"), ephemeral=True)
        cur = db.q("INSERT INTO applications(guild_id,user_id,answers,ts) VALUES(?,?,?,?)",
                   (it.guild.id, it.user.id, json.dumps({"yas":self.yas.value,"den":self.den.value,"ned":self.ned.value,"akt":self.akt.value}),
                    datetime.datetime.now().isoformat()))
        aid = cur.lastrowid
        ch = it.guild.get_channel(st["log_ch"])
        if ch:
            m = await ch.send(head("clip", "YENİ BAŞVURU #" + str(aid)) + "\n" +
                KV([(e("dot")+" Kullanıcı", it.user.mention), (e("cake")+" Yaş", self.yas.value),
                    (e("shield")+" Deneyim", self.den.value[:300]), (e("heart")+" Neden", self.ned.value[:300]),
                    (e("alarm")+" Aktif", self.akt.value[:60])]), view=AppReviewView(aid))
            db.q("UPDATE applications SET message_id=? WHERE id=?", (m.id, aid))
        await it.response.send_message(OK("BAŞVURU ALINDI", "No: **#" + str(aid) + "** • Durum: `k!başvurum`"), ephemeral=True)
class AppReviewView(View):
    def __init__(self, aid):
        super().__init__(timeout=None); self.aid = aid
        b1 = Button(label="Kabul Et", style=discord.ButtonStyle.success, emoji="✅", custom_id="ka_acc_" + str(aid)); b1.callback = self.acc
        b2 = Button(label="Reddet", style=discord.ButtonStyle.danger, emoji="❌", custom_id="ka_rej_" + str(aid)); b2.callback = self.rej
        self.add_item(b1); self.add_item(b2)
    async def yk(self, it):
        ok = it.user.guild_permissions.administrator
        st = db.one("SELECT * FROM app_settings WHERE guild_id=?", (it.guild.id,))
        if st and st["staff_role"]:
            r = it.guild.get_role(st["staff_role"])
            if r and r in it.user.roles: ok = True
        if not ok: await it.response.send_message(ER("YETKİ YOK"), ephemeral=True); return False
        return True
    async def acc(self, it):
        if not await self.yk(it): return
        a = db.one("SELECT * FROM applications WHERE id=?", (self.aid,))
        if not a or a["status"] != "pending": return await it.response.send_message(WN("İŞLENMİŞ"), ephemeral=True)
        db.q("UPDATE applications SET status='accepted' WHERE id=?", (self.aid,))
        st = db.one("SELECT * FROM app_settings WHERE guild_id=?", (it.guild.id,))
        r = it.guild.get_role(st["staff_role"]) if st and st["staff_role"] else None
        mb = it.guild.get_member(a["user_id"])
        if r and mb:
            try: await mb.add_roles(r, reason="Başvuru kabul")
            except Exception: pass
        try: await it.message.edit(view=None)
        except Exception: pass
        u = it.client.get_user(a["user_id"])
        if u:
            try: await u.send(OK("BAŞVURUN KABUL EDİLDİ", "**" + it.guild.name + "** sunucusunda yetkilisin!"))
            except Exception: pass
        await it.response.send_message(OK("KABUL", "<@" + str(a["user_id"]) + "> yetkili oldu."))
    async def rej(self, it):
        if not await self.yk(it): return
        a = db.one("SELECT * FROM applications WHERE id=?", (self.aid,))
        if not a or a["status"] != "pending": return await it.response.send_message(WN("İŞLENMİŞ"), ephemeral=True)
        db.q("UPDATE applications SET status='rejected' WHERE id=?", (self.aid,))
        try: await it.message.edit(view=None)
        except Exception: pass
        u = it.client.get_user(a["user_id"])
        if u:
            try: await u.send(WN("BAŞVURUN REDDEDİLDİ", it.guild.name + " • Tekrar deneyebilirsin."))
            except Exception: pass
        await it.response.send_message(ER("RED", "<@" + str(a["user_id"]) + ">"))

# ─────────────── 🎤 TEMP VOICE PANELİ (KALICI) ───────────────
class TVNameModal(Modal, title="Oda İsmi"):
    def __init__(self, ch_id):
        super().__init__(); self.ch_id = ch_id
        self.name_in = TextInput(label="Yeni isim", max_length=50)
        self.add_item(self.name_in)
    async def on_submit(self, it):
        ch = it.client.get_channel(self.ch_id)
        if not ch: return await it.response.send_message(ER("ODA YOK"), ephemeral=True)
        await ch.edit(name=self.name_in.value[:50])
        await it.response.send_message(OK("İSİM DEĞİŞTİ", ch.name), ephemeral=True)
class TVLimitModal(Modal, title="Oda Limiti"):
    def __init__(self, ch_id):
        super().__init__(); self.ch_id = ch_id
        self.lim = TextInput(label="Limit (0 = sınırsız, max 99)", max_length=2)
        self.add_item(self.lim)
    async def on_submit(self, it):
        ch = it.client.get_channel(self.ch_id)
        if not ch: return await it.response.send_message(ER("ODA YOK"), ephemeral=True)
        try: n = max(0, min(99, int(self.lim.value)))
        except ValueError: n = 0
        await ch.edit(user_limit=n if n else None)
        await it.response.send_message(OK("LİMİT", str(n) if n else "Sınırsız"), ephemeral=True)
class TVPanel(View):
    def __init__(self, ch_id):
        super().__init__(timeout=None)
        self.ch_id = ch_id
        for label, style, emoji, cid, cb in [
            ("Kilitle/Aç", discord.ButtonStyle.secondary, "🔒", "tv_lock", self.cb_lock),
            ("İsim", discord.ButtonStyle.primary, "✏️", "tv_name", self.cb_name),
            ("Limit", discord.ButtonStyle.primary, "👥", "tv_limit", self.cb_limit),
            ("Davet", discord.ButtonStyle.success, "➕", "tv_inv", self.cb_inv),
            ("Odayı Sil", discord.ButtonStyle.danger, "🗑️", "tv_del", self.cb_del)]:
            btn = Button(label=label, style=style, emoji=emoji, custom_id=cid + "_" + str(ch_id))
            btn.callback = cb
            self.add_item(btn)
    async def owner_check(self, it):
        row = db.one("SELECT * FROM temp_channels WHERE channel_id=?", (self.ch_id,))
        if not row or row["owner_id"] != it.user.id:
            await it.response.send_message(ER("YETKİ YOK", "Bu odanın sahibi değilsin."), ephemeral=True); return None
        ch = it.client.get_channel(self.ch_id)
        if not ch:
            await it.response.send_message(ER("ODA YOK", "Kanal silinmiş."), ephemeral=True); return None
        return ch
    async def cb_lock(self, it):
        ch = await self.owner_check(it)
        if not ch: return
        cur = ch.overwrites_for(ch.guild.default_role)
        locked = cur.connect is False
        await ch.set_permissions(ch.guild.default_role, connect=None if locked else False, view_channel=None if locked else False)
        await it.response.send_message(OK("KİLİT", "Oda açıldı 🔓" if locked else "Oda kilitlendi 🔒"), ephemeral=True)
    async def cb_name(self, it):
        if await self.owner_check(it): await it.response.send_modal(TVNameModal(self.ch_id))
    async def cb_limit(self, it):
        if await self.owner_check(it): await it.response.send_modal(TVLimitModal(self.ch_id))
    async def cb_inv(self, it):
        ch = await self.owner_check(it)
        if not ch: return
        inv = await ch.create_invite(max_uses=1, max_age=3600)
        await it.response.send_message(OK("DAVET LİNKİ", inv.url), ephemeral=True)
    async def cb_del(self, it):
        ch = await self.owner_check(it)
        if not ch: return
        db.q("DELETE FROM temp_channels WHERE channel_id=?", (self.ch_id,))
        await ch.delete(reason="Sahibi sildi")
        await it.response.send_message(OK("ODA SİLİNDİ"), ephemeral=True)

# ═══════════════════════════════════════════════════════════════════════════
# 🤖 BOT
# ═══════════════════════════════════════════════════════════════════════════
MAINT_CD = {}
class KatreBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix=self.get_prefix, intents=discord.Intents.all(),
                         case_insensitive=True, help_command=None,
                         allowed_mentions=discord.AllowedMentions(users=True, roles=False, everyone=False))
        self.start_time = datetime.datetime.now()
        self.xp_cd = {}; self.ar_cd = {}; self._si = 0
        self.spam = {}; self.flood = {}; self.joins = {}
    async def get_prefix(self, m):
        p = "k!"
        if m.guild:
            s = db.one("SELECT prefix FROM servers WHERE guild_id=?", (m.guild.id,))
            if s: p = s["prefix"]
        b = {p, p.lower(), p.upper()}
        if self.user: b.add("<@" + str(self.user.id) + "> "); b.add("<@!" + str(self.user.id) + "> ")
        return list(b)
    async def setup_hook(self):
        self.gwv = GiveawayView(self)
        for v in (self.gwv, TicketOpenView(), TicketView(), AppOpenView(), HelpView(self), OwnerPanelView(self)):
            self.add_view(v)
        self.status_loop.start(); self.gw_checker.start(); self.pro_checker.start(); self.backup_loop.start()
    async def on_ready(self):
        try:
            for r in db.all("SELECT * FROM role_menus"):
                g = self.get_guild(r["guild_id"])
                if not g: continue
                roles = [(rid, g.get_role(rid).name) for rid in json.loads(r["role_ids"]) if g.get_role(rid)]
                if roles: self.add_view(RoleMenuView(r["menu_id"], roles))
            for r in db.all("SELECT id FROM applications WHERE status='pending'"): self.add_view(AppReviewView(r["id"]))
            for r in db.all("SELECT channel_id FROM temp_channels"): self.add_view(TVPanel(r["channel_id"]))
            for r in db.all("SELECT id, options FROM polls WHERE status='active'"): self.add_view(PollView(r["id"], json.loads(r["options"])))
            if not EMO_CACHE:
                for g in self.guilds:
                    if auto_map_emojis(g): break
        except Exception: pass
        if BACKUP_CH:
            try:
                if not EMO_CACHE:
                    d = await pull_backup(self, "emoji")
                    if d: print("☁️ Yedekten " + str(emoji_restore(d)) + " emoji geri yüklendi!")
                if not db.all("SELECT 1 FROM users WHERE pro=1") and not db.all("SELECT 1 FROM pro_logs"):
                    d = await pull_backup(self, "pro")
                    if d: print("☁️ Yedekten " + str(pro_restore(d)) + " PRO + log geri yüklendi!")
                if not db.all("SELECT 1 FROM servers"):
                    d = await pull_backup(self, "settings")
                    if d: print("☁️ Yedekten " + str(settings_restore(d)) + " AYAR kaydı geri yüklendi!")
            except Exception: traceback.print_exc()
            _HASH["emoji"] = json.dumps(EMO_CACHE, sort_keys=True)
            _HASH["pro"] = json.dumps(pro_snapshot(), sort_keys=True, default=str)
            _HASH["set"] = json.dumps(settings_snapshot(), sort_keys=True, default=str)
        refresh_emojis()
        await check_update(self)
        print("💧 KATRE v" + BOT_VERSION + " | " + str(self.user) + " | " + str(len(self.guilds)) + " sunucu | " +
              str(len(self.commands)) + " komut | yedek: " + ("AÇIK" if BACKUP_CH else "KAPALI") +
              " | bakım: " + ("AÇIK" if is_maintenance() else "KAPALI"))
        await self.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="k!yardım | Katre Bot"))
    @tasks.loop(seconds=12)
    async def status_loop(self):
        o = self.get_user(OWNER_ID); on = o.display_name if o else "Owner"
        ms = [(discord.ActivityType.watching, "k!yardım | Katre Bot"), (discord.ActivityType.playing, str(len(self.guilds)) + " sunucuda"),
              (discord.ActivityType.listening, str(sum(g.member_count or 0 for g in self.guilds)) + " kullanıcıya"),
              (discord.ActivityType.competing, "k!quiz ile yarış"), (discord.ActivityType.watching, "Owner: " + on),
              (discord.ActivityType.playing, "k!pro ayrıcalıkları"), (discord.ActivityType.listening, "k!oylama 🗳️")]
        t, m = ms[self._si % len(ms)]; self._si += 1
        try: await self.change_presence(activity=discord.Activity(type=t, name=m))
        except Exception: pass
    @tasks.loop(seconds=15)
    async def gw_checker(self):
        nw = datetime.datetime.now().timestamp()
        for g in db.all("SELECT * FROM giveaways WHERE status='active' AND end_time<=?", (nw,)):
            await finalize_giveaway(self, g["message_id"])
    @tasks.loop(minutes=5)
    async def pro_checker(self):
        nw = datetime.datetime.now()
        for r in db.all("SELECT user_id FROM users WHERE pro=1 AND pro_expiry IS NOT NULL AND pro_expiry<?", (nw.isoformat(),)):
            db.q("UPDATE users SET pro=0 WHERE user_id=?", (r["user_id"],)); pro_log(r["user_id"], "SÜRESİ DOLDU")
    @tasks.loop(minutes=1)
    async def backup_loop(self):
        if not BACKUP_CH: return
        eh = json.dumps(EMO_CACHE, sort_keys=True)
        ph = json.dumps(pro_snapshot(), sort_keys=True, default=str)
        sh = json.dumps(settings_snapshot(), sort_keys=True, default=str)
        if _HASH["emoji"] is None: _HASH["emoji"] = eh
        if _HASH["pro"] is None: _HASH["pro"] = ph
        if _HASH["set"] is None: _HASH["set"] = sh
        if eh != _HASH["emoji"]:
            _HASH["emoji"] = eh; await push_backup(self, "emoji", EMO_CACHE)
        if ph != _HASH["pro"]:
            _HASH["pro"] = ph; await push_backup(self, "pro", pro_snapshot())
        if sh != _HASH["set"]:
            _HASH["set"] = sh; await push_backup(self, "settings", settings_snapshot())
    async def punish(self, m, mn, r):
        try: await m.timeout(datetime.timedelta(minutes=mn), reason=r); return True
        except Exception: return False
    async def mod_log(self, g, txt):
        p = db.one("SELECT log_ch FROM protections WHERE guild_id=?", (g.id,))
        if p and p["log_ch"]:
            ch = g.get_channel(p["log_ch"])
            if ch:
                try: await ch.send(txt)
                except Exception: pass
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
                await self.mod_log(m.guild, e("link") + " ANTİ-LİNK: " + m.author.mention + " mesaj silindi.")
            elif p["badword"]:
                ws = [w["word"] for w in db.all("SELECT word FROM badwords WHERE guild_id=?", (m.guild.id,))]
                if any(w and w in c.lower() for w in ws):
                    try: await m.delete()
                    except Exception: pass
                    ok = await self.punish(m.author, 1, "Küfür")
                    await self.mod_log(m.guild, e("warn") + " KÜFÜR: " + m.author.mention + " 1dk " + ("✅" if ok else "❌"))
            if p["anti_spam"]:
                dq = self.spam.setdefault(m.guild.id, {}).setdefault(m.author.id, deque()); dq.append(nw)
                while dq and nw - dq[0] > 5: dq.popleft()
                if len(dq) >= 7:
                    dq.clear(); ok = await self.punish(m.author, 5, "Spam")
                    try: await m.channel.purge(limit=6, check=lambda x: x.author.id == m.author.id)
                    except Exception: pass
                    await self.mod_log(m.guild, e("cross") + " ANTİ-SPAM: " + m.author.mention + " 5dk " + ("✅" if ok else "❌"))
            if p["anti_flood"]:
                k = (m.guild.id, m.author.id); pv = self.flood.get(k)
                cn = (pv[1] + 1) if (pv and pv[0] == c and nw - pv[2] < 10) else 1
                self.flood[k] = (c, cn, nw)
                if cn >= 3:
                    self.flood[k] = (c, 0, nw)
                    try: await m.delete()
                    except Exception: pass
                    ok = await self.punish(m.author, 2, "Flood")
                    await self.mod_log(m.guild, e("warn") + " ANTİ-FLOOD: " + m.author.mention + " 2dk " + ("✅" if ok else "❌"))
        except Exception: traceback.print_exc()
    async def on_message(self, m):
        if m.author.bot: return
        try:
            if is_maintenance() and m.author.id != OWNER_ID:
                prefs = await self.get_prefix(m)
                if m.content and any(m.content.startswith(p) for p in prefs):
                    nw = datetime.datetime.now().timestamp()
                    if nw - MAINT_CD.get(m.author.id, 0) > 30:
                        MAINT_CD[m.author.id] = nw
                        try:
                            await m.channel.send(head("warn", "BAKIMDAYIZ") + "\n" + e("gear") + " Katre Bot şu anda **bakım modunda**, komutlar geçici olarak kapalı.\n" + e("time") + " En kısa sürede geri döneceğiz!\n" + e("link") + " Destek: " + SUPPORT_URL)
                        except Exception: pass
                return
            if db.one("SELECT 1 FROM blacklist WHERE user_id=?", (m.author.id,)): return
        except Exception: pass
        # 😴 AFK (v3.5.2 güzelleştirilmiş)
        try:
            a = db.one("SELECT * FROM afk WHERE user_id=?", (m.author.id,))
            if a:
                dk = int((datetime.datetime.now() - datetime.datetime.fromisoformat(a["since"])).total_seconds() // 60)
                db.q("DELETE FROM afk WHERE user_id=?", (m.author.id,))
                msg = await m.channel.send(head("wave", "TEKRAR ARAMIZDA") + "\n" + m.author.mention + " AFK'dan döndü!\n" +
                    e("time") + " Uzak kaldığı süre: **" + sure_txt(dk) + "**\n" +
                    e("target") + " Mentionlenme: **" + str(a["mentions"] or 0) + "** kez\n" +
                    e("spark") + " Tekrar hoş geldin!")
                try: await msg.delete(delay=20)
                except Exception: pass
            if m.guild:
                for mm in m.mentions:
                    a = db.one("SELECT * FROM afk WHERE user_id=?", (mm.id,))
                    if a:
                        db.q("UPDATE afk SET mentions=mentions+1 WHERE user_id=?", (mm.id,))
                        await m.channel.send(head("sleep", mm.display_name + " ŞU AN AFK") + "\n" +
                            e("arrow") + " Sebep: **" + (a["reason"] or "Belirtilmedi") + "**\n" +
                            e("time") + " AFK olalı: <t:" + str(int(datetime.datetime.fromisoformat(a["since"]).timestamp())) + ":R>\n" +
                            e("target") + " Toplam mention: **" + str((a["mentions"] or 0) + 1) + "**")
                        break
        except Exception: pass
        await self.protections(m)
        try:
            if m.guild and not m.content.startswith(("k!", "K!")):
                nw = datetime.datetime.now().timestamp()
                if nw - self.ar_cd.get(m.guild.id, 0) > 3:
                    low = (m.content or "").lower()
                    for r in db.all("SELECT * FROM auto_replies WHERE guild_id=?", (m.guild.id,)):
                        if r["trigger"] and r["trigger"] in low:
                            self.ar_cd[m.guild.id] = nw; await m.channel.send(r["response"][:1900]); break
        except Exception: pass
        try:
            ensure_user(m.author.id, str(m.author))
            if m.guild:
                db.q("UPDATE users SET messages=messages+1, name=? WHERE user_id=?", (str(m.author), m.author.id))
                nw = datetime.datetime.now().timestamp()
                s = db.one("SELECT rank_on FROM servers WHERE guild_id=?", (m.guild.id,))
                if (not s or s["rank_on"]) and nw - self.xp_cd.get(m.author.id, 0) > 60:
                    self.xp_cd[m.author.id] = nw
                    u = db.one("SELECT xp,level,xp2 FROM users WHERE user_id=?", (m.author.id))
                    g = random.randint(5, 15) * (2 if u["xp2"] else 1)
                    xp, lv = u["xp"] + g, u["level"]; nd = lv * 100
                    if xp >= nd:
                        xp -= nd; lv += 1; cn = random.randint(50, 150)
                        db.q("UPDATE users SET coins=coins+? WHERE user_id=?", (cn, m.author.id))
                        for lr in db.all("SELECT * FROM level_roles WHERE guild_id=? AND level<=?", (m.guild.id, lv)):
                            rr = m.guild.get_role(lr["role_id"])
                            if rr and rr not in m.author.roles:
                                try: await m.author.add_roles(rr, reason="Seviye rolü")
                                except Exception: pass
                        await m.channel.send(head("chartup", "SEVİYE ATLADIN") + "\n" + m.author.mention +
                                             " → **Seviye " + str(lv) + "**\n" + e("gift") + " +" + str(cn) + " coin")
                    db.q("UPDATE users SET xp=?,level=? WHERE user_id=?", (xp, lv, m.author.id))
        except Exception: traceback.print_exc()
        await self.process_commands(m)
    async def on_voice_state_update(self, member, before, after):
        try:
            guild = member.guild
            tv = db.one("SELECT * FROM tempvoice WHERE guild_id=?", (guild.id,))
            if tv and after.channel and after.channel.id == tv["trigger_ch"]:
                cat = guild.get_channel(tv["category_id"]) if tv["category_id"] else after.channel.category
                ow = {guild.default_role: discord.PermissionOverwrite(view_channel=False, connect=False),
                      member: discord.PermissionOverwrite(view_channel=True, connect=True, manage_channels=True,
                                                          mute_members=True, move_members=True, priority_speaker=True),
                      guild.me: discord.PermissionOverwrite(view_channel=True, connect=True, manage_channels=True, move_members=True)}
                ch = await guild.create_voice_channel("🔊 " + member.display_name, category=cat, overwrites=ow)
                db.q("INSERT OR REPLACE INTO temp_channels(channel_id,owner_id,guild_id) VALUES(?,?,?)", (ch.id, member.id, guild.id))
                self.add_view(TVPanel(ch.id))
                await member.move_to(ch, reason="Temp voice")
                try:
                    await member.send(head("mic", "ÖZEL ODAN HAZIR!") + "\n**" + ch.name + "**\nAşağıdaki panelden odayı yönet.", view=TVPanel(ch.id))
                except Exception: pass
            for chn in (before.channel, after.channel):
                if not chn: continue
                row = db.one("SELECT * FROM temp_channels WHERE channel_id=?", (chn.id,))
                if row and len(chn.members) == 0:
                    db.q("DELETE FROM temp_channels WHERE channel_id=?", (chn.id,))
                    try: await chn.delete(reason="Oda boşaldı")
                    except Exception: pass
        except Exception:
            traceback.print_exc()
    async def on_message_edit(self, b, a):
        if b.author.bot or not b.guild or b.content == a.content: return
        await guild_log_send(b.guild, head("pen", "MESAJ DÜZENLENDİ") + "\n" + b.author.mention + " " + b.channel.mention +
                             "\n> Eski: " + (b.content or "")[:200] + "\n> Yeni: " + (a.content or "")[:200])
    async def on_message_delete(self, m):
        try:
            if m.author.bot or not m.guild: return
            db.q("INSERT OR REPLACE INTO snipe(channel_id,author_id,content,attachment,ts) VALUES(?,?,?,?,?)",
                 (m.channel.id, m.author.id, (m.content or "")[:1000], m.attachments[0].url if m.attachments else None,
                  datetime.datetime.now().isoformat()))
            await guild_log_send(m.guild, head("trash", "MESAJ SİLİNDİ") + "\n" + m.author.mention + " " + m.channel.mention +
                                 "\n> " + ((m.content or "")[:200] or "_ek_"))
        except Exception: pass
    async def on_member_remove(self, m):
        await guild_log_send(m.guild, e("wave") + " **AYRILDI** › " + str(m) + " • Kalan: **" + str(m.guild.member_count) + "**")
    async def on_member_update(self, b, a):
        if b.nick != a.nick:
            await guild_log_send(a.guild, head("tag", "NICK DEĞİŞTİ") + "\n" + a.mention + "\n> Eski: " + str(b.nick) + "\n> Yeni: " + str(a.nick))
    async def on_command_completion(self, ctx):
        db.q("INSERT INTO cmd_stats(cmd,uses) VALUES(?,1) ON CONFLICT(cmd) DO UPDATE SET uses=uses+1", (ctx.command.name,))
    async def on_command_error(self, ctx, er):
        if isinstance(er, OwnerOnly): return
        if isinstance(er, ProOnly):
            v = View(); v.add_item(Button(label="Pro Destek", url=SUPPORT_URL, style=discord.ButtonStyle.link, emoji="💎"))
            await rp(ctx, head("pro", "PRO GEREKLİ") + "\nBu komut Pro üyelere özel.\n📋 `k!pro`", v); return
        if isinstance(er, commands.CommandNotFound):
            await rp(ctx, e("search") + " Bulunamadı → `k!yardım`"); return
        if isinstance(er, commands.MissingRequiredArgument):
            await rp(ctx, ER("EKSİK", "`k!" + ctx.command.name + " " + ctx.command.signature + "`")); return
        if isinstance(er, commands.CommandOnCooldown):
            await rp(ctx, head("time", "BEKLEME") + "\n**" + str(int(er.retry_after)) + " sn** sonra dene."); return
        if isinstance(er, commands.MissingPermissions):
            await rp(ctx, ER("YETKİ YOK", "`" + ", ".join(er.missing_permissions) + "`")); return
        if isinstance(er, commands.CheckFailure):
            await rp(ctx, ER("YETKİ YOK")); return
        if isinstance(er, commands.CommandInvokeError):
            o = er.original
            if isinstance(o, discord.Forbidden):
                try: await ctx.author.send(ER("YETKİ", "**#" + str(ctx.channel) + "** kanalında yetkim yok."))
                except Exception: pass
                return
            er = o
        await rp(ctx, head("warn", "HATA") + "\n```\n" + str(er)[:800] + "\n```")
        traceback.print_exc()
    async def on_member_join(self, mb):
        ensure_user(mb.id, str(mb))
        try:
            p = db.one("SELECT * FROM protections WHERE guild_id=?", (mb.guild.id,))
            if p and p["anti_raid"]:
                nw = datetime.datetime.now().timestamp()
                dq = self.joins.setdefault(mb.guild.id, deque()); dq.append(nw)
                while dq and nw - dq[0] > 10: dq.popleft()
                if len(dq) >= 8 and nw > (p["raid_until"] or 0):
                    db.q("UPDATE protections SET raid_until=? WHERE guild_id=?", (nw + 600, mb.guild.id))
                    await self.mod_log(mb.guild, head("shield", "RAID ALGILANDI") + "\n10sn'de 8+ giriş → 10dk kilit!")
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
                    try: await ch.send(head("wave", "HOŞ GELDİN") + "\n### " + mb.mention +
                        "\n" + e("party") + " Sunucumuz artık **" + str(mb.guild.member_count) + "** üye!" +
                        "\n" + e("time") + " Hesap: <t:" + str(int(mb.created_at.timestamp())) + ":R>")
                    except Exception: pass
        try:
            c = db.one("SELECT * FROM counters WHERE guild_id=?", (mb.guild.id,))
            if c and not c["reached"]:
                ch = mb.guild.get_channel(c["channel_id"])
                if ch:
                    cu = mb.guild.member_count
                    if cu >= c["target"]:
                        db.q("UPDATE counters SET reached=1 WHERE guild_id=?", (mb.guild.id,))
                        await ch.send(head("party", "HEDEFE ULAŞILDI") + "\n**" + str(c["target"]) + "** üye!")
                    else:
                        await ch.send(head("target", "SAYAÇ") + "\n**" + str(cu) + "/" + str(c["target"]) + "** üye\n" + bar(cu / c["target"] * 100))
        except Exception: pass
    async def on_guild_join(self, g):
        ensure_server(g.id)
        db.q("INSERT OR IGNORE INTO protections(guild_id) VALUES(?)", (g.id,))
        if not EMO_CACHE: auto_map_emojis(g)
        ch = g.system_channel or next((c for c in g.text_channels if c.permissions_for(g.me).send_messages), None)
        if ch:
            v = View(); v.add_item(Button(label="Destek", url=SUPPORT_URL, style=discord.ButtonStyle.link, emoji="🔗"))
            await ch.send(head("logo", "KATRE BOT ARANIZDA") + "\n`k!yardım` • `k!kurulum` • `k!tempvoice` • `k!koruma antispam aç`", v)

async def finalize_giveaway(bot, mid):
    gw = db.one("SELECT * FROM giveaways WHERE message_id=?", (mid,))
    if not gw or gw["status"] != "active": return
    p = json.loads(gw["participants"])
    db.q("UPDATE giveaways SET status='ended' WHERE message_id=?", (mid,))
    ch = bot.get_channel(gw["channel_id"])
    if not ch: return
    if not p:
        try: await ch.send(head("warn", "ÇEKİLİŞ BİTTİ") + "\n**" + gw["prize"] + "** • katılımcı yok.")
        except Exception: pass
        return
    n = min(gw["winners"], len(p))
    ws = [bot.get_user(int(w)) for w in random.sample(p, n)]
    men = "\n".join(w.mention if w else "?" for w in ws)
    jump = None
    try:
        msg = await ch.fetch_message(mid); jump = msg.jump_url
        await msg.edit(content=gw_end_text(gw, men, p), view=GwJumpView(jump))
    except Exception: pass
    await ch.send(head("party", "ÇEKİLİŞ SONUCU") + "\n" + men + " kazandı!\n" + e("dot") + " Düzenleyen › <@" + str(gw["host"]) + ">",
                  view=GwJumpView(jump), allowed_mentions=discord.AllowedMentions(users=True))
    for w in ws:
        if w:
            try:
                await w.send(head("star", "ÇEKİLİŞİ KAZANDIN") + "\n**" + ch.guild.name + " #" + ch.name +
                             "** sunucusundaki **" + gw["prize"] + "** çekilişini kazandın.\nÖdülünü almak için sunucu yetkilileriyle iletişime geç.",
                             view=GwJumpView(jump))
            except Exception: pass

bot = KatreBot()

# ═══════════════════════════════════════════════════════════════════════════
# 🌐 GENEL
# ═══════════════════════════════════════════════════════════════════════════
@kategori("genel")
@bot.command(name="yardım", aliases=["yardim","help","komutlar"], help="Yardım menüsü")
@commands.cooldown(1, 5, commands.BucketType.user)
async def yardim(ctx): await rp(ctx, help_content(bot), HelpView(bot).links())
@kategori("genel")
@bot.command(name="ping", help="Gecikme")
async def ping(ctx):
    ms = round(bot.latency * 1000)
    await rp(ctx, e("bolt") + " **PONG** › `" + str(ms) + "ms` " + ("🟢" if ms < 100 else "🟡" if ms < 200 else "🔴"))
@kategori("genel")
@bot.command(name="istatistik", aliases=["stats"], help="Bot istatistiği")
async def istatistik(ctx):
    up = str(datetime.datetime.now() - bot.start_time).split(".")[0]
    await rp(ctx, head("chart", "KATRE İSTATİSTİK") + "\n" + KV([
        ("Sunucu", len(bot.guilds)), ("Kullanıcı", sum(g.member_count or 0 for g in bot.guilds)),
        ("Komut", len(bot.commands)), ("Uptime", up), ("Ping", str(round(bot.latency*1000))+"ms"),
        ("Sürüm", "v" + BOT_VERSION),
        ("Toplam kullanım", db.one("SELECT SUM(uses) u FROM cmd_stats")["u"] or 0), ("Owner", "<@"+str(OWNER_ID)+">")]))
@kategori("genel")
@bot.command(name="davet", aliases=["invite"], help="Davet linki")
async def davet(ctx):
    u = "https://discord.com/oauth2/authorize?client_id=" + str(bot.user.id) + "&permissions=8&scope=bot%20applications.commands"
    v = View()
    v.add_item(Button(label="Botu Ekle", url=u, style=discord.ButtonStyle.link, emoji="➕"))
    v.add_item(Button(label="Destek", url=SUPPORT_URL, style=discord.ButtonStyle.link, emoji="🔗"))
    await rp(ctx, head("logo", "KATRE BOT'U EKLE") + "\n" + u, v)
@kategori("genel")
@bot.command(name="avatar", aliases=["av","pfp"], help="Avatar")
async def avatar(ctx, u: discord.Member = None):
    u = u or ctx.author
    v = View(); v.add_item(Button(label="Tarayıcıda Aç", url=u.display_avatar.url, style=discord.ButtonStyle.link, emoji="🔗"))
    await rp(ctx, head("cam", u.display_name.upper() + " AVATAR") + "\n" + u.display_avatar.url, v)
@kategori("genel")
@bot.command(name="oda", help="<isim/limit/kilit/davet/sil> [değer] — Özel odanı yönet")
async def oda(ctx, i: str = "bilgi", *, arg=None):
    row = db.one("SELECT * FROM temp_channels WHERE owner_id=? AND guild_id=?", (ctx.author.id, ctx.guild.id))
    if not row: return await rp(ctx, ER("ODAN YOK", "Temp voice kanalına girerek oda kur."))
    ch = ctx.guild.get_channel(row["channel_id"])
    if not ch:
        db.q("DELETE FROM temp_channels WHERE channel_id=?", (row["channel_id"],))
        return await rp(ctx, ER("ODA YOK", "Odan silinmiş."))
    i = i.lower()
    if i == "isim" and arg:
        await ch.edit(name=arg[:50]); await rp(ctx, OK("İSİM", ch.name))
    elif i == "limit" and arg:
        try: n = max(0, min(99, int(arg)))
        except ValueError: return await rp(ctx, ER("GEÇERSİZ", "0-99"))
        await ch.edit(user_limit=n if n else None); await rp(ctx, OK("LİMİT", str(n) if n else "Sınırsız"))
    elif i == "kilit":
        cur = ch.overwrites_for(ctx.guild.default_role)
        locked = cur.connect is False
        await ch.set_permissions(ctx.guild.default_role, connect=None if locked else False, view_channel=None if locked else False)
        await rp(ctx, OK("KİLİT", "Oda açıldı 🔓" if locked else "Oda kilitlendi 🔒"))
    elif i == "davet":
        inv = await ch.create_invite(max_uses=1, max_age=3600)
        await rp(ctx, OK("DAVET", inv.url))
    elif i == "sil":
        db.q("DELETE FROM temp_channels WHERE channel_id=?", (ch.id,)); await ch.delete(reason="Sahibi sildi")
        await rp(ctx, OK("ODA SİLİNDİ"))
    else:
        await rp(ctx, head("mic", "ODAN: " + ch.name) + "\n`k!oda isim <yeni>` • `k!oda limit <0-99>` • `k!oda kilit` • `k!oda davet` • `k!oda sil`")
@kategori("genel")
@bot.command(name="rank", aliases=["seviye","level"], help="Seviye kartı")
@commands.cooldown(1, 3, commands.BucketType.user)
async def rank(ctx, u: discord.Member = None):
    u = u or ctx.author; ensure_user(u.id, str(u))
    d = db.one("SELECT * FROM users WHERE user_id=?", (u.id,)); nd = d["level"] * 100
    bd = []
    if d["pro"]: bd.append(e("pro") + " PRO")
    if d["pro_tag"]: bd.append(e("tag") + " " + d["pro_tag"])
    if d["xp2"]: bd.append(e("bolt") + " 2x XP")
    await rp(ctx, head("chartup", u.display_name.upper() + " RANK") + "\n" + ("### " + " • ".join(bd) + "\n" if bd else "") +
        KV([(e("star")+" Seviye", d["level"]), (e("spark")+" XP", str(d["xp"])+"/"+str(nd)),
            (e("coin")+" Coin", d["coins"]), (e("star")+" İtibar", d["rep"])]) + "\n" + bar(d["xp"]/nd*100))
@kategori("genel")
@bot.command(name="sıralama", aliases=["sirala","top","lb"], help="Seviye sıralaması")
async def sıralama(ctx):
    rs = db.all("SELECT * FROM users ORDER BY level DESC, xp DESC LIMIT 10")
    if not rs: return await rp(ctx, e("chart") + " Henüz veri yok.")
    L = [head("star", "SUNUCU SIRALAMASI")]
    md = ["🥇","🥈","🥉"]
    for i, r in enumerate(rs):
        L.append((md[i] if i < 3 else "**" + str(i+1) + ".**") + " <@" + str(r["user_id"]) + ">" +
                 (" " + e("pro") if r["pro"] else "") + " ─ Lv.**" + str(r["level"]) + "** • `" + str(r["xp"]) + " XP`")
    await rp(ctx, "\n".join(L))
@kategori("genel")
@bot.command(name="profil", aliases=["profile"], help="Profil kartı")
async def profil(ctx, u: discord.Member = None):
    u = u or ctx.author; ensure_user(u.id, str(u))
    d = db.one("SELECT * FROM users WHERE user_id=?", (u.id,))
    a = db.one("SELECT * FROM afk WHERE user_id=?", (u.id,))
    await rp(ctx, head("logo", u.display_name.upper() + " PROFİL") + "\n" + KV([
        (e("dot")+" ID", "`"+str(u.id)+"`"), (e("time")+" Hesap", "<t:"+str(int(u.created_at.timestamp()))+":R>"),
        (e("wave")+" Katılım", "<t:"+str(int(u.joined_at.timestamp()))+":R>" if u.joined_at else "—"),
        (e("chartup")+" Seviye", d["level"]), (e("coin")+" Coin", d["coins"]), (e("star")+" Rep", d["rep"]),
        (e("pro")+" Pro", "✅" if d["pro"] else "❌"),
        (e("sleep")+" AFK", ("✅ (" + (a["reason"] or "sebep yok")[:30] + ")") if a else "❌")]))
@kategori("genel")
@bot.command(name="sunucubilgi", aliases=["serverinfo"], help="Sunucu bilgisi")
async def sunucubilgi(ctx):
    g = ctx.guild
    await rp(ctx, head("logo", g.name.upper()) + "\n" + KV([
        (e("crown")+" Kurucu", "<@"+str(g.owner_id)+">"), (e("dot")+" ID", "`"+str(g.id)+"`"),
        (e("time")+" Kuruluş", "<t:"+str(int(g.created_at.timestamp()))+":D>"), (e("dot")+" Üye", g.member_count),
        (e("dot")+" Kanal", len(g.channels)), (e("shield")+" Rol", len(g.roles)), (e("bolt")+" Boost", g.premium_subscription_count or 0)]))
@kategori("genel")
@bot.command(name="kanalbilgi", help="[#kanal] — Kanal bilgisi")
async def kanalbilgi(ctx, ch: discord.TextChannel = None):
    ch = ch or ctx.channel
    await rp(ctx, head("logo", "#" + ch.name) + "\n" + KV([
        (e("dot")+"ID", ch.id), (e("dot")+"Konu", ch.topic or "—"), (e("dot")+"Yavaşmod", ch.slowmode_delay),
        (e("dot")+"NSFW", ch.nsfw), (e("time")+"Oluşturma", "<t:"+str(int(ch.created_at.timestamp()))+":D>")]))
@kategori("genel")
@bot.command(name="firstmsg", aliases=["ilkmessaj"], help="Kanalın ilk mesajı")
async def firstmsg(ctx):
    async for m in ctx.channel.history(limit=1, oldest_first=True):
        v = View(); v.add_item(Button(label="Mesaja Git", url=m.jump_url, style=discord.ButtonStyle.link, emoji="🔗"))
        await rp(ctx, head("cam", "İLK MESAJ") + "\n" + e("dot") + " " + m.author.mention + "\n> " + ((m.content or "_ek_")[:300]), v)
        return
    await rp(ctx, e("cam") + " Mesaj yok.")
@kategori("genel")
@bot.command(name="snipe", help="Silinen son mesaj")
@commands.cooldown(1, 3, commands.BucketType.user)
async def snipe(ctx):
    s = db.one("SELECT * FROM snipe WHERE channel_id=?", (ctx.channel.id,))
    if not s: return await rp(ctx, e("cam") + " Kayıt yok.")
    await rp(ctx, head("cam", "SNIPE") + "\n" + KV([(e("dot")+" Kullanıcı", "<@"+str(s["author_id"])+">"), (e("time")+" Tarih", s["ts"][:16].replace("T"," "))]) +
             "\n> " + ((s["content"] or "_ek_")[:800]) + (("\n" + s["attachment"]) if s["attachment"] else ""))
@kategori("genel")
@bot.command(name="afk", help="[sebep] — AFK ol (tekrar yazınca dönersin)")
async def afk(ctx, *, s=None):
    cur = db.one("SELECT * FROM afk WHERE user_id=?", (ctx.author.id,))
    if cur and not s:
        db.q("DELETE FROM afk WHERE user_id=?", (ctx.author.id,))
        return await rp(ctx, OK("AFK KAPATILDI", "Artık AFK değilsin. Tekrar aramıza hoş geldin!"))
    reason = (s or "Belirtilmedi")[:100]
    db.q("INSERT OR REPLACE INTO afk(user_id,reason,since,mentions) VALUES(?,?,?,0)",
         (ctx.author.id, reason, datetime.datetime.now().isoformat()))
    await rp(ctx, head("sleep", "AFK MODU AÇIK") + "\n" +
             e("arrow") + " Sebep: **" + reason + "**\n" +
             e("time") + " Başlangıç: <t:" + str(int(datetime.datetime.now().timestamp())) + ":F>\n" +
             e("info") + " Bir mesaj yazdığında otomatik olarak AFK'dan çıkarsın.\n" +
             e("target") + " Seni mentionleyenlere AFK olduğunu söyleyeceğim.")
@kategori("genel")
@bot.command(name="rep", help="<@üye> — İtibar (12s)")
@commands.cooldown(1, 43200, commands.BucketType.user)
async def rep(ctx, u: discord.Member):
    if u.id == ctx.author.id: return await rp(ctx, ER("OLMAZ", "Kendine veremezsin."))
    ensure_user(u.id, str(u)); db.q("UPDATE users SET rep=rep+1 WHERE user_id=?", (u.id,))
    await rp(ctx, e("star") + " " + ctx.author.mention + " → " + u.mention + " **+1 itibar**")
@kategori("genel")
@bot.command(name="destek", aliases=["ticketpanel"], help="Destek paneli (Yönetici)")
@commands.has_permissions(administrator=True)
async def destek(ctx):
    await rp(ctx, head("ticket", "DESTEK MERKEZİ") + "\nSorun mu var? Butona tıkla, formu doldur!\n" + e("time") + " Ortalama yanıt: **< 1 saat**", TicketOpenView())
    try: await ctx.message.delete()
    except Exception: pass
@kategori("genel")
@bot.command(name="not", help="<metin> — Not")
async def not_(ctx, *, m):
    ensure_user(ctx.author.id, str(ctx.author))
    u = db.one("SELECT notes FROM users WHERE user_id=?", (ctx.author.id,))
    n = json.loads(u["notes"]); n.append({"t": m, "d": datetime.datetime.now().isoformat()})
    db.q("UPDATE users SET notes=? WHERE user_id=?", (json.dumps(n), ctx.author.id))
    await rp(ctx, OK("NOT KAYDEDİLDİ", "Toplam: `" + str(len(n)) + "`"))
@kategori("genel")
@bot.command(name="notlar", help="Notların")
async def notlar(ctx):
    u = db.one("SELECT notes FROM users WHERE user_id=?", (ctx.author.id,))
    n = json.loads(u["notes"]) if u else []
    if not n: return await rp(ctx, e("pen") + " Notun yok.")
    await rp(ctx, head("pen", "NOTLARIN") + "\n" + "\n".join(e("arrow") + " `" + x["d"][:10] + "` " + x["t"][:70] for x in n[-8:]))
@kategori("genel")
@bot.command(name="doğumgünü", aliases=["dogumgunu"], help="<gün> <ay>")
async def doğumgünü(ctx, g: int, a: int):
    if not (1 <= g <= 31 and 1 <= a <= 12): return await rp(ctx, ER("GEÇERSİZ", "`k!doğumgünü 24 8`"))
    db.q("UPDATE users SET birthday=? WHERE user_id=?", (str(g)+"."+str(a), ctx.author.id))
    await rp(ctx, e("cake") + " Doğum günün: **" + str(g) + "." + str(a) + "**")
@kategori("genel")
@bot.command(name="doğumgünleri", aliases=["dogumgunleri"], help="Bu ayın doğum günleri")
async def doğumgünleri(ctx):
    nw = datetime.datetime.now()
    rs = [r for r in db.all("SELECT user_id,birthday FROM users WHERE birthday IS NOT NULL") if r["birthday"] and int(r["birthday"].split(".")[1]) == nw.month]
    if not rs: return await rp(ctx, e("cake") + " Bu ay yok.")
    await rp(ctx, head("cake", str(nw.month) + ". AY DOĞUM GÜNLERİ") + "\n" + "\n".join(e("arrow") + " `" + r["birthday"] + "` <@" + str(r["user_id"]) + ">" for r in rs))
@kategori("genel")
@bot.command(name="hatırlat", aliases=["hatirlat"], help="<dk> <metin>")
async def hatırlat(ctx, dk: int, *, m):
    if dk < 1 or dk > 1440: return await rp(ctx, ER("GEÇERSİZ", "1-1440 dk"))
    await rp(ctx, e("alarm") + " **" + str(dk) + " dk** sonra: " + m)
    await asyncio.sleep(dk * 60)
    await ctx.send(ctx.author.mention + " " + e("alarm") + " **HATIRLATMA:** " + m)
@kategori("genel")
@bot.command(name="botkontrol", aliases=["check"], help="Yetki teşhisi")
@commands.has_permissions(administrator=True)
async def botkontrol(ctx):
    p = ctx.channel.permissions_for(ctx.guild.me)
    cs = [("Mesaj Gör",p.view_channel),("Mesaj Gönder",p.send_messages),("Embed",p.embed_links),("Tepki",p.add_reactions),
          ("Mesaj Yönet",p.manage_messages),("Timeout",p.moderate_members),("Rol",p.manage_roles),("Kanal",p.manage_channels),("At",p.kick_members),("Ban",p.ban_members)]
    await rp(ctx, head("gear", "BOT KONTROL #" + ctx.channel.name) + "\n" + "\n".join((e("check") if ok else e("cross")) + " " + n for n, ok in cs))

# ═══════════════════════════════════════════════════════════════════════════
# 🛡️ MOD
# ═══════════════════════════════════════════════════════════════════════════
@kategori("mod")
@bot.command(name="yasakla", aliases=["ban"], help="<@üye> [sebep]")
@commands.has_permissions(ban_members=True)
@commands.bot_has_permissions(ban_members=True)
async def yasakla(ctx, u: discord.Member, *, s="Belirtilmedi"):
    g = mod_guard(ctx, u, "yasakla")
    if g: return await rp(ctx, ER("OLMAZ", g))
    v = ConfirmView(); await rp(ctx, head("warn", "ONAY") + "\n**" + str(u) + "** banlansın mı?\nSebep: " + s, v)
    await v.wait()
    if v.value is None: return await rp(ctx, WN("ZAMAN AŞIMI"))
    if v.value:
        try: await u.send(ER("BAN", ctx.guild.name + " • " + s))
        except Exception: pass
        await u.ban(reason=str(ctx.author)+" | "+s)
        punish_log(ctx.guild.id, u.id, "BAN", s, ctx.author.id)
        await guild_log_send(ctx.guild, head("hammer", "BAN") + "\n" + u.mention + " › " + s + " › " + ctx.author.mention)
        await rp(ctx, head("hammer", "YASAKLAMA") + "\n" + u.mention + " › " + s)
@kategori("mod")
@bot.command(name="at", aliases=["kick"], help="<@üye> [sebep]")
@commands.has_permissions(kick_members=True)
@commands.bot_has_permissions(kick_members=True)
async def at(ctx, u: discord.Member, *, s="Belirtilmedi"):
    g = mod_guard(ctx, u, "at")
    if g: return await rp(ctx, ER("OLMAZ", g))
    v = ConfirmView(); await rp(ctx, head("warn", "ONAY") + "\n**" + str(u) + "** atılsın mı?", v)
    await v.wait()
    if v.value is None: return await rp(ctx, WN("ZAMAN AŞIMI"))
    if v.value:
        await u.kick(reason=str(ctx.author)+" | "+s)
        punish_log(ctx.guild.id, u.id, "KICK", s, ctx.author.id)
        await guild_log_send(ctx.guild, head("kick", "KICK") + "\n" + u.mention + " › " + s)
        await rp(ctx, head("kick", "ATILDI") + "\n" + u.mention)
@kategori("mod")
@bot.command(name="mute", aliases=["sustur"], help="<@üye> <süre> [sebep] — Süreli sustur (30m/1h/2d)")
@commands.has_permissions(moderate_members=True)
@commands.bot_has_permissions(moderate_members=True)
async def mute(ctx, u: discord.Member, süre: str, *, s="Belirtilmedi"):
    g = mod_guard(ctx, u, "sustur")
    if g: return await rp(ctx, ER("OLMAZ", g))
    try: dk = parse_sure(süre)
    except Exception: return await rp(ctx, ER("SÜRE", "`30m` `1h` `2d`"))
    if dk < 1 or dk > 40320: return await rp(ctx, ER("SÜRE", "1 dk – 28 gün arası."))
    await u.timeout(datetime.timedelta(minutes=dk), reason=str(ctx.author)+" | "+s)
    punish_log(ctx.guild.id, u.id, "MUTE", s, ctx.author.id, dk)
    await guild_log_send(ctx.guild, head("lock", "MUTE") + "\n" + u.mention + " › **" + süre + "** › " + s)
    await rp(ctx, OK("SUSTURULDU", u.mention + " › **" + süre + "**\nSebep: " + s))
@kategori("mod")
@bot.command(name="unmute", aliases=["susturmaç"], help="<@üye> — Susturmayı kaldırır")
@commands.has_permissions(moderate_members=True)
@commands.bot_has_permissions(moderate_members=True)
async def unmute(ctx, u: discord.Member, *, s="Belirtilmedi"):
    await u.timeout(None, reason=str(ctx.author)+" | "+s)
    punish_log(ctx.guild.id, u.id, "UNMUTE", s, ctx.author.id)
    await rp(ctx, OK("SUSTURMA KALDIRILDI", u.mention))
@kategori("mod")
@bot.command(name="ceza-sistemi", aliases=["cezasistemi"], help="<ayarla <mute_u> <ban_u>|kapat|bilgi> — Oto ceza zinciri")
@commands.has_permissions(administrator=True)
async def ceza_sistemi(ctx, i: str = "bilgi", a: int = 3, b: int = 5):
    i = i.lower()
    if i in ("ayarla","aç"):
        db.q("INSERT OR REPLACE INTO punish_config(guild_id,mute_at,ban_at) VALUES(?,?,?)", (ctx.guild.id, a, b))
        await rp(ctx, OK("CEZA SİSTEMİ", "**" + str(a) + " uyarı → 1 saat mute**\n**" + str(b) + " uyarı → ban**\n☁️ Bu ayar restart sonrası da kalır."))
    elif i in ("kapat","off"):
        db.q("DELETE FROM punish_config WHERE guild_id=?", (ctx.guild.id,))
        await rp(ctx, OK("CEZA SİSTEMİ", "Kapatıldı."))
    else:
        c = db.one("SELECT * FROM punish_config WHERE guild_id=?", (ctx.guild.id,))
        await rp(ctx, head("shield", "CEZA SİSTEMİ") + "\n" + (str(c["mute_at"]) + " uyarı → 1s mute • " + str(c["ban_at"]) + " uyarı → ban" if c else "Kapalı. Kur: `k!ceza-sistemi ayarla 3 5`"))
@kategori("mod")
@bot.command(name="ceza-geçmişi", aliases=["cezalar","sicil"], help="[<@üye>] — Ceza geçmişi")
@commands.has_permissions(manage_messages=True)
async def ceza_geçmişi(ctx, u: discord.Member = None):
    u = u or ctx.author
    rs = db.all("SELECT * FROM punishments WHERE guild_id=? AND user_id=? ORDER BY id DESC LIMIT 10", (ctx.guild.id, u.id))
    if not rs: return await rp(ctx, e("shield") + " " + u.mention + " temiz sicil.")
    await rp(ctx, head("log", u.display_name.upper() + " CEZA GEÇMİŞİ") + "\n" + "\n".join(
        e("arrow") + " **" + r["type"] + "** › " + (r["reason"] or "—")[:40] + " › " + r["ts"][:10] + ((" › " + str(r["duration"]) + "dk") if r["duration"] else "") for r in rs))
@kategori("mod")
@bot.command(name="unban", help="<user_id> [sebep] — Ban kaldırır")
@commands.has_permissions(ban_members=True)
@commands.bot_has_permissions(ban_members=True)
async def unban(ctx, uid: int, *, s="Belirtilmedi"):
    try:
        b = await ctx.guild.fetch_ban(discord.Object(id=uid))
    except discord.NotFound:
        return await rp(ctx, ER("BULUNAMADI", "Bu ID'ye sahip banlı kullanıcı yok."))
    except Exception as ex:
        return await rp(ctx, ER("HATA", str(ex)[:200]))
    await ctx.guild.unban(b.user, reason=str(ctx.author)+" | "+s)
    await guild_log_send(ctx.guild, head("unlock", "UNBAN") + "\n" + str(b.user) + " › " + s + " › " + ctx.author.mention)
    await rp(ctx, OK("BAN KALDIRILDI", "**" + str(b.user) + "** › " + s))
@kategori("mod")
@bot.command(name="banlist", aliases=["banliste"], help="Banlı kullanıcılar")
@commands.has_permissions(ban_members=True)
async def banlist(ctx):
    bans = [b async for b in ctx.guild.bans()]
    if not bans: return await rp(ctx, e("shield") + " Banlı kullanıcı yok.")
    L = [head("hammer", "BAN LİSTESİ (" + str(len(bans)) + ")")]
    for b in bans[:15]:
        L.append(e("arrow") + " **" + str(b.user) + "** ─ `" + str(b.user.id) + "`" + (" ─ " + (b.reason or "—")[:40] if b.reason else ""))
    await rp(ctx, "\n".join(L))
@kategori("mod")
@bot.command(name="nick", help="<@üye> <yeni nick> — Nick değiştirir")
@commands.has_permissions(manage_nicknames=True)
@commands.bot_has_permissions(manage_nicknames=True)
async def nick(ctx, u: discord.Member, *, n):
    g = mod_guard(ctx, u, "nick değiştir")
    if g: return await rp(ctx, ER("OLMAZ", g))
    await u.edit(nick=n[:32], reason=str(ctx.author))
    await rp(ctx, OK("NICK", u.mention + " → `" + n[:32] + "`"))
@kategori("mod")
@bot.command(name="nicksıfırla", aliases=["nickreset"], help="<@üye> — Nick sıfırlar")
@commands.has_permissions(manage_nicknames=True)
@commands.bot_has_permissions(manage_nicknames=True)
async def nicksıfırla(ctx, u: discord.Member):
    g = mod_guard(ctx, u, "işlem")
    if g: return await rp(ctx, ER("OLMAZ", g))
    await u.edit(nick=None, reason=str(ctx.author))
    await rp(ctx, OK("NICK", u.mention + " sıfırlandı."))
@kategori("mod")
@bot.command(name="rolbilgi", help="<@rol> — Rol bilgisi")
async def rolbilgi(ctx, role: discord.Role):
    await rp(ctx, head("shield", role.name.upper()) + "\n" + KV([
        (e("dot")+"ID", role.id), (e("dot")+"Üye", len(role.members)), (e("dot")+"Renk", str(role.color)),
        (e("dot")+"Etiket", role.mention), (e("time")+"Oluşturma", "<t:"+str(int(role.created_at.timestamp()))+":D>")]))
@kategori("mod")
@bot.command(name="uyar", aliases=["warn"], help="<@üye> [sebep] — Uyarı (oto ceza tetikler)")
@commands.has_permissions(manage_messages=True)
async def uyar(ctx, u: discord.Member, *, s="Belirtilmedi"):
    if u.id == ctx.author.id: return await rp(ctx, ER("OLMAZ", "Kendini uyaramazsın!"))
    ensure_user(u.id, str(u)); db.q("UPDATE users SET warnings=warnings+1 WHERE user_id=?", (u.id,))
    w = db.one("SELECT warnings FROM users WHERE user_id=?", (u.id,))["warnings"]
    punish_log(ctx.guild.id, u.id, "WARN", s, ctx.author.id)
    extra = ""
    cfg = db.one("SELECT * FROM punish_config WHERE guild_id=?", (ctx.guild.id,))
    if cfg:
        if w == cfg["ban_at"]:
            try:
                await u.ban(reason="Oto ceza: " + str(w) + " uyarı")
                punish_log(ctx.guild.id, u.id, "AUTO-BAN", str(w) + " uyarı", ctx.bot.user.id)
                extra = "\n" + e("hammer") + " **" + str(w) + " uyarı → OTOMATİK BAN**"
            except Exception: pass
        elif w == cfg["mute_at"]:
            try:
                await u.timeout(datetime.timedelta(minutes=60), reason="Oto ceza: " + str(w) + " uyarı")
                punish_log(ctx.guild.id, u.id, "AUTO-MUTE", str(w) + " uyarı", ctx.bot.user.id, 60)
                extra = "\n" + e("lock") + " **" + str(w) + " uyarı → 1 SAAT OTOMATİK SUSTURMA**"
            except Exception: pass
    await rp(ctx, head("warn", "UYARI") + "\n" + u.mention + " › toplam **" + str(w) + "**" + extra)
@kategori("mod")
@bot.command(name="uyarılar", aliases=["warns"], help="[<@üye>]")
async def uyarılar(ctx, u: discord.Member = None):
    u = u or ctx.author; ensure_user(u.id, str(u))
    await rp(ctx, e("warn") + " " + u.mention + " › **" + str(db.one("SELECT warnings FROM users WHERE user_id=?", (u.id,))["warnings"]) + "** uyarı")
@kategori("mod")
@bot.command(name="temizle", aliases=["purge","sil"], help="<adet>")
@commands.has_permissions(manage_messages=True)
@commands.bot_has_permissions(manage_messages=True)
async def temizle(ctx, a: int):
    if not 1 <= a <= 500: return await rp(ctx, ER("GEÇERSİZ", "1-500"))
    await ctx.channel.purge(limit=a+1)
    m = await rp(ctx, e("trash") + " **" + str(a) + "** mesaj silindi.")
    await m.delete(delay=5)
@kategori("mod")
@bot.command(name="say", help="<metin> — Bot söyletir (Yönetici)")
@commands.has_permissions(manage_messages=True)
async def say(ctx, *, m):
    try: await ctx.message.delete()
    except Exception: pass
    await rp(ctx, m[:1900])
@kategori("mod")
@bot.command(name="yavaşmod", aliases=["slowmode"], help="<sn>")
@commands.has_permissions(manage_channels=True)
async def yavaşmod(ctx, s: int):
    await ctx.channel.edit(slowmode_delay=s); await rp(ctx, e("gear") + " Yavaş mod: **" + str(s) + " sn**")
@kategori("mod")
@bot.command(name="kilit", help="Kilitle")
@commands.has_permissions(manage_channels=True)
async def kilit(ctx):
    await ctx.channel.set_permissions(ctx.guild.default_role, send_messages=False)
    await rp(ctx, e("lock") + " " + ctx.channel.mention + " kilitlendi.")
@kategori("mod")
@bot.command(name="kilitaç", aliases=["unlock"], help="Kilidi aç")
@commands.has_permissions(manage_channels=True)
async def kilitaç(ctx):
    await ctx.channel.set_permissions(ctx.guild.default_role, send_messages=None)
    await rp(ctx, e("unlock") + " " + ctx.channel.mention + " açıldı.")
@kategori("mod")
@bot.command(name="rolver", help="<@rol> <@üye...> — Toplu rol ver")
@commands.has_permissions(manage_roles=True)
@commands.bot_has_permissions(manage_roles=True)
async def rolver(ctx, role: discord.Role, ms: commands.Greedy[discord.Member]):
    if not ms: return await rp(ctx, ER("EKSİK", "`k!rolver @Rol @üye1 @üye2 ...`"))
    d = 0
    for m in ms:
        try: await m.add_roles(role, reason="Toplu rol"); d += 1
        except Exception: pass
    await rp(ctx, OK("TOPLU ROL VERİLDİ", role.mention + " → **" + str(d) + "/" + str(len(ms)) + "** üye"))
@kategori("mod")
@bot.command(name="rolal", help="<@rol> <@üye...> — Toplu rol al")
@commands.has_permissions(manage_roles=True)
@commands.bot_has_permissions(manage_roles=True)
async def rolal(ctx, role: discord.Role, ms: commands.Greedy[discord.Member]):
    if not ms: return await rp(ctx, ER("EKSİK", "`k!rolal @Rol @üye1 @üye2 ...`"))
    d = 0
    for m in ms:
        try: await m.remove_roles(role, reason="Toplu rol"); d += 1
        except Exception: pass
    await rp(ctx, OK("TOPLU ROL ALINDI", role.mention + " ← **" + str(d) + "/" + str(len(ms)) + "** üye"))
@kategori("mod")
@bot.command(name="herkeserol", help="<@rol> — Tüm üyelere rol verir")
@commands.has_permissions(administrator=True)
@commands.bot_has_permissions(manage_roles=True)
async def herkeserol(ctx, role: discord.Role):
    v = ConfirmView()
    await rp(ctx, head("warn", "ONAY") + "\n**" + str(len(ctx.guild.members)) + "** üyeye " + role.mention + " verilsin mi?", v)
    await v.wait()
    if not v.value: return await rp(ctx, WN("İPTAL"))
    d = 0
    for m in ctx.guild.members:
        if m.bot: continue
        try: await m.add_roles(role, reason="Herkese rol"); d += 1
        except Exception: pass
    await rp(ctx, OK("DAĞITIM BİTTİ", role.mention + " → **" + str(d) + "** üye"))
@kategori("mod")
@bot.command(name="otorol", aliases=["autorol"], help="<@rol|kapat>")
@commands.has_permissions(administrator=True)
async def otorol(ctx, *, arg):
    ensure_server(ctx.guild.id)
    if arg.lower() in ("kapat","off","0"):
        db.q("UPDATE servers SET auto_role=NULL WHERE guild_id=?", (ctx.guild.id,))
        return await rp(ctx, OK("OTOROL", "Kapatıldı."))
    role = await commands.RoleConverter().convert(ctx, arg)
    db.q("UPDATE servers SET auto_role=? WHERE guild_id=?", (role.id, ctx.guild.id))
    await rp(ctx, OK("OTOROL", "Yeni üyelere " + role.mention + " verilecek.\n☁️ Restart sonrası da aktif kalır."))
@kategori("mod")
@bot.command(name="hoşgeldin", aliases=["hosgeldin"], help="<#kanal|kapat>")
@commands.has_permissions(administrator=True)
async def hoşgeldin(ctx, ch: discord.TextChannel = None):
    ensure_server(ctx.guild.id)
    if ch is None:
        db.q("UPDATE servers SET welcome_ch=NULL WHERE guild_id=?", (ctx.guild.id,))
        return await rp(ctx, OK("HOŞGELDİN", "Kapatıldı."))
    db.q("UPDATE servers SET welcome_ch=? WHERE guild_id=?", (ch.id, ctx.guild.id))
    await rp(ctx, OK("HOŞGELDİN", "Yeni üyeler " + ch.mention + " kanalında karşılanacak.\n☁️ Restart sonrası da aktif kalır."))
@kategori("mod")
@bot.command(name="butonrol", aliases=["rolmenü"], help="<@rol...> — Rol menüsü")
@commands.has_permissions(administrator=True)
async def butonrol(ctx, rs: commands.Greedy[discord.Role], *, a="Rollerinizi butonlarla alın!"):
    if not rs or len(rs) > 25: return await rp(ctx, ER("GEÇERSİZ", "1-25 rol"))
    mid = str(random.randint(10**11, 10**12-1))
    db.q("INSERT OR REPLACE INTO role_menus(menu_id,guild_id,role_ids) VALUES(?,?,?)", (mid, ctx.guild.id, json.dumps([r.id for r in rs])))
    v = RoleMenuView(mid, [(r.id, r.name) for r in rs]); bot.add_view(v)
    await rp(ctx, head("shield", "ROL MENÜSÜ") + "\n" + a + "\n" + "\n".join(e("arrow") + " " + r.mention for r in rs), v)
@kategori("mod")
@bot.command(name="koruma", help="<mod> <aç/kapat>")
@commands.has_permissions(administrator=True)
async def koruma(ctx, md: str, d: str):
    md = md.lower().replace("-","").replace("_","")
    col = {"antispam":"anti_spam","antiflood":"anti_flood","antiraid":"anti_raid","antilink":"anti_link","badword":"badword","küfür":"badword"}.get(md)
    if not col: return await rp(ctx, ER("MODÜL", "`antispam antiflood antiraid antilink badword`"))
    db.q("INSERT OR IGNORE INTO protections(guild_id) VALUES(?)", (ctx.guild.id,))
    v = 1 if d.lower() in ("aç","ac","on","1") else 0
    db.q("UPDATE protections SET " + col + "=? WHERE guild_id=?", (v, ctx.guild.id))
    await rp(ctx, head("shield", "KORUMA") + "\n**" + md.upper() + "** → " + ("AÇIK " + e("check") if v else "KAPALI " + e("cross")) + "\nLog: `k!korumalog #kanal`")
@kategori("mod")
@bot.command(name="korumadurum", help="Durum")
async def korumadurum(ctx):
    p = db.one("SELECT * FROM protections WHERE guild_id=?", (ctx.guild.id,)) or {}
    f = lambda v: e("check") if v else e("cross")
    await rp(ctx, head("shield", "KORUMA DURUMU") + "\n" + KV([
        (f(p.get("anti_spam"))+" Spam", "─"), (f(p.get("anti_flood"))+" Flood", "─"), (f(p.get("anti_raid"))+" Raid", "─"),
        (f(p.get("anti_link"))+" Link", "─"), (f(p.get("badword"))+" Küfür", "─")]))
@kategori("mod")
@bot.command(name="korumalog", help="<#kanal>")
@commands.has_permissions(administrator=True)
async def korumalog(ctx, ch: discord.TextChannel):
    db.q("INSERT OR IGNORE INTO protections(guild_id) VALUES(?)", (ctx.guild.id,))
    db.q("UPDATE protections SET log_ch=? WHERE guild_id=?", (ch.id, ctx.guild.id))
    await rp(ctx, OK("KORUMA LOG", ch.mention))
@kategori("mod")
@bot.command(name="badword", help="<ekle/sil/liste> [kelime]")
@commands.has_permissions(administrator=True)
async def badword(ctx, i: str, *, k=None):
    g = ctx.guild.id
    if i.lower() in ("ekle","add"):
        if not k: return await rp(ctx, ER("EKSİK", "Kelime gir."))
        db.q("INSERT OR IGNORE INTO badwords(guild_id,word) VALUES(?,?)", (g, k.lower())); await rp(ctx, OK("FİLTRE", "`"+k.lower()+"`"))
    elif i.lower() in ("sil","remove"):
        db.q("DELETE FROM badwords WHERE guild_id=? AND word=?", (g, (k or "").lower())); await rp(ctx, OK("SİLİNDİ"))
    else:
        ws = [w["word"] for w in db.all("SELECT word FROM badwords WHERE guild_id=?", (g,))]
        await rp(ctx, head("warn", "YASAKLI KELİMELER") + "\n" + ("`" + "`, `".join(ws) + "`" if ws else "Boş"))
@kategori("mod")
@bot.command(name="raidmodu", help="<aç/kapat>")
@commands.has_permissions(administrator=True)
async def raidmodu(ctx, m: str):
    db.q("INSERT OR IGNORE INTO protections(guild_id) VALUES(?)", (ctx.guild.id,))
    if m.lower() in ("aç","ac","on"):
        db.q("UPDATE protections SET raid_until=? WHERE guild_id=?", (datetime.datetime.now().timestamp()+600, ctx.guild.id))
        await rp(ctx, head("shield", "RAID MODU") + "\n10 dk boyunca yeni girişler engelli!")
    else:
        db.q("UPDATE protections SET raid_until=0 WHERE guild_id=?", (ctx.guild.id,)); await rp(ctx, OK("RAID", "Kapatıldı."))
@kategori("mod")
@bot.command(name="kurulum", aliases=["sunucukur","setup"], help="Tek komutla sunucu kur")
@commands.has_permissions(administrator=True)
@commands.bot_has_permissions(manage_channels=True, manage_roles=True)
async def kurulum(ctx):
    v = SetupConfirmView()
    await rp(ctx, head("gear", "SUNUCU KURULUM") + "\n4 kategori • 12 kanal • 4 rol + hoşgeldin\nOnaylıyor musun?", v)
    await v.wait()
    if not v.value: return
    g = ctx.guild; ck = 0
    try:
        ry = await g.create_role(name="Yönetici", color=discord.Color(0xE74C3C), permissions=discord.Permissions(administrator=True))
        rm = await g.create_role(name="Moderatör", color=discord.Color(0x3498DB), permissions=discord.Permissions(kick_members=True, manage_messages=True, moderate_members=True))
        await g.create_role(name="Üye", color=discord.Color(0x2ECC71))
        rb = await g.create_role(name="Bot", color=discord.Color(0xFFD700), hoist=True)
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
        await rp(ctx, OK("KURULUM BİTTİ", "4 kategori • " + str(ck) + " kanal • 4 rol\nHoşgeldin: " + hg.mention + "\n🎤 Ses sistemi: `k!tempvoice`"))
    except discord.Forbidden: await rp(ctx, ER("YETKİ", "Kanal+Rol yönet gerekli."))
    except Exception as ex: await rp(ctx, ER("HATA", "```\n" + str(ex)[:300] + "\n```"))

# ═══════════════════════════════════════════════════════════════════════════
# 📋 SİSTEMLER
# ═══════════════════════════════════════════════════════════════════════════
@kategori("sys")
@bot.command(name="tempvoice", aliases=["geçicises"], help="[kur|#seskanalı|kapat] — Temp voice sistemi")
@commands.has_permissions(administrator=True)
@commands.bot_has_permissions(administrator=True)
async def tempvoice(ctx, *, arg=None):
    if arg and arg.lower() in ("kapat","off","0"):
        db.q("DELETE FROM tempvoice WHERE guild_id=?", (ctx.guild.id,))
        return await rp(ctx, OK("TEMP VOICE", "Sistem kapatıldı."))
    if arg:
        ch = await commands.VoiceChannelConverter().convert(ctx, arg)
        db.q("INSERT OR REPLACE INTO tempvoice(guild_id,trigger_ch,category_id) VALUES(?,?,?)",
             (ctx.guild.id, ch.id, ch.category.id if ch.category else None))
        await rp(ctx, OK("TEMP VOICE", ch.mention + " artık tetikleyici kanal.\nGiren üye kendi odasını kurar!"))
    else:
        cat = await ctx.guild.create_category("ÖZEL ODALAR")
        trig = await cat.create_voice_channel("➕ Katıl & Oda Kur")
        await trig.set_permissions(ctx.guild.default_role, view_channel=True, connect=True, speak=False)
        db.q("INSERT OR REPLACE INTO tempvoice(guild_id,trigger_ch,category_id) VALUES(?,?,?)", (ctx.guild.id, trig.id, cat.id))
        await rp(ctx, OK("TEMP VOICE KURULDU", trig.mention + " kanalına giren **kendi özel odasını** kurar.\nOda boşalınca otomatik silinir.\nYönetim: DM paneli veya `k!oda`"))
@kategori("sys")
@bot.command(name="ticket", help="<kapat/bilgi/listele> — Ticket yönetimi")
async def ticket(ctx, i: str = "bilgi"):
    i = i.lower()
    t = db.one("SELECT * FROM tickets WHERE channel_id=?", (ctx.channel.id,))
    if i == "kapat":
        if not t: return await rp(ctx, ER("BURASI TICKET DEĞİL", "Ticket kanalında kullan."))
        if not (ctx.author.guild_permissions.administrator or ctx.author.id == t["user_id"]):
            return await rp(ctx, ER("YETKİ YOK"))
        db.q("UPDATE tickets SET status='closed' WHERE channel_id=?", (ctx.channel.id,))
        await guild_log_send(ctx.guild, head("ticket", "TALEP KAPANDI") + "\n" + e("dot") + " Kanal: #" + ctx.channel.name +
                             "\n" + e("dot") + " Kullanıcı: <@" + str(t["user_id"]) + "> • Kapatan: " + ctx.author.mention)
        await rp(ctx, WN("KAPATILIYOR", "10 sn...")); await asyncio.sleep(10)
        try: await ctx.channel.delete()
        except Exception: pass
    elif i == "bilgi":
        if not t: return await rp(ctx, ER("BURASI TICKET DEĞİL"))
        await rp(ctx, head("ticket", "TALEP BİLGİSİ") + "\n" + KV([
            (e("dot")+"Kullanıcı", "<@"+str(t["user_id"])+">"),
            (e("dot")+"Üstlenen", ("<@"+str(t["claimed_by"])+">") if t["claimed_by"] else "—"),
            (e("dot")+"Durum", t["status"])]))
    elif i == "listele":
        if not ctx.author.guild_permissions.administrator: return await rp(ctx, ER("YETKİ YOK"))
        rs = db.all("SELECT * FROM tickets WHERE guild_id=? AND status='open'", (ctx.guild.id,))
        await rp(ctx, head("ticket", "AÇIK TALEPLER (" + str(len(rs)) + ")") + "\n" +
                 ("\n".join(e("arrow") + " <#" + str(r["channel_id"]) + "> • <@" + str(r["user_id"]) + ">" for r in rs) if rs else "Yok."))
    else:
        await rp(ctx, ER("KOMUT", "`k!ticket kapat / bilgi / listele`"))
@kategori("sys")
@bot.command(name="başvuru-ayarla", aliases=["basvuru-ayarla"], help="<#log> [@rol]")
@commands.has_permissions(administrator=True)
async def başvuru_ayarla(ctx, ch: discord.TextChannel, role: discord.Role = None):
    db.q("INSERT OR REPLACE INTO app_settings(guild_id,log_ch,staff_role) VALUES(?,?,?)", (ctx.guild.id, ch.id, role.id if role else None))
    await rp(ctx, OK("BAŞVURU SİSTEMİ", "Log: " + ch.mention + (("\nRol: " + role.mention) if role else "") + "\nPanel: `k!başvuru-panel`"))
@kategori("sys")
@bot.command(name="başvuru-panel", aliases=["basvuru-panel"], help="Panel gönderir")
@commands.has_permissions(administrator=True)
async def başvuru_panel(ctx):
    await rp(ctx, head("clip", "YETKİLİ BAŞVURU") + "\n### Ekibimize katılmak ister misin?\n" + e("check") + " 14+ yaş\n" + e("check") + " Haftada 20+ saat aktif\n" + e("check") + " Discord deneyimi\n\n**Butona tıkla, formu doldur!**", AppOpenView())
    try: await ctx.message.delete()
    except Exception: pass
@kategori("sys")
@bot.command(name="başvurular", aliases=["basvurular"], help="Bekleyenler")
@commands.has_permissions(administrator=True)
async def başvurular(ctx):
    rs = db.all("SELECT * FROM applications WHERE guild_id=? AND status='pending'", (ctx.guild.id,))
    if not rs: return await rp(ctx, e("clip") + " Bekleyen yok.")
    await rp(ctx, head("clip", "BEKLEYEN (" + str(len(rs)) + ")") + "\n" + "\n".join(e("arrow") + " **#" + str(r["id"]) + "** <@" + str(r["user_id"]) + "> • " + r["ts"][:10] for r in rs[:10]))
@kategori("sys")
@bot.command(name="başvurum", aliases=["basvurum"], help="Durumun")
async def başvurum(ctx):
    r = db.one("SELECT * FROM applications WHERE guild_id=? AND user_id=? ORDER BY id DESC", (ctx.guild.id, ctx.author.id))
    if not r: return await rp(ctx, e("clip") + " Başvurun yok.")
    st = {"pending": e("time")+" Beklemede", "accepted": e("check")+" Kabul", "rejected": e("cross")+" Red"}.get(r["status"], r["status"])
    await rp(ctx, head("clip", "BAŞVURU #" + str(r["id"])) + "\n" + st + " • " + r["ts"][:16].replace("T"," "))
@kategori("sys")
@bot.command(name="otocevap", help="<ekle/sil/liste>")
@commands.has_permissions(administrator=True)
async def otocevap(ctx, i: str, *, a=None):
    g = ctx.guild.id
    if i.lower() in ("ekle","add"):
        if not a or "|" not in a: return await rp(ctx, ER("ÖRNEK", "`k!otocevap ekle selam | Aleyküm selam!`"))
        t, r = [p.strip() for p in a.split("|", 1)]
        db.q("INSERT OR REPLACE INTO auto_replies(guild_id,trigger,response) VALUES(?,?,?)", (g, t.lower(), r[:500]))
        await rp(ctx, OK("OTO CEVAP", "`"+t.lower()+"` → "+r[:60]))
    elif i.lower() in ("sil","remove"):
        db.q("DELETE FROM auto_replies WHERE guild_id=? AND trigger=?", (g, (a or "").lower())); await rp(ctx, OK("SİLİNDİ"))
    else:
        rs = db.all("SELECT * FROM auto_replies WHERE guild_id=?", (g,))
        await rp(ctx, head("robot", "OTO CEVAP (" + str(len(rs)) + ")") + "\n" + "\n".join(e("arrow") + " `"+r["trigger"]+"` → "+r["response"][:50] for r in rs[:15]))
@kategori("sys")
@bot.command(name="sayaç", help="<hedef> <#kanal|kapat>")
@commands.has_permissions(administrator=True)
async def sayaç(ctx, h: int, ch: discord.TextChannel = None):
    if ch is None or h <= 0:
        db.q("DELETE FROM counters WHERE guild_id=?", (ctx.guild.id,)); return await rp(ctx, OK("SAYAÇ", "Kapalı."))
    db.q("INSERT OR REPLACE INTO counters(guild_id,target,channel_id,reached) VALUES(?,?,?,0)", (ctx.guild.id, h, ch.id))
    await rp(ctx, OK("SAYAÇ", "Hedef **" + str(h) + "** • " + ch.mention))
@kategori("sys")
@bot.command(name="seviyerol", help="<ekle/sil/liste> [seviye] [@rol]")
@commands.has_permissions(administrator=True)
async def seviyerol(ctx, i: str, s: int = 0, role: discord.Role = None):
    g = ctx.guild.id
    if i.lower() in ("ekle","add"):
        if not role: return await rp(ctx, ER("ÖRNEK", "`k!seviyerol ekle 5 @Rol`"))
        db.q("INSERT INTO level_roles(guild_id,level,role_id) VALUES(?,?,?)", (g, s, role.id)); await rp(ctx, OK("SEVİYE ROL", "Lv.**"+str(s)+"** → "+role.mention))
    elif i.lower() in ("sil","remove"):
        db.q("DELETE FROM level_roles WHERE guild_id=? AND level=?", (g, s)); await rp(ctx, OK("SİLİNDİ", "Lv."+str(s)))
    else:
        rs = db.all("SELECT * FROM level_roles WHERE guild_id=? ORDER BY level", (g,))
        await rp(ctx, head("chartup", "SEVİYE ROLLERİ") + "\n" + ("\n".join(e("arrow") + " Lv.**"+str(r["level"])+"** → <@&"+str(r["role_id"])+">" for r in rs) if rs else "Kayıt yok."))
@kategori("sys")
@bot.command(name="sunuculog", help="<#kanal|kapat>")
@commands.has_permissions(administrator=True)
async def sunuculog(ctx, ch: discord.TextChannel = None):
    if ch is None:
        db.q("DELETE FROM guild_logs WHERE guild_id=?", (ctx.guild.id,)); return await rp(ctx, OK("LOG", "Kapalı."))
    db.q("INSERT OR REPLACE INTO guild_logs(guild_id,channel_id) VALUES(?,?)", (ctx.guild.id, ch.id))
    await rp(ctx, OK("LOG", ch.mention + "\nMesaj silme/düzenleme, giriş-çıkış, nick"))

# ═══════════════════════════════════════════════════════════════════════════
# 💰 EKONOMİ
# ═══════════════════════════════════════════════════════════════════════════
@kategori("eco")
@bot.command(name="cüzdan", aliases=["balance","para"], help="Cüzdan")
async def cüzdan(ctx, u: discord.Member = None):
    u = u or ctx.author; ensure_user(u.id, str(u))
    d = db.one("SELECT * FROM users WHERE user_id=?", (u.id,))
    await rp(ctx, head("money", u.display_name.upper() + " CÜZDAN") + "\n" + KV([
        (e("coin")+" Coin", format(d["coins"], ",").replace(",", ".")), (e("star")+" İtibar", d["rep"]),
        (e("pro")+" Pro", "✅" if d["pro"] else "❌")]))
@kategori("eco")
@bot.command(name="zenginler", aliases=["coinlb","zengin"], help="Coin sıralaması")
async def zenginler(ctx):
    rs = db.all("SELECT * FROM users ORDER BY coins DESC LIMIT 10")
    if not rs: return await rp(ctx, e("coin") + " Veri yok.")
    L = [head("coin", "EN ZENGİNLER")]
    md = ["🥇","","🥉"]
    for i, r in enumerate(rs):
        L.append((md[i] if i < 3 else "**" + str(i+1) + ".**") + " <@" + str(r["user_id"]) + "> ─ **" + format(r["coins"], ",").replace(",", ".") + "** coin")
    await rp(ctx, "\n".join(L))
@kategori("eco")
@bot.command(name="günlük", aliases=["gunluk","daily"], help="Günlük coin")
@commands.cooldown(1, 86400, commands.BucketType.user)
async def günlük(ctx):
    ensure_user(ctx.author.id, str(ctx.author))
    u = db.one("SELECT * FROM users WHERE user_id=?", (ctx.author.id,))
    b = random.randint(150, 400) + (250 if u["pro"] else 0)
    db.q("UPDATE users SET coins=coins+? WHERE user_id=?", (b, ctx.author.id))
    await rp(ctx, head("gift", "GÜNLÜK ÖDÜL") + "\n**+" + str(b) + " coin**" + (" (" + e("pro") + " bonus dahil)" if u["pro"] else ""))
@kategori("eco")
@bot.command(name="çalış", aliases=["calis","work"], help="Çalış")
@commands.cooldown(1, 1800, commands.BucketType.user)
async def çalış(ctx):
    j, a, b = random.choice([("Yazılım",200,400),("Tasarım",150,300),("İçerik",180,350),("Pizzacı",100,220),("Şoför",120,260),("Ders",160,320)])
    p = random.randint(a, b); db.q("UPDATE users SET coins=coins+? WHERE user_id=?", (p, ctx.author.id))
    await rp(ctx, e("gear") + " **" + j + "** işinde çalıştın → **" + str(p) + " coin**")
@kategori("eco")
@bot.command(name="balık", aliases=["fish"], help="Balık (5dk)")
@commands.cooldown(1, 300, commands.BucketType.user)
async def balık(ctx):
    n, v = random.choice([("Levrek",40),("Nemo",90),("Balon",60),("Köpekbalığı",200),("Ahtapot",120),("Çizme",5)])
    db.q("UPDATE users SET coins=coins+? WHERE user_id=?", (v, ctx.author.id))
    await rp(ctx, e("fish") + " **" + n + "** yakaladın → **" + str(v) + " coin**")
@kategori("eco")
@bot.command(name="maden", aliases=["mine"], help="Maden (5dk)")
@commands.cooldown(1, 300, commands.BucketType.user)
async def maden(ctx):
    n, v = random.choice([("Kömür",30),("Bakır",60),("Gümüş",110),("Altın",200),("Elmas",400),("Taş",5)])
    db.q("UPDATE users SET coins=coins+? WHERE user_id=?", (v, ctx.author.id))
    await rp(ctx, e("pick") + " **" + n + "** kazdın → **" + str(v) + " coin**")
@kategori("eco")
@bot.command(name="soy", aliases=["rob"], help="<@üye>")
@commands.cooldown(1, 600, commands.BucketType.user)
async def soy(ctx, u: discord.Member):
    if u.id == ctx.author.id or u.bot: return await rp(ctx, ER("GEÇERSİZ"))
    ensure_user(u.id, str(u))
    t = db.one("SELECT coins FROM users WHERE user_id=?", (u.id,)); me = db.one("SELECT coins FROM users WHERE user_id=?", (ctx.author.id,))
    if t["coins"] < 200: return await rp(ctx, ER("FAKİR HEDEF"))
    if random.random() < 0.45:
        s = random.randint(50, min(500, t["coins"]))
        db.q("UPDATE users SET coins=coins-? WHERE user_id=?", (s, u.id)); db.q("UPDATE users SET coins=coins+? WHERE user_id=?", (s, ctx.author.id))
        await rp(ctx, head("fire", "SOYGUN BAŞARILI") + "\n**+" + str(s) + " coin**")
    else:
        f = min(me["coins"], random.randint(50, 200))
        db.q("UPDATE users SET coins=coins-? WHERE user_id=?", (f, ctx.author.id))
        await rp(ctx, head("cross", "YAKALANDIN") + "\n**-" + str(f) + " coin** ceza")
@kategori("eco")
@bot.command(name="transfer", help="<@üye> <miktar>")
async def transfer(ctx, u: discord.Member, m: int):
    if m <= 0 or u.id == ctx.author.id: return await rp(ctx, ER("GEÇERSİZ"))
    ensure_user(u.id, str(u)); me = db.one("SELECT coins FROM users WHERE user_id=?", (ctx.author.id,))
    if me["coins"] < m: return await rp(ctx, ER("YETERSİZ"))
    db.q("UPDATE users SET coins=coins-? WHERE user_id=?", (m, ctx.author.id)); db.q("UPDATE users SET coins=coins+? WHERE user_id=?", (m, u.id))
    await rp(ctx, head("coin", "TRANSFER") + "\n" + ctx.author.mention + " → " + u.mention + " **" + str(m) + " coin**")
@kategori("eco")
@bot.command(name="bahis", aliases=["bet"], help="<miktar> x2")
@commands.cooldown(1, 10, commands.BucketType.user)
async def bahis(ctx, m: int):
    if m <= 0: return await rp(ctx, ER("GEÇERSİZ"))
    me = db.one("SELECT coins FROM users WHERE user_id=?", (ctx.author.id,))
    if me["coins"] < m: return await rp(ctx, ER("YETERSİZ"))
    w = random.random() < 0.5
    db.q("UPDATE users SET coins=coins+? WHERE user_id=?", (m if w else -m, ctx.author.id))
    await rp(ctx, (head("star", "KAZANDIN") + "\n**+" + str(m*2) + " coin**") if w else (head("cross", "KAYBETTİN") + "\n**-" + str(m) + " coin**"))
@kategori("eco")
@bot.command(name="market", aliases=["shop"], help="Market")
async def market(ctx):
    v = View(); v.add_item(Button(label="Satın Al", url=SUPPORT_URL, style=discord.ButtonStyle.link, emoji="🛒"))
    await rp(ctx, head("gift", "KATRE MARKET") + "\n" + KV([
        (e("pro")+" Pro 30 gün", "50.000 coin"), (e("palette")+" Rank rengi", "5.000 coin (Pro)"),
        (e("star")+" +10 Rep", "2.500 coin"), (e("tag")+" Tag", "7.500 coin (Pro)")]), v)

# ═══════════════════════════════════════════════════════════════════════════
# 🎮 EĞLENCE
# ═══════════════════════════════════════════════════════════════════════════
@kategori("fun")
@bot.command(name="8ball", help="<soru>")
async def eightball(ctx, *, s):
    await rp(ctx, e("search") + " **" + s[:80] + "**\n" + e("dot") + " " + random.choice(["Evet!", "Büyük ihtimal", "Belki", "Hayır", "Asla!", "Yüksek şans"]))
@kategori("fun")
@bot.command(name="yazıtura", aliases=["coin"], help="Yazı tura")
async def yazıtura(ctx): await rp(ctx, e("dice") + " Sonuç: **" + random.choice(["YAZI", "TURA"]) + "**")
@kategori("fun")
@bot.command(name="zar", help="Zar")
async def zar(ctx):
    r = random.randint(1, 6)
    await rp(ctx, e("dice") + " Zar: **" + str(r) + "** " + ["⚀","","⚂","⚃","⚄","⚅"][r-1])
@kategori("fun")
@bot.command(name="aşk", aliases=["ask","love"], help="<@üye> aşk ölçer")
async def aşk(ctx, u: discord.Member):
    p = random.randint(0, 100)
    m = "Yok bu iş..." if p < 30 else ("Fena değil!" if p < 60 else ("Güzel çift!" if p < 85 else "RUH İKİZİ!"))
    await rp(ctx, head("heart", "AŞK ÖLÇER") + "\n" + ctx.author.mention + " " + e("heart") + " " + u.mention + "\n" + bar(p) + "\n**" + m + "**")
@kategori("fun")
@bot.command(name="slot", help="Slot")
async def slot(ctx):
    s = ["🍒","","🍇","💎","7️⃣","🔔"]; r = [random.choice(s) for _ in range(3)]
    w = len(set(r)) == 1
    await rp(ctx, head("slot", "SLOT") + "\n┃ " + " ┃ ".join(r) + " ┃\n" + ("**JACKPOT!**" if w else "Olmadı..."))
@kategori("fun")
@bot.command(name="seç", aliases=["sec"], help="<a> <b>...")
async def seç(ctx, *, s):
    o = s.split()
    if len(o) < 2: return await rp(ctx, ER("GEÇERSİZ", "2+ seçenek"))
    await rp(ctx, e("target") + " Seçimim: **" + random.choice(o) + "**")
@kategori("fun")
@bot.command(name="oylama", aliases=["anket"], help="<soru> [| A | B | C...] — Butonlu anket (tek oy)")
@commands.cooldown(1, 5, commands.BucketType.user)
async def oylama(ctx, *, s):
    try:
        parts = [x.strip() for x in s.split("|")]
        question = parts[0][:200] or "Anket"
        opts = [x[:60] for x in parts[1:6] if x] if len(parts) > 1 else ["Evet", "Hayır", "Çekimser"]
        if len(opts) < 2:
            return await rp(ctx, ER("GEÇERSİZ", "En az 2 seçenek gir:\n`k!oylama Soru | A | B`"))
        cur = db.q("INSERT INTO polls(guild_id,channel_id,message_id,question,options,votes,status,creator,ts) VALUES(?,?,0,?,?,'{}','active',?,?)",
                   (ctx.guild.id, ctx.channel.id, question, json.dumps(opts, ensure_ascii=False), ctx.author.id, datetime.datetime.now().isoformat()))
        pid = cur.lastrowid
        p = db.one("SELECT * FROM polls WHERE id=?", (pid,))
        view = PollView(pid, opts)
        msg = await ctx.send(poll_content(p), view=view)
        db.q("UPDATE polls SET message_id=? WHERE id=?", (msg.id, pid))
        bot.add_view(view)
    except Exception as ex:
        traceback.print_exc()
        await rp(ctx, ER("ANKET HATASI", "```\n" + str(ex)[:300] + "\n```"))
@kategori("fun")
@bot.command(name="ppboyu", aliases=["pp"], help="Efsanevi ölçüm")
@commands.cooldown(1, 5, commands.BucketType.user)
async def ppboyu(ctx, u: discord.Member = None):
    u = u or ctx.author
    n = (u.id % 18) + 3
    await rp(ctx, head("game", "PP ÖLÇÜM") + "\n" + u.mention + "\n`8" + "=" * n + "D`  (**" + str(n + 2) + " cm**)")
@kategori("fun")
@bot.command(name="burç", help="<burç> — Günlük yorum")
async def burç(ctx, *, b):
    B = {"koç":"Enerjin tavan yapacak, liderlik sende.","boğa":"Maddi konularda şanslı bir gün.","ikizler":"İletişim trafiği yoğun, haberler var.","yengeç":"Aile içinde tatlı bir sürpriz.",
         "aslan":"Sahne senin, parlamaktan çekinme.","başak":"Detaylar başarıyı getirecek.","terazi":"Karar verirken kalbini dinle.","akrep":"Gizli bir konu açığa çıkıyor.",
         "yay":"Yeni bir macera kapıda.","oğlak":"Emeklerinin karşılığını alıyorsun.","kova":"Fikirlerin ilgi çekecek, paylaş.","balık":"Sezgilerin çok güçlü, onlara güven."}
    k = b.lower().strip()
    if k not in B: return await rp(ctx, ER("GEÇERSİZ BURÇ", "`" + "`, `".join(B.keys()) + "`"))
    await rp(ctx, head("star", k.upper() + " BURCU") + "\n" + B[k] + "\n" + e("spark") + " Şanslı sayın: **" + str(random.randint(1, 99)) + "**")
@kategori("fun")
@bot.command(name="quiz", aliases=["bilgi"], help="Yarışma +75 coin")
@commands.cooldown(1, 10, commands.BucketType.user)
async def quiz(ctx):
    Q = [("Türkiye'nin başkenti?",["İstanbul","Ankara","İzmir","Bursa"],1),("En büyük gezegen?",["Dünya","Mars","Jüpiter","Satürn"],2),
         ("Discord.py dili?",["Java","Python","C++","Go"],1),("Suyun formülü?",["H2O","CO2","O2","NaCl"],0),
         ("Bir yılda kaç gün?",["360","365","370","355"],1),("1 KB kaç byte?",["1000","1024","512","2048"],1)]
    q, o, a = random.choice(Q)
    view = View(timeout=30); emj = ["1️⃣","2️⃣","3️⃣","4️⃣"]
    def cb(i):
        async def _c(it):
            if i == a:
                ensure_user(it.user.id, str(it.user))
                db.q("UPDATE users SET coins=coins+75, xp=xp+20 WHERE user_id=?", (it.user.id,))
                await it.response.send_message(OK("DOĞRU", "+75 coin +20 XP"), ephemeral=True)
            else:
                await it.response.send_message(ER("YANLIŞ", "Doğru: **" + o[a] + "**"), ephemeral=True)
            for b in view.children: b.disabled = True
            try: await it.message.edit(view=view)
            except Exception: pass
        return _c
    for i, op in enumerate(o):
        b = Button(label=op[:78], style=discord.ButtonStyle.primary, emoji=emj[i]); b.callback = cb(i); view.add_item(b)
    await rp(ctx, head("game", "BİLGİ YARIŞMASI") + "\n### " + q + "\n" + e("time") + " 30 sn • " + e("gift") + " +75 coin", view)
@kategori("fun")
@bot.command(name="tahmin", help="<1-10> +100")
@commands.cooldown(1, 15, commands.BucketType.user)
async def tahmin(ctx, s: int):
    if not 1 <= s <= 10: return await rp(ctx, ER("GEÇERSİZ", "1-10"))
    t = random.randint(1, 10)
    if s == t:
        db.q("UPDATE users SET coins=coins+100 WHERE user_id=?", (ctx.author.id,)); await rp(ctx, head("star", "BİLDİN") + "\n**+100 coin**")
    else: await rp(ctx, head("cross", "BİLEMEDİN") + "\nTutulan: **" + str(t) + "**")
@kategori("fun")
@bot.command(name="evlen", help="<@üye>")
async def evlen(ctx, u: discord.Member):
    if u.id == ctx.author.id or u.bot: return await rp(ctx, ER("GEÇERSİZ"))
    if db.one("SELECT 1 FROM marriages WHERE user1=? OR user2=? OR user1=? OR user2=?", (ctx.author.id,ctx.author.id,u.id,u.id)):
        return await rp(ctx, ER("ZATEN EVLİ"))
    db.q("INSERT INTO marriages(user1,user2,since) VALUES(?,?,?)", (ctx.author.id, u.id, datetime.datetime.now().isoformat()))
    await rp(ctx, head("ring", "EVLENDİNİZ") + "\n" + ctx.author.mention + " " + e("heart") + " " + u.mention + "\nMutluluklar!")
@kategori("fun")
@bot.command(name="boşan", help="Boşan")
async def boşan(ctx):
    db.q("DELETE FROM marriages WHERE user1=? OR user2=?", (ctx.author.id, ctx.author.id))
    await rp(ctx, head("broken", "BOŞANDIN"))
@kategori("fun")
@bot.command(name="eş", help="[<@üye>]")
async def eş(ctx, u: discord.Member = None):
    u = u or ctx.author
    m = db.one("SELECT * FROM marriages WHERE user1=? OR user2=?", (u.id, u.id))
    if not m: return await rp(ctx, e("broken") + " " + u.mention + " bekar.")
    o = m["user2"] if m["user1"] == u.id else m["user1"]
    await rp(ctx, e("ring") + " " + u.mention + " " + e("heart") + " <@" + str(o) + ">")

# ═══════════════════════════════════════════════════════════════════════════
# 🎉 ÇEKİLİŞ
# ═══════════════════════════════════════════════════════════════════════════
@kategori("give")
@bot.command(name="çekiliş", aliases=["cekilis"], help="<süre> <kazanan> <ödül>")
@commands.has_permissions(administrator=True)
async def çekiliş(ctx, s: str, k: int, *, ö):
    try: dk = parse_sure(s)
    except Exception: return await rp(ctx, ER("SÜRE", "`k!çekiliş 60m 1 Nitro` • `2h` • `1d`"))
    if dk < 1 or k < 1: return await rp(ctx, ER("GEÇERSİZ"))
    end = datetime.datetime.now() + datetime.timedelta(minutes=dk)
    gw = {"prize": ö, "winners": k, "end_time": end.timestamp(), "host": ctx.author.id, "participants": "[]"}
    msg = await rp(ctx, gw_start_text(gw), bot.gwv)
    db.q("INSERT INTO giveaways(message_id,guild_id,channel_id,prize,winners,end_time,host) VALUES(?,?,?,?,?,?,?)",
         (msg.id, ctx.guild.id, ctx.channel.id, ö, k, end.timestamp(), ctx.author.id))
@kategori("give")
@bot.command(name="çekilişler", aliases=["cekilisler"], help="Aktifler")
async def çekilişler(ctx):
    rs = db.all("SELECT * FROM giveaways WHERE guild_id=? AND status='active'", (ctx.guild.id,))
    if not rs: return await rp(ctx, e("give") + " Aktif çekiliş yok.")
    await rp(ctx, head("give", "AKTİF (" + str(len(rs)) + ")") + "\n" + "\n".join(
        e("arrow") + " **" + g["prize"] + "** ─ " + str(len(json.loads(g["participants"]))) + " katılım • <t:" + str(int(g["end_time"])) + ":R>" for g in rs))
@kategori("give")
@bot.command(name="çekilişbitir", aliases=["cekilisbitir"], help="<id>")
@commands.has_permissions(administrator=True)
async def çekilişbitir(ctx, m: int):
    g = db.one("SELECT * FROM giveaways WHERE message_id=? AND guild_id=?", (m, ctx.guild.id))
    if not g or g["status"] != "active": return await rp(ctx, ER("BULUNAMADI"))
    await finalize_giveaway(bot, m); await rp(ctx, OK("BİTİRİLDİ"))

# ═══════════════════════════════════════════════════════════════════════════
# 💎 PRO
# ═══════════════════════════════════════════════════════════════════════════
@kategori("pro")
@bot.command(name="pro", help="Pro durum")
async def pro(ctx, u: discord.Member = None):
    u = u or ctx.author; ensure_user(u.id, str(u))
    d = db.one("SELECT * FROM users WHERE user_id=?", (u.id,))
    await rp(ctx, head("pro", "KATRE PRO") + "\n" + KV([
        (e("dot")+" Durum", "PRO ÜYE" if d["pro"] else "Yok"),
        (e("log")+" Log kayıt", len(db.all("SELECT 1 FROM pro_logs WHERE user_id=?", (u.id,))))]) +
        "\n\n" + e("star") + " **AYRICALIKLAR**\n" + e("arrow") + " `prooda` özel ses odası\n" + e("arrow") + " `prorenk` rank rengi\n" +
        e("arrow") + " `protag` rozet\n" + e("arrow") + " `proxp` 2x XP\n" + e("arrow") + " `prostats` detay\n" +
        e("arrow") + " `proyazı` havalı yazı\n" + e("arrow") + " `proembed` özel embed\n" + e("arrow") + " günlük +250 coin")
@kategori("pro")
@bot.command(name="prooda", help="Özel oda (PRO)")
@is_pro()
async def prooda(ctx):
    c = discord.utils.get(ctx.guild.categories, name="PRO ODALAR") or await ctx.guild.create_category("PRO ODALAR")
    try: await c.set_permissions(ctx.guild.default_role, view_channel=False)
    except Exception: pass
    ch = await ctx.guild.create_voice_channel(ctx.author.display_name, category=c)
    await ch.set_permissions(ctx.author, connect=True, manage_channels=True, move_members=True)
    await rp(ctx, OK("PRO ODA", ch.mention + " hazır!"))
@kategori("pro")
@bot.command(name="prorenk", help="<hex> (PRO)")
@is_pro()
async def prorenk(ctx, h: str):
    h = h.lstrip("#")
    if len(h) != 6: return await rp(ctx, ER("ÖRNEK", "ff0000"))
    try: int(h, 16)
    except ValueError: return await rp(ctx, ER("GEÇERSİZ HEX"))
    db.q("UPDATE users SET pro_color=? WHERE user_id=?", (h, ctx.author.id))
    await rp(ctx, OK("RENK", "#" + h.upper()))
@kategori("pro")
@bot.command(name="prostats", help="Detay (PRO)")
@is_pro()
async def prostats(ctx):
    d = db.one("SELECT * FROM users WHERE user_id=?", (ctx.author.id,))
    await rp(ctx, head("chart", "PRO İSTATİSTİK") + "\n" + KV([
        (e("dot")+" Mesaj", d["messages"]), (e("chartup")+" Seviye", d["level"]), (e("spark")+" XP", d["xp"]),
        (e("coin")+" Coin", d["coins"]), (e("star")+" Rep", d["rep"]), (e("bolt")+" 2x", "✅" if d["xp2"] else "❌")]))
@kategori("pro")
@bot.command(name="proyazı", help="<metin> (PRO)")
@is_pro()
async def proyazı(ctx, *, m): await rp(ctx, head("pen", "PRO YAZI") + "\n" + fancy(m[:200]))
@kategori("pro")
@bot.command(name="proembed", help="<başlık> | <metin> | <hex> (PRO)")
@is_pro()
async def proembed(ctx, *, a):
    p = [x.strip() for x in a.split("|")]
    if len(p) < 2: return await rp(ctx, ER("ÖRNEK", "Duyuru | Merhaba | ff0000"))
    await rp(ctx, "### " + p[0][:100] + "\n" + DIV + "\n" + p[1][:1500] + "\n" + e("pro") + " " + ctx.author.display_name)
@kategori("pro")
@bot.command(name="protag", help="<metin> (PRO)")
@is_pro()
async def protag(ctx, *, t):
    db.q("UPDATE users SET pro_tag=? WHERE user_id=?", (t[:12], ctx.author.id)); await rp(ctx, OK("TAG", t[:12]))
@kategori("pro")
@bot.command(name="proxp", help="2x (PRO)")
@is_pro()
async def proxp(ctx):
    u = db.one("SELECT xp2 FROM users WHERE user_id=?", (ctx.author.id,))
    n = 0 if u["xp2"] else 1
    db.q("UPDATE users SET xp2=? WHERE user_id=?", (n, ctx.author.id))
    await rp(ctx, OK("BOOST", "2x AÇIK" if n else "2x KAPALI"))

# ═══════════════════════════════════════════════════════════════════════════
# 👑 OWNER + HALF OWNER
# ═══════════════════════════════════════════════════════════════════════════
@kategori("owner")
@bot.command(name="halfowner", aliases=["coowner","yardımcıowner"], help="<ayarla/kaldır/bilgi/liste> [@üye]")
async def halfowner(ctx, i: str = "bilgi", u: discord.Member = None):
    i = i.lower()
    if i in ("ayarla","set","ekle"):
        if ctx.author.id != OWNER_ID: return
        if not u: return await rp(ctx, ER("EKSİK", "`k!halfowner ayarla @üye`"))
        if u.id == OWNER_ID: return await rp(ctx, ER("OLMAZ", "Zaten owner."))
        db.q("INSERT OR REPLACE INTO half_owners(user_id,since,added_by) VALUES(?,?,?)",
             (u.id, datetime.datetime.now().isoformat(), ctx.author.id))
        await rp(ctx, OK("HALF OWNER", u.mention + " artık **sadece Pro yönetebilir** (prover/proal/prologlar)."))
    elif i in ("kaldır","remove"):
        if ctx.author.id != OWNER_ID: return
        if not u: return await rp(ctx, ER("EKSİK", "`k!halfowner kaldır @üye`"))
        db.q("DELETE FROM half_owners WHERE user_id=?", (u.id,))
        await rp(ctx, WN("KALDIRILDI", u.mention))
    elif i == "liste":
        rs = db.all("SELECT * FROM half_owners")
        await rp(ctx, head("owner", "HALF OWNER LİSTESİ") + "\n" + ("\n".join(e("arrow") + " <@" + str(r["user_id"]) + "> • " + r["since"][:10] for r in rs) if rs else "Yok."))
    else:
        me = db.one("SELECT * FROM half_owners WHERE user_id=?", (ctx.author.id,))
        L = [head("owner", "HALF OWNER BİLGİ"),
             "Half Owner, bot sahibinin yardımcı yöneticisidir.", "",
             e("star") + " **YETKİLERİ:**",
             e("arrow") + " `k!prover` — Pro üyelik verir",
             e("arrow") + " `k!proal` — Pro üyeliği alır",
             e("arrow") + " `k!prologlar` — Pro loglarını görür", "",
             e("cross") + " **YAPAMAZ:**",
             e("arrow") + " Bakım, prefix, blacklist, duyuru, eval, emoji ve diğer owner komutları"]
        L += ["", (e("check") + " Sen bir **Half Owner**'sın! • Desde: " + me["since"][:10]) if me else (e("info") + " Sen half owner değilsin.")]
        await rp(ctx, "\n".join(L))
@kategori("owner")
@bot.command(name="sahip", aliases=["owner","panel"], help="Owner paneli")
@is_owner()
async def sahip(ctx):
    await rp(ctx, head("owner", "OWNER PANELİ") + "\n### Hoş geldin Owner!\n" + KV([
        (e("dot")+" Sunucu", len(bot.guilds)), (e("dot")+" Kullanıcı", sum(g.member_count or 0 for g in bot.guilds)),
        (e("gear")+" Bakım", "AÇIK" if is_maintenance() else "KAPALI"), (e("log")+" Bulut yedek", "AÇIK" if BACKUP_CH else "KAPALI"),
        (e("owner")+" Half Owner", len(db.all("SELECT 1 FROM half_owners"))), (e("spark")+" Sürüm", "v" + BOT_VERSION)]) +
        "\n\n`k!prover` `k!proal` `k!prologlar` `k!halfowner` `k!emoji` `k!yedek` `k!bakım` `k!restart` `k!eval`", OwnerPanelView(bot))
@kategori("owner")
@bot.command(name="bakım", aliases=["bakim"], help="<aç/kapat> — Bakım modu")
@is_owner()
async def bakım(ctx, mod: str = None):
    if mod is None or mod.lower() in ("kapat", "off", "0"):
        db.q("UPDATE owner_settings SET maintenance=0 WHERE id=1")
        await rp(ctx, OK("BAKIM MODU", "Kapatıldı. Komutlar herkese açık."))
    else:
        db.q("UPDATE owner_settings SET maintenance=1 WHERE id=1")
        await rp(ctx, OK("BAKIM MODU", "Açıldı. Kullanıcılar komut yazınca **BAKIMDAYIZ** mesajı görür."))
@kategori("owner")
@bot.command(name="restart", aliases=["yenidenbaşlat","rb"], help="Botu yeniden başlatır")
@is_owner()
async def restart(ctx):
    await rp(ctx, OK("RESTART", "Bot yeniden başlatılıyor... (butonlar ve ayarlar korunur)"))
    await asyncio.sleep(1)
    os.execv(sys.executable, [sys.executable] + sys.argv)
@kategori("owner")
@bot.command(name="yedek", help="<durum/kaydet/yükle> [emoji/pro/settings] — Bulut yedek")
@is_owner()
async def yedek(ctx, i: str = "durum", hedef: str = None):
    if not BACKUP_CH: return await rp(ctx, ER("KANAL YOK", "Railway Variables → `BACKUP_CHANNEL_ID` ekle."))
    i = i.lower()
    if i == "kaydet":
        await push_backup(bot, "emoji", EMO_CACHE)
        await push_backup(bot, "pro", pro_snapshot())
        await push_backup(bot, "settings", settings_snapshot())
        _HASH["emoji"] = json.dumps(EMO_CACHE, sort_keys=True)
        _HASH["pro"] = json.dumps(pro_snapshot(), sort_keys=True, default=str)
        _HASH["set"] = json.dumps(settings_snapshot(), sort_keys=True, default=str)
        await rp(ctx, OK("YEDEKLENDİ", "Emoji + Pro + **Ayarlar** bulut kanalına yazıldı."))
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
            if d: msg.append("ayar: " + str(settings_restore(d)))
        _HASH["emoji"] = json.dumps(EMO_CACHE, sort_keys=True)
        _HASH["pro"] = json.dumps(pro_snapshot(), sort_keys=True, default=str)
        _HASH["set"] = json.dumps(settings_snapshot(), sort_keys=True, default=str)
        await rp(ctx, OK("GERİ YÜKLENDİ", ", ".join(msg) or "Yedek bulunamadı."))
    else:
        await rp(ctx, head("log", "YEDEK DURUMU") + "\n" + KV([
            (e("dot")+" Kanal", "<#" + str(BACKUP_CH) + ">"), (e("dot")+" Emoji slot", len(EMO_CACHE)),
            (e("dot")+" Pro üye", len(db.all("SELECT 1 FROM users WHERE pro=1"))),
            (e("dot")+" Pro log", len(db.all("SELECT 1 FROM pro_logs"))),
            (e("dot")+" Ayar kaydı", sum(len(v) for v in settings_snapshot().values())),
            (e("time")+" Kontrol", "her 1 dk (otomatik)")]))
@kategori("owner")
@bot.command(name="güncelleme-kanal", aliases=["guncelleme-kanal"], help="<#kanal|kapat> — Bildirim kanalı")
@is_owner()
async def güncelleme_kanal(ctx, ch: discord.TextChannel = None):
    if ch is None:
        db.q("DELETE FROM bot_meta WHERE key='update_ch'")
        await rp(ctx, OK("GÜNCELLEME KANALI", "Bildirimler kapatıldı."))
    else:
        db.q("INSERT OR REPLACE INTO bot_meta(key,value) VALUES('update_ch',?)", (str(ch.id),))
        await rp(ctx, OK("GÜNCELLEME KANALI", "Yeni sürümler " + ch.mention + " kanalına duyurulacak."))
@kategori("owner")
@bot.command(name="sürüm", aliases=["surum","version"], help="Bot sürümü + yenilikler")
async def sürüm(ctx):
    await rp(ctx, head("logo", "SÜRÜM v" + BOT_VERSION) + "\n" +
             "\n".join(e("arrow") + " " + n for n in CHANGELOG.get(BOT_VERSION, [])[:10]))
@kategori("owner")
@bot.command(name="güncelleme-test", help="Örnek bildirim gönderir")
@is_owner()
async def güncelleme_test(ctx):
    notes = CHANGELOG.get(BOT_VERSION, [])
    L = [e("party") + " **KATRE BOT GÜNCELLENDİ! (test)**", DIV,
         e("spark") + " Sürüm: **v" + BOT_VERSION + "**", ""] + \
        [e("arrow") + " " + n for n in notes] + ["", e("logo") + " Katre Bot"]
    await rp(ctx, "\n".join(L))
@kategori("owner")
@bot.command(name="emoji", help="<ayarla/yakala/oto/liste/sıfırla/slotlar/rehber>")
@is_owner()
async def emoji_cmd(ctx, i: str = "rehber", slot: str = None, *, val=None):
    i = i.lower()
    if i in ("ayarla","set"):
        if not slot or not val: return await rp(ctx, ER("KULLANIM", "`k!emoji ayarla <slot> <emoji>`"))
        if "<" not in val: return await rp(ctx, ER("HATA", "Özel emoji yapıştır: `<a:tick:109...>`"))
        slot = slot.lower()
        if slot not in SLOTS: return await rp(ctx, ER("SLOT", "`k!emoji slotlar`"))
        db.q("INSERT OR REPLACE INTO emojis(slot,emoji) VALUES(?,?)", (slot, val)); refresh_emojis()
        await rp(ctx, OK("AYARLANDI", "`"+slot+"` → "+val))
    elif i == "yakala":
        if not slot: return await rp(ctx, ER("KULLANIM", "`k!emoji yakala check` (mesajı yanıtla)"))
        slot = slot.lower()
        if slot not in SLOTS: return await rp(ctx, ER("SLOT", "`k!emoji slotlar`"))
        ref = ctx.message.reference; mg = ref.resolved if ref else None
        if not mg: return await rp(ctx, ER("YANIT YOK", "Emoji mesajını yanıtla!"))
        f = str(mg.emojis[0]) if mg.emojis else None
        if not f:
            mm = re.search(r"<a?:[a-zA-Z0-9_]+:\d+>", mg.content or ""); f = mm.group(0) if mm else None
        if not f: return await rp(ctx, ER("EMOJİ YOK", "Mesajda özel emoji yok."))
        db.q("INSERT OR REPLACE INTO emojis(slot,emoji) VALUES(?,?)", (slot, f)); refresh_emojis()
        await rp(ctx, OK("YAKALANDI", "`"+slot+"` → "+f))
    elif i == "oto":
        mp = auto_map_emojis(ctx.guild)
        if not mp: return await rp(ctx, WN("BULUNAMADI", "Eşleşen özel emoji yok.\nManuel: `k!emoji yakala <slot>`"))
        await rp(ctx, OK("OTOMATİK EMOJİ", "**" + str(len(mp)) + "** slot dolduruldu!\n" +
                         "\n".join(e("arrow") + " `"+k+"` → "+v for k, v in list(mp.items())[:20])))
    elif i == "rehber":
        await rp(ctx, head("info", "SLOT REHBERİ (Türkçe)") + "\n" + "\n".join("`"+k+"` → "+v for k, v in SLOT_TR.items()))
    elif i in ("liste","list"):
        rs = db.all("SELECT * FROM emojis")
        await rp(ctx, head("star", "AYARLI (" + str(len(rs)) + "/" + str(len(SLOTS)) + ")") + "\n" + ("\n".join(e("arrow")+" `"+r["slot"]+"` "+r["emoji"] for r in rs) if rs else "Boş. `k!emoji oto` dene!"))
    elif i in ("sıfırla","reset"):
        if slot in (None,"tümü","all"): db.q("DELETE FROM emojis")
        else: db.q("DELETE FROM emojis WHERE slot=?", (slot.lower(),))
        refresh_emojis(); await rp(ctx, OK("SIFIRLANDI"))
    elif i in ("slotlar","slots"):
        await rp(ctx, head("info", "SLOTLAR") + "\n`" + "`, `".join(SLOTS.keys()) + "`")
    else:
        await rp(ctx, ER("KOMUT", "`ayarla/yakala/oto/liste/sıfırla/slotlar/rehber`"))
@kategori("owner")
@bot.command(name="prover", help="<@üye> [gün] — Owner + Half Owner")
@is_half()
async def prover(ctx, u: discord.Member, g: int = 30):
    ensure_user(u.id, str(u))
    ex = (datetime.datetime.now() + datetime.timedelta(days=g)).isoformat()
    db.q("UPDATE users SET pro=1, pro_expiry=? WHERE user_id=?", (ex, u.id)); pro_log(u.id, "VERİLDİ", g, ctx.author.id)
    await rp(ctx, OK("PRO VERİLDİ", u.mention + " • **" + str(g) + " gün** • ☁️ buluta yedeklendi"))
    try: await u.send(OK("PRO OLDUN", str(g) + " gün PRO!"))
    except Exception: pass
@kategori("owner")
@bot.command(name="proal", help="<@üye> — Owner + Half Owner")
@is_half()
async def proal(ctx, u: discord.Member):
    db.q("UPDATE users SET pro=0, pro_expiry=NULL WHERE user_id=?", (u.id)); pro_log(u.id, "ALINDI", 0, ctx.author.id)
    await rp(ctx, WN("PRO ALINDI", u.mention + " • ☁️ loglandı"))
@kategori("owner")
@bot.command(name="prologlar", help="Kalıcı pro geçmişi — Owner + Half Owner")
@is_half()
async def prologlar(ctx, u: discord.User = None):
    rs = db.all("SELECT * FROM pro_logs WHERE user_id=? ORDER BY id DESC LIMIT 15", (u.id,)) if u else db.all("SELECT * FROM pro_logs ORDER BY id DESC LIMIT 15")
    if not rs: return await rp(ctx, e("log") + " Kayıt yok.")
    await rp(ctx, head("log", "PRO LOG (" + str(len(rs)) + ")") + "\n" + "\n".join(
        e("arrow") + " **#" + str(r["id"]) + " " + r["action"] + "** <@" + str(r["user_id"]) + "> • " + r["ts"][:16].replace("T"," ") +
        (" • " + str(r["days"]) + "g" if r["days"] else "") for r in rs))
@kategori("owner")
@bot.command(name="prefix", help="<prefix>")
@is_owner()
async def prefix(ctx, y: str):
    ensure_server(ctx.guild.id); db.q("UPDATE servers SET prefix=? WHERE guild_id=?", (y, ctx.guild.id))
    await rp(ctx, OK("PREFIX", "`" + y + "`"))
@kategori("owner")
@bot.command(name="blacklist", aliases=["bl"], help="<ekle/çıkar> <@üye>")
@is_owner()
async def blacklist(ctx, i: str, u: discord.User, *, s="—"):
    if i.lower() in ("ekle","add"):
        db.q("INSERT OR REPLACE INTO blacklist(user_id,reason) VALUES(?,?)", (u.id, s)); await rp(ctx, OK("KARALİSTE", u.mention))
    elif i.lower() in ("çıkar","cikar","remove"):
        db.q("DELETE FROM blacklist WHERE user_id=?", (u.id,)); await rp(ctx, OK("ÇIKARILDI", u.mention))
    else: await rp(ctx, ER("KOMUT", "ekle/çıkar"))
@kategori("owner")
@bot.command(name="durum", aliases=["status"], help="<metin>")
@is_owner()
async def durum(ctx, *, m):
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name=m))
    await rp(ctx, OK("DURUM", m[:80]))
@kategori("owner")
@bot.command(name="sunucular", aliases=["guilds"], help="Liste")
@is_owner()
async def sunucular(ctx):
    rs = sorted(bot.guilds, key=lambda g: -(g.member_count or 0))
    await rp(ctx, head("owner", "SUNUCULAR (" + str(len(rs)) + ")") + "\n" + "\n".join(e("arrow") + " **" + g.name + "** ─ " + str(g.member_count) for g in rs[:15]))
@kategori("owner")
@bot.command(name="eval", aliases=["py"], help="<kod>")
@is_owner()
async def eval_cmd(ctx, *, code):
    env = {"bot": bot, "ctx": ctx, "db": db, "discord": discord, "guild": ctx.guild, "author": ctx.author}
    buf = io.StringIO()
    fn = "async def __f():\n" + textwrap.indent(code, "    ")
    try:
        exec(compile(fn, "<e>", "exec"), env)
        with redirect_stdout(buf): await env["__f"]()
        await ctx.send("```py\n" + (buf.getvalue()[:1900] or "OK") + "\n```")
    except Exception as ex:
        await ctx.send("```py\n" + str(ex)[:1900] + "\n```")

if __name__ == "__main__":
    bot.run(BOT_TOKEN)
