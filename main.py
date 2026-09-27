# ═══════════════════════════════════════════════════════════════════════════
#  💧 KATRE BOT v2.1 — ULTRA PROFESYONEL ÇOK AMAÇLI DISCORD BOTU (TEK DOSYA)
#  ✅ Tüm syntax hataları düzeltildi (f-string yok → SyntaxError imkansız)
#  ✅ Prefix: k! / K! / özel prefix   ✅ Dönen durum   ✅ Kalıcı butonlar
#  ✅ 8 PRO komutu   ✅ Gelişmiş çekiliş paneli   ✅ Rol buton menüsü
#  ─ ENV: BOT_TOKEN, OWNER_ID, SUPPORT_URL
#  ─ KURULUM: pip install -U discord.py  →  python katre.py
# ═══════════════════════════════════════════════════════════════════════════

import discord
from discord.ext import commands, tasks
from discord.ui import View, Button, Select, Modal, TextInput
import sqlite3, os, json, random, asyncio, datetime, traceback, textwrap, io
from contextlib import redirect_stdout

# ═══════════════════════════════════════════════════════════════════════════
# ⚙️ YAPILANDIRMA (SADECE 3 ENV — GERİSİ OWNER PANELDEN)
# ═══════════════════════════════════════════════════════════════════════════
BOT_TOKEN   = os.getenv("BOT_TOKEN", "BURAYA_TOKEN")
OWNER_ID    = int(os.getenv("OWNER_ID", "0"))
SUPPORT_URL = os.getenv("SUPPORT_URL", "https://discord.gg/katre")

