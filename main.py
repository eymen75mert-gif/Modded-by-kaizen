# ═══════════════════════════════════════════════════════════════════════════
#  💧 KATRE BOT v2.5 — TEK DOSYA • GÖRSEL KARTLAR • KALICI PRO LOG • 80+ KOMUT
#  ─ ENV: BOT_TOKEN, OWNER_ID, SUPPORT_URL
#  ─ pip install -U discord.py Pillow  →  python katre.py
# ═══════════════════════════════════════════════════════════════════════════

import discord
from discord.ext import commands, tasks
from discord.ui import View, Button, Select, Modal, TextInput
import sqlite3, os, json, random, asyncio, datetime, traceback, textwrap, io, re
from collections import deque
from contextlib import redirect_stdout

try:
    from PIL import Image, ImageDraw, ImageFont
    HAS_PIL = True
except Exception:
    HAS_PIL = False

BOT_TOKEN   = os.getenv("BOT_TOKEN", "BURAYA_TOKEN")
OWNER_ID    = int(os.getenv("OWNER_ID", "0"))
SUPPORT_URL = os.getenv("SUPPORT_URL", "https://discord.gg/katre")

C_MAIN  = 0x00A8FF; C_PRO = 0xFFD700; C_ERROR = 0xED4245; C_OK = 0x57F287
C_WARN  = 0xFEBB40; C_GIVE = 0xEB459E; C_FUN = 0x9B59B6; C_MOD = 0xE74C3C
C_ECO   = 0x2ECC71; C_OWNER = 0xFF0000
FOOTER  = "💧 Katre Bot • k!yardım"
SEP     = "┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈"
DICE    = ["⚀", "⚁", "", "⚃", "⚄", ""]
SLOTS   = ["🍒", "🍋", "🍇", "", "7️⃣", "🔔"]
MEDALS  = ["🥇", "🥈", "🥉"]
LINK_RE = re.compile(r"(https?://|discord\.gg/|www\.)", re.I)
FISH    = [("🐟 Levrek", 40), ("🐠 Nemo", 90), ("🐡 Balon", 60), ("🦈 Köpekbalığı", 200), ("🐙 Ahtapot", 120), ("👢 Çizme", 5)]
ORES    = [("⛏️ Kömür", 30), ("🥉 Bakır", 60), ("🥈 Gümüş", 110), ("🥇 Altın", 200), ("💎 Elmas", 400), ("🪨 Taş", 5)]
QUIZ    = [
    ("Türkiye'nin başkenti neresidir?", ["İstanbul", "Ankara", "İzmir", "Bursa"], 1),
    ("Güneş sisteminin en büyük gezegeni?", ["Dünya", "Mars", "Jüpiter", "Satürn"], 2),
    ("Discord.py hangi dilde yazılmıştır?", ["Java", "Python", "C++", "Go"], 1),
    ("Suyun kimyasal formülü?", ["H2O", "CO2", "O2", "NaCl"], 0),
    ("Bir yılda kaç gün vardır?", ["360", "365", "370", "355"], 1),
    ("Karada en hızlı hayvan?", ["Aslan", "Çita", "Kartal", "Tavşan"], 1),
    ("Ay'a ilk ayak basan insan?", ["Buzz Aldrin", "Neil Armstrong", "Gagarin", "Collins"], 1),
    ("1 KB kaç byte'tır?", ["1000", "1024", "512", "2048"], 1),
    ("En derin okyanus?", ["Atlas", "Hint", "Pasifik", "Arktik"], 2),
    ("Python'da liste hangi simge?", ["()", "[]", "{}", "<>"], 1),
]

# ═══════════════════════════════════════════════════════════════════════════
# 🗄️ VERİTABANI (pro_logs = KALICI, restart'ta silinmez)
# ═══════════════════════════════════════════════════════════════════════════
class DB:
    def __init__(self, path="katre.db"):
        self.conn = sqlite3.connect(path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        c = self.conn.cursor()
        c.executescript("""
        CREATE TABLE IF NOT EXISTS servers(
            guild_id INTEGER PRIMARY KEY, prefix TEXT DEFAULT 'k!',
            welcome_ch INTEGER, auto_role INTEGER, rank_on INTEGER DEFAULT 1, joined_at TEXT);
        CREATE TABLE IF NOT EXISTS users(
            user_id INTEGER PRIMARY KEY, name TEXT, xp INTEGER DEFAULT 0,
            level INTEGER DEFAULT 1, coins INTEGER DEFAULT 0, messages INTEGER DEFAULT 0,
            warnings INTEGER DEFAULT 0, pro INTEGER DEFAULT 0, pro_expiry TEXT,
            pro_color TEXT, pro_tag TEXT, xp2 INTEGER DEFAULT 0,
            birthday TEXT, notes TEXT DEFAULT '[]', rep INTEGER DEFAULT 0);
        CREATE TABLE IF NOT EXISTS owner_settings(
            id INTEGER PRIMARY KEY DEFAULT 1, maintenance INTEGER DEFAULT 0,
            status_text TEXT DEFAULT 'k!yardım | 💧 Katre Bot');
        CREATE TABLE IF NOT EXISTS giveaways(
            message_id INTEGER PRIMARY KEY, guild_id INTEGER, channel_id INTEGER, prize TEXT,
            winners INTEGER, end_time REAL, participants TEXT DEFAULT '[]',
            status TEXT DEFAULT 'active', host INTEGER);
        CREATE TABLE IF NOT EXISTS tickets(
            channel_id INTEGER PRIMARY KEY, guild_id INTEGER, user_id INTEGER, status TEXT DEFAULT 'open');
        CREATE TABLE IF NOT EXISTS role_menus(
            menu_id TEXT PRIMARY KEY, guild_id INTEGER, role_ids TEXT);
        CREATE TABLE IF NOT EXISTS blacklist(user_id INTEGER PRIMARY KEY, reason TEXT);
        CREATE TABLE IF NOT EXISTS cmd_stats(cmd TEXT PRIMARY KEY, uses INTEGER DEFAULT 0);
        CREATE TABLE IF NOT EXISTS protections(
            guild_id INTEGER PRIMARY KEY, anti_spam INTEGER DEFAULT 0, anti_flood INTEGER DEFAULT 0,
            anti_raid INTEGER DEFAULT 0, anti_link INTEGER DEFAULT 0, badword INTEGER DEFAULT 0,
            log_ch INTEGER, raid_until REAL DEFAULT 0);
        CREATE TABLE IF NOT EXISTS badwords(guild_id INTEGER, word TEXT, PRIMARY KEY(guild_id, word));
        CREATE TABLE IF NOT EXISTS pro_logs(
            id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, action TEXT,
            days INTEGER DEFAULT 0, by_id INTEGER, ts TEXT);
        CREATE TABLE IF NOT EXISTS afk(user_id INTEGER PRIMARY KEY, reason TEXT, since TEXT);
        CREATE TABLE IF NOT EXISTS snipe(
            channel_id INTEGER PRIMARY KEY, author_id INTEGER, content TEXT, attachment TEXT, ts TEXT);
        CREATE TABLE IF NOT EXISTS marriages(
            id INTEGER PRIMARY KEY AUTOINCREMENT, user1 INTEGER, user2 INTEGER, since TEXT);
        INSERT OR IGNORE INTO owner_settings(id) VALUES (1);
        """)
        for col, typ in (("pro_tag", "TEXT"), ("xp2", "INTEGER DEFAULT 0")):
            try: c.execute("ALTER TABLE users ADD COLUMN " + col + " " + typ)
            except sqlite3.OperationalError: pass
        self.conn.commit()

    def q(self, sql, params=()):
        c = self.conn.cursor(); c.execute(sql, params); self.conn.commit(); return c
    def one(self, sql, params=()):
        r = self.q(sql, params).fetchone(); return dict(r) if r else None
    def all(self, sql, params=()):
        return [dict(r) for r in self.q(sql, params).fetchall()]

db = DB()

def ensure_user(uid, name):
    db.q("INSERT OR IGNORE INTO users(user_id,name) VALUES(?,?)", (uid, name))

def pro_log(user_id, action, days=0, by_id=0):
    """✅ KALICI pro logu — restart'ta kaybolmaz"""
    db.q("INSERT INTO pro_logs(user_id, action, days, by_id, ts) VALUES(?,?,?,?,?)",
         (user_id, action, days, by_id, datetime.datetime.now().isoformat()))

# ═══════════════════════════════════════════════════════════════════════════
# 🛡️ CHECK'LER
# ═══════════════════════════════════════════════════════════════════════════
class OwnerOnly(commands.CheckFailure): pass
class ProOnly(commands.CheckFailure): pass

def is_owner():
    async def pred(ctx):
        if ctx.author.id != OWNER_ID: raise OwnerOnly()
        return True
    return commands.check(pred)

def is_pro():
    async def pred(ctx):
        u = db.one("SELECT pro, pro_expiry FROM users WHERE user_id=?", (ctx.author.id,))
        if u and u["pro"]:
            if u["pro_expiry"]:
                if datetime.datetime.now() < datetime.datetime.fromisoformat(u["pro_expiry"]):
                    return True
                db.q("UPDATE users SET pro=0 WHERE user_id=?", (ctx.author.id,))
                pro_log(ctx.author.id, "SÜRESİ DOLDU")
        raise ProOnly()
    return commands.check(pred)

def kategori(ad):
    def deco(cmd): cmd.kategori = ad; return cmd
    return deco

# ═══════════════════════════════════════════════════════════════════════════
# 🎨 EMBED + GÖRSEL MOTORU
# ═══════════════════════════════════════════════════════════════════════════
def E(title=None, desc=None, color=C_MAIN, thumb=None, img=None, footer=FOOTER):
    em = discord.Embed(title=title, description=desc, color=color,
                       timestamp=datetime.datetime.now())
    if thumb: em.set_thumbnail(url=thumb)
    if img: em.set_image(url=img)
    if footer: em.set_footer(text=footer)
    return em

def LINE(em, name, value, inline=False):
    em.add_field(name=name, value=value, inline=inline)

async def safe_reply(ctx, embed, view=None):
    try: return await ctx.send(embed=embed, view=view)
    except Exception:
        try: return await ctx.author.send(embed=embed, view=view)
        except Exception: return None

def progress_bar(pct, length=12):
    pct = max(0, min(100, int(pct)))
    filled = round(pct / 100 * length)
    return "`[" + "█" * filled + "░" * (length - filled) + "] %" + str(pct) + "`"

def parse_sure(text):
    text = str(text).lower().strip()
    mult = {"m": 1, "dk": 1, "h": 60, "s": 60, "d": 1440, "g": 1440, "w": 10080}
    for suf, m in mult.items():
        if text.endswith(suf):
            return int(float(text[:-len(suf)]) * m)
    return int(float(text))

def fancy(t):
    out = []
    for ch in t:
        o = ord(ch)
        if 97 <= o <= 122:   out.append(chr(o - 97 + 0xFF41))
        elif 65 <= o <= 90:  out.append(chr(o - 65 + 0xFF21))
        elif 48 <= o <= 57:  out.append(chr(o - 48 + 0xFF10))
        else: out.append(ch)
    return "".join(out)

async def fetch_avatar(user, size=256):
    try: return await user.display_avatar.with_size(size).read()
    except Exception: return None

# ─────────────── 🖼️ PIL GÖRSEL ÜRETİCİLER ───────────────
FONT_PATHS = ["/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
              "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
              "/System/Library/Fonts/Helvetica.ttc", "C:/Windows/Fonts/arial.ttf"]
def get_font(size):
    if not HAS_PIL: return None
    for p in FONT_PATHS:
        try: return ImageFont.truetype(p, size)
        except Exception: pass
    try: return ImageFont.load_default(size)
    except Exception: return ImageFont.load_default()

def hex_to_rgb(h, default=(0, 168, 255)):
    try:
        h = h.lstrip("#")
        return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))
    except Exception: return default

def base_card(W, H, accent):
    img = Image.new("RGB", (W, H), (23, 24, 28))
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, W, 8], fill=accent)
    d.rectangle([0, H - 8, W, H], fill=accent)
    d.rounded_rectangle([18, 26, W - 18, H - 26], radius=24, fill=(32, 33, 40))
    return img, d

def paste_circle(img, raw, x, y, size):
    try:
        ava = Image.open(io.BytesIO(raw)).convert("RGBA").resize((size, size))
        mask = Image.new("L", (size, size), 0)
        ImageDraw.Draw(mask).ellipse((0, 0, size, size), fill=255)
        img.paste(ava, (x, y), mask)
        return True
    except Exception: return False

def make_rank_card(name, level, xp, need, coins, rep, pro, tag, accent, avatar_bytes):
    W, H = 900, 340
    img, d = base_card(W, H, accent)
    if avatar_bytes: paste_circle(img, avatar_bytes, 50, 62, 150)
    d = ImageDraw.Draw(img)
    d.ellipse((50, 62, 200, 212), outline=accent, width=4)
    d.text((230, 55), name[:22], font=get_font(40), fill=(255, 255, 255))
    d.text((230, 112), "Seviye " + str(level) + "   •   " + str(xp) + "/" + str(need) +
           " XP   •   " + str(coins) + " coin   •   " + str(rep) + " rep",
           font=get_font(24), fill=(160, 165, 175))
    bx0, by0, bx1, by1 = 230, 170, 850, 200
    d.rounded_rectangle([bx0, by0, bx1, by1], radius=15, fill=(45, 46, 54))
    pct = min(100, (xp / need * 100) if need else 0)
    fw = int((bx1 - bx0) * pct / 100)
    if fw > 12: d.rounded_rectangle([bx0, by0, bx0 + fw, by1], radius=15, fill=accent)
    d.text((bx1 - 60, by0 - 30), "%" + str(int(pct)), font=get_font(24), fill=accent)
    x, y = 230, 230
    if pro:
        d.rounded_rectangle([x, y, x + 90, y + 42], radius=21, fill=(255, 215, 0))
        d.text((x + 24, y + 9), "PRO", font=get_font(24), fill=(20, 20, 20)); x += 105
    if tag:
        tw = 60 + 13 * len(tag[:12])
        d.rounded_rectangle([x, y, x + tw, y + 42], radius=21, fill=(70, 72, 82))
        d.text((x + 16, y + 9), tag[:12], font=get_font(24), fill=(255, 255, 255)); x += tw + 15
    d.text((x, y + 10), "Katre Bot", font=get_font(20), fill=(120, 125, 135))
    return img

def make_leaderboard(entries):
    W, row_h = 820, 62
    H = 150 + row_h * max(1, len(entries)) + 20
    img = Image.new("RGB", (W, H), (23, 24, 28))
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, W, 90], fill=(0, 168, 255))
    d.text((30, 24), "SUNUCU SIRALAMASI", font=get_font(38), fill=(255, 255, 255))
    d.text((W - 300, 36), "Katre Bot  •  Top " + str(len(entries)), font=get_font(22), fill=(225, 240, 255))
    medals = [(255, 215, 0), (192, 192, 192), (205, 127, 50)]
    y = 110
    for i, (name, level, xp, pro) in enumerate(entries):
        if i % 2 == 0: d.rectangle([0, y, W, y + row_h], fill=(30, 31, 37))
        col = medals[i] if i < 3 else (120, 125, 135)
        d.ellipse((25, y + 13, 61, y + 49), fill=col)
        d.text((38, y + 19), str(i + 1), font=get_font(24), fill=(20, 20, 20))
        d.text((80, y + 16), name[:24] + ("  [PRO]" if pro else ""), font=get_font(26), fill=(255, 255, 255))
        d.text((W - 280, y + 18), "Lv." + str(level) + "  •  " + str(xp) + " XP", font=get_font(24), fill=(160, 165, 175))
        y += row_h
    return img

