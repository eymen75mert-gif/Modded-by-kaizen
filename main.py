# ═══════════════════════════════════════════════════════════════════════════
#  💧 KATRE BOT v2.4 — TEK DOSYA • KORUMA • KURULUM • GÖRSEL RANK
#  ─ ENV: BOT_TOKEN, OWNER_ID, SUPPORT_URL
#  ─ KURULUM: pip install -U discord.py Pillow   →   python katre.py
#  ─ Railway requirements.txt:  discord.py
#                               Pillow
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
DICE    = ["⚀", "⚁", "", "", "⚄", "⚅"]
SLOTS   = ["🍒", "🍋", "🍇", "💎", "7️⃣", "🔔"]
MEDALS  = ["🥇", "🥈", "🥉"]
LINK_RE = re.compile(r"(https?://|discord\.gg/|www\.)", re.I)

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
            welcome_ch INTEGER, auto_role INTEGER, rank_on INTEGER DEFAULT 1,
            joined_at TEXT);
        CREATE TABLE IF NOT EXISTS users(
            user_id INTEGER PRIMARY KEY, name TEXT, xp INTEGER DEFAULT 0,
            level INTEGER DEFAULT 1, coins INTEGER DEFAULT 0,
            messages INTEGER DEFAULT 0, warnings INTEGER DEFAULT 0,
            pro INTEGER DEFAULT 0, pro_expiry TEXT, pro_color TEXT,
            pro_tag TEXT, xp2 INTEGER DEFAULT 0,
            birthday TEXT, notes TEXT DEFAULT '[]', rep INTEGER DEFAULT 0);
        CREATE TABLE IF NOT EXISTS owner_settings(
            id INTEGER PRIMARY KEY DEFAULT 1, maintenance INTEGER DEFAULT 0,
            status_text TEXT DEFAULT 'k!yardım | 💧 Katre Bot');
        CREATE TABLE IF NOT EXISTS giveaways(
            message_id INTEGER PRIMARY KEY, guild_id INTEGER, channel_id INTEGER,
            prize TEXT, winners INTEGER, end_time REAL, participants TEXT DEFAULT '[]',
            status TEXT DEFAULT 'active', host INTEGER);
        CREATE TABLE IF NOT EXISTS tickets(
            channel_id INTEGER PRIMARY KEY, guild_id INTEGER, user_id INTEGER,
            status TEXT DEFAULT 'open');
        CREATE TABLE IF NOT EXISTS role_menus(
            menu_id TEXT PRIMARY KEY, guild_id INTEGER, role_ids TEXT);
        CREATE TABLE IF NOT EXISTS blacklist(user_id INTEGER PRIMARY KEY, reason TEXT);
        CREATE TABLE IF NOT EXISTS cmd_stats(cmd TEXT PRIMARY KEY, uses INTEGER DEFAULT 0);
        CREATE TABLE IF NOT EXISTS protections(
            guild_id INTEGER PRIMARY KEY, anti_spam INTEGER DEFAULT 0,
            anti_flood INTEGER DEFAULT 0, anti_raid INTEGER DEFAULT 0,
            anti_link INTEGER DEFAULT 0, badword INTEGER DEFAULT 0,
            log_ch INTEGER, raid_until REAL DEFAULT 0);
        CREATE TABLE IF NOT EXISTS badwords(
            guild_id INTEGER, word TEXT, PRIMARY KEY(guild_id, word));
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
        raise ProOnly()
    return commands.check(pred)

def kategori(ad):
    def deco(cmd): cmd.kategori = ad; return cmd
    return deco

# ═══════════════════════════════════════════════════════════════════════════
# 🎨 EMBED + GÖRSEL YARDIMCILARI
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
    try:
        return await ctx.send(embed=embed, view=view)
    except Exception:
        try:
            return await ctx.author.send(embed=embed, view=view)
        except Exception:
            return None

def progress_bar(pct, length=12):
    pct = max(0, min(100, int(pct)))
    filled = round(pct / 100 * length)
    bar = "[" + "█" * filled + "░" * (length - filled) + "]"
    return "`" + bar + " %" + str(pct) + "`"

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

# ─────────────── 🖼️ GÖRSEL ÜRETİMİ (Pillow) ───────────────
FONT_PATHS = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/System/Library/Fonts/Helvetica.ttc",
    "C:/Windows/Fonts/arial.ttf",
]
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
    except Exception:
        return default

def make_rank_card(name, level, xp, need, coins, rep, pro, tag, accent, avatar_bytes):
    W, H = 900, 340
    img = Image.new("RGB", (W, H), (23, 24, 28))
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, W, 8], fill=accent)
    d.rectangle([0, H - 8, W, H], fill=accent)
    d.rounded_rectangle([18, 26, W - 18, H - 26], radius=24, fill=(32, 33, 40))
    if avatar_bytes:
        try:
            ava = Image.open(io.BytesIO(avatar_bytes)).convert("RGBA").resize((150, 150))
            mask = Image.new("L", (150, 150), 0)
            ImageDraw.Draw(mask).ellipse((0, 0, 150, 150), fill=255)
            img.paste(ava, (50, 62), mask)
            d = ImageDraw.Draw(img)
        except Exception: pass
    d.ellipse((50, 62, 200, 212), outline=accent, width=4)
    d.text((230, 55), name[:22], font=get_font(40), fill=(255, 255, 255))
    sub = ("Seviye " + str(level) + "   •   " + str(xp) + "/" + str(need) +
           " XP   •   " + str(coins) + " coin   •   " + str(rep) + " rep")
    d.text((230, 112), sub, font=get_font(24), fill=(160, 165, 175))
    bx0, by0, bx1, by1 = 230, 170, 850, 200
    d.rounded_rectangle([bx0, by0, bx1, by1], radius=15, fill=(45, 46, 54))
    pct = min(100, (xp / need * 100) if need else 0)
    fw = int((bx1 - bx0) * pct / 100)
    if fw > 12:
        d.rounded_rectangle([bx0, by0, bx0 + fw, by1], radius=15, fill=accent)
    d.text((bx1 - 60, by0 - 30), "%" + str(int(pct)), font=get_font(24), fill=accent)
    x, y = 230, 230
    if pro:
        d.rounded_rectangle([x, y, x + 90, y + 42], radius=21, fill=(255, 215, 0))
        d.text((x + 24, y + 9), "PRO", font=get_font(24), fill=(20, 20, 20))
        x += 105
    if tag:
        tw = 60 + 13 * len(tag[:12])
        d.rounded_rectangle([x, y, x + tw, y + 42], radius=21, fill=(70, 72, 82))
        d.text((x + 16, y + 9), tag[:12], font=get_font(24), fill=(255, 255, 255))
        x += tw + 15
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
        if i % 2 == 0:
            d.rectangle([0, y, W, y + row_h], fill=(30, 31, 37))
        col = medals[i] if i < 3 else (120, 125, 135)
        d.ellipse((25, y + 13, 61, y + 49), fill=col)
        d.text((38, y + 19), str(i + 1), font=get_font(24), fill=(20, 20, 20))
        label = name[:24] + ("  [PRO]" if pro else "")
        d.text((80, y + 16), label, font=get_font(26), fill=(255, 255, 255))
        d.text((W - 280, y + 18), "Lv." + str(level) + "  •  " + str(xp) + " XP",
               font=get_font(24), fill=(160, 165, 175))
        y += row_h
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
        "",
        "📂 **Aşağıdaki menüden kategori seç:**",
        "",
    ]
    for k, (i, n, _) in CATS.items():
        lines.append(i + " **" + n + "** ─ `" + str(cat_count(bot, k)) + "` komut")
    lines.append("")
    lines.append("🔗 Destek: [Tıkla](" + SUPPORT_URL + ")")
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
        pre = "🔒 **Bu komutlar yalnızca bot sahibine özeldir!**\nOwner olmayan kullanıcılar hiçbir yanıt alamaz.\n" + SEP + "\n"
    lines = []
    for c in sorted(cmds, key=lambda x: x.name):
        lines.append("`k!" + c.name + "` ─ " + (c.help or "—"))
    em.description = pre + ("\n".join(lines) if lines else "")
    return em

class HelpSelect(Select):
    def __init__(self, bot):
        opts = [discord.SelectOption(label=n, value=k, emoji=i,
                description=n + " komutlarını görüntüle") for k, (i, n, _) in CATS.items()]
        super().__init__(placeholder="📂 Bir kategori seçin...", options=opts,
                         min_values=1, max_values=1)
        self.bot = bot
    async def callback(self, it):
        key = self.values[0]
        if key == "owner" and it.user.id != OWNER_ID:
            return await it.response.send_message(
                embed=E("🔒 YETKİ YOK", "Owner paneli yalnızca bot sahibine açıktır!", C_ERROR),
                ephemeral=True)
        await it.response.edit_message(embed=cat_embed(self.bot, key), view=self.view)

class HelpView(View):
    def __init__(self, bot):
        super().__init__(timeout=600)
        self.bot = bot
        self.add_item(HelpSelect(bot))

    @discord.ui.button(label="Ana Menü", style=discord.ButtonStyle.primary, emoji="🏠")
    async def home(self, it, btn):
        await it.response.edit_message(embed=help_main_embed(self.bot), view=self)

    @discord.ui.button(label="İstatistik", style=discord.ButtonStyle.secondary, emoji="📊")
    async def stats(self, it, btn):
        up = datetime.datetime.now() - self.bot.start_time
        em = E(None, None, C_MAIN)
        em.set_author(name="📊 KATRE CANLI İSTATİSTİK", icon_url=self.bot.user.display_avatar.url)
        members = sum(g.member_count or 0 for g in self.bot.guilds)
        LINE(em, "🌐 Sunucu", "`" + str(len(self.bot.guilds)) + "`", True)
        LINE(em, "👥 Kullanıcı", "`" + str(members) + "`", True)
        LINE(em, "📡 Ping", "`" + str(round(self.bot.latency * 1000)) + "ms`", True)
        LINE(em, "⏱️ Uptime", "`" + str(up).split(".")[0] + "`", True)
        LINE(em, "🧩 Komut", "`" + str(len(self.bot.commands)) + "`", True)
        LINE(em, "️ Görsel Mod", "✅ Aktif" if HAS_PIL else "❌ Pillow yok", True)
        await it.response.send_message(embed=em, ephemeral=True)

    @discord.ui.button(label="Menüyü Kapat", style=discord.ButtonStyle.danger, emoji="🗑️")
    async def close(self, it, btn):
        await it.message.delete()

    def link_buttons(self):
        self.add_item(Button(label="Destek Sunucusu", url=SUPPORT_URL,
                             style=discord.ButtonStyle.link, emoji="🔗"))
        return self

class BroadcastModal(Modal, title="📢 Genel Duyuru"):
    txt = TextInput(label="Duyuru metni", style=discord.TextStyle.paragraph,
                    placeholder="Tüm sunuculara gönderilecek mesaj...")
    async def on_submit(self, it):
        ok = 0
        for g in it.client.guilds:
            ch = g.system_channel or next((c for c in g.text_channels
                         if c.permissions_for(g.me).send_messages), None)
            if ch:
                try:
                    await ch.send(embed=E("📢 OWNER DUYURUSU", self.txt.value, C_OWNER)); ok += 1
                except Exception: pass
        await it.response.send_message(embed=E("✅ DUYURU GÖNDERİLDİ",
            "`" + str(ok) + "/" + str(len(it.client.guilds)) + "` sunucuya iletildi.", C_OK),
            ephemeral=True)

