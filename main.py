# ═══════════════════════════════════════════════════════════════════
#  💧 KATRE BOT v4.8 — BÖLÜM 1/2 • BUTON FIX • V2 TEST • YENİ PRO KOMUTLAR
#  ENV: BOT_TOKEN, OWNER_ID, SUPPORT_URL, BACKUP_CHANNEL_ID
#  requirements.txt: discord.py>=2.6.0
# ═══════════════════════════════════════════════════════════════════
import discord
from discord.ext import commands, tasks
from discord.ui import View, Button, Select, Modal, TextInput
import sqlite3, os, sys, json, random, asyncio, datetime, traceback, textwrap, io, re
from collections import deque
from contextlib import redirect_stdout
try:
    from discord.ui import Container, TextDisplay
    HAS_V2 = True
except Exception:
    Container = None; TextDisplay = None; HAS_V2 = False
BOT_TOKEN = os.getenv("BOT_TOKEN", "BURAYA_TOKEN")
OWNER_ID = int(os.getenv("OWNER_ID", "0"))
SUPPORT_URL = os.getenv("SUPPORT_URL", "https://discord.gg/katre")
DB_PATH = os.getenv("DB_PATH", "katre.db")
BACKUP_CH = int(os.getenv("BACKUP_CHANNEL_ID", "0"))
MARKER = "#KATRE_YEDEK"
DIV = "──────────────────────────────"
PAGE_SIZE = 15
BOT_VERSION = "4.8"
CHANGELOG = {"4.8": ["🔘 Buton 'zamanında yanıt vermedi' hatası KÖKTEN çözüldü", "🧩 k!v2test: Components V2 teşhisi", "💎 Yeni PRO komutlar: prorol, probonus, probanner, proşans", "📋 Kategori seçimi SELECT menü"]}

class DB:
    def __init__(self, path):
        self.conn = sqlite3.connect(path, check_same_thread=False); self.conn.row_factory = sqlite3.Row
        c = self.conn.cursor()
        c.executescript("""
        CREATE TABLE IF NOT EXISTS servers(guild_id INTEGER PRIMARY KEY, prefix TEXT DEFAULT 'k!', welcome_ch INTEGER, auto_role INTEGER, rank_on INTEGER DEFAULT 1, joined_at TEXT);
        CREATE TABLE IF NOT EXISTS users(user_id INTEGER PRIMARY KEY, name TEXT, xp INTEGER DEFAULT 0, level INTEGER DEFAULT 1, coins INTEGER DEFAULT 0, messages INTEGER DEFAULT 0, warnings INTEGER DEFAULT 0, pro INTEGER DEFAULT 0, pro_expiry TEXT, pro_color TEXT, pro_tag TEXT, xp2 INTEGER DEFAULT 0, birthday TEXT, notes TEXT DEFAULT '[]', rep INTEGER DEFAULT 0);
        CREATE TABLE IF NOT EXISTS owner_settings(id INTEGER PRIMARY KEY DEFAULT 1, maintenance INTEGER DEFAULT 0);
        CREATE TABLE IF NOT EXISTS bot_meta(key TEXT PRIMARY KEY, value TEXT);
        CREATE TABLE IF NOT EXISTS half_owners(user_id INTEGER PRIMARY KEY, since TEXT, added_by INTEGER);
        CREATE TABLE IF NOT EXISTS giveaways(message_id INTEGER PRIMARY KEY, guild_id INTEGER, channel_id INTEGER, prize TEXT, winners INTEGER, end_time REAL, participants TEXT DEFAULT '[]', status TEXT DEFAULT 'active', host INTEGER);
        CREATE TABLE IF NOT EXISTS tickets(channel_id INTEGER PRIMARY KEY, guild_id INTEGER, user_id INTEGER, claimed_by INTEGER, status TEXT DEFAULT 'open');
        CREATE TABLE IF NOT EXISTS role_menus(menu_id TEXT PRIMARY KEY, guild_id INTEGER, role_ids TEXT);
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
        CREATE TABLE IF NOT EXISTS emojis(slot TEXT PRIMARY KEY, emoji TEXT);
        CREATE TABLE IF NOT EXISTS tempvoice(guild_id INTEGER PRIMARY KEY, trigger_ch INTEGER, category_id INTEGER);
        CREATE TABLE IF NOT EXISTS temp_channels(channel_id INTEGER PRIMARY KEY, owner_id INTEGER, guild_id INTEGER);
        CREATE TABLE IF NOT EXISTS punishments(id INTEGER PRIMARY KEY AUTOINCREMENT, guild_id INTEGER, user_id INTEGER, type TEXT, reason TEXT, by_id INTEGER, ts TEXT, duration INTEGER);
        CREATE TABLE IF NOT EXISTS punish_config(guild_id INTEGER PRIMARY KEY, mute_at INTEGER DEFAULT 3, ban_at INTEGER DEFAULT 5);
        CREATE TABLE IF NOT EXISTS polls(id INTEGER PRIMARY KEY AUTOINCREMENT, guild_id INTEGER, channel_id INTEGER, message_id INTEGER DEFAULT 0, question TEXT, options TEXT, votes TEXT DEFAULT '{}', status TEXT DEFAULT 'active', creator INTEGER, ts TEXT);
        INSERT OR IGNORE INTO owner_settings(id) VALUES (1);""")
        for t, col, ty in (("users","pro_tag","TEXT"),("users","xp2","INTEGER DEFAULT 0"),("tickets","claimed_by","INTEGER"),("afk","mentions","INTEGER DEFAULT 0")):
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
SET_TABLES = ["servers","punish_config","protections","app_settings","counters","level_roles","guild_logs","auto_replies","badwords","tempvoice"]
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
# 🎨 UI: V2 METİN KARTI + LEGACY PANEL (BUTON/SELECT GARANTİLİ)
# ═══════════════════════════════════════════════════════════════════
def head(i, t): return "## " + e(i) + " " + t + "\n" + DIV
def OK(t, b=None): return head("check", t) + ("\n" + b if b else "")
def ER(t, b=None): return head("cross", t) + ("\n" + b if b else "")
def WN(t, b=None): return head("warn", t) + ("\n" + b if b else "")
def KV(ps): return "\n".join("> " + k + " › **" + str(v) + "**" for k, v in ps)
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

async def v2_text(sendable, text, eph=False):
    if HAS_V2:
        try:
            con = Container(); con.add_item(TextDisplay(text))
            if eph: return await sendable.send(view=con, ephemeral=True)
            return await sendable.send(view=con)
        except Exception:
            pass
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
    """✅ v4.8 FIX: Interaction'a kesin yanıt (response → followup zinciri)"""
    if HAS_V2:
        try:
            con = Container(); con.add_item(TextDisplay(text))
            return await it.response.send_message(view=con, ephemeral=True)
        except Exception: pass
    try: return await it.response.send_message(text, ephemeral=True)
    except Exception:
        try: return await it.followup.send(text, ephemeral=True)
        except Exception: return None
async def guild_log_send(g, t):
    r = db.one("SELECT channel_id FROM guild_logs WHERE guild_id=?", (g.id,))
    if r and r["channel_id"]:
        ch = g.get_channel(r["channel_id"])
        if ch:
            try: await rp_ch(ch, t); return True
            except Exception: pass
    return False
async def check_update(bot):
    try:
        row = db.one("SELECT value FROM bot_meta WHERE key='update_ch'")
        cid = int(row["value"]) if row else int(os.getenv("UPDATE_CHANNEL_ID", "0") or 0)
        if not cid: return
        ch = bot.get_channel(cid) or await bot.fetch_channel(cid)
        last = db.one("SELECT value FROM bot_meta WHERE key='version'"); lv = last["value"] if last else None
        if lv == BOT_VERSION: return
        L = [e("party") + " **KATRE BOT GÜNCELLENDİ!**", DIV, e("spark") + " Yeni sürüm: **v" + BOT_VERSION + "**", ""]
        ns = CHANGELOG.get(BOT_VERSION, [])
        if ns: L += [e("star") + " **GELENLER:**"] + [e("arrow") + " " + n for n in ns]
        L += ["", e("logo") + " Katre Bot • `k!yardım`"]
        await rp_ch(ch, "\n".join(L)); db.q("INSERT OR REPLACE INTO bot_meta(key,value) VALUES('version',?)", (BOT_VERSION,))
    except Exception: traceback.print_exc()

class OwnerOnly(commands.CheckFailure): pass
class ProOnly(commands.CheckFailure): pass
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
CAT_DESC = {"genel":"Rank, profil, avatar, snipe, AFK, oda","mod":"Ban, kick, unban, mute, uyarı, oto-ceza, koruma","sys":"Başvuru, ticket, temp voice, oto-cevap, sayaç, log","eco":"Coin, günlük, çalışma, balık, maden, market","fun":"Quiz, slot, aşk, anket ve oyunlar","give":"Butonlu çekiliş, reroll, sonuç paneli","pro":"Pro oda, rol, bonus, banner, şans","owner":"Owner + Half Owner paneli"}
def cat_count(b, k): return len([c for c in b.commands if getattr(c, "kategori", None) == k])
def help_content(bot):
    L = ["## " + e("logo") + " " + bot.user.name.upper() + " YARDIM MENÜSÜ", DIV, "Selam, ben **" + bot.user.name + "!** " + e("spark"),
         "Toplam **" + str(len(bot.commands)) + "** komutum var; `k!komut` şeklinde çalışır.", "",
         e("star") + " **Kategoriler:** aşağıdaki **menüden** seç!", ""]
    for k in CATS: L += [e(k) + " **" + CATS[k][1] + "** ─ `" + str(cat_count(bot, k)) + "` komut", "> " + CAT_DESC[k], ""]
    L.append(e("link") + " Destek: " + SUPPORT_URL); return "\n".join(L)
def cat_content(bot, key, page=1):
    cmds = sorted([c for c in bot.commands if getattr(c, "kategori", None) == key], key=lambda x: x.name)
    pages = [cmds[i:i+PAGE_SIZE] for i in range(0, len(cmds), PAGE_SIZE)] or [[]]
    page = max(1, min(page, len(pages)))
    base = ["## " + e(key) + " " + CATS[key][1].upper(), "> " + str(len(cmds)) + " komut ─ **Sayfa " + str(page) + "/" + str(len(pages)) + "**", DIV, ""]
    body = "\n".join(base + [e("arrow") + " `k!" + c.name + "` ─ " + (c.help or "") for c in pages[page-1]])
    if len(body) > 1900: body = "\n".join(base + ["`k!" + c.name + "`" for c in pages[page-1]])
    return (body + "\n\n" + e("info") + " ◀ ▶ gezin • 🏠 ana menü")[:1990]

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
            await sendv_eph(it, head("chart", "İSTATİSTİK") + "\n" + KV([("Sunucu", len(self.bot.guilds)), ("Kullanıcı", sum(g.member_count or 0 for g in self.bot.guilds)), ("Komut", len(self.bot.commands)), ("Uptime", up), ("Ping", str(round(self.bot.latency*1000))+"ms")]))
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
            self.value = False; self.stop(); await editv(it, Panel(ER("İPTAL")))
        self.btn("Onayla", y, style=discord.ButtonStyle.success, emoji=e("check"))
        self.btn("Vazgeç", n, style=discord.ButtonStyle.secondary, emoji=e("cross"))

class OwnerPanel(Panel):
    def __init__(self, bot, text):
        super().__init__(text, timeout=None); self.bot = bot
        async def g(it):
            if it.user.id != OWNER_ID: await sendv_eph(it, ER("YETKİ YOK")); return False
            return True
        async def bk(it):
            if not await g(it): return
            cur = db.one("SELECT maintenance FROM owner_settings WHERE id=1")["maintenance"]
            db.q("UPDATE owner_settings SET maintenance=? WHERE id=1", (0 if cur else 1,))
            await sendv_eph(it, head("gear", "BAKIM") + "\n**" + ("AÇIK" if not cur else "KAPALI") + "**")
        async def st(it):
            if not await g(it): return
            await sendv_eph(it, head("chart", "OWNER") + "\n" + KV([("Sunucu", len(self.bot.guilds)), ("Pro", len(db.all("SELECT 1 FROM users WHERE pro=1"))), ("Half", len(db.all("SELECT 1 FROM half_owners"))), ("Bakım", "AÇIK" if is_maintenance() else "KAPALI")]))
        async def gl(it):
            if not await g(it): return
            await sendv_eph(it, head("owner", "SUNUCULAR") + "\n" + "\n".join(e("arrow") + " **" + x.name + "** " + str(x.member_count) for x in sorted(self.bot.guilds, key=lambda y: -(y.member_count or 0))[:10]))
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
                try: await rp_ch(ch, head("owner", "DUYURU") + "\n" + self.txt.value); ok += 1
                except Exception: pass
        await it.response.send_message(OK("DUYURU", str(ok) + "/" + str(len(it.client.guilds))), ephemeral=True)

def gw_start(gw):
    return ("## " + e("give") + " ÇEKİLİŞ: " + gw["prize"] + "\n" + DIV + "\n" + KV([(e("star")+"Kazanan", str(gw["winners"]) + " kişi"), (e("dot")+"Katılım", str(len(json.loads(gw["participants"]))) + " kişi"), (e("time")+"Bitiş", "<t:" + str(int(gw["end_time"])) + ":R>"), (e("dot")+"Düzenleyen", "<@" + str(gw["host"]) + ">")]) + "\n\n" + e("spark") + " **KATIL** butonuna bas!")
def gw_end(gw, men, parts):
    return ("## " + e("star") + " " + gw["prize"] + "\n" + DIV + "\n**ÇEKİLİŞ BİTTİ**\n\n" + KV([(e("star")+"Kazanan", men), (e("dot")+"Katılım", str(len(parts)) + " kişi"), (e("dot")+"Düzenleyen", "<@" + str(gw["host"]) + ">"), (e("alarm")+"Bitti", "<t:" + str(int(datetime.datetime.now().timestamp())) + ":F>")]) + "\n\n" + e("party") + " Kazananlar duyuruda.")