def make_profile_card(name, uid, created, joined, level, coins, rep, pro, tag, avatar_bytes, accent):
    W, H = 900, 400
    img, d = base_card(W, H, accent)
    if avatar_bytes: paste_circle(img, avatar_bytes, 50, 60, 150)
    d = ImageDraw.Draw(img)
    d.ellipse((50, 60, 200, 210), outline=accent, width=4)
    d.text((230, 55), name[:22], font=get_font(40), fill=(255, 255, 255))
    d.text((230, 108), "ID: " + str(uid), font=get_font(22), fill=(140, 145, 155))
    d.text((230, 145), "Hesap: " + created + "   •   Katılım: " + joined, font=get_font(22), fill=(160, 165, 175))
    x, y = 230, 195
    if pro:
        d.rounded_rectangle([x, y, x + 90, y + 40], radius=20, fill=(255, 215, 0))
        d.text((x + 24, y + 8), "PRO", font=get_font(24), fill=(20, 20, 20)); x += 105
    if tag:
        tw = 60 + 13 * len(tag[:12])
        d.rounded_rectangle([x, y, x + tw, y + 40], radius=20, fill=(70, 72, 82))
        d.text((x + 16, y + 8), tag[:12], font=get_font(24), fill=(255, 255, 255))
    d.text((50, 260), "Seviye: " + str(level) + "      Coin: " + str(coins) +
           "      İtibar: " + str(rep), font=get_font(28), fill=(220, 225, 235))
    d.text((50, 310), "Katre Bot", font=get_font(20), fill=(110, 115, 125))
    return img

def make_wallet_card(name, coins, rep, pro, avatar_bytes, accent):
    W, H = 800, 300
    img, d = base_card(W, H, accent)
    if avatar_bytes: paste_circle(img, avatar_bytes, 50, 70, 120)
    d = ImageDraw.Draw(img)
    d.ellipse((50, 70, 170, 190), outline=accent, width=4)
    d.text((210, 65), name[:22], font=get_font(36), fill=(255, 255, 255))
    d.text((210, 115), ("PRO ÜYE  •  " if pro else "") + str(rep) + " itibar", font=get_font(22), fill=(160, 165, 175))
    d.text((210, 155), format(coins, ",").replace(",", ".") + " coin", font=get_font(44), fill=(255, 215, 0))
    return img