class OwnerPanelView(View):
    def __init__(self, bot):
        super().__init__(timeout=600); self.bot = bot

    async def guard(self, it):
        if it.user.id != OWNER_ID:
            await it.response.send_message(embed=E("🔒", "Yalnızca owner!", C_ERROR), ephemeral=True)
            return False
        return True

    @discord.ui.button(label="Bakım Modu", style=discord.ButtonStyle.secondary, emoji="🔧")
    async def bakim(self, it, btn):
        if not await self.guard(it): return
        cur = db.one("SELECT maintenance FROM owner_settings WHERE id=1")["maintenance"]
        db.q("UPDATE owner_settings SET maintenance=? WHERE id=1", (0 if cur else 1,))
        msg = "**🔴 AÇILDI** — Bot artık sadece owner'a yanıt veriyor." if not cur else "**🟢 KAPATILDI** — Bot herkese açık."
        await it.response.send_message(embed=E("🔧 BAKIM MODU", msg, C_WARN), ephemeral=True)

    @discord.ui.button(label="İstatistik", style=discord.ButtonStyle.success, emoji="📊")
    async def stats(self, it, btn):
        if not await self.guard(it): return
        up = datetime.datetime.now() - self.bot.start_time
        total = db.one("SELECT SUM(uses) u FROM cmd_stats")["u"] or 0
        aktif = len(db.all("SELECT * FROM giveaways WHERE status='active'"))
        em = E(None, None, C_OWNER)
        em.set_author(name="👑 OWNER İSTATİSTİK PANELİ", icon_url=self.bot.user.display_avatar.url)
        LINE(em, "🌐 Sunucu", "`" + str(len(self.bot.guilds)) + "`", True)
        members = sum(g.member_count or 0 for g in self.bot.guilds)
        LINE(em, "👥 Kullanıcı", "`" + str(members) + "`", True)
        LINE(em, "📡 Ping", "`" + str(round(self.bot.latency * 1000)) + "ms`", True)
        LINE(em, "⏱️ Uptime", "`" + str(up).split(".")[0] + "`", True)
        LINE(em, "⌨️ Komut Kullanımı", "`" + str(total) + "`", True)
        LINE(em, "🎉 Aktif Çekiliş", "`" + str(aktif) + "`", True)
        top = db.all("SELECT cmd, uses FROM cmd_stats ORDER BY uses DESC LIMIT 5")
        if top:
            lines = []
            for i, t in enumerate(top, 1):
                lines.append("`" + str(i) + ".` k!" + t["cmd"] + " — **" + str(t["uses"]) + "**")
            LINE(em, "🔥 Top Komutlar", "\n".join(lines))
        await it.response.send_message(embed=em, ephemeral=True)

    @discord.ui.button(label="Sunucular", style=discord.ButtonStyle.primary, emoji="🖥️")
    async def guilds(self, it, btn):
        if not await self.guard(it): return
        em = E(None, None, C_OWNER)
        em.set_author(name="🖥️ BOTUN SUNUCULARI (" + str(len(self.bot.guilds)) + ")")
        rows = sorted(self.bot.guilds, key=lambda x: -(x.member_count or 0))[:10]
        for i, g in enumerate(rows, 1):
            LINE(em, "`" + str(i) + ".` " + g.name,
                 "└ 👥 " + str(g.member_count) + " • ID: `" + str(g.id) + "`")
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
    em.description = "### 🎁 Ödül: **" + gw["prize"] + "**\n🔘 Aşağıdaki **KATIL** butonuna bas!\n" + SEP
    LINE(em, "🏆 Kazanan", "`" + str(gw["winners"]) + "` kişi", True)
    LINE(em, "👥 Katılımcı", "`" + str(len(parts)) + "` kişi", True)
    LINE(em, "⏰ Bitiş", "<t:" + str(int(gw["end_time"])) + ":R>", True)
    LINE(em, "📣 Başlatan", "<@" + str(gw["host"]) + ">", True)
    LINE(em, "🆔 Çekiliş ID", "`" + str(gw["message_id"]) + "`", True)
    LINE(em, "️ Durum", " Aktif", True)
    return em

class GiveawayView(View):
    def __init__(self, bot):
        super().__init__(timeout=None); self.bot = bot

    @discord.ui.button(label="Katıl", style=discord.ButtonStyle.success, emoji="🎉",
                       custom_id="katre_gw_join", row=0)
    async def join(self, it, btn):
        gw = db.one("SELECT * FROM giveaways WHERE message_id=?", (it.message.id,))
        if not gw or gw["status"] != "active":
            return await it.response.send_message(embed=E("❌", "Çekiliş aktif değil!", C_ERROR), ephemeral=True)
        parts = json.loads(gw["participants"])
        if str(it.user.id) in parts:
            return await it.response.send_message(embed=E("ℹ️ ZATEN KATILDIN",
                "**" + gw["prize"] + "** çekilişine zaten katıldın! 🍀", C_WARN), ephemeral=True)
        parts.append(str(it.user.id))
        db.q("UPDATE giveaways SET participants=? WHERE message_id=?", (json.dumps(parts), it.message.id))
        try: await it.message.edit(embed=gw_embed(dict(gw, participants=json.dumps(parts)), self.bot), view=self)
        except Exception: pass
        await it.response.send_message(embed=E("✅ KATILDIN!",
            "**" + gw["prize"] + "** çekilişine kaydoldun!\n🍀 Bol şans!", C_OK), ephemeral=True)

    @discord.ui.button(label="Ayrıl", style=discord.ButtonStyle.secondary, emoji="🚪",
                       custom_id="katre_gw_leave", row=0)
    async def leave(self, it, btn):
        gw = db.one("SELECT * FROM giveaways WHERE message_id=?", (it.message.id,))
        if not gw or gw["status"] != "active":
            return await it.response.send_message(embed=E("❌", "Çekiliş aktif değil!", C_ERROR), ephemeral=True)
        parts = json.loads(gw["participants"])
        if str(it.user.id) not in parts:
            return await it.response.send_message(embed=E("ℹ️", "Bu çekilişe katılmamışsın.", C_WARN), ephemeral=True)
        parts.remove(str(it.user.id))
        db.q("UPDATE giveaways SET participants=? WHERE message_id=?", (json.dumps(parts), it.message.id))
        try: await it.message.edit(embed=gw_embed(dict(gw, participants=json.dumps(parts)), self.bot), view=self)
        except Exception: pass
        await it.response.send_message(embed=E("🚪 AYRILDIN", "**" + gw["prize"] + "** çekilişinden çıktın.", C_WARN), ephemeral=True)

    @discord.ui.button(label="Bitir", style=discord.ButtonStyle.primary, emoji="🏁",
                       custom_id="katre_gw_end", row=1)
    async def end(self, it, btn):
        if not it.user.guild_permissions.administrator:
            return await it.response.send_message(embed=E("🔒", "Yönetici olmalısın!", C_ERROR), ephemeral=True)
        await finalize_giveaway(self.bot, it.message.id)
        await it.response.send_message(embed=E("🏁", "Çekiliş sonlandırıldı!", C_OK), ephemeral=True)

    @discord.ui.button(label="Yeniden Çek", style=discord.ButtonStyle.secondary, emoji="🎲",
                       custom_id="katre_gw_reroll", row=1)
    async def reroll(self, it, btn):
        if not it.user.guild_permissions.administrator:
            return await it.response.send_message(embed=E("🔒", "Yönetici olmalısın!", C_ERROR), ephemeral=True)
        gw = db.one("SELECT * FROM giveaways WHERE message_id=?", (it.message.id,))
        if not gw: return
        parts = json.loads(gw["participants"])
        if not parts:
            return await it.response.send_message(embed=E("❌", "Katılımcı yok!", C_ERROR), ephemeral=True)
        w = self.bot.get_user(int(random.choice(parts)))
        await it.channel.send(embed=E("🎲 YENİDEN ÇEKİLİŞ",
            "### 🎁 " + gw["prize"] + "\n🏆 Yeni kazanan: " + (w.mention if w else "?") + "\n🎉 Tebrikler!", C_PRO))
        await it.response.defer()

    @discord.ui.button(label="+1 Saat", style=discord.ButtonStyle.success, emoji="⏳",
                       custom_id="katre_gw_extend", row=1)
    async def extend(self, it, btn):
        if not it.user.guild_permissions.administrator:
            return await it.response.send_message(embed=E("🔒", "Yönetici olmalısın!", C_ERROR), ephemeral=True)
        gw = db.one("SELECT * FROM giveaways WHERE message_id=?", (it.message.id,))
        if not gw or gw["status"] != "active":
            return await it.response.send_message(embed=E("❌", "Aktif çekiliş değil!", C_ERROR), ephemeral=True)
        new = gw["end_time"] + 3600
        db.q("UPDATE giveaways SET end_time=? WHERE message_id=?", (new, it.message.id))
        try: await it.message.edit(embed=gw_embed(dict(gw, end_time=new), self.bot), view=self)
        except Exception: pass
        await it.response.send_message(embed=E("⏳ UZATILDI", "Bitiş: <t:" + str(int(new)) + ":R>", C_OK), ephemeral=True)

    @discord.ui.button(label="İptal", style=discord.ButtonStyle.danger, emoji="🛑",
                       custom_id="katre_gw_cancel", row=1)
    async def cancel(self, it, btn):
        if not it.user.guild_permissions.administrator:
            return await it.response.send_message(embed=E("🔒", "Yönetici olmalısın!", C_ERROR), ephemeral=True)
        gw = db.one("SELECT * FROM giveaways WHERE message_id=?", (it.message.id,))
        if not gw: return
        db.q("UPDATE giveaways SET status='cancelled' WHERE message_id=?", (it.message.id,))
        try: await it.message.edit(embed=E("🛑 ÇEKİLİŞ İPTAL EDİLDİ", "**" + gw["prize"] + "** iptal edildi.", C_ERROR), view=None)
        except Exception: pass
        await it.response.send_message(embed=E("🛑", "Çekiliş iptal edildi.", C_WARN), ephemeral=True)

class RoleButton(Button):
    def __init__(self, role_id, label, custom_id, row):
        super().__init__(label=label[:78], style=discord.ButtonStyle.secondary,
                         emoji="🎭", custom_id=custom_id, row=row)
        self.role_id = role_id
    async def callback(self, it):
        role = it.guild.get_role(self.role_id)
        if not role:
            return await it.response.send_message(embed=E("❌", "Rol silinmiş.", C_ERROR), ephemeral=True)
        if role in it.user.roles:
            await it.user.remove_roles(role, reason="Rol menüsü")
            msg = "❌ **" + role.name + "** rolü üzerinden alındı."
        else:
            await it.user.add_roles(role, reason="Rol menüsü")
            msg = "✅ **" + role.name + "** rolü verildi!"
        await it.response.send_message(embed=E("🎭 ROL GÜNCELLENDİ", msg, C_OK), ephemeral=True)

class RoleMenuView(View):
    def __init__(self, menu_id, roles):
        super().__init__(timeout=None)
        for i, (rid, name) in enumerate(roles):
            self.add_item(RoleButton(rid, name, "katre_role_" + menu_id + "_" + str(rid), i // 5))

class TicketModal(Modal, title="🎫 Destek Talebi"):
    konu = TextInput(label="Konu", max_length=100, placeholder="Örn: Ödeme sorunu")
    aciklama = TextInput(label="Açıklama", style=discord.TextStyle.paragraph,
                         placeholder="Sorununu detaylı anlat...")
    async def on_submit(self, it):
        existing = db.one("SELECT * FROM tickets WHERE user_id=? AND status='open'", (it.user.id,))
        if existing:
            return await it.response.send_message(embed=E("❌ ZATEN TALEBİN VAR",
                "Mevcut talebin: <#" + str(existing["channel_id"]) + ">", C_WARN), ephemeral=True)
        guild = it.guild
        cat = discord.utils.get(guild.categories, name="💧 DESTEK")
        if not cat: cat = await guild.create_category("💧 DESTEK")
        ow = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            it.user: discord.PermissionOverwrite(view_channel=True, send_messages=True,
                                                 attach_files=True, embed_links=True),
            guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True,
                                                  manage_channels=True, manage_messages=True),
        }
        for r in guild.me.roles:
            if r.permissions.administrator or r.permissions.manage_messages:
                ow[r] = discord.PermissionOverwrite(view_channel=True, send_messages=True)
        ch = await guild.create_text_channel("destek-" + it.user.name, category=cat, overwrites=ow)
        db.q("INSERT INTO tickets(channel_id,guild_id,user_id) VALUES(?,?,?)", (ch.id, guild.id, it.user.id))
        em = E(None, None, C_MAIN, thumb=it.user.display_avatar.url)
        em.set_author(name="🎫 DESTEK TALEBİ OLUŞTURULDU")
        em.description = ("**Konu:** " + self.konu.value + "\n**Açıklama:** " + self.aciklama.value +
                          "\n" + SEP + "\n👤 **Kullanıcı:** " + it.user.mention +
                          "\n📅 **Tarih:** <t:" + str(int(datetime.datetime.now().timestamp())) + ":F>\n\n⏳ Ekibimiz birazdan yanında!")
        await ch.send(embed=em, view=TicketCloseView())
        await it.response.send_message(embed=E("✅ TALEP OLUŞTURULDU", "Kanalın: " + ch.mention, C_OK), ephemeral=True)

class TicketOpenView(View):
    def __init__(self):
        super().__init__(timeout=None)
    @discord.ui.button(label="Destek Talebi Oluştur", style=discord.ButtonStyle.primary,
                       emoji="🎫", custom_id="katre_ticket_open")
    async def open_ticket(self, it, btn):
        await it.response.send_modal(TicketModal())

class TicketCloseView(View):
    def __init__(self):
        super().__init__(timeout=None)
    @discord.ui.button(label="Talebi Kapat", style=discord.ButtonStyle.danger,
                       emoji="🔒", custom_id="katre_ticket_close")
    async def close_ticket(self, it, btn):
        t = db.one("SELECT * FROM tickets WHERE channel_id=?", (it.channel.id,))
        if not t:
            return await it.response.send_message(embed=E("❌", "Talep bulunamadı.", C_ERROR), ephemeral=True)
        if not (it.user.guild_permissions.administrator or it.user.id == t["user_id"]):
            return await it.response.send_message(embed=E("🔒", "Bu talebi kapatamazsın!", C_ERROR), ephemeral=True)
        db.q("UPDATE tickets SET status='closed' WHERE channel_id=?", (it.channel.id,))
        await it.response.send_message(embed=E("🔒 KAPATILIYOR", "Kanal **10 saniye** içinde silinecek...", C_WARN))
        await asyncio.sleep(10)
        try: await it.channel.delete(reason="Destek talebi kapatıldı")
        except Exception: pass