class GiveawayPanel(Panel):
    def __init__(self, bot, text):
        super().__init__(text, timeout=None); self.bot = bot
        async def join(it):
            gw = db.one("SELECT * FROM giveaways WHERE message_id=?", (it.message.id,))
            if not gw or gw["status"] != "active": return await sendv_eph(it, ER("AKTİF DEĞİL"))
            p = json.loads(gw["participants"])
            if str(it.user.id) in p: return await sendv_eph(it, WN("ZATEN KATILDIN"))
            p.append(str(it.user.id)); db.q("UPDATE giveaways SET participants=? WHERE message_id=?", (json.dumps(p), it.message.id))
            nt = gw_start(dict(gw, participants=json.dumps(p)))
            try: await it.message.edit(content=nt, view=GiveawayPanel(self.bot, nt))
            except Exception: pass
            await sendv_eph(it, OK("KATILDIN", gw["prize"]))
        async def leave(it):
            gw = db.one("SELECT * FROM giveaways WHERE message_id=?", (it.message.id,))
            if not gw or gw["status"] != "active": return await sendv_eph(it, ER("AKTİF DEĞİL"))
            p = json.loads(gw["participants"])
            if str(it.user.id) not in p: return await sendv_eph(it, WN("KATILMAMIŞSIN"))
            p.remove(str(it.user.id)); db.q("UPDATE giveaways SET participants=? WHERE message_id=?", (json.dumps(p), it.message.id))
            await sendv_eph(it, WN("AYRILDIN"))
        async def end(it):
            if not it.user.guild_permissions.administrator: return await sendv_eph(it, ER("YETKİ YOK"))
            await finalize_giveaway(self.bot, it.message.id); await sendv_eph(it, OK("BİTİRİLDİ"))
        async def rr(it):
            if not it.user.guild_permissions.administrator: return await sendv_eph(it, ER("YETKİ YOK"))
            gw = db.one("SELECT * FROM giveaways WHERE message_id=?", (it.message.id,))
            if not gw: return
            p = json.loads(gw["participants"])
            if not p: return await sendv_eph(it, ER("KATILIMCI YOK"))
            w = self.bot.get_user(int(random.choice(p)))
            await rp_ch(it.channel, head("dice", "REROLL") + "\n" + (w.mention if w else "?")); await it.response.defer()
        async def ext(it):
            if not it.user.guild_permissions.administrator: return await sendv_eph(it, ER("YETKİ YOK"))
            gw = db.one("SELECT * FROM giveaways WHERE message_id=?", (it.message.id,))
            if not gw or gw["status"] != "active": return await sendv_eph(it, ER("AKTİF DEĞİL"))
            nw = gw["end_time"] + 3600; db.q("UPDATE giveaways SET end_time=? WHERE message_id=?", (nw, it.message.id))
            nt = gw_start(dict(gw, end_time=nw))
            try: await it.message.edit(content=nt, view=GiveawayPanel(self.bot, nt))
            except Exception: pass
            await sendv_eph(it, OK("UZATILDI"))
        async def can(it):
            if not it.user.guild_permissions.administrator: return await sendv_eph(it, ER("YETKİ YOK"))
            gw = db.one("SELECT * FROM giveaways WHERE message_id=?", (it.message.id,))
            if not gw: return
            db.q("UPDATE giveaways SET status='cancelled' WHERE message_id=?", (it.message.id,))
            try: await it.message.edit(content=ER("İPTAL", gw["prize"]), view=None)
            except Exception: pass
            await sendv_eph(it, WN("İPTAL"))
        self.btn("Katıl", join, style=discord.ButtonStyle.success, emoji=e("party"), cid="kg_join", row=0)
        self.btn("Ayrıl", leave, style=discord.ButtonStyle.secondary, cid="kg_leave", row=0)
        self.btn("Bitir", end, emoji="🏁", cid="kg_end", row=1)
        self.btn("Yeniden Çek", rr, style=discord.ButtonStyle.secondary, emoji=e("dice"), cid="kg_rr", row=1)
        self.btn("+1 Saat", ext, style=discord.ButtonStyle.success, emoji=e("time"), cid="kg_ext", row=1)
        self.btn("İptal", can, style=discord.ButtonStyle.danger, cid="kg_can", row=1)
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
                if not p or p["status"] != "active": return await sendv_eph(it, ER("KAPALI"))
                v = json.loads(p["votes"])
                for lst in v.values():
                    if str(it.user.id) in lst: return await sendv_eph(it, WN("ZATEN OY VERDİN"))
                v.setdefault(str(idx), []).append(str(it.user.id)); db.q("UPDATE polls SET votes=? WHERE id=?", (json.dumps(v), self.pid))
                p2 = db.one("SELECT * FROM polls WHERE id=?", (self.pid,))
                try: await it.message.edit(content=poll_content(p2), view=PollPanel(self.pid, json.loads(p2["options"]), poll_content(p2)))
                except Exception: pass
                await sendv_eph(it, OK("OYUN KAYDEDİLDİ", json.loads(p["options"])[idx]))
            self.btn(op[:60], cb, emoji=e("dot"), cid="poll_" + str(pid) + "_" + str(i), row=0)
        async def close(it):
            p = db.one("SELECT * FROM polls WHERE id=?", (self.pid,))
            if not p: return
            if not (it.user.id == p["creator"] or (it.guild and it.guild.permissions_for(it.user).administrator)): return await sendv_eph(it, ER("YETKİ YOK"))
            if p["status"] != "active": return await sendv_eph(it, WN("ZATEN KAPALI"))
            db.q("UPDATE polls SET status='closed' WHERE id=?", (self.pid,))
            p2 = db.one("SELECT * FROM polls WHERE id=?", (self.pid,))
            try: await it.message.edit(content=poll_content(p2), view=PollPanel(self.pid, json.loads(p2["options"]), poll_content(p2)))
            except Exception: pass
            await sendv_eph(it, OK("KAPATILDI"))
        self.btn("Anketi Kapat", close, style=discord.ButtonStyle.danger, emoji=e("lock"), cid="pollc_" + str(pid), row=1)