def make_stats_card(servers, users, cmds, uptime, ping, total):
    W, H = 860, 400
    img, d = base_card(W, H, (0, 168, 255))
    d.text((50, 50), "KATRE BOT İSTATİSTİK", font=get_font(40), fill=(255, 255, 255))
    d.text((50, 105), "Canlı sistem özeti", font=get_font(22), fill=(150, 155, 165))
    items = [("Sunucu", str(servers)), ("Kullanıcı", str(users)), ("Komut", str(cmds)),
             ("Uptime", uptime), ("Ping", ping + "ms"), ("Kullanım", str(total))]
    for i, (k, v) in enumerate(items):
        cx = 60 + (i % 3) * 260
        cy = 160 + (i // 3) * 100
        d.rounded_rectangle([cx, cy, cx + 240, cy + 85], radius=16, fill=(45, 46, 54))
        d.text((cx + 18, cy + 12), k, font=get_font(20), fill=(150, 155, 165))
        d.text((cx + 18, cy + 40), v[:18], font=get_font(28), fill=(255, 255, 255))
    return img

def make_server_card(name, owner, members, channels, roles, boost, created, icon_bytes):
    W, H = 900, 400
    img, d = base_card(W, H, (87, 101, 240))
    if icon_bytes: paste_circle(img, icon_bytes, 50, 55, 140)
    d = ImageDraw.Draw(img)
    d.ellipse((50, 55, 190, 195), outline=(87, 101, 240), width=4)
    d.text((220, 55), name[:24], font=get_font(38), fill=(255, 255, 255))
    d.text((220, 105), "Kurucu: " + owner[:20] + "   •   Kuruluş: " + created, font=get_font(22), fill=(160, 165, 175))
    stats = [("Üye", str(members)), ("Kanal", str(channels)), ("Rol", str(roles)), ("Boost", str(boost))]
    for i, (k, v) in enumerate(stats):
        cx = 60 + i * 200
        d.rounded_rectangle([cx, 230, cx + 180, 320], radius=16, fill=(45, 46, 54))
        d.text((cx + 16, 242), k, font=get_font(20), fill=(150, 155, 165))
        d.text((cx + 16, 270), v[:10], font=get_font(30), fill=(255, 255, 255))
    return img

def make_love_card(n1, n2, pct, av1, av2):
    W, H = 860, 330
    img, d = base_card(W, H, (255, 105, 180))
    if av1: paste_circle(img, av1, 80, 60, 130)
    if av2: paste_circle(img, av2, W - 210, 60, 130)
    d = ImageDraw.Draw(img)
    d.ellipse((80, 60, 210, 190), outline=(255, 105, 180), width=4)
    d.ellipse((W - 210, 60, W - 80, 190), outline=(255, 105, 180), width=4)
    hx, hy = W // 2, 100
    d.ellipse((hx - 34, hy - 20, hx - 2, hy + 12), fill=(255, 60, 120))
    d.ellipse((hx + 2, hy - 20, hx + 34, hy + 12), fill=(255, 60, 120))
    d.polygon([(hx - 32, hy), (hx + 32, hy), (hx, hy + 42)], fill=(255, 60, 120))
    d.text((hx - 45, hy + 55), str(pct) + "%", font=get_font(44), fill=(255, 105, 180))
    d.text((80, 210), n1[:18], font=get_font(26), fill=(255, 255, 255))
    d.text((W - 280, 210), n2[:18], font=get_font(26), fill=(255, 255, 255))
    bx0, by0, bx1, by1 = 80, 255, W - 80, 282
    d.rounded_rectangle([bx0, by0, bx1, by1], radius=13, fill=(45, 46, 54))
    fw = int((bx1 - bx0) * pct / 100)
    if fw > 10: d.rounded_rectangle([bx0, by0, bx0 + fw, by1], radius=13, fill=(255, 105, 180))
    return img

# ═══════════════════════════════════════════════════════════════════════════
# 🔘 VIEW'LAR
# ═══════════════════════════════════════════════════════════════════════════
CATS = {
    "genel": ("🌐", "Genel & Sistem", C_MAIN),
    "mod":   ("🛡️", "Moderasyon + Koruma", C_MOD),
    "eco":   ("💰", "Ekonomi",        C_ECO),
    "fun":   ("🎮", "Eğlence",        C_FUN),
    "give":  ("🎉", "Çekiliş",        C_GIVE),
    "pro":   ("💎", "Pro Sistem",     C_PRO),
    "owner": ("👑", "Owner Panel",    C_OWNER),
}

def cat_count(bot, key):
    return len([c for c in bot.commands if getattr(c, "kategori", None) == key])

def help_main_embed(bot):
    members = sum(g.member_count or 0 for g in bot.guilds)
    em = E(None, None, C_MAIN)
    em.set_author(name="💧 KATRE BOT • YARDIM MERKEZİ", icon_url=bot.user.display_avatar.url)
    lines = [
        "> 🧩 **" + str(len(bot.commands)) + "** komut • 🌐 **" + str(len(bot.guilds)) + "** sunucu • 👥 **" + str(members) + "** üye",
        "> 👑 Owner: <@" + str(OWNER_ID) + "> • 📡 Ping: **" + str(round(bot.latency * 1000)) + "ms**",
        "", "📂 **Aşağıdaki menüden kategori seç:**", "",
    ]
    for k, (i, n, _) in CATS.items():
        lines.append(i + " **" + n + "** ─ `" + str(cat_count(bot, k)) + "` komut")
    lines += ["", "🔗 Destek: [Tıkla](" + SUPPORT_URL + ")"]
    em.description = "\n".join(lines)
    return em

def cat_embed(bot, key):
    icon, name, color = CATS[key]
    em = E(None, None, color)
    em.set_author(name=icon + " " + name.upper() + " ─ " + str(cat_count(bot, key)) + " KOMUT",
                  icon_url=bot.user.display_avatar.url)
    cmds = [c for c in bot.commands if getattr(c, "kategori", None) == key]
    pre = ""
    if key == "owner":
        pre = "🔒 **Yalnızca bot sahibine özeldir!** Owner olmayan yanıt alamaz.\n" + SEP + "\n"
    lines = ["`k!" + c.name + "` ─ " + (c.help or "—") for c in sorted(cmds, key=lambda x: x.name)]
    em.description = pre + ("\n".join(lines) if lines else "")
    return em

class HelpSelect(Select):
    def __init__(self, bot):
        opts = [discord.SelectOption(label=n, value=k, emoji=i, description=n + " komutları")
                for k, (i, n, _) in CATS.items()]
        super().__init__(placeholder="📂 Bir kategori seçin...", options=opts, min_values=1, max_values=1)
        self.bot = bot
    async def callback(self, it):
        key = self.values[0]
        if key == "owner" and it.user.id != OWNER_ID:
            return await it.response.send_message(embed=E("🔒 YETKİ YOK", "Owner paneli yalnızca bot sahibine açıktır!", C_ERROR), ephemeral=True)
        await it.response.edit_message(embed=cat_embed(self.bot, key), view=self.view)

class HelpView(View):
    def __init__(self, bot):
        super().__init__(timeout=600); self.bot = bot
        self.add_item(HelpSelect(bot))
    @discord.ui.button(label="Ana Menü", style=discord.ButtonStyle.primary, emoji="🏠")
    async def home(self, it, btn):
        await it.response.edit_message(embed=help_main_embed(self.bot), view=self)
    @discord.ui.button(label="İstatistik", style=discord.ButtonStyle.secondary, emoji="📊")
    async def stats(self, it, btn):
        up = datetime.datetime.now() - self.bot.start_time
        em = E(None, None, C_MAIN)
        em.set_author(name="📊 KATRE CANLI İSTATİSTİK", icon_url=self.bot.user.display_avatar.url)
        LINE(em, "🌐 Sunucu", "`" + str(len(self.bot.guilds)) + "`", True)
        LINE(em, "👥 Kullanıcı", "`" + str(sum(g.member_count or 0 for g in self.bot.guilds)) + "`", True)
        LINE(em, "📡 Ping", "`" + str(round(self.bot.latency * 1000)) + "ms`", True)
        LINE(em, "⏱️ Uptime", "`" + str(up).split(".")[0] + "`", True)
        LINE(em, "🧩 Komut", "`" + str(len(self.bot.commands)) + "`", True)
        LINE(em, "🖼️ Görsel", "✅" if HAS_PIL else "❌", True)
        await it.response.send_message(embed=em, ephemeral=True)
    @discord.ui.button(label="Menüyü Kapat", style=discord.ButtonStyle.danger, emoji="🗑️")
    async def close(self, it, btn):
        await it.message.delete()
    def link_buttons(self):
        self.add_item(Button(label="Destek Sunucusu", url=SUPPORT_URL, style=discord.ButtonStyle.link, emoji="🔗"))
        return self

class BroadcastModal(Modal, title="📢 Genel Duyuru"):
    txt = TextInput(label="Duyuru metni", style=discord.TextStyle.paragraph)
    async def on_submit(self, it):
        ok = 0
        for g in it.client.guilds:
            ch = g.system_channel or next((c for c in g.text_channels if c.permissions_for(g.me).send_messages), None)
            if ch:
                try: await ch.send(embed=E("📢 OWNER DUYURUSU", self.txt.value, C_OWNER)); ok += 1
                except Exception: pass
        await it.response.send_message(embed=E("✅ DUYURU", "`" + str(ok) + "/" + str(len(it.client.guilds)) + "` sunucuya iletildi.", C_OK), ephemeral=True)

class OwnerPanelView(View):
    def __init__(self, bot):
        super().__init__(timeout=600); self.bot = bot
    async def guard(self, it):
        if it.user.id != OWNER_ID:
            await it.response.send_message(embed=E("🔒", "Yalnızca owner!", C_ERROR), ephemeral=True); return False
        return True
    @discord.ui.button(label="Bakım Modu", style=discord.ButtonStyle.secondary, emoji="🔧")
    async def bakim(self, it, btn):
        if not await self.guard(it): return
        cur = db.one("SELECT maintenance FROM owner_settings WHERE id=1")["maintenance"]
        db.q("UPDATE owner_settings SET maintenance=? WHERE id=1", (0 if cur else 1,))
        msg = "**🔴 AÇILDI** — Bot sadece owner'a yanıt verir." if not cur else "**🟢 KAPATILDI** — Bot herkese açık."
        await it.response.send_message(embed=E("🔧 BAKIM MODU", msg, C_WARN), ephemeral=True)
    @discord.ui.button(label="İstatistik", style=discord.ButtonStyle.success, emoji="📊")
    async def stats(self, it, btn):
        if not await self.guard(it): return
        up = datetime.datetime.now() - self.bot.start_time
        total = db.one("SELECT SUM(uses) u FROM cmd_stats")["u"] or 0
        em = E(None, None, C_OWNER)
        em.set_author(name="👑 OWNER İSTATİSTİK", icon_url=self.bot.user.display_avatar.url)
        LINE(em, "🌐 Sunucu", "`" + str(len(self.bot.guilds)) + "`", True)
        LINE(em, "👥 Kullanıcı", "`" + str(sum(g.member_count or 0 for g in self.bot.guilds)) + "`", True)
        LINE(em, "⌨️ Kullanım", "`" + str(total) + "`", True)
        LINE(em, "⏱️ Uptime", "`" + str(up).split(".")[0] + "`", True)
        LINE(em, "📜 Pro Log", "`" + str(len(db.all("SELECT 1 FROM pro_logs"))) + "`", True)
        LINE(em, "🎉 Çekiliş", "`" + str(len(db.all("SELECT 1 FROM giveaways WHERE status='active'"))) + "`", True)
        await it.response.send_message(embed=em, ephemeral=True)
    @discord.ui.button(label="Sunucular", style=discord.ButtonStyle.primary, emoji="🖥️")
    async def guilds(self, it, btn):
        if not await self.guard(it): return
        em = E(None, None, C_OWNER)
        em.set_author(name="🖥️ SUNUCULAR (" + str(len(self.bot.guilds)) + ")")
        for i, g in enumerate(sorted(self.bot.guilds, key=lambda x: -(x.member_count or 0))[:10], 1):
            LINE(em, "`" + str(i) + ".` " + g.name, "└ 👥 " + str(g.member_count) + " • ID: `" + str(g.id) + "`")
        await it.response.send_message(embed=em, ephemeral=True)
    @discord.ui.button(label="Duyuru", style=discord.ButtonStyle.primary, emoji="📢")
    async def duyuru(self, it, btn):
        if not await self.guard(it): return
        await it.response.send_modal(BroadcastModal())
    @discord.ui.button(label="Kapat", style=discord.ButtonStyle.danger, emoji="🗑️")
    async def close(self, it, btn):
        if not await self.guard(it): return
        await it.message.delete()

def gw_embed(gw, bot):
    parts = json.loads(gw["participants"])
    em = E(None, None, C_GIVE)
    em.set_author(name="🎉 ÇEKİLİŞ BAŞLADI! 🎉", icon_url=bot.user.display_avatar.url)
    em.description = "### 🎁 Ödül: **" + gw["prize"] + "**\n🔘 **KATIL** butonuna bas!\n" + SEP
    LINE(em, "🏆 Kazanan", "`" + str(gw["winners"]) + "` kişi", True)
    LINE(em, "👥 Katılımcı", "`" + str(len(parts)) + "` kişi", True)
    LINE(em, "⏰ Bitiş", "<t:" + str(int(gw["end_time"])) + ":R>", True)
    LINE(em, "📣 Başlatan", "<@" + str(gw["host"]) + ">", True)
    return em

class GiveawayView(View):
    def __init__(self, bot):
        super().__init__(timeout=None); self.bot = bot
    @discord.ui.button(label="Katıl", style=discord.ButtonStyle.success, emoji="🎉", custom_id="katre_gw_join", row=0)
    async def join(self, it, btn):
        gw = db.one("SELECT * FROM giveaways WHERE message_id=?", (it.message.id,))
        if not gw or gw["status"] != "active":
            return await it.response.send_message(embed=E("❌", "Çekiliş aktif değil!", C_ERROR), ephemeral=True)
        parts = json.loads(gw["participants"])
        if str(it.user.id) in parts:
            return await it.response.send_message(embed=E("ℹ️ ZATEN KATILDIN", "**" + gw["prize"] + "** çekilişindesin! 🍀", C_WARN), ephemeral=True)
        parts.append(str(it.user.id))
        db.q("UPDATE giveaways SET participants=? WHERE message_id=?", (json.dumps(parts), it.message.id))
        try: await it.message.edit(embed=gw_embed(dict(gw, participants=json.dumps(parts)), self.bot), view=self)
        except Exception: pass
        await it.response.send_message(embed=E("✅ KATILDIN!", "**" + gw["prize"] + "** çekilişine kaydoldun! 🍀", C_OK), ephemeral=True)
    @discord.ui.button(label="Ayrıl", style=discord.ButtonStyle.secondary, emoji="🚪", custom_id="katre_gw_leave", row=0)
    async def leave(self, it, btn):
        gw = db.one("SELECT * FROM giveaways WHERE message_id=?", (it.message.id,))
        if not gw or gw["status"] != "active":
            return await it.response.send_message(embed=E("❌", "Çekiliş aktif değil!", C_ERROR), ephemeral=True)
        parts = json.loads(gw["participants"])
        if str(it.user.id) not in parts:
            return await it.response.send_message(embed=E("ℹ️", "Katılmamışsın.", C_WARN), ephemeral=True)
        parts.remove(str(it.user.id))
        db.q("UPDATE giveaways SET participants=? WHERE message_id=?", (json.dumps(parts), it.message.id))
        try: await it.message.edit(embed=gw_embed(dict(gw, participants=json.dumps(parts)), self.bot), view=self)
        except Exception: pass
        await it.response.send_message(embed=E("🚪 AYRILDIN", "Çekilişten çıktın.", C_WARN), ephemeral=True)
    @discord.ui.button(label="Bitir", style=discord.ButtonStyle.primary, emoji="🏁", custom_id="katre_gw_end", row=1)
    async def end(self, it, btn):
        if not it.user.guild_permissions.administrator:
            return await it.response.send_message(embed=E("🔒", "Yönetici olmalısın!", C_ERROR), ephemeral=True)
        await finalize_giveaway(self.bot, it.message.id)
        await it.response.send_message(embed=E("🏁", "Çekiliş sonlandırıldı!", C_OK), ephemeral=True)
    @discord.ui.button(label="Yeniden Çek", style=discord.ButtonStyle.secondary, emoji="🎲", custom_id="katre_gw_reroll", row=1)
    async def reroll(self, it, btn):
        if not it.user.guild_permissions.administrator:
            return await it.response.send_message(embed=E("🔒", "Yönetici olmalısın!", C_ERROR), ephemeral=True)
        gw = db.one("SELECT * FROM giveaways WHERE message_id=?", (it.message.id,))
        if not gw: return
        parts = json.loads(gw["participants"])
        if not parts:
            return await it.response.send_message(embed=E("❌", "Katılımcı yok!", C_ERROR), ephemeral=True)
        w = self.bot.get_user(int(random.choice(parts)))
        await it.channel.send(embed=E("🎲 YENİDEN ÇEKİLİŞ", "### 🎁 " + gw["prize"] + "\n🏆 Kazanan: " + (w.mention if w else "?"), C_PRO))
        await it.response.defer()
    @discord.ui.button(label="+1 Saat", style=discord.ButtonStyle.success, emoji="⏳", custom_id="katre_gw_extend", row=1)
    async def extend(self, it, btn):
        if not it.user.guild_permissions.administrator:
            return await it.response.send_message(embed=E("🔒", "Yönetici olmalısın!", C_ERROR), ephemeral=True)
        gw = db.one("SELECT * FROM giveaways WHERE message_id=?", (it.message.id,))
        if not gw or gw["status"] != "active":
            return await it.response.send_message(embed=E("❌", "Aktif değil!", C_ERROR), ephemeral=True)
        new = gw["end_time"] + 3600
        db.q("UPDATE giveaways SET end_time=? WHERE message_id=?", (new, it.message.id))
        try: await it.message.edit(embed=gw_embed(dict(gw, end_time=new), self.bot), view=self)
        except Exception: pass
        await it.response.send_message(embed=E("⏳ UZATILDI", "Bitiş: <t:" + str(int(new)) + ":R>", C_OK), ephemeral=True)
    @discord.ui.button(label="İptal", style=discord.ButtonStyle.danger, emoji="🛑", custom_id="katre_gw_cancel", row=1)
    async def cancel(self, it, btn):
        if not it.user.guild_permissions.administrator:
            return await it.response.send_message(embed=E("🔒", "Yönetici olmalısın!", C_ERROR), ephemeral=True)
        gw = db.one("SELECT * FROM giveaways WHERE message_id=?", (it.message.id,))
        if not gw: return
        db.q("UPDATE giveaways SET status='cancelled' WHERE message_id=?", (it.message.id,))
        try: await it.message.edit(embed=E("🛑 İPTAL", "**" + gw["prize"] + "** iptal edildi.", C_ERROR), view=None)
        except Exception: pass
        await it.response.send_message(embed=E("🛑", "İptal edildi.", C_WARN), ephemeral=True)

class RoleButton(Button):
    def __init__(self, role_id, label, custom_id, row):
        super().__init__(label=label[:78], style=discord.ButtonStyle.secondary, emoji="🎭", custom_id=custom_id, row=row)
        self.role_id = role_id
    async def callback(self, it):
        role = it.guild.get_role(self.role_id)
        if not role:
            return await it.response.send_message(embed=E("❌", "Rol silinmiş.", C_ERROR), ephemeral=True)
        if role in it.user.roles:
            await it.user.remove_roles(role, reason="Rol menüsü"); msg = "❌ **" + role.name + "** alındı."
        else:
            await it.user.add_roles(role, reason="Rol menüsü"); msg = "✅ **" + role.name + "** verildi!"
        await it.response.send_message(embed=E("🎭 ROL GÜNCELLENDİ", msg, C_OK), ephemeral=True)

class RoleMenuView(View):
    def __init__(self, menu_id, roles):
        super().__init__(timeout=None)
        for i, (rid, name) in enumerate(roles):
            self.add_item(RoleButton(rid, name, "katre_role_" + menu_id + "_" + str(rid), i // 5))

class TicketModal(Modal, title="🎫 Destek Talebi"):
    konu = TextInput(label="Konu", max_length=100)
    aciklama = TextInput(label="Açıklama", style=discord.TextStyle.paragraph)
    async def on_submit(self, it):
        ex = db.one("SELECT * FROM tickets WHERE user_id=? AND status='open'", (it.user.id,))
        if ex:
            return await it.response.send_message(embed=E("❌", "Açık talebin var: <#" + str(ex["channel_id"]) + ">", C_WARN), ephemeral=True)
        guild = it.guild
        cat = discord.utils.get(guild.categories, name="💧 DESTEK")
        if not cat: cat = await guild.create_category("💧 DESTEK")
        ow = {guild.default_role: discord.PermissionOverwrite(view_channel=False),
              it.user: discord.PermissionOverwrite(view_channel=True, send_messages=True, attach_files=True, embed_links=True),
              guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True, manage_channels=True, manage_messages=True)}
        for r in guild.me.roles:
            if r.permissions.administrator or r.permissions.manage_messages:
                ow[r] = discord.PermissionOverwrite(view_channel=True, send_messages=True)
        ch = await guild.create_text_channel("destek-" + it.user.name, category=cat, overwrites=ow)
        db.q("INSERT INTO tickets(channel_id,guild_id,user_id) VALUES(?,?,?)", (ch.id, guild.id, it.user.id))
        em = E(None, None, C_MAIN, thumb=it.user.display_avatar.url)
        em.set_author(name="🎫 DESTEK TALEBİ")
        em.description = "**Konu:** " + self.konu.value + "\n**Açıklama:** " + self.aciklama.value + "\n" + SEP + "\n👤 " + it.user.mention + "\n⏳ Ekibimiz birazdan yanında!"
        await ch.send(embed=em, view=TicketCloseView())
        await it.response.send_message(embed=E("✅ TALEP", "Kanalın: " + ch.mention, C_OK), ephemeral=True)

class TicketOpenView(View):
    def __init__(self): super().__init__(timeout=None)
    @discord.ui.button(label="Destek Talebi Oluştur", style=discord.ButtonStyle.primary, emoji="🎫", custom_id="katre_ticket_open")
    async def open_ticket(self, it, btn):
        await it.response.send_modal(TicketModal())

class TicketCloseView(View):
    def __init__(self): super().__init__(timeout=None)
    @discord.ui.button(label="Talebi Kapat", style=discord.ButtonStyle.danger, emoji="🔒", custom_id="katre_ticket_close")
    async def close_ticket(self, it, btn):
        t = db.one("SELECT * FROM tickets WHERE channel_id=?", (it.channel.id,))
        if not t:
            return await it.response.send_message(embed=E("❌", "Talep yok.", C_ERROR), ephemeral=True)
        if not (it.user.guild_permissions.administrator or it.user.id == t["user_id"]):
            return await it.response.send_message(embed=E("🔒", "Kapatamazsın!", C_ERROR), ephemeral=True)
        db.q("UPDATE tickets SET status='closed' WHERE channel_id=?", (it.channel.id,))
        await it.response.send_message(embed=E("🔒 KAPATILIYOR", "Kanal 10 sn içinde silinecek...", C_WARN))
        await asyncio.sleep(10)
        try: await it.channel.delete()
        except Exception: pass

class ConfirmView(View):
    def __init__(self, timeout=30):
        super().__init__(timeout=timeout); self.value = None
    @discord.ui.button(label="Onayla", style=discord.ButtonStyle.danger, emoji="✅")
    async def yes(self, it, btn):
        self.value = True; self.stop()
        await it.response.edit_message(embed=E("⏳ İŞLENİYOR...", "Uygulanıyor...", C_WARN), view=None)
    @discord.ui.button(label="Vazgeç", style=discord.ButtonStyle.secondary, emoji="❌")
    async def no(self, it, btn):
        self.value = False; self.stop()
        await it.response.edit_message(embed=E("❌ İPTAL", "İşlem iptal.", C_WARN), view=None)

class SetupConfirmView(View):
    def __init__(self, timeout=60):
        super().__init__(timeout=timeout); self.value = None
    @discord.ui.button(label="Kurulumu Başlat", style=discord.ButtonStyle.success, emoji="🏗️")
    async def yes(self, it, btn):
        self.value = True; self.stop()
        await it.response.edit_message(embed=E("🏗️ KURULUM", "Sunucu kuruluyor... (≈10 sn)", C_WARN), view=None)
    @discord.ui.button(label="Vazgeç", style=discord.ButtonStyle.secondary, emoji="❌")
    async def no(self, it, btn):
        self.value = False; self.stop()
        await it.response.edit_message(embed=E("❌ İPTAL", "Kurulum iptal.", C_WARN), view=None)

# ═══════════════════════════════════════════════════════════════════════════
# 🤖 BOT
# ═══════════════════════════════════════════════════════════════════════════
class KatreBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.all()
        super().__init__(command_prefix=self.get_prefix, intents=intents, case_insensitive=True,
                         help_command=None,
                         allowed_mentions=discord.AllowedMentions(users=True, roles=False, everyone=False))
        self.start_time = datetime.datetime.now()
        self.xp_cd = {}; self._st_i = 0
        self.spam = {}; self.flood = {}; self.joins = {}

    async def get_prefix(self, message):
        p = "k!"
        if message.guild:
            s = db.one("SELECT prefix FROM servers WHERE guild_id=?", (message.guild.id,))
            if s: p = s["prefix"]
        base = {p, p.lower(), p.upper()}
        if self.user:
            base.add("<@" + str(self.user.id) + "> "); base.add("<@!" + str(self.user.id) + "> ")
        return list(base)

    async def setup_hook(self):
        self.gw_view = GiveawayView(self)
        self.add_view(self.gw_view); self.add_view(TicketOpenView()); self.add_view(TicketCloseView())
        self.status_loop.start(); self.gw_checker.start(); self.pro_checker.start()

    async def on_ready(self):
        try:
            for row in db.all("SELECT * FROM role_menus"):
                guild = self.get_guild(row["guild_id"])
                if not guild: continue
                roles = [(rid, guild.get_role(rid).name) for rid in json.loads(row["role_ids"]) if guild.get_role(rid)]
                if roles: self.add_view(RoleMenuView(row["menu_id"], roles))
        except Exception: pass
        print("")
        print("╔═══════════════════════════════════════════════╗")
        print("║      💧  K A T R E   B O T   v2.5  💧           ║")
        print("║  Görsel Kartlar • Kalıcı Pro Log • 80+ Komut   ║")
        print("╚═══════════════════════════════════════════════╝")
        print("✅ Giriş: " + str(self.user) + "  🌐 Sunucu: " + str(len(self.guilds)) +
              "  🧩 Komut: " + str(len(self.commands)) + "  🖼️ PIL: " + ("✅" if HAS_PIL else "❌"))
        await self.change_presence(status=discord.Status.online,
            activity=discord.Activity(type=discord.ActivityType.watching, name="k!yardım | 💧 Katre Bot"))

    @tasks.loop(seconds=12)
    async def status_loop(self):
        owner = self.get_user(OWNER_ID)
        oname = owner.display_name if owner else "Owner"
        members = sum(g.member_count or 0 for g in self.guilds)
        msgs = [(discord.ActivityType.watching, "k!yardım | 💧 Katre Bot"),
                (discord.ActivityType.playing, str(len(self.guilds)) + " sunucuda! 🌐"),
                (discord.ActivityType.listening, str(members) + " kullanıcıya 🎧"),
                (discord.ActivityType.competing, "k!quiz ile yarış! 🧠"),
                (discord.ActivityType.watching, "Owner: " + oname + " 👑"),
                (discord.ActivityType.playing, "k!pro ile ayrıcalık 💎"),
                (discord.ActivityType.listening, "k!koruma • Sunucun güvende 🛡️")]
        t, m = msgs[self._st_i % len(msgs)]; self._st_i += 1
        try: await self.change_presence(status=discord.Status.online, activity=discord.Activity(type=t, name=m))
        except Exception: pass

    @tasks.loop(seconds=15)
    async def gw_checker(self):
        now = datetime.datetime.now().timestamp()
        for gw in db.all("SELECT * FROM giveaways WHERE status='active' AND end_time<=?", (now,)):
            await finalize_giveaway(self, gw["message_id"])

    @tasks.loop(minutes=5)
    async def pro_checker(self):
        now = datetime.datetime.now()
        rows = db.all("SELECT user_id FROM users WHERE pro=1 AND pro_expiry IS NOT NULL AND pro_expiry<?", (now.isoformat(),))
        for r in rows:
            db.q("UPDATE users SET pro=0 WHERE user_id=?", (r["user_id"],))
            pro_log(r["user_id"], "SÜRESİ DOLDU")   # ✅ kalıcı log

    async def punish(self, member, minutes, reason):
        try:
            await member.timeout(datetime.timedelta(minutes=minutes), reason=reason); return True
        except Exception: return False

    async def mod_log(self, guild, embed):
        p = db.one("SELECT log_ch FROM protections WHERE guild_id=?", (guild.id,))
        if p and p["log_ch"]:
            ch = guild.get_channel(p["log_ch"])
            if ch:
                try: await ch.send(embed=embed); return
                except Exception: pass

    async def run_protections(self, message):
        try:
            if not message.guild or message.author.guild_permissions.administrator: return
            if not message.guild.me.guild_permissions.moderate_members: return
            p = db.one("SELECT * FROM protections WHERE guild_id=?", (message.guild.id,))
            if not p: return
            now = datetime.datetime.now().timestamp()
            content = message.content or ""
            if p["anti_link"] and LINK_RE.search(content):
                try: await message.delete()
                except Exception: pass
                await self.mod_log(message.guild, E("🔗 ANTİ-LİNK", message.author.mention + " link → silindi.", C_MOD))
            elif p["badword"]:
                ws = [w["word"] for w in db.all("SELECT word FROM badwords WHERE guild_id=?", (message.guild.id,))]
                low = content.lower()
                if any(w and w in low for w in ws):
                    try: await message.delete()
                    except Exception: pass
                    okc = await self.punish(message.author, 1, "Küfür filtresi")
                    await self.mod_log(message.guild, E("🤬 KÜFÜR", message.author.mention + " → 1dk susturma " + ("✅" if okc else "(yetki yok)"), C_MOD))
            if p["anti_spam"]:
                dq = self.spam.setdefault(message.guild.id, {}).setdefault(message.author.id, deque())
                dq.append(now)
                while dq and now - dq[0] > 5: dq.popleft()
                if len(dq) >= 7:
                    dq.clear()
                    okc = await self.punish(message.author, 5, "Anti-spam")
                    try: await message.channel.purge(limit=6, check=lambda m: m.author.id == message.author.id)
                    except Exception: pass
                    await self.mod_log(message.guild, E("🚫 ANTİ-SPAM", message.author.mention + " → 5dk susturma " + ("✅" if okc else "(yetki yok)"), C_MOD))
            if p["anti_flood"]:
                key = (message.guild.id, message.author.id)
                prev = self.flood.get(key)
                cnt = (prev[1] + 1) if (prev and prev[0] == content and now - prev[2] < 10) else 1
                self.flood[key] = (content, cnt, now)
                if cnt >= 3:
                    self.flood[key] = (content, 0, now)
                    try: await message.delete()
                    except Exception: pass
                    okc = await self.punish(message.author, 2, "Anti-flood")
                    await self.mod_log(message.guild, E("🌊 ANTİ-FLOOD", message.author.mention + " → 2dk susturma " + ("✅" if okc else "(yetki yok)"), C_MOD))
        except Exception:
            traceback.print_exc()

    async def on_message(self, message):
        if message.author.bot: return
        try:
            maint = db.one("SELECT maintenance FROM owner_settings WHERE id=1")["maintenance"]
            if maint and message.author.id != OWNER_ID: return
            if db.one("SELECT 1 FROM blacklist WHERE user_id=?", (message.author.id,)): return
        except Exception: traceback.print_exc()
        # 😴 AFK kontrolü
        try:
            afk = db.one("SELECT * FROM afk WHERE user_id=?", (message.author.id,))
            if afk:
                db.q("DELETE FROM afk WHERE user_id=?", (message.author.id,))
                await message.channel.send(embed=E("🔄 AFK BİTTİ", message.author.mention + " tekrar aramızda! 🎉", C_OK))
            if message.guild:
                for m in message.mentions:
                    a = db.one("SELECT * FROM afk WHERE user_id=?", (m.id,))
                    if a:
                        await message.channel.send(embed=E("😴 AFK", m.mention + " şu an AFK: **" + (a["reason"] or "—") +
                                                           "**\n📅 " + a["since"][:16].replace("T", " "), C_WARN))
                        break
        except Exception: pass
        await self.run_protections(message)
        try:
            ensure_user(message.author.id, str(message.author))
            if message.guild:
                db.q("UPDATE users SET messages=messages+1, name=? WHERE user_id=?", (str(message.author), message.author.id))
                now = datetime.datetime.now().timestamp()
                srv = db.one("SELECT rank_on FROM servers WHERE guild_id=?", (message.guild.id,))
                if (not srv or srv["rank_on"]) and now - self.xp_cd.get(message.author.id, 0) > 60:
                    self.xp_cd[message.author.id] = now
                    u = db.one("SELECT xp, level, xp2 FROM users WHERE user_id=?", (message.author.id))
                    gain = random.randint(5, 15) * (2 if u["xp2"] else 1)
                    xp, lvl = u["xp"] + gain, u["level"]
                    need = lvl * 100
                    if xp >= need:
                        xp -= need; lvl += 1
                        coin = random.randint(50, 150)
                        db.q("UPDATE users SET coins=coins+? WHERE user_id=?", (coin, message.author.id))
                        em = E(None, None, C_PRO, thumb=message.author.display_avatar.url)
                        em.set_author(name="🎉 SEVİYE ATLADIN!", icon_url=message.display_avatar.url)
                        em.description = message.author.mention + " artık **Seviye " + str(lvl) + "**! 🚀\n" + SEP + "\n🎁 **+" + str(coin) + " coin**"
                        LINE(em, "📊 İlerleme", progress_bar(xp / (lvl * 100) * 100))
                        try: await message.channel.send(embed=em)
                        except Exception: pass
                    db.q("UPDATE users SET xp=?, level=? WHERE user_id=?", (xp, lvl, message.author.id))
        except Exception: traceback.print_exc()
        await self.process_commands(message)

    async def on_message_delete(self, message):
        try:
            if message.author.bot or not message.guild: return
            db.q("INSERT OR REPLACE INTO snipe(channel_id, author_id, content, attachment, ts) VALUES(?,?,?,?,?)",
                 (message.channel.id, message.author.id, (message.content or "")[:1000],
                  message.attachments[0].url if message.attachments else None,
                  datetime.datetime.now().isoformat()))
        except Exception: pass

    async def on_command_completion(self, ctx):
        db.q("INSERT INTO cmd_stats(cmd,uses) VALUES(?,1) ON CONFLICT(cmd) DO UPDATE SET uses=uses+1", (ctx.command.name,))

    async def on_command_error(self, ctx, error):
        if isinstance(error, OwnerOnly): return
        if isinstance(error, ProOnly):
            v = View(); v.add_item(Button(label="Pro Destek", url=SUPPORT_URL, style=discord.ButtonStyle.link, emoji="💎"))
            await safe_reply(ctx, E("💎 PRO GEREKLİ!", "Bu komut yalnızca **Pro üyelere** özeldir!\n" + SEP + "\n📋 `k!pro`", C_PRO), v); return
        if isinstance(error, commands.CommandNotFound):
            await safe_reply(ctx, E("❓ BULUNAMADI", "Tüm komutlar: `k!yardım`", C_WARN)); return
        if isinstance(error, commands.MissingRequiredArgument):
            await safe_reply(ctx, E("❌ EKSİK ARGÜMAN", "`k!" + ctx.command.name + " " + ctx.command.signature + "`", C_ERROR)); return
        if isinstance(error, commands.CommandOnCooldown):
            await safe_reply(ctx, E("⏳ BEKLE", "**" + str(int(error.retry_after)) + " sn** sonra tekrar dene.", C_WARN)); return
        if isinstance(error, commands.MissingPermissions):
            await safe_reply(ctx, E("🔒 YETKİ YOK", "`" + ", ".join(error.missing_permissions) + "`", C_ERROR)); return
        if isinstance(error, commands.CheckFailure):
            await safe_reply(ctx, E("🔒 YETKİ YOK", "Bu komutu kullanamazsın!", C_ERROR)); return
        if isinstance(error, commands.CommandInvokeError):
            orig = error.original
            if isinstance(orig, discord.Forbidden):
                try:
                    await ctx.author.send(embed=E("🔒 YETKİ", "**#" + str(ctx.channel) + "** kanalında yetkim yok!\nYöneticiye söyle: Mesaj+Embed yetkisi.", C_ERROR))
                except Exception: pass
                return
            error = orig
        await safe_reply(ctx, E("⚠️ HATA", "```\n" + str(error)[:900] + "\n```", C_ERROR))
        traceback.print_exc()

    async def on_member_join(self, member):
        ensure_user(member.id, str(member))
        try:
            p = db.one("SELECT * FROM protections WHERE guild_id=?", (member.guild.id,))
            if p and p["anti_raid"]:
                now = datetime.datetime.now().timestamp()
                dq = self.joins.setdefault(member.guild.id, deque())
                dq.append(now)
                while dq and now - dq[0] > 10: dq.popleft()
                if len(dq) >= 8 and now > (p["raid_until"] or 0):
                    db.q("UPDATE protections SET raid_until=? WHERE guild_id=?", (now + 600, member.guild.id))
                    alert = E("⚔️ RAID ALGILANDI!", "10sn'de 8+ giriş → Raid modu 10dk aktif!", C_ERROR)
                    await self.mod_log(member.guild, alert)
                if (p["raid_until"] or 0) > now:
                    try: await member.send(embed=E("⚔️ RAID MODU", member.guild.name + " raid korumasında. Sonra tekrar dene!", C_WARN))
                    except Exception: pass
                    try: await member.kick(reason="Anti-raid")
                    except Exception: pass
                    await self.mod_log(member.guild, E("⚔️ ANTİ-RAID", str(member) + " engellendi.", C_ERROR))
                    return
        except Exception: traceback.print_exc()
        s = db.one("SELECT * FROM servers WHERE guild_id=?", (member.guild.id,))
        if not s: return
        if s["auto_role"]:
            r = member.guild.get_role(s["auto_role"])
            if r:
                try: await member.add_roles(r, reason="Otorol")
                except Exception: pass
        if s["welcome_ch"]:
            ch = member.guild.get_channel(s["welcome_ch"])
            if ch:
                em = E(None, None, C_OK, thumb=member.display_avatar.url)
                em.set_author(name="👋 HOŞ GELDİN!", icon_url=member.display_avatar.url)
                em.description = "### " + member.mention + " aramıza katıldı!\n🎉 **" + str(member.guild.member_count) + "** üye olduk!\n" + SEP + "\n📅 Hesap: <t:" + str(int(member.created_at.timestamp())) + ":R>"
                try: await ch.send(embed=em)
                except Exception: pass

    async def on_guild_join(self, guild):
        db.q("INSERT OR IGNORE INTO servers(guild_id, joined_at) VALUES(?,?)", (guild.id, datetime.datetime.now().isoformat()))
        db.q("INSERT OR IGNORE INTO protections(guild_id) VALUES(?)", (guild.id,))
        ch = guild.system_channel or next((c for c in guild.text_channels if c.permissions_for(guild.me).send_messages), None)
        if ch:
            em = E(None, None, C_MAIN, thumb=self.user.display_avatar.url)
            em.set_author(name="💧 KATRE BOT ARANIZDA!", icon_url=self.user.display_avatar.url)
            em.description = "**" + guild.name + "** hoş geldim! 🎉\n" + SEP + "\n📚 `k!yardım` • 🏗️ `k!kurulum` • 🛡️ `k!koruma antispam aç` • 🖼️ `k!rank`"
            v = View(); v.add_item(Button(label="Destek", url=SUPPORT_URL, style=discord.ButtonStyle.link, emoji="🔗"))
            await ch.send(embed=em, view=v)

async def finalize_giveaway(bot, message_id):
    gw = db.one("SELECT * FROM giveaways WHERE message_id=?", (message_id,))
    if not gw or gw["status"] != "active": return
    parts = json.loads(gw["participants"])
    db.q("UPDATE giveaways SET status='ended' WHERE message_id=?", (message_id,))
    ch = bot.get_channel(gw["channel_id"])
    if not parts:
        if ch:
            try: await ch.send(embed=E("🎊 BİTTİ", "**" + gw["prize"] + "** — katılımcı yok!", C_WARN))
            except Exception: pass
        return
    n = min(gw["winners"], len(parts))
    winners = [bot.get_user(int(w)) for w in random.sample(parts, n)]
    mentions = "\n".join(w.mention if w else "?" for w in winners)
    if ch:
        try:
            await ch.send(embed=E("🎊 ÇEKİLİŞ BİTTİ!", "### 🎁 " + gw["prize"] + "\n🏆 **KAZANANLAR:**\n" + mentions + "\n" + SEP + "\n👥 " + str(len(parts)) + " katılımcı", C_PRO))
            msg = await ch.fetch_message(message_id)
            done = gw_embed(gw, bot); done.set_author(name="🎊 ÇEKİLİŞ SONA ERDİ"); done.color = C_PRO
            done.add_field(name="🏆 Kazananlar", value=mentions, inline=False)
            await msg.edit(embed=done, view=bot.gw_view)
        except Exception: pass

bot = KatreBot()

# ═══════════════════════════════════════════════════════════════════════════
# 🌐 GENEL
# ═══════════════════════════════════════════════════════════════════════════
@kategori("genel")
@bot.command(name="yardım", aliases=["yardim", "help", "komutlar", "menü"], help="Yardım menüsünü açar")
@commands.cooldown(1, 5, commands.BucketType.user)
async def yardim(ctx):
    await ctx.send(embed=help_main_embed(bot), view=HelpView(bot).link_buttons())

@kategori("genel")
@bot.command(name="ping", help="Bot gecikmesini gösterir")
async def ping(ctx):
    ms = round(bot.latency * 1000)
    await safe_reply(ctx, E("🏓 PONG!", ("🟢" if ms < 100 else ("🟡" if ms < 200 else "🔴")) + " **" + str(ms) + "ms**", C_OK))

@kategori("genel")
@bot.command(name="istatistik", aliases=["stats"], help="Görsel bot istatistikleri")
async def istatistik(ctx):
    up = str(datetime.datetime.now() - bot.start_time).split(".")[0]
    total = db.one("SELECT SUM(uses) u FROM cmd_stats")["u"] or 0
    if HAS_PIL:
        img = make_stats_card(len(bot.guilds), sum(g.member_count or 0 for g in bot.guilds),
                              len(bot.commands), up, str(round(bot.latency * 1000)), total)
        buf = io.BytesIO(); img.save(buf, format="PNG"); buf.seek(0)
        em = E(None, None, C_MAIN); em.set_image(url="attachment://stats.png")
        LINE(em, "👑 Owner", "<@" + str(OWNER_ID) + ">")
        await ctx.send(file=discord.File(buf, filename="stats.png"), embed=em)
    else:
        em = E(None, None, C_MAIN)
        em.set_author(name="📊 KATRE İSTATİSTİK", icon_url=bot.user.display_avatar.url)
        LINE(em, "🌐 Sunucu", "`" + str(len(bot.guilds)) + "`", True)
        LINE(em, "🧩 Komut", "`" + str(len(bot.commands)) + "`", True)
        LINE(em, "⏱️ Uptime", "`" + up + "`", True)
        await safe_reply(ctx, em)

@kategori("genel")
@bot.command(name="davet", aliases=["invite"], help="Bot davet linki")
async def davet(ctx):
    url = discord.utils.oauth_url(str(bot.user.id), permissions=discord.Permissions(administrator=True))
    em = E(None, None, C_MAIN)
    em.set_author(name="➕ KATRE BOT'U EKLE", icon_url=bot.user.display_avatar.url)
    v = View()
    v.add_item(Button(label="Botu Ekle", url=url, style=discord.ButtonStyle.link, emoji="➕"))
    v.add_item(Button(label="Destek", url=SUPPORT_URL, style=discord.ButtonStyle.link, emoji="🔗"))
    await safe_reply(ctx, em, v)

@kategori("genel")
@bot.command(name="avatar", aliases=["av", "pp"], help="Kullanıcı avatarı")
async def avatar(ctx, user: discord.Member = None):
    user = user or ctx.author
    em = E("🖼️ " + user.display_name, color=C_MAIN, img=user.display_avatar.url)
    v = View(); v.add_item(Button(label="Tarayıcıda Aç", url=user.display_avatar.url, style=discord.ButtonStyle.link, emoji="🔗"))
    await safe_reply(ctx, em, v)

@kategori("genel")
@bot.command(name="profil", aliases=["profile"], help="Görsel profil kartı")
@commands.cooldown(1, 3, commands.BucketType.user)
async def profil(ctx, user: discord.Member = None):
    user = user or ctx.author
    ensure_user(user.id, str(user))
    u = db.one("SELECT * FROM users WHERE user_id=?", (user.id,))
    accent = hex_to_rgb(u["pro_color"]) if (u["pro"] and u["pro_color"]) else ((255, 215, 0) if u["pro"] else (0, 168, 255))
    if HAS_PIL:
        av = await fetch_avatar(user)
        img = make_profile_card(user.display_name, user.id,
                                user.created_at.strftime("%d.%m.%Y"),
                                user.joined_at.strftime("%d.%m.%Y") if user.joined_at else "—",
                                u["level"], u["coins"], u["rep"], bool(u["pro"]), u["pro_tag"], av, accent)
        buf = io.BytesIO(); img.save(buf, format="PNG"); buf.seek(0)
        em = E(None, None, int(accent[0]) * 65536 + int(accent[1]) * 256 + int(accent[2]))
        em.set_image(url="attachment://profil.png")
        await ctx.send(file=discord.File(buf, filename="profil.png"), embed=em)
    else:
        em = E(None, None, C_MAIN, thumb=user.display_avatar.url)
        em.set_author(name="👤 " + user.display_name, icon_url=user.display_avatar.url)
        LINE(em, "📈 Seviye", "`" + str(u["level"]) + "`", True)
        LINE(em, "🪙 Coin", "`" + str(u["coins"]) + "`", True)
        LINE(em, "⭐ Rep", "`" + str(u["rep"]) + "`", True)
        await safe_reply(ctx, em)

@kategori("genel")
@bot.command(name="sunucubilgi", aliases=["serverinfo"], help="Görsel sunucu kartı")
async def sunucubilgi(ctx):
    g = ctx.guild
    if HAS_PIL:
        icon = None
        try:
            if g.icon: icon = await g.icon.with_size(256).read()
        except Exception: pass
        owner = bot.get_user(g.owner_id)
        img = make_server_card(g.name, owner.display_name if owner else str(g.owner_id),
                               g.member_count, len(g.channels), len(g.roles),
                               g.premium_subscription_count or 0, g.created_at.strftime("%d.%m.%Y"), icon)
        buf = io.BytesIO(); img.save(buf, format="PNG"); buf.seek(0)
        em = E(None, None, 0x5765F0); em.set_image(url="attachment://sunucu.png")
        await ctx.send(file=discord.File(buf, filename="sunucu.png"), embed=em)
    else:
        em = E(None, None, C_MAIN, thumb=g.icon.url if g.icon else None)
        em.set_author(name="🌐 " + g.name)
        LINE(em, "👥 Üye", "`" + str(g.member_count) + "`", True)
        LINE(em, "💬 Kanal", "`" + str(len(g.channels)) + "`", True)
        LINE(em, "🎭 Rol", "`" + str(len(g.roles)) + "`", True)
        await safe_reply(ctx, em)

@kategori("genel")
@bot.command(name="rank", aliases=["seviye", "level"], help="Görsel seviye kartı")
@commands.cooldown(1, 3, commands.BucketType.user)
async def rank(ctx, user: discord.Member = None):
    user = user or ctx.author
    ensure_user(user.id, str(user))
    u = db.one("SELECT * FROM users WHERE user_id=?", (user.id,))
    need = u["level"] * 100
    accent = hex_to_rgb(u["pro_color"]) if (u["pro"] and u["pro_color"]) else ((255, 215, 0) if u["pro"] else (0, 168, 255))
    if HAS_PIL:
        av = await fetch_avatar(user)
        img = make_rank_card(user.display_name, u["level"], u["xp"], need, u["coins"], u["rep"],
                             bool(u["pro"]), u["pro_tag"], accent, av)
        buf = io.BytesIO(); img.save(buf, format="PNG"); buf.seek(0)
        em = E(None, None, int(accent[0]) * 65536 + int(accent[1]) * 256 + int(accent[2]))
        em.set_image(url="attachment://rank.png")
        await ctx.send(file=discord.File(buf, filename="rank.png"), embed=em)
    else:
        em = E(None, None, C_MAIN, thumb=user.display_avatar.url)
        em.set_author(name="📈 " + user.display_name, icon_url=user.display_avatar.url)
        LINE(em, "🏆 Seviye", "`" + str(u["level"]) + "`", True)
        LINE(em, "✨ XP", "`" + str(u["xp"]) + "/" + str(need) + "`", True)
        LINE(em, "📊", progress_bar(min(100, u["xp"] / need * 100)))
        await safe_reply(ctx, em)

@kategori("genel")
@bot.command(name="sıralama", aliases=["sirala", "top", "lb"], help="Görsel sıralama")
async def sıralama(ctx):
    rows = db.all("SELECT * FROM users ORDER BY level DESC, xp DESC LIMIT 10")
    if not rows: return await safe_reply(ctx, E("📊", "Henüz veri yok!", C_WARN))
    if HAS_PIL:
        entries = []
        for r in rows:
            mem = bot.get_user(r["user_id"])
            entries.append((mem.display_name if mem else (r["name"] or "?"), r["level"], r["xp"], bool(r["pro"])))
        img = make_leaderboard(entries)
        buf = io.BytesIO(); img.save(buf, format="PNG"); buf.seek(0)
        em = E(None, None, C_PRO); em.set_image(url="attachment://top10.png")
        await ctx.send(file=discord.File(buf, filename="top10.png"), embed=em)
    else:
        em = E(None, None, C_PRO); txt = ""
        for i, r in enumerate(rows):
            txt += (MEDALS[i] if i < 3 else "**" + str(i+1) + ".**") + " <@" + str(r["user_id"]) + "> — **Lv." + str(r["level"]) + "**\n"
        em.description = txt
        await safe_reply(ctx, em)

@kategori("genel")
@bot.command(name="snipe", help="Kanalda silinen son mesajı gösterir")
@commands.cooldown(1, 3, commands.BucketType.user)
async def snipe(ctx):
    s = db.one("SELECT * FROM snipe WHERE channel_id=?", (ctx.channel.id,))
    if not s: return await safe_reply(ctx, E("📸", "Bu kanalda silinmiş mesaj kaydı yok.", C_WARN))
    em = E(None, None, C_FUN)
    em.set_author(name="📸 SNIPE — silinen son mesaj")
    em.description = ("**İçerik:**\n" + (s["content"] or "_metin yok_")[:1500]) if s["content"] else "_Metin yok, ek vardı._"
    if s["attachment"]: em.set_image(url=s["attachment"])
    LINE(em, "👤 Kullanıcı", "<@" + str(s["author_id"]) + ">", True)
    LINE(em, "📅 Tarih", s["ts"][:16].replace("T", " "), True)
    await safe_reply(ctx, em)

@kategori("genel")
@bot.command(name="afk", help="[sebep] — AFK moduna geçersin")
async def afk(ctx, *, sebep="Belirtilmedi"):
    db.q("INSERT OR REPLACE INTO afk(user_id, reason, since) VALUES(?,?,?)",
         (ctx.author.id, sebep[:100], datetime.datetime.now().isoformat()))
    await safe_reply(ctx, E("😴 AFK MODU", "Artık AFK'sın: **" + sebep[:100] + "**\nMentionleyenlere haber vereceğim.", C_WARN))

@kategori("genel")
@bot.command(name="rep", aliases=["itibar"], help="<@üye> — İtibar ver (12s)")
@commands.cooldown(1, 43200, commands.BucketType.user)
async def rep(ctx, user: discord.Member):
    if user.id == ctx.author.id: return await safe_reply(ctx, E("❌", "Kendine veremezsin!", C_ERROR))
    ensure_user(user.id, str(user))
    db.q("UPDATE users SET rep=rep+1 WHERE user_id=?", (user.id,))
    await safe_reply(ctx, E("⭐ İTİBAR", ctx.author.mention + " → " + user.mention + " +1 ⭐", C_PRO))

@kategori("genel")
@bot.command(name="destek", aliases=["ticket"], help="Destek paneli (Yönetici)")
@commands.has_permissions(administrator=True)
async def destek(ctx):
    em = E(None, None, C_MAIN)
    em.set_author(name="🎫 DESTEK MERKEZİ", icon_url=bot.user.display_avatar.url)
    em.description = "Butona tıkla, formu doldur! 💧\n" + SEP
    await ctx.send(embed=em, view=TicketOpenView())
    try: await ctx.message.delete()
    except Exception: pass

@kategori("genel")
@bot.command(name="not", aliases=["note"], help="<metin> — Not kaydet")
async def not_(ctx, *, metin):
    ensure_user(ctx.author.id, str(ctx.author))
    u = db.one("SELECT notes FROM users WHERE user_id=?", (ctx.author.id,))
    notes = json.loads(u["notes"]); notes.append({"t": metin, "d": datetime.datetime.now().isoformat()})
    db.q("UPDATE users SET notes=? WHERE user_id=?", (json.dumps(notes), ctx.author.id))
    await safe_reply(ctx, E("📝 NOT", "Kaydedildi! Toplam: `" + str(len(notes)) + "`", C_OK))

@kategori("genel")
@bot.command(name="notlar", aliases=["notes"], help="Notlarını listeler")
async def notlar(ctx):
    u = db.one("SELECT notes FROM users WHERE user_id=?", (ctx.author.id,))
    notes = json.loads(u["notes"]) if u else []
    if not notes: return await safe_reply(ctx, E("📝", "Notun yok.", C_WARN))
    em = E("📝 NOTLARIN (" + str(len(notes)) + ")", color=C_MAIN)
    for i, n in enumerate(notes[-8:], 1):
        LINE(em, "`" + str(i) + ".`", n["t"][:80])
    await safe_reply(ctx, em)

@kategori("genel")
@bot.command(name="doğumgünü", aliases=["dogumgunu"], help="<gün> <ay> — Doğum günü")
async def doğumgünü(ctx, gün: int, ay: int):
    if not (1 <= gün <= 31 and 1 <= ay <= 12): return await safe_reply(ctx, E("❌", "Örnek: `k!doğumgünü 24 8`", C_ERROR))
    db.q("UPDATE users SET birthday=? WHERE user_id=?", (str(gün) + "." + str(ay), ctx.author.id))
    await safe_reply(ctx, E("🎂 KAYDEDİLDİ", "**" + str(gün) + "." + str(ay) + "** 🎈", C_PRO))

@kategori("genel")
@bot.command(name="doğumgünleri", aliases=["dogumgunleri"], help="Bu ayın doğum günleri")
async def doğumgünleri(ctx):
    now = datetime.datetime.now()
    rows = [r for r in db.all("SELECT user_id,birthday FROM users WHERE birthday IS NOT NULL")
            if r["birthday"] and int(r["birthday"].split(".")[1]) == now.month]
    if not rows: return await safe_reply(ctx, E("🎂", "Bu ay yok!", C_WARN))
    em = E("🎂 " + str(now.month) + ". AY", color=C_PRO)
    for r in sorted(rows, key=lambda x: int(x["birthday"].split(".")[0])):
        LINE(em, "🎈 " + r["birthday"], "<@" + str(r["user_id"]) + ">")
    await safe_reply(ctx, em)

@kategori("genel")
@bot.command(name="hatırlat", aliases=["hatirlat"], help="<dk> <metin> — Hatırlatıcı")
async def hatırlat(ctx, dk: int, *, metin):
    if dk < 1 or dk > 1440: return await safe_reply(ctx, E("❌", "1-1440 dk!", C_ERROR))
    await safe_reply(ctx, E("⏰ KURULDU", "**" + str(dk) + " dk** sonra: " + metin, C_OK))
    await asyncio.sleep(dk * 60)
    await ctx.send(ctx.author.mention + " ⏰ **HATIRLATMA:** " + metin)

@kategori("genel")
@bot.command(name="botkontrol", aliases=["check"], help="Bot yetki teşhisi")
@commands.has_permissions(administrator=True)
async def botkontrol(ctx):
    p = ctx.channel.permissions_for(ctx.guild.me)
    checks = [("Mesaj Gör", p.view_channel), ("Mesaj Gönder", p.send_messages), ("Embed", p.embed_links),
              ("Tepki", p.add_reactions), ("Mesaj Yönet", p.manage_messages), ("Timeout", p.moderate_members),
              ("Rol Yönet", p.manage_roles), ("Kanal Yönet", p.manage_channels), ("At", p.kick_members), ("Ban", p.ban_members)]
    em = E(None, None, C_MAIN)
    em.set_author(name="🩺 BOT KONTROL — #" + ctx.channel.name, icon_url=bot.user.display_avatar.url)
    em.description = "\n".join(("✅ " if ok else "❌ ") + n for n, ok in checks)
    miss = [n for n, ok in checks if not ok]
    LINE(em, "🔧", "Tam yetkili!" if not miss else "Eksik: **" + ", ".join(miss) + "**")
    await safe_reply(ctx, em)

# ═══════════════════════════════════════════════════════════════════════════
# 🛡️ MODERASYON + KORUMA
# ═══════════════════════════════════════════════════════════════════════════
@kategori("mod")
@bot.command(name="yasakla", aliases=["ban"], help="<@üye> [sebep] — Yasaklar")
@commands.has_permissions(ban_members=True)
@commands.bot_has_permissions(ban_members=True)
async def yasakla(ctx, user: discord.Member, *, sebep="Belirtilmedi"):
    v = ConfirmView()
    await ctx.send(embed=E("⚠️ ONAY", "**" + str(user) + "** banlansın mı?\nSebep: " + sebep, C_WARN), view=v)
    await v.wait()
    if v.value is None: return await safe_reply(ctx, E("⌛", "Zaman aşımı.", C_WARN))
    if v.value:
        try: await user.send(embed=E("🔨 BAN", "**" + ctx.guild.name + "**\nSebep: " + sebep, C_ERROR))
        except Exception: pass
        await user.ban(reason=str(ctx.author) + " | " + sebep)
        await safe_reply(ctx, E("🔨 BAN", user.mention + " yasaklandı!", C_MOD))

@kategori("mod")
@bot.command(name="at", aliases=["kick"], help="<@üye> [sebep] — Atar")
@commands.has_permissions(kick_members=True)
@commands.bot_has_permissions(kick_members=True)
async def at(ctx, user: discord.Member, *, sebep="Belirtilmedi"):
    v = ConfirmView()
    await ctx.send(embed=E("⚠️ ONAY", "**" + str(user) + "** atılsın mı?", C_WARN), view=v)
    await v.wait()
    if v.value is None: return await safe_reply(ctx, E("⌛", "Zaman aşımı.", C_WARN))
    if v.value:
        await user.kick(reason=str(ctx.author) + " | " + sebep)
        await safe_reply(ctx, E("👢 ATILDI", user.mention, C_MOD))

@kategori("mod")
@bot.command(name="uyar", aliases=["warn"], help="<@üye> [sebep] — Uyarır")
@commands.has_permissions(manage_messages=True)
async def uyar(ctx, user: discord.Member, *, sebep="Belirtilmedi"):
    ensure_user(user.id, str(user))
    db.q("UPDATE users SET warnings=warnings+1 WHERE user_id=?", (user.id,))
    w = db.one("SELECT warnings FROM users WHERE user_id=?", (user.id,))["warnings"]
    await safe_reply(ctx, E("⚠️ UYARI", user.mention + " • Toplam: `" + str(w) + "`", C_WARN))

@kategori("mod")
@bot.command(name="uyarılar", aliases=["warns"], help="[<@üye>] — Uyarılar")
async def uyarılar(ctx, user: discord.Member = None):
    user = user or ctx.author
    ensure_user(user.id, str(user))
    w = db.one("SELECT warnings FROM users WHERE user_id=?", (user.id,))["warnings"]
    await safe_reply(ctx, E("⚠️", user.mention + " → **" + str(w) + "** uyarı", C_WARN))

@kategori("mod")
@bot.command(name="temizle", aliases=["purge", "sil"], help="<adet> — Mesaj siler")
@commands.has_permissions(manage_messages=True)
@commands.bot_has_permissions(manage_messages=True)
async def temizle(ctx, adet: int):
    if not 1 <= adet <= 500: return await safe_reply(ctx, E("❌", "1-500!", C_ERROR))
    await ctx.channel.purge(limit=adet + 1)
    m = await ctx.send(embed=E("🧹", "**" + str(adet) + "** mesaj silindi!", C_OK))
    await m.delete(delay=5)

@kategori("mod")
@bot.command(name="yavaşmod", aliases=["slowmode"], help="<sn> — Yavaş mod")
@commands.has_permissions(manage_channels=True)
async def yavaşmod(ctx, sn: int):
    await ctx.channel.edit(slowmode_delay=sn)
    await safe_reply(ctx, E("🐌", "**" + str(sn) + " sn**" if sn else "Kapatıldı", C_OK))

@kategori("mod")
@bot.command(name="kilit", aliases=["lock"], help="Kanalı kilitler")
@commands.has_permissions(manage_channels=True)
async def kilit(ctx):
    await ctx.channel.set_permissions(ctx.guild.default_role, send_messages=False)
    await safe_reply(ctx, E("🔒 KİLİT", ctx.channel.mention, C_MOD))

@kategori("mod")
@bot.command(name="kilitaç", aliases=["unlock"], help="Kilidi açar")
@commands.has_permissions(manage_channels=True)
async def kilitaç(ctx):
    await ctx.channel.set_permissions(ctx.guild.default_role, send_messages=None)
    await safe_reply(ctx, E("🔓 AÇIK", ctx.channel.mention, C_OK))

@kategori("mod")
@bot.command(name="otorol", aliases=["autorol"], help="<@rol|kapat> — Otorol")
@commands.has_permissions(administrator=True)
async def otorol(ctx, *, arg):
    if arg.lower() in ("kapat", "off", "0"):
        db.q("UPDATE servers SET auto_role=NULL WHERE guild_id=?", (ctx.guild.id,))
        return await safe_reply(ctx, E("✅", "Otorol kapalı.", C_OK))
    role = await commands.RoleConverter().convert(ctx, arg)
    db.q("UPDATE servers SET auto_role=? WHERE guild_id=?", (role.id, ctx.guild.id))
    await safe_reply(ctx, E("✅ OTOROL", role.mention, C_OK))

@kategori("mod")
@bot.command(name="hoşgeldin", aliases=["hosgeldin"], help="<#kanal|kapat> — Hoşgeldin")
@commands.has_permissions(administrator=True)
async def hoşgeldin(ctx, ch: discord.TextChannel = None):
    if ch is None:
        db.q("UPDATE servers SET welcome_ch=NULL WHERE guild_id=?", (ctx.guild.id,))
        return await safe_reply(ctx, E("✅", "Kapalı.", C_OK))
    db.q("UPDATE servers SET welcome_ch=? WHERE guild_id=?", (ch.id, ctx.guild.id))
    await safe_reply(ctx, E("✅", ch.mention, C_OK))

@kategori("mod")
@bot.command(name="butonrol", aliases=["rolmenü"], help="<@rol...> — Rol menüsü")
@commands.has_permissions(administrator=True)
async def butonrol(ctx, roles: commands.Greedy[discord.Role], *, açıklama="Rollerinizi butonlarla alın!"):
    if not roles or len(roles) > 25: return await safe_reply(ctx, E("❌", "1-25 rol!", C_ERROR))
    menu_id = str(random.randint(10**11, 10**12 - 1))
    db.q("INSERT OR REPLACE INTO role_menus(menu_id,guild_id,role_ids) VALUES(?,?,?)",
         (menu_id, ctx.guild.id, json.dumps([r.id for r in roles])))
    em = E(None, None, C_MAIN)
    em.set_author(name="🎭 ROL MENÜSÜ")
    em.description = açıklama + "\n" + SEP + "\n" + "\n".join("🔹 " + r.mention for r in roles)
    view = RoleMenuView(menu_id, [(r.id, r.name) for r in roles])
    bot.add_view(view)
    await ctx.send(embed=em, view=view)

@kategori("mod")
@bot.command(name="koruma", help="<mod> <aç/kapat> — Koruma modülleri")
@commands.has_permissions(administrator=True)
async def koruma(ctx, mod: str, durum: str):
    mod = mod.lower().replace("-", "").replace("_", "")
    col = {"antispam": "anti_spam", "antiflood": "anti_flood", "antiraid": "anti_raid",
           "antilink": "anti_link", "badword": "badword", "küfür": "badword"}.get(mod)
    if not col: return await safe_reply(ctx, E("❌", "Modüller: `antispam antiflood antiraid antilink badword`", C_ERROR))
    db.q("INSERT OR IGNORE INTO protections(guild_id) VALUES(?)", (ctx.guild.id,))
    val = 1 if durum.lower() in ("aç", "ac", "on", "1") else 0
    db.q("UPDATE protections SET " + col + "=? WHERE guild_id=?", (val, ctx.guild.id))
    await safe_reply(ctx, E("🛡️ KORUMA", "**" + mod.upper() + "** " + ("AÇIK ✅" if val else "KAPALI ❌") + "\nLog: `k!korumalog #kanal`", C_OK))

@kategori("mod")
@bot.command(name="korumadurum", aliases=["korumalar"], help="Koruma durumu")
async def korumadurum(ctx):
    p = db.one("SELECT * FROM protections WHERE guild_id=?", (ctx.guild.id,)) or {}
    def st(v): return "✅ Açık" if v else "❌ Kapalı"
    em = E(None, None, C_MOD)
    em.set_author(name="🛡️ KORUMA — " + ctx.guild.name)
    LINE(em, "🚫 Spam", st(p.get("anti_spam")), True)
    LINE(em, "🌊 Flood", st(p.get("anti_flood")), True)
    LINE(em, "⚔️ Raid", st(p.get("anti_raid")), True)
    LINE(em, "🔗 Link", st(p.get("anti_link")), True)
    LINE(em, "🤬 Küfür", st(p.get("badword")), True)
    LINE(em, "📜 Log", ("<#" + str(p["log_ch"]) + ">") if p.get("log_ch") else "—", True)
    await safe_reply(ctx, em)

@kategori("mod")
@bot.command(name="korumalog", help="<#kanal> — Koruma log kanalı")
@commands.has_permissions(administrator=True)
async def korumalog(ctx, ch: discord.TextChannel):
    db.q("INSERT OR IGNORE INTO protections(guild_id) VALUES(?)", (ctx.guild.id,))
    db.q("UPDATE protections SET log_ch=? WHERE guild_id=?", (ch.id, ctx.guild.id))
    await safe_reply(ctx, E("📜 LOG", ch.mention, C_OK))

@kategori("mod")
@bot.command(name="badword", help="<ekle/sil/liste> [kelime] — Küfür filtresi")
@commands.has_permissions(administrator=True)
async def badword(ctx, işlem: str, *, kelime: str = None):
    gid = ctx.guild.id
    if işlem.lower() in ("ekle", "add"):
        if not kelime: return await safe_reply(ctx, E("❌", "Kelime gir!", C_ERROR))
        db.q("INSERT OR IGNORE INTO badwords(guild_id, word) VALUES(?,?)", (gid, kelime.lower()))
        await safe_reply(ctx, E("🤬 EKLENDİ", "`" + kelime.lower() + "`", C_OK))
    elif işlem.lower() in ("sil", "remove"):
        db.q("DELETE FROM badwords WHERE guild_id=? AND word=?", (gid, (kelime or "").lower()))
        await safe_reply(ctx, E("🤬 SİLİNDİ", str(kelime), C_OK))
    elif işlem.lower() in ("liste", "list"):
        ws = [w["word"] for w in db.all("SELECT word FROM badwords WHERE guild_id=?", (gid,))]
        await safe_reply(ctx, E("🤬 LİSTE (" + str(len(ws)) + ")", ("`" + "`, `".join(ws) + "`") if ws else "Boş", C_WARN))
    else:
        await safe_reply(ctx, E("❌", "`ekle/sil/liste`", C_ERROR))

@kategori("mod")
@bot.command(name="raidmodu", help="<aç/kapat> — Manuel raid kilidi")
@commands.has_permissions(administrator=True)
async def raidmodu(ctx, mod: str):
    now = datetime.datetime.now().timestamp()
    db.q("INSERT OR IGNORE INTO protections(guild_id) VALUES(?)", (ctx.guild.id,))
    if mod.lower() in ("aç", "ac", "on"):
        db.q("UPDATE protections SET raid_until=? WHERE guild_id=?", (now + 600, ctx.guild.id))
        await safe_reply(ctx, E("⚔️ RAID", "10 dk boyunca girişler engelli!", C_ERROR))
    else:
        db.q("UPDATE protections SET raid_until=0 WHERE guild_id=?", (ctx.guild.id,))
        await safe_reply(ctx, E("⚔️ RAID", "Kapatıldı.", C_OK))

@kategori("mod")
@bot.command(name="kurulum", aliases=["sunucukur", "setup"], help="Tek komutla sunucu kurar")
@commands.has_permissions(administrator=True)
@commands.bot_has_permissions(manage_channels=True, manage_roles=True)
async def kurulum(ctx):
    v = SetupConfirmView()
    await ctx.send(embed=E("🏗️ KURULUM", "4 kategori • 12 kanal • 4 rol + hoşgeldin\n**Onaylıyor musun?**", C_MAIN), view=v)
    await v.wait()
    if not v.value: return
    g = ctx.guild; ck = 0
    try:
        r_yon = await g.create_role(name="Yönetici", color=discord.Color(0xE74C3C), permissions=discord.Permissions(administrator=True))
        r_mod = await g.create_role(name="Moderatör", color=discord.Color(0x3498DB),
                                    permissions=discord.Permissions(kick_members=True, manage_messages=True, moderate_members=True))
        await g.create_role(name="Üye", color=discord.Color(0x2ECC71))
        r_bot = await g.create_role(name="Bot", color=discord.Color(0xFFD700), hoist=True)
        try: await g.me.add_roles(r_bot)
        except Exception: pass
        k1 = await g.create_category("📢 BİLGİ"); k2 = await g.create_category("💬 SOHBET")
        k3 = await g.create_category("🎧 SES"); k4 = await g.create_category("🛡️ YÖNETİM")
        ow = {g.default_role: discord.PermissionOverwrite(view_channel=True, send_messages=False)}
        for n in ("duyurular", "kurallar", "etkinlik"):
            await g.create_text_channel(n, category=k1, overwrites=ow); ck += 1
        hg = await g.create_text_channel("hoşgeldin", category=k1, overwrites=ow); ck += 1
        for n in ("genel", "sohbet", "medya", "bot-komut"):
            await g.create_text_channel(n, category=k2); ck += 1
        for n in ("Sohbet 1", "Sohbet 2", "Müzik"):
            await g.create_voice_channel(n, category=k3); ck += 1
        owy = {g.default_role: discord.PermissionOverwrite(view_channel=False),
               r_yon: discord.PermissionOverwrite(view_channel=True),
               r_mod: discord.PermissionOverwrite(view_channel=True)}
        await g.create_text_channel("yetkili-sohbet", category=k4, overwrites=owy); ck += 1
        db.q("UPDATE servers SET welcome_ch=? WHERE guild_id=?", (hg.id, g.id))
        await safe_reply(ctx, E("✅ KURULUM BİTTİ!", "📁 4 kategori • 💬 " + str(ck) + " kanal • 🎭 4 rol\n👋 " + hg.mention, C_OK))
    except discord.Forbidden:
        await safe_reply(ctx, E("❌ YETKİ", "Kanal+Rol yönet yetkisi gerekli.", C_ERROR))
    except Exception as e:
        await safe_reply(ctx, E("⚠️", "```\n" + str(e)[:400] + "\n```", C_ERROR))

# ═══════════════════════════════════════════════════════════════════════════
# 💰 EKONOMİ
# ═══════════════════════════════════════════════════════════════════════════
@kategori("eco")
@bot.command(name="cüzdan", aliases=["balance", "para"], help="Görsel cüzdan kartı")
async def cüzdan(ctx, user: discord.Member = None):
    user = user or ctx.author
    ensure_user(user.id, str(user))
    u = db.one("SELECT * FROM users WHERE user_id=?", (user.id,))
    if HAS_PIL:
        av = await fetch_avatar(user)
        accent = (255, 215, 0) if u["pro"] else (46, 204, 113)
        img = make_wallet_card(user.display_name, u["coins"], u["rep"], bool(u["pro"]), av, accent)
        buf = io.BytesIO(); img.save(buf, format="PNG"); buf.seek(0)
        em = E(None, None, C_ECO); em.set_image(url="attachment://cuzdan.png")
        await ctx.send(file=discord.File(buf, filename="cuzdan.png"), embed=em)
    else:
        await safe_reply(ctx, E("💰 " + user.display_name, "**" + str(u["coins"]) + "** coin • ⭐ " + str(u["rep"]), C_ECO))

@kategori("eco")
@bot.command(name="günlük", aliases=["gunluk", "daily"], help="Günlük coin")
@commands.cooldown(1, 86400, commands.BucketType.user)
async def günlük(ctx):
    ensure_user(ctx.author.id, str(ctx.author))
    u = db.one("SELECT * FROM users WHERE user_id=?", (ctx.author.id,))
    bonus = random.randint(150, 400) + (250 if u["pro"] else 0)
    db.q("UPDATE users SET coins=coins+? WHERE user_id=?", (bonus, ctx.author.id))
    await safe_reply(ctx, E("🎁 GÜNLÜK", "**+" + str(bonus) + " coin** 🪙" + ("\n💎 Pro bonusu dahil!" if u["pro"] else ""), C_ECO))

@kategori("eco")
@bot.command(name="çalış", aliases=["calis", "work"], help="Çalış coin kazan")
@commands.cooldown(1, 1800, commands.BucketType.user)
async def çalış(ctx):
    jobs = [("💻 Yazılım geliştirdin", 200, 400), ("🎨 Tasarım yaptın", 150, 300), ("📹 İçerik ürettin", 180, 350),
            ("🍕 Pizzacılık yaptın", 100, 220), ("🚕 Şoförlük yaptın", 120, 260), ("📚 Ders verdin", 160, 320)]
    job, a, b = random.choice(jobs)
    pay = random.randint(a, b)
    db.q("UPDATE users SET coins=coins+? WHERE user_id=?", (pay, ctx.author.id))
    await safe_reply(ctx, E("💼 ÇALIŞTIN", job + " → **+" + str(pay) + " coin**", C_ECO))

@kategori("eco")
@bot.command(name="balık", aliases=["fish"], help="Balık tut (5dk)")
@commands.cooldown(1, 300, commands.BucketType.user)
async def balık(ctx):
    name, val = random.choice(FISH)
    db.q("UPDATE users SET coins=coins+? WHERE user_id=?", (val, ctx.author.id))
    await safe_reply(ctx, E("🎣 BALIK AVI", name + " → **+" + str(val) + " coin**", C_ECO))

@kategori("eco")
@bot.command(name="maden", aliases=["mine"], help="Maden kaz (5dk)")
@commands.cooldown(1, 300, commands.BucketType.user)
async def maden(ctx):
    name, val = random.choice(ORES)
    db.q("UPDATE users SET coins=coins+? WHERE user_id=?", (val, ctx.author.id))
    await safe_reply(ctx, E("⛏️ MADEN", name + " → **+" + str(val) + " coin**", C_ECO))

@kategori("eco")
@bot.command(name="soy", aliases=["rob"], help="<@üye> — Soymayı dener")
@commands.cooldown(1, 600, commands.BucketType.user)
async def soy(ctx, user: discord.Member):
    if user.id == ctx.author.id or user.bot: return await safe_reply(ctx, E("❌", "Geçersiz!", C_ERROR))
    ensure_user(user.id, str(user))
    t = db.one("SELECT coins FROM users WHERE user_id=?", (user.id,))
    me = db.one("SELECT coins FROM users WHERE user_id=?", (ctx.author.id,))
    if t["coins"] < 200: return await safe_reply(ctx, E("❌", "Çalınacak coin yok!", C_ERROR))
    if random.random() < 0.45:
        steal = random.randint(50, min(500, t["coins"]))
        db.q("UPDATE users SET coins=coins-? WHERE user_id=?", (steal, user.id))
        db.q("UPDATE users SET coins=coins+? WHERE user_id=?", (steal, ctx.author.id))
        await safe_reply(ctx, E("🦹 BAŞARILI", "**+" + str(steal) + " coin** çaldın!", C_ECO))
    else:
        fine = min(me["coins"], random.randint(50, 200))
        db.q("UPDATE users SET coins=coins-? WHERE user_id=?", (fine, ctx.author.id))
        await safe_reply(ctx, E("🚨 YAKALANDIN", "**-" + str(fine) + " coin** ceza!", C_ERROR))

@kategori("eco")
@bot.command(name="transfer", aliases=["gönder"], help="<@üye> <miktar> — Transfer")
async def transfer(ctx, user: discord.Member, miktar: int):
    if miktar <= 0 or user.id == ctx.author.id: return await safe_reply(ctx, E("❌", "Geçersiz!", C_ERROR))
    ensure_user(user.id, str(user))
    me = db.one("SELECT coins FROM users WHERE user_id=?", (ctx.author.id,))
    if me["coins"] < miktar: return await safe_reply(ctx, E("❌", "Yetersiz bakiye!", C_ERROR))
    db.q("UPDATE users SET coins=coins-? WHERE user_id=?", (miktar, ctx.author.id))
    db.q("UPDATE users SET coins=coins+? WHERE user_id=?", (miktar, user.id))
    await safe_reply(ctx, E("💸 TRANSFER", "**" + str(miktar) + " coin** → " + user.mention, C_ECO))

@kategori("eco")
@bot.command(name="bahis", aliases=["bet"], help="<miktar> — x2 bahis")
@commands.cooldown(1, 10, commands.BucketType.user)
async def bahis(ctx, miktar: int):
    if miktar <= 0: return await safe_reply(ctx, E("❌", "Geçersiz!", C_ERROR))
    me = db.one("SELECT coins FROM users WHERE user_id=?", (ctx.author.id,))
    if me["coins"] < miktar: return await safe_reply(ctx, E("❌", "Yetersiz!", C_ERROR))
    win = random.random() < 0.5
    db.q("UPDATE users SET coins=coins+? WHERE user_id=?", (miktar if win else -miktar, ctx.author.id))
    await safe_reply(ctx, E("🎰 BAHİS", ("🎉 +" + str(miktar * 2)) if win else ("😔 -" + str(miktar)), C_ECO if win else C_ERROR))

@kategori("eco")
@bot.command(name="market", aliases=["shop"], help="Market")
async def market(ctx):
    em = E(None, None, C_ECO)
    em.set_author(name="🛒 KATRE MARKET", icon_url=bot.user.display_avatar.url)
    LINE(em, "💎 Pro (30 gün)", "`50.000` coin")
    LINE(em, "🎨 Rank rengi", "`5.000` coin (Pro)")
    LINE(em, "⭐ +10 Rep", "`2.500` coin")
    LINE(em, "🏷️ Tag", "`7.500` coin (Pro)")
    v = View(); v.add_item(Button(label="Satın Al", url=SUPPORT_URL, style=discord.ButtonStyle.link, emoji="🛒"))
    await safe_reply(ctx, em, v)

# ═══════════════════════════════════════════════════════════════════════════
# 🎮 EĞLENCE
# ═══════════════════════════════════════════════════════════════════════════
@kategori("fun")
@bot.command(name="8ball", help="<soru> — Sihirli top")
async def eightball(ctx, *, soru):
    cev = ["✅ Evet!", "🌟 Büyük ihtimal", "🤔 Belki", "❌ Hayır", "💀 Asla!", "🎯 Yüksek şans", "😴 Pas", "🔥 Evet evet!"]
    await safe_reply(ctx, E("🎱 " + soru[:100], "**" + random.choice(cev) + "**", C_FUN))

@kategori("fun")
@bot.command(name="yazıtura", aliases=["coin"], help="Yazı tura")
async def yazıtura(ctx):
    await safe_reply(ctx, E("🪙", "**" + random.choice(["📝 YAZI", "🪙 TURA"]) + "**", C_FUN))

@kategori("fun")
@bot.command(name="zar", aliases=["dice"], help="Zar (1-6)")
async def zar(ctx):
    r = random.randint(1, 6)
    await safe_reply(ctx, E("🎲", DICE[r-1] + " **" + str(r) + "**", C_FUN))

@kategori("fun")
@bot.command(name="aşk", aliases=["ask", "love"], help="<@üye> — Görsel aşk ölçer")
async def aşk(ctx, user: discord.Member):
    pct = random.randint(0, 100)
    msg = "💔 Yok bu iş..." if pct < 30 else ("💛 Fena değil!" if pct < 60 else ("💚 Güzel çift!" if pct < 85 else "❤️ RUH İKİZİ!"))
    if HAS_PIL:
        av1 = await fetch_avatar(ctx.author, 128); av2 = await fetch_avatar(user, 128)
        img = make_love_card(ctx.author.display_name, user.display_name, pct, av1, av2)
        buf = io.BytesIO(); img.save(buf, format="PNG"); buf.seek(0)
        em = E(None, None, 0xFF69B4); em.set_image(url="attachment://ask.png")
        em.description = msg
        await ctx.send(file=discord.File(buf, filename="ask.png"), embed=em)
    else:
        await safe_reply(ctx, E("💕 AŞK", ctx.author.mention + " 💘 " + user.mention + "\n" + progress_bar(pct) + "\n" + msg, C_FUN))

@kategori("fun")
@bot.command(name="slot", aliases=["slots"], help="Slot")
async def slot(ctx):
    r = [random.choice(SLOTS) for _ in range(3)]
    win = len(set(r)) == 1
    await safe_reply(ctx, E("🎰 SLOT", "┃ " + " ┃ ".join(r) + " ┃\n" + ("🎉 JACKPOT!" if win else "😔 Olmadı..."), C_PRO if win else C_FUN))

@kategori("fun")
@bot.command(name="seç", aliases=["sec"], help="<a> <b> ... — Seçim")
async def seç(ctx, *, seçenekler):
    opts = seçenekler.split()
    if len(opts) < 2: return await safe_reply(ctx, E("❌", "2+ seçenek!", C_ERROR))
    await safe_reply(ctx, E("🎯", "**" + random.choice(opts) + "**", C_FUN))

@kategori("fun")
@bot.command(name="oylama", aliases=["anket"], help="<soru> — Tepki oylaması")
async def oylama(ctx, *, soru):
    em = E(None, None, C_FUN)
    em.set_author(name="🗳️ OYLAMA — " + ctx.author.display_name, icon_url=ctx.author.display_avatar.url)
    em.description = "### " + soru[:200] + "\n" + SEP + "\n👍 Evet • 👎 Hayır • 🤷 Çekimser"
    msg = await ctx.send(embed=em)
    for r in ("👍", "👎", ""):
        await msg.add_reaction(r)

@kategori("fun")
@bot.command(name="quiz", aliases=["bilgi"], help="Bilgi yarışması (+75 coin)")
@commands.cooldown(1, 10, commands.BucketType.user)
async def quiz(ctx):
    q, opts, ans = random.choice(QUIZ)
    view = View(timeout=30)
    emojis = ["1️⃣", "2️⃣", "3️⃣", "4️⃣"]
    def make_cb(idx):
        async def _cb(it):
            if idx == ans:
                ensure_user(it.user.id, str(it.user))
                db.q("UPDATE users SET coins=coins+75, xp=xp+20 WHERE user_id=?", (it.user.id,))
                await it.response.send_message(embed=E("✅ DOĞRU!", it.user.mention + " **+75 coin, +20 XP**! 🎉", C_OK), ephemeral=True)
            else:
                await it.response.send_message(embed=E("❌ YANLIŞ", "Doğru: **" + opts[ans] + "**", C_ERROR), ephemeral=True)
            for b in view.children: b.disabled = True
            try: await it.message.edit(view=view)
            except Exception: pass
        return _cb
    for i, o in enumerate(opts):
        b = Button(label=o[:78], style=discord.ButtonStyle.primary, emoji=emojis[i])
        b.callback = make_cb(i)
        view.add_item(b)
    em = E(None, None, C_FUN)
    em.set_author(name="🧠 BİLGİ YARIŞMASI", icon_url=ctx.author.display_avatar.url)
    em.description = "### ❓ " + q + "\n" + SEP + "\n⏱️ 30 saniye • 🏆 +75 coin"
    await ctx.send(embed=em, view=view)

@kategori("fun")
@bot.command(name="tahmin", aliases=["sayı"], help="<1-10> — Tuttur +100 coin")
@commands.cooldown(1, 15, commands.BucketType.user)
async def tahmin(ctx, sayi: int):
    if not 1 <= sayi <= 10: return await safe_reply(ctx, E("❌", "1-10!", C_ERROR))
    t = random.randint(1, 10)
    if sayi == t:
        db.q("UPDATE users SET coins=coins+100 WHERE user_id=?", (ctx.author.id,))
        await safe_reply(ctx, E("🎯 BİLDİN!", "**+100 coin** 🤑", C_PRO))
    else:
        await safe_reply(ctx, E("😔", "Tutulan: **" + str(t) + "**", C_WARN))

@kategori("fun")
@bot.command(name="evlen", aliases=["marry"], help="<@üye> — Evlen")
async def evlen(ctx, user: discord.Member):
    if user.id == ctx.author.id or user.bot: return await safe_reply(ctx, E("❌", "Geçersiz!", C_ERROR))
    m = db.one("SELECT * FROM marriages WHERE user1=? OR user2=? OR user1=? OR user2=?",
               (ctx.author.id, ctx.author.id, user.id, user.id))
    if m: return await safe_reply(ctx, E("💔", "Biriniz zaten evli!", C_ERROR))
    db.q("INSERT INTO marriages(user1, user2, since) VALUES(?,?,?)",
         (ctx.author.id, user.id, datetime.datetime.now().isoformat()))
    await safe_reply(ctx, E("💍 EVLENDİNİZ!", ctx.author.mention + " ❤️ " + user.mention + "\n🎉 Mutluluklar!", C_FUN))

@kategori("fun")
@bot.command(name="boşan", aliases=["divorce"], help="Boşan")
async def boşan(ctx):
    db.q("DELETE FROM marriages WHERE user1=? OR user2=?", (ctx.author.id, ctx.author.id))
    await safe_reply(ctx, E("💔 BOŞANDIN", "Evlilik bitti.", C_WARN))

@kategori("fun")
@bot.command(name="eş", help="[<@üye>] — Eşini göster")
async def eş(ctx, user: discord.Member = None):
    user = user or ctx.author
    m = db.one("SELECT * FROM marriages WHERE user1=? OR user2=?", (user.id, user.id))
    if not m: return await safe_reply(ctx, E("💔", user.mention + " bekar.", C_WARN))
    other = m["user2"] if m["user1"] == user.id else m["user1"]
    await safe_reply(ctx, E("❤️ EŞ", user.mention + " 💍 <@" + str(other) + ">\n📅 <t:" +
                            str(int(datetime.datetime.fromisoformat(m["since"]).timestamp())) + ":D>", C_FUN))

# ═══════════════════════════════════════════════════════════════════════════
# 🎉 ÇEKİLİŞ
# ═══════════════════════════════════════════════════════════════════════════
@kategori("give")
@bot.command(name="çekiliş", aliases=["cekilis"], help="<süre> <kazanan> <ödül> — Çekiliş (Yönetici)")
@commands.has_permissions(administrator=True)
async def çekiliş(ctx, süre: str, kazanan: int, *, ödül):
    try: dk = parse_sure(süre)
    except Exception: return await safe_reply(ctx, E("❌", "Örnek: `k!çekiliş 60m 1 Nitro`", C_ERROR))
    if dk < 1 or kazanan < 1: return await safe_reply(ctx, E("❌", "Geçersiz!", C_ERROR))
    end = datetime.datetime.now() + datetime.timedelta(minutes=dk)
    em = gw_embed({"prize": ödül, "winners": kazanan, "end_time": end.timestamp(),
                   "host": ctx.author.id, "message_id": 0, "participants": "[]"}, bot)
    msg = await ctx.send(embed=em, view=bot.gw_view)
    db.q("INSERT INTO giveaways(message_id,guild_id,channel_id,prize,winners,end_time,host) VALUES(?,?,?,?,?,?,?)",
         (msg.id, ctx.guild.id, ctx.channel.id, ödül, kazanan, end.timestamp(), ctx.author.id))
    try:
        await msg.edit(embed=gw_embed({"prize": ödül, "winners": kazanan, "end_time": end.timestamp(),
                                       "host": ctx.author.id, "message_id": msg.id, "participants": "[]"}, bot), view=bot.gw_view)
    except Exception: pass

@kategori("give")
@bot.command(name="çekilişler", aliases=["cekilisler"], help="Aktif çekilişler")
async def çekilişler(ctx):
    rows = db.all("SELECT * FROM giveaways WHERE guild_id=? AND status='active'", (ctx.guild.id,))
    if not rows: return await safe_reply(ctx, E("🎉", "Aktif çekiliş yok.", C_WARN))
    em = E(None, None, C_GIVE)
    em.set_author(name="🎉 AKTİF (" + str(len(rows)) + ")")
    for g in rows:
        LINE(em, "🎁 " + g["prize"], "└ 👥 " + str(len(json.loads(g["participants"]))) + " • ⏰ <t:" + str(int(g["end_time"])) + ":R>")
    await safe_reply(ctx, em)

@kategori("give")
@bot.command(name="çekilişbitir", aliases=["cekilisbitir"], help="<id> — Bitir")
@commands.has_permissions(administrator=True)
async def çekilişbitir(ctx, mid: int):
    gw = db.one("SELECT * FROM giveaways WHERE message_id=? AND guild_id=?", (mid, ctx.guild.id))
    if not gw or gw["status"] != "active": return await safe_reply(ctx, E("❌", "Bulunamadı!", C_ERROR))
    await finalize_giveaway(bot, mid)
    await safe_reply(ctx, E("🏁", "Bitti!", C_OK))

# ═══════════════════════════════════════════════════════════════════════════
# 💎 PRO
# ═══════════════════════════════════════════════════════════════════════════
@kategori("pro")
@bot.command(name="pro", help="Pro durumu + ayrıcalıklar")
async def pro(ctx, user: discord.Member = None):
    user = user or ctx.author
    ensure_user(user.id, str(user))
    u = db.one("SELECT * FROM users WHERE user_id=?", (user.id,))
    logs = len(db.all("SELECT 1 FROM pro_logs WHERE user_id=?", (user.id,)))
    em = E(None, None, C_PRO, thumb=user.display_avatar.url)
    em.set_author(name="💎 KATRE PRO", icon_url=bot.user.display_avatar.url)
    if u["pro"]:
        exp = datetime.datetime.fromisoformat(u["pro_expiry"]).strftime("%d.%m.%Y") if u["pro_expiry"] else "∞"
        LINE(em, "✅ DURUM", "**PRO ÜYE** • Bitiş: `" + exp + "`")
    else:
        LINE(em, "❌ DURUM", "Pro değil. Owner: `k!prover`")
    LINE(em, "📜 Pro Log Kaydı", "`" + str(logs) + "` işlem (kalıcı)")
    LINE(em, "🌟 AYRICALIKLAR", "┃ 🎙️ `prooda` • 🎨 `prorenk` • 📊 `prostats`\n┃ ️ `proyazı` • 📣 `proembed` • 🏷️ `protag`\n┃ ⚡ `proxp` • 🎁 +250 günlük bonus")
    await safe_reply(ctx, em)

@kategori("pro")
@bot.command(name="prooda", help="Özel ses odası (PRO)")
@is_pro()
async def prooda(ctx):
    cat = discord.utils.get(ctx.guild.categories, name="💎 PRO ODALAR")
    if not cat:
        cat = await ctx.guild.create_category("💎 PRO ODALAR")
        await cat.set_permissions(ctx.guild.default_role, view_channel=False)
    ch = await ctx.guild.create_voice_channel("👑 " + ctx.author.display_name, category=cat)
    await ch.set_permissions(ctx.author, connect=True, manage_channels=True, move_members=True)
    await safe_reply(ctx, E("🎙️ PRO ODA", ch.mention + " hazır!", C_PRO))

@kategori("pro")
@bot.command(name="prorenk", help="<hex> — Rank rengi (PRO)")
@is_pro()
async def prorenk(ctx, hexcode: str):
    hexcode = hexcode.lstrip("#")
    if len(hexcode) != 6: return await safe_reply(ctx, E("❌", "`k!prorenk ff0000`", C_ERROR))
    try: int(hexcode, 16)
    except ValueError: return await safe_reply(ctx, E("❌", "Geçersiz hex!", C_ERROR))
    db.q("UPDATE users SET pro_color=? WHERE user_id=?", (hexcode, ctx.author.id))
    await safe_reply(ctx, E("🎨 RENK", "#" + hexcode.upper(), int(hexcode, 16)))

@kategori("pro")
@bot.command(name="prostats", help="Detaylı istatistik (PRO)")
@is_pro()
async def prostats(ctx):
    u = db.one("SELECT * FROM users WHERE user_id=?", (ctx.author.id,))
    em = E(None, None, C_PRO, thumb=ctx.author.display_avatar.url)
    em.set_author(name="📊 PRO İSTATİSTİK", icon_url=ctx.author.display_avatar.url)
    LINE(em, "💬 Mesaj", "`" + str(u["messages"]) + "`", True)
    LINE(em, "📈 Seviye", "`" + str(u["level"]) + "`", True)
    LINE(em, "🪙 Coin", "`" + str(u["coins"]) + "`", True)
    LINE(em, "⭐ Rep", "`" + str(u["rep"]) + "`", True)
    LINE(em, "⚡ 2x", "✅" if u["xp2"] else "❌", True)
    LINE(em, "🏷️ Tag", u["pro_tag"] or "—", True)
    await safe_reply(ctx, em)

@kategori("pro")
@bot.command(name="proyazı", help="<metin> — Havalı yazı (PRO)")
@is_pro()
async def proyazı(ctx, *, metin):
    await safe_reply(ctx, E("✒️ PRO YAZI", fancy(metin[:200]), C_PRO))

@kategori("pro")
@bot.command(name="proembed", help="<başlık> | <metin> | <hex> (PRO)")
@is_pro()
async def proembed(ctx, *, args):
    parts = [p.strip() for p in args.split("|")]
    if len(parts) < 2: return await safe_reply(ctx, E("❌", "Örnek: `k!proembed Duyuru | Merhaba | ff0000`", C_ERROR))
    color = C_PRO
    if len(parts) >= 3:
        try: color = int(parts[2].lstrip("#"), 16)
        except ValueError: pass
    em = E(parts[0][:256], parts[1][:4000], color)
    em.set_footer(text="💎 " + ctx.author.display_name + " • PRO")
    await safe_reply(ctx, em)

@kategori("pro")
@bot.command(name="protag", help="<metin> — Rozet tag (PRO)")
@is_pro()
async def protag(ctx, *, tag):
    db.q("UPDATE users SET pro_tag=? WHERE user_id=?", (tag[:12], ctx.author.id))
    await safe_reply(ctx, E("🏷️ TAG", "**" + tag[:12] + "**", C_PRO))

@kategori("pro")
@bot.command(name="proxp", help="2x XP aç/kapat (PRO)")
@is_pro()
async def proxp(ctx):
    u = db.one("SELECT xp2 FROM users WHERE user_id=?", (ctx.author.id,))
    new = 0 if u["xp2"] else 1
    db.q("UPDATE users SET xp2=? WHERE user_id=?", (new, ctx.author.id))
    await safe_reply(ctx, E("⚡ BOOST", "**2x AÇIK!**" if new else "**2x KAPALI.**", C_PRO))

# ═══════════════════════════════════════════════════════════════════════════
# 👑 OWNER
# ═══════════════════════════════════════════════════════════════════════════
@kategori("owner")
@bot.command(name="sahip", aliases=["owner", "panel"], help="Owner paneli")
@is_owner()
async def sahip(ctx):
    maint = db.one("SELECT maintenance FROM owner_settings WHERE id=1")["maintenance"]
    em = E(None, None, C_OWNER)
    em.set_author(name="👑 OWNER PANELİ", icon_url=bot.user.display_avatar.url)
    em.description = ("### Hoş geldin Owner! 👋\n" + SEP +
                      "\n🌐 " + str(len(bot.guilds)) + " sunucu • 👥 " + str(sum(g.member_count or 0 for g in bot.guilds)) + " kullanıcı" +
                      "\n🔧 Bakım: **" + ("🔴 AÇIK" if maint else "🟢 KAPALI") + "**" +
                      "\n📜 Pro log: `k!prologlar` (kalıcı)")
    await ctx.send(embed=em, view=OwnerPanelView(bot))

@kategori("owner")
@bot.command(name="prover", help="<@üye> [gün] — Pro ver (KALICI LOGLANIR)")
@is_owner()
async def prover(ctx, user: discord.Member, gun: int = 30):
    ensure_user(user.id, str(user))
    exp = (datetime.datetime.now() + datetime.timedelta(days=gun)).isoformat()
    db.q("UPDATE users SET pro=1, pro_expiry=? WHERE user_id=?", (exp, user.id))
    pro_log(user.id, "VERİLDİ", gun, ctx.author.id)   # ✅ kalıcı
    await safe_reply(ctx, E("💎 PRO VERİLDİ", user.mention + " • **" + str(gun) + " gün**\n📜 Loglandı (restart'ta silinmez)", C_PRO))
    try: await user.send(embed=E("🎉 PRO OLDUN!", str(gun) + " gün PRO! 💎", C_PRO))
    except Exception: pass

@kategori("owner")
@bot.command(name="proal", help="<@üye> — Pro al (KALICI LOGLANIR)")
@is_owner()
async def proal(ctx, user: discord.Member):
    db.q("UPDATE users SET pro=0, pro_expiry=NULL WHERE user_id=?", (user.id,))
    pro_log(user.id, "ALINDI", 0, ctx.author.id)      # ✅ kalıcı
    await safe_reply(ctx, E("💔 PRO ALINDI", user.mention + "\n📜 Loglandı", C_WARN))

@kategori("owner")
@bot.command(name="prologlar", aliases=["prolog"], help="Kalıcı pro işlem geçmişi")
@is_owner()
async def prologlar(ctx, user: discord.User = None):
    rows = db.all("SELECT * FROM pro_logs WHERE user_id=? ORDER BY id DESC LIMIT 15", (user.id,)) if user \
           else db.all("SELECT * FROM pro_logs ORDER BY id DESC LIMIT 15")
    em = E(None, None, C_PRO)
    em.set_author(name="📜 PRO LOGLARI (" + str(len(rows)) + ") — KALICI", icon_url=bot.user.display_avatar.url)
    if not rows: em.description = "Henüz kayıt yok."
    for r in rows:
        by = "<@" + str(r["by_id"]) + ">" if r["by_id"] else "🤖 Sistem"
        em.add_field(name="#" + str(r["id"]) + " • " + r["action"],
                     value="└ 👤 <@" + str(r["user_id"]) + "> • 📅 " + r["ts"][:16].replace("T", " ") +
                           (" • ⏳ " + str(r["days"]) + " gün" if r["days"] else "") + " • By: " + by, inline=False)
    await safe_reply(ctx, em)

@kategori("owner")
@bot.command(name="bakım", aliases=["bakim"], help="[aç/kapat] — Bakım modu")
@is_owner()
async def bakım(ctx, mod: str = None):
    cur = db.one("SELECT maintenance FROM owner_settings WHERE id=1")["maintenance"]
    new = (not cur) if mod is None else (mod.lower() in ("aç", "ac", "on", "1"))
    db.q("UPDATE owner_settings SET maintenance=? WHERE id=1", (int(new),))
    await safe_reply(ctx, E("🔧 BAKIM", "**🔴 AÇIK**" if new else "**🟢 KAPALI**", C_WARN))

@kategori("owner")
@bot.command(name="prefix", help="<prefix> — Sunucu prefixi")
@is_owner()
async def prefix(ctx, yeni: str):
    db.q("UPDATE servers SET prefix=? WHERE guild_id=?", (yeni, ctx.guild.id))
    await safe_reply(ctx, E("✅ PREFIX", "`" + yeni + "`", C_OK))

@kategori("owner")
@bot.command(name="blacklist", aliases=["bl"], help="<ekle/çıkar> <@üye>")
@is_owner()
async def blacklist(ctx, işlem: str, user: discord.User, *, sebep="—"):
    if işlem.lower() in ("ekle", "add"):
        db.q("INSERT OR REPLACE INTO blacklist(user_id,reason) VALUES(?,?)", (user.id, sebep))
        await safe_reply(ctx, E("🚫", user.mention + " eklendi.", C_ERROR))
    elif işlem.lower() in ("çıkar", "cikar", "remove"):
        db.q("DELETE FROM blacklist WHERE user_id=?", (user.id,))
        await safe_reply(ctx, E("✅", user.mention + " çıkarıldı.", C_OK))
    else:
        await safe_reply(ctx, E("❌", "`ekle/çıkar`", C_ERROR))

@kategori("owner")
@bot.command(name="durum", aliases=["status"], help="<metin> — Durum")
@is_owner()
async def durum(ctx, *, metin):
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name=metin))
    await safe_reply(ctx, E("✅ DURUM", metin[:100], C_OK))