class ConfirmView(View):
    def __init__(self, timeout=30):
        super().__init__(timeout=timeout); self.value = None
    @discord.ui.button(label="Onayla", style=discord.ButtonStyle.danger, emoji="✅")
    async def yes(self, it, btn):
        self.value = True; self.stop()
        await it.response.edit_message(embed=E("⏳ İŞLENİYOR...", "İşlem uygulanıyor...", C_WARN), view=None)
    @discord.ui.button(label="Vazgeç", style=discord.ButtonStyle.secondary, emoji="❌")
    async def no(self, it, btn):
        self.value = False; self.stop()
        await it.response.edit_message(embed=E("❌ İPTAL", "İşlem iptal edildi.", C_WARN), view=None)

class SetupConfirmView(View):
    def __init__(self, timeout=60):
        super().__init__(timeout=timeout); self.value = None
    @discord.ui.button(label="Kurulumu Başlat", style=discord.ButtonStyle.success, emoji="🏗️")
    async def yes(self, it, btn):
        self.value = True; self.stop()
        await it.response.edit_message(embed=E("🏗️ KURULUM", "Sunucu kuruluyor... lütfen bekle (≈10 sn)", C_WARN), view=None)
    @discord.ui.button(label="Vazgeç", style=discord.ButtonStyle.secondary, emoji="❌")
    async def no(self, it, btn):
        self.value = False; self.stop()
        await it.response.edit_message(embed=E("❌ İPTAL", "Kurulum iptal edildi.", C_WARN), view=None)

# ═══════════════════════════════════════════════════════════════════════════
# 🤖 BOT
# ═══════════════════════════════════════════════════════════════════════════
class KatreBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.all()
        super().__init__(command_prefix=self.get_prefix, intents=intents,
                         case_insensitive=True, help_command=None,
                         allowed_mentions=discord.AllowedMentions(users=True, roles=False, everyone=False))
        self.start_time = datetime.datetime.now()
        self.xp_cd = {}
        self._st_i = 0
        self.spam = {}
        self.flood = {}
        self.joins = {}

    async def get_prefix(self, message):
        p = "k!"
        if message.guild:
            s = db.one("SELECT prefix FROM servers WHERE guild_id=?", (message.guild.id,))
            if s: p = s["prefix"]
        base = {p, p.lower(), p.upper()}
        if self.user:
            base.add("<@" + str(self.user.id) + "> ")
            base.add("<@!" + str(self.user.id) + "> ")
        return list(base)

    async def setup_hook(self):
        self.gw_view = GiveawayView(self)
        self.add_view(self.gw_view)
        self.add_view(TicketOpenView())
        self.add_view(TicketCloseView())
        self.status_loop.start()
        self.gw_checker.start()
        self.pro_checker.start()

    async def on_ready(self):
        try:
            for row in db.all("SELECT * FROM role_menus"):
                guild = self.get_guild(row["guild_id"])
                if not guild: continue
                roles = []
                for rid in json.loads(row["role_ids"]):
                    r = guild.get_role(rid)
                    if r: roles.append((rid, r.name))
                if roles: self.add_view(RoleMenuView(row["menu_id"], roles))
        except Exception: pass
        print("")
        print("╔═══════════════════════════════════════════════╗")
        print("║      💧  K A T R E   B O T   v2.4  💧           ║")
        print("║   Koruma • Kurulum • Görsel Rank • Tek Dosya    ║")
        print("╚═══════════════════════════════════════════════╝")
        print("✅ Giriş yapıldı : " + str(self.user))
        print("🌐 Sunucu sayısı : " + str(len(self.guilds)))
        print("👑 Owner         : " + str(OWNER_ID))
        print("🧩 Komut sayısı  : " + str(len(self.commands)))
        print("🖼️ Görsel mod    : " + ("Pillow ✅" if HAS_PIL else "Yok ❌ (embed fallback)"))
        print("═══════════════════════════════════════════════")
        await self.change_presence(status=discord.Status.online,
            activity=discord.Activity(type=discord.ActivityType.watching, name="k!yardım | 💧 Katre Bot"))

    @tasks.loop(seconds=12)
    async def status_loop(self):
        owner = self.get_user(OWNER_ID)
        oname = owner.display_name if owner else "Owner"
        members = sum(g.member_count or 0 for g in self.guilds)
        msgs = [
            (discord.ActivityType.watching, "k!yardım | 💧 Katre Bot"),
            (discord.ActivityType.playing,  str(len(self.guilds)) + " sunucuda! 🌐"),
            (discord.ActivityType.listening, str(members) + " kullanıcıya 🎧"),
            (discord.ActivityType.competing, "k!çekiliş ile yarış! 🎉"),
            (discord.ActivityType.watching, "Owner: " + oname + " 👑"),
            (discord.ActivityType.playing,  "k!pro ile ayrıcalık 💎"),
            (discord.ActivityType.listening, "k!koruma • Sunucun güvende 🛡️"),
        ]
        t, m = msgs[self._st_i % len(msgs)]
        self._st_i += 1
        try: await self.change_presence(status=discord.Status.online, activity=discord.Activity(type=t, name=m))
        except Exception: pass

    @tasks.loop(seconds=15)
    async def gw_checker(self):
        now = datetime.datetime.now().timestamp()
        for gw in db.all("SELECT * FROM giveaways WHERE status='active' AND end_time<=?", (now,)):
            await finalize_giveaway(self, gw["message_id"])

    @tasks.loop(minutes=5)
    async def pro_checker(self):
        now = datetime.datetime.now().isoformat()
        db.q("UPDATE users SET pro=0 WHERE pro=1 AND pro_expiry IS NOT NULL AND pro_expiry<?", (now,))

    # ── 🛡️ KORUMA YARDIMCILARI ──
    async def punish(self, member, minutes, reason):
        try:
            await member.timeout(datetime.timedelta(minutes=minutes), reason=reason)
            return True
        except Exception:
            return False

    async def mod_log(self, guild, embed):
        p = db.one("SELECT log_ch FROM protections WHERE guild_id=?", (guild.id,))
        if p and p["log_ch"]:
            ch = guild.get_channel(p["log_ch"])
            if ch:
                try:
                    await ch.send(embed=embed); return
                except Exception: pass

    async def run_protections(self, message):
        """✅ Anti-spam / flood / link / küfür — istisna fırlatmaz"""
        try:
            if not message.guild: return
            if message.author.guild_permissions.administrator: return
            if not message.guild.me.guild_permissions.moderate_members: return
            p = db.one("SELECT * FROM protections WHERE guild_id=?", (message.guild.id,))
            if not p: return
            now = datetime.datetime.now().timestamp()
            content = message.content or ""
            if p["anti_link"] and LINK_RE.search(content):
                try: await message.delete()
                except Exception: pass
                await self.mod_log(message.guild, E("🔗 ANTİ-LİNK",
                    message.author.mention + " link paylaştı → mesaj silindi.", C_MOD))
            elif p["badword"]:
                ws = [w["word"] for w in db.all("SELECT word FROM badwords WHERE guild_id=?", (message.guild.id,))]
                low = content.lower()
                if any(w and w in low for w in ws):
                    try: await message.delete()
                    except Exception: pass
                    okc = await self.punish(message.author, 1, "Küfür filtresi")
                    await self.mod_log(message.guild, E("🤬 KÜFÜR FİLTRESİ",
                        message.author.mention + " yasaklı kelime kullandı → 1 dk susturma " + ("✅" if okc else "(yetki yok)"), C_MOD))
            if p["anti_spam"]:
                dq = self.spam.setdefault(message.guild.id, {}).setdefault(message.author.id, deque())
                dq.append(now)
                while dq and now - dq[0] > 5: dq.popleft()
                if len(dq) >= 7:
                    dq.clear()
                    okc = await self.punish(message.author, 5, "Anti-spam")
                    try: await message.channel.purge(limit=6, check=lambda m: m.author.id == message.author.id)
                    except Exception: pass
                    await self.mod_log(message.guild, E("🚫 ANTİ-SPAM",
                        message.author.mention + " 5sn'de 7+ mesaj → 5 dk susturma " + ("✅" if okc else "(yetki yok)"), C_MOD))
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
                    await self.mod_log(message.guild, E("🌊 ANTİ-FLOOD",
                        message.author.mention + " aynı mesajı floodladı → 2 dk susturma " + ("✅" if okc else "(yetki yok)"), C_MOD))
        except Exception:
            traceback.print_exc()

    async def on_message(self, message):
        if message.author.bot:
            return
        # 1) Sessiz engeller
        try:
            maint = db.one("SELECT maintenance FROM owner_settings WHERE id=1")["maintenance"]
            if maint and message.author.id != OWNER_ID:
                return
            if db.one("SELECT 1 FROM blacklist WHERE user_id=?", (message.author.id,)):
                return
        except Exception:
            traceback.print_exc()
        # 2) 🛡️ Koruma sistemleri
        await self.run_protections(message)
        # 3) XP / istatistik (asla komutları engellemez)
        try:
            ensure_user(message.author.id, str(message.author))
            if message.guild:
                db.q("UPDATE users SET messages=messages+1, name=? WHERE user_id=?",
                     (str(message.author), message.author.id))
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
                        em.description = (message.author.mention + " artık **Seviye " + str(lvl) + "**! 🚀\n" +
                                          SEP + "\n🎁 Hediye: **" + str(coin) + " coin**\n💧 Devam et, harika gidiyorsun!")
                        LINE(em, "📊 İlerleme", progress_bar(xp / (lvl * 100) * 100))
                        try: await message.channel.send(embed=em)
                        except Exception: pass
                    db.q("UPDATE users SET xp=?, level=? WHERE user_id=?", (xp, lvl, message.author.id))
        except Exception:
            traceback.print_exc()
        # 4) ✅ KOMUTLAR HER DURUMDA İŞLENİR
        await self.process_commands(message)

    async def on_command_completion(self, ctx):
        db.q("INSERT INTO cmd_stats(cmd,uses) VALUES(?,1) ON CONFLICT(cmd) DO UPDATE SET uses=uses+1",
             (ctx.command.name,))

    async def on_command_error(self, ctx, error):
        if isinstance(error, OwnerOnly):
            return
        if isinstance(error, ProOnly):
            v = View(); v.add_item(Button(label="Pro Olmak İçin Destek", url=SUPPORT_URL,
                                          style=discord.ButtonStyle.link, emoji="💎"))
            await safe_reply(ctx, E("💎 PRO GEREKLİ!",
                "Bu komut yalnızca **Pro üyelere** özeldir!\n" + SEP +
                "\n👑 Owner'dan pro üyelik alabilirsin.\n📋 Pro komutlar: `k!pro`", C_PRO), v)
            return
        if isinstance(error, commands.CommandNotFound):
            await safe_reply(ctx, E("❓ KOMUT BULUNAMADI", "Tüm komutlar için: `k!yardım`", C_WARN))
            return
        if isinstance(error, commands.MissingRequiredArgument):
            await safe_reply(ctx, E("❌ EKSİK ARGÜMAN",
                "Doğru kullanım:\n`k!" + ctx.command.name + " " + ctx.command.signature + "`", C_ERROR))
            return
        if isinstance(error, commands.CommandOnCooldown):
            await safe_reply(ctx, E("⏳ BEKLEME SÜRESİ",
                "Tekrar kullanmak için **" + str(int(error.retry_after)) + " saniye** beklemelisin.", C_WARN))
            return
        if isinstance(error, commands.MissingPermissions):
            await safe_reply(ctx, E("🔒 YETKİ YOK",
                "Gerekli yetki(ler): `" + ", ".join(error.missing_permissions) + "`", C_ERROR))
            return
        if isinstance(error, commands.CheckFailure):
            await safe_reply(ctx, E("🔒 YETKİ YOK", "Bu komutu kullanma yetkin yok!", C_ERROR))
            return
        if isinstance(error, commands.CommandInvokeError):
            original = error.original
            if isinstance(original, discord.Forbidden):
                try:
                    await ctx.author.send(embed=E("🔒 YETKİ SORUNU",
                        "**#" + str(ctx.channel) + "** kanalında mesaj/embed gönderme yetkim yok!\n" +
                        "Yöneticiden bot'a **Mesaj Gönder + Embed Gönder** yetkisi vermesini iste.", C_ERROR))
                except Exception:
                    pass
                return
            error = original
        await safe_reply(ctx, E("⚠️ BEKLENMEYEN HATA", "```\n" + str(error)[:900] + "\n```", C_ERROR))
        traceback.print_exc()

    async def on_member_join(self, member):
        ensure_user(member.id, str(member))
        # ⚔️ ANTI-RAID
        try:
            p = db.one("SELECT * FROM protections WHERE guild_id=?", (member.guild.id,))
            if p and p["anti_raid"]:
                now = datetime.datetime.now().timestamp()
                dq = self.joins.setdefault(member.guild.id, deque())
                dq.append(now)
                while dq and now - dq[0] > 10: dq.popleft()
                if len(dq) >= 8 and now > (p["raid_until"] or 0):
                    db.q("UPDATE protections SET raid_until=? WHERE guild_id=?", (now + 600, member.guild.id))
                    alert = E("⚔️ RAID ALGILANDI!",
                              "10 saniyede **8+** giriş tespit edildi!\nRaid modu **10 dakika** aktif → yeni girişler engelleniyor.", C_ERROR)
                    await self.mod_log(member.guild, alert)
                    try:
                        if member.guild.system_channel: await member.guild.system_channel.send(embed=alert)
                    except Exception: pass
                if (p["raid_until"] or 0) > now:
                    try:
                        await member.send(embed=E("⚔️ RAID MODU",
                            member.guild.name + " sunucusu şu an raid korumasında.\nBirkaç dakika sonra tekrar dene!", C_WARN))
                    except Exception: pass
                    try: await member.kick(reason="Anti-raid")
                    except Exception: pass
                    await self.mod_log(member.guild, E("⚔️ ANTİ-RAID", str(member) + " raid modu nedeniyle engellendi.", C_ERROR))
                    return
        except Exception:
            traceback.print_exc()
        # Hoşgeldin + otorol
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
                em.description = ("### " + member.mention + " aramıza katıldı!\n" +
                                  "🎉 Sunucumuz artık **" + str(member.guild.member_count) + "** üye!\n" + SEP +
                                  "\n📅 Hesap: <t:" + str(int(member.created_at.timestamp())) + ":R>" +
                                  "\n💧 İyi eğlenceler dileriz!")
                try: await ch.send(embed=em)
                except Exception: pass

    async def on_guild_join(self, guild):
        db.q("INSERT OR IGNORE INTO servers(guild_id, joined_at) VALUES(?,?)",
             (guild.id, datetime.datetime.now().isoformat()))
        db.q("INSERT OR IGNORE INTO protections(guild_id) VALUES(?)", (guild.id,))
        ch = guild.system_channel or next((c for c in guild.text_channels
                     if c.permissions_for(guild.me).send_messages), None)
        if ch:
            em = E(None, None, C_MAIN, thumb=self.user.display_avatar.url)
            em.set_author(name="💧 KATRE BOT ARANIZDA!", icon_url=self.user.display_avatar.url)
            em.description = ("**" + guild.name + "** sunucusuna hoş geldim! 🎉\n" + SEP +
                              "\n📚 Komutlar: `k!yardım`\n🏗️ Sunucu kur: `k!kurulum`" +
                              "\n🛡️ Koruma: `k!koruma antispam aç`\n🎉 Çekiliş: `k!çekiliş`" +
                              "\n📈 Rank: `k!rank` (görsel!)\n💎 Pro: `k!pro`")
            v = View(); v.add_item(Button(label="Destek Sunucusu", url=SUPPORT_URL,
                                          style=discord.ButtonStyle.link, emoji="🔗"))
            await ch.send(embed=em, view=v)