# 🎨 RENK PALETİ
C_MAIN  = 0x00A8FF; C_PRO = 0xFFD700; C_ERROR = 0xED4245; C_OK = 0x57F287
C_WARN  = 0xFEBB40; C_GIVE = 0xEB459E; C_FUN = 0x9B59B6; C_MOD = 0xE74C3C
C_ECO   = 0x2ECC71; C_OWNER = 0xFF0000
FOOTER  = "💧 Katre Bot • MarpeL Kalitesinde • k!yardım"
SEP     = "┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈"

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
        INSERT OR IGNORE INTO owner_settings(id) VALUES (1);
        """)
        # Eski DB'ler için güvenli kolon ekleme
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
# 🎨 EMBED YARDIMCILARI (F-STRING YOK → SÖZDİZİMİ HATASI İMKANSIZ)
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

def progress_bar(pct, length=12):
    """✅ DÜZELTİLDİ: f-string yok, saf birleştirme"""
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
    """Tam genişlik havalı yazı (Unicode blokları bitişik → güvenli)"""
    out = []
    for ch in t:
        o = ord(ch)
        if 97 <= o <= 122:   out.append(chr(o - 97 + 0xFF41))
        elif 65 <= o <= 90:  out.append(chr(o - 65 + 0xFF21))
        elif 48 <= o <= 57:  out.append(chr(o - 48 + 0xFF10))
        else: out.append(ch)
    return "".join(out)

# ═══════════════════════════════════════════════════════════════════════════
# 🔘 VIEW'LAR
# ═══════════════════════════════════════════════════════════════════════════
CATS = {
    "genel": ("🌐", "Genel & Sistem", C_MAIN),
    "mod":   ("🛡️", "Moderasyon",     C_MOD),
    "eco":   ("💰", "Ekonomi",        C_ECO),
    "fun":   ("🎮", "Eğlence",        C_FUN),
    "give":  ("🎉", "Çekiliş",        C_GIVE),
    "pro":   ("💎", "Pro Sistem",     C_PRO),
    "owner": ("👑", "Owner Panel",    C_OWNER),
}

def cat_embed(bot, key):
    icon, name, color = CATS[key]
    em = E(icon + " " + name.upper() + " KOMUTLARI", color=color,
           thumb=bot.user.display_avatar.url)
    cmds = [c for c in bot.commands if getattr(c, "kategori", None) == key]
    if key == "owner":
        em.description = "🔒 **Bu komutlar yalnızca bot sahibine özeldir!**" + "\n" + SEP
    for c in sorted(cmds, key=lambda x: x.name):
        sig = "`k!" + c.name + "`"
        if c.signature and key != "owner":
            sig += " `" + c.signature + "`"
        em.add_field(name=sig, value="└ " + (c.help or "—"), inline=False)
    if not cmds: em.description = "Bu kategoride komut yok."
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

    @discord.ui.button(label="İstatistik", style=discord.ButtonStyle.secondary, emoji="📊")
    async def stats(self, it, btn):
        up = datetime.datetime.now() - self.bot.start_time
        em = E("📊 KATRE CANLI İSTATİSTİK", color=C_MAIN, thumb=self.bot.user.display_avatar.url)
        LINE(em, "🌐 Sunucu", "`" + str(len(self.bot.guilds)) + "`", True)
        total = sum(g.member_count or 0 for g in self.bot.guilds)
        LINE(em, "👥 Kullanıcı", "`" + str(total) + "`", True)
        LINE(em, "📡 Ping", "`" + str(round(self.bot.latency * 1000)) + "ms`", True)
        LINE(em, "⏱️ Uptime", "`" + str(up).split(".")[0] + "`", True)
        LINE(em, "🧩 Komut", "`" + str(len(self.bot.commands)) + "`", True)
        LINE(em, "👑 Owner", "<@" + str(OWNER_ID) + ">", True)
        await it.response.send_message(embed=em, ephemeral=True)

    @discord.ui.button(label="Menüyü Kapat", style=discord.ButtonStyle.danger, emoji="🗑️")
    async def close(self, it, btn):
        await it.message.delete()

    def link_buttons(self):
        self.add_item(Button(label="Destek Sunucusu", url=SUPPORT_URL,
                             style=discord.ButtonStyle.link, emoji="🔗"))
        return self

# ─────────────────────────── OWNER PANELİ ───────────────────────────
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
        aktif = len(db.all("SELECT * FROM giveaways WHERE status='active'"))  # ✅ DÜZELTİLDİ
        em = E("👑 OWNER İSTATİSTİK PANELİ", color=C_OWNER, thumb=self.bot.user.display_avatar.url)
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
        em = E("🖥️ BOTUN SUNUCULARI (" + str(len(self.bot.guilds)) + ")", color=C_OWNER)
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

# ─────────────────────────── ÇEKİLİŞ (KALICI) ───────────────────────────
def gw_embed(gw, bot):
    parts = json.loads(gw["participants"])
    em = E("🎉 ÇEKİLİŞ BAŞLADI! 🎉",
           "### 🎁 Ödül: **" + gw["prize"] + "**\n🔘 Aşağıdaki **KATIL** butonuna bas!\n" + SEP,
           C_GIVE, thumb=bot.user.display_avatar.url)
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

# ─────────────────────────── ROL BUTON MENÜSÜ (KALICI) ───────────────────────────
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

# ─────────────────────────── DESTEK / TICKET (KALICI) ───────────────────────────
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
        em = E("🎫 DESTEK TALEBİ OLUŞTURULDU",
               "**Konu:** " + self.konu.value + "\n**Açıklama:** " + self.aciklama.value + "\n" + SEP +
               "\n👤 **Kullanıcı:** " + it.user.mention +
               "\n📅 **Tarih:** <t:" + str(int(datetime.datetime.now().timestamp())) + ":F>\n\n⏳ Ekibimiz birazdan yanında!",
               C_MAIN, thumb=it.user.display_avatar.url)
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
    async def no(self, btn=None, it=None):
        pass
    @discord.ui.button(label="Vazgeç", style=discord.ButtonStyle.secondary, emoji="❌")
    async def no2(self, it, btn):
        self.value = False; self.stop()
        await it.response.edit_message(embed=E("❌ İPTAL", "İşlem iptal edildi.", C_WARN), view=None)

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
        # Rol menülerini yeniden kaydet
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
        print("║      💧  K A T R E   B O T   v2.1  💧           ║")
        print("║   MarpeL Kalitesinde • Tek Dosya • Kusursuz     ║")
        print("╚═══════════════════════════════════════════════╝")
        print("✅ Giriş yapıldı : " + str(self.user))
        print("🌐 Sunucu sayısı : " + str(len(self.guilds)))
        print("👑 Owner         : " + str(OWNER_ID))
        print("🧩 Komut sayısı  : " + str(len(self.commands)))
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
            (discord.ActivityType.listening, "k!rank • Seviye sistemi 📈"),
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

    async def on_message(self, message):
        if message.author.bot: return
        maint = db.one("SELECT maintenance FROM owner_settings WHERE id=1")["maintenance"]
        if maint and message.author.id != OWNER_ID: return
        if db.one("SELECT 1 FROM blacklist WHERE user_id=?", (message.author.id,)): return
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
                    em = E("🎉 SEVİYE ATLADIN!",
                           message.author.mention + " artık **Seviye " + str(lvl) + "**! 🚀\n" + SEP +
                           "\n🎁 Hediye: **" + str(coin) + " coin**\n💧 Devam et, harika gidiyorsun!",
                           C_PRO, thumb=message.author.display_avatar.url)
                    LINE(em, "📊 İlerleme", progress_bar(xp / (lvl * 100) * 100))
                    await message.channel.send(embed=em)
                db.q("UPDATE users SET xp=?, level=? WHERE user_id=?", (xp, lvl, message.author.id))
        await self.process_commands(message)

    async def on_command_completion(self, ctx):
        db.q("INSERT INTO cmd_stats(cmd,uses) VALUES(?,1) ON CONFLICT(cmd) DO UPDATE SET uses=uses+1",
             (ctx.command.name,))

    async def on_command_error(self, ctx, error):
        if isinstance(error, OwnerOnly): return
        if isinstance(error, ProOnly):
            v = View(); v.add_item(Button(label="Pro Olmak İçin Destek", url=SUPPORT_URL,
                                          style=discord.ButtonStyle.link, emoji="💎"))
            return await ctx.send(embed=E("💎 PRO GEREKLİ!",
                "Bu komut yalnızca **Pro üyelere** özeldir!\n" + SEP +
                "\n👑 Owner'dan pro üyelik alabilirsin.\n📋 Pro komutlar: `k!pro`", C_PRO), view=v)
        if isinstance(error, commands.CommandNotFound):
            return await ctx.send(embed=E("❓ KOMUT BULUNAMADI", "Tüm komutlar için: `k!yardım`", C_WARN))
        if isinstance(error, commands.MissingRequiredArgument):
            return await ctx.send(embed=E("❌ EKSİK ARGÜMAN",
                "Doğru kullanım:\n`k!" + ctx.command.name + " " + ctx.command.signature + "`", C_ERROR))
        if isinstance(error, commands.CommandOnCooldown):
            return await ctx.send(embed=E("⏳ BEKLEME SÜRESİ",
                "Tekrar kullanmak için **" + str(int(error.retry_after)) + " saniye** beklemelisin.", C_WARN))
        if isinstance(error, commands.MissingPermissions):
            return await ctx.send(embed=E("🔒 YETKİ YOK",
                "Gerekli yetki(ler): `" + ", ".join(error.missing_permissions) + "`", C_ERROR))
        if isinstance(error, commands.CheckFailure):
            return await ctx.send(embed=E("🔒 YETKİ YOK", "Bu komutu kullanma yetkin yok!", C_ERROR))
        if isinstance(error, commands.CommandInvokeError):
            error = error.original
        try:
            await ctx.send(embed=E("⚠️ BEKLENMEYEN HATA", "```\n" + str(error)[:900] + "\n```", C_ERROR))
        except Exception: pass
        traceback.print_exc()

    async def on_member_join(self, member):
        ensure_user(member.id, str(member))
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
                em = E("👋 HOŞ GELDİN!",
                       "### " + member.mention + " aramıza katıldı!\n" +
                       "🎉 Sunucumuz artık **" + str(member.guild.member_count) + "** üye!\n" + SEP +
                       "\n📅 Hesap: <t:" + str(int(member.created_at.timestamp())) + ":R>" +
                       "\n💧 İyi eğlenceler dileriz!", C_OK, thumb=member.display_avatar.url)
                await ch.send(embed=em)

    async def on_guild_join(self, guild):
        db.q("INSERT OR IGNORE INTO servers(guild_id, joined_at) VALUES(?,?)",
             (guild.id, datetime.datetime.now().isoformat()))
        ch = guild.system_channel or next((c for c in guild.text_channels
                     if c.permissions_for(guild.me).send_messages), None)
        if ch:
            em = E("💧 KATRE BOT ARANIZDA!",
                   "**" + guild.name + "** sunucusuna hoş geldim! 🎉\n" + SEP +
                   "\n📚 Komutlar: `k!yardım`\n🎉 Çekiliş: `k!çekiliş`" +
                   "\n📈 Rank: `k!rank`\n🎫 Destek: `k!destek`\n💎 Pro: `k!pro`",
                   C_MAIN, thumb=self.user.display_avatar.url)
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
            done.title = "🎊 ÇEKİLİŞ SONA ERDİ"; done.color = C_PRO
            done.add_field(name="🏆 Kazananlar", value=mentions, inline=False)
            await msg.edit(embed=done, view=bot.gw_view)
        except Exception: pass

bot = KatreBot()

# ═══════════════════════════════════════════════════════════════════════════
# 🌐 GENEL & SİSTEM
# ═══════════════════════════════════════════════════════════════════════════
@bot.command(name="yardım", aliases=["yardim", "help", "komutlar", "menü"], help="Yardım menüsünü açar")
@kategori("genel")
@commands.cooldown(1, 5, commands.BucketType.user)
async def yardim(ctx):
    total = sum(g.member_count or 0 for g in bot.guilds)
    em = E("💧 KATRE BOT — YARDIM MENÜSÜ",
           "### 🌟 MarpeL kalitesinde çok amaçlı bot!\n" + SEP +
           "\n🧩 **" + str(len(bot.commands)) + "** komut • 🌐 **" + str(len(bot.guilds)) + "** sunucu" +
           "\n👥 **" + str(total) + "** kullanıcı • 👑 Owner: <@" + str(OWNER_ID) + ">" +
           "\n" + SEP + "\n📂 **Aşağıdaki menüden kategori seç!**",
           C_MAIN, thumb=bot.user.display_avatar.url)
    for k, (i, n, c) in CATS.items():
        cnt = len([c2 for c2 in bot.commands if getattr(c2, "kategori", None) == k])
        LINE(em, i + " " + n, "`" + str(cnt) + "` komut", True)
    await ctx.send(embed=em, view=HelpView(bot).link_buttons())

@bot.command(name="ping", help="Bot gecikmesini gösterir")
@kategori("genel")
async def ping(ctx):
    ms = round(bot.latency * 1000)
    bar = "🟢" if ms < 100 else ("🟡" if ms < 200 else "🔴")
    await ctx.send(embed=E("🏓 PONG!", bar + " Gecikme: **" + str(ms) + "ms**", C_OK))

@bot.command(name="istatistik", aliases=["stats", "botbilgi"], help="Bot istatistiklerini gösterir")
@kategori("genel")
async def istatistik(ctx):
    up = datetime.datetime.now() - bot.start_time
    total = db.one("SELECT SUM(uses) u FROM cmd_stats")["u"] or 0
    em = E("📊 KATRE BOT İSTATİSTİK", color=C_MAIN, thumb=bot.user.display_avatar.url)
    LINE(em, "🌐 Sunucu", "`" + str(len(bot.guilds)) + "`", True)
    LINE(em, "👥 Kullanıcı", "`" + str(sum(g.member_count or 0 for g in bot.guilds)) + "`", True)
    LINE(em, "🧩 Komut", "`" + str(len(bot.commands)) + "`", True)
    LINE(em, "⏱️ Uptime", "`" + str(up).split(".")[0] + "`", True)
    LINE(em, "📡 Ping", "`" + str(round(bot.latency * 1000)) + "ms`", True)
    LINE(em, "⌨️ Toplam Komut", "`" + str(total) + "`", True)
    LINE(em, "👑 Owner", "<@" + str(OWNER_ID) + ">")
    LINE(em, "🐍 Altyapı", "`discord.py 2.x • SQLite • Tek Dosya`")
    await ctx.send(embed=em)

@bot.command(name="davet", aliases=["invite", "ekle"], help="Bot davet linki")
@kategori("genel")
async def davet(ctx):
    url = discord.utils.oauth_url(str(bot.user.id), permissions=discord.Permissions(administrator=True))
    em = E("➕ KATRE BOT'U EKLE", "Butona tıkla, tüm sistemler tek botta! 🚀\n" + SEP,
           C_MAIN, thumb=bot.user.display_avatar.url)
    v = View()
    v.add_item(Button(label="Botu Ekle", url=url, style=discord.ButtonStyle.link, emoji="➕"))
    v.add_item(Button(label="Destek Sunucusu", url=SUPPORT_URL, style=discord.ButtonStyle.link, emoji="🔗"))
    await ctx.send(embed=em, view=v)

@bot.command(name="avatar", aliases=["av", "pp"], help="Kullanıcı avatarını gösterir")
@kategori("genel")
async def avatar(ctx, user: discord.Member = None):
    user = user or ctx.author
    em = E("🖼️ " + user.display_name + " — AVATAR", color=C_MAIN, img=user.display_avatar.url)
    v = View(); v.add_item(Button(label="Tarayıcıda Aç", url=user.display_avatar.url,
                                  style=discord.ButtonStyle.link, emoji="🔗"))
    await ctx.send(embed=em, view=v)

@bot.command(name="sunucubilgi", aliases=["serverinfo"], help="Sunucu bilgileri")
@kategori("genel")
async def sunucubilgi(ctx):
    g = ctx.guild
    em = E("🌐 " + g.name + " — SUNUCU BİLGİSİ", color=C_MAIN, thumb=g.icon.url if g.icon else None)
    LINE(em, "👑 Kurucu", "<@" + str(g.owner_id) + ">", True)
    LINE(em, "🆔 ID", "`" + str(g.id) + "`", True)
    LINE(em, "📅 Kuruluş", "<t:" + str(int(g.created_at.timestamp())) + ":D>", True)
    LINE(em, "👥 Üye", "`" + str(g.member_count) + "`", True)
    LINE(em, "💬 Kanal", "`" + str(len(g.channels)) + "`", True)
    LINE(em, "🎭 Rol", "`" + str(len(g.roles)) + "`", True)
    LINE(em, "🎉 Boost", "`" + str(g.premium_subscription_count or 0) + "`", True)
    LINE(em, "😊 Emoji", "`" + str(len(g.emojis)) + "`", True)
    await ctx.send(embed=em)

@bot.command(name="kullanıcıbilgi", aliases=["userinfo", "kb"], help="Kullanıcı bilgileri")
@kategori("genel")
async def kullanıcıbilgi(ctx, user: discord.Member = None):
    user = user or ctx.author
    u = db.one("SELECT * FROM users WHERE user_id=?", (user.id,)) or {}
    em = E("👤 " + user.display_name + " — BİLGİ", color=C_MAIN, thumb=user.display_avatar.url)
    LINE(em, "🆔 ID", "`" + str(user.id) + "`", True)
    LINE(em, "📅 Hesap", "<t:" + str(int(user.created_at.timestamp())) + ":R>", True)
    kat = "<t:" + str(int(user.joined_at.timestamp())) + ":R>" if user.joined_at else "—"
    LINE(em, "🎉 Katılım", kat, True)
    LINE(em, "📈 Seviye", "`" + str(u.get("level", 1)) + "`", True)
    LINE(em, "💰 Coin", "`" + str(u.get("coins", 0)) + "`", True)
    LINE(em, "💎 Pro", "✅" if u.get("pro") else "❌", True)
    if u.get("pro_tag"): LINE(em, "🏷️ Tag", "`" + u["pro_tag"] + "`", True)
    LINE(em, "🎭 Roller", ", ".join(r.mention for r in user.roles[1:][:8]) or "—")
    await ctx.send(embed=em)

@bot.command(name="rank", aliases=["seviye", "level", "xp"], help="Seviye kartını gösterir")
@kategori("genel")
@commands.cooldown(1, 3, commands.BucketType.user)
async def rank(ctx, user: discord.Member = None):
    user = user or ctx.author
    ensure_user(user.id, str(user))
    u = db.one("SELECT * FROM users WHERE user_id=?", (user.id,))
    need = u["level"] * 100
    pct = min(100, u["xp"] / need * 100)
    color = int(u["pro_color"], 16) if u["pro"] and u["pro_color"] else (C_PRO if u["pro"] else C_MAIN)
    em = E("📈 " + user.display_name + " — RANK KARTI", color=color, thumb=user.display_avatar.url)
    badges = []
    if u["pro"]: badges.append("💎 PRO")
    if u["pro_tag"]: badges.append("🏷️ " + u["pro_tag"])
    if u["xp2"]: badges.append("⚡ 2x XP")
    if badges: em.description = "### " + " • ".join(badges)
    LINE(em, "🏆 Seviye", "`" + str(u["level"]) + "`", True)
    LINE(em, "✨ XP", "`" + str(u["xp"]) + "/" + str(need) + "`", True)
    LINE(em, "💬 Mesaj", "`" + str(u["messages"]) + "`", True)
    LINE(em, "💰 Coin", "`" + str(u["coins"]) + "`", True)
    LINE(em, "⭐ İtibar", "`" + str(u["rep"]) + "`", True)
    LINE(em, "⚠️ Uyarı", "`" + str(u["warnings"]) + "`", True)
    LINE(em, "📊 İlerleme", progress_bar(pct))
    await ctx.send(embed=em)

@bot.command(name="sıralama", aliases=["sirala", "top", "lb", "leaderboard"], help="Sunucu seviye sıralaması")  # ✅ DÜZELTİLDİ
@kategori("genel")
async def sıralama(ctx):
    rows = db.all("SELECT * FROM users ORDER BY level DESC, xp DESC LIMIT 10")
    if not rows: return await ctx.send(embed=E("📊", "Henüz veri yok!", C_WARN))
    medals = ["🥇", "", ""]  # ✅ DÜZELTİLDİ
    em = E("🏆 " + ctx.guild.name + " — SIRALAMA", color=C_PRO)
    txt = ""
    for i, r in enumerate(rows):
        head = medals[i] if i < 3 else "**" + str(i + 1) + ".**"
        pro = " 💎" if r["pro"] else ""
        txt += head + " <@" + r["user_id"] + ">" + pro + " — **Lv." + str(r["level"]) + "** • `" + str(r["xp"]) + " XP`\n"
    em.description = txt
    await ctx.send(embed=em)

@bot.command(name="rep", aliases=["itibar"], help="<@üye> — İtibar ver (12s)")
@kategori("genel")
@commands.cooldown(1, 43200, commands.BucketType.user)
async def rep(ctx, user: discord.Member):
    if user.id == ctx.author.id:
        return await ctx.send(embed=E("❌", "Kendine itibar veremezsin!", C_ERROR))
    ensure_user(user.id, str(user))
    db.q("UPDATE users SET rep=rep+1 WHERE user_id=?", (user.id,))
    await ctx.send(embed=E("⭐ İTİBAR VERİLDİ", ctx.author.mention + " → " + user.mention + " ⭐\n+1 itibar!", C_PRO))

@bot.command(name="destek", aliases=["ticket"], help="Destek paneli gönderir (Yönetici)")
@kategori("genel")
@commands.has_permissions(administrator=True)
async def destek(ctx):
    em = E("🎫 KATRE DESTEK MERKEZİ",
           "Sorun mu var? Önerin mi var?\n**Butona tıkla, formu doldur, ekibimiz yanında!** 💧\n" + SEP +
           "\n⏱️ Ortalama yanıt: **< 1 saat**", C_MAIN, thumb=bot.user.display_avatar.url)
    await ctx.send(embed=em, view=TicketOpenView())
    try: await ctx.message.delete()
    except Exception: pass

@bot.command(name="not", aliases=["note"], help="<metin> — Kendine not kaydet")
@kategori("genel")
async def not_(ctx, *, metin):
    ensure_user(ctx.author.id, str(ctx.author))
    u = db.one("SELECT notes FROM users WHERE user_id=?", (ctx.author.id,))
    notes = json.loads(u["notes"]); notes.append({"t": metin, "d": datetime.datetime.now().isoformat()})
    db.q("UPDATE users SET notes=? WHERE user_id=?", (json.dumps(notes), ctx.author.id))
    await ctx.send(embed=E("📝 NOT KAYDEDİLDİ", "```\n" + metin[:500] + "\n```\nToplam not: `" + str(len(notes)) + "`", C_OK))

@bot.command(name="notlar", aliases=["notes"], help="Kayıtlı notlarını listeler")
@kategori("genel")
async def notlar(ctx):
    u = db.one("SELECT notes FROM users WHERE user_id=?", (ctx.author.id,))
    notes = json.loads(u["notes"]) if u else []
    if not notes: return await ctx.send(embed=E("📝", "Henüz notun yok! `k!not <metin>`", C_WARN))
    em = E("📝 NOTLARIN (" + str(len(notes)) + ")", color=C_MAIN)
    for i, n in enumerate(notes[-8:], 1):
        LINE(em, "`" + str(i) + ".` " + datetime.datetime.fromisoformat(n["d"]).strftime("%d.%m.%Y"),
             "└ " + n["t"][:80])
    await ctx.send(embed=em)

@bot.command(name="doğumgünü", aliases=["dogumgunu", "birthday"], help="<gün> <ay> — Doğum günü ayarla")
@kategori("genel")
async def doğumgünü(ctx, gün: int, ay: int):
    if not (1 <= gün <= 31 and 1 <= ay <= 12):
        return await ctx.send(embed=E("❌", "Geçersiz tarih! Örnek: `k!doğumgünü 24 8`", C_ERROR))
    db.q("UPDATE users SET birthday=? WHERE user_id=?", (str(gün) + "." + str(ay), ctx.author.id))
    await ctx.send(embed=E("🎂 DOĞUM GÜNÜ KAYDEDİLDİ", "Doğum günün: **" + str(gün) + "." + str(ay) + "** 🎈", C_PRO))

@bot.command(name="doğumgünleri", aliases=["dogumgunleri"], help="Bu ayın doğum günleri")
@kategori("genel")
async def doğumgünleri(ctx):
    now = datetime.datetime.now()
    rows = [r for r in db.all("SELECT user_id,birthday FROM users WHERE birthday IS NOT NULL")
            if r["birthday"] and int(r["birthday"].split(".")[1]) == now.month]
    if not rows: return await ctx.send(embed=E("🎂", "Bu ay doğum günü yok!", C_WARN))
    em = E("🎂 " + str(now.month) + ". AY DOĞUM GÜNLERİ", color=C_PRO)
    for r in sorted(rows, key=lambda x: int(x["birthday"].split(".")[0])):
        LINE(em, "🎈 " + r["birthday"], "<@" + str(r["user_id"]) + ">")
    await ctx.send(embed=em)

@bot.command(name="hatırlat", aliases=["hatirlat"], help="<dakika> <metin> — Hatırlatıcı")
@kategori("genel")
async def hatırlat(ctx, dk: int, *, metin):
    if dk < 1 or dk > 1440: return await ctx.send(embed=E("❌", "1-1440 dakika arası gir!", C_ERROR))
    await ctx.send(embed=E("⏰ HATIRLATICI KURULDU", "**" + str(dk) + " dakika** sonra: " + metin, C_OK))
    await asyncio.sleep(dk * 60)
    await ctx.send(ctx.author.mention + " ⏰ **HATIRLATMA:** " + metin)

# ═══════════════════════════════════════════════════════════════════════════
# 🛡️ MODERASYON
# ═══════════════════════════════════════════════════════════════════════════
@bot.command(name="yasakla", aliases=["ban"], help="<@üye> [sebep] — Üyeyi yasaklar")
@kategori("mod")
@commands.has_permissions(ban_members=True)
@commands.bot_has_permissions(ban_members=True)
async def yasakla(ctx, user: discord.Member, *, sebep="Belirtilmedi"):
    v = ConfirmView()
    await ctx.send(embed=E("⚠️ ONAY GEREKLİ",
        "**" + str(user) + "** üyesini yasaklamak üzeresin!\n**Sebep:** " + sebep + "\n\nOnaylıyor musun?", C_WARN), view=v)
    await v.wait()
    if v.value is None:
        return await ctx.send(embed=E("⌛ ZAMAN AŞIMI", "Onay beklenmedi, işlem iptal.", C_WARN))
    if v.value:
        try: await user.send(embed=E("🔨 YASAKLANDIN", "**" + ctx.guild.name + "**\n**Sebep:** " + sebep, C_ERROR))
        except Exception: pass
        await user.ban(reason=str(ctx.author) + " | " + sebep)
        await ctx.send(embed=E("🔨 YASAKLAMA", user.mention + " yasaklandı!\n**Sebep:** `" + sebep + "`", C_MOD))

@bot.command(name="at", aliases=["kick"], help="<@üye> [sebep] — Üyeyi atar")
@kategori("mod")
@commands.has_permissions(kick_members=True)
@commands.bot_has_permissions(kick_members=True)
async def at(ctx, user: discord.Member, *, sebep="Belirtilmedi"):
    v = ConfirmView()
    await ctx.send(embed=E("⚠️ ONAY GEREKLİ", "**" + str(user) + "** üyesini atmak üzeresin!\n**Sebep:** " + sebep, C_WARN), view=v)
    await v.wait()
    if v.value is None:
        return await ctx.send(embed=E("⌛ ZAMAN AŞIMI", "İşlem iptal.", C_WARN))
    if v.value:
        await user.kick(reason=str(ctx.author) + " | " + sebep)
        await ctx.send(embed=E("👢 ATMA", user.mention + " atıldı!\n**Sebep:** `" + sebep + "`", C_MOD))

@bot.command(name="uyar", aliases=["warn"], help="<@üye> [sebep] — Üyeyi uyarır")
@kategori("mod")
@commands.has_permissions(manage_messages=True)
async def uyar(ctx, user: discord.Member, *, sebep="Belirtilmedi"):
    ensure_user(user.id, str(user))
    db.q("UPDATE users SET warnings=warnings+1 WHERE user_id=?", (user.id,))
    w = db.one("SELECT warnings FROM users WHERE user_id=?", (user.id,))["warnings"]
    await ctx.send(embed=E("⚠️ UYARI", user.mention + " uyarıldı!\n**Sebep:** `" + sebep + "`\n**Toplam:** `" + str(w) + "`", C_WARN))
    try: await user.send(embed=E("⚠️ UYARILDIN", "**" + ctx.guild.name + "**\n**Sebep:** " + sebep, C_WARN))
    except Exception: pass

@bot.command(name="uyarılar", aliases=["warns"], help="[<@üye>] — Uyarıları listeler")
@kategori("mod")
async def uyarılar(ctx, user: discord.Member = None):
    user = user or ctx.author
    ensure_user(user.id, str(user))
    w = db.one("SELECT warnings FROM users WHERE user_id=?", (user.id,))["warnings"]
    await ctx.send(embed=E("⚠️ UYARILAR", user.mention + " üyesinin **" + str(w) + "** uyarısı var.", C_WARN))

@bot.command(name="temizle", aliases=["purge", "sil"], help="<adet> — Mesajları siler")
@kategori("mod")
@commands.has_permissions(manage_messages=True)
@commands.bot_has_permissions(manage_messages=True)
async def temizle(ctx, adet: int):
    if not 1 <= adet <= 500: return await ctx.send(embed=E("❌", "1-500 arası sayı gir!", C_ERROR))
    await ctx.channel.purge(limit=adet + 1)
    m = await ctx.send(embed=E("🧹 TEMİZLENDİ", "**" + str(adet) + "** mesaj silindi!", C_OK))
    await m.delete(delay=5)

@bot.command(name="yavaşmod", aliases=["slowmode"], help="<saniye> — Yavaş mod")
@kategori("mod")
@commands.has_permissions(manage_channels=True)
async def yavaşmod(ctx, sn: int):
    await ctx.channel.edit(slowmode_delay=sn)
    msg = "Kanal yavaş modu: **" + str(sn) + " saniye**" if sn else "**Kapatıldı**"
    await ctx.send(embed=E("🐌 YAVAŞ MOD", msg, C_OK))

@bot.command(name="kilit", aliases=["lock"], help="Kanalı kilitler")
@kategori("mod")
@commands.has_permissions(manage_channels=True)
async def kilit(ctx):
    await ctx.channel.set_permissions(ctx.guild.default_role, send_messages=False)
    await ctx.send(embed=E("🔒 KANAL KİLİTLENDİ", ctx.channel.mention + " artık yazmaya kapalı.", C_MOD))

@bot.command(name="kilitaç", aliases=["unlock"], help="Kanal kilidini açar")
@kategori("mod")
@commands.has_permissions(manage_channels=True)
async def kilitaç(ctx):
    await ctx.channel.set_permissions(ctx.guild.default_role, send_messages=None)
    await ctx.send(embed=E("🔓 KİLİT AÇILDI", ctx.channel.mention + " yazmaya açık.", C_OK))

@bot.command(name="otorol", aliases=["autorol"], help="<@rol|kapat> — Otorol ayarlar")
@kategori("mod")
@commands.has_permissions(administrator=True)
async def otorol(ctx, *, arg):
    if arg.lower() in ("kapat", "off", "0"):
        db.q("UPDATE servers SET auto_role=NULL WHERE guild_id=?", (ctx.guild.id,))
        return await ctx.send(embed=E("✅ OTOROL", "Otorol **kapatıldı**.", C_OK))
    role = await commands.RoleConverter().convert(ctx, arg)
    db.q("UPDATE servers SET auto_role=? WHERE guild_id=?", (role.id, ctx.guild.id))
    await ctx.send(embed=E("✅ OTOROL", "Yeni üyelere " + role.mention + " rolü verilecek.", C_OK))

@bot.command(name="hoşgeldin", aliases=["hosgeldin", "welcome"], help="<#kanal|kapat> — Hoşgeldin kanalı")
@kategori("mod")
@commands.has_permissions(administrator=True)
async def hoşgeldin(ctx, ch: discord.TextChannel = None):
    if ch is None:
        db.q("UPDATE servers SET welcome_ch=NULL WHERE guild_id=?", (ctx.guild.id,))
        return await ctx.send(embed=E("✅ HOŞGELDİN", "Hoşgeldin sistemi **kapatıldı**.", C_OK))
    db.q("UPDATE servers SET welcome_ch=? WHERE guild_id=?", (ch.id, ctx.guild.id))
    await ctx.send(embed=E("✅ HOŞGELDİN", "Yeni üyeler " + ch.mention + " kanalında karşılanacak! 👋", C_OK))

@bot.command(name="butonrol", aliases=["rolmenü"], help="<@rol...> — Rol buton menüsü oluşturur")
@kategori("mod")
@commands.has_permissions(administrator=True)
async def butonrol(ctx, roles: commands.Greedy[discord.Role], *, açıklama="Rollerinizi butonlarla alın!"):
    if not roles or len(roles) > 25: return await ctx.send(embed=E("❌", "1-25 arası rol etiketle!", C_ERROR))
    menu_id = str(random.randint(10**11, 10**12 - 1))
    db.q("INSERT OR REPLACE INTO role_menus(menu_id,guild_id,role_ids) VALUES(?,?,?)",
         (menu_id, ctx.guild.id, json.dumps([r.id for r in roles])))
    em = E("🎭 ROL SEÇİM MENÜSÜ", açıklama + "\n" + SEP + "\n" +
           "\n".join("🔹 " + r.mention for r in roles), C_MAIN)
    view = RoleMenuView(menu_id, [(r.id, r.name) for r in roles])
    bot.add_view(view)
    await ctx.send(embed=em, view=view)

# ═══════════════════════════════════════════════════════════════════════════
# 💰 EKONOMİ
# ═══════════════════════════════════════════════════════════════════════════
@bot.command(name="cüzdan", aliases=["balance", "para"], help="[<@üye>] — Coin bakiyesi")
@kategori("eco")
async def cüzdan(ctx, user: discord.Member = None):
    user = user or ctx.author
    ensure_user(user.id, str(user))
    u = db.one("SELECT * FROM users WHERE user_id=?", (user.id,))
    em = E("💰 " + user.display_name + " — CÜZDAN", color=C_ECO, thumb=user.display_avatar.url)
    LINE(em, "🪙 Coin", "`" + format(u["coins"], ",").replace(",", ".") + "`", True)
    LINE(em, "⭐ İtibar", "`" + str(u["rep"]) + "`", True)
    LINE(em, "💎 Pro", "✅" if u["pro"] else "❌", True)
    await ctx.send(embed=em)

@bot.command(name="günlük", aliases=["gunluk", "daily"], help="Günlük coin ödülü")
@kategori("eco")
@commands.cooldown(1, 86400, commands.BucketType.user)
async def günlük(ctx):
    ensure_user(ctx.author.id, str(ctx.author))
    u = db.one("SELECT * FROM users WHERE user_id=?", (ctx.author.id,))
    bonus = random.randint(150, 400) + (250 if u["pro"] else 0)
    db.q("UPDATE users SET coins=coins+? WHERE user_id=?", (bonus, ctx.author.id))
    extra = "\n💎 **Pro bonusu:** +250" if u["pro"] else ""
    await ctx.send(embed=E("🎁 GÜNLÜK ÖDÜL", "**+" + str(bonus) + " coin** kazandın! 🪙" + extra, C_ECO))

@bot.command(name="çalış", aliases=["calis", "work"], help="Çalışıp coin kazanırsın")
@kategori("eco")
@commands.cooldown(1, 1800, commands.BucketType.user)
async def çalış(ctx):
    jobs = [("💻 Yazılım geliştirdin", 200, 400), ("🎨 Tasarım yaptın", 150, 300),
            ("📹 İçerik ürettin", 180, 350), ("🍕 Pizzacılık yaptın", 100, 220),
            ("🚕 Şoförlük yaptın", 120, 260), ("📚 Ders verdin", 160, 320)]
    job, a, b = random.choice(jobs)
    pay = random.randint(a, b)
    db.q("UPDATE users SET coins=coins+? WHERE user_id=?", (pay, ctx.author.id))
    await ctx.send(embed=E("💼 ÇALIŞTIN!", job + "\n**+" + str(pay) + " coin** kazandın! 🪙", C_ECO))

@bot.command(name="soy", aliases=["rob"], help="<@üye> — Üyeyi soymayı dener")
@kategori("eco")
@commands.cooldown(1, 600, commands.BucketType.user)
async def soy(ctx, user: discord.Member):
    if user.id == ctx.author.id or user.bot:
        return await ctx.send(embed=E("❌", "Geçersiz hedef!", C_ERROR))
    ensure_user(user.id, str(user))
    t = db.one("SELECT coins FROM users WHERE user_id=?", (user.id,))
    me = db.one("SELECT coins FROM users WHERE user_id=?", (ctx.author.id,))
    if t["coins"] < 200:
        return await ctx.send(embed=E("❌", user.mention + " üyesinde çalınacak coin yok!", C_ERROR))
    if random.random() < 0.45:
        steal = random.randint(50, min(500, t["coins"]))
        db.q("UPDATE users SET coins=coins-? WHERE user_id=?", (steal, user.id))
        db.q("UPDATE users SET coins=coins+? WHERE user_id=?", (steal, ctx.author.id))
        await ctx.send(embed=E("🦹 SOYGUN BAŞARILI!", user.mention + " üyesinden **" + str(steal) + " coin** çaldın! 💰", C_ECO))
    else:
        fine = min(me["coins"], random.randint(50, 200))
        db.q("UPDATE users SET coins=coins-? WHERE user_id=?", (fine, ctx.author.id))
        await ctx.send(embed=E("🚨 YAKALANDIN!", "Soygun başarısız! **" + str(fine) + " coin** ceza! 👮", C_ERROR))

@bot.command(name="transfer", aliases=["gönder"], help="<@üye> <miktar> — Coin gönderir")
@kategori("eco")
async def transfer(ctx, user: discord.Member, miktar: int):
    if miktar <= 0 or user.id == ctx.author.id:
        return await ctx.send(embed=E("❌", "Geçersiz işlem!", C_ERROR))
    ensure_user(user.id, str(user))
    me = db.one("SELECT coins FROM users WHERE user_id=?", (ctx.author.id,))
    if me["coins"] < miktar:
        return await ctx.send(embed=E("❌ YETERSİZ BAKİYE", "Sadece **" + str(me["coins"]) + "** coinin var!", C_ERROR))
    db.q("UPDATE users SET coins=coins-? WHERE user_id=?", (miktar, ctx.author.id))
    db.q("UPDATE users SET coins=coins+? WHERE user_id=?", (miktar, user.id))
    await ctx.send(embed=E("💸 TRANSFER", ctx.author.mention + " → " + user.mention + "\n**" + str(miktar) + " coin** gönderildi! ✅", C_ECO))

@bot.command(name="bahis", aliases=["bet"], help="<miktar> — Yazı tura bahsi (x2)")
@kategori("eco")
@commands.cooldown(1, 10, commands.BucketType.user)
async def bahis(ctx, miktar: int):
    if miktar <= 0: return await ctx.send(embed=E("❌", "Geçersiz miktar!", C_ERROR))
    me = db.one("SELECT coins FROM users WHERE user_id=?", (ctx.author.id,))
    if me["coins"] < miktar:
        return await ctx.send(embed=E("❌ YETERSİZ BAKİYE", "Sadece **" + str(me["coins"]) + "** coinin var!", C_ERROR))
    win = random.random() < 0.5
    db.q("UPDATE users SET coins=coins+? WHERE user_id=?", (miktar if win else -miktar, ctx.author.id))
    msg = "🎉 KAZANDIN! +" + str(miktar * 2) + " coin" if win else "😔 Kaybettin -" + str(miktar) + " coin"
    await ctx.send(embed=E("🎰 BAHİS SONUCU", "**" + msg + "**", C_ECO if win else C_ERROR))

@bot.command(name="market", aliases=["shop"], help="Market ürünlerini listeler")
@kategori("eco")
async def market(ctx):
    em = E("🛒 KATRE MARKET", "💎 Ürünler coin ile satın alınır!\n" + SEP, C_ECO)
    LINE(em, "💎 Pro Üyelik (30 gün)", "`50.000 coin` — k!destek")
    LINE(em, "🎨 Özel Rank Rengi", "`5.000 coin` — Pro gerekli")
    LINE(em, "⭐ +10 İtibar", "`2.500 coin` — k!destek")
    LINE(em, "🏷️ Özel Tag", "`7.500 coin` — Pro gerekli")
    v = View(); v.add_item(Button(label="Satın Al", url=SUPPORT_URL, style=discord.ButtonStyle.link, emoji="🛒"))
    await ctx.send(embed=em, view=v)

# ═══════════════════════════════════════════════════════════════════════════
# 🎮 EĞLENCE
# ═══════════════════════════════════════════════════════════════════════════
@bot.command(name="8ball", aliases=["ball"], help="<soru> — Sihirli top")
@kategori("fun")
async def eightball(ctx, *, soru):
    cev = ["✅ Evet, kesinlikle!", "🌟 Büyük ihtimalle evet", "🤔 Belki", "❌ Hayır",
           "💀 Kesinlikle hayır!", "🎯 Şansın yüksek", "😴 Bana sorma", "🔥 Evet evet evet!"]
    await ctx.send(embed=E("🎱 SORU: " + soru, "**Cevap:** " + random.choice(cev), C_FUN))

@bot.command(name="yazıtura", aliases=["yazitura", "coin"], help="Yazı tura atar")
@kategori("fun")
async def yazıtura(ctx):
    await ctx.send(embed=E("🪙 YAZI TURA", "**" + random.choice(["📝 YAZI", "🪙 TURA"]) + "**", C_FUN))

@bot.command(name="zar", aliases=["dice"], help="Zar atar (1-6)")
@kategori("fun")
async def zar(ctx):
    r = random.randint(1, 6)
    await ctx.send(embed=E("🎲 ZAR", ["⚀", "", "", "⚃", "⚄", ""][r - 1] + " Sonuç: **" + str(r) + "**", C_FUN))

@bot.command(name="aşk", aliases=["ask", "love"], help="<@üye> — Aşk ölçer")
@kategori("fun")
async def aşk(ctx, user: discord.Member):
    pct = random.randint(0, 100)
    msg = "💔 Yok bu iş..." if pct < 30 else ("💛 Fena değil!" if pct < 60 else ("💚 Güzel çift!" if pct < 85 else "❤️ RUH İKİZİ!"))
    await ctx.send(embed=E("💕 AŞK ÖLÇER",
        ctx.author.mention + " 💘 " + user.mention + "\n" + progress_bar(pct) + "\n" + msg, C_FUN))

@bot.command(name="slot", aliases=["slots"], help="Slot makinesi çevirir")
@kategori("fun")
async def slot(ctx):
    s = ["🍒", "", "", "💎", "7️⃣", ""]
    r = [random.choice(s) for _ in range(3)]
    win = len(set(r)) == 1
    msg = "🎉 JACKPOT! Üçlü eşleşme!" if win else "😔 Bu sefer olmadı..."
    await ctx.send(embed=E("🎰 SLOT MAKİNESİ", "┃ " + " ┃ ".join(r) + " ┃\n\n" + msg, C_PRO if win else C_FUN))

@bot.command(name="seç", aliases=["sec"], help="<a> <b> ... — Rastgele seçim")
@kategori("fun")
async def seç(ctx, *, seçenekler):
    opts = seçenekler.split()
    if len(opts) < 2: return await ctx.send(embed=E("❌", "En az 2 seçenek gir!", C_ERROR))
    await ctx.send(embed=E("🎯 RASTGELE SEÇİM", "Seçimim: **" + random.choice(opts) + "**", C_FUN))

# ═══════════════════════════════════════════════════════════════════════════
# 🎉 ÇEKİLİŞ (YETKİLİ HERKES — PRO GEREKMEZ)
# ═══════════════════════════════════════════════════════════════════════════
@bot.command(name="çekiliş", aliases=["cekilis", "giveaway"],
             help="<süre> <kazanan> <ödül> — Çekiliş başlatır (Yönetici)")
@kategori("give")
@commands.has_permissions(administrator=True)
async def çekiliş(ctx, süre: str, kazanan: int, *, ödül):
    try: dk = parse_sure(süre)
    except Exception:
        return await ctx.send(embed=E("❌ SÜRE HATASI", "Örnek: `k!çekiliş 60m 1 Nitro` • `2h` • `1d`", C_ERROR))
    if dk < 1 or kazanan < 1: return await ctx.send(embed=E("❌", "Geçersiz değerler!", C_ERROR))
    end = datetime.datetime.now() + datetime.timedelta(minutes=dk)
    em = E("🎉 ÇEKİLİŞ BAŞLADI! 🎉",
           "### 🎁 Ödül: **" + ödül + "**\n🔘 **KATIL** butonuna bas!\n" + SEP,
           C_GIVE, thumb=bot.user.display_avatar.url)
    LINE(em, "🏆 Kazanan", "`" + str(kazanan) + "` kişi", True)
    LINE(em, "👥 Katılımcı", "`0` kişi", True)
    LINE(em, "⏰ Bitiş", "<t:" + str(int(end.timestamp())) + ":R>", True)
    LINE(em, "📣 Başlatan", ctx.author.mention, True)
    msg = await ctx.send(embed=em, view=bot.gw_view)
    db.q("INSERT INTO giveaways(message_id,guild_id,channel_id,prize,winners,end_time,host) VALUES(?,?,?,?,?,?,?)",
         (msg.id, ctx.guild.id, ctx.channel.id, ödül, kazanan, end.timestamp(), ctx.author.id))

@bot.command(name="çekilişler", aliases=["cekilisler"], help="Aktif çekilişleri listeler")
@kategori("give")
async def çekilişler(ctx):
    rows = db.all("SELECT * FROM giveaways WHERE guild_id=? AND status='active'", (ctx.guild.id,))
    if not rows: return await ctx.send(embed=E("🎉", "Aktif çekiliş yok. `k!çekiliş` ile başlat!", C_WARN))
    em = E("🎉 AKTİF ÇEKİLİŞLER (" + str(len(rows)) + ")", color=C_GIVE)
    for g in rows:
        p = len(json.loads(g["participants"]))
        LINE(em, "🎁 " + g["prize"],
             "└ 👥 " + str(p) + " katılımcı • ⏰ <t:" + str(int(g["end_time"])) + ":R> • 🆔 `" + str(g["message_id"]) + "`")
    await ctx.send(embed=em)

@bot.command(name="çekilişbitir", aliases=["cekilisbitir"], help="<mesaj_id> — Çekilişi bitirir")
@kategori("give")
@commands.has_permissions(administrator=True)
async def çekilişbitir(ctx, mid: int):
    gw = db.one("SELECT * FROM giveaways WHERE message_id=? AND guild_id=?", (mid, ctx.guild.id))
    if not gw or gw["status"] != "active":
        return await ctx.send(embed=E("❌", "Aktif çekiliş bulunamadı!", C_ERROR))
    await finalize_giveaway(bot, mid)
    await ctx.send(embed=E("🏁", "Çekiliş sonlandırıldı!", C_OK))

# ═══════════════════════════════════════════════════════════════════════════
# 💎 PRO SİSTEMİ — 8 KOMUT!
# ═══════════════════════════════════════════════════════════════════════════
@bot.command(name="pro", aliases=["probilgi"], help="Pro durumunu ve ayrıcalıkları gösterir")
@kategori("pro")
async def pro(ctx, user: discord.Member = None):
    user = user or ctx.author
    ensure_user(user.id, str(user))
    u = db.one("SELECT * FROM users WHERE user_id=?", (user.id,))
    em = E("💎 KATRE PRO", color=C_PRO, thumb=user.display_avatar.url)
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
    await ctx.send(embed=em)

@bot.command(name="prooda", aliases=["proroom"], help="Özel ses odası oluşturur (PRO)")
@kategori("pro")
@is_pro()
async def prooda(ctx):
    cat = discord.utils.get(ctx.guild.categories, name="💎 PRO ODALAR")
    if not cat:
        cat = await ctx.guild.create_category("💎 PRO ODALAR")
        await cat.set_permissions(ctx.guild.default_role, view_channel=False)
    ch = await ctx.guild.create_voice_channel("👑 " + ctx.author.display_name, category=cat)
    await ch.set_permissions(ctx.author, connect=True, manage_channels=True, move_members=True)
    await ctx.send(embed=E("🎙️ PRO ODA HAZIR!", ch.mention + " odan oluşturuldu!\n🔑 Yönetim sende!", C_PRO))

@bot.command(name="prorenk", aliases=["procolor"], help="<hex> — Rank kartı rengi (PRO)")
@kategori("pro")
@is_pro()
async def prorenk(ctx, hexcode: str):
    hexcode = hexcode.lstrip("#")
    if len(hexcode) != 6:
        return await ctx.send(embed=E("❌", "Örnek: `k!prorenk ff0000`", C_ERROR))
    try: int(hexcode, 16)
    except ValueError:
        return await ctx.send(embed=E("❌", "Geçersiz hex kodu!", C_ERROR))
    db.q("UPDATE users SET pro_color=? WHERE user_id=?", (hexcode, ctx.author.id))
    await ctx.send(embed=E("🎨 RENK DEĞİŞTİ", "Rank kartı rengin: #" + hexcode.upper(), int(hexcode, 16)))

@bot.command(name="prostats", aliases=["proistatistik"], help="Detaylı kişisel istatistik (PRO)")
@kategori("pro")
@is_pro()
async def prostats(ctx):
    u = db.one("SELECT * FROM users WHERE user_id=?", (ctx.author.id,))
    em = E("📊 PRO İSTATİSTİK", color=C_PRO, thumb=ctx.author.display_avatar.url)
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
    await ctx.send(embed=em)

@bot.command(name="proyazı", aliases=["proyazi"], help="<metin> — Havalı yazı tipi (PRO)")
@kategori("pro")
@is_pro()
async def proyazı(ctx, *, metin):
    await ctx.send(embed=E("✒️ PRO YAZI", "𝗵𝗼𝘀: " + fancy(metin[:200]), C_PRO))

@bot.command(name="proembed", help="<başlık> | <açıklama> | <hex> — Özel embed (PRO)")
@kategori("pro")
@is_pro()
async def proembed(ctx, *, args):
    parts = [p.strip() for p in args.split("|")]
    if len(parts) < 2:
        return await ctx.send(embed=E("❌ KULLANIM", "Örnek: `k!proembed Duyuru | Merhaba! | ff0000`", C_ERROR))
    color = C_PRO
    if len(parts) >= 3:
        try: color = int(parts[2].lstrip("#"), 16)
        except ValueError: pass
    em = E(parts[0][:256], parts[1][:4000], color)
    em.set_footer(text="💎 " + ctx.author.display_name + " • PRO Embed")
    await ctx.send(embed=em)

@bot.command(name="protag", help="<metin> — Kişisel rozet tagi (PRO)")
@kategori("pro")
@is_pro()
async def protag(ctx, *, tag):
    tag = tag[:12]
    db.q("UPDATE users SET pro_tag=? WHERE user_id=?", (tag, ctx.author.id))
    await ctx.send(embed=E("🏷️ TAG AYARLANDI", "Rozetin: **" + tag + "**\nRank kartında ve profilinde görünecek!", C_PRO))

@bot.command(name="proxp", help="2x XP boost aç/kapat (PRO)")
@kategori("pro")
@is_pro()
async def proxp(ctx):
    u = db.one("SELECT xp2 FROM users WHERE user_id=?", (ctx.author.id,))
    new = 0 if u["xp2"] else 1
    db.q("UPDATE users SET xp2=? WHERE user_id=?", (new, ctx.author.id))
    msg = "**⚡ 2x XP AÇIK!** Mesaj başına çifte XP kazanıyorsun." if new else "**2x XP KAPALI.**"
    await ctx.send(embed=E("⚡ XP BOOST", msg, C_PRO))

# ═══════════════════════════════════════════════════════════════════════════
# 👑 OWNER PANELİ (OWNER OLMAYAN YANIT ALAMAZ — SESSİZ)
# ═══════════════════════════════════════════════════════════════════════════
@bot.command(name="sahip", aliases=["owner", "ownerpanel", "panel"], help="Owner panelini açar")
@kategori("owner")
@is_owner()
async def sahip(ctx):
    maint = db.one("SELECT maintenance FROM owner_settings WHERE id=1")["maintenance"]
    up = datetime.datetime.now() - bot.start_time
    members = sum(g.member_count or 0 for g in bot.guilds)
    em = E("👑 KATRE OWNER PANELİ",
           "### Hoş geldin Sayın Owner! 👋\n" + SEP +
           "\n🌐 Sunucu: `" + str(len(bot.guilds)) + "` • 👥 Kullanıcı: `" + str(members) + "`" +
           "\n⏱️ Uptime: `" + str(up).split(".")[0] + "` • 📡 Ping: `" + str(round(bot.latency * 1000)) + "ms`" +
           "\n🔧 Bakım Modu: **" + ("🔴 AÇIK" if maint else "🟢 KAPALI") + "**\n" + SEP +
           "\n**Komutlar:** `k!prover` `k!proal` `k!bakım` `k!prefix` `k!blacklist` `k!durum` `k!eval`",
           C_OWNER, thumb=bot.user.display_avatar.url)
    await ctx.send(embed=em, view=OwnerPanelView(bot))

@bot.command(name="prover", help="<@üye> [gün] — Pro üyelik verir")
@kategori("owner")
@is_owner()
async def prover(ctx, user: discord.Member, gun: int = 30):
    ensure_user(user.id, str(user))
    exp = (datetime.datetime.now() + datetime.timedelta(days=gun)).isoformat()
    db.q("UPDATE users SET pro=1, pro_expiry=? WHERE user_id=?", (exp, user.id))
    await ctx.send(embed=E("💎 PRO VERİLDİ",
        user.mention + " → **" + str(gun) + " gün** PRO!\n📅 Bitiş: `" +
        datetime.datetime.fromisoformat(exp).strftime("%d.%m.%Y") + "`", C_PRO))
    try: await user.send(embed=E("🎉 PRO OLDUN!", "**" + str(gun) + " gün** boyunca PRO ayrıcalıkları seninle! 💎", C_PRO))
    except Exception: pass

@bot.command(name="proal", help="<@üye> — Pro üyeliği geri alır")
@kategori("owner")
@is_owner()
async def proal(ctx, user: discord.Member):
    db.q("UPDATE users SET pro=0, pro_expiry=NULL WHERE user_id=?", (user.id,))
    await ctx.send(embed=E("💔 PRO ALINDI", user.mention + " üyesinin pro üyeliği sonlandırıldı.", C_WARN))

@bot.command(name="bakım", aliases=["bakim"], help="[aç/kapat] — Bakım modunu yönetir")
@kategori("owner")
@is_owner()
async def bakım(ctx, mod: str = None):
    cur = db.one("SELECT maintenance FROM owner_settings WHERE id=1")["maintenance"]
    new = (not cur) if mod is None else (mod.lower() in ("aç", "ac", "on", "1"))
    db.q("UPDATE owner_settings SET maintenance=? WHERE id=1", (int(new),))
    msg = "**🔴 AÇILDI** — Bot sadece sana yanıt veriyor!" if new else "**🟢 KAPATILDI** — Bot herkese açık!"
    await ctx.send(embed=E("🔧 BAKIM MODU", msg, C_WARN))

@bot.command(name="prefix", aliases=["önek"], help="<yeni prefix> — Sunucu prefixini değiştirir")
@kategori("owner")
@is_owner()
async def prefix(ctx, yeni: str):
    db.q("UPDATE servers SET prefix=? WHERE guild_id=?", (yeni, ctx.guild.id))
    await ctx.send(embed=E("✅ PREFIX", "Yeni prefix: `" + yeni + "` (büyük/küçük fark etmez)", C_OK))

@bot.command(name="blacklist", aliases=["bl"], help="<ekle/çıkar> <@üye> — Kara liste")
@kategori("owner")
@is_owner()
async def blacklist(ctx, işlem: str, user: discord.User, *, sebep="—"):
    if işlem.lower() in ("ekle", "add"):
        db.q("INSERT OR REPLACE INTO blacklist(user_id,reason) VALUES(?,?)", (user.id, sebep))
        await ctx.send(embed=E("🚫 KARALİSTE", user.mention + " kara listeye alındı!\n**Sebep:** " + sebep, C_ERROR))
    elif işlem.lower() in ("çıkar", "cikar", "remove"):
        db.q("DELETE FROM blacklist WHERE user_id=?", (user.id,))
        await ctx.send(embed=E("✅ KARALİSTE", user.mention + " kara listeden çıkarıldı.", C_OK))
    else:
        await ctx.send(embed=E("❌", "`k!blacklist ekle/çıkar @üye [sebep]`", C_ERROR))

@bot.command(name="durum", aliases=["status"], help="<metin> — Bot durumunu değiştirir")
@kategori("owner")
@is_owner()
async def durum(ctx, *, metin):
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name=metin))
    db.q("UPDATE owner_settings SET status_text=? WHERE id=1", (metin,))
    await ctx.send(embed=E("✅ DURUM", "Yeni durum: **" + metin + "**", C_OK))

@bot.command(name="sunucular", aliases=["guilds"], help="Botun tüm sunucularını listeler")
@kategori("owner")
@is_owner()
async def sunucular(ctx):
    rows = sorted(bot.guilds, key=lambda g: -(g.member_count or 0))
    em = E("🖥️ SUNUCULAR (" + str(len(rows)) + ")", color=C_OWNER)
    for i, g in enumerate(rows[:15], 1):
        LINE(em, "`" + str(i) + ".` " + g.name, "└ 👥 " + str(g.member_count) + " • 🆔 `" + str(g.id) + "`")
    await ctx.send(embed=em)

@bot.command(name="eval", aliases=["py"], help="<kod> — Python çalıştır (Owner)")
@kategori("owner")
@is_owner()
async def eval_cmd(ctx, *, code):
    env = {"bot": bot, "ctx": ctx, "db": db, "discord": discord,
           "guild": ctx.guild, "author": ctx.author, "channel": ctx.channel}
    buf = io.StringIO()
    func = "async def __f():\n" + textwrap.indent(code, "    ")   # ✅ DÜZELTİLDİ
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