class RoleMenuPanel(Panel):
    def __init__(self, mid, roles, text):
        super().__init__(text, timeout=None)
        for i, (rid, nm) in enumerate(roles):
            async def cb(it, r_id=rid):
                r = it.guild.get_role(r_id)
                if not r: return await sendv_eph(it, ER("ROL YOK"))
                if r in it.user.roles: await it.user.remove_roles(r); m = e("cross") + " " + r.name
                else: await it.user.add_roles(r); m = e("check") + " " + r.name
                await sendv_eph(it, head("shield", "ROL") + "\n" + m)
            self.btn(nm[:78], cb, style=discord.ButtonStyle.secondary, emoji="🎭", cid="kr_" + mid + "_" + str(rid), row=i // 5)

class TicketModal(Modal, title="Destek Talebi"):
    konu = TextInput(label="Konu", max_length=100); acik = TextInput(label="Açıklama", style=discord.TextStyle.paragraph)
    async def on_submit(self, it):
        if db.one("SELECT 1 FROM tickets WHERE user_id=? AND status='open'", (it.user.id,)): return await it.response.send_message(ER("AÇIK TALEBİN VAR"), ephemeral=True)
        g = it.guild; cat = discord.utils.get(g.categories, name="DESTEK") or await g.create_category("DESTEK")
        ow = {g.default_role: discord.PermissionOverwrite(view_channel=False), it.user: discord.PermissionOverwrite(view_channel=True, send_messages=True, attach_files=True), g.me: discord.PermissionOverwrite(view_channel=True, send_messages=True, manage_channels=True, manage_messages=True)}
        try: ch = await g.create_text_channel("destek-" + it.user.name.lower(), category=cat, overwrites=ow)
        except Exception as ex: return await it.response.send_message(ER("KANAL HATASI", str(ex)[:150]), ephemeral=True)
        db.q("INSERT INTO tickets(channel_id,guild_id,user_id) VALUES(?,?,?)", (ch.id, g.id, it.user.id))
        await rp_ch(ch, head("ticket", "DESTEK TALEBİ") + "\n" + KV([(e("dot")+"Kullanıcı", it.user.mention), (e("clip")+"Konu", self.konu.value), (e("pen")+"Açıklama", self.acik.value[:400])]) + "\n\n" + e("info") + " Yetkililer birazdan burada.", TicketPanel(" "))
        await it.response.send_message(OK("TALEP", ch.mention), ephemeral=True)
class TicketOpenPanel(Panel):
    def __init__(self, text):
        super().__init__(text, timeout=None)
        async def o(it): await it.response.send_modal(TicketModal())
        async def mine(it):
            t = db.one("SELECT * FROM tickets WHERE user_id=? AND status='open'", (it.user.id,))
            await sendv_eph(it, OK("TALEBİN", "<#" + str(t["channel_id"]) + ">") if t else WN("TALEBİN YOK"))
        self.btn("Talep Oluştur", o, emoji=e("ticket"), cid="kt_open", row=0)
        self.btn("Talebim Var mı?", mine, style=discord.ButtonStyle.secondary, emoji=e("search"), cid="kt_mine", row=0)
class TicketPanel(Panel):
    def __init__(self, text):
        super().__init__(text, timeout=None)
        async def claim(it):
            if not it.user.guild_permissions.manage_messages: return await sendv_eph(it, ER("YETKİ YOK"))
            db.q("UPDATE tickets SET claimed_by=? WHERE channel_id=?", (it.user.id, it.channel.id))
            await rp_ch(it.channel, head("shield", "ÜSTLENİLDİ") + "\n" + it.user.mention); await it.response.defer()
        async def close(it):
            t = db.one("SELECT * FROM tickets WHERE channel_id=?", (it.channel.id,))
            if not t: return await sendv_eph(it, ER("BULUNAMADI"))
            if not (it.user.guild_permissions.administrator or it.user.id == t["user_id"]): return await sendv_eph(it, ER("YETKİ YOK"))
            db.q("UPDATE tickets SET status='closed' WHERE channel_id=?", (it.channel.id,))
            await guild_log_send(it.guild, head("ticket", "KAPANDI") + "\n#" + it.channel.name)
            await sendv_eph(it, WN("KAPATILIYOR", "10 sn")); await asyncio.sleep(10)
            try: await it.channel.delete()
            except Exception: pass
        self.btn("Üstlendim", claim, emoji="👮", cid="kt_claim", row=0)
        self.btn("Kapat", close, style=discord.ButtonStyle.danger, emoji=e("lock"), cid="kt_close", row=0)

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
        if db.one("SELECT 1 FROM applications WHERE guild_id=? AND user_id=? AND status='pending'", (it.guild.id, it.user.id)): return await it.response.send_message(WN("BEKLEYEN BAŞVURUN VAR"), ephemeral=True)
        cur = db.q("INSERT INTO applications(guild_id,user_id,answers,ts) VALUES(?,?,?,?)", (it.guild.id, it.user.id, json.dumps({"y":self.yas.value,"d":self.den.value,"n":self.ned.value,"a":self.akt.value}), datetime.datetime.now().isoformat()))
        aid = cur.lastrowid; ch = it.guild.get_channel(st["log_ch"])
        if ch:
            m = await rp_ch(ch, head("clip", "BAŞVURU #" + str(aid)) + "\n" + KV([(e("dot")+"Kim", it.user.mention), (e("cake")+"Yaş", self.yas.value), (e("shield")+"Deneyim", self.den.value[:250]), (e("heart")+"Neden", self.ned.value[:250])]), AppReviewPanel(aid, " "))
            db.q("UPDATE applications SET message_id=? WHERE id=?", (m.id, aid))
        await it.response.send_message(OK("ALINDI", "#" + str(aid)), ephemeral=True)
class AppReviewPanel(Panel):
    def __init__(self, aid, text):
        super().__init__(text, timeout=None); self.aid = aid
        async def yk(it):
            ok = it.user.guild_permissions.administrator
            st = db.one("SELECT * FROM app_settings WHERE guild_id=?", (it.guild.id,))
            if st and st["staff_role"]:
                r = it.guild.get_role(st["staff_role"])
                if r and r in it.user.roles: ok = True
            if not ok: await sendv_eph(it, ER("YETKİ YOK")); return False
            return True
        async def acc(it):
            if not await yk(it): return
            a = db.one("SELECT * FROM applications WHERE id=?", (self.aid,))
            if not a or a["status"] != "pending": return await sendv_eph(it, WN("İŞLENMİŞ"))
            db.q("UPDATE applications SET status='accepted' WHERE id=?", (self.aid,))
            st = db.one("SELECT * FROM app_settings WHERE guild_id=?", (it.guild.id,))
            r = it.guild.get_role(st["staff_role"]) if st and st["staff_role"] else None
            mb = it.guild.get_member(a["user_id"])
            if r and mb:
                try: await mb.add_roles(r, reason="Başvuru")
                except Exception: pass
            try: await it.message.edit(content=OK("İŞLENDİ", "Kabul"), view=None)
            except Exception: pass
            u = it.client.get_user(a["user_id"])
            if u:
                try: await u.send(OK("KABUL", it.guild.name))
                except Exception: pass
            await sendv_eph(it, OK("KABUL", "<@" + str(a["user_id"]) + ">"))
        async def rej(it):
            if not await yk(it): return
            a = db.one("SELECT * FROM applications WHERE id=?", (self.aid,))
            if not a or a["status"] != "pending": return await sendv_eph(it, WN("İŞLENMİŞ"))
            db.q("UPDATE applications SET status='rejected' WHERE id=?", (self.aid,))
            try: await it.message.edit(content=ER("İŞLENDİ", "Red"), view=None)
            except Exception: pass
            await sendv_eph(it, ER("RED", "<@" + str(a["user_id"]) + ">"))
        self.btn("Kabul", acc, style=discord.ButtonStyle.success, emoji=e("check"), cid="ka_acc_" + str(aid))
        self.btn("Red", rej, style=discord.ButtonStyle.danger, emoji=e("cross"), cid="ka_rej_" + str(aid))

class TVNameModal(Modal, title="Oda İsmi"):
    def __init__(self, cid):
        super().__init__(); self.cid = cid; self.ni = TextInput(label="Yeni isim", max_length=50); self.add_item(self.ni)
    async def on_submit(self, it):
        ch = it.client.get_channel(self.cid)
        if not ch: return await it.response.send_message(ER("ODA YOK"), ephemeral=True)
        await ch.edit(name=self.ni.value[:50]); await it.response.send_message(OK("İSİM", ch.name), ephemeral=True)
class TVLimitModal(Modal, title="Oda Limiti"):
    def __init__(self, cid):
        super().__init__(); self.cid = cid; self.li = TextInput(label="Limit 0-99", max_length=2); self.add_item(self.li)
    async def on_submit(self, it):
        ch = it.client.get_channel(self.cid)
        if not ch: return await it.response.send_message(ER("ODA YOK"), ephemeral=True)
        try: n = max(0, min(99, int(self.li.value)))
        except ValueError: n = 0
        await ch.edit(user_limit=n or None); await it.response.send_message(OK("LİMİT", str(n or "sınırsız")), ephemeral=True)
class TVPanel(Panel):
    def __init__(self, cid, text):
        super().__init__(text, timeout=None); self.cid = cid
        async def oc(it):
            row = db.one("SELECT * FROM temp_channels WHERE channel_id=?", (self.cid,))
            if not row or row["owner_id"] != it.user.id: await sendv_eph(it, ER("YETKİ", "Sahibi değilsin.")); return None
            ch = it.client.get_channel(self.cid)
            if not ch: await sendv_eph(it, ER("ODA YOK")); return None
            return ch
        async def lock(it):
            ch = await oc(it)
            if not ch: return
            lk = ch.overwrites_for(ch.guild.default_role).connect is False
            await ch.set_permissions(ch.guild.default_role, connect=None if lk else False, view_channel=None if lk else False)
            await sendv_eph(it, OK("KİLİT", "Açıldı" if lk else "Kilitlendi"))
        async def nm(it):
            if await oc(it): await it.response.send_modal(TVNameModal(self.cid))
        async def lm(it):
            if await oc(it): await it.response.send_modal(TVLimitModal(self.cid))
        async def iv(it):
            ch = await oc(it)
            if ch: await sendv_eph(it, OK("DAVET", (await ch.create_invite(max_uses=1, max_age=3600)).url))
        async def dl(it):
            ch = await oc(it)
            if not ch: return
            db.q("DELETE FROM temp_channels WHERE channel_id=?", (self.cid,)); await ch.delete(reason="Sahibi sildi"); await sendv_eph(it, OK("SİLİNDİ"))
        self.btn("Kilitle/Aç", lock, style=discord.ButtonStyle.secondary, emoji=e("lock"), cid="tv_lock_" + str(cid))
        self.btn("İsim", nm, emoji="✏️", cid="tv_name_" + str(cid))
        self.btn("Limit", lm, emoji="👥", cid="tv_limit_" + str(cid))
        self.btn("Davet", iv, style=discord.ButtonStyle.success, cid="tv_inv_" + str(cid))
        self.btn("Sil", dl, style=discord.ButtonStyle.danger, emoji=e("trash"), cid="tv_del_" + str(cid))

MAINT_CD = {}
class KatreBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix=self.get_prefix, intents=discord.Intents.all(), case_insensitive=True, help_command=None, allowed_mentions=discord.AllowedMentions(users=True, roles=False, everyone=False))
        self.start_time = datetime.datetime.now(); self.xp_cd = {}; self.ar_cd = {}; self._si = 0; self.spam = {}; self.flood = {}; self.joins = {}
    async def get_prefix(self, m):
        p = "k!"
        if m.guild:
            s = db.one("SELECT prefix FROM servers WHERE guild_id=?", (m.guild.id,))
            if s: p = s["prefix"]
        b = {p, p.lower(), p.upper()}
        if self.user: b.add("<@" + str(self.user.id) + "> "); b.add("<@!" + str(self.user.id) + "> ")
        return list(b)
    async def setup_hook(self):
        self.gwv = GiveawayPanel(self, " ")
        for v in (self.gwv, TicketOpenPanel(" "), TicketPanel(" "), AppOpenPanel(" "), HelpPanel(self, " "), OwnerPanel(self, " ")): self.add_view(v)
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
                    if d: print("☁️ ayar:", settings_restore(d))
            except Exception: traceback.print_exc()
            _HASH["emoji"] = json.dumps(EMO_CACHE, sort_keys=True); _HASH["pro"] = json.dumps(pro_snapshot(), sort_keys=True, default=str); _HASH["set"] = json.dumps(settings_snapshot(), sort_keys=True, default=str)
        refresh_emojis(); await check_update(self)
        print("💧 KATRE v" + BOT_VERSION + " | " + str(self.user) + " | " + str(len(self.guilds)) + " sunucu | " + str(len(self.commands)) + " komut")
        print("🩺 TEŞHİS | V2: " + ("AÇIK" if HAS_V2 else "YOK") + " | OWNER: " + str(OWNER_ID) + " | BAKIM: " + ("AÇIK!" if is_maintenance() else "kapalı"))
        await self.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="k!yardım | Katre Bot"))
    @tasks.loop(seconds=12)
    async def status_loop(self):
        o = self.get_user(OWNER_ID); on = o.display_name if o else "Owner"
        ms = [(discord.ActivityType.watching, "k!yardım | Katre Bot"), (discord.ActivityType.playing, str(len(self.guilds)) + " sunucuda"), (discord.ActivityType.listening, str(sum(g.member_count or 0 for g in self.guilds)) + " kullanıcıya"), (discord.ActivityType.competing, "k!quiz"), (discord.ActivityType.watching, "Owner: " + on), (discord.ActivityType.playing, "k!pro"), (discord.ActivityType.listening, "k!probonus 💎")]
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
            txt = head("chart", "CANLI İSTATİSTİK") + "\n" + KV([(e("dot")+"Sunucu", len(self.guilds)), (e("dot")+"Kullanıcı", sum(g.member_count or 0 for g in self.guilds)), (e("dot")+"Komut", len(self.commands)), (e("dot")+"Uptime", up), (e("dot")+"Ping", str(round(self.latency*1000))+"ms"), (e("fire")+"Top", ", ".join("k!"+t["cmd"] for t in top) or "—")])
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
        p = db.one("SELECT log_ch FROM protections WHERE guild_id=?", (g.id,))
        if p and p["log_ch"]:
            ch = g.get_channel(p["log_ch"])
            if ch:
                try: await rp_ch(ch, t)
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
            if is_maintenance() and m.author.id != OWNER_ID:
                prefs = await self.get_prefix(m)
                if m.content and any(m.content.startswith(p) for p in prefs):
                    nw = datetime.datetime.now().timestamp()
                    if nw - MAINT_CD.get(m.author.id, 0) > 30:
                        MAINT_CD[m.author.id] = nw
                        try: await rp_ch(m.channel, head("warn", "BAKIMDAYIZ") + "\nBirazdan döneriz!")
                        except Exception: pass
                return
            if db.one("SELECT 1 FROM blacklist WHERE user_id=?", (m.author.id,)): return
        except Exception: pass
        try:
            a = db.one("SELECT * FROM afk WHERE user_id=?", (m.author.id,))
            if a:
                dk = int((datetime.datetime.now() - datetime.datetime.fromisoformat(a["since"])).total_seconds() // 60)
                db.q("DELETE FROM afk WHERE user_id=?", (m.author.id,))
                msg = await rp_ch(m.channel, head("wave", "DÖNDÜ") + "\n" + m.author.mention + " • **" + sure_txt(dk) + "** • **" + str(a["mentions"] or 0) + "** mention")
                try: await msg.delete(delay=20)
                except Exception: pass
            if m.guild:
                for mm in m.mentions:
                    a = db.one("SELECT * FROM afk WHERE user_id=?", (mm.id,))
                    if a:
                        db.q("UPDATE afk SET mentions=mentions+1 WHERE user_id=?", (mm.id,))
                        await rp_ch(m.channel, head("sleep", mm.display_name + " AFK") + "\n**" + (a["reason"] or "—") + "**"); break
        except Exception: pass
        try:
            await self.protections(m)
            if m.guild and not m.content.startswith(("k!", "K!")):
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
                    u = db.one("SELECT xp,level,xp2 FROM users WHERE user_id=?", (m.author.id))
                    g = random.randint(5, 15) * (2 if u["xp2"] else 1); xp, lv = u["xp"] + g, u["level"]; nd = lv * 100
                    if xp >= nd:
                        xp -= nd; lv += 1; cn = random.randint(50, 150)
                        db.q("UPDATE users SET coins=coins+? WHERE user_id=?", (cn, m.author.id))
                        for lr in db.all("SELECT * FROM level_roles WHERE guild_id=? AND level<=?", (m.guild.id, lv)):
                            rr = m.guild.get_role(lr["role_id"])
                            if rr and rr not in m.author.roles:
                                try: await m.author.add_roles(rr, reason="Seviye")
                                except Exception: pass
                        await rp_ch(m.channel, head("chartup", "SEVİYE") + "\n" + m.author.mention + " → **Lv " + str(lv) + "**")
                    db.q("UPDATE users SET xp=?,level=? WHERE user_id=?", (xp, lv, m.author.id))
        except Exception: traceback.print_exc()
        finally:
            await self.process_commands(m)
    async def on_voice_state_update(self, member, before, after):
        try:
            g = member.guild; tv = db.one("SELECT * FROM tempvoice WHERE guild_id=?", (g.id,))
            if tv and after.channel and after.channel.id == tv["trigger_ch"]:
                cat = g.get_channel(tv["category_id"]) if tv["category_id"] else after.channel.category
                ow = {g.default_role: discord.PermissionOverwrite(view_channel=False, connect=False), member: discord.PermissionOverwrite(view_channel=True, connect=True, manage_channels=True, mute_members=True, move_members=True), g.me: discord.PermissionOverwrite(view_channel=True, connect=True, manage_channels=True, move_members=True)}
                ch = await g.create_voice_channel("🔊 " + member.display_name, category=cat, overwrites=ow)
                db.q("INSERT OR REPLACE INTO temp_channels(channel_id,owner_id,guild_id) VALUES(?,?,?)", (ch.id, member.id, g.id))
                self.add_view(TVPanel(ch.id, " ")); await member.move_to(ch, reason="Temp voice")
                try: await member.send(head("mic", "ODAN HAZIR") + "\n**" + ch.name + "**", view=TVPanel(ch.id, head("mic", "ODAN HAZIR") + "\n**" + ch.name + "**"))
                except Exception: pass
            for chn in (before.channel, after.channel):
                if not chn: continue
                row = db.one("SELECT * FROM temp_channels WHERE channel_id=?", (chn.id,))
                if row and len(chn.members) == 0:
                    db.q("DELETE FROM temp_channels WHERE channel_id=?", (chn.id,))
                    try: await chn.delete(reason="Boş")
                    except Exception: pass
        except Exception: traceback.print_exc()
    async def on_message_edit(self, b, a):
        if b.author.bot or not b.guild or b.content == a.content: return
        await guild_log_send(b.guild, head("pen", "DÜZENLENDİ") + "\n" + b.author.mention + "\n> " + (b.content or "")[:200] + "\n> " + (a.content or "")[:200])
    async def on_message_delete(self, m):
        try:
            if m.author.bot or not m.guild: return
            db.q("INSERT OR REPLACE INTO snipe(channel_id,author_id,content,attachment,ts) VALUES(?,?,?,?,?)", (m.channel.id, m.author.id, (m.content or "")[:1000], m.attachments[0].url if m.attachments else None, datetime.datetime.now().isoformat()))
            await guild_log_send(m.guild, head("trash", "SİLİNDİ") + "\n" + m.author.mention + "\n> " + ((m.content or "")[:200] or "_ek_"))
        except Exception: pass
    async def on_member_remove(self, m): await guild_log_send(m.guild, e("wave") + " **AYRILDI** › " + str(m))
    async def on_member_update(self, b, a):
        if b.nick != a.nick: await guild_log_send(a.guild, head("tag", "NICK") + "\n" + a.mention + "\n> " + str(b.nick) + " → " + str(a.nick))
    async def on_command_completion(self, ctx): db.q("INSERT INTO cmd_stats(cmd,uses) VALUES(?,1) ON CONFLICT(cmd) DO UPDATE SET uses=uses+1", (ctx.command.name,))
    async def on_command_error(self, ctx, er):
        if isinstance(er, OwnerOnly): return
        if isinstance(er, ProOnly):
            v = Panel(head("pro", "PRO GEREKLİ") + "\nBu komut sadece PRO üyelere özel.\n📋 `k!pro` • 💎 `k!probonus`")
            v.btn_url("Pro Destek", SUPPORT_URL, emoji=e("diamond"))
            await rp(ctx, v.text, v); return
        if isinstance(er, commands.CommandNotFound): await rp(ctx, e("search") + " Yok → `k!yardım`"); return
        if isinstance(er, commands.MissingRequiredArgument): await rp(ctx, ER("EKSİK", "`k!" + ctx.command.name + " " + ctx.command.signature + "`")); return
        if isinstance(er, commands.CommandOnCooldown): await rp(ctx, head("time", "BEKLE") + "\n**" + str(int(er.retry_after)) + " sn** sonra dene."); return
        if isinstance(er, commands.BotMissingPermissions):
            await rp(ctx, ER("BOT YETKİSİ EKSİK", "`" + ", ".join(er.missing_permissions) + "`\nKatre rolüne **Yönetici** ver + en üste taşı.")); return
        if isinstance(er, commands.MissingPermissions): await rp(ctx, ER("YETKİN YOK", "`" + ", ".join(er.missing_permissions) + "`")); return
        if isinstance(er, commands.CheckFailure): await rp(ctx, ER("YETKİ YOK")); return
        if isinstance(er, commands.CommandInvokeError):
            o = er.original
            if isinstance(o, discord.Forbidden):
                try: await ctx.author.send(ER("YETKİ", "#" + str(ctx.channel) + " yetkim yok."))
                except Exception: pass
                return
            er = o
        await rp(ctx, head("warn", "HATA") + "\n```\n" + str(er)[:700] + "\n```"); traceback.print_exc()
    async def on_member_join(self, mb):
        ensure_user(mb.id, str(mb))
        try:
            p = db.one("SELECT * FROM protections WHERE guild_id=?", (mb.guild.id,))
            if p and p["anti_raid"]:
                nw = datetime.datetime.now().timestamp(); dq = self.joins.setdefault(mb.guild.id, deque()); dq.append(nw)
                while dq and nw - dq[0] > 10: dq.popleft()
                if len(dq) >= 8 and nw > (p["raid_until"] or 0):
                    db.q("UPDATE protections SET raid_until=? WHERE guild_id=?", (nw + 600, mb.guild.id)); await self.mod_log(mb.guild, head("shield", "RAID") + "\n10dk kilit!")
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
                    try: await rp_ch(ch, head("wave", "HOŞ GELDİN") + "\n### " + mb.mention + "\n" + e("party") + " **" + str(mb.guild.member_count) + "** üye!")
                    except Exception: pass
        try:
            c = db.one("SELECT * FROM counters WHERE guild_id=?", (mb.guild.id,))
            if c and not c["reached"]:
                ch = mb.guild.get_channel(c["channel_id"])
                if ch:
                    cu = mb.guild.member_count
                    if cu >= c["target"]:
                        db.q("UPDATE counters SET reached=1 WHERE guild_id=?", (mb.guild.id,)); await rp_ch(ch, head("party", "HEDEF") + "\n**" + str(c["target"]) + "** üye!")
                    else: await rp_ch(ch, head("target", "SAYAÇ") + "\n**" + str(cu) + "/" + str(c["target"]) + "**\n" + bar(cu / c["target"] * 100))
        except Exception: pass
    async def on_guild_join(self, g):
        ensure_server(g.id); db.q("INSERT OR IGNORE INTO protections(guild_id) VALUES(?)", (g.id,))
        if not EMO_CACHE: auto_map_emojis(g)
        ch = g.system_channel or next((c for c in g.text_channels if c.permissions_for(g.me).send_messages), None)
        if ch:
            v = Panel(head("logo", "KATRE ARANIZDA") + "\n`k!yardım` • `k!kurulum` • `k!tempvoice`"); v.btn_url("Destek", SUPPORT_URL, emoji=e("link"))
            await rp_ch(ch, v.text, v)

async def finalize_giveaway(bot, mid):
    gw = db.one("SELECT * FROM giveaways WHERE message_id=?", (mid,))
    if not gw or gw["status"] != "active": return
    p = json.loads(gw["participants"]); db.q("UPDATE giveaways SET status='ended' WHERE message_id=?", (mid,))
    ch = bot.get_channel(gw["channel_id"])
    if not ch: return
    if not p:
        try: await rp_ch(ch, head("warn", "BİTTİ") + "\n**" + gw["prize"] + "** katılımcı yok.")
        except Exception: pass
        return
    n = min(gw["winners"], len(p)); ws = [bot.get_user(int(w)) for w in random.sample(p, n)]
    men = "\n".join(w.mention if w else "?" for w in ws); jump = None
    try:
        msg = await ch.fetch_message(mid); jump = msg.jump_url
        await msg.edit(content=gw_end(gw, men, p), view=GwJumpPanel(gw_end(gw, men, p), jump))
    except Exception: pass
    await rp_ch(ch, head("party", "SONUÇ") + "\n" + men + " kazandı!")
    for w in ws:
        if w:
            try: await w.send(head("star", "KAZANDIN") + "\n**" + gw["prize"] + "** • " + ch.guild.name, view=GwJumpPanel(" ", jump) if jump else None)
            except Exception: pass

bot = KatreBot()
# >>> BÖLÜM 1 SONU — "devam" yaz, BÖLÜM 2 (komutlar) gelsin <<<
# ═══════════════════════════════════════════════════════════════════
#  💧 BÖLÜM 2/2 — KOMUTLAR
# ═══════════════════════════════════════════════════════════════════
@kategori("genel")
@bot.command(name="yardım", aliases=["yardim","help","komutlar"], help="Yardım menüsü")
@commands.cooldown(1, 5, commands.BucketType.user)
async def yardim(ctx): await rp(ctx, help_content(bot), HelpPanel(bot, help_content(bot)))
@kategori("genel")
@bot.command(name="komutbilgi", aliases=["cmd"], help="<komut> — detay")
async def komutbilgi(ctx, *, name: str):
    c = bot.get_command(name.lower().replace("k!", "").strip())
    if not c: return await rp(ctx, ER("YOK", "`k!komutbilgi mute`"))
    await rp(ctx, head("info", "k!" + c.name) + "\n" + (c.help or "—") + "\n" + e("dot") + " `k!" + c.name + (" " + c.signature if c.signature else "") + "`")
@kategori("genel")
@bot.command(name="ping", help="Gecikme")
async def ping(ctx): await rp(ctx, e("bolt") + " **PONG** › `" + str(round(bot.latency * 1000)) + "ms`")
@kategori("genel")
@bot.command(name="istatistik", aliases=["stats"], help="Bot istatistiği")
async def istatistik(ctx):
    up = str(datetime.datetime.now() - bot.start_time).split(".")[0]
    await rp(ctx, head("chart", "İSTATİSTİK") + "\n" + KV([(e("dot")+"Sunucu", len(bot.guilds)), (e("dot")+"Kullanıcı", sum(g.member_count or 0 for g in bot.guilds)), (e("dot")+"Komut", len(bot.commands)), (e("dot")+"Uptime", up), (e("dot")+"Ping", str(round(bot.latency*1000))+"ms"), (e("dot")+"Sürüm", "v"+BOT_VERSION), (e("dot")+"V2", "✅" if HAS_V2 else "—")]))
@kategori("genel")
@bot.command(name="mesajtop", help="Mesaj sıralaması")
async def mesajtop(ctx):
    rs = db.all("SELECT * FROM users ORDER BY messages DESC LIMIT 10")
    if not rs: return await rp(ctx, e("chart") + " Veri yok.")
    md = ["🥇","🥈","🥉"]
    await rp(ctx, head("pen", "MESAJ TOP") + "\n" + "\n".join((md[i] if i < 3 else "**" + str(i+1) + ".**") + " <@" + str(r["user_id"]) + "> ─ **" + str(r["messages"]) + "**" for i, r in enumerate(rs)))
@kategori("genel")
@bot.command(name="davet", aliases=["invite"], help="Davet")
async def davet(ctx):
    u = "https://discord.com/oauth2/authorize?client_id=" + str(bot.user.id) + "&permissions=8&scope=bot%20applications.commands"
    v = Panel(head("logo", "KATRE BOT'U EKLE")); v.btn_url("Botu Ekle", u, emoji="➕"); v.btn_url("Destek", SUPPORT_URL, emoji=e("link"))
    await rp(ctx, v.text, v)
@kategori("genel")
@bot.command(name="avatar", aliases=["av","pfp"], help="Avatar")
async def avatar(ctx, u: discord.Member = None):
    u = u or ctx.author
    v = Panel(head("cam", u.display_name + " AVATAR") + "\n" + u.display_avatar.url); v.btn_url("Aç", u.display_avatar.url, emoji=e("link"))
    await rp(ctx, v.text, v)
@kategori("genel")
@bot.command(name="oda", help="<isim/limit/kilit/davet/sil> — odanı yönet")
async def oda(ctx, i: str = "bilgi", *, arg=None):
    row = db.one("SELECT * FROM temp_channels WHERE owner_id=? AND guild_id=?", (ctx.author.id, ctx.guild.id))
    if not row: return await rp(ctx, ER("ODAN YOK", "Temp voice kanalına gir."))
    ch = ctx.guild.get_channel(row["channel_id"])
    if not ch:
        db.q("DELETE FROM temp_channels WHERE channel_id=?", (row["channel_id"],)); return await rp(ctx, ER("ODA YOK"))
    i = i.lower()
    if i == "isim" and arg: await ch.edit(name=arg[:50]); await rp(ctx, OK("İSİM", ch.name))
    elif i == "limit" and arg:
        try: n = max(0, min(99, int(arg)))
        except ValueError: return await rp(ctx, ER("GEÇERSİZ", "0-99"))
        await ch.edit(user_limit=n or None); await rp(ctx, OK("LİMİT", str(n or "sınırsız")))
    elif i == "kilit":
        lk = ch.overwrites_for(ctx.guild.default_role).connect is False
        await ch.set_permissions(ctx.guild.default_role, connect=None if lk else False, view_channel=None if lk else False)
        await rp(ctx, OK("KİLİT", "Açıldı" if lk else "Kilitlendi"))
    elif i == "davet": await rp(ctx, OK("DAVET", (await ch.create_invite(max_uses=1, max_age=3600)).url))
    elif i == "sil":
        db.q("DELETE FROM temp_channels WHERE channel_id=?", (ch.id,)); await ch.delete(); await rp(ctx, OK("SİLİNDİ"))
    else: await rp(ctx, head("mic", ch.name) + "\n`isim` `limit` `kilit` `davet` `sil`")
@kategori("genel")
@bot.command(name="rank", aliases=["seviye","level"], help="Seviye kartı")
@commands.cooldown(1, 3, commands.BucketType.user)
async def rank(ctx, u: discord.Member = None):
    u = u or ctx.author; ensure_user(u.id, str(u)); d = db.one("SELECT * FROM users WHERE user_id=?", (u.id,)); nd = d["level"] * 100
    bd = []
    if d["pro"]: bd.append(e("pro") + " PRO")
    if d["pro_tag"]: bd.append(e("tag") + " " + d["pro_tag"])
    if d["xp2"]: bd.append(e("bolt") + " 2x")
    await rp(ctx, head("chartup", u.display_name + " RANK") + "\n" + ("### " + " • ".join(bd) + "\n" if bd else "") + KV([(e("star")+"Seviye", d["level"]), (e("spark")+"XP", str(d["xp"])+"/"+str(nd)), (e("coin")+"Coin", d["coins"]), (e("star")+"Rep", d["rep"])]) + "\n" + bar(d["xp"]/nd*100))
@kategori("genel")
@bot.command(name="sıralama", aliases=["sirala","top","lb"], help="Seviye top10")
async def sıralama(ctx):
    rs = db.all("SELECT * FROM users ORDER BY level DESC, xp DESC LIMIT 10")
    if not rs: return await rp(ctx, e("chart") + " Veri yok.")
    md = ["🥇","","🥉"]
    await rp(ctx, head("star", "SIRALAMA") + "\n" + "\n".join((md[i] if i < 3 else "**" + str(i+1) + ".**") + " <@" + str(r["user_id"]) + "> Lv.**" + str(r["level"]) + "** `" + str(r["xp"]) + "`" for i, r in enumerate(rs)))
@kategori("genel")
@bot.command(name="profil", aliases=["profile"], help="Profil")
async def profil(ctx, u: discord.Member = None):
    u = u or ctx.author; ensure_user(u.id, str(u)); d = db.one("SELECT * FROM users WHERE user_id=?", (u.id,)); a = db.one("SELECT * FROM afk WHERE user_id=?", (u.id,))
    await rp(ctx, head("logo", u.display_name + " PROFİL") + "\n" + KV([(e("dot")+"ID", u.id), (e("time")+"Hesap", "<t:"+str(int(u.created_at.timestamp()))+":R>"), (e("chartup")+"Seviye", d["level"]), (e("coin")+"Coin", d["coins"]), (e("star")+"Rep", d["rep"]), (e("pro")+"Pro", "✅" if d["pro"] else "❌"), (e("sleep")+"AFK", "✅" if a else "❌")]))
@kategori("genel")
@bot.command(name="sunucubilgi", aliases=["serverinfo"], help="Sunucu")
async def sunucubilgi(ctx):
    g = ctx.guild
    await rp(ctx, head("logo", g.name) + "\n" + KV([(e("crown")+"Kurucu", "<@"+str(g.owner_id)+">"), (e("dot")+"Üye", g.member_count), (e("dot")+"Kanal", len(g.channels)), (e("shield")+"Rol", len(g.roles)), (e("bolt")+"Boost", g.premium_subscription_count or 0)]))
@kategori("genel")
@bot.command(name="snipe", help="Silinen son mesaj")
@commands.cooldown(1, 3, commands.BucketType.user)
async def snipe(ctx):
    s = db.one("SELECT * FROM snipe WHERE channel_id=?", (ctx.channel.id,))
    if not s: return await rp(ctx, e("cam") + " Kayıt yok.")
    await rp(ctx, head("cam", "SNIPE") + "\n" + KV([(e("dot")+"Kim", "<@"+str(s["author_id"])+">"), (e("time")+"Tarih", s["ts"][:16])]) + "\n> " + ((s["content"] or "_ek_")[:700]))
@kategori("genel")
@bot.command(name="afk", help="[sebep] — AFK")
async def afk(ctx, *, s=None):
    cur = db.one("SELECT * FROM afk WHERE user_id=?", (ctx.author.id,))
    if cur and not s:
        db.q("DELETE FROM afk WHERE user_id=?", (ctx.author.id,)); return await rp(ctx, OK("AFK KAPALI", "Döndün!"))
    db.q("INSERT OR REPLACE INTO afk(user_id,reason,since,mentions) VALUES(?,?,?,0)", (ctx.author.id, (s or "—")[:100], datetime.datetime.now().isoformat()))
    await rp(ctx, head("sleep", "AFK AÇIK") + "\n" + e("arrow") + " **" + (s or "—")[:100] + "**")
@kategori("genel")
@bot.command(name="rep", help="<@üye> — itibar")
@commands.cooldown(1, 43200, commands.BucketType.user)
async def rep(ctx, u: discord.Member):
    if u.id == ctx.author.id: return await rp(ctx, ER("OLMAZ"))
    ensure_user(u.id, str(u)); db.q("UPDATE users SET rep=rep+1 WHERE user_id=?", (u.id,))
    await rp(ctx, e("star") + " " + ctx.author.mention + " → " + u.mention + " +1")
@kategori("genel")
@bot.command(name="destek", aliases=["ticketpanel"], help="Destek paneli")
@commands.has_permissions(administrator=True)
async def destek(ctx):
    t = head("ticket", "DESTEK MERKEZİ") + "\nButona bas, formu doldur!"; await rp(ctx, t, TicketOpenPanel(t))
    try: await ctx.message.delete()
    except Exception: pass
@kategori("genel")
@bot.command(name="not", help="<metin>")
async def not_(ctx, *, m):
    ensure_user(ctx.author.id, str(ctx.author)); u = db.one("SELECT notes FROM users WHERE user_id=?", (ctx.author.id,))
    n = json.loads(u["notes"]); n.append({"t": m, "d": datetime.datetime.now().isoformat()})
    db.q("UPDATE users SET notes=? WHERE user_id=?", (json.dumps(n), ctx.author.id)); await rp(ctx, OK("NOT", str(len(n))))
@kategori("genel")
@bot.command(name="notlar", help="Notların")
async def notlar(ctx):
    u = db.one("SELECT notes FROM users WHERE user_id=?", (ctx.author.id,)); n = json.loads(u["notes"]) if u else []
    if not n: return await rp(ctx, e("pen") + " Yok.")
    await rp(ctx, head("pen", "NOTLAR") + "\n" + "\n".join(e("arrow") + " `" + x["d"][:10] + "` " + x["t"][:60] for x in n[-8:]))
@kategori("genel")
@bot.command(name="doğumgünü", aliases=["dogumgunu"], help="<gün> <ay>")
async def doğumgünü(ctx, g: int, a: int):
    if not (1 <= g <= 31 and 1 <= a <= 12): return await rp(ctx, ER("GEÇERSİZ"))
    db.q("UPDATE users SET birthday=? WHERE user_id=?", (str(g)+"."+str(a), ctx.author.id)); await rp(ctx, e("cake") + " **" + str(g) + "." + str(a) + "**")
@kategori("genel")
@bot.command(name="hatırlat", aliases=["hatirlat"], help="<dk> <metin>")
async def hatırlat(ctx, dk: int, *, m):
    if dk < 1 or dk > 1440: return await rp(ctx, ER("GEÇERSİZ", "1-1440"))
    await rp(ctx, e("alarm") + " **" + str(dk) + " dk**"); await asyncio.sleep(dk * 60); await ctx.send(ctx.author.mention + " " + e("alarm") + " " + m)
@kategori("genel")
@bot.command(name="botkontrol", aliases=["check"], help="Yetki teşhisi")
@commands.has_permissions(administrator=True)
async def botkontrol(ctx):
    p = ctx.channel.permissions_for(ctx.guild.me)
    cs = [("Mesaj",p.view_channel),("Gönder",p.send_messages),("Embed",p.embed_links),("Yönet",p.manage_messages),("Timeout",p.moderate_members),("Rol",p.manage_roles),("Kanal",p.manage_channels),("Ban",p.ban_members)]
    await rp(ctx, head("gear", "BOT KONTROL") + "\n" + "\n".join((e("check") if ok else e("cross")) + " " + n for n, ok in cs))

@kategori("mod")
@bot.command(name="yasakla", aliases=["ban"], help="<@üye> [sebep]")
@commands.has_permissions(ban_members=True)
@commands.bot_has_permissions(ban_members=True)
async def yasakla(ctx, u: discord.Member, *, s="—"):
    g = mod_guard(ctx, u, "yasakla")
    if g: return await rp(ctx, ER("OLMAZ", g))
    t = head("warn", "ONAY") + "\n**" + str(u) + "** banlansın mı?"; v = ConfirmPanel(t); await rp(ctx, t, v); await v.wait()
    if v.value is None: return await rp(ctx, WN("AŞIM"))
    if v.value:
        try: await u.send(ER("BAN", ctx.guild.name))
        except Exception: pass
        await u.ban(reason=str(ctx.author)); punish_log(ctx.guild.id, u.id, "BAN", s, ctx.author.id)
        await guild_log_send(ctx.guild, head("hammer", "BAN") + "\n" + u.mention); await rp(ctx, head("hammer", "BAN") + "\n" + u.mention)
@kategori("mod")
@bot.command(name="at", aliases=["kick"], help="<@üye> [sebep]")
@commands.has_permissions(kick_members=True)
@commands.bot_has_permissions(kick_members=True)
async def at(ctx, u: discord.Member, *, s="—"):
    g = mod_guard(ctx, u, "at")
    if g: return await rp(ctx, ER("OLMAZ", g))
    t = head("warn", "ONAY") + "\n**" + str(u) + "** atılsın mı?"; v = ConfirmPanel(t); await rp(ctx, t, v); await v.wait()
    if v.value is None: return await rp(ctx, WN("AŞIM"))
    if v.value:
        await u.kick(reason=str(ctx.author)); punish_log(ctx.guild.id, u.id, "KICK", s, ctx.author.id)
        await guild_log_send(ctx.guild, head("kick", "KICK") + "\n" + u.mention); await rp(ctx, head("kick", "ATILDI") + "\n" + u.mention)
@kategori("mod")
@bot.command(name="mute", aliases=["sustur"], help="<@üye> <süre> [sebep]")
@commands.has_permissions(moderate_members=True)
@commands.bot_has_permissions(moderate_members=True)
async def mute(ctx, u: discord.Member, süre: str, *, s="—"):
    g = mod_guard(ctx, u, "sustur")
    if g: return await rp(ctx, ER("OLMAZ", g))
    try: dk = parse_sure(süre)
    except Exception: return await rp(ctx, ER("SÜRE", "30m / 1h / 2d"))
    if dk < 1 or dk > 40320: return await rp(ctx, ER("SÜRE", "1dk-28gün"))
    await u.timeout(datetime.timedelta(minutes=dk), reason=str(ctx.author)); punish_log(ctx.guild.id, u.id, "MUTE", s, ctx.author.id, dk)
    await guild_log_send(ctx.guild, head("lock", "MUTE") + "\n" + u.mention + " " + süre); await rp(ctx, OK("MUTE", u.mention + " " + süre))
@kategori("mod")
@bot.command(name="unmute", help="<@üye>")
@commands.has_permissions(moderate_members=True)
@commands.bot_has_permissions(moderate_members=True)
async def unmute(ctx, u: discord.Member):
    await u.timeout(None); punish_log(ctx.guild.id, u.id, "UNMUTE", "-", ctx.author.id); await rp(ctx, OK("UNMUTE", u.mention))
@kategori("mod")
@bot.command(name="ceza-sistemi", help="<ayarla a b|kapat|bilgi>")
@commands.has_permissions(administrator=True)
async def ceza_sistemi(ctx, i: str = "bilgi", a: int = 3, b: int = 5):
    i = i.lower()
    if i in ("ayarla","aç"):
        db.q("INSERT OR REPLACE INTO punish_config(guild_id,mute_at,ban_at) VALUES(?,?,?)", (ctx.guild.id, a, b))
        await rp(ctx, OK("CEZA", str(a) + " uyarı→1s mute • " + str(b) + " uyarı→ban"))
    elif i in ("kapat","off"):
        db.q("DELETE FROM punish_config WHERE guild_id=?", (ctx.guild.id,)); await rp(ctx, OK("KAPALI"))
    else:
        c = db.one("SELECT * FROM punish_config WHERE guild_id=?", (ctx.guild.id,))
        await rp(ctx, head("shield", "CEZA") + "\n" + ((str(c["mute_at"]) + "→mute • " + str(c["ban_at"]) + "→ban") if c else "Kapalı"))
@kategori("mod")
@bot.command(name="ceza-geçmişi", aliases=["cezalar","sicil"], help="[<@üye>]")
@commands.has_permissions(manage_messages=True)
async def ceza_geçmişi(ctx, u: discord.Member = None):
    u = u or ctx.author
    rs = db.all("SELECT * FROM punishments WHERE guild_id=? AND user_id=? ORDER BY id DESC LIMIT 10", (ctx.guild.id, u.id))
    if not rs: return await rp(ctx, e("shield") + " Temiz sicil.")
    await rp(ctx, head("log", "SİCİL") + "\n" + "\n".join(e("arrow") + " **" + r["type"] + "** " + r["ts"][:10] for r in rs))
@kategori("mod")
@bot.command(name="unban", help="<id> [sebep]")
@commands.has_permissions(ban_members=True)
@commands.bot_has_permissions(ban_members=True)
async def unban(ctx, uid: int, *, s="—"):
    try: b = await ctx.guild.fetch_ban(discord.Object(id=uid))
    except discord.NotFound: return await rp(ctx, ER("YOK"))
    except Exception: return await rp(ctx, ER("HATA"))
    await ctx.guild.unban(b.user, reason=str(ctx.author)); await rp(ctx, OK("UNBAN", str(b.user)))
@kategori("mod")
@bot.command(name="banlist", help="Banlılar")
@commands.has_permissions(ban_members=True)
async def banlist(ctx):
    bs = [b async for b in ctx.guild.bans()]
    if not bs: return await rp(ctx, e("shield") + " Yok.")
    await rp(ctx, head("hammer", "BAN (" + str(len(bs)) + ")") + "\n" + "\n".join(e("arrow") + " " + str(b.user) + " `" + str(b.user.id) + "`" for b in bs[:15]))
@kategori("mod")
@bot.command(name="nick", help="<@üye> <nick>")
@commands.has_permissions(manage_nicknames=True)
@commands.bot_has_permissions(manage_nicknames=True)
async def nick(ctx, u: discord.Member, *, n):
    g = mod_guard(ctx, u, "nick")
    if g: return await rp(ctx, ER("OLMAZ", g))
    await u.edit(nick=n[:32]); await rp(ctx, OK("NICK", n[:32]))
@kategori("mod")
@bot.command(name="nicksıfırla", help="<@üye>")
@commands.has_permissions(manage_nicknames=True)
async def nicksıfırla(ctx, u: discord.Member):
    g = mod_guard(ctx, u, "işlem")
    if g: return await rp(ctx, ER("OLMAZ", g))
    await u.edit(nick=None); await rp(ctx, OK("NICK", "sıfır"))
@kategori("mod")
@bot.command(name="rolbilgi", help="<@rol>")
async def rolbilgi(ctx, role: discord.Role):
    await rp(ctx, head("shield", role.name) + "\n" + KV([(e("dot")+"ID", role.id), (e("dot")+"Üye", len(role.members)), (e("dot")+"Renk", str(role.color))]))
@kategori("mod")
@bot.command(name="uyar", aliases=["warn"], help="<@üye> [sebep]")
@commands.has_permissions(manage_messages=True)
async def uyar(ctx, u: discord.Member, *, s="—"):
    if u.id == ctx.author.id: return await rp(ctx, ER("OLMAZ"))
    ensure_user(u.id, str(u)); db.q("UPDATE users SET warnings=warnings+1 WHERE user_id=?", (u.id,))
    w = db.one("SELECT warnings FROM users WHERE user_id=?", (u.id,))["warnings"]; punish_log(ctx.guild.id, u.id, "WARN", s, ctx.author.id)
    ex = ""; cfg = db.one("SELECT * FROM punish_config WHERE guild_id=?", (ctx.guild.id,))
    if cfg:
        if w == cfg["ban_at"]:
            try:
                await u.ban(reason="Oto " + str(w) + " uyarı"); punish_log(ctx.guild.id, u.id, "AUTO-BAN", str(w), ctx.bot.user.id); ex = "\n" + e("hammer") + " **OTO BAN**"
            except Exception: pass
        elif w == cfg["mute_at"]:
            try:
                await u.timeout(datetime.timedelta(minutes=60), reason="Oto"); punish_log(ctx.guild.id, u.id, "AUTO-MUTE", str(w), ctx.bot.user.id, 60); ex = "\n" + e("lock") + " **OTO 1s MUTE**"
            except Exception: pass
    await rp(ctx, head("warn", "UYARI") + "\n" + u.mention + " → **" + str(w) + "**" + ex)
@kategori("mod")
@bot.command(name="uyarılar", aliases=["warns"], help="[<@üye>]")
async def uyarılar(ctx, u: discord.Member = None):
    u = u or ctx.author; ensure_user(u.id, str(u))
    await rp(ctx, e("warn") + " " + u.mention + " → **" + str(db.one("SELECT warnings FROM users WHERE user_id=?", (u.id,))["warnings"]) + "**")
@kategori("mod")
@bot.command(name="temizle", aliases=["purge","sil"], help="<adet>")
@commands.has_permissions(manage_messages=True)
@commands.bot_has_permissions(manage_messages=True)
async def temizle(ctx, a: int):
    if not 1 <= a <= 500: return await rp(ctx, ER("1-500"))
    await ctx.channel.purge(limit=a+1); m = await rp(ctx, e("trash") + " **" + str(a) + "**"); await m.delete(delay=5)
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
    await ctx.channel.edit(slowmode_delay=s); await rp(ctx, e("gear") + " **" + str(s) + "sn**")
@kategori("mod")
@bot.command(name="kilit", help="Kilitle")
@commands.has_permissions(manage_channels=True)
async def kilit(ctx):
    await ctx.channel.set_permissions(ctx.guild.default_role, send_messages=False); await rp(ctx, e("lock") + " kilitli")
@kategori("mod")
@bot.command(name="kilitaç", aliases=["unlock"], help="Aç")
@commands.has_permissions(manage_channels=True)
async def kilitaç(ctx):
    await ctx.channel.set_permissions(ctx.guild.default_role, send_messages=None); await rp(ctx, e("unlock") + " açık")
@kategori("mod")
@bot.command(name="rolver", help="<@rol> <@üye...>")
@commands.has_permissions(manage_roles=True)
@commands.bot_has_permissions(manage_roles=True)
async def rolver(ctx, role: discord.Role, ms: commands.Greedy[discord.Member]):
    if not ms: return await rp(ctx, ER("EKSİK"))
    d = 0
    for m in ms:
        try: await m.add_roles(role); d += 1
        except Exception: pass
    await rp(ctx, OK("ROL VERİLDİ", str(d) + "/" + str(len(ms))))
@kategori("mod")
@bot.command(name="rolal", help="<@rol> <@üye...>")
@commands.has_permissions(manage_roles=True)
@commands.bot_has_permissions(manage_roles=True)
async def rolal(ctx, role: discord.Role, ms: commands.Greedy[discord.Member]):
    if not ms: return await rp(ctx, ER("EKSİK"))
    d = 0
    for m in ms:
        try: await m.remove_roles(role); d += 1
        except Exception: pass
    await rp(ctx, OK("ROL ALINDI", str(d) + "/" + str(len(ms))))
@kategori("mod")
@bot.command(name="herkeserol", help="<@rol>")
@commands.has_permissions(administrator=True)
@commands.bot_has_permissions(manage_roles=True)
async def herkeserol(ctx, role: discord.Role):
    t = head("warn", "ONAY") + "\nTüm üyelere " + role.mention + "?"; v = ConfirmPanel(t, 60); await rp(ctx, t, v); await v.wait()
    if not v.value: return await rp(ctx, WN("İPTAL"))
    d = 0
    for m in ctx.guild.members:
        if m.bot: continue
        try: await m.add_roles(role); d += 1
        except Exception: pass
    await rp(ctx, OK("BİTTİ", str(d)))
@kategori("mod")
@bot.command(name="otorol", help="<@rol|kapat>")
@commands.has_permissions(administrator=True)
async def otorol(ctx, *, arg):
    ensure_server(ctx.guild.id)
    if arg.lower() in ("kapat","off","0"):
        db.q("UPDATE servers SET auto_role=NULL WHERE guild_id=?", (ctx.guild.id,)); return await rp(ctx, OK("KAPALI"))
    role = await commands.RoleConverter().convert(ctx, arg)
    db.q("UPDATE servers SET auto_role=? WHERE guild_id=?", (role.id, ctx.guild.id)); await rp(ctx, OK("OTOROL", role.mention))
@kategori("mod")
@bot.command(name="hoşgeldin", aliases=["hosgeldin"], help="<#kanal|kapat>")
@commands.has_permissions(administrator=True)
async def hoşgeldin(ctx, ch: discord.TextChannel = None):
    ensure_server(ctx.guild.id)
    if ch is None:
        db.q("UPDATE servers SET welcome_ch=NULL WHERE guild_id=?", (ctx.guild.id,)); return await rp(ctx, OK("KAPALI"))
    db.q("UPDATE servers SET welcome_ch=? WHERE guild_id=?", (ch.id, ctx.guild.id)); await rp(ctx, OK("HOŞGELDİN", ch.mention))
@kategori("mod")
@bot.command(name="butonrol", aliases=["rolmenü"], help="<@rol...>")
@commands.has_permissions(administrator=True)
async def butonrol(ctx, rs: commands.Greedy[discord.Role], *, a="Rolünü seç!"):
    if not rs or len(rs) > 25: return await rp(ctx, ER("1-25 rol"))
    mid = str(random.randint(10**11, 10**12-1))
    db.q("INSERT OR REPLACE INTO role_menus(menu_id,guild_id,role_ids) VALUES(?,?,?)", (mid, ctx.guild.id, json.dumps([r.id for r in rs])))
    t = head("shield", "ROL MENÜSÜ") + "\n" + a; v = RoleMenuPanel(mid, [(r.id, r.name) for r in rs], t); bot.add_view(v); await rp(ctx, t, v)
@kategori("mod")
@bot.command(name="koruma", help="<mod> <aç/kapat>")
@commands.has_permissions(administrator=True)
async def koruma(ctx, md: str, d: str):
    md = md.lower().replace("-","").replace("_","")
    col = {"antispam":"anti_spam","antiflood":"anti_flood","antiraid":"anti_raid","antilink":"anti_link","badword":"badword","küfür":"badword"}.get(md)
    if not col: return await rp(ctx, ER("MODÜL", "antispam/antiflood/antiraid/antilink/badword"))
    db.q("INSERT OR IGNORE INTO protections(guild_id) VALUES(?)", (ctx.guild.id,))
    v = 1 if d.lower() in ("aç","ac","on","1") else 0
    db.q("UPDATE protections SET " + col + "=? WHERE guild_id=?", (v, ctx.guild.id))
    await rp(ctx, head("shield", "KORUMA") + "\n**" + md + "** → " + ("AÇIK" if v else "KAPALI"))
@kategori("mod")
@bot.command(name="korumadurum", help="Durum")
async def korumadurum(ctx):
    p = db.one("SELECT * FROM protections WHERE guild_id=?", (ctx.guild.id,)) or {}
    f = lambda v: e("check") if v else e("cross")
    await rp(ctx, head("shield", "DURUM") + "\n" + KV([(f(p.get("anti_spam"))+"Spam","─"),(f(p.get("anti_flood"))+"Flood","─"),(f(p.get("anti_raid"))+"Raid","─"),(f(p.get("anti_link"))+"Link","─"),(f(p.get("badword"))+"Küfür","─")]))
@kategori("mod")
@bot.command(name="korumalog", help="<#kanal>")
@commands.has_permissions(administrator=True)
async def korumalog(ctx, ch: discord.TextChannel):
    db.q("INSERT OR IGNORE INTO protections(guild_id) VALUES(?)", (ctx.guild.id,)); db.q("UPDATE protections SET log_ch=? WHERE guild_id=?", (ch.id, ctx.guild.id)); await rp(ctx, OK("LOG", ch.mention))
@kategori("mod")
@bot.command(name="badword", help="<ekle/sil/liste> [kelime]")
@commands.has_permissions(administrator=True)
async def badword(ctx, i: str, *, k=None):
    g = ctx.guild.id
    if i.lower() in ("ekle","add"):
        if not k: return await rp(ctx, ER("KELİME"))
        db.q("INSERT OR IGNORE INTO badwords(guild_id,word) VALUES(?,?)", (g, k.lower())); await rp(ctx, OK("+", k.lower()))
    elif i.lower() in ("sil","remove"):
        db.q("DELETE FROM badwords WHERE guild_id=? AND word=?", (g, (k or "").lower())); await rp(ctx, OK("-"))
    else:
        ws = [w["word"] for w in db.all("SELECT word FROM badwords WHERE guild_id=?", (g,))]
        await rp(ctx, head("warn", "FİLTRE") + "\n" + ("`" + "`, `".join(ws) + "`" if ws else "Boş"))
@kategori("mod")
@bot.command(name="raidmodu", help="<aç/kapat>")
@commands.has_permissions(administrator=True)
async def raidmodu(ctx, m: str):
    db.q("INSERT OR IGNORE INTO protections(guild_id) VALUES(?)", (ctx.guild.id,))
    if m.lower() in ("aç","ac","on"):
        db.q("UPDATE protections SET raid_until=? WHERE guild_id=?", (datetime.datetime.now().timestamp()+600, ctx.guild.id)); await rp(ctx, head("shield", "RAID") + "\n10dk")
    else:
        db.q("UPDATE protections SET raid_until=0 WHERE guild_id=?", (ctx.guild.id)); await rp(ctx, OK("KAPALI"))
@kategori("mod")
@bot.command(name="kurulum", aliases=["sunucukur","setup"], help="Sunucu kur")
@commands.has_permissions(administrator=True)
@commands.bot_has_permissions(manage_channels=True, manage_roles=True)
async def kurulum(ctx):
    t = head("gear", "KURULUM") + "\n4 kategori • 12 kanal • 4 rol. Onay?"; v = ConfirmPanel(t, 60); await rp(ctx, t, v); await v.wait()
    if not v.value: return
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
        await rp(ctx, OK("KURULUM", str(ck) + " kanal • hoşgeldin: " + hg.mention))
    except discord.Forbidden: await rp(ctx, ER("YETKİ"))
    except Exception as ex: await rp(ctx, ER("HATA", str(ex)[:250]))

@kategori("sys")
@bot.command(name="tempvoice", help="[kur|#kanal|kapat]")
@commands.has_permissions(administrator=True)
@commands.bot_has_permissions(manage_channels=True, move_members=True)
async def tempvoice(ctx, *, arg=None):
    if arg and arg.lower() in ("kapat","off","0"):
        db.q("DELETE FROM tempvoice WHERE guild_id=?", (ctx.guild.id,)); return await rp(ctx, OK("KAPALI"))
    if arg:
        ch = await commands.VoiceChannelConverter().convert(ctx, arg)
        db.q("INSERT OR REPLACE INTO tempvoice(guild_id,trigger_ch,category_id) VALUES(?,?,?)", (ctx.guild.id, ch.id, ch.category.id if ch.category else None))
        await rp(ctx, OK("TETİKLEYİCİ", ch.mention))
    else:
        cat = await ctx.guild.create_category("ÖZEL ODALAR"); trig = await cat.create_voice_channel("➕ Katıl & Oda Kur")
        await trig.set_permissions(ctx.guild.default_role, view_channel=True, connect=True, speak=False)
        db.q("INSERT OR REPLACE INTO tempvoice(guild_id,trigger_ch,category_id) VALUES(?,?,?)", (ctx.guild.id, trig.id, cat.id))
        await rp(ctx, OK("KURULDU", trig.mention))
@kategori("sys")
@bot.command(name="ticket", help="<kapat/bilgi/listele>")
async def ticket(ctx, i: str = "bilgi"):
    i = i.lower(); t = db.one("SELECT * FROM tickets WHERE channel_id=?", (ctx.channel.id,))
    if i == "kapat":
        if not t: return await rp(ctx, ER("TICKET DEĞİL"))
        if not (ctx.author.guild_permissions.administrator or ctx.author.id == t["user_id"]): return await rp(ctx, ER("YETKİ"))
        db.q("UPDATE tickets SET status='closed' WHERE channel_id=?", (ctx.channel.id,))
        await rp(ctx, WN("KAPANIYOR")); await asyncio.sleep(10)
        try: await ctx.channel.delete()
        except Exception: pass
    elif i == "bilgi":
        if not t: return await rp(ctx, ER("TICKET DEĞİL"))
        await rp(ctx, head("ticket", "BİLGİ") + "\n" + KV([(e("dot")+"Kim", "<@"+str(t["user_id"])+">"), (e("dot")+"Üstlenen", ("<@"+str(t["claimed_by"])+">") if t["claimed_by"] else "—")]))
    elif i == "listele":
        if not ctx.author.guild_permissions.administrator: return await rp(ctx, ER("YETKİ"))
        rs = db.all("SELECT * FROM tickets WHERE guild_id=? AND status='open'", (ctx.guild.id,))
        await rp(ctx, head("ticket", "AÇIK (" + str(len(rs)) + ")") + "\n" + ("\n".join(e("arrow") + " <#" + str(r["channel_id"]) + ">" for r in rs) if rs else "Yok"))
    else: await rp(ctx, ER("KOMUT", "kapat/bilgi/listele"))
@kategori("sys")
@bot.command(name="başvuru-ayarla", help="<#log> [@rol]")
@commands.has_permissions(administrator=True)
async def başvuru_ayarla(ctx, ch: discord.TextChannel, role: discord.Role = None):
    db.q("INSERT OR REPLACE INTO app_settings(guild_id,log_ch,staff_role) VALUES(?,?,?)", (ctx.guild.id, ch.id, role.id if role else None))
    await rp(ctx, OK("BAŞVURU", ch.mention + "\nPanel: `k!başvuru-panel`"))
@kategori("sys")
@bot.command(name="başvuru-panel", help="Panel")
@commands.has_permissions(administrator=True)
async def başvuru_panel(ctx):
    t = head("clip", "YETKİLİ BAŞVURU") + "\n### Ekibimize katıl!\n" + e("check") + " 14+ • " + e("check") + " aktif • " + e("check") + " deneyimli\n\nButona bas!"; await rp(ctx, t, AppOpenPanel(t))
    try: await ctx.message.delete()
    except Exception: pass
@kategori("sys")
@bot.command(name="başvurular", help="Bekleyenler")
@commands.has_permissions(administrator=True)
async def başvurular(ctx):
    rs = db.all("SELECT * FROM applications WHERE guild_id=? AND status='pending'", (ctx.guild.id,))
    if not rs: return await rp(ctx, e("clip") + " Yok.")
    await rp(ctx, head("clip", "BEKLEYEN") + "\n" + "\n".join(e("arrow") + " #" + str(r["id"]) + " <@" + str(r["user_id"]) + ">" for r in rs[:10]))
@kategori("sys")
@bot.command(name="başvurum", help="Durumun")
async def başvurum(ctx):
    r = db.one("SELECT * FROM applications WHERE guild_id=? AND user_id=? ORDER BY id DESC", (ctx.guild.id, ctx.author.id))
    if not r: return await rp(ctx, e("clip") + " Yok.")
    await rp(ctx, head("clip", "#" + str(r["id"])) + "\n**" + r["status"] + "**")
@kategori("sys")
@bot.command(name="otocevap", help="<ekle/sil/liste>")
@commands.has_permissions(administrator=True)
async def otocevap(ctx, i: str, *, a=None):
    g = ctx.guild.id
    if i.lower() in ("ekle","add"):
        if not a or "|" not in a: return await rp(ctx, ER("ÖRNEK", "ekle selam | merhaba!"))
        t, r = [p.strip() for p in a.split("|", 1)]
        db.q("INSERT OR REPLACE INTO auto_replies(guild_id,trigger,response) VALUES(?,?,?)", (g, t.lower(), r[:500])); await rp(ctx, OK("+", t.lower()))
    elif i.lower() in ("sil","remove"):
        db.q("DELETE FROM auto_replies WHERE guild_id=? AND trigger=?", (g, (a or "").lower())); await rp(ctx, OK("-"))
    else:
        rs = db.all("SELECT * FROM auto_replies WHERE guild_id=?", (g,))
        await rp(ctx, head("robot", "OTO (" + str(len(rs)) + ")") + "\n" + "\n".join(e("arrow") + " `" + r["trigger"] + "`" for r in rs[:15]))
@kategori("sys")
@bot.command(name="sayaç", help="<hedef> <#kanal|kapat>")
@commands.has_permissions(administrator=True)
async def sayaç(ctx, h: int, ch: discord.TextChannel = None):
    if ch is None or h <= 0:
        db.q("DELETE FROM counters WHERE guild_id=?", (ctx.guild.id,)); return await rp(ctx, OK("KAPALI"))
    db.q("INSERT OR REPLACE INTO counters(guild_id,target,channel_id,reached) VALUES(?,?,?,0)", (ctx.guild.id, h, ch.id)); await rp(ctx, OK("SAYAÇ", str(h)))
@kategori("sys")
@bot.command(name="seviyerol", help="<ekle/sil/liste> [lv] [@rol]")
@commands.has_permissions(administrator=True)
async def seviyerol(ctx, i: str, s: int = 0, role: discord.Role = None):
    g = ctx.guild.id
    if i.lower() in ("ekle","add"):
        if not role: return await rp(ctx, ER("ÖRNEK", "ekle 5 @Rol"))
        db.q("INSERT INTO level_roles(guild_id,level,role_id) VALUES(?,?,?)", (g, s, role.id)); await rp(ctx, OK("+", "Lv" + str(s)))
    elif i.lower() in ("sil","remove"):
        db.q("DELETE FROM level_roles WHERE guild_id=? AND level=?", (g, s)); await rp(ctx, OK("-"))
    else:
        rs = db.all("SELECT * FROM level_roles WHERE guild_id=? ORDER BY level", (g,))
        await rp(ctx, head("chartup", "ROLLER") + "\n" + ("\n".join(e("arrow") + " Lv" + str(r["level"]) + " <@&" + str(r["role_id"]) + ">" for r in rs) if rs else "Yok"))
@kategori("sys")
@bot.command(name="sunuculog", help="<#kanal|kapat>")
@commands.has_permissions(administrator=True)
async def sunuculog(ctx, ch: discord.TextChannel = None):
    if ch is None:
        db.q("DELETE FROM guild_logs WHERE guild_id=?", (ctx.guild.id,)); return await rp(ctx, OK("KAPALI"))
    db.q("INSERT OR REPLACE INTO guild_logs(guild_id,channel_id) VALUES(?,?)", (ctx.guild.id, ch.id)); await rp(ctx, OK("LOG", ch.mention))

@kategori("eco")
@bot.command(name="cüzdan", aliases=["balance","para"], help="Cüzdan")
async def cüzdan(ctx, u: discord.Member = None):
    u = u or ctx.author; ensure_user(u.id, str(u)); d = db.one("SELECT * FROM users WHERE user_id=?", (u.id,))
    await rp(ctx, head("money", u.display_name) + "\n" + KV([(e("coin")+"Coin", d["coins"]), (e("star")+"Rep", d["rep"]), (e("pro")+"Pro", "✅" if d["pro"] else "❌")]))
@kategori("eco")
@bot.command(name="zenginler", aliases=["coinlb"], help="Coin top")
async def zenginler(ctx):
    rs = db.all("SELECT * FROM users ORDER BY coins DESC LIMIT 10")
    if not rs: return await rp(ctx, e("coin") + " Yok.")
    md = ["🥇","","🥉"]
    await rp(ctx, head("coin", "ZENGİNLER") + "\n" + "\n".join((md[i] if i < 3 else "**" + str(i+1) + ".**") + " <@" + str(r["user_id"]) + "> **" + str(r["coins"]) + "**" for i, r in enumerate(rs)))
@kategori("eco")
@bot.command(name="günlük", aliases=["gunluk","daily"], help="Günlük")
@commands.cooldown(1, 86400, commands.BucketType.user)
async def günlük(ctx):
    ensure_user(ctx.author.id, str(ctx.author)); u = db.one("SELECT * FROM users WHERE user_id=?", (ctx.author.id,))
    b = random.randint(150, 400) + (250 if u["pro"] else 0); db.q("UPDATE users SET coins=coins+? WHERE user_id=?", (b, ctx.author.id))
    await rp(ctx, head("gift", "GÜNLÜK") + "\n**+" + str(b) + " coin**")
@kategori("eco")
@bot.command(name="çalış", aliases=["calis","work"], help="Çalış")
@commands.cooldown(1, 1800, commands.BucketType.user)
async def çalış(ctx):
    j, a, b = random.choice([("Yazılım",200,400),("Tasarım",150,300),("İçerik",180,350),("Pizzacı",100,220),("Şoför",120,260)])
    p = random.randint(a, b); db.q("UPDATE users SET coins=coins+? WHERE user_id=?", (p, ctx.author.id))
    await rp(ctx, e("gear") + " " + j + " → **" + str(p) + "**")
@kategori("eco")
@bot.command(name="balık", aliases=["fish"], help="5dk")
@commands.cooldown(1, 300, commands.BucketType.user)
async def balık(ctx):
    n, v = random.choice([("Levrek",40),("Nemo",90),("Köpekbalığı",200),("Ahtapot",120),("Çizme",5)])
    db.q("UPDATE users SET coins=coins+? WHERE user_id=?", (v, ctx.author.id)); await rp(ctx, e("fish") + " " + n + " **" + str(v) + "**")
@kategori("eco")
@bot.command(name="maden", aliases=["mine"], help="5dk")
@commands.cooldown(1, 300, commands.BucketType.user)
async def maden(ctx):
    n, v = random.choice([("Kömür",30),("Gümüş",110),("Altın",200),("Elmas",400),("Taş",5)])
    db.q("UPDATE users SET coins=coins+? WHERE user_id=?", (v, ctx.author.id)); await rp(ctx, e("pick") + " " + n + " **" + str(v) + "**")
@kategori("eco")
@bot.command(name="soy", aliases=["rob"], help="<@üye>")
@commands.cooldown(1, 600, commands.BucketType.user)
async def soy(ctx, u: discord.Member):
    if u.id == ctx.author.id or u.bot: return await rp(ctx, ER("GEÇERSİZ"))
    ensure_user(u.id, str(u)); t = db.one("SELECT coins FROM users WHERE user_id=?", (u.id,)); me = db.one("SELECT coins FROM users WHERE user_id=?", (ctx.author.id,))
    if t["coins"] < 200: return await rp(ctx, ER("HEDEF FAKİR"))
    if random.random() < 0.45:
        s = random.randint(50, min(500, t["coins"]))
        db.q("UPDATE users SET coins=coins-? WHERE user_id=?", (s, u.id)); db.q("UPDATE users SET coins=coins+? WHERE user_id=?", (s, ctx.author.id))
        await rp(ctx, head("fire", "SOYGUN") + "\n+" + str(s))
    else:
        f = min(me["coins"], random.randint(50, 200)); db.q("UPDATE users SET coins=coins-? WHERE user_id=?", (f, ctx.author.id))
        await rp(ctx, head("cross", "YAKALANDIN") + "\n-" + str(f))
@kategori("eco")
@bot.command(name="transfer", help="<@üye> <miktar>")
async def transfer(ctx, u: discord.Member, m: int):
    if m <= 0 or u.id == ctx.author.id: return await rp(ctx, ER("GEÇERSİZ"))
    ensure_user(u.id, str(u)); me = db.one("SELECT coins FROM users WHERE user_id=?", (ctx.author.id,))
    if me["coins"] < m: return await rp(ctx, ER("YETERSİZ"))
    db.q("UPDATE users SET coins=coins-? WHERE user_id=?", (m, ctx.author.id)); db.q("UPDATE users SET coins=coins+? WHERE user_id=?", (m, u.id))
    await rp(ctx, head("coin", "TRANSFER") + "\n" + str(m) + " → " + u.mention)
@kategori("eco")
@bot.command(name="bahis", aliases=["bet"], help="<miktar>")
@commands.cooldown(1, 10, commands.BucketType.user)
async def bahis(ctx, m: int):
    if m <= 0: return await rp(ctx, ER("GEÇERSİZ"))
    me = db.one("SELECT coins FROM users WHERE user_id=?", (ctx.author.id,))
    if me["coins"] < m: return await rp(ctx, ER("YETERSİZ"))
    w = random.random() < 0.5; db.q("UPDATE users SET coins=coins+? WHERE user_id=?", (m if w else -m, ctx.author.id))
    await rp(ctx, (head("star", "KAZANDIN") + "\n+" + str(m*2)) if w else (head("cross", "KAYBETTİN") + "\n-" + str(m)))
@kategori("eco")
@bot.command(name="market", aliases=["shop"], help="Market")
async def market(ctx):
    v = Panel(head("gift", "MARKET") + "\n" + KV([(e("pro")+"Pro", "50.000"), (e("palette")+"Renk", "5.000"), (e("tag")+"Tag", "7.500")])); v.btn_url("Satın Al", SUPPORT_URL, emoji="🛒")
    await rp(ctx, v.text, v)

@kategori("fun")
@bot.command(name="8ball", help="<soru>")
async def eightball(ctx, *, s): await rp(ctx, e("search") + " " + s[:80] + "\n" + e("dot") + " " + random.choice(["Evet!", "Belki", "Hayır", "Asla!", "Kesinlikle"]))
@kategori("fun")
@bot.command(name="yazıtura", help="At")
async def yazıtura(ctx): await rp(ctx, e("dice") + " **" + random.choice(["YAZI", "TURA"]) + "**")
@kategori("fun")
@bot.command(name="zar", help="1-6")
async def zar(ctx):
    r = random.randint(1, 6); await rp(ctx, e("dice") + " **" + str(r) + "** " + ["⚀","","⚂","","⚄","⚅"][r-1])
@kategori("fun")
@bot.command(name="aşk", aliases=["ask","love"], help="<@üye>")
async def aşk(ctx, u: discord.Member):
    p = random.randint(0, 100); m = "Yok bu iş" if p < 30 else ("Fena değil" if p < 60 else ("Güzel çift" if p < 85 else "RUH İKİZİ"))
    await rp(ctx, head("heart", "AŞK") + "\n" + ctx.author.mention + " x " + u.mention + "\n" + bar(p) + "\n**" + m + "**")
@kategori("fun")
@bot.command(name="slot", help="Çevir")
async def slot(ctx):
    s = ["🍒","","🍇","💎","7️⃣",""]; r = [random.choice(s) for _ in range(3)]; w = len(set(r)) == 1
    await rp(ctx, head("slot", "SLOT") + "\n┃ " + " ┃ ".join(r) + " ┃\n" + ("**JACKPOT!**" if w else "Olmadı"))
@kategori("fun")
@bot.command(name="seç", aliases=["sec"], help="<a> <b>")
async def seç(ctx, *, s):
    o = s.split()
    if len(o) < 2: return await rp(ctx, ER("2+"))
    await rp(ctx, e("target") + " **" + random.choice(o) + "**")
@kategori("fun")
@bot.command(name="şanslı", aliases=["sansli"], help="<1-100>")
@commands.cooldown(1, 30, commands.BucketType.user)
async def şanslı(ctx, t2: int):
    if not 1 <= t2 <= 100: return await rp(ctx, ER("1-100"))
    t = random.randint(1, 100)
    if t2 == t: w, msg = 500, "JACKPOT!"
    elif abs(t2 - t) <= 5: w, msg = 50, "Yakın!"
    else: w, msg = 0, "Olmadı"
    if w: db.q("UPDATE users SET coins=coins+? WHERE user_id=?", (w, ctx.author.id))
    await rp(ctx, head("dice", "ŞANS") + "\n" + str(t) + " vs " + str(t2) + " → " + msg + (" +" + str(w) if w else ""))
@kategori("fun")
@bot.command(name="oylama", aliases=["anket"], help="<soru> [| A | B]")
@commands.cooldown(1, 5, commands.BucketType.user)
async def oylama(ctx, *, s):
    try:
        parts = [x.strip() for x in s.split("|")]; q = parts[0][:200] or "Anket"
        opts = [x[:60] for x in parts[1:6] if x] if len(parts) > 1 else ["Evet", "Hayır", "Çekimser"]
        if len(opts) < 2: return await rp(ctx, ER("ÖRNEK", "Soru | A | B"))
        cur = db.q("INSERT INTO polls(guild_id,channel_id,message_id,question,options,votes,status,creator,ts) VALUES(?,?,0,?,?,'{}','active',?,?)", (ctx.guild.id, ctx.channel.id, q, json.dumps(opts, ensure_ascii=False), ctx.author.id, datetime.datetime.now().isoformat()))
        pid = cur.lastrowid; p = db.one("SELECT * FROM polls WHERE id=?", (pid,))
        v = PollPanel(pid, opts, poll_content(p)); msg = await rp(ctx, poll_content(p), v)
        db.q("UPDATE polls SET message_id=? WHERE id=?", (msg.id, pid)); bot.add_view(v)
    except Exception as ex:
        traceback.print_exc(); await rp(ctx, ER("ANKET", str(ex)[:250]))
@kategori("fun")
@bot.command(name="ppboyu", aliases=["pp"], help="Ölçüm")
@commands.cooldown(1, 5, commands.BucketType.user)
async def ppboyu(ctx, u: discord.Member = None):
    u = u or ctx.author; n = (u.id % 18) + 3
    await rp(ctx, head("game", "PP") + "\n" + u.mention + "\n`8" + "=" * n + "D` **" + str(n+2) + "cm**")
@kategori("fun")
@bot.command(name="quiz", aliases=["bilgi"], help="+75 coin")
@commands.cooldown(1, 10, commands.BucketType.user)
async def quiz(ctx):
    Q = [("Başkent?",["İstanbul","Ankara","İzmir","Bursa"],1),("En büyük gezegen?",["Dünya","Mars","Jüpiter","Satürn"],2),("Discord.py dili?",["Java","Python","C++","Go"],1),("H2O?",["Su","Tuz","O2","CO2"],0)]
    q, o, a = random.choice(Q)
    txt = head("game", "QUIZ") + "\n### " + q + "\n" + e("gift") + " +75 coin"
    view = Panel(txt, timeout=30); emj = ["1️⃣","2️⃣","3️⃣","4️⃣"]
    def cb(i):
        async def _c(it):
            if i == a:
                ensure_user(it.user.id, str(it.user)); db.q("UPDATE users SET coins=coins+75, xp=xp+20 WHERE user_id=?", (it.user.id,))
                await sendv_eph(it, OK("DOĞRU", "+75"))
            else: await sendv_eph(it, ER("YANLIŞ", o[a]))
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
    if not 1 <= s <= 10: return await rp(ctx, ER("1-10"))
    t = random.randint(1, 10)
    if s == t:
        db.q("UPDATE users SET coins=coins+100 WHERE user_id=?", (ctx.author.id)); await rp(ctx, head("star", "BİLDİN") + "\n+100")
    else: await rp(ctx, head("cross", "OLMADI") + "\n" + str(t))
@kategori("fun")
@bot.command(name="evlen", help="<@üye>")
async def evlen(ctx, u: discord.Member):
    if u.id == ctx.author.id or u.bot: return await rp(ctx, ER("GEÇERSİZ"))
    if db.one("SELECT 1 FROM marriages WHERE user1=? OR user2=? OR user1=? OR user2=?", (ctx.author.id,ctx.author.id,u.id,u.id)): return await rp(ctx, ER("EVLİ"))
    db.q("INSERT INTO marriages(user1,user2,since) VALUES(?,?,?)", (ctx.author.id, u.id, datetime.datetime.now().isoformat()))
    await rp(ctx, head("ring", "EVLENDİNİZ") + "\n" + ctx.author.mention + " x " + u.mention)
@kategori("fun")
@bot.command(name="boşan", help="Boşan")
async def boşan(ctx):
    db.q("DELETE FROM marriages WHERE user1=? OR user2=?", (ctx.author.id, ctx.author.id)); await rp(ctx, head("broken", "BOŞANDIN"))
@kategori("fun")
@bot.command(name="eş", help="[<@üye>]")
async def eş(ctx, u: discord.Member = None):
    u = u or ctx.author; m = db.one("SELECT * FROM marriages WHERE user1=? OR user2=?", (u.id, u.id))
    if not m: return await rp(ctx, e("broken") + " bekar")
    await rp(ctx, e("ring") + " " + u.mention + " x <@" + str(m["user2"] if m["user1"] == u.id else m["user1"]) + ">")

@kategori("give")
@bot.command(name="çekiliş", aliases=["cekilis"], help="<süre> <kazanan> <ödül>")
@commands.has_permissions(administrator=True)
async def çekiliş(ctx, s: str, k: int, *, ö):
    try: dk = parse_sure(s)
    except Exception: return await rp(ctx, ER("SÜRE", "60m / 2h / 1d"))
    if dk < 1 or k < 1: return await rp(ctx, ER("GEÇERSİZ"))
    end = datetime.datetime.now() + datetime.timedelta(minutes=dk)
    gw = {"prize": ö, "winners": k, "end_time": end.timestamp(), "host": ctx.author.id, "participants": "[]"}
    t = gw_start(gw); msg = await rp(ctx, t, GiveawayPanel(bot, t))
    db.q("INSERT INTO giveaways(message_id,guild_id,channel_id,prize,winners,end_time,host) VALUES(?,?,?,?,?,?,?)", (msg.id, ctx.guild.id, ctx.channel.id, ö, k, end.timestamp(), ctx.author.id))
@kategori("give")
@bot.command(name="çekilişler", help="Aktifler")
async def çekilişler(ctx):
    rs = db.all("SELECT * FROM giveaways WHERE guild_id=? AND status='active'", (ctx.guild.id,))
    if not rs: return await rp(ctx, e("give") + " Yok.")
    await rp(ctx, head("give", "AKTİF") + "\n" + "\n".join(e("arrow") + " **" + g["prize"] + "** <t:" + str(int(g["end_time"])) + ":R>" for g in rs))
@kategori("give")
@bot.command(name="çekilişbitir", help="<id>")
@commands.has_permissions(administrator=True)
async def çekilişbitir(ctx, m: int):
    g = db.one("SELECT * FROM giveaways WHERE message_id=? AND guild_id=?", (m, ctx.guild.id))
    if not g or g["status"] != "active": return await rp(ctx, ER("YOK"))
    await finalize_giveaway(bot, m); await rp(ctx, OK("BİTTİ"))

@kategori("pro")
@bot.command(name="pro", help="Durum + ayrıcalıklar")
async def pro(ctx, u: discord.Member = None):
    u = u or ctx.author; ensure_user(u.id, str(u)); d = db.one("SELECT * FROM users WHERE user_id=?", (u.id,))
    await rp(ctx, head("pro", "KATRE PRO") + "\n" + KV([(e("dot")+"Durum", "PRO ÜYE" if d["pro"] else "Yok"), (e("log")+"Log", len(db.all("SELECT 1 FROM pro_logs WHERE user_id=?", (u.id,))))]) +
        "\n\n" + e("star") + " **PRO KOMUTLARI**\n" + e("arrow") + " `prooda` özel ses odası\n" + e("arrow") + " `k!prorol` renkli PRO rolü\n" + e("arrow") + " `k!probonus` 12s'de bir +500 coin\n" + e("arrow") + " `k!probanner` havalı banner\n" + e("arrow") + " `k!proşans` saatlik 1000 coin oyunu\n" + e("arrow") + " `prorenk` `protag` `proxp` `prostats` `proyazı` `proembed`")
@kategori("pro")
@bot.command(name="prooda", help="Özel oda")
@is_pro()
async def prooda(ctx):
    c = discord.utils.get(ctx.guild.categories, name="PRO ODALAR") or await ctx.guild.create_category("PRO ODALAR")
    try: await c.set_permissions(ctx.guild.default_role, view_channel=False)
    except Exception: pass
    ch = await ctx.guild.create_voice_channel(ctx.author.display_name, category=c)
    await ch.set_permissions(ctx.author, connect=True, manage_channels=True, move_members=True)
    await rp(ctx, OK("ODA", ch.mention))
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
        except Exception: return await rp(ctx, ER("YETKİ", "Rol oluşturamıyorum."))
    else:
        try: await r.edit(color=color)
        except Exception: pass
    if r in ctx.author.roles: return await rp(ctx, WN("ZATEN VAR", r.mention))
    await ctx.author.add_roles(r, reason="Pro üye")
    await rp(ctx, OK("PRO ROL", r.mention + " verildi!"))
@kategori("pro")
@bot.command(name="probonus", help="12 saatte bir +500 coin (PRO)")
@is_pro()
@commands.cooldown(1, 43200, commands.BucketType.user)
async def probonus(ctx):
    db.q("UPDATE users SET coins=coins+500 WHERE user_id=?", (ctx.author.id,))
    await rp(ctx, head("gift", "PRO BONUS") + "\n" + ctx.author.mention + " → **+500 coin** " + e("pro") + "\n" + e("time") + " Sonraki: <t:" + str(int(datetime.datetime.now().timestamp()) + 43200) + ":R>")
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
        await rp(ctx, head("star", "PRO ŞANS") + "\nÇekilen: **" + str(n) + "** (1-10 kazanır)\n" + e("party") + " **KAZANDIN → +1000 coin**")
    else:
        await rp(ctx, head("dice", "PRO ŞANS") + "\nÇekilen: **" + str(n) + "** (1-10 kazanır)\n" + e("cross") + " Olmadı... 1 saat sonra tekrar dene.")
@kategori("pro")
@bot.command(name="prorenk", help="<hex>")
@is_pro()
async def prorenk(ctx, h: str):
    h = h.lstrip("#")
    if len(h) != 6: return await rp(ctx, ER("ff0000"))
    try: int(h, 16)
    except ValueError: return await rp(ctx, ER("HEX"))
    db.q("UPDATE users SET pro_color=? WHERE user_id=?", (h, ctx.author.id)); await rp(ctx, OK("RENK", "#" + h.upper() + "\n`k!prorol` ile rolüne uygula."))
@kategori("pro")
@bot.command(name="prostats", help="Detay")
@is_pro()
async def prostats(ctx):
    d = db.one("SELECT * FROM users WHERE user_id=?", (ctx.author.id,))
    await rp(ctx, head("chart", "PRO") + "\n" + KV([(e("dot")+"Mesaj", d["messages"]), (e("chartup")+"Lv", d["level"]), (e("coin")+"Coin", d["coins"]), (e("bolt")+"2x", "✅" if d["xp2"] else "❌")]))
@kategori("pro")
@bot.command(name="proyazı", help="<metin>")
@is_pro()
async def proyazı(ctx, *, m): await rp(ctx, head("pen", "PRO") + "\n" + fancy(m[:200]))
@kategori("pro")
@bot.command(name="proembed", help="<b> | <m> | <hex>")
@is_pro()
async def proembed(ctx, *, a):
    p = [x.strip() for x in a.split("|")]
    if len(p) < 2: return await rp(ctx, ER("ÖRNEK"))
    await rp(ctx, "### " + p[0][:100] + "\n" + DIV + "\n" + p[1][:1500])
@kategori("pro")
@bot.command(name="protag", help="<metin>")
@is_pro()
async def protag(ctx, *, t):
    db.q("UPDATE users SET pro_tag=? WHERE user_id=?", (t[:12], ctx.author.id)); await rp(ctx, OK("TAG", t[:12]))
@kategori("pro")
@bot.command(name="proxp", help="2x")
@is_pro()
async def proxp(ctx):
    u = db.one("SELECT xp2 FROM users WHERE user_id=?", (ctx.author.id,)); n = 0 if u["xp2"] else 1
    db.q("UPDATE users SET xp2=? WHERE user_id=?", (n, ctx.author.id)); await rp(ctx, OK("BOOST", "AÇIK" if n else "KAPALI"))

@kategori("owner")
@bot.command(name="halfowner", aliases=["coowner"], help="<ayarla/kaldır/bilgi/liste>")
async def halfowner(ctx, i: str = "bilgi", u: discord.Member = None):
    i = i.lower()
    if i in ("ayarla","ekle"):
        if ctx.author.id != OWNER_ID: return
        if not u: return await rp(ctx, ER("@üye"))
        db.q("INSERT OR REPLACE INTO half_owners(user_id,since,added_by) VALUES(?,?,?)", (u.id, datetime.datetime.now().isoformat(), ctx.author.id))
        await rp(ctx, OK("HALF", u.mention))
    elif i in ("kaldır","remove"):
        if ctx.author.id != OWNER_ID: return
        db.q("DELETE FROM half_owners WHERE user_id=?", ((u or ctx.author).id,)); await rp(ctx, WN("-"))
    elif i == "liste":
        rs = db.all("SELECT * FROM half_owners")
        await rp(ctx, head("owner", "HALF") + "\n" + ("\n".join(e("arrow") + " <@" + str(r["user_id"]) + ">" for r in rs) if rs else "Yok"))
    else:
        me = db.one("SELECT * FROM half_owners WHERE user_id=?", (ctx.author.id,))
        await rp(ctx, head("owner", "HALF OWNER") + "\n" + e("star") + " `prover` `proal` `prologlar`\n" + e("cross") + " diğer owner komutları YOK\n\n" + (e("check") + " Sen half owner'sın!" if me else e("info") + " Half owner değilsin."))
@kategori("owner")
@bot.command(name="sahip", aliases=["owner","panel"], help="Panel")
@is_owner()
async def sahip(ctx):
    t = head("owner", "PANEL") + "\n" + KV([(e("dot")+"Sunucu", len(bot.guilds)), (e("dot")+"Bakım", "AÇIK" if is_maintenance() else "KAPALI"), (e("dot")+"Yedek", "AÇIK" if BACKUP_CH else "KAPALI"), (e("spark")+"Sürüm", "v"+BOT_VERSION)])
    await rp(ctx, t, OwnerPanel(bot, t))
@kategori("owner")
@bot.command(name="bakım", aliases=["bakim"], help="<aç/kapat>")
@is_owner()
async def bakım(ctx, mod: str = None):
    if mod is None or mod.lower() in ("kapat","off","0"):
        db.q("UPDATE owner_settings SET maintenance=0 WHERE id=1"); await rp(ctx, OK("BAKIM KAPALI"))
    else:
        db.q("UPDATE owner_settings SET maintenance=1 WHERE id=1"); await rp(ctx, OK("BAKIM AÇIK"))
@kategori("owner")
@bot.command(name="restart", aliases=["rb"], help="Yeniden başlat")
@is_owner()
async def restart(ctx):
    await rp(ctx, OK("RESTART", "3 sn...")); await asyncio.sleep(3); sys.exit(0)
@kategori("owner")
@bot.command(name="yedek", help="<durum/kaydet/yükle>")
@is_owner()
async def yedek(ctx, i: str = "durum", hedef: str = None):
    if not BACKUP_CH: return await rp(ctx, ER("BACKUP_CHANNEL_ID yok"))
    i = i.lower()
    if i == "kaydet":
        await push_backup(bot, "emoji", EMO_CACHE); await push_backup(bot, "pro", pro_snapshot()); await push_backup(bot, "settings", settings_snapshot())
        _HASH["emoji"] = json.dumps(EMO_CACHE, sort_keys=True); _HASH["pro"] = json.dumps(pro_snapshot(), sort_keys=True, default=str); _HASH["set"] = json.dumps(settings_snapshot(), sort_keys=True, default=str)
        await rp(ctx, OK("YEDEKLENDİ"))
    elif i == "yükle":
        h = (hedef or "hepsi").lower(); msg = []
        if h in ("emoji","hepsi"):
            d = await pull_backup(bot, "emoji")
            if d: msg.append(str(emoji_restore(d)))
        if h in ("pro","hepsi"):
            d = await pull_backup(bot, "pro")
            if d: msg.append(str(pro_restore(d)))
        if h in ("settings","ayarlar","hepsi"):
            d = await pull_backup(bot, "settings")
            if d: msg.append(str(settings_restore(d)))
        await rp(ctx, OK("YÜKLENDİ", ", ".join(msg) or "yok"))
    else:
        await rp(ctx, head("log", "YEDEK") + "\n" + KV([(e("dot")+"Emoji", len(EMO_CACHE)), (e("dot")+"Pro", len(db.all("SELECT 1 FROM users WHERE pro=1"))), (e("dot")+"Ayar", sum(len(v) for v in settings_snapshot().values()))]))
@kategori("owner")
@bot.command(name="istatistik-kanal", help="<#kanal|kapat>")
@is_owner()
async def istatistik_kanal(ctx, ch: discord.TextChannel = None):
    if ch is None:
        db.q("DELETE FROM bot_meta WHERE key='stats_ch'"); await rp(ctx, OK("KAPALI"))
    else:
        db.q("INSERT OR REPLACE INTO bot_meta(key,value) VALUES('stats_ch',?)", (str(ch.id),)); await rp(ctx, OK("PANO", ch.mention))
@kategori("owner")
@bot.command(name="güncelleme-kanal", aliases=["guncelleme-kanal"], help="<#kanal|kapat>")
@is_owner()
async def güncelleme_kanal(ctx, ch: discord.TextChannel = None):
    if ch is None:
        db.q("DELETE FROM bot_meta WHERE key='update_ch'"); await rp(ctx, OK("KAPALI"))
    else:
        db.q("INSERT OR REPLACE INTO bot_meta(key,value) VALUES('update_ch',?)", (str(ch.id),)); await rp(ctx, OK("KANAL", ch.mention))
@kategori("owner")
@bot.command(name="sürüm", aliases=["surum"], help="Sürüm")
async def sürüm(ctx): await rp(ctx, head("logo", "v" + BOT_VERSION) + "\n" + "\n".join(e("arrow") + " " + n for n in CHANGELOG.get(BOT_VERSION, [])))
@kategori("owner")
@bot.command(name="v2test", help="Components V2 testi")
@is_owner()
async def v2test(ctx):
    if not HAS_V2:
        return await rp(ctx, ER("V2 YOK", "discord.py " + discord.__version__ + " Container desteklemiyor.\nÇözüm: requirements.txt → `discord.py>=2.6.0` → redeploy."))
    try:
        con = Container(); con.add_item(TextDisplay(head("spark", "V2 TEST") + "\nBu mesajı **çerçeveli kart** içinde görüyorsan V2 çalışıyor!"))
        await ctx.send(view=con)
        await rp(ctx, OK("V2 GÖNDERİLDİ", "discord.py " + discord.__version__))
    except Exception as ex:
        await rp(ctx, ER("V2 HATA", "```\n" + str(ex)[:300] + "\n```\nsürüm: " + discord.__version__))
@kategori("owner")
@bot.command(name="emoji", help="<ayarla/yakala/oto/liste/sıfırla/slotlar>")
@is_owner()
async def emoji_cmd(ctx, i: str = "slotlar", slot: str = None, *, val=None):
    i = i.lower()
    if i in ("ayarla","set"):
        if not slot or not val or "<" not in val: return await rp(ctx, ER("ÖRNEK", "ayarla check <:x:123>"))
        slot = slot.lower()
        if slot not in SLOTS: return await rp(ctx, ER("SLOT"))
        db.q("INSERT OR REPLACE INTO emojis(slot,emoji) VALUES(?,?)", (slot, val)); refresh_emojis(); await rp(ctx, OK("+", slot))
    elif i == "yakala":
        if not slot: return await rp(ctx, ER("ÖRNEK", "yakala check"))
        ref = ctx.message.reference; mg = ref.resolved if ref else None
        if not mg: return await rp(ctx, ER("YANITLA"))
        f = str(mg.emojis[0]) if mg.emojis else None
        if not f:
            mm = re.search(r"<a?:[a-zA-Z0-9_]+:\d+>", mg.content or ""); f = mm.group(0) if mm else None
        if not f: return await rp(ctx, ER("EMOJİ YOK"))
        db.q("INSERT OR REPLACE INTO emojis(slot,emoji) VALUES(?,?)", (slot.lower(), f)); refresh_emojis(); await rp(ctx, OK("+", slot))
    elif i == "oto":
        mp = auto_map_emojis(ctx.guild)
        if not mp: return await rp(ctx, WN("EŞLEŞME YOK"))
        await rp(ctx, OK("OTO", str(len(mp)) + " slot"))
    elif i in ("liste","list"):
        rs = db.all("SELECT * FROM emojis")
        await rp(ctx, head("star", "AYARLI") + "\n" + ("\n".join(e("arrow") + " `" + r["slot"] + "` " + r["emoji"] for r in rs) if rs else "Boş"))
    elif i in ("sıfırla","reset"):
        if slot in (None,"tümü","all"): db.q("DELETE FROM emojis")
        else: db.q("DELETE FROM emojis WHERE slot=?", (slot.lower(),))
        refresh_emojis(); await rp(ctx, OK("SIFIR"))
    else:
        await rp(ctx, head("info", "SLOTLAR") + "\n`" + "`, `".join(SLOTS.keys()) + "`")
@kategori("owner")
@bot.command(name="prover", help="<@üye> [gün]")
@is_half()
async def prover(ctx, u: discord.Member, g: int = 30):
    ensure_user(u.id, str(u)); ex = (datetime.datetime.now() + datetime.timedelta(days=g)).isoformat()
    db.q("UPDATE users SET pro=1, pro_expiry=? WHERE user_id=?", (ex, u.id)); pro_log(u.id, "VERİLDİ", g, ctx.author.id)
    await rp(ctx, OK("PRO", u.mention + " " + str(g) + "g"))
    try: await u.send(OK("PRO OLDUN", str(g) + " gün"))
    except Exception: pass
@kategori("owner")
@bot.command(name="proal", help="<@üye>")
@is_half()
async def proal(ctx, u: discord.Member):
    db.q("UPDATE users SET pro=0, pro_expiry=NULL WHERE user_id=?", (u.id)); pro_log(u.id, "ALINDI", 0, ctx.author.id); await rp(ctx, WN("PRO-", u.mention))
@kategori("owner")
@bot.command(name="prologlar", help="Log")
@is_half()
async def prologlar(ctx, u: discord.User = None):
    rs = db.all("SELECT * FROM pro_logs WHERE user_id=? ORDER BY id DESC LIMIT 15", (u.id,)) if u else db.all("SELECT * FROM pro_logs ORDER BY id DESC LIMIT 15")
    if not rs: return await rp(ctx, e("log") + " Yok")
    await rp(ctx, head("log", "PRO LOG") + "\n" + "\n".join(e("arrow") + " **" + r["action"] + "** <@" + str(r["user_id"]) + "> " + r["ts"][:10] for r in rs))
@kategori("owner")
@bot.command(name="prefix", help="<yeni>")
@is_owner()
async def prefix(ctx, y: str):
    ensure_server(ctx.guild.id); db.q("UPDATE servers SET prefix=? WHERE guild_id=?", (y, ctx.guild.id)); await rp(ctx, OK("PREFIX", y))
@kategori("owner")
@bot.command(name="blacklist", aliases=["bl"], help="<ekle/çıkar> <@üye>")
@is_owner()
async def blacklist(ctx, i: str, u: discord.User, *, s="—"):
    if i.lower() in ("ekle","add"):
        db.q("INSERT OR REPLACE INTO blacklist(user_id,reason) VALUES(?,?)", (u.id, s)); await rp(ctx, OK("+", u.mention))
    elif i.lower() in ("çıkar","remove"):
        db.q("DELETE FROM blacklist WHERE user_id=?", (u.id,)); await rp(ctx, OK("-", u.mention))
    else: await rp(ctx, ER("ekle/çıkar"))
@kategori("owner")
@bot.command(name="durum", aliases=["status"], help="<metin>")
@is_owner()
async def durum(ctx, *, m):
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name=m)); await rp(ctx, OK("DURUM", m[:60]))
@kategori("owner")
@bot.command(name="sunucular", aliases=["guilds"], help="Liste")
@is_owner()
async def sunucular(ctx):
    rs = sorted(bot.guilds, key=lambda g: -(g.member_count or 0))
    await rp(ctx, head("owner", "SUNUCULAR") + "\n" + "\n".join(e("arrow") + " **" + g.name + "** " + str(g.member_count) for g in rs[:15]))
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
# 🚀 BAŞLAT
# ═══════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    bot.run(BOT_TOKEN)