async def finalize_giveaway(bot, message_id):
    gw = db.one("SELECT * FROM giveaways WHERE message_id=?", (message_id,))
    if not gw or gw["status"] != "active": return
    parts = json.loads(gw["participants"])
    db.q("UPDATE giveaways SET status='ended' WHERE message_id=?", (message_id,))
    ch = bot.get_channel(gw["channel_id"])
    if not parts:
        if ch:
            try: await ch.send(embed=E("🎊 ÇEKİLİŞ SONA ERDİ", "**" + gw["prize"] + "**\n😔 Katılımcı yok!", C_WARN))
            except Exception: pass
        return
    n = min(gw["winners"], len(parts))
    winners = [bot.get_user(int(w)) for w in random.sample(parts, n)]
    mentions = "\n".join(w.mention if w else "?" for w in winners)
    if ch:
        try:
            await ch.send(embed=E("🎊 ÇEKİLİŞ SONA ERDİ!",
                "### 🎁 Ödül: **" + gw["prize"] + "**\n🏆 **KAZANANLAR:**\n" + mentions + "\n" + SEP +
                "\n👥 Toplam katılımcı: `" + str(len(parts)) + "`\n🎉 Tebrikler!", C_PRO))
            msg = await ch.fetch_message(message_id)
            done = gw_embed(gw, bot)
            done.set_author(name="🎊 ÇEKİLİŞ SONA ERDİ")
            done.color = C_PRO
            done.add_field(name="🏆 Kazananlar", value=mentions, inline=False)
            await msg.edit(embed=done, view=bot.gw_view)
        except Exception: pass

bot = KatreBot()

# ═══════════════════════════════════════════════════════════════════════════
# 🌐 GENEL & SİSTEM
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
    bar = "🟢" if ms < 100 else ("🟡" if ms < 200 else "🔴")
    await safe_reply(ctx, E("🏓 PONG!", bar + " Gecikme: **" + str(ms) + "ms**", C_OK))

@kategori("genel")
@bot.command(name="istatistik", aliases=["stats", "botbilgi"], help="Bot istatistiklerini gösterir")
async def istatistik(ctx):
    up = datetime.datetime.now() - bot.start_time
    total = db.one("SELECT SUM(uses) u FROM cmd_stats")["u"] or 0
    em = E(None, None, C_MAIN)
    em.set_author(name="📊 KATRE BOT İSTATİSTİK", icon_url=bot.user.display_avatar.url)
    LINE(em, "🌐 Sunucu", "`" + str(len(bot.guilds)) + "`", True)
    LINE(em, "👥 Kullanıcı", "`" + str(sum(g.member_count or 0 for g in bot.guilds)) + "`", True)
    LINE(em, "🧩 Komut", "`" + str(len(bot.commands)) + "`", True)
    LINE(em, "⏱️ Uptime", "`" + str(up).split(".")[0] + "`", True)
    LINE(em, "📡 Ping", "`" + str(round(bot.latency * 1000)) + "ms`", True)
    LINE(em, "⌨️ Toplam Komut", "`" + str(total) + "`", True)
    LINE(em, "👑 Owner", "<@" + str(OWNER_ID) + ">")
    LINE(em, "🐍 Altyapı", "`discord.py 2.x • SQLite • Pillow • Tek Dosya`")
    await safe_reply(ctx, em)

@kategori("genel")
@bot.command(name="davet", aliases=["invite", "ekle"], help="Bot davet linki")
async def davet(ctx):
    url = discord.utils.oauth_url(str(bot.user.id), permissions=discord.Permissions(administrator=True))
    em = E(None, None, C_MAIN)
    em.set_author(name="➕ KATRE BOT'U EKLE", icon_url=bot.user.display_avatar.url)
    em.description = "Butona tıkla, tüm sistemler tek botta! 🚀\n" + SEP
    v = View()
    v.add_item(Button(label="Botu Ekle", url=url, style=discord.ButtonStyle.link, emoji="➕"))
    v.add_item(Button(label="Destek Sunucusu", url=SUPPORT_URL, style=discord.ButtonStyle.link, emoji="🔗"))
    await safe_reply(ctx, em, v)

@kategori("genel")
@bot.command(name="avatar", aliases=["av", "pp"], help="Kullanıcı avatarını gösterir")
async def avatar(ctx, user: discord.Member = None):
    user = user or ctx.author
    em = E("🖼️ " + user.display_name + " — AVATAR", color=C_MAIN, img=user.display_avatar.url)
    v = View(); v.add_item(Button(label="Tarayıcıda Aç", url=user.display_avatar.url,
                                  style=discord.ButtonStyle.link, emoji="🔗"))
    await safe_reply(ctx, em, v)

@kategori("genel")
@bot.command(name="sunucubilgi", aliases=["serverinfo"], help="Sunucu bilgileri")
async def sunucubilgi(ctx):
    g = ctx.guild
    em = E(None, None, C_MAIN, thumb=g.icon.url if g.icon else None)
    em.set_author(name="🌐 " + g.name + " — SUNUCU BİLGİSİ")
    LINE(em, "👑 Kurucu", "<@" + str(g.owner_id) + ">", True)
    LINE(em, "🆔 ID", "`" + str(g.id) + "`", True)
    LINE(em, "📅 Kuruluş", "<t:" + str(int(g.created_at.timestamp())) + ":D>", True)
    LINE(em, "👥 Üye", "`" + str(g.member_count) + "`", True)
    LINE(em, "💬 Kanal", "`" + str(len(g.channels)) + "`", True)
    LINE(em, "🎭 Rol", "`" + str(len(g.roles)) + "`", True)
    LINE(em, "🎉 Boost", "`" + str(g.premium_subscription_count or 0) + "`", True)
    LINE(em, "😊 Emoji", "`" + str(len(g.emojis)) + "`", True)
    await safe_reply(ctx, em)

@kategori("genel")
@bot.command(name="kullanıcıbilgi", aliases=["userinfo", "kb"], help="Kullanıcı bilgileri")
async def kullanıcıbilgi(ctx, user: discord.Member = None):
    user = user or ctx.author
    u = db.one("SELECT * FROM users WHERE user_id=?", (user.id,)) or {}
    em = E(None, None, C_MAIN, thumb=user.display_avatar.url)
    em.set_author(name="👤 " + user.display_name + " — BİLGİ", icon_url=user.display_avatar.url)
    LINE(em, "🆔 ID", "`" + str(user.id) + "`", True)
    LINE(em, "📅 Hesap", "<t:" + str(int(user.created_at.timestamp())) + ":R>", True)
    kat = "<t:" + str(int(user.joined_at.timestamp())) + ":R>" if user.joined_at else "—"
    LINE(em, "🎉 Katılım", kat, True)
    LINE(em, "📈 Seviye", "`" + str(u.get("level", 1)) + "`", True)
    LINE(em, "💰 Coin", "`" + str(u.get("coins", 0)) + "`", True)
    LINE(em, "💎 Pro", "✅" if u.get("pro") else "❌", True)
    if u.get("pro_tag"): LINE(em, "🏷️ Tag", "`" + u["pro_tag"] + "`", True)
    LINE(em, "🎭 Roller", ", ".join(r.mention for r in user.roles[1:][:8]) or "—")
    await safe_reply(ctx, em)

@kategori("genel")
@bot.command(name="rank", aliases=["seviye", "level", "xp"], help="Görsel seviye kartını gösterir")
@commands.cooldown(1, 3, commands.BucketType.user)
async def rank(ctx, user: discord.Member = None):
    user = user or ctx.author
    ensure_user(user.id, str(user))
    u = db.one("SELECT * FROM users WHERE user_id=?", (user.id,))
    need = u["level"] * 100
    pct = min(100, u["xp"] / need * 100)
    accent = hex_to_rgb(u["pro_color"]) if (u["pro"] and u["pro_color"]) else ((255, 215, 0) if u["pro"] else (0, 168, 255))
    color = int(u["pro_color"], 16) if (u["pro"] and u["pro_color"]) else (C_PRO if u["pro"] else C_MAIN)
    if HAS_PIL:
        avatar_bytes = None
        try: avatar_bytes = await user.display_avatar.with_size(256).read()
        except Exception: pass
        img = make_rank_card(user.display_name, u["level"], u["xp"], need, u["coins"],
                             u["rep"], bool(u["pro"]), u["pro_tag"], accent, avatar_bytes)
        buf = io.BytesIO(); img.save(buf, format="PNG"); buf.seek(0)
        file = discord.File(buf, filename="rank.png")
        em = E(None, None, color)
        em.set_image(url="attachment://rank.png")
        await ctx.send(file=file, embed=em)
    else:
        em = E(None, None, color, thumb=user.display_avatar.url)
        em.set_author(name="📈 " + user.display_name + " — RANK KARTI", icon_url=user.display_avatar.url)
        badges = []
        if u["pro"]: badges.append("💎 PRO")
        if u["pro_tag"]: badges.append("🏷️ " + u["pro_tag"])
        if u["xp2"]: badges.append("⚡ 2x XP")
        if badges: em.description = "### " + " • ".join(badges)
        LINE(em, "🏆 Seviye", "`" + str(u["level"]) + "`", True)
        LINE(em, "✨ XP", "`" + str(u["xp"]) + "/" + str(need) + "`", True)
        LINE(em, "💰 Coin", "`" + str(u["coins"]) + "`", True)
        LINE(em, "📊 İlerleme", progress_bar(pct))
        await safe_reply(ctx, em)

@kategori("genel")
@bot.command(name="sıralama", aliases=["sirala", "top", "lb", "leaderboard"], help="Görsel sunucu sıralaması")
async def sıralama(ctx):
    rows = db.all("SELECT * FROM users ORDER BY level DESC, xp DESC LIMIT 10")
    if not rows: return await safe_reply(ctx, E("📊", "Henüz veri yok!", C_WARN))
    if HAS_PIL:
        entries = []
        for r in rows:
            mem = bot.get_user(r["user_id"])
            nm = mem.display_name if mem else (r["name"] or str(r["user_id"]))
            entries.append((nm, r["level"], r["xp"], bool(r["pro"])))
        img = make_leaderboard(entries)
        buf = io.BytesIO(); img.save(buf, format="PNG"); buf.seek(0)
        file = discord.File(buf, filename="top10.png")
        em = E(None, None, C_PRO)
        em.set_image(url="attachment://top10.png")
        await ctx.send(file=file, embed=em)
    else:
        em = E(None, None, C_PRO)
        em.set_author(name="🏆 " + ctx.guild.name + " — SIRALAMA")
        txt = ""
        for i, r in enumerate(rows):
            head = MEDALS[i] if i < 3 else "**" + str(i + 1) + ".**"
            pro = " 💎" if r["pro"] else ""
            txt += head + " <@" + str(r["user_id"]) + ">" + pro + " — **Lv." + str(r["level"]) + "** • `" + str(r["xp"]) + " XP`\n"
        em.description = txt
        await safe_reply(ctx, em)

