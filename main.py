# ═══════════════════════════════════════════════════════════════════════════
#  💧 KATRE BOT v2.7 — MESAJ STİLİ YARDIM + FULL NİTRO EMOJİ SİSTEMİ
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
C_ECO   = 0x2ECC71; C_OWNER = 0xFF0000; C_SYS = 0x3498DB
SEP     = "┈┈┈┈┈┈┈┈┈┈┈"
FOOTER  = "Katre Bot • k!yardım"

# ═══════════════════════════════════════════════════════════════════════════
# 💎 NİTRO EMOJİ SLOTLARI (owner k!emoji ile hepsini değiştirir)
# ═══════════════════════════════════════════════════════════════════════════
SLOTS = {
    "logo": "💧", "check": "✅", "cross": "❌", "warn": "⚠️", "info": "ℹ️",
    "star": "🌟", "spark": "✨", "crown": "👑", "owner": "👑", "diamond": "💎", "pro": "💎",
    "coin": "🪙", "money": "💰", "gift": "🎁", "party": "🎉", "give": "🎉",
    "shield": "🛡️", "mod": "🛡️", "hammer": "🔨", "kick": "👢", "lock": "🔒", "unlock": "🔓",
    "gear": "⚙️", "chart": "📊", "chartup": "📈", "fire": "🔥", "bolt": "⚡",
    "heart": "❤️", "broken": "💔", "ring": "💍", "game": "🎮", "fun": "🎮",
    "dice": "🎲", "slot": "🎰", "fish": "🎣", "pick": "⛏️", "target": "🎯",
    "ticket": "🎫", "clip": "📋", "sys": "📋", "pen": "📝", "cam": "📸", "log": "📜",
    "sleep": "😴", "wave": "👋", "cake": "🎂", "alarm": "⏰", "time": "⏳",
    "genel": "🌐", "eco": "💰", "mic": "🎙️", "palette": "🎨", "tag": "🏷️",
    "robot": "🤖", "search": "🔍", "arrow": "»", "dot": "•",
    "home": "🏠", "trash": "🗑️", "link": "🔗", "mail": "📢", "tool": "🔧",
}
EMO_CACHE = {}
def refresh_emojis():
    global EMO_CACHE
    EMO_CACHE = {r["slot"]: r["emoji"] for r in db.all("SELECT * FROM emojis")}
def e(slot):
    return EMO_CACHE.get(slot, SLOTS.get(slot, "•"))

# ═══════════════════════════════════════════════════════════════════════════
# 🗄️ VERİTABANI
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
            status_text TEXT DEFAULT 'k!yardım | Katre Bot');
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
        CREATE TABLE IF NOT EXISTS applications(
            id INTEGER PRIMARY KEY AUTOINCREMENT, guild_id INTEGER, user_id INTEGER,
            message_id INTEGER, status TEXT DEFAULT 'pending', answers TEXT, ts TEXT);
        CREATE TABLE IF NOT EXISTS app_settings(
            guild_id INTEGER PRIMARY KEY, log_ch INTEGER, staff_role INTEGER);
        CREATE TABLE IF NOT EXISTS auto_replies(
            guild_id INTEGER, trigger TEXT, response TEXT, PRIMARY KEY(guild_id, trigger));
        CREATE TABLE IF NOT EXISTS counters(
            guild_id INTEGER PRIMARY KEY, target INTEGER, channel_id INTEGER, reached INTEGER DEFAULT 0);
        CREATE TABLE IF NOT EXISTS level_roles(
            id INTEGER PRIMARY KEY AUTOINCREMENT, guild_id INTEGER, level INTEGER, role_id INTEGER);
        CREATE TABLE IF NOT EXISTS guild_logs(guild_id INTEGER PRIMARY KEY, channel_id INTEGER);
        CREATE TABLE IF NOT EXISTS emojis(slot TEXT PRIMARY KEY, emoji TEXT);
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
refresh_emojis()

def ensure_user(uid, name):
    db.q("INSERT OR IGNORE INTO users(user_id,name) VALUES(?,?)", (uid, name))

def pro_log(user_id, action, days=0, by_id=0):
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
# 🎨 YARDIMCILAR
# ═══════════════════════════════════════════════════════════════════════════
def E(title=None, desc=None, color=C_MAIN, thumb=None, img=None, footer=FOOTER):
    em = discord.Embed(title=title, description=desc, color=color, timestamp=datetime.datetime.now())
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
        if text.endswith(suf): return int(float(text[:-len(suf)]) * m)
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

# ─────────────── 🖼️ PIL ───────────────
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
        h = h.lstrip("#"); return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))
    except Exception: return default

def base_card(W, H, accent):
    img = Image.new("RGB", (W, H), (23, 24, 28))
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, W, 8], fill=accent); d.rectangle([0, H - 8, W, H], fill=accent)
    d.rounded_rectangle([18, 26, W - 18, H - 26], radius=24, fill=(32, 33, 40))
    return img, d

def paste_circle(img, raw, x, y, size):
    try:
        ava = Image.open(io.BytesIO(raw)).convert("RGBA").resize((size, size))
        mask = Image.new("L", (size, size), 0)
        ImageDraw.Draw(mask).ellipse((0, 0, size, size), fill=255)
        img.paste(ava, (x, y), mask); return True
    except Exception: return False

def make_help_banner(avatar_bytes, name, cmds, guilds):
    W, H = 1000, 320
    img, d = base_card(W, H, (0, 168, 255))
    if avatar_bytes: paste_circle(img, avatar_bytes, W - 230, 60, 170)
    d = ImageDraw.Draw(img)
    d.ellipse((W - 230, 60, W - 60, 230), outline=(0, 168, 255), width=4)
    d.text((60, 55), name.upper(), font=get_font(46), fill=(255, 255, 255))
    d.text((60, 125), "YARDIM MENUSU", font=get_font(28), fill=(150, 200, 255))
    d.text((60, 185), str(cmds) + " komut   •   " + str(guilds) + " sunucu", font=get_font(26), fill=(190, 195, 205))
    d.text((60, 240), "k!yardim  •  k!pro  •  k!cekilis", font=get_font(22), fill=(120, 125, 135))
    return img

def make_rank_card(name, level, xp, need, coins, rep, pro, tag, accent, avatar_bytes):
    W, H = 900, 340
    img, d = base_card(W, H, accent)
    if avatar_bytes: paste_circle(img, avatar_bytes, 50, 62, 150)
    d = ImageDraw.Draw(img)
    d.ellipse((50, 62, 200, 212), outline=accent, width=4)
    d.text((230, 55), name[:22], font=get_font(40), fill=(255, 255, 255))
    d.text((230, 112), "Seviye " + str(level) + "  •  " + str(xp) + "/" + str(need) + " XP  •  " +
           str(coins) + " coin  •  " + str(rep) + " rep", font=get_font(24), fill=(160, 165, 175))
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
        d.text((x + 16, y + 9), tag[:12], font=get_font(24), fill=(255, 255, 255))
    return img

def make_leaderboard(entries):
    W, row_h = 820, 62
    H = 150 + row_h * max(1, len(entries)) + 20
    img = Image.new("RGB", (W, H), (23, 24, 28)); d = ImageDraw.Draw(img)
    d.rectangle([0, 0, W, 90], fill=(0, 168, 255))
    d.text((30, 24), "SUNUCU SIRALAMASI", font=get_font(38), fill=(255, 255, 255))
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
    d.text((230, 145), "Hesap: " + created + "  •  Katılım: " + joined, font=get_font(22), fill=(160, 165, 175))
    x, y = 230, 195
    if pro:
        d.rounded_rectangle([x, y, x + 90, y + 40], radius=20, fill=(255, 215, 0))
        d.text((x + 24, y + 8), "PRO", font=get_font(24), fill=(20, 20, 20)); x += 105
    if tag:
        tw = 60 + 13 * len(tag[:12])
        d.rounded_rectangle([x, y, x + tw, y + 40], radius=20, fill=(70, 72, 82))
        d.text((x + 16, y + 8), tag[:12], font=get_font(24), fill=(255, 255, 255))
    d.text((50, 260), "Seviye: " + str(level) + "   Coin: " + str(coins) + "   İtibar: " + str(rep),
           font=get_font(28), fill=(220, 225, 235))
    return img

def make_wallet_card(name, coins, rep, pro, avatar_bytes, accent):
    W, H = 800, 300
    img, d = base_card(W, H, accent)
    if avatar_bytes: paste_circle(img, avatar_bytes, 50, 70, 120)
    d = ImageDraw.Draw(img)
    d.ellipse((50, 70, 170, 190), outline=accent, width=4)
    d.text((210, 65), name[:22], font=get_font(36), fill=(255, 255, 255))
    d.text((210, 115), ("PRO UYE  •  " if pro else "") + str(rep) + " itibar", font=get_font(22), fill=(160, 165, 175))
    d.text((210, 155), format(coins, ",").replace(",", ".") + " coin", font=get_font(44), fill=(255, 215, 0))
    return img