@kategori("owner")
@bot.command(name="sunucular", aliases=["guilds"], help="Sunucu listesi")
@is_owner()
async def sunucular(ctx):
    rows = sorted(bot.guilds, key=lambda g: -(g.member_count or 0))
    em = E(None, None, C_OWNER)
    em.set_author(name="🖥️ SUNUCULAR (" + str(len(rows)) + ")")
    for i, g in enumerate(rows[:15], 1):
        LINE(em, "`" + str(i) + ".` " + g.name, "└ 👥 " + str(g.member_count))
    await safe_reply(ctx, em)

@kategori("owner")
@bot.command(name="eval", aliases=["py"], help="<kod> — Python (Owner)")
@is_owner()
async def eval_cmd(ctx, *, code):
    env = {"bot": bot, "ctx": ctx, "db": db, "discord": discord, "guild": ctx.guild, "author": ctx.author}
    buf = io.StringIO()
    func = "async def __f():\n" + textwrap.indent(code, "    ")
    try:
        exec(compile(func, "<eval>", "exec"), env)
        with redirect_stdout(buf):
            await env["__f"]()
        await ctx.send(content="```py\n" + (buf.getvalue()[:1900] or "✅ OK") + "\n```")
    except Exception as e:
        await ctx.send(content="```py\nHATA: " + str(e)[:1900] + "\n```")

# ═══════════════════════════════════════════════════════════════════════════
# 🚀 BAŞLAT
# ═══════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    bot.run(BOT_TOKEN)