@kategori("genel")
@bot.command(name="rep", aliases=["itibar"], help="<@üye> — İtibar ver (12s)")
@commands.cooldown(1, 43200, commands.BucketType.user)
async def rep(ctx, user: discord.Member):
    if user.id == ctx.author.id:
        return await safe_reply(ctx, E("❌", "Kendine itibar veremezsin!", C_ERROR))
    ensure_user(user.id, str(user))
    db.q("UPDATE users SET rep=rep+1 WHERE user_id=?", (user.id,))
    await safe_reply(ctx, E("⭐ İTİBAR VERİLDİ", ctx.author.mention + " → " + user.mention + " ⭐\n+1 itibar!", C_PRO))

@kategori("genel")
@bot.command(name="destek", aliases=["ticket"], help="Destek paneli gönderir (Yönetici)")
@commands.has_permissions(administrator=True)
async def destek(ctx):
    em = E(None, None, C_MAIN)
    em.set_author(name="🎫 KATRE DESTEK MERKEZİ", icon_url=bot.user.display_avatar.url)
    em.description = ("Sorun mu var? Önerin mi var?\n**Butona tıkla, formu doldur, ekibimiz yanında!** 💧\n" +
                      SEP + "\n⏱️ Ortalama yanıt: **< 1 saat**")
    await ctx.send(embed=em, view=TicketOpenView())
    try: await ctx.message.delete()
    except Exception: pass

@kategori("genel")
@bot.command(name="not", aliases=["note"], help="<metin> — Kendine not kaydet")
async def not_(ctx, *, metin):
    ensure_user(ctx.author.id, str(ctx.author))
    u = db.one("SELECT notes FROM users WHERE user_id=?", (ctx.author.id,))
    notes = json.loads(u["notes"]); notes.append({"t": metin, "d": datetime.datetime.now().isoformat()})
    db.q("UPDATE users SET notes=? WHERE user_id=?", (json.dumps(notes), ctx.author.id))
    await safe_reply(ctx, E("📝 NOT KAYDEDİLDİ", "```\n" + metin[:500] + "\n```\nToplam not: `" + str(len(notes)) + "`", C_OK))

@kategori("genel")
@bot.command(name="notlar", aliases=["notes"], help="Kayıtlı notlarını listeler")
async def notlar(ctx):
    u = db.one("SELECT notes FROM users WHERE user_id=?", (ctx.author.id,))
    notes = json.loads(u["notes"]) if u else []
    if not notes: return await safe_reply(ctx, E("📝", "Henüz notun yok! `k!not <metin>`", C_WARN))
    em = E("📝 NOTLARIN (" + str(len(notes)) + ")", color=C_MAIN)
    for i, n in enumerate(notes[-8:], 1):
        LINE(em, "`" + str(i) + ".` " + datetime.datetime.fromisoformat(n["d"]).strftime("%d.%m.%Y"),
             "└ " + n["t"][:80])
    await safe_reply(ctx, em)

@kategori("genel")
@bot.command(name="doğumgünü", aliases=["dogumgunu", "birthday"], help="<gün> <ay> — Doğum günü ayarla")
async def doğumgünü(ctx, gün: int, ay: int):
    if not (1 <= gün <= 31 and 1 <= ay <= 12):
        return await safe_reply(ctx, E("❌", "Geçersiz tarih! Örnek: `k!doğumgünü 24 8`", C_ERROR))
    db.q("UPDATE users SET birthday=? WHERE user_id=?", (str(gün) + "." + str(ay), ctx.author.id))
    await safe_reply(ctx, E("🎂 DOĞUM GÜNÜ KAYDEDİLDİ", "Doğum günün: **" + str(gün) + "." + str(ay) + "** 🎈", C_PRO))

@kategori("genel")
@bot.command(name="doğumgünleri", aliases=["dogumgunleri"], help="Bu ayın doğum günleri")
async def doğumgünleri(ctx):
    now = datetime.datetime.now()
    rows = [r for r in db.all("SELECT user_id,birthday FROM users WHERE birthday IS NOT NULL")
            if r["birthday"] and int(r["birthday"].split(".")[1]) == now.month]
    if not rows: return await safe_reply(ctx, E("🎂", "Bu ay doğum günü yok!", C_WARN))
    em = E("🎂 " + str(now.month) + ". AY DOĞUM GÜNLERİ", color=C_PRO)
    for r in sorted(rows, key=lambda x: int(x["birthday"].split(".")[0])):
        LINE(em, "🎈 " + r["birthday"], "<@" + str(r["user_id"]) + ">")
    await safe_reply(ctx, em)

@kategori("genel")
@bot.command(name="hatırlat", aliases=["hatirlat"], help="<dakika> <metin> — Hatırlatıcı")
async def hatırlat(ctx, dk: int, *, metin):
    if dk < 1 or dk > 1440: return await safe_reply(ctx, E("❌", "1-1440 dakika arası gir!", C_ERROR))
    await safe_reply(ctx, E("⏰ HATIRLATICI KURULDU", "**" + str(dk) + " dakika** sonra: " + metin, C_OK))
    await asyncio.sleep(dk * 60)
    await ctx.send(ctx.author.mention + " ⏰ **HATIRLATMA:** " + metin)

@kategori("genel")
@bot.command(name="botkontrol", aliases=["check"], help="Botun kanaldaki yetkilerini kontrol eder")
@commands.has_permissions(administrator=True)
async def botkontrol(ctx):
    p = ctx.channel.permissions_for(ctx.guild.me)
    checks = [
        ("Mesajları Gör", p.view_channel), ("Mesaj Gönder", p.send_messages),
        ("Embed Gönder", p.embed_links), ("Tepki Ekle", p.add_reactions),
        ("Mesaj Yönet", p.manage_messages), ("Üyeleri Zaman Aşımına Al", p.moderate_members),
        ("Rol Yönet", p.manage_roles), ("Kanal Yönet", p.manage_channels),
        ("Üye At", p.kick_members), ("Üye Yasakla", p.ban_members),
    ]
    em = E(None, None, C_MAIN)
    em.set_author(name="🩺 BOT KONTROL — #" + ctx.channel.name, icon_url=bot.user.display_avatar.url)
    em.description = "\n".join(("✅ " if ok else "❌ ") + n for n, ok in checks)
    missing = [n for n, ok in checks if not ok]
    LINE(em, "🔧 Sonuç", "Eksik yetki yok! Bot bu kanalda tam çalışır." if not missing
         else "⚠️ Eksik: **" + ", ".join(missing) + "** → Bu yüzden bazen susuyorum!")
    await safe_reply(ctx, em)

# ═══════════════════════════════════════════════════════════════════════════
# 🛡️ MODERASYON + KORUMA
# ═══════════════════════════════════════════════════════════════════════════
@kategori("mod")
@bot.command(name="yasakla", aliases=["ban"], help="<@üye> [sebep] — Üyeyi yasaklar")
@commands.has_permissions(ban_members=True)
@commands.bot_has_permissions(ban_members=True)
async def yasakla(ctx, user: discord.Member, *, sebep="Belirtilmedi"):
    v = ConfirmView()
    await ctx.send(embed=E("⚠️ ONAY GEREKLİ",
        "**" + str(user) + "** üyesini yasaklamak üzeresin!\n**Sebep:** " + sebep + "\n\nOnaylıyor musun?", C_WARN), view=v)
    await v.wait()
    if v.value is None:
        return await safe_reply(ctx, E("⌛ ZAMAN AŞIMI", "Onay beklenmedi, işlem iptal.", C_WARN))
    if v.value:
        try: await user.send(embed=E("🔨 YASAKLANDIN", "**" + ctx.guild.name + "**\n**Sebep:** " + sebep, C_ERROR))
        except Exception: pass
        await user.ban(reason=str(ctx.author) + " | " + sebep)
        await safe_reply(ctx, E("🔨 YASAKLAMA", user.mention + " yasaklandı!\n**Sebep:** `" + sebep + "`", C_MOD))

@kategori("mod")
@bot.command(name="at", aliases=["kick"], help="<@üye> [sebep] — Üyeyi atar")
@commands.has_permissions(kick_members=True)
@commands.bot_has_permissions(kick_members=True)
async def at(ctx, user: discord.Member, *, sebep="Belirtilmedi"):
    v = ConfirmView()
    await ctx.send(embed=E("⚠️ ONAY GEREKLİ", "**" + str(user) + "** üyesini atmak üzeresin!\n**Sebep:** " + sebep, C_WARN), view=v)
    await v.wait()
    if v.value is None:
        return await safe_reply(ctx, E("⌛ ZAMAN AŞIMI", "İşlem iptal.", C_WARN))
    if v.value:
        await user.kick(reason=str(ctx.author) + " | " + sebep)
        await safe_reply(ctx, E("👢 ATMA", user.mention + " atıldı!\n**Sebep:** `" + sebep + "`", C_MOD))

@kategori("mod")
@bot.command(name="uyar", aliases=["warn"], help="<@üye> [sebep] — Üyeyi uyarır")
@commands.has_permissions(manage_messages=True)
async def uyar(ctx, user: discord.Member, *, sebep="Belirtilmedi"):
    ensure_user(user.id, str(user))
    db.q("UPDATE users SET warnings=warnings+1 WHERE user_id=?", (user.id,))
    w = db.one("SELECT warnings FROM users WHERE user_id=?", (user.id,))["warnings"]
    await safe_reply(ctx, E("⚠️ UYARI", user.mention + " uyarıldı!\n**Sebep:** `" + sebep + "`\n**Toplam:** `" + str(w) + "`", C_WARN))
    try: await user.send(embed=E("⚠️ UYARILDIN", "**" + ctx.guild.name + "**\n**Sebep:** " + sebep, C_WARN))
    except Exception: pass

@kategori("mod")
@bot.command(name="uyarılar", aliases=["warns"], help="[<@üye>] — Uyarıları listeler")
async def uyarılar(ctx, user: discord.Member = None):
    user = user or ctx.author
    ensure_user(user.id, str(user))
    w = db.one("SELECT warnings FROM users WHERE user_id=?", (user.id,))["warnings"]
    await safe_reply(ctx, E("⚠️ UYARILAR", user.mention + " üyesinin **" + str(w) + "** uyarısı var.", C_WARN))

@kategori("mod")
@bot.command(name="temizle", aliases=["purge", "sil"], help="<adet> — Mesajları siler")
@commands.has_permissions(manage_messages=True)
@commands.bot_has_permissions(manage_messages=True)
async def temizle(ctx, adet: int):
    if not 1 <= adet <= 500: return await safe_reply(ctx, E("❌", "1-500 arası sayı gir!", C_ERROR))
    await ctx.channel.purge(limit=adet + 1)
    m = await ctx.send(embed=E("🧹 TEMİZLENDİ", "**" + str(adet) + "** mesaj silindi!", C_OK))
    await m.delete(delay=5)

@kategori("mod")
@bot.command(name="yavaşmod", aliases=["slowmode"], help="<saniye> — Yavaş mod")
@commands.has_permissions(manage_channels=True)
async def yavaşmod(ctx, sn: int):
    await ctx.channel.edit(slowmode_delay=sn)
    msg = "Kanal yavaş modu: **" + str(sn) + " saniye**" if sn else "**Kapatıldı**"
    await safe_reply(ctx, E("🐌 YAVAŞ MOD", msg, C_OK))

@kategori("mod")
@bot.command(name="kilit", aliases=["lock"], help="Kanalı kilitler")
@commands.has_permissions(manage_channels=True)
async def kilit(ctx):
    await ctx.channel.set_permissions(ctx.guild.default_role, send_messages=False)
    await safe_reply(ctx, E("🔒 KANAL KİLİTLENDİ", ctx.channel.mention + " artık yazmaya kapalı.", C_MOD))

@kategori("mod")
@bot.command(name="kilitaç", aliases=["unlock"], help="Kanal kilidini açar")
@commands.has_permissions(manage_channels=True)
async def kilitaç(ctx):
    await ctx.channel.set_permissions(ctx.guild.default_role, send_messages=None)
    await safe_reply(ctx, E("🔓 KİLİT AÇILDI", ctx.channel.mention + " yazmaya açık.", C_OK))

@kategori("mod")
@bot.command(name="otorol", aliases=["autorol"], help="<@rol|kapat> — Otorol ayarlar")
@commands.has_permissions(administrator=True)
async def otorol(ctx, *, arg):
    if arg.lower() in ("kapat", "off", "0"):
        db.q("UPDATE servers SET auto_role=NULL WHERE guild_id=?", (ctx.guild.id,))
        return await safe_reply(ctx, E("✅ OTOROL", "Otorol **kapatıldı**.", C_OK))
    role = await commands.RoleConverter().convert(ctx, arg)
    db.q("UPDATE servers SET auto_role=? WHERE guild_id=?", (role.id, ctx.guild.id))
    await safe_reply(ctx, E("✅ OTOROL", "Yeni üyelere " + role.mention + " rolü verilecek.", C_OK))