def make_stats_card(servers, users, cmds, uptime, ping, total):
    W, H = 860, 400
    img, d = base_card(W, H, (0, 168, 255))
    d.text((50, 50), "KATRE BOT ISTATISTIK", font=get_font(40), fill=(255, 255, 255))
    items = [("Sunucu", str(servers)), ("Kullanici", str(users)), ("Komut", str(cmds)),
             ("Uptime", uptime), ("Ping", ping + "ms"), ("Kullanim", str(total))]
    for i, (k, v) in enumerate(items):
        cx = 60 + (i % 3) * 260; cy = 150 + (i // 3) * 100
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
    d.text((220, 105), "Kurucu: " + owner[:20] + "  •  Kurulus: " + created, font=get_font(22), fill=(160, 165, 175))
    for i, (k, v) in enumerate([("Uye", str(members)), ("Kanal", str(channels)), ("Rol", str(roles)), ("Boost", str(boost))]):
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
# 📖 MESAJ STİLİ YARDIM SİSTEMİ (embed YOK)
# ═══════════════════════════════════════════════════════════════════════════
CATS = {
    "genel": ("🌐", "Genel & Sunucu", C_MAIN),
    "mod":   ("🛡️", "Moderasyon",     C_MOD),
    "sys":   ("📋", "Sistemler",      C_SYS),
    "eco":   ("💰", "Ekonomi",        C_ECO),
    "fun":   ("🎮", "Eğlence",        C_FUN),
    "give":  ("🎉", "Çekiliş",        C_GIVE),
    "pro":   ("💎", "Pro",            C_PRO),
    "owner": ("👑", "Owner",          C_OWNER),
}
CAT_DESC = {
    "genel": "Rank, profil, avatar, snipe, AFK, hatırlatıcı ve genel araçlar",
    "mod":   "Ban, kick, uyarı, temizle ve anti-spam/raid/flood korumaları",
    "sys":   "Yetkili başvuru, oto-cevap, sayaç, seviye rol ve log sistemleri",
    "eco":   "Coin, günlük, çalışma, balık, maden, bahis ve market",
    "fun":   "Quiz, slot, aşk ölçer, oylama, evlilik ve eğlence oyunları",
    "give":  "Butonlu çekiliş başlatma, bitirme, reroll ve süre uzatma",
    "pro":   "Pro üyelere özel oda, renk, tag, boost ve embed komutları",
    "owner": "Yalnızca bot sahibine özel yönetim ve emoji paneli",
}

def help_content(bot):
    L = [e("logo") + " **KATRE BOT YARDIM MENÜSÜ**", ""]
    L.append("Selam, ben **" + bot.user.name + "!** " + e("spark"))
    L.append("Toplam **" + str(len(bot.commands)) + "** komutum var; hepsi `k!komut` şeklinde çalışır.")
    L.append("Büyük/küçük prefix fark etmez: `K!` da geçerlidir.")
    L.append("")
    L.append("Aşağıdaki menüden bir kategori seç.")
    L.append("")
    L.append(e("star") + " **Kategoriler**")
    L.append("")
    for k, (i, n, _) in CATS.items():
        L.append(e("arrow") + " " + e(k) + " **" + n + "**")
        L.append(CAT_DESC[k])
        L.append("")
    L.append(e("dot") + " Owner: <@" + str(OWNER_ID) + ">  " + e("dot") + " Sunucu: **" + str(len(bot.guilds)) + "**")
    return "\n".join(L)

def cat_content(bot, key):
    icon, name, color = CATS[key]
    L = [e(key) + " **" + name.upper() + " KOMUTLARI**", ""]
    cmds = [c for c in bot.commands if getattr(c, "kategori", None) == key]
    if key == "owner":
        L.append(e("lock") + " _Bu komutlar yalnızca bot sahibine özeldir; diğerleri yanıt alamaz._")
        L.append("")
    for c in sorted(cmds, key=lambda x: x.name):
        L.append(e("arrow") + " `k!" + c.name + "` ─ " + (c.help or "—"))
    L.append("")
    L.append(e("info") + " Ana menüye dönmek için **Ana Menü** butonunu kullan.")
    return "\n".join(L)

class HelpSelect(Select):
    def __init__(self, bot):
        super().__init__(placeholder="📂 Bir kategori seçin...", min_values=1, max_values=1,
                         options=[discord.SelectOption(label=n, value=k, emoji=i, description=CAT_DESC[k][:90])
                                  for k, (i, n, _) in CATS.items()])
        self.bot = bot
    async def callback(self, it):
        key = self.values[0]
        if key == "owner" and it.user.id != OWNER_ID:
            return await it.response.send_message(content=e("lock") + " Owner paneli yalnızca bot sahibine açıktır!", ephemeral=True)
        await it.response.edit_message(content=cat_content(self.bot, key), view=self.view)

class HelpView(View):
    def __init__(self, bot):
        super().__init__(timeout=600); self.bot = bot
        self.add_item(HelpSelect(bot))
    @discord.ui.button(label="Ana Menü", style=discord.ButtonStyle.primary, emoji="🏠")
    async def home(self, it, btn):
        await it.response.edit_message(content=help_content(self.bot), view=self)
    @discord.ui.button(label="İstatistik", style=discord.ButtonStyle.secondary, emoji="📊")
    async def stats(self, it, btn):
        up = str(datetime.datetime.now() - self.bot.start_time).split(".")[0]
        txt = (e("chart") + " **KATRE İSTATİSTİK**\n" + SEP +
               "\n" + e("dot") + " Sunucu: **" + str(len(self.bot.guilds)) + "**" +
               "\n" + e("dot") + " Kullanıcı: **" + str(sum(g.member_count or 0 for g in self.bot.guilds)) + "**" +
               "\n" + e("dot") + " Komut: **" + str(len(self.bot.commands)) + "**" +
               "\n" + e("dot") + " Uptime: **" + up + "**" +
               "\n" + e("dot") + " Ping: **" + str(round(self.bot.latency * 1000)) + "ms**")
        await it.response.send_message(content=txt, ephemeral=True)
    @discord.ui.button(label="Kapat", style=discord.ButtonStyle.danger, emoji="🗑️")
    async def close(self, it, btn):
        await it.message.delete()
    def link_buttons(self):
        self.add_item(Button(label="Destek Sunucusu", url=SUPPORT_URL, style=discord.ButtonStyle.link, emoji="🔗"))
        return self

# ═══════════════════════════════════════════════════════════════════════════
# 🔘 DİĞER VIEW'LAR
# ═══════════════════════════════════════════════════════════════════════════
class BroadcastModal(Modal, title="📢 Genel Duyuru"):
    txt = TextInput(label="Duyuru metni", style=discord.TextStyle.paragraph)
    async def on_submit(self, it):
        ok = 0
        for g in it.client.guilds:
            ch = g.system_channel or next((c for c in g.text_channels if c.permissions_for(g.me).send_messages), None)
            if ch:
                try: await ch.send(embed=E(e("mail") + " OWNER DUYURUSU", self.txt.value, C_OWNER)); ok += 1
                except Exception: pass
        await it.response.send_message(content=e("check") + " " + str(ok) + "/" + str(len(it.client.guilds)) + " sunucuya iletildi.", ephemeral=True)

class OwnerPanelView(View):
    def __init__(self, bot):
        super().__init__(timeout=600); self.bot = bot
    async def guard(self, it):
        if it.user.id != OWNER_ID:
            await it.response.send_message(content=e("lock") + " Yalnızca owner!", ephemeral=True); return False
        return True
    @discord.ui.button(label="Bakım", style=discord.ButtonStyle.secondary, emoji="🔧")
    async def bakim(self, it, btn):
        if not await self.guard(it): return
        cur = db.one("SELECT maintenance FROM owner_settings WHERE id=1")["maintenance"]
        db.q("UPDATE owner_settings SET maintenance=? WHERE id=1", (0 if cur else 1,))
        await it.response.send_message(content=e("tool") + " Bakım: **" + ("🔴 AÇIK" if not cur else "🟢 KAPALI") + "**", ephemeral=True)
    @discord.ui.button(label="İstatistik", style=discord.ButtonStyle.success, emoji="📊")
    async def stats(self, it, btn):
        if not await self.guard(it): return
        total = db.one("SELECT SUM(uses) u FROM cmd_stats")["u"] or 0
        txt = (e("chart") + " **OWNER İSTATİSTİK**\n" + SEP +
               "\n" + e("dot") + " Sunucu: **" + str(len(self.bot.guilds)) + "**" +
               "\n" + e("dot") + " Komut kullanımı: **" + str(total) + "**" +
               "\n" + e("dot") + " Pro log: **" + str(len(db.all("SELECT 1 FROM pro_logs"))) + "**" +
               "\n" + e("dot") + " Bekleyen başvuru: **" + str(len(db.all("SELECT 1 FROM applications WHERE status='pending'"))) + "**")
        await it.response.send_message(content=txt, ephemeral=True)
    @discord.ui.button(label="Sunucular", style=discord.ButtonStyle.primary, emoji="🖥️")
    async def guilds(self, it, btn):
        if not await self.guard(it): return
        rows = sorted(self.bot.guilds, key=lambda x: -(x.member_count or 0))[:10]
        txt = e("gear") + " **SUNUCULAR (" + str(len(self.bot.guilds)) + ")**\n" + "\n".join(
            e("arrow") + " **" + g.name + "** ─ " + str(g.member_count) + " üye" for g in rows)
        await it.response.send_message(content=txt, ephemeral=True)
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
    em.set_author(name=e("give") + " ÇEKİLİŞ BAŞLADI!", icon_url=bot.user.display_avatar.url)
    em.description = "### 🎁 Ödül: **" + gw["prize"] + "**\n" + e("arrow") + " **KATIL** butonuna bas!\n" + SEP
    LINE(em, e("star") + " Kazanan", "`" + str(gw["winners"]) + "`", True)
    LINE(em, e("dot") + " Katılımcı", "`" + str(len(parts)) + "`", True)
    LINE(em, e("time") + " Bitiş", "<t:" + str(int(gw["end_time"])) + ":R>", True)
    LINE(em, e("owner") + " Başlatan", "<@" + str(gw["host"]) + ">", True)
    return em

class GiveawayView(View):
    def __init__(self, bot):
        super().__init__(timeout=None); self.bot = bot
    @discord.ui.button(label="Katıl", style=discord.ButtonStyle.success, emoji="🎉", custom_id="katre_gw_join", row=0)
    async def join(self, it, btn):
        gw = db.one("SELECT * FROM giveaways WHERE message_id=?", (it.message.id,))
        if not gw or gw["status"] != "active":
            return await it.response.send_message(content=e("cross") + " Aktif değil!", ephemeral=True)
        parts = json.loads(gw["participants"])
        if str(it.user.id) in parts:
            return await it.response.send_message(content=e("info") + " Zaten katıldın!", ephemeral=True)
        parts.append(str(it.user.id))
        db.q("UPDATE giveaways SET participants=? WHERE message_id=?", (json.dumps(parts), it.message.id))
        try: await it.message.edit(embed=gw_embed(dict(gw, participants=json.dumps(parts)), self.bot), view=self)
        except Exception: pass
        await it.response.send_message(content=e("check") + " Katıldın! Bol şans!", ephemeral=True)
    @discord.ui.button(label="Ayrıl", style=discord.ButtonStyle.secondary, emoji="🚪", custom_id="katre_gw_leave", row=0)
    async def leave(self, it, btn):
        gw = db.one("SELECT * FROM giveaways WHERE message_id=?", (it.message.id,))
        if not gw or gw["status"] != "active":
            return await it.response.send_message(content=e("cross") + " Aktif değil!", ephemeral=True)
        parts = json.loads(gw["participants"])
        if str(it.user.id) not in parts:
            return await it.response.send_message(content=e("info") + " Katılmamışsın.", ephemeral=True)
        parts.remove(str(it.user.id))
        db.q("UPDATE giveaways SET participants=? WHERE message_id=?", (json.dumps(parts), it.message.id))
        try: await it.message.edit(embed=gw_embed(dict(gw, participants=json.dumps(parts)), self.bot), view=self)
        except Exception: pass
        await it.response.send_message(content=e("check") + " Ayrıldın.", ephemeral=True)
    @discord.ui.button(label="Bitir", style=discord.ButtonStyle.primary, emoji="🏁", custom_id="katre_gw_end", row=1)
    async def end(self, it, btn):
        if not it.user.guild_permissions.administrator:
            return await it.response.send_message(content=e("lock"), ephemeral=True)
        await finalize_giveaway(self.bot, it.message.id)
        await it.response.send_message(content=e("check") + " Bitirildi.", ephemeral=True)
    @discord.ui.button(label="Yeniden Çek", style=discord.ButtonStyle.secondary, emoji="🎲", custom_id="katre_gw_reroll", row=1)
    async def reroll(self, it, btn):
        if not it.user.guild_permissions.administrator:
            return await it.response.send_message(content=e("lock"), ephemeral=True)
        gw = db.one("SELECT * FROM giveaways WHERE message_id=?", (it.message.id,))
        if not gw: return
        parts = json.loads(gw["participants"])
        if not parts: return await it.response.send_message(content=e("cross") + " Katılımcı yok!", ephemeral=True)
        w = self.bot.get_user(int(random.choice(parts)))
        await it.channel.send(embed=E(e("dice") + " REROLL", "🏆 " + (w.mention if w else "?"), C_PRO))
        await it.response.defer()
    @discord.ui.button(label="+1 Saat", style=discord.ButtonStyle.success, emoji="⏳", custom_id="katre_gw_extend", row=1)
    async def extend(self, it, btn):
        if not it.user.guild_permissions.administrator:
            return await it.response.send_message(content=e("lock"), ephemeral=True)
        gw = db.one("SELECT * FROM giveaways WHERE message_id=?", (it.message.id,))
        if not gw or gw["status"] != "active":
            return await it.response.send_message(content=e("cross"), ephemeral=True)
        new = gw["end_time"] + 3600
        db.q("UPDATE giveaways SET end_time=? WHERE message_id=?", (new, it.message.id))
        try: await it.message.edit(embed=gw_embed(dict(gw, end_time=new), self.bot), view=self)
        except Exception: pass
        await it.response.send_message(content=e("time") + " Uzatıldı: <t:" + str(int(new)) + ":R>", ephemeral=True)
    @discord.ui.button(label="İptal", style=discord.ButtonStyle.danger, emoji="🛑", custom_id="katre_gw_cancel", row=1)
    async def cancel(self, it, btn):
        if not it.user.guild_permissions.administrator:
            return await it.response.send_message(content=e("lock"), ephemeral=True)
        gw = db.one("SELECT * FROM giveaways WHERE message_id=?", (it.message.id,))
        if not gw: return
        db.q("UPDATE giveaways SET status='cancelled' WHERE message_id=?", (it.message.id,))
        try: await it.message.edit(embed=E(e("cross") + " İPTAL", gw["prize"], C_ERROR), view=None)
        except Exception: pass
        await it.response.send_message(content=e("cross") + " İptal edildi.", ephemeral=True)

class RoleButton(Button):
    def __init__(self, role_id, label, custom_id, row):
        super().__init__(label=label[:78], style=discord.ButtonStyle.secondary, emoji="🎭", custom_id=custom_id, row=row)
        self.role_id = role_id
    async def callback(self, it):
        role = it.guild.get_role(self.role_id)
        if not role: return await it.response.send_message(content=e("cross"), ephemeral=True)
        if role in it.user.roles:
            await it.user.remove_roles(role, reason="Rol menüsü"); msg = e("cross") + " **" + role.name + "** alındı."
        else:
            await it.user.add_roles(role, reason="Rol menüsü"); msg = e("check") + " **" + role.name + "** verildi!"
        await it.response.send_message(content=msg, ephemeral=True)

class RoleMenuView(View):
    def __init__(self, menu_id, roles):
        super().__init__(timeout=None)
        for i, (rid, name) in enumerate(roles):
            self.add_item(RoleButton(rid, name, "katre_role_" + menu_id + "_" + str(rid), i // 5))

class TicketModal(Modal, title="Destek Talebi"):
    konu = TextInput(label="Konu", max_length=100)
    aciklama = TextInput(label="Açıklama", style=discord.TextStyle.paragraph)
    async def on_submit(self, it):
        ex = db.one("SELECT * FROM tickets WHERE user_id=? AND status='open'", (it.user.id,))
        if ex: return await it.response.send_message(content=e("cross") + " Açık talebin var!", ephemeral=True)
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
        em.set_author(name=e("ticket") + " DESTEK TALEBİ")
        em.description = "**Konu:** " + self.konu.value + "\n**Açıklama:** " + self.aciklama.value[:900] + "\n" + SEP + "\n👤 " + it.user.mention
        await ch.send(embed=em, view=TicketCloseView())
        await it.response.send_message(content=e("check") + " Talebin: " + ch.mention, ephemeral=True)

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
        if not t: return await it.response.send_message(content=e("cross"), ephemeral=True)
        if not (it.user.guild_permissions.administrator or it.user.id == t["user_id"]):
            return await it.response.send_message(content=e("lock"), ephemeral=True)
        db.q("UPDATE tickets SET status='closed' WHERE channel_id=?", (it.channel.id,))
        await it.response.send_message(content=e("lock") + " 10 sn içinde silinecek...")
        await asyncio.sleep(10)
        try: await it.channel.delete()
        except Exception: pass

class ConfirmView(View):
    def __init__(self, timeout=30):
        super().__init__(timeout=timeout); self.value = None
    @discord.ui.button(label="Onayla", style=discord.ButtonStyle.danger, emoji="✅")
    async def yes(self, it, btn):
        self.value = True; self.stop()
        await it.response.edit_message(content=e("time") + " Uygulanıyor...", view=None)
    @discord.ui.button(label="Vazgeç", style=discord.ButtonStyle.secondary, emoji="❌")
    async def no(self, it, btn):
        self.value = False; self.stop()
        await it.response.edit_message(content=e("cross") + " İptal.", view=None)

class SetupConfirmView(View):
    def __init__(self, timeout=60):
        super().__init__(timeout=timeout); self.value = None
    @discord.ui.button(label="Kurulumu Başlat", style=discord.ButtonStyle.success, emoji="🏗️")
    async def yes(self, it, btn):
        self.value = True; self.stop()
        await it.response.edit_message(content=e("time") + " Kuruluyor... (≈10 sn)", view=None)
    @discord.ui.button(label="Vazgeç", style=discord.ButtonStyle.secondary, emoji="❌")
    async def no(self, it, btn):
        self.value = False; self.stop()
        await it.response.edit_message(content=e("cross") + " İptal.", view=None)

class AppOpenView(View):
    def __init__(self): super().__init__(timeout=None)
    @discord.ui.button(label="Yetkili Başvurusu Yap", style=discord.ButtonStyle.primary, emoji="📋", custom_id="katre_app_open")
    async def apply(self, it, btn):
        await it.response.send_modal(AppModal())

class AppModal(Modal, title="Yetkili Başvurusu"):
    yas = TextInput(label="Yaş", max_length=2)
    deneyim = TextInput(label="Discord / bot deneyimin", style=discord.TextStyle.paragraph, max_length=500)
    neden = TextInput(label="Neden yetkili olmak istiyorsun?", style=discord.TextStyle.paragraph, max_length=500)
    aktif = TextInput(label="Günlük aktif saatlerin", max_length=100)
    async def on_submit(self, it):
        g = it.guild
        st = db.one("SELECT * FROM app_settings WHERE guild_id=?", (g.id,))
        if not st or not st["log_ch"]:
            return await it.response.send_message(content=e("cross") + " Sistem kurulu değil. (`k!başvuru-ayarla`)", ephemeral=True)
        if db.one("SELECT 1 FROM applications WHERE guild_id=? AND user_id=? AND status='pending'", (g.id, it.user.id)):
            return await it.response.send_message(content=e("time") + " Zaten bekleyen başvurun var!", ephemeral=True)
        answers = json.dumps({"Yaş": self.yas.value, "Deneyim": self.deneyim.value,
                              "Neden": self.neden.value, "Aktif": self.aktif.value})
        cur = db.q("INSERT INTO applications(guild_id, user_id, answers, ts) VALUES(?,?,?,?)",
                   (g.id, it.user.id, answers, datetime.datetime.now().isoformat()))
        app_id = cur.lastrowid
        em = E(None, None, C_SYS, thumb=it.user.display_avatar.url)
        em.set_author(name=e("clip") + " YENİ BAŞVURU #" + str(app_id) + " — " + it.user.display_name)
        em.description = ("👤 " + it.user.mention + "\n" + SEP +
                          "\n" + e("dot") + " Yaş: **" + self.yas.value + "**" +
                          "\n" + e("dot") + " Deneyim: " + self.deneyim.value[:400] +
                          "\n" + e("dot") + " Neden: " + self.neden.value[:400] +
                          "\n" + e("dot") + " Aktif: " + self.aktif.value[:80])
        ch = g.get_channel(st["log_ch"])
        if ch:
            msg = await ch.send(embed=em, view=AppReviewView(app_id))
            db.q("UPDATE applications SET message_id=? WHERE id=?", (msg.id, app_id))
        await it.response.send_message(content=e("check") + " Başvurun alındı! (#" + str(app_id) + ") Takip: `k!başvurum`", ephemeral=True)

class AppReviewView(View):
    def __init__(self, app_id):
        super().__init__(timeout=None)
        self.app_id = app_id
        b1 = Button(label="Kabul Et", style=discord.ButtonStyle.success, emoji="✅", custom_id="katre_app_acc_" + str(app_id))
        b1.callback = self.accept
        b2 = Button(label="Reddet", style=discord.ButtonStyle.danger, emoji="❌", custom_id="katre_app_rej_" + str(app_id))
        b2.callback = self.reject
        self.add_item(b1); self.add_item(b2)
    async def _yetki(self, it):
        ok = it.user.guild_permissions.administrator
        st = db.one("SELECT * FROM app_settings WHERE guild_id=?", (it.guild.id,))
        if st and st["staff_role"]:
            r = it.guild.get_role(st["staff_role"])
            if r and r in it.user.roles: ok = True
        if not ok:
            await it.response.send_message(content=e("lock"), ephemeral=True); return False
        return True
    async def accept(self, it):
        if not await self._yetki(it): return
        app = db.one("SELECT * FROM applications WHERE id=?", (self.app_id,))
        if not app or app["status"] != "pending":
            return await it.response.send_message(content=e("cross") + " Zaten işlenmiş.", ephemeral=True)
        db.q("UPDATE applications SET status='accepted' WHERE id=?", (self.app_id,))
        st = db.one("SELECT * FROM app_settings WHERE guild_id=?", (it.guild.id,))
        role = it.guild.get_role(st["staff_role"]) if st and st["staff_role"] else None
        member = it.guild.get_member(app["user_id"])
        if role and member:
            try: await member.add_roles(role, reason="Başvuru kabul")
            except Exception: pass
        try: await it.message.edit(view=None)
        except Exception: pass
        await it.response.send_message(content=e("check") + " Kabul edildi: <@" + str(app["user_id"]) + ">")
        u = it.client.get_user(app["user_id"])
        if u:
            try: await u.send(content=e("party") + " **Başvurun kabul edildi!** " + it.guild.name)
            except Exception: pass
    async def reject(self, it):
        if not await self._yetki(it): return
        app = db.one("SELECT * FROM applications WHERE id=?", (self.app_id,))
        if not app or app["status"] != "pending":
            return await it.response.send_message(content=e("cross") + " Zaten işlenmiş.", ephemeral=True)
        db.q("UPDATE applications SET status='rejected' WHERE id=?", (self.app_id,))
        try: await it.message.edit(view=None)
        except Exception: pass
        await it.response.send_message(content=e("cross") + " Reddedildi: <@" + str(app["user_id"]) + ">")
        u = it.client.get_user(app["user_id"])
        if u:
            try: await u.send(content=e("broken") + " Başvurun reddedildi. " + it.guild.name)
            except Exception: pass

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
        self.xp_cd = {}; self._st_i = 0; self.ar_cd = {}
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
        self.add_view(self.gw_view); self.add_view(TicketOpenView()); self.add_view(TicketCloseView()); self.add_view(AppOpenView())
        self.status_loop.start(); self.gw_checker.start(); self.pro_checker.start()

    async def on_ready(self):
        refresh_emojis()
        try:
            for row in db.all("SELECT * FROM role_menus"):
                g = self.get_guild(row["guild_id"])
                if not g: continue
                roles = [(rid, g.get_role(rid).name) for rid in json.loads(row["role_ids"]) if g.get_role(rid)]
                if roles: self.add_view(RoleMenuView(row["menu_id"], roles))
            for row in db.all("SELECT id FROM applications WHERE status='pending'"):
                self.add_view(AppReviewView(row["id"]))
        except Exception: pass
        print("")
        print("╔═══════════════════════════════════════════════╗")
        print("║      💧  K A T R E   B O T   v2.7  💧           ║")
        print("║   Mesaj Stil Yardım • Nitro Emoji • 95+ Komut ║")
        print("╚═══════════════════════════════════════════════╝")
        print("✅ " + str(self.user) + "  🌐 " + str(len(self.guilds)) + "  🧩 " + str(len(self.commands)) +
              "  💎 Emoji slot: " + str(len(EMO_CACHE)) + "/" + str(len(SLOTS)))
        await self.change_presence(status=discord.Status.online,
            activity=discord.Activity(type=discord.ActivityType.watching, name="k!yardım | Katre Bot"))

    @tasks.loop(seconds=12)
    async def status_loop(self):
        owner = self.get_user(OWNER_ID)
        oname = owner.display_name if owner else "Owner"
        msgs = [(discord.ActivityType.watching, "k!yardım | Katre Bot"),
                (discord.ActivityType.playing, str(len(self.guilds)) + " sunucuda!"),
                (discord.ActivityType.listening, str(sum(g.member_count or 0 for g in self.guilds)) + " kullanıcıya"),
                (discord.ActivityType.competing, "k!quiz ile yarış!"),
                (discord.ActivityType.watching, "Owner: " + oname),
                (discord.ActivityType.playing, "k!pro ile ayrıcalık"),
                (discord.ActivityType.listening, "k!başvuru-panel")]
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
        for r in db.all("SELECT user_id FROM users WHERE pro=1 AND pro_expiry IS NOT NULL AND pro_expiry<?", (now.isoformat(),)):
            db.q("UPDATE users SET pro=0 WHERE user_id=?", (r["user_id"],))
            pro_log(r["user_id"], "SÜRESİ DOLDU")

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

    async def guild_log(self, guild, embed):
        try:
            r = db.one("SELECT channel_id FROM guild_logs WHERE guild_id=?", (guild.id,))
            if r and r["channel_id"]:
                ch = guild.get_channel(r["channel_id"])
                if ch: await ch.send(embed=embed)
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
                await self.mod_log(message.guild, E(e("lock") + " ANTİ-LİNK", message.author.mention + " → silindi.", C_MOD))
            elif p["badword"]:
                ws = [w["word"] for w in db.all("SELECT word FROM badwords WHERE guild_id=?", (message.guild.id,))]
                low = content.lower()
                if any(w and w in low for w in ws):
                    try: await message.delete()
                    except Exception: pass
                    okc = await self.punish(message.author, 1, "Küfür")
                    await self.mod_log(message.guild, E(e("cross") + " KÜFÜR", message.author.mention + " → 1dk " + ("✅" if okc else "❌"), C_MOD))
            if p["anti_spam"]:
                dq = self.spam.setdefault(message.guild.id, {}).setdefault(message.author.id, deque())
                dq.append(now)
                while dq and now - dq[0] > 5: dq.popleft()
                if len(dq) >= 7:
                    dq.clear()
                    okc = await self.punish(message.author, 5, "Spam")
                    try: await message.channel.purge(limit=6, check=lambda m: m.author.id == message.author.id)
                    except Exception: pass
                    await self.mod_log(message.guild, E(e("shield") + " ANTİ-SPAM", message.author.mention + " → 5dk " + ("✅" if okc else "❌"), C_MOD))
            if p["anti_flood"]:
                key = (message.guild.id, message.author.id)
                prev = self.flood.get(key)
                cnt = (prev[1] + 1) if (prev and prev[0] == content and now - prev[2] < 10) else 1
                self.flood[key] = (content, cnt, now)
                if cnt >= 3:
                    self.flood[key] = (content, 0, now)
                    try: await message.delete()
                    except Exception: pass
                    okc = await self.punish(message.author, 2, "Flood")
                    await self.mod_log(message.guild, E(e("shield") + " ANTİ-FLOOD", message.author.mention + " → 2dk " + ("✅" if okc else "❌"), C_MOD))
        except Exception:
            traceback.print_exc()

    async def on_message(self, message):
        if message.author.bot: return
        try:
            maint = db.one("SELECT maintenance FROM owner_settings WHERE id=1")["maintenance"]
            if maint and message.author.id != OWNER_ID: return
            if db.one("SELECT 1 FROM blacklist WHERE user_id=?", (message.author.id,)): return
        except Exception: traceback.print_exc()
        try:
            afk = db.one("SELECT * FROM afk WHERE user_id=?", (message.author.id,))
            if afk:
                db.q("DELETE FROM afk WHERE user_id=?", (message.author.id,))
                await message.channel.send(content=e("wave") + " " + message.author.mention + " tekrar aramızda!")
            if message.guild:
                for m in message.mentions:
                    a = db.one("SELECT * FROM afk WHERE user_id=?", (m.id,))
                    if a:
                        await message.channel.send(content=e("sleep") + " " + m.mention + " AFK: **" + (a["reason"] or "—") + "**"); break
        except Exception: pass
        await self.run_protections(message)
        try:
            if message.guild and not message.content.startswith(("k!", "K!")):
                nowt = datetime.datetime.now().timestamp()
                if nowt - self.ar_cd.get(message.guild.id, 0) > 3:
                    low = (message.content or "").lower()
                    for r in db.all("SELECT * FROM auto_replies WHERE guild_id=?", (message.guild.id,)):
                        if r["trigger"] and r["trigger"] in low:
                            self.ar_cd[message.guild.id] = nowt
                            await message.channel.send(r["response"][:1900]); break
        except Exception: pass
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
                        for lr in db.all("SELECT * FROM level_roles WHERE guild_id=? AND level<=?", (message.guild.id, lvl)):
                            rr = message.guild.get_role(lr["role_id"])
                            if rr and rr not in message.author.roles:
                                try: await message.author.add_roles(rr, reason="Seviye rolü")
                                except Exception: pass
                        await message.channel.send(content=e("chartup") + " " + message.author.mention +
                                                   " **Seviye " + str(lvl) + "** oldu! " + e("gift") + " +" + str(coin) + " coin")
                    db.q("UPDATE users SET xp=?, level=? WHERE user_id=?", (xp, lvl, message.author.id))
        except Exception: traceback.print_exc()
        await self.process_commands(message)

    async def on_message_edit(self, before, after):
        if before.author.bot or not before.guild or before.content == after.content: return
        await self.guild_log(before.guild, E(e("pen") + " MESAJ DÜZENLENDİ",
            before.author.mention + " • " + before.channel.mention +
            "\n**Eski:** " + (before.content or "")[:300] + "\n**Yeni:** " + (after.content or "")[:300], C_WARN))

    async def on_message_delete(self, message):
        try:
            if message.author.bot or not message.guild: return
            db.q("INSERT OR REPLACE INTO snipe(channel_id, author_id, content, attachment, ts) VALUES(?,?,?,?,?)",
                 (message.channel.id, message.author.id, (message.content or "")[:1000],
                  message.attachments[0].url if message.attachments else None, datetime.datetime.now().isoformat()))
            await self.guild_log(message.guild, E(e("trash") + " MESAJ SİLİNDİ",
                message.author.mention + " • " + message.channel.mention +
                "\n**İçerik:** " + ((message.content or "")[:300] or "_ek/medya_"), C_ERROR))
        except Exception: pass

    async def on_member_remove(self, member):
        await self.guild_log(member.guild, E(e("wave") + " AYRILDI",
            member.mention + " • Kalan: **" + str(member.guild.member_count) + "**", C_ERROR))

    async def on_member_update(self, before, after):
        if before.nick != after.nick:
            await self.guild_log(after.guild, E(e("tag") + " NICK DEĞİŞTİ",
                after.mention + "\n**Eski:** " + str(before.nick) + "\n**Yeni:** " + str(after.nick), C_WARN))

    async def on_command_completion(self, ctx):
        db.q("INSERT INTO cmd_stats(cmd,uses) VALUES(?,1) ON CONFLICT(cmd) DO UPDATE SET uses=uses+1", (ctx.command.name,))

    async def on_command_error(self, ctx, error):
        if isinstance(error, OwnerOnly): return
        if isinstance(error, ProOnly):
            v = View(); v.add_item(Button(label="Pro Destek", url=SUPPORT_URL, style=discord.ButtonStyle.link, emoji="💎"))
            await safe_reply(ctx, E(e("pro") + " PRO GEREKLİ!", "Bu komut Pro üyelere özel!\n" + SEP + "\n`k!pro`", C_PRO), v); return
        if isinstance(error, commands.CommandNotFound):
            await safe_reply(ctx, E(e("search") + " BULUNAMADI", "Tüm komutlar: `k!yardım`", C_WARN)); return
        if isinstance(error, commands.MissingRequiredArgument):
            await safe_reply(ctx, E(e("cross") + " EKSİK", "`k!" + ctx.command.name + " " + ctx.command.signature + "`", C_ERROR)); return
        if isinstance(error, commands.CommandOnCooldown):
            await safe_reply(ctx, E(e("time") + " BEKLE", "**" + str(int(error.retry_after)) + " sn** sonra.", C_WARN)); return
        if isinstance(error, commands.MissingPermissions):
            await safe_reply(ctx, E(e("lock") + " YETKİ", "`" + ", ".join(error.missing_permissions) + "`", C_ERROR)); return
        if isinstance(error, commands.CheckFailure):
            await safe_reply(ctx, E(e("lock") + " YETKİ", "Bu komutu kullanamazsın!", C_ERROR)); return
        if isinstance(error, commands.CommandInvokeError):
            orig = error.original
            if isinstance(orig, discord.Forbidden):
                try: await ctx.author.send(content=e("lock") + " #" + str(ctx.channel) + " kanalında yetkim yok!")
                except Exception: pass
                return
            error = orig
        await safe_reply(ctx, E(e("warn") + " HATA", "```\n" + str(error)[:900] + "\n```", C_ERROR))
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
                    await self.mod_log(member.guild, E(e("shield") + " RAID!", "10sn'de 8+ giriş → 10dk kilit!", C_ERROR))
                if (p["raid_until"] or 0) > now:
                    try: await member.send(content=e("shield") + " Sunucu raid korumasında!")
                    except Exception: pass
                    try: await member.kick(reason="Anti-raid")
                    except Exception: pass
                    return
        except Exception: traceback.print_exc()
        s = db.one("SELECT * FROM servers WHERE guild_id=?", (member.guild.id,))
        if s:
            if s["auto_role"]:
                r = member.guild.get_role(s["auto_role"])
                if r:
                    try: await member.add_roles(r, reason="Otorol")
                    except Exception: pass
            if s["welcome_ch"]:
                ch = member.guild.get_channel(s["welcome_ch"])
                if ch:
                    em = E(None, None, C_OK, thumb=member.display_avatar.url)
                    em.set_author(name=e("wave") + " HOŞ GELDİN!", icon_url=member.display_avatar.url)
                    em.description = "### " + member.mention + "\n" + e("party") + " **" + str(member.guild.member_count) + "** üye!\n📅 Hesap: <t:" + str(int(member.created_at.timestamp())) + ":R>"
                    try: await ch.send(embed=em)
                    except Exception: pass
        try:
            c = db.one("SELECT * FROM counters WHERE guild_id=?", (member.guild.id,))
            if c and not c["reached"]:
                ch = member.guild.get_channel(c["channel_id"])
                if ch:
                    cur = member.guild.member_count
                    if cur >= c["target"]:
                        db.q("UPDATE counters SET reached=1 WHERE guild_id=?", (member.guild.id,))
                        await ch.send(content=e("party") + " **HEDEFE ULAŞILDI: " + str(c["target"]) + " üye!**")
                    else:
                        await ch.send(content=e("target") + " **SAYAÇ: " + str(cur) + "/" + str(c["target"]) + "**\n" + progress_bar(cur / c["target"] * 100))
        except Exception: pass

    async def on_guild_join(self, guild):
        db.q("INSERT OR IGNORE INTO servers(guild_id, joined_at) VALUES(?,?)", (guild.id, datetime.datetime.now().isoformat()))
        db.q("INSERT OR IGNORE INTO protections(guild_id) VALUES(?)", (guild.id,))
        ch = guild.system_channel or next((c for c in guild.text_channels if c.permissions_for(guild.me).send_messages), None)
        if ch:
            await ch.send(content=e("logo") + " **KATRE BOT ARANIZDA!**\n" + SEP +
                          "\n" + e("arrow") + " `k!yardım` • `k!kurulum` • `k!başvuru-panel` • `k!koruma antispam aç`")

async def finalize_giveaway(bot, message_id):
    gw = db.one("SELECT * FROM giveaways WHERE message_id=?", (message_id,))
    if not gw or gw["status"] != "active": return
    parts = json.loads(gw["participants"])
    db.q("UPDATE giveaways SET status='ended' WHERE message_id=?", (message_id,))
    ch = bot.get_channel(gw["channel_id"])
    if not parts:
        if ch:
            try: await ch.send(content=e("give") + " **" + gw["prize"] + "** bitti — katılımcı yok.")
            except Exception: pass
        return
    n = min(gw["winners"], len(parts))
    winners = [bot.get_user(int(w)) for w in random.sample(parts, n)]
    mentions = "\n".join(w.mention if w else "?" for w in winners)
    if ch:
        try:
            await ch.send(content=e("party") + " **ÇEKİLİŞ BİTTİ: " + gw["prize"] + "**\n🏆 " + mentions)
            msg = await ch.fetch_message(message_id)
            done = gw_embed(gw, bot); done.set_author(name=e("give") + " SONA ERDİ"); done.color = C_PRO
            done.add_field(name="🏆 Kazananlar", value=mentions, inline=False)
            await msg.edit(embed=done, view=bot.gw_view)
        except Exception: pass

bot = KatreBot()
LINK_RE = re.compile(r"(https?://|discord\.gg/|www\.)", re.I)
FISH    = [("🐟 Levrek", 40), ("🐠 Nemo", 90), ("🐡 Balon", 60), ("🦈 Köpekbalığı", 200), ("🐙 Ahtapot", 120), ("👢 Çizme", 5)]
ORES    = [("⛏️ Kömür", 30), ("🥉 Bakır", 60), ("🥈 Gümüş", 110), ("🥇 Altın", 200), ("💎 Elmas", 400), ("🪨 Taş", 5)]
QUIZ    = [
    ("Türkiye'nin başkenti?", ["İstanbul", "Ankara", "İzmir", "Bursa"], 1),
    ("En büyük gezegen?", ["Dünya", "Mars", "Jüpiter", "Satürn"], 2),
    ("Discord.py hangi dilde?", ["Java", "Python", "C++", "Go"], 1),
    ("Suyun formülü?", ["H2O", "CO2", "O2", "NaCl"], 0),
    ("Bir yılda kaç gün?", ["360", "365", "370", "355"], 1),
    ("Karada en hızlı hayvan?", ["Aslan", "Çita", "Kartal", "Tavşan"], 1),
    ("1 KB kaç byte?", ["1000", "1024", "512", "2048"], 1),
    ("En derin okyanus?", ["Atlas", "Hint", "Pasifik", "Arktik"], 2),
]
DICE  = ["⚀", "", "", "⚃", "⚄", ""]
SLOTSY = ["🍒", "", "🍇", "🔔", "7️⃣", "💎"]
MEDALS = ["🥇", "", ""]

# ═══════════════════════════════════════════════════════════════════════════
# 🌐 GENEL
# ═══════════════════════════════════════════════════════════════════════════
@kategori("genel")
@bot.command(name="yardım", aliases=["yardim", "help", "komutlar"], help="Yardım menüsü")
@commands.cooldown(1, 5, commands.BucketType.user)
async def yardim(ctx):
    view = HelpView(bot).link_buttons()
    if HAS_PIL:
        av = await fetch_avatar(bot.user, 256)
        img = make_help_banner(av, bot.user.name, len(bot.commands), len(bot.guilds))
        buf = io.BytesIO(); img.save(buf, format="PNG"); buf.seek(0)
        await ctx.send(content=help_content(bot), file=discord.File(buf, filename="banner.png"), view=view)
    else:
        await ctx.send(content=help_content(bot), view=view)

@kategori("genel")
@bot.command(name="ping", help="Gecikme")
async def ping(ctx):
    ms = round(bot.latency * 1000)
    await ctx.send(content=e("chart") + " **PONG:** `" + str(ms) + "ms` " + ("🟢" if ms < 100 else "🟡"))

@kategori("genel")
@bot.command(name="istatistik", aliases=["stats"], help="Görsel istatistik")
async def istatistik(ctx):
    up = str(datetime.datetime.now() - bot.start_time).split(".")[0]
    total = db.one("SELECT SUM(uses) u FROM cmd_stats")["u"] or 0
    if HAS_PIL:
        img = make_stats_card(len(bot.guilds), sum(g.member_count or 0 for g in bot.guilds), len(bot.commands),
                              up, str(round(bot.latency * 1000)), total)
        buf = io.BytesIO(); img.save(buf, format="PNG"); buf.seek(0)
        em = E(None, None, C_MAIN); em.set_image(url="attachment://stats.png")
        await ctx.send(file=discord.File(buf, filename="stats.png"), embed=em)
    else:
        await ctx.send(content=e("chart") + " **İSTATİSTİK**\n" + e("dot") + " " + str(len(bot.guilds)) + " sunucu • " + str(len(bot.commands)) + " komut • " + up)

@kategori("genel")
@bot.command(name="davet", aliases=["invite"], help="Davet")
async def davet(ctx):
    url = discord.utils.oauth_url(str(bot.user.id), permissions=discord.Permissions(administrator=True))
    v = View()
    v.add_item(Button(label="Botu Ekle", url=url, style=discord.ButtonStyle.link, emoji="➕"))
    v.add_item(Button(label="Destek", url=SUPPORT_URL, style=discord.ButtonStyle.link, emoji="🔗"))
    await ctx.send(content=e("link") + " **KATRE BOT'U EKLE**\n" + SEP + "\nTüm sistemler tek botta!", view=v)

@kategori("genel")
@bot.command(name="avatar", aliases=["av", "pp"], help="Avatar")
async def avatar(ctx, user: discord.Member = None):
    user = user or ctx.author
    em = E(e("cam") + " " + user.display_name, color=C_MAIN, img=user.display_avatar.url)
    v = View(); v.add_item(Button(label="Aç", url=user.display_avatar.url, style=discord.ButtonStyle.link, emoji="🔗"))
    await safe_reply(ctx, em, v)

@kategori("genel")
@bot.command(name="profil", aliases=["profile"], help="Görsel profil")
@commands.cooldown(1, 3, commands.BucketType.user)
async def profil(ctx, user: discord.Member = None):
    user = user or ctx.author
    ensure_user(user.id, str(user))
    u = db.one("SELECT * FROM users WHERE user_id=?", (user.id,))
    accent = hex_to_rgb(u["pro_color"]) if (u["pro"] and u["pro_color"]) else ((255, 215, 0) if u["pro"] else (0, 168, 255))
    if HAS_PIL:
        av = await fetch_avatar(user)
        img = make_profile_card(user.display_name, user.id, user.created_at.strftime("%d.%m.%Y"),
                                user.joined_at.strftime("%d.%m.%Y") if user.joined_at else "—",
                                u["level"], u["coins"], u["rep"], bool(u["pro"]), u["pro_tag"], av, accent)
        buf = io.BytesIO(); img.save(buf, format="PNG"); buf.seek(0)
        em = E(None, None, C_MAIN); em.set_image(url="attachment://profil.png")
        await ctx.send(file=discord.File(buf, filename="profil.png"), embed=em)
    else:
        await ctx.send(content=e("star") + " **" + user.display_name + "** ─ Lv." + str(u["level"]) + " • " + str(u["coins"]) + " coin")

@kategori("genel")
@bot.command(name="sunucubilgi", aliases=["serverinfo"], help="Görsel sunucu kartı")
async def sunucubilgi(ctx):
    g = ctx.guild
    if HAS_PIL:
        icon = None
        try:
            if g.icon: icon = await g.icon.with_size(256).read()
        except Exception: pass
        ow = bot.get_user(g.owner_id)
        img = make_server_card(g.name, ow.display_name if ow else "?", g.member_count, len(g.channels),
                               len(g.roles), g.premium_subscription_count or 0, g.created_at.strftime("%d.%m.%Y"), icon)
        buf = io.BytesIO(); img.save(buf, format="PNG"); buf.seek(0)
        em = E(None, None, C_SYS); em.set_image(url="attachment://sunucu.png")
        await ctx.send(file=discord.File(buf, filename="sunucu.png"), embed=em)
    else:
        await ctx.send(content=e("gear") + " **" + g.name + "** ─ 👥 " + str(g.member_count) + " • 💬 " + str(len(g.channels)))

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
        em = E(None, None, C_MAIN); em.set_image(url="attachment://rank.png")
        await ctx.send(file=discord.File(buf, filename="rank.png"), embed=em)
    else:
        await ctx.send(content=e("chartup") + " **" + user.display_name + "** ─ Lv." + str(u["level"]) + " " + progress_bar(min(100, u["xp"] / need * 100)))

@kategori("genel")
@bot.command(name="sıralama", aliases=["sirala", "top", "lb"], help="Görsel sıralama")
async def sıralama(ctx):
    rows = db.all("SELECT * FROM users ORDER BY level DESC, xp DESC LIMIT 10")
    if not rows: return await ctx.send(content=e("chart") + " Henüz veri yok.")
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
        txt = e("star") + " **SIRALAMA**\n"
        for i, r in enumerate(rows):
            txt += (MEDALS[i] if i < 3 else str(i+1) + ".") + " <@" + str(r["user_id"]) + "> Lv." + str(r["level"]) + "\n"
        await ctx.send(content=txt)

@kategori("genel")
@bot.command(name="snipe", help="Silinen son mesaj")
@commands.cooldown(1, 3, commands.BucketType.user)
async def snipe(ctx):
    s = db.one("SELECT * FROM snipe WHERE channel_id=?", (ctx.channel.id,))
    if not s: return await ctx.send(content=e("cam") + " Kayıt yok.")
    em = E(None, None, C_FUN)
    em.set_author(name=e("cam") + " SNIPE")
    em.description = (s["content"] or "_metin yok_")[:1500]
    if s["attachment"]: em.set_image(url=s["attachment"])
    LINE(em, "👤", "<@" + str(s["author_id"]) + ">", True)
    LINE(em, e("time"), s["ts"][:16].replace("T", " "), True)
    await safe_reply(ctx, em)

@kategori("genel")
@bot.command(name="afk", help="[sebep] — AFK")
async def afk(ctx, *, sebep="Belirtilmedi"):
    db.q("INSERT OR REPLACE INTO afk(user_id, reason, since) VALUES(?,?,?)",
         (ctx.author.id, sebep[:100], datetime.datetime.now().isoformat()))
    await ctx.send(content=e("sleep") + " AFK oldun: **" + sebep[:100] + "**")

@kategori("genel")
@bot.command(name="rep", aliases=["itibar"], help="<@üye> — İtibar (12s)")
@commands.cooldown(1, 43200, commands.BucketType.user)
async def rep(ctx, user: discord.Member):
    if user.id == ctx.author.id: return await ctx.send(content=e("cross") + " Kendine olmaz!")
    ensure_user(user.id, str(user))
    db.q("UPDATE users SET rep=rep+1 WHERE user_id=?", (user.id,))
    await ctx.send(content=e("star") + " " + ctx.author.mention + " → " + user.mention + " +1 itibar")

@kategori("genel")
@bot.command(name="destek", aliases=["ticket"], help="Destek paneli (Yönetici)")
@commands.has_permissions(administrator=True)
async def destek(ctx):
    await ctx.send(content=e("ticket") + " **DESTEK MERKEZİ**\n" + SEP + "\nButona tıkla, formu doldur!", view=TicketOpenView())
    try: await ctx.message.delete()
    except Exception: pass

@kategori("genel")
@bot.command(name="not", aliases=["note"], help="<metin> — Not")
async def not_(ctx, *, metin):
    ensure_user(ctx.author.id, str(ctx.author))
    u = db.one("SELECT notes FROM users WHERE user_id=?", (ctx.author.id,))
    notes = json.loads(u["notes"]); notes.append({"t": metin, "d": datetime.datetime.now().isoformat()})
    db.q("UPDATE users SET notes=? WHERE user_id=?", (json.dumps(notes), ctx.author.id))
    await ctx.send(content=e("pen") + " Not kaydedildi (`" + str(len(notes)) + "`)")

@kategori("genel")
@bot.command(name="notlar", aliases=["notes"], help="Notların")
async def notlar(ctx):
    u = db.one("SELECT notes FROM users WHERE user_id=?", (ctx.author.id,))
    notes = json.loads(u["notes"]) if u else []
    if not notes: return await ctx.send(content=e("pen") + " Notun yok.")
    txt = e("pen") + " **NOTLARIN**\n" + "\n".join(e("arrow") + " " + n["t"][:80] for n in notes[-8:])
    await ctx.send(content=txt)

@kategori("genel")
@bot.command(name="doğumgünü", aliases=["dogumgunu"], help="<gün> <ay>")
async def doğumgünü(ctx, gün: int, ay: int):
    if not (1 <= gün <= 31 and 1 <= ay <= 12): return await ctx.send(content=e("cross") + " `k!doğumgünü 24 8`")
    db.q("UPDATE users SET birthday=? WHERE user_id=?", (str(gün) + "." + str(ay), ctx.author.id))
    await ctx.send(content=e("cake") + " Kaydedildi: **" + str(gün) + "." + str(ay) + "**")

@kategori("genel")
@bot.command(name="doğumgünleri", aliases=["dogumgunleri"], help="Bu ayın doğum günleri")
async def doğumgünleri(ctx):
    now = datetime.datetime.now()
    rows = [r for r in db.all("SELECT user_id,birthday FROM users WHERE birthday IS NOT NULL")
            if r["birthday"] and int(r["birthday"].split(".")[1]) == now.month]
    if not rows: return await ctx.send(content=e("cake") + " Bu ay yok.")
    txt = e("cake") + " **" + str(now.month) + ". AY DOĞUM GÜNLERİ**\n" + "\n".join(
        e("arrow") + " " + r["birthday"] + " → <@" + str(r["user_id"]) + ">" for r in sorted(rows, key=lambda x: int(x["birthday"].split(".")[0])))
    await ctx.send(content=txt)

@kategori("genel")
@bot.command(name="hatırlat", aliases=["hatirlat"], help="<dk> <metin>")
async def hatırlat(ctx, dk: int, *, metin):
    if dk < 1 or dk > 1440: return await ctx.send(content=e("cross") + " 1-1440!")
    await ctx.send(content=e("alarm") + " **" + str(dk) + " dk** → " + metin)
    await asyncio.sleep(dk * 60)
    await ctx.send(ctx.author.mention + " " + e("alarm") + " " + metin)

@kategori("genel")
@bot.command(name="botkontrol", aliases=["check"], help="Yetki teşhisi")
@commands.has_permissions(administrator=True)
async def botkontrol(ctx):
    p = ctx.channel.permissions_for(ctx.guild.me)
    checks = [("Mesaj Gör", p.view_channel), ("Mesaj Gönder", p.send_messages), ("Embed", p.embed_links),
              ("Tepki", p.add_reactions), ("Mesaj Yönet", p.manage_messages), ("Timeout", p.moderate_members),
              ("Rol", p.manage_roles), ("Kanal", p.manage_channels), ("At", p.kick_members), ("Ban", p.ban_members)]
    txt = e("tool") + " **BOT KONTROL — #" + ctx.channel.name + "**\n" + "\n".join(
        (e("check") if ok else e("cross")) + " " + n for n, ok in checks)
    await ctx.send(content=txt)

# ═══════════════════════════════════════════════════════════════════════════
# 🛡️ MODERASYON
# ═══════════════════════════════════════════════════════════════════════════
@kategori("mod")
@bot.command(name="yasakla", aliases=["ban"], help="<@üye> [sebep]")
@commands.has_permissions(ban_members=True)
@commands.bot_has_permissions(ban_members=True)
async def yasakla(ctx, user: discord.Member, *, sebep="Belirtilmedi"):
    v = ConfirmView()
    await ctx.send(content=e("warn") + " **" + str(user) + "** banlansın mı?\nSebep: " + sebep, view=v)
    await v.wait()
    if v.value is None: return await ctx.send(content=e("time") + " Zaman aşımı.")
    if v.value:
        try: await user.send(content=e("hammer") + " **" + ctx.guild.name + "** • " + sebep)
        except Exception: pass
        await user.ban(reason=str(ctx.author) + " | " + sebep)
        await ctx.send(content=e("hammer") + " " + user.mention + " yasaklandı!")

@kategori("mod")
@bot.command(name="at", aliases=["kick"], help="<@üye> [sebep]")
@commands.has_permissions(kick_members=True)
@commands.bot_has_permissions(kick_members=True)
async def at(ctx, user: discord.Member, *, sebep="Belirtilmedi"):
    v = ConfirmView()
    await ctx.send(content=e("warn") + " **" + str(user) + "** atılsın mı?", view=v)
    await v.wait()
    if v.value is None: return await ctx.send(content=e("time") + " Zaman aşımı.")
    if v.value:
        await user.kick(reason=str(ctx.author) + " | " + sebep)
        await ctx.send(content=e("kick") + " " + user.mention + " atıldı!")

@kategori("mod")
@bot.command(name="uyar", aliases=["warn"], help="<@üye> [sebep]")
@commands.has_permissions(manage_messages=True)
async def uyar(ctx, user: discord.Member, *, sebep="Belirtilmedi"):
    ensure_user(user.id, str(user))
    db.q("UPDATE users SET warnings=warnings+1 WHERE user_id=?", (user.id,))
    w = db.one("SELECT warnings FROM users WHERE user_id=?", (user.id,))["warnings"]
    await ctx.send(content=e("warn") + " " + user.mention + " uyarıldı (`" + str(w) + "`)")

@kategori("mod")
@bot.command(name="uyarılar", aliases=["warns"], help="[<@üye>]")
async def uyarılar(ctx, user: discord.Member = None):
    user = user or ctx.author
    ensure_user(user.id, str(user))
    w = db.one("SELECT warnings FROM users WHERE user_id=?", (user.id,))["warnings"]
    await ctx.send(content=e("warn") + " " + user.mention + " → **" + str(w) + "** uyarı")

@kategori("mod")
@bot.command(name="temizle", aliases=["purge", "sil"], help="<adet>")
@commands.has_permissions(manage_messages=True)
@commands.bot_has_permissions(manage_messages=True)
async def temizle(ctx, adet: int):
    if not 1 <= adet <= 500: return await ctx.send(content=e("cross") + " 1-500!")
    await ctx.channel.purge(limit=adet + 1)
    m = await ctx.send(content=e("trash") + " **" + str(adet) + "** mesaj silindi.")
    await m.delete(delay=5)

@kategori("mod")
@bot.command(name="yavaşmod", aliases=["slowmode"], help="<sn>")
@commands.has_permissions(manage_channels=True)
async def yavaşmod(ctx, sn: int):
    await ctx.channel.edit(slowmode_delay=sn)
    await ctx.send(content=e("time") + " Yavaşmod: **" + str(sn) + " sn**")

@kategori("mod")
@bot.command(name="kilit", aliases=["lock"], help="Kilitle")
@commands.has_permissions(manage_channels=True)
async def kilit(ctx):
    await ctx.channel.set_permissions(ctx.guild.default_role, send_messages=False)
    await ctx.send(content=e("lock") + " " + ctx.channel.mention + " kilitlendi.")

@kategori("mod")
@bot.command(name="kilitaç", aliases=["unlock"], help="Kilidi aç")
@commands.has_permissions(manage_channels=True)
async def kilitaç(ctx):
    await ctx.channel.set_permissions(ctx.guild.default_role, send_messages=None)
    await ctx.send(content=e("unlock") + " " + ctx.channel.mention + " açıldı.")

@kategori("mod")
@bot.command(name="otorol", aliases=["autorol"], help="<@rol|kapat>")
@commands.has_permissions(administrator=True)
async def otorol(ctx, *, arg):
    if arg.lower() in ("kapat", "off", "0"):
        db.q("UPDATE servers SET auto_role=NULL WHERE guild_id=?", (ctx.guild.id,))
        return await ctx.send(content=e("check") + " Otorol kapalı.")
    role = await commands.RoleConverter().convert(ctx, arg)
    db.q("UPDATE servers SET auto_role=? WHERE guild_id=?", (role.id, ctx.guild.id))
    await ctx.send(content=e("check") + " Otorol: " + role.mention)

@kategori("mod")
@bot.command(name="hoşgeldin", aliases=["hosgeldin"], help="<#kanal|kapat>")
@commands.has_permissions(administrator=True)
async def hoşgeldin(ctx, ch: discord.TextChannel = None):
    if ch is None:
        db.q("UPDATE servers SET welcome_ch=NULL WHERE guild_id=?", (ctx.guild.id,))
        return await ctx.send(content=e("check") + " Kapalı.")
    db.q("UPDATE servers SET welcome_ch=? WHERE guild_id=?", (ch.id, ctx.guild.id))
    await ctx.send(content=e("wave") + " Kanal: " + ch.mention)

@kategori("mod")
@bot.command(name="butonrol", aliases=["rolmenü"], help="<@rol...>")
@commands.has_permissions(administrator=True)
async def butonrol(ctx, roles: commands.Greedy[discord.Role], *, açıklama="Rollerinizi butonlarla alın!"):
    if not roles or len(roles) > 25: return await ctx.send(content=e("cross") + " 1-25 rol!")
    menu_id = str(random.randint(10**11, 10**12 - 1))
    db.q("INSERT OR REPLACE INTO role_menus(menu_id,guild_id,role_ids) VALUES(?,?,?)",
         (menu_id, ctx.guild.id, json.dumps([r.id for r in roles])))
    txt = e("tag") + " **ROL MENÜSÜ**\n" + açıklama + "\n" + SEP + "\n" + "\n".join(e("arrow") + " " + r.mention for r in roles)
    view = RoleMenuView(menu_id, [(r.id, r.name) for r in roles])
    bot.add_view(view)
    await ctx.send(content=txt, view=view)

@kategori("mod")
@bot.command(name="koruma", help="<mod> <aç/kapat>")
@commands.has_permissions(administrator=True)
async def koruma(ctx, mod: str, durum: str):
    mod = mod.lower().replace("-", "").replace("_", "")
    col = {"antispam": "anti_spam", "antiflood": "anti_flood", "antiraid": "anti_raid",
           "antilink": "anti_link", "badword": "badword", "küfür": "badword"}.get(mod)
    if not col: return await ctx.send(content=e("cross") + " Modüller: `antispam antiflood antiraid antilink badword`")
    db.q("INSERT OR IGNORE INTO protections(guild_id) VALUES(?)", (ctx.guild.id,))
    val = 1 if durum.lower() in ("aç", "ac", "on", "1") else 0
    db.q("UPDATE protections SET " + col + "=? WHERE guild_id=?", (val, ctx.guild.id))
    await ctx.send(content=e("shield") + " **" + mod.upper() + "** → " + ("AÇIK " + e("check") if val else "KAPALI " + e("cross")))

@kategori("mod")
@bot.command(name="korumadurum", help="Koruma durumu")
async def korumadurum(ctx):
    p = db.one("SELECT * FROM protections WHERE guild_id=?", (ctx.guild.id,)) or {}
    def st(v): return e("check") if v else e("cross")
    await ctx.send(content=e("shield") + " **KORUMA — " + ctx.guild.name + "**\n" +
        st(p.get("anti_spam")) + " Spam   " + st(p.get("anti_flood")) + " Flood   " +
        st(p.get("anti_raid")) + " Raid   " + st(p.get("anti_link")) + " Link   " + st(p.get("badword")) + " Küfür")

@kategori("mod")
@bot.command(name="korumalog", help="<#kanal>")
@commands.has_permissions(administrator=True)
async def korumalog(ctx, ch: discord.TextChannel):
    db.q("INSERT OR IGNORE INTO protections(guild_id) VALUES(?)", (ctx.guild.id,))
    db.q("UPDATE protections SET log_ch=? WHERE guild_id=?", (ch.id, ctx.guild.id))
    await ctx.send(content=e("log") + " Log: " + ch.mention)

@kategori("mod")
@bot.command(name="badword", help="<ekle/sil/liste> [kelime]")
@commands.has_permissions(administrator=True)
async def badword(ctx, işlem: str, *, kelime: str = None):
    gid = ctx.guild.id
    if işlem.lower() in ("ekle", "add"):
        if not kelime: return await ctx.send(content=e("cross") + " Kelime gir!")
        db.q("INSERT OR IGNORE INTO badwords(guild_id, word) VALUES(?,?)", (gid, kelime.lower()))
        await ctx.send(content=e("check") + " `" + kelime.lower() + "` eklendi.")
    elif işlem.lower() in ("sil", "remove"):
        db.q("DELETE FROM badwords WHERE guild_id=? AND word=?", (gid, (kelime or "").lower()))
        await ctx.send(content=e("check") + " Silindi.")
    else:
        ws = [w["word"] for w in db.all("SELECT word FROM badwords WHERE guild_id=?", (gid,))]
        await ctx.send(content=e("shield") + " **LİSTE:** " + (("`" + "`, `".join(ws) + "`") if ws else "Boş"))

@kategori("mod")
@bot.command(name="raidmodu", help="<aç/kapat>")
@commands.has_permissions(administrator=True)
async def raidmodu(ctx, mod: str):
    now = datetime.datetime.now().timestamp()
    db.q("INSERT OR IGNORE INTO protections(guild_id) VALUES(?)", (ctx.guild.id,))
    if mod.lower() in ("aç", "ac", "on"):
        db.q("UPDATE protections SET raid_until=? WHERE guild_id=?", (now + 600, ctx.guild.id))
        await ctx.send(content=e("shield") + " Raid modu **10 dk** AÇIK!")
    else:
        db.q("UPDATE protections SET raid_until=0 WHERE guild_id=?", (ctx.guild.id,))
        await ctx.send(content=e("check") + " Raid modu kapalı.")

@kategori("mod")
@bot.command(name="kurulum", aliases=["sunucukur", "setup"], help="Tek komutla sunucu kur")
@commands.has_permissions(administrator=True)
@commands.bot_has_permissions(manage_channels=True, manage_roles=True)
async def kurulum(ctx):
    v = SetupConfirmView()
    await ctx.send(content=e("gear") + " **SUNUCU KURULUM**\n4 kategori • 12 kanal • 4 rol + hoşgeldin\nOnaylıyor musun?", view=v)
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
        await ctx.send(content=e("check") + " **KURULUM BİTTİ!** 📁 4 • 💬 " + str(ck) + " • 🎭 4\n" + e("wave") + " " + hg.mention)
    except discord.Forbidden:
        await ctx.send(content=e("cross") + " Kanal+Rol yetkisi gerekli.")
    except Exception as ex:
        await ctx.send(content=e("warn") + " ```\n" + str(ex)[:400] + "\n```")

# ═══════════════════════════════════════════════════════════════════════════
# 📋 SİSTEMLER
# ═══════════════════════════════════════════════════════════════════════════
@kategori("sys")
@bot.command(name="başvuru-ayarla", aliases=["basvuru-ayarla"], help="<#log> [@rol]")
@commands.has_permissions(administrator=True)
async def başvuru_ayarla(ctx, ch: discord.TextChannel, role: discord.Role = None):
    db.q("INSERT OR REPLACE INTO app_settings(guild_id, log_ch, staff_role) VALUES(?,?,?)",
         (ctx.guild.id, ch.id, role.id if role else None))
    await ctx.send(content=e("clip") + " Başvuru sistemi: " + ch.mention + (("\nYetkili rolü: " + role.mention) if role else "") + "\nPanel: `k!başvuru-panel`")

@kategori("sys")
@bot.command(name="başvuru-panel", aliases=["basvuru-panel"], help="Başvuru paneli")
@commands.has_permissions(administrator=True)
async def başvuru_panel(ctx):
    txt = (e("clip") + " **YETKİLİ BAŞVURU**\n" + SEP +
           "\n" + e("check") + " 14+ yaş\n" + e("check") + " Haftada 20+ saat aktif\n" + e("check") + " Discord deneyimi\n\n**Butona tıkla, formu doldur!**")
    await ctx.send(content=txt, view=AppOpenView())
    try: await ctx.message.delete()
    except Exception: pass

@kategori("sys")
@bot.command(name="başvurular", aliases=["basvurular"], help="Bekleyen başvurular")
@commands.has_permissions(administrator=True)
async def başvurular(ctx):
    rows = db.all("SELECT * FROM applications WHERE guild_id=? AND status='pending'", (ctx.guild.id,))
    if not rows: return await ctx.send(content=e("clip") + " Bekleyen yok.")
    txt = e("time") + " **BEKLEYEN (" + str(len(rows)) + ")**\n" + "\n".join(
        e("arrow") + " #" + str(r["id"]) + " → <@" + str(r["user_id"]) + ">" for r in rows[:10])
    await ctx.send(content=txt)

@kategori("sys")
@bot.command(name="başvurum", aliases=["basvurum"], help="Başvuru durumun")
async def başvurum(ctx):
    r = db.one("SELECT * FROM applications WHERE guild_id=? AND user_id=? ORDER BY id DESC", (ctx.guild.id, ctx.author.id))
    if not r: return await ctx.send(content=e("clip") + " Başvurun yok.")
    st = {"pending": e("time") + " Beklemede", "accepted": e("check") + " Kabul", "rejected": e("cross") + " Red"}.get(r["status"], r["status"])
    await ctx.send(content=e("clip") + " Başvuru #" + str(r["id"]) + " → " + st)

@kategori("sys")
@bot.command(name="otocevap", help="<ekle/sil/liste>")
@commands.has_permissions(administrator=True)
async def otocevap(ctx, işlem: str, *, args=None):
    gid = ctx.guild.id
    if işlem.lower() in ("ekle", "add"):
        if not args or "|" not in args:
            return await ctx.send(content=e("cross") + " Örnek: `k!otocevap ekle selam | Aleyküm selam!`")
        trig, resp = [p.strip() for p in args.split("|", 1)]
        db.q("INSERT OR REPLACE INTO auto_replies(guild_id, trigger, response) VALUES(?,?,?)", (gid, trig.lower(), resp[:500]))
        await ctx.send(content=e("robot") + " `" + trig.lower() + "` → " + resp[:80])
    elif işlem.lower() in ("sil", "remove"):
        db.q("DELETE FROM auto_replies WHERE guild_id=? AND trigger=?", (gid, (args or "").lower()))
        await ctx.send(content=e("check") + " Silindi.")
    else:
        rows = db.all("SELECT * FROM auto_replies WHERE guild_id=?", (gid,))
        txt = e("robot") + " **OTO CEVAP (" + str(len(rows)) + ")**\n" + "\n".join(
            e("arrow") + " `" + r["trigger"] + "` → " + r["response"][:60] for r in rows[:15])
        await ctx.send(content=txt or (e("robot") + " Liste boş."))

@kategori("sys")
@bot.command(name="sayaç", help="<hedef> <#kanal|kapat>")
@commands.has_permissions(administrator=True)
async def sayaç(ctx, hedef: int, ch: discord.TextChannel = None):
    if ch is None or hedef <= 0:
        db.q("DELETE FROM counters WHERE guild_id=?", (ctx.guild.id,))
        return await ctx.send(content=e("check") + " Sayaç kapalı.")
    db.q("INSERT OR REPLACE INTO counters(guild_id, target, channel_id, reached) VALUES(?,?,?,0)", (ctx.guild.id, hedef, ch.id))
    await ctx.send(content=e("target") + " Hedef **" + str(hedef) + "** • " + ch.mention)

@kategori("sys")
@bot.command(name="seviyerol", help="<ekle/sil/liste> [seviye] [@rol]")
@commands.has_permissions(administrator=True)
async def seviyerol(ctx, işlem: str, seviye: int = 0, role: discord.Role = None):
    gid = ctx.guild.id
    if işlem.lower() in ("ekle", "add"):
        if not role: return await ctx.send(content=e("cross") + " `k!seviyerol ekle 5 @Rol`")
        db.q("INSERT INTO level_roles(guild_id, level, role_id) VALUES(?,?,?)", (gid, seviye, role.id))
        await ctx.send(content=e("chartup") + " Lv.**" + str(seviye) + "** → " + role.mention)
    elif işlem.lower() in ("sil", "remove"):
        db.q("DELETE FROM level_roles WHERE guild_id=? AND level=?", (gid, seviye))
        await ctx.send(content=e("check") + " Lv." + str(seviye) + " silindi.")
    else:
        rows = db.all("SELECT * FROM level_roles WHERE guild_id=? ORDER BY level", (gid,))
        if not rows: return await ctx.send(content=e("chartup") + " Kayıt yok.")
        await ctx.send(content=e("chartup") + " **SEVİYE ROLLERİ**\n" + "\n".join(
            e("arrow") + " Lv." + str(r["level"]) + " → <@&" + str(r["role_id"]) + ">" for r in rows))

@kategori("sys")
@bot.command(name="sunuculog", aliases=["logayarla"], help="<#kanal|kapat>")
@commands.has_permissions(administrator=True)
async def sunuculog(ctx, ch: discord.TextChannel = None):
    if ch is None:
        db.q("DELETE FROM guild_logs WHERE guild_id=?", (ctx.guild.id,))
        return await ctx.send(content=e("check") + " Log kapalı.")
    db.q("INSERT OR REPLACE INTO guild_logs(guild_id, channel_id) VALUES(?,?)", (ctx.guild.id, ch.id))
    await ctx.send(content=e("log") + " Log: " + ch.mention + "\n└ Mesaj silme/düzenleme, giriş-çıkış, nick")

# ═══════════════════════════════════════════════════════════════════════════
# 💰 EKONOMİ
# ═══════════════════════════════════════════════════════════════════════════
@kategori("eco")
@bot.command(name="cüzdan", aliases=["balance", "para"], help="Görsel cüzdan")
async def cüzdan(ctx, user: discord.Member = None):
    user = user or ctx.author
    ensure_user(user.id, str(user))
    u = db.one("SELECT * FROM users WHERE user_id=?", (user.id,))
    if HAS_PIL:
        av = await fetch_avatar(user)
        img = make_wallet_card(user.display_name, u["coins"], u["rep"], bool(u["pro"]), av,
                               (255, 215, 0) if u["pro"] else (46, 204, 113))
        buf = io.BytesIO(); img.save(buf, format="PNG"); buf.seek(0)
        em = E(None, None, C_ECO); em.set_image(url="attachment://cuzdan.png")
        await ctx.send(file=discord.File(buf, filename="cuzdan.png"), embed=em)
    else:
        await ctx.send(content=e("coin") + " **" + user.display_name + "** ─ " + str(u["coins"]) + " coin")

@kategori("eco")
@bot.command(name="günlük", aliases=["gunluk", "daily"], help="Günlük coin")
@commands.cooldown(1, 86400, commands.BucketType.user)
async def günlük(ctx):
    ensure_user(ctx.author.id, str(ctx.author))
    u = db.one("SELECT * FROM users WHERE user_id=?", (ctx.author.id,))
    bonus = random.randint(150, 400) + (250 if u["pro"] else 0)
    db.q("UPDATE users SET coins=coins+? WHERE user_id=?", (bonus, ctx.author.id))
    await ctx.send(content=e("gift") + " **+" + str(bonus) + " coin** " + e("coin"))

@kategori("eco")
@bot.command(name="çalış", aliases=["calis", "work"], help="Çalış")
@commands.cooldown(1, 1800, commands.BucketType.user)
async def çalış(ctx):
    job, a, b = random.choice([("💻 Yazılım", 200, 400), ("🎨 Tasarım", 150, 300), ("📹 İçerik", 180, 350),
                               ("🍕 Pizza", 100, 220), ("🚕 Şoför", 120, 260), ("📚 Ders", 160, 320)])
    pay = random.randint(a, b)
    db.q("UPDATE users SET coins=coins+? WHERE user_id=?", (pay, ctx.author.id))
    await ctx.send(content=e("coin") + " " + job + " → **+" + str(pay) + " coin**")

@kategori("eco")
@bot.command(name="balık", aliases=["fish"], help="Balık (5dk)")
@commands.cooldown(1, 300, commands.BucketType.user)
async def balık(ctx):
    name, val = random.choice(FISH)
    db.q("UPDATE users SET coins=coins+? WHERE user_id=?", (val, ctx.author.id))
    await ctx.send(content=e("fish") + " " + name + " → **+" + str(val) + "**")

@kategori("eco")
@bot.command(name="maden", aliases=["mine"], help="Maden (5dk)")
@commands.cooldown(1, 300, commands.BucketType.user)
async def maden(ctx):
    name, val = random.choice(ORES)
    db.q("UPDATE users SET coins=coins+? WHERE user_id=?", (val, ctx.author.id))
    await ctx.send(content=e("pick") + " " + name + " → **+" + str(val) + "**")

@kategori("eco")
@bot.command(name="soy", aliases=["rob"], help="<@üye>")
@commands.cooldown(1, 600, commands.BucketType.user)
async def soy(ctx, user: discord.Member):
    if user.id == ctx.author.id or user.bot: return await ctx.send(content=e("cross"))
    ensure_user(user.id, str(user))
    t = db.one("SELECT coins FROM users WHERE user_id=?", (user.id,))
    me = db.one("SELECT coins FROM users WHERE user_id=?", (ctx.author.id,))
    if t["coins"] < 200: return await ctx.send(content=e("cross") + " Coin yok!")
    if random.random() < 0.45:
        steal = random.randint(50, min(500, t["coins"]))
        db.q("UPDATE users SET coins=coins-? WHERE user_id=?", (steal, user.id))
        db.q("UPDATE users SET coins=coins+? WHERE user_id=?", (steal, ctx.author.id))
        await ctx.send(content=e("coin") + " Soydun! **+" + str(steal) + "**")
    else:
        fine = min(me["coins"], random.randint(50, 200))
        db.q("UPDATE users SET coins=coins-? WHERE user_id=?", (fine, ctx.author.id))
        await ctx.send(content=e("cross") + " Yakalandın! **-" + str(fine) + "**")

@kategori("eco")
@bot.command(name="transfer", aliases=["gönder"], help="<@üye> <miktar>")
async def transfer(ctx, user: discord.Member, miktar: int):
    if miktar <= 0 or user.id == ctx.author.id: return await ctx.send(content=e("cross"))
    ensure_user(user.id, str(user))
    me = db.one("SELECT coins FROM users WHERE user_id=?", (ctx.author.id,))
    if me["coins"] < miktar: return await ctx.send(content=e("cross") + " Yetersiz!")
    db.q("UPDATE users SET coins=coins-? WHERE user_id=?", (miktar, ctx.author.id))
    db.q("UPDATE users SET coins=coins+? WHERE user_id=?", (miktar, user.id))
    await ctx.send(content=e("coin") + " **" + str(miktar) + "** → " + user.mention)

@kategori("eco")
@bot.command(name="bahis", aliases=["bet"], help="<miktar> x2")
@commands.cooldown(1, 10, commands.BucketType.user)
async def bahis(ctx, miktar: int):
    if miktar <= 0: return await ctx.send(content=e("cross"))
    me = db.one("SELECT coins FROM users WHERE user_id=?", (ctx.author.id,))
    if me["coins"] < miktar: return await ctx.send(content=e("cross") + " Yetersiz!")
    win = random.random() < 0.5
    db.q("UPDATE users SET coins=coins+? WHERE user_id=?", (miktar if win else -miktar, ctx.author.id))
    await ctx.send(content=(e("gift") if win else e("cross")) + " **" + ("+" + str(miktar * 2) if win else "-" + str(miktar)) + "**")

@kategori("eco")
@bot.command(name="market", aliases=["shop"], help="Market")
async def market(ctx):
    txt = (e("money") + " **KATRE MARKET**\n" + SEP +
           "\n" + e("arrow") + " 💎 Pro 30g ─ `50.000`" +
           "\n" + e("arrow") + " 🎨 Rank rengi ─ `5.000`" +
           "\n" + e("arrow") + " ⭐ +10 Rep ─ `2.500`" +
           "\n" + e("arrow") + " 🏷️ Tag  `7.500`")
    v = View(); v.add_item(Button(label="Satın Al", url=SUPPORT_URL, style=discord.ButtonStyle.link, emoji="🛒"))
    await ctx.send(content=txt, view=v)

# ═══════════════════════════════════════════════════════════════════════════
# 🎮 EĞLENCE
# ═══════════════════════════════════════════════════════════════════════════
@kategori("fun")
@bot.command(name="8ball", help="<soru>")
async def eightball(ctx, *, soru):
    await ctx.send(content=e("game") + " **" + soru[:80] + "**\n" + e("arrow") + " " +
                   random.choice(["✅ Evet!", "🌟 Büyük ihtimal", "🤔 Belki", "❌ Hayır", "💀 Asla!", "🎯 Yüksek şans"]))

@kategori("fun")
@bot.command(name="yazıtura", aliases=["coin"], help="Yazı tura")
async def yazıtura(ctx):
    await ctx.send(content=e("dice") + " **" + random.choice(["YAZI", "TURA"]) + "**")

@kategori("fun")
@bot.command(name="zar", aliases=["dice"], help="Zar")
async def zar(ctx):
    r = random.randint(1, 6)
    await ctx.send(content=e("dice") + " " + DICE[r-1] + " **" + str(r) + "**")

@kategori("fun")
@bot.command(name="aşk", aliases=["ask", "love"], help="<@üye> görsel aşk")
async def aşk(ctx, user: discord.Member):
    pct = random.randint(0, 100)
    msg = "💔 Yok..." if pct < 30 else ("💛 Fena!" if pct < 60 else ("💚 Güzel!" if pct < 85 else "❤️ RUH İKİZİ!"))
    if HAS_PIL:
        av1 = await fetch_avatar(ctx.author, 128); av2 = await fetch_avatar(user, 128)
        img = make_love_card(ctx.author.display_name, user.display_name, pct, av1, av2)
        buf = io.BytesIO(); img.save(buf, format="PNG"); buf.seek(0)
        em = E(None, None, 0xFF69B4); em.set_image(url="attachment://ask.png"); em.description = msg
        await ctx.send(file=discord.File(buf, filename="ask.png"), embed=em)
    else:
        await ctx.send(content=e("heart") + " " + ctx.author.mention + " x " + user.mention + " " + progress_bar(pct) + " " + msg)

@kategori("fun")
@bot.command(name="slot", aliases=["slots"], help="Slot")
async def slot(ctx):
    r = [random.choice(SLOTSY) for _ in range(3)]
    await ctx.send(content=e("slot") + " ┃ " + " ┃ ".join(r) + " ┃\n" + (e("gift") + " JACKPOT!" if len(set(r)) == 1 else e("cross") + " Olmadı..."))

@kategori("fun")
@bot.command(name="seç", aliases=["sec"], help="<a> <b>...")
async def seç(ctx, *, seçenekler):
    opts = seçenekler.split()
    if len(opts) < 2: return await ctx.send(content=e("cross") + " 2+!")
    await ctx.send(content=e("target") + " Seçimim: **" + random.choice(opts) + "**")

@kategori("fun")
@bot.command(name="oylama", aliases=["anket"], help="<soru>")
async def oylama(ctx, *, soru):
    msg = await ctx.send(content=e("chart") + " **OYLAMA — " + ctx.author.display_name + "**\n### " + soru[:200] + "\n👍 • 👎 • 🤷")
    for r in ("👍", "👎", ""): await msg.add_reaction(r)

@kategori("fun")
@bot.command(name="quiz", aliases=["bilgi"], help="Yarışma +75 coin")
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
                await it.response.send_message(content=e("check") + " +75 coin +20 XP!", ephemeral=True)
            else:
                await it.response.send_message(content=e("cross") + " Doğru: **" + opts[ans] + "**", ephemeral=True)
            for b in view.children: b.disabled = True
            try: await it.message.edit(view=view)
            except Exception: pass
        return _cb
    for i, o in enumerate(opts):
        b = Button(label=o[:78], style=discord.ButtonStyle.primary, emoji=emojis[i])
        b.callback = make_cb(i); view.add_item(b)
    await ctx.send(content=e("game") + " **BİLGİ YARIŞMASI**\n### ❓ " + q + "\n⏱️ 30sn • 🏆 +75 coin", view=view)

@kategori("fun")
@bot.command(name="tahmin", help="<1-10> +100")
@commands.cooldown(1, 15, commands.BucketType.user)
async def tahmin(ctx, sayi: int):
    if not 1 <= sayi <= 10: return await ctx.send(content=e("cross") + " 1-10!")
    t = random.randint(1, 10)
    if sayi == t:
        db.q("UPDATE users SET coins=coins+100 WHERE user_id=?", (ctx.author.id,))
        await ctx.send(content=e("target") + " BİLDİN! **+100 coin**")
    else:
        await ctx.send(content=e("cross") + " Cevap: **" + str(t) + "**")

@kategori("fun")
@bot.command(name="evlen", aliases=["marry"], help="<@üye>")
async def evlen(ctx, user: discord.Member):
    if user.id == ctx.author.id or user.bot: return await ctx.send(content=e("cross"))
    if db.one("SELECT 1 FROM marriages WHERE user1=? OR user2=? OR user1=? OR user2=?",
              (ctx.author.id, ctx.author.id, user.id, user.id)):
        return await ctx.send(content=e("broken") + " Biriniz evli!")
    db.q("INSERT INTO marriages(user1, user2, since) VALUES(?,?,?)",
         (ctx.author.id, user.id, datetime.datetime.now().isoformat()))
    await ctx.send(content=e("ring") + " " + ctx.author.mention + " ❤️ " + user.mention + " evlendi!")

@kategori("fun")
@bot.command(name="boşan", aliases=["divorce"], help="Boşan")
async def boşan(ctx):
    db.q("DELETE FROM marriages WHERE user1=? OR user2=?", (ctx.author.id, ctx.author.id))
    await ctx.send(content=e("broken") + " Boşandın.")

@kategori("fun")
@bot.command(name="eş", help="[<@üye>]")
async def eş(ctx, user: discord.Member = None):
    user = user or ctx.author
    m = db.one("SELECT * FROM marriages WHERE user1=? OR user2=?", (user.id, user.id))
    if not m: return await ctx.send(content=e("broken") + " " + user.mention + " bekar.")
    other = m["user2"] if m["user1"] == user.id else m["user1"]
    await ctx.send(content=e("ring") + " " + user.mention + " ❤️ <@" + str(other) + ">")

# ═══════════════════════════════════════════════════════════════════════════
# 🎉 ÇEKİLİŞ
# ═══════════════════════════════════════════════════════════════════════════
@kategori("give")
@bot.command(name="çekiliş", aliases=["cekilis"], help="<süre> <kazanan> <ödül>")
@commands.has_permissions(administrator=True)
async def çekiliş(ctx, süre: str, kazanan: int, *, ödül):
    try: dk = parse_sure(süre)
    except Exception: return await ctx.send(content=e("cross") + " `k!çekiliş 60m 1 Nitro`")
    if dk < 1 or kazanan < 1: return await ctx.send(content=e("cross"))
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
    if not rows: return await ctx.send(content=e("give") + " Aktif çekiliş yok.")
    txt = e("give") + " **AKTİF (" + str(len(rows)) + ")**\n" + "\n".join(
        e("arrow") + " **" + g["prize"] + "** ─ 👥 " + str(len(json.loads(g["participants"]))) + " • <t:" + str(int(g["end_time"])) + ":R>"
        for g in rows)
    await ctx.send(content=txt)

@kategori("give")
@bot.command(name="çekilişbitir", aliases=["cekilisbitir"], help="<id>")
@commands.has_permissions(administrator=True)
async def çekilişbitir(ctx, mid: int):
    gw = db.one("SELECT * FROM giveaways WHERE message_id=? AND guild_id=?", (mid, ctx.guild.id))
    if not gw or gw["status"] != "active": return await ctx.send(content=e("cross"))
    await finalize_giveaway(bot, mid)
    await ctx.send(content=e("check") + " Bitirildi.")

# ═══════════════════════════════════════════════════════════════════════════
# 💎 PRO
# ═══════════════════════════════════════════════════════════════════════════
@kategori("pro")
@bot.command(name="pro", help="Pro durum")
async def pro(ctx, user: discord.Member = None):
    user = user or ctx.author
    ensure_user(user.id, str(user))
    u = db.one("SELECT * FROM users WHERE user_id=?", (user.id,))
    txt = (e("pro") + " **KATRE PRO**\n" + SEP +
           "\n" + e("dot") + " Durum: " + ("**PRO ✅**" if u["pro"] else "Yok") +
           "\n" + e("dot") + " Log: `" + str(len(db.all("SELECT 1 FROM pro_logs WHERE user_id=?", (user.id,)))) + "` kayıt" +
           "\n\n" + e("star") + " **AYRICALIKLAR**\n" + e("arrow") + " `prooda` `prorenk` `prostats` `proyazı`\n" + e("arrow") + " `proembed` `protag` `proxp` +250 günlük")
    await ctx.send(content=txt)

@kategori("pro")
@bot.command(name="prooda", help="Özel oda (PRO)")
@is_pro()
async def prooda(ctx):
    cat = discord.utils.get(ctx.guild.categories, name="💎 PRO ODALAR")
    if not cat:
        cat = await ctx.guild.create_category("💎 PRO ODALAR")
        await cat.set_permissions(ctx.guild.default_role, view_channel=False)
    ch = await ctx.guild.create_voice_channel("👑 " + ctx.author.display_name, category=cat)
    await ch.set_permissions(ctx.author, connect=True, manage_channels=True, move_members=True)
    await ctx.send(content=e("mic") + " Odan: " + ch.mention)

@kategori("pro")
@bot.command(name="prorenk", help="<hex> (PRO)")
@is_pro()
async def prorenk(ctx, hexcode: str):
    hexcode = hexcode.lstrip("#")
    if len(hexcode) != 6: return await ctx.send(content=e("cross") + " ff0000")
    try: int(hexcode, 16)
    except ValueError: return await ctx.send(content=e("cross") + " hex!")
    db.q("UPDATE users SET pro_color=? WHERE user_id=?", (hexcode, ctx.author.id))
    await ctx.send(content=e("palette") + " Renk: #" + hexcode.upper())

@kategori("pro")
@bot.command(name="prostats", help="Detay (PRO)")
@is_pro()
async def prostats(ctx):
    u = db.one("SELECT * FROM users WHERE user_id=?", (ctx.author.id,))
    await ctx.send(content=e("chart") + " **PRO İSTATİSTİK**\n" + e("dot") + " Mesaj `" + str(u["messages"]) +
                   "` • Lv `" + str(u["level"]) + "` • Coin `" + str(u["coins"]) + "` • Rep `" + str(u["rep"]) + "`")

@kategori("pro")
@bot.command(name="proyazı", help="<metin> (PRO)")
@is_pro()
async def proyazı(ctx, *, metin):
    await ctx.send(content=e("pen") + " " + fancy(metin[:200]))

@kategori("pro")
@bot.command(name="proembed", help="<başlık> | <metin> | <hex> (PRO)")
@is_pro()
async def proembed(ctx, *, args):
    parts = [p.strip() for p in args.split("|")]
    if len(parts) < 2: return await ctx.send(content=e("cross") + " `Duyuru | Merhaba | ff0000`")
    color = C_PRO
    if len(parts) >= 3:
        try: color = int(parts[2].lstrip("#"), 16)
        except ValueError: pass
    em = E(parts[0][:256], parts[1][:4000], color)
    em.set_footer(text="PRO • " + ctx.author.display_name)
    await safe_reply(ctx, em)

@kategori("pro")
@bot.command(name="protag", help="<metin> (PRO)")
@is_pro()
async def protag(ctx, *, tag):
    db.q("UPDATE users SET pro_tag=? WHERE user_id=?", (tag[:12], ctx.author.id))
    await ctx.send(content=e("tag") + " Tag: **" + tag[:12] + "**")

@kategori("pro")
@bot.command(name="proxp", help="2x (PRO)")
@is_pro()
async def proxp(ctx):
    u = db.one("SELECT xp2 FROM users WHERE user_id=?", (ctx.author.id,))
    new = 0 if u["xp2"] else 1
    db.q("UPDATE users SET xp2=? WHERE user_id=?", (new, ctx.author.id))
    await ctx.send(content=e("bolt") + " 2x XP: **" + ("AÇIK" if new else "KAPALI") + "**")

# ═══════════════════════════════════════════════════════════════════════════
# 👑 OWNER
# ═══════════════════════════════════════════════════════════════════════════
@kategori("owner")
@bot.command(name="sahip", aliases=["owner", "panel"], help="Owner paneli")
@is_owner()
async def sahip(ctx):
    maint = db.one("SELECT maintenance FROM owner_settings WHERE id=1")["maintenance"]
    txt = (e("owner") + " **OWNER PANELİ**\n" + SEP +
           "\n" + e("dot") + " Sunucu: **" + str(len(bot.guilds)) + "**" +
           "\n" + e("dot") + " Bakım: **" + ("🔴 AÇIK" if maint else "🟢 KAPALI") + "**" +
           "\n" + e("dot") + " Emoji: **" + str(len(EMO_CACHE)) + "/" + str(len(SLOTS)) + "** slot ayarlı" +
           "\n\n" + e("arrow") + " `k!emoji ayarla <slot> <emoji>` → nitro emoji sistemi")
    await ctx.send(content=txt, view=OwnerPanelView(bot))

@kategori("owner")
@bot.command(name="emoji", aliases=["emojiler"], help="<ayarla/liste/sıfırla/slotlar> — NİTRO EMOJİ YÖNETİMİ")
@is_owner()
async def emoji_cmd(ctx, işlem: str, slot: str = None, *, value: str = None):
    işlem = işlem.lower()
    if işlem in ("ayarla", "set"):
        if not slot or not value:
            return await ctx.send(content=e("cross") + " Kullanım: `k!emoji ayarla <slot> <emoji>`\nÖrnek: `k!emoji ayarla check <:tik:1093...>`")
        if "<" not in value or ":" not in value:
            return await ctx.send(content=e("cross") + " **Özel emoji yapıştır!** (Botun bulunduğu sunucudan emoji kopyala → mesaj olarak at)\nÖrnek: `<a:tick:1093...>`")
        slot = slot.lower()
        if slot not in SLOTS:
            return await ctx.send(content=e("cross") + " Bilinmeyen slot! Liste: `k!emoji slotlar`")
        db.q("INSERT OR REPLACE INTO emojis(slot, emoji) VALUES(?,?)", (slot, value))
        refresh_emojis()
        await ctx.send(content=e("check") + " Slot `" + slot + "` → " + value + "\n" + e("spark") + " Artık her yerde bu nitro emojisi!")
    elif işlem in ("liste", "list"):
        rows = db.all("SELECT * FROM emojis")
        if not rows:
            return await ctx.send(content=e("info") + " Henüz özel emoji yok. `k!emoji ayarla <slot> <emoji>`")
        await ctx.send(content=e("star") + " **AYARLI EMOJİLER (" + str(len(rows)) + "/" + str(len(SLOTS)) + ")**\n" +
                       "\n".join(e("arrow") + " `" + r["slot"] + "` → " + r["emoji"] for r in rows))
    elif işlem in ("sıfırla", "reset"):
        if slot in (None, "tümü", "all"):
            db.q("DELETE FROM emojis")
        else:
            db.q("DELETE FROM emojis WHERE slot=?", (slot.lower(),))
        refresh_emojis()
        await ctx.send(content=e("check") + " Varsayılana dönüldü.")
    elif işlem in ("slotlar", "slots"):
        await ctx.send(content=e("info") + " **EMOJİ SLOTLARI (" + str(len(SLOTS)) + ")**\n`" + "`, `".join(SLOTS.keys()) +
                       "`\n\nHer slotu özel/animasyonlu emojiyle değiştir → botun HER yeri nitro emoji olur!")
    else:
        await ctx.send(content=e("cross") + " `ayarla / liste / sıfırla / slotlar`")

@kategori("owner")
@bot.command(name="prover", help="<@üye> [gün] (KALICI LOG)")
@is_owner()
async def prover(ctx, user: discord.Member, gun: int = 30):
    ensure_user(user.id, str(user))
    exp = (datetime.datetime.now() + datetime.timedelta(days=gun)).isoformat()
    db.q("UPDATE users SET pro=1, pro_expiry=? WHERE user_id=?", (exp, user.id))
    pro_log(user.id, "VERİLDİ", gun, ctx.author.id)
    await ctx.send(content=e("pro") + " " + user.mention + " → **" + str(gun) + " gün** PRO • 📜 loglandı")
    try: await user.send(content=e("party") + " PRO oldun! **" + str(gun) + " gün**")
    except Exception: pass

@kategori("owner")
@bot.command(name="proal", help="<@üye> (KALICI LOG)")
@is_owner()
async def proal(ctx, user: discord.Member):
    db.q("UPDATE users SET pro=0, pro_expiry=NULL WHERE user_id=?", (user.id,))
    pro_log(user.id, "ALINDI", 0, ctx.author.id)
    await ctx.send(content=e("broken") + " " + user.mention + " pro alındı • 📜 loglandı")

@kategori("owner")
@bot.command(name="prologlar", aliases=["prolog"], help="Kalıcı pro geçmişi")
@is_owner()
async def prologlar(ctx, user: discord.User = None):
    rows = db.all("SELECT * FROM pro_logs WHERE user_id=? ORDER BY id DESC LIMIT 15", (user.id,)) if user \
           else db.all("SELECT * FROM pro_logs ORDER BY id DESC LIMIT 15")
    if not rows: return await ctx.send(content=e("log") + " Kayıt yok.")
    txt = e("log") + " **PRO LOG (" + str(len(rows)) + ") — KALICI**\n" + "\n".join(
        e("arrow") + " #" + str(r["id"]) + " **" + r["action"] + "** <@" + str(r["user_id"]) + "> • " + r["ts"][:16].replace("T", " ") for r in rows)
    await ctx.send(content=txt)

@kategori("owner")
@bot.command(name="bakım", aliases=["bakim"], help="[aç/kapat]")
@is_owner()
async def bakım(ctx, mod: str = None):
    cur = db.one("SELECT maintenance FROM owner_settings WHERE id=1")["maintenance"]
    new = (not cur) if mod is None else (mod.lower() in ("aç", "ac", "on", "1"))
    db.q("UPDATE owner_settings SET maintenance=? WHERE id=1", (int(new),))
    await ctx.send(content=e("tool") + " Bakım: **" + ("🔴 AÇIK" if new else "🟢 KAPALI") + "**")

@kategori("owner")
@bot.command(name="prefix", help="<prefix>")
@is_owner()
async def prefix(ctx, yeni: str):
    db.q("UPDATE servers SET prefix=? WHERE guild_id=?", (yeni, ctx.guild.id))
    await ctx.send(content=e("check") + " Prefix: `" + yeni + "`")

@kategori("owner")
@bot.command(name="blacklist", aliases=["bl"], help="<ekle/çıkar> <@üye>")
@is_owner()
async def blacklist(ctx, işlem: str, user: discord.User, *, sebep="—"):
    if işlem.lower() in ("ekle", "add"):
        db.q("INSERT OR REPLACE INTO blacklist(user_id,reason) VALUES(?,?)", (user.id, sebep))
        await ctx.send(content=e("cross") + " " + user.mention + " karalisteye eklendi.")
    elif işlem.lower() in ("çıkar", "cikar", "remove"):
        db.q("DELETE FROM blacklist WHERE user_id=?", (user.id,))
        await ctx.send(content=e("check") + " " + user.mention + " çıkarıldı.")
    else:
        await ctx.send(content=e("cross") + " `ekle/çıkar`")

@kategori("owner")
@bot.command(name="durum", aliases=["status"], help="<metin>")
@is_owner()
async def durum(ctx, *, metin):
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name=metin))
    await ctx.send(content=e("check") + " Durum: " + metin[:80])

@kategori("owner")
@bot.command(name="sunucular", aliases=["guilds"], help="Liste")
@is_owner()
async def sunucular(ctx):
    rows = sorted(bot.guilds, key=lambda g: -(g.member_count or 0))
    await ctx.send(content=e("gear") + " **SUNUCULAR (" + str(len(rows)) + ")**\n" + "\n".join(
        e("arrow") + " **" + g.name + "** ─ " + str(g.member_count) for g in rows[:15]))

@kategori("owner")
@bot.command(name="eval", aliases=["py"], help="<kod>")
@is_owner()
async def eval_cmd(ctx, *, code):
    env = {"bot": bot, "ctx": ctx, "db": db, "discord": discord, "guild": ctx.guild, "author": ctx.author}
    buf = io.StringIO()
    func = "async def __f():\n" + textwrap.indent(code, "    ")
    try:
        exec(compile(func, "<eval>", "exec"), env)
        with redirect_stdout(buf): await env["__f"]()
        await ctx.send(content="```py\n" + (buf.getvalue()[:1900] or "✅") + "\n```")
    except Exception as ex:
        await ctx.send(content="```py\n" + str(ex)[:1900] + "\n```")

# ═══════════════════════════════════════════════════════════════════════════
# 🚀 BAŞLAT
# ═══════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    bot.run(BOT_TOKEN)