@kategori("mod")
@bot.command(name="hoşgeldin", aliases=["hosgeldin", "welcome"], help="<#kanal|kapat> — Hoşgeldin kanalı")
@commands.has_permissions(administrator=True)
async def hoşgeldin(ctx, ch: discord.TextChannel = None):
    if ch is None:
        db.q("UPDATE servers SET welcome_ch=NULL WHERE guild_id=?", (ctx.guild.id,))
        return await safe_reply(ctx, E("✅ HOŞGELDİN", "Hoşgeldin sistemi **kapatıldı**.", C_OK))
    db.q("UPDATE servers SET welcome_ch=? WHERE guild_id=?", (ch.id, ctx.guild.id))
    await safe_reply(ctx, E("✅ HOŞGELDİN", "Yeni üyeler " + ch.mention + " kanalında karşılanacak! 👋", C_OK))

@kategori("mod")
@bot.command(name="butonrol", aliases=["rolmenü"], help="<@rol...> — Rol buton menüsü oluşturur")
@commands.has_permissions(administrator=True)
async def butonrol(ctx, roles: commands.Greedy[discord.Role], *, açıklama="Rollerinizi butonlarla alın!"):
    if not roles or len(roles) > 25: return await safe_reply(ctx, E("❌", "1-25 arası rol etiketle!", C_ERROR))
    menu_id = str(random.randint(10**11, 10**12 - 1))
    db.q("INSERT OR REPLACE INTO role_menus(menu_id,guild_id,role_ids) VALUES(?,?,?)",
         (menu_id, ctx.guild.id, json.dumps([r.id for r in roles])))
    em = E(None, None, C_MAIN)
    em.set_author(name="🎭 ROL SEÇİM MENÜSÜ", icon_url=ctx.guild.icon.url if ctx.guild.icon else None)
    em.description = açıklama + "\n" + SEP + "\n" + "\n".join("🔹 " + r.mention for r in roles)
    view = RoleMenuView(menu_id, [(r.id, r.name) for r in roles])
    bot.add_view(view)
    await ctx.send(embed=em, view=view)

# ─────────────── 🛡️ KORUMA KOMUTLARI ───────────────
@kategori("mod")
@bot.command(name="koruma", help="<mod> <aç/kapat> — Koruma modülleri (Yönetici)")
@commands.has_permissions(administrator=True)
async def koruma(ctx, mod: str, durum: str):
    mod = mod.lower().replace("-", "").replace("_", "")
    col = {"antispam": "anti_spam", "antiflood": "anti_flood", "antiraid": "anti_raid",
           "antilink": "anti_link", "badword": "badword", "küfür": "badword"}.get(mod)
    if not col:
        return await safe_reply(ctx, E("❌ GEÇERSİZ MODÜL",
            "Kullanılabilir: `antispam` `antiflood` `antiraid` `antilink` `badword`\n"
            "Örnek: `k!koruma antispam aç`", C_ERROR))
    db.q("INSERT OR IGNORE INTO protections(guild_id) VALUES(?)", (ctx.guild.id,))
    val = 1 if durum.lower() in ("aç", "ac", "on", "1") else 0
    db.q("UPDATE protections SET " + col + "=? WHERE guild_id=?", (val, ctx.guild.id))
    await safe_reply(ctx, E("🛡️ KORUMA SİSTEMİ",
        "**" + mod.upper() + "** modülü " + ("**AÇILDI** ✅" if val else "**KAPATILDI** ❌") +
        "\n📜 Log için: `k!korumalog #kanal`", C_OK))

@kategori("mod")
@bot.command(name="korumadurum", aliases=["korumalar"], help="Koruma modüllerinin durumunu gösterir")
async def korumadurum(ctx):
    p = db.one("SELECT * FROM protections WHERE guild_id=?", (ctx.guild.id,)) or {}
    def st(v): return "✅ Açık" if v else "❌ Kapalı"
    em = E(None, None, C_MOD)
    em.set_author(name="🛡️ KORUMA DURUMU — " + ctx.guild.name, icon_url=ctx.guild.icon.url if ctx.guild.icon else None)
    LINE(em, "🚫 Anti-Spam", st(p.get("anti_spam")), True)
    LINE(em, "🌊 Anti-Flood", st(p.get("anti_flood")), True)
    LINE(em, "⚔️ Anti-Raid", st(p.get("anti_raid")), True)
    LINE(em, "🔗 Anti-Link", st(p.get("anti_link")), True)
    LINE(em, "🤬 Küfür Filtresi", st(p.get("badword")), True)
    LINE(em, "📜 Log Kanalı", ("<#" + str(p["log_ch"]) + ">") if p.get("log_ch") else "Ayarlı değil", True)
    await safe_reply(ctx, em)

@kategori("mod")
@bot.command(name="korumalog", help="<#kanal> — Koruma log kanalı ayarlar")
@commands.has_permissions(administrator=True)
async def korumalog(ctx, ch: discord.TextChannel):
    db.q("INSERT OR IGNORE INTO protections(guild_id) VALUES(?)", (ctx.guild.id,))
    db.q("UPDATE protections SET log_ch=? WHERE guild_id=?", (ch.id, ctx.guild.id))
    await safe_reply(ctx, E("📜 KORUMA LOG", "Tüm koruma olayları " + ch.mention + " kanalına düşecek.", C_OK))

@kategori("mod")
@bot.command(name="badword", aliases=["küfürfiltre"], help="<ekle/sil/liste> [kelime] — Küfür filtresi")
@commands.has_permissions(administrator=True)
async def badword(ctx, işlem: str, *, kelime: str = None):
    gid = ctx.guild.id
    if işlem.lower() in ("ekle", "add"):
        if not kelime: return await safe_reply(ctx, E("❌", "Kelime gir! Örnek: `k!badword ekle aptal`", C_ERROR))
        db.q("INSERT OR IGNORE INTO badwords(guild_id, word) VALUES(?,?)", (gid, kelime.lower()))
        await safe_reply(ctx, E("🤬 FİLTREYE EKLENDİ", "`" + kelime.lower() + "` artık yasaklı.", C_OK))
    elif işlem.lower() in ("sil", "remove"):
        db.q("DELETE FROM badwords WHERE guild_id=? AND word=?", (gid, (kelime or "").lower()))
        await safe_reply(ctx, E("🤬 FİLTREDEN SİLİNDİ", "`" + str(kelime) + "` artık serbest.", C_OK))
    elif işlem.lower() in ("liste", "list"):
        ws = [w["word"] for w in db.all("SELECT word FROM badwords WHERE guild_id=?", (gid,))]
        await safe_reply(ctx, E("🤬 YASAKLI KELİMELER (" + str(len(ws)) + ")",
                                ("`" + "`, `".join(ws) + "`") if ws else "Liste boş.", C_WARN))
    else:
        await safe_reply(ctx, E("❌", "`k!badword ekle/sil/liste [kelime]`", C_ERROR))

@kategori("mod")
@bot.command(name="raidmodu", help="<aç/kapat> — Raid modunu manuel yönetir")
@commands.has_permissions(administrator=True)
async def raidmodu(ctx, mod: str):
    now = datetime.datetime.now().timestamp()
    db.q("INSERT OR IGNORE INTO protections(guild_id) VALUES(?)", (ctx.guild.id,))
    if mod.lower() in ("aç", "ac", "on"):
        db.q("UPDATE protections SET raid_until=? WHERE guild_id=?", (now + 600, ctx.guild.id))
        await safe_reply(ctx, E("⚔️ RAID MODU", "**10 dakika** boyunca yeni girişler otomatik engellenecek!", C_ERROR))
    else:
        db.q("UPDATE protections SET raid_until=0 WHERE guild_id=?", (ctx.guild.id,))
        await safe_reply(ctx, E("⚔️ RAID MODU", "Raid modu **kapatıldı**.", C_OK))

@kategori("mod")
@bot.command(name="kurulum", aliases=["sunucukur", "setup"], help="Sunucuyu tek komutla kurar (Yönetici)")
@commands.has_permissions(administrator=True)
@commands.bot_has_permissions(manage_channels=True, manage_roles=True)
async def kurulum(ctx):
    v = SetupConfirmView()
    await ctx.send(embed=E("🏗️ SUNUCU KURULUM",
        "Bu komut sunucunda şunları oluşturur:\n" + SEP +
        "\n📁 4 kategori • 8 yazı kanalı • 3 ses kanalı" +
        "\n🎭 4 rol (Yönetici / Moderatör / Üye / Bot)" +
        "\n👋 Hoşgeldin kanalı + otomatik sistem" +
        "\n🔒 Yetkili kategorisi (gizli)" +
        "\n\n**Onaylıyor musun?**", C_MAIN), view=v)
    await v.wait()
    if not v.value:
        return
    g = ctx.guild
    ck = 0
    try:
        r_yon = await g.create_role(name="Yönetici", color=discord.Color(0xE74C3C),
                                    permissions=discord.Permissions(administrator=True))
        r_mod = await g.create_role(name="Moderatör", color=discord.Color(0x3498DB),
                                    permissions=discord.Permissions(kick_members=True, manage_messages=True,
                                                                   moderate_members=True))
        r_uye = await g.create_role(name="Üye", color=discord.Color(0x2ECC71))
        r_bot = await g.create_role(name="Bot", color=discord.Color(0xFFD700), hoist=True)
        try: await g.me.add_roles(r_bot)
        except Exception: pass
        k_bilgi = await g.create_category("📢 BİLGİ")
        k_sohbet = await g.create_category("💬 SOHBET")
        k_ses = await g.create_category("🎧 SES")
        k_yonet = await g.create_category("🛡️ YÖNETİM")
        ow_bilgi = {g.default_role: discord.PermissionOverwrite(view_channel=True, send_messages=False)}
        for name in ("duyurular", "kurallar", "etkinlik"):
            await g.create_text_channel(name, category=k_bilgi, overwrites=ow_bilgi); ck += 1
        hg = await g.create_text_channel("hoşgeldin", category=k_bilgi, overwrites=ow_bilgi); ck += 1
        for name in ("genel", "sohbet", "medya", "bot-komut"):
            await g.create_text_channel(name, category=k_sohbet); ck += 1
        for name in ("Sohbet 1", "Sohbet 2", "Müzik"):
            await g.create_voice_channel(name, category=k_ses); ck += 1
        ow_yonet = {g.default_role: discord.PermissionOverwrite(view_channel=False),
                    r_yon: discord.PermissionOverwrite(view_channel=True),
                    r_mod: discord.PermissionOverwrite(view_channel=True)}
        await g.create_text_channel("yetkili-sohbet", category=k_yonet, overwrites=ow_yonet); ck += 1
        db.q("UPDATE servers SET welcome_ch=? WHERE guild_id=?", (hg.id, g.id))
        await safe_reply(ctx, E("✅ KURULUM TAMAMLANDI!",
            "📁 Kategori: **4**\n💬 Kanal: **" + str(ck) + "**\n🎭 Rol: **4**" +
            "\n👋 Hoşgeldin kanalı: " + hg.mention +
            "\n\n🎉 Sunucun hazır! Önerilen: `k!koruma antispam aç` + `k!korumalog #kanal`", C_OK))
    except discord.Forbidden:
        await safe_reply(ctx, E("❌ YETKİ YOK", "Kurulum için bot'a **Kanal Yönet + Rol Yönet** yetkisi gerekli.", C_ERROR))
    except Exception as e:
        await safe_reply(ctx, E("⚠️ KURULUM HATASI", "```\n" + str(e)[:500] + "\n```", C_ERROR))

# ═══════════════════════════════════════════════════════════════════════════
# 💰 EKONOMİ
# ═══════════════════════════════════════════════════════════════════════════
@kategori("eco")
@bot.command(name="cüzdan", aliases=["balance", "para"], help="[<@üye>] — Coin bakiyesi")
async def cüzdan(ctx, user: discord.Member = None):
    user = user or ctx.author
    ensure_user(user.id, str(user))
    u = db.one("SELECT * FROM users WHERE user_id=?", (user.id,))
    em = E(None, None, C_ECO, thumb=user.display_avatar.url)
    em.set_author(name="💰 " + user.display_name + " — CÜZDAN", icon_url=user.display_avatar.url)
    LINE(em, "🪙 Coin", "`" + format(u["coins"], ",").replace(",", ".") + "`", True)
    LINE(em, "⭐ İtibar", "`" + str(u["rep"]) + "`", True)
    LINE(em, "💎 Pro", "✅" if u["pro"] else "❌", True)
    await safe_reply(ctx, em)

@kategori("eco")
@bot.command(name="günlük", aliases=["gunluk", "daily"], help="Günlük coin ödülü")
@commands.cooldown(1, 86400, commands.BucketType.user)
async def günlük(ctx):
    ensure_user(ctx.author.id, str(ctx.author))
    u = db.one("SELECT * FROM users WHERE user_id=?", (ctx.author.id,))
    bonus = random.randint(150, 400) + (250 if u["pro"] else 0)
    db.q("UPDATE users SET coins=coins+? WHERE user_id=?", (bonus, ctx.author.id))
    extra = "\n💎 **Pro bonusu:** +250" if u["pro"] else ""
    await safe_reply(ctx, E("🎁 GÜNLÜK ÖDÜL", "**+" + str(bonus) + " coin** kazandın! 🪙" + extra, C_ECO))

@kategori("eco")
@bot.command(name="çalış", aliases=["calis", "work"], help="Çalışıp coin kazanırsın")
@commands.cooldown(1, 1800, commands.BucketType.user)
async def çalış(ctx):
    jobs = [("💻 Yazılım geliştirdin", 200, 400), ("🎨 Tasarım yaptın", 150, 300),
            ("📹 İçerik ürettin", 180, 350), ("🍕 Pizzacılık yaptın", 100, 220),
            ("🚕 Şoförlük yaptın", 120, 260), ("📚 Ders verdin", 160, 320)]
    job, a, b = random.choice(jobs)
    pay = random.randint(a, b)
    db.q("UPDATE users SET coins=coins+? WHERE user_id=?", (pay, ctx.author.id))
    await safe_reply(ctx, E("💼 ÇALIŞTIN!", job + "\n**+" + str(pay) + " coin** kazandın! 🪙", C_ECO))

@kategori("eco")
@bot.command(name="soy", aliases=["rob"], help="<@üye> — Üyeyi soymayı dener")
@commands.cooldown(1, 600, commands.BucketType.user)
async def soy(ctx, user: discord.Member):
    if user.id == ctx.author.id or user.bot:
        return await safe_reply(ctx, E("❌", "Geçersiz hedef!", C_ERROR))
    ensure_user(user.id, str(user))
    t = db.one("SELECT coins FROM users WHERE user_id=?", (user.id,))
    me = db.one("SELECT coins FROM users WHERE user_id=?", (ctx.author.id,))
    if t["coins"] < 200:
        return await safe_reply(ctx, E("❌", user.mention + " üyesinde çalınacak coin yok!", C_ERROR))
    if random.random() < 0.45:
        steal = random.randint(50, min(500, t["coins"]))
        db.q("UPDATE users SET coins=coins-? WHERE user_id=?", (steal, user.id))
        db.q("UPDATE users SET coins=coins+? WHERE user_id=?", (steal, ctx.author.id))
        await safe_reply(ctx, E("🦹 SOYGUN BAŞARILI!", user.mention + " üyesinden **" + str(steal) + " coin** çaldın! 💰", C_ECO))
    else:
        fine = min(me["coins"], random.randint(50, 200))
        db.q("UPDATE users SET coins=coins-? WHERE user_id=?", (fine, ctx.author.id))
        await safe_reply(ctx, E("🚨 YAKALANDIN!", "Soygun başarısız! **" + str(fine) + " coin** ceza! 👮", C_ERROR))

@kategori("eco")
@bot.command(name="transfer", aliases=["gönder"], help="<@üye> <miktar> — Coin gönderir")
async def transfer(ctx, user: discord.Member, miktar: int):
    if miktar <= 0 or user.id == ctx.author.id:
        return await safe_reply(ctx, E("❌", "Geçersiz işlem!", C_ERROR))
    ensure_user(user.id, str(user))
    me = db.one("SELECT coins FROM users WHERE user_id=?", (ctx.author.id,))
    if me["coins"] < miktar:
        return await safe_reply(ctx, E("❌ YETERSİZ BAKİYE", "Sadece **" + str(me["coins"]) + "** coinin var!", C_ERROR))
    db.q("UPDATE users SET coins=coins-? WHERE user_id=?", (miktar, ctx.author.id))
    db.q("UPDATE users SET coins=coins+? WHERE user_id=?", (miktar, user.id))
    await safe_reply(ctx, E("💸 TRANSFER", ctx.author.mention + " → " + user.mention + "\n**" + str(miktar) + " coin** gönderildi! ✅", C_ECO))

@kategori("eco")
@bot.command(name="bahis", aliases=["bet"], help="<miktar> — Yazı tura bahsi (x2)")
@commands.cooldown(1, 10, commands.BucketType.user)
async def bahis(ctx, miktar: int):
    if miktar <= 0: return await safe_reply(ctx, E("❌", "Geçersiz miktar!", C_ERROR))
    me = db.one("SELECT coins FROM users WHERE user_id=?", (ctx.author.id,))
    if me["coins"] < miktar:
        return await safe_reply(ctx, E("❌ YETERSİZ BAKİYE", "Sadece **" + str(me["coins"]) + "** coinin var!", C_ERROR))
    win = random.random() < 0.5
    db.q("UPDATE users SET coins=coins+? WHERE user_id=?", (miktar if win else -miktar, ctx.author.id))
    msg = "🎉 KAZANDIN! +" + str(miktar * 2) + " coin" if win else "😔 Kaybettin -" + str(miktar) + " coin"
    await safe_reply(ctx, E("🎰 BAHİS SONUCU", "**" + msg + "**", C_ECO if win else C_ERROR))

@kategori("eco")
@bot.command(name="market", aliases=["shop"], help="Market ürünlerini listeler")
async def market(ctx):
    em = E(None, None, C_ECO)
    em.set_author(name="🛒 KATRE MARKET", icon_url=bot.user.display_avatar.url)
    em.description = "💎 Ürünler coin ile satın alınır!\n" + SEP
    LINE(em, "💎 Pro Üyelik (30 gün)", "`50.000 coin` — k!destek")
    LINE(em, "🎨 Özel Rank Rengi", "`5.000 coin` — Pro gerekli")
    LINE(em, "⭐ +10 İtibar", "`2.500 coin` — k!destek")
    LINE(em, "🏷️ Özel Tag", "`7.500 coin` — Pro gerekli")
    v = View(); v.add_item(Button(label="Satın Al", url=SUPPORT_URL, style=discord.ButtonStyle.link, emoji="🛒"))
    await safe_reply(ctx, em, v)

# ═══════════════════════════════════════════════════════════════════════════
# 🎮 EĞLENCE
# ═══════════════════════════════════════════════════════════════════════════
@kategori("fun")
@bot.command(name="8ball", aliases=["ball"], help="<soru> — Sihirli top")
async def eightball(ctx, *, soru):
    cev = ["✅ Evet, kesinlikle!", "🌟 Büyük ihtimalle evet", "🤔 Belki", "❌ Hayır",
           "💀 Kesinlikle hayır!", "🎯 Şansın yüksek", "😴 Bana sorma", "🔥 Evet evet evet!"]
    await safe_reply(ctx, E("🎱 SORU: " + soru, "**Cevap:** " + random.choice(cev), C_FUN))

@kategori("fun")
@bot.command(name="yazıtura", aliases=["yazitura", "coin"], help="Yazı tura atar")
async def yazıtura(ctx):
    await safe_reply(ctx, E("🪙 YAZI TURA", "**" + random.choice(["📝 YAZI", "🪙 TURA"]) + "**", C_FUN))

@kategori("fun")
@bot.command(name="zar", aliases=["dice"], help="Zar atar (1-6)")
async def zar(ctx):
    r = random.randint(1, 6)
    await safe_reply(ctx, E("🎲 ZAR", DICE[r - 1] + " Sonuç: **" + str(r) + "**", C_FUN))

@kategori("fun")
@bot.command(name="aşk", aliases=["ask", "love"], help="<@üye> — Aşk ölçer")
async def aşk(ctx, user: discord.Member):
    pct = random.randint(0, 100)
    msg = "💔 Yok bu iş..." if pct < 30 else ("💛 Fena değil!" if pct < 60 else ("💚 Güzel çift!" if pct < 85 else "❤️ RUH İKİZİ!"))
    await safe_reply(ctx, E("💕 AŞK ÖLÇER",
        ctx.author.mention + " 💘 " + user.mention + "\n" + progress_bar(pct) + "\n" + msg, C_FUN))

@kategori("fun")
@bot.command(name="slot", aliases=["slots"], help="Slot makinesi çevirir")
async def slot(ctx):
    r = [random.choice(SLOTS) for _ in range(3)]
    win = len(set(r)) == 1
    msg = "🎉 JACKPOT! Üçlü eşleşme!" if win else "😔 Bu sefer olmadı..."
    await safe_reply(ctx, E("🎰 SLOT MAKİNESİ", "┃ " + " ┃ ".join(r) + " ┃\n\n" + msg, C_PRO if win else C_FUN))

@kategori("fun")
@bot.command(name="seç", aliases=["sec"], help="<a> <b> ... — Rastgele seçim")
async def seç(ctx, *, seçenekler):
    opts = seçenekler.split()
    if len(opts) < 2: return await safe_reply(ctx, E("❌", "En az 2 seçenek gir!", C_ERROR))
    await safe_reply(ctx, E("🎯 RASTGELE SEÇİM", "Seçimim: **" + random.choice(opts) + "**", C_FUN))

# ═══════════════════════════════════════════════════════════════════════════
# 🎉 ÇEKİLİŞ
# ═══════════════════════════════════════════════════════════════════════════
@kategori("give")
@bot.command(name="çekiliş", aliases=["cekilis", "giveaway"],
             help="<süre> <kazanan> <ödül> — Çekiliş başlatır (Yönetici)")
@commands.has_permissions(administrator=True)
async def çekiliş(ctx, süre: str, kazanan: int, *, ödül):
    try: dk = parse_sure(süre)
    except Exception:
        return await safe_reply(ctx, E("❌ SÜRE HATASI", "Örnek: `k!çekiliş 60m 1 Nitro` • `2h` • `1d`", C_ERROR))
    if dk < 1 or kazanan < 1: return await safe_reply(ctx, E("❌", "Geçersiz değerler!", C_ERROR))
    end = datetime.datetime.now() + datetime.timedelta(minutes=dk)
    em = gw_embed({"prize": ödül, "winners": kazanan, "end_time": end.timestamp(),
                   "host": ctx.author.id, "message_id": 0, "participants": "[]"}, bot)
    msg = await ctx.send(embed=em, view=bot.gw_view)
    db.q("INSERT INTO giveaways(message_id,guild_id,channel_id,prize,winners,end_time,host) VALUES(?,?,?,?,?,?,?)",
         (msg.id, ctx.guild.id, ctx.channel.id, ödül, kazanan, end.timestamp(), ctx.author.id))
    try:
        await msg.edit(embed=gw_embed({"prize": ödül, "winners": kazanan, "end_time": end.timestamp(),
                                       "host": ctx.author.id, "message_id": msg.id, "participants": "[]"}, bot),
                       view=bot.gw_view)
    except Exception: pass

@kategori("give")
@bot.command(name="çekilişler", aliases=["cekilisler"], help="Aktif çekilişleri listeler")
async def çekilişler(ctx):
    rows = db.all("SELECT * FROM giveaways WHERE guild_id=? AND status='active'", (ctx.guild.id,))
    if not rows: return await safe_reply(ctx, E("🎉", "Aktif çekiliş yok. `k!çekiliş` ile başlat!", C_WARN))
    em = E(None, None, C_GIVE)
    em.set_author(name="🎉 AKTİF ÇEKİLİŞLER (" + str(len(rows)) + ")", icon_url=ctx.guild.icon.url if ctx.guild.icon else None)
    for g in rows:
        p = len(json.loads(g["participants"]))
        LINE(em, "🎁 " + g["prize"],
             "└ 👥 " + str(p) + " katılımcı • ⏰ <t:" + str(int(g["end_time"])) + ":R> • 🆔 `" + str(g["message_id"]) + "`")
    await safe_reply(ctx, em)

@kategori("give")
@bot.command(name="çekilişbitir", aliases=["cekilisbitir"], help="<mesaj_id> — Çekilişi bitirir")
@commands.has_permissions(administrator=True)
async def çekilişbitir(ctx, mid: int):
    gw = db.one("SELECT * FROM giveaways WHERE message_id=? AND guild_id=?", (mid, ctx.guild.id))
    if not gw or gw["status"] != "active":
        return await safe_reply(ctx, E("❌", "Aktif çekiliş bulunamadı!", C_ERROR))
    await finalize_giveaway(bot, mid)
    await safe_reply(ctx, E("🏁", "Çekiliş sonlandırıldı!", C_OK))

# ═══════════════════════════════════════════════════════════════════════════
# 💎 PRO SİSTEMİ
# ═══════════════════════════════════════════════════════════════════════════
@kategori("pro")
@bot.command(name="pro", aliases=["probilgi"], help="Pro durumunu ve ayrıcalıkları gösterir")
async def pro(ctx, user: discord.Member = None):
    user = user or ctx.author
    ensure_user(user.id, str(user))
    u = db.one("SELECT * FROM users WHERE user_id=?", (user.id,))
    em = E(None, None, C_PRO, thumb=user.display_avatar.url)
    em.set_author(name="💎 KATRE PRO", icon_url=bot.user.display_avatar.url)
    if u["pro"]:
        exp = datetime.datetime.fromisoformat(u["pro_expiry"]).strftime("%d.%m.%Y") if u["pro_expiry"] else "∞"
        LINE(em, "✅ DURUM", "**" + user.display_name + " PRO ÜYE!**\n📅 Bitiş: `" + exp + "`")
    else:
        LINE(em, "❌ DURUM", user.mention + " pro değil.\n👑 Owner verir: `k!prover`")
    LINE(em, "🌟 PRO AYRICALIKLARI (8 KOMUT)",
         "┃ 🎙️ `k!prooda` — Özel ses odası\n"
         "┃ 🎨 `k!prorenk` — Rank kartı rengi\n"
         "┃ 📊 `k!prostats` — Detaylı istatistik\n"
         "┃ ✒️ `k!proyazı` — Havalı yazı tipi\n"
         "┃ 📣 `k!proembed` — Özel embed oluştur\n"
         "┃ 🏷️ `k!protag` — Kişisel rozet tagi\n"
         "┃ ⚡ `k!proxp` — 2x XP boost\n"
         "┃ 🎁 Günlük +250 coin bonus")
    await safe_reply(ctx, em)

@kategori("pro")
@bot.command(name="prooda", aliases=["proroom"], help="Özel ses odası oluşturur (PRO)")
@is_pro()
async def prooda(ctx):
    cat = discord.utils.get(ctx.guild.categories, name="💎 PRO ODALAR")
    if not cat:
        cat = await ctx.guild.create_category("💎 PRO ODALAR")
        await cat.set_permissions(ctx.guild.default_role, view_channel=False)
    ch = await ctx.guild.create_voice_channel("👑 " + ctx.author.display_name, category=cat)
    await ch.set_permissions(ctx.author, connect=True, manage_channels=True, move_members=True)
    await safe_reply(ctx, E("🎙️ PRO ODA HAZIR!", ch.mention + " odan oluşturuldu!\n🔑 Yönetim sende!", C_PRO))

@kategori("pro")
@bot.command(name="prorenk", aliases=["procolor"], help="<hex> — Rank kartı rengi (PRO)")
@is_pro()
async def prorenk(ctx, hexcode: str):
    hexcode = hexcode.lstrip("#")
    if len(hexcode) != 6:
        return await safe_reply(ctx, E("❌", "Örnek: `k!prorenk ff0000`", C_ERROR))
    try: int(hexcode, 16)
    except ValueError:
        return await safe_reply(ctx, E("❌", "Geçersiz hex kodu!", C_ERROR))
    db.q("UPDATE users SET pro_color=? WHERE user_id=?", (hexcode, ctx.author.id))
    await safe_reply(ctx, E("🎨 RENK DEĞİŞTİ", "Rank kartı rengin: #" + hexcode.upper(), int(hexcode, 16)))

@kategori("pro")
@bot.command(name="prostats", aliases=["proistatistik"], help="Detaylı kişisel istatistik (PRO)")
@is_pro()
async def prostats(ctx):
    u = db.one("SELECT * FROM users WHERE user_id=?", (ctx.author.id,))
    em = E(None, None, C_PRO, thumb=ctx.author.display_avatar.url)
    em.set_author(name="📊 PRO İSTATİSTİK", icon_url=ctx.author.display_avatar.url)
    LINE(em, "💬 Toplam Mesaj", "`" + str(u["messages"]) + "`", True)
    LINE(em, "📈 Seviye", "`" + str(u["level"]) + "`", True)
    LINE(em, "✨ XP", "`" + str(u["xp"]) + "`", True)
    LINE(em, "🪙 Coin", "`" + str(u["coins"]) + "`", True)
    LINE(em, "⭐ İtibar", "`" + str(u["rep"]) + "`", True)
    LINE(em, "📝 Not", "`" + str(len(json.loads(u["notes"]))) + "`", True)
    LINE(em, "🎂 Doğum Günü", u["birthday"] or "—", True)
    LINE(em, "⚡ 2x XP", "✅" if u["xp2"] else "❌", True)
    if u["pro_tag"]: LINE(em, "🏷️ Tag", "`" + u["pro_tag"] + "`", True)
    LINE(em, "📊 İlerleme", progress_bar(min(100, u["xp"] / (u["level"] * 100) * 100)))
    await safe_reply(ctx, em)

@kategori("pro")
@bot.command(name="proyazı", aliases=["proyazi"], help="<metin> — Havalı yazı tipi (PRO)")
@is_pro()
async def proyazı(ctx, *, metin):
    await safe_reply(ctx, E("✒️ PRO YAZI", fancy(metin[:200]), C_PRO))

@kategori("pro")
@bot.command(name="proembed", help="<başlık> | <açıklama> | <hex> — Özel embed (PRO)")
@is_pro()
async def proembed(ctx, *, args):
    parts = [p.strip() for p in args.split("|")]
    if len(parts) < 2:
        return await safe_reply(ctx, E("❌ KULLANIM", "Örnek: `k!proembed Duyuru | Merhaba! | ff0000`", C_ERROR))
    color = C_PRO
    if len(parts) >= 3:
        try: color = int(parts[2].lstrip("#"), 16)
        except ValueError: pass
    em = E(parts[0][:256], parts[1][:4000], color)
    em.set_footer(text="💎 " + ctx.author.display_name + " • PRO Embed")
    await safe_reply(ctx, em)

@kategori("pro")
@bot.command(name="protag", help="<metin> — Kişisel rozet tagi (PRO)")
@is_pro()
async def protag(ctx, *, tag):
    tag = tag[:12]
    db.q("UPDATE users SET pro_tag=? WHERE user_id=?", (tag, ctx.author.id))
    await safe_reply(ctx, E("🏷️ TAG AYARLANDI", "Rozetin: **" + tag + "**\nRank kartında ve profilinde görünecek!", C_PRO))

@kategori("pro")
@bot.command(name="proxp", help="2x XP boost aç/kapat (PRO)")
@is_pro()
async def proxp(ctx):
    u = db.one("SELECT xp2 FROM users WHERE user_id=?", (ctx.author.id,))
    new = 0 if u["xp2"] else 1
    db.q("UPDATE users SET xp2=? WHERE user_id=?", (new, ctx.author.id))
    msg = "**⚡ 2x XP AÇIK!** Mesaj başına çifte XP kazanıyorsun." if new else "**2x XP KAPALI.**"
    await safe_reply(ctx, E("⚡ XP BOOST", msg, C_PRO))

# ═══════════════════════════════════════════════════════════════════════════
# 👑 OWNER PANELİ
# ═══════════════════════════════════════════════════════════════════════════
@kategori("owner")
@bot.command(name="sahip", aliases=["owner", "ownerpanel", "panel"], help="Owner panelini açar")
@is_owner()
async def sahip(ctx):
    maint = db.one("SELECT maintenance FROM owner_settings WHERE id=1")["maintenance"]
    up = datetime.datetime.now() - bot.start_time
    members = sum(g.member_count or 0 for g in bot.guilds)
    em = E(None, None, C_OWNER)
    em.set_author(name="👑 KATRE OWNER PANELİ", icon_url=bot.user.display_avatar.url)
    em.description = ("### Hoş geldin Sayın Owner! 👋\n" + SEP +
                      "\n🌐 Sunucu: `" + str(len(bot.guilds)) + "` • 👥 Kullanıcı: `" + str(members) + "`" +
                      "\n⏱️ Uptime: `" + str(up).split(".")[0] + "` • 📡 Ping: `" + str(round(bot.latency * 1000)) + "ms`" +
                      "\n🔧 Bakım Modu: **" + ("🔴 AÇIK" if maint else "🟢 KAPALI") + "**\n" + SEP +
                      "\n**Komutlar:** `k!prover` `k!proal` `k!bakım` `k!prefix` `k!blacklist` `k!durum` `k!eval`")
    await ctx.send(embed=em, view=OwnerPanelView(bot))

@kategori("owner")
@bot.command(name="prover", help="<@üye> [gün] — Pro üyelik verir")
@is_owner()
async def prover(ctx, user: discord.Member, gun: int = 30):
    ensure_user(user.id, str(user))
    exp = (datetime.datetime.now() + datetime.timedelta(days=gun)).isoformat()
    db.q("UPDATE users SET pro=1, pro_expiry=? WHERE user_id=?", (exp, user.id))
    await safe_reply(ctx, E("💎 PRO VERİLDİ",
        user.mention + " → **" + str(gun) + " gün** PRO!\n📅 Bitiş: `" +
        datetime.datetime.fromisoformat(exp).strftime("%d.%m.%Y") + "`", C_PRO))
    try: await user.send(embed=E("🎉 PRO OLDUN!", "**" + str(gun) + " gün** boyunca PRO ayrıcalıkları seninle! 💎", C_PRO))
    except Exception: pass

@kategori("owner")
@bot.command(name="proal", help="<@üye> — Pro üyeliği geri alır")
@is_owner()
async def proal(ctx, user: discord.Member):
    db.q("UPDATE users SET pro=0, pro_expiry=NULL WHERE user_id=?", (user.id,))
    await safe_reply(ctx, E("💔 PRO ALINDI", user.mention + " üyesinin pro üyeliği sonlandırıldı.", C_WARN))

@kategori("owner")
@bot.command(name="bakım", aliases=["bakim"], help="[aç/kapat] — Bakım modunu yönetir")
@is_owner()
async def bakım(ctx, mod: str = None):
    cur = db.one("SELECT maintenance FROM owner_settings WHERE id=1")["maintenance"]
    new = (not cur) if mod is None else (mod.lower() in ("aç", "ac", "on", "1"))
    db.q("UPDATE owner_settings SET maintenance=? WHERE id=1", (int(new),))
    msg = "**🔴 AÇILDI** — Bot sadece sana yanıt veriyor!" if new else "**🟢 KAPATILDI** — Bot herkese açık!"
    await safe_reply(ctx, E("🔧 BAKIM MODU", msg, C_WARN))

@kategori("owner")
@bot.command(name="prefix", aliases=["önek"], help="<yeni prefix> — Sunucu prefixini değiştirir")
@is_owner()
async def prefix(ctx, yeni: str):
    db.q("UPDATE servers SET prefix=? WHERE guild_id=?", (yeni, ctx.guild.id))
    await safe_reply(ctx, E("✅ PREFIX", "Yeni prefix: `" + yeni + "` (büyük/küçük fark etmez)", C_OK))

@kategori("owner")
@bot.command(name="blacklist", aliases=["bl"], help="<ekle/çıkar> <@üye> — Kara liste")
@is_owner()
async def blacklist(ctx, işlem: str, user: discord.User, *, sebep="—"):
    if işlem.lower() in ("ekle", "add"):
        db.q("INSERT OR REPLACE INTO blacklist(user_id,reason) VALUES(?,?)", (user.id, sebep))
        await safe_reply(ctx, E("🚫 KARALİSTE", user.mention + " kara listeye alındı!\n**Sebep:** " + sebep, C_ERROR))
    elif işlem.lower() in ("çıkar", "cikar", "remove"):
        db.q("DELETE FROM blacklist WHERE user_id=?", (user.id,))
        await safe_reply(ctx, E("✅ KARALİSTE", user.mention + " kara listeden çıkarıldı.", C_OK))
    else:
        await safe_reply(ctx, E("❌", "`k!blacklist ekle/çıkar @üye [sebep]`", C_ERROR))

@kategori("owner")
@bot.command(name="durum", aliases=["status"], help="<metin> — Bot durumunu değiştirir")
@is_owner()
async def durum(ctx, *, metin):
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name=metin))
    db.q("UPDATE owner_settings SET status_text=? WHERE id=1", (metin,))
    await safe_reply(ctx, E("✅ DURUM", "Yeni durum: **" + metin + "**", C_OK))

@kategori("owner")
@bot.command(name="sunucular", aliases=["guilds"], help="Botun tüm sunucularını listeler")
@is_owner()
async def sunucular(ctx):
    rows = sorted(bot.guilds, key=lambda g: -(g.member_count or 0))
    em = E(None, None, C_OWNER)
    em.set_author(name="🖥️ SUNUCULAR (" + str(len(rows)) + ")")
    for i, g in enumerate(rows[:15], 1):
        LINE(em, "`" + str(i) + ".` " + g.name, "└ 👥 " + str(g.member_count) + " • 🆔 `" + str(g.id) + "`")
    await safe_reply(ctx, em)

@kategori("owner")
@bot.command(name="eval", aliases=["py"], help="<kod> — Python çalıştır (Owner)")
@is_owner()
async def eval_cmd(ctx, *, code):
    env = {"bot": bot, "ctx": ctx, "db": db, "discord": discord,
           "guild": ctx.guild, "author": ctx.author, "channel": ctx.channel}
    buf = io.StringIO()
    func = "async def __f():\n" + textwrap.indent(code, "    ")
    try:
        exec(compile(func, "<eval>", "exec"), env)
        with redirect_stdout(buf):
            await env["__f"]()
        out = buf.getvalue()
        await ctx.send(content="```py\n" + (out[:1900] or "✅ OK (çıktı yok)") + "\n```")
    except Exception as e:
        await ctx.send(content="```py\nHATA: " + str(e)[:1900] + "\n```")

# ═══════════════════════════════════════════════════════════════════════════
# 🚀 BAŞLAT
# ═══════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    bot.run(BOT_TOKEN)
