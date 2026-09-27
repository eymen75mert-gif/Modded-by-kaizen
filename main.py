import os
import re
import json
import random
import asyncio
import sqlite3
import time
from datetime import datetime, timedelta, timezone

import discord
from discord import app_commands
from discord.ext import commands, tasks

# ============================================================
# NOVA BOT | Tek dosyalı Discord botu
# Python 3.10+ | discord.py 2.4+
# Railway değişkenleri: DISCORD_TOKEN, OWNER_ID (isteğe bağlı)
# ============================================================

TOKEN = os.getenv("DISCORD_TOKEN", "").strip()
OWNER_ID = int(os.getenv("OWNER_ID", "0") or 0)
DB_PATH = os.getenv("DB_PATH", "nova_data.db")
PREFIX = "!"
COLOR = 0x7C4DFF
GREEN = 0x2ECC71
RED = 0xE74C3C
GOLD = 0xF1C40F

intents = discord.Intents.default()
intents.members = True
intents.message_content = True
intents.guilds = True
intents.moderation = True

bot = commands.Bot(command_prefix=commands.when_mentioned_or(PREFIX),
                   intents=intents, help_command=None)

db = sqlite3.connect(DB_PATH)
db.row_factory = sqlite3.Row
db.execute("""CREATE TABLE IF NOT EXISTS settings(
 guild_id INTEGER PRIMARY KEY, welcome_channel INTEGER, welcome_text TEXT,
 leave_channel INTEGER, leave_text TEXT, log_channel INTEGER, auto_role INTEGER,
 ticket_category INTEGER, ticket_panel INTEGER, ticket_staff INTEGER,
 ad_channel INTEGER, ad_text TEXT, automod INTEGER DEFAULT 1,
 bad_words TEXT DEFAULT '[]', anti_raid INTEGER DEFAULT 1,
 raid_limit INTEGER DEFAULT 8, raid_window INTEGER DEFAULT 10,
 giveaway_channel INTEGER)""")
db.execute("""CREATE TABLE IF NOT EXISTS warnings(
 id INTEGER PRIMARY KEY AUTOINCREMENT, guild_id INTEGER, user_id INTEGER,
 moderator_id INTEGER, reason TEXT, created_at INTEGER)""")
db.execute("""CREATE TABLE IF NOT EXISTS giveaways(
 message_id INTEGER PRIMARY KEY, guild_id INTEGER, channel_id INTEGER,
 prize TEXT, ends_at INTEGER, winners INTEGER, ended INTEGER DEFAULT 0)""")
db.execute("""CREATE TABLE IF NOT EXISTS tickets(
 channel_id INTEGER PRIMARY KEY, guild_id INTEGER, user_id INTEGER,
 status TEXT DEFAULT 'open', created_at INTEGER)""")
db.commit()

def setting(guild_id):
    row = db.execute("SELECT * FROM settings WHERE guild_id=?", (guild_id,)).fetchone()
    if row:
        return dict(row)
    db.execute("INSERT OR IGNORE INTO settings(guild_id) VALUES(?)", (guild_id,))
    db.commit()
    return dict(db.execute("SELECT * FROM settings WHERE guild_id=?", (guild_id,)).fetchone())

def update_setting(guild_id, **kwargs):
    setting(guild_id)
    for key, value in kwargs.items():
        db.execute(f"UPDATE settings SET {key}=? WHERE guild_id=?", (value, guild_id))
    db.commit()

def embed(title, description=None, color=COLOR):
    e = discord.Embed(title=title, description=description, color=color,
                      timestamp=datetime.now(timezone.utc))
    e.set_footer(text="NOVA • Gelişmiş Discord Botu", icon_url=bot.user.display_avatar.url if bot.user else None)
    return e

def is_owner():
    async def predicate(ctx):
        return ctx.author.id == OWNER_ID if OWNER_ID else ctx.author.guild_permissions.administrator
    return commands.check(predicate)

async def send_log(guild, title, description, color=COLOR):
    if not guild:
        return
    s = setting(guild.id)
    channel = guild.get_channel(s.get("log_channel") or 0)
    if channel:
        try:
            await channel.send(embed=embed(title, description, color))
        except discord.HTTPException:
            pass

def can_manage():
    async def predicate(interaction: discord.Interaction):
        return interaction.user.guild_permissions.manage_guild or (
            OWNER_ID and interaction.user.id == OWNER_ID)
    return app_commands.check(predicate)

class ConfirmView(discord.ui.View):
    def __init__(self, author_id, timeout=30):
        super().__init__(timeout=timeout)
        self.author_id = author_id
        self.value = None
    async def interaction_check(self, interaction):
        if interaction.user.id != self.author_id:
            await interaction.response.send_message("Bu buton sana ait değil.", ephemeral=True)
            return False
        return True
    @discord.ui.button(label="Onayla", style=discord.ButtonStyle.danger, emoji="✅")
    async def yes(self, interaction, button):
        self.value = True
        await interaction.response.edit_message(content="İşlem onaylandı.", view=None)
        self.stop()
    @discord.ui.button(label="İptal", style=discord.ButtonStyle.secondary, emoji="✖️")
    async def no(self, interaction, button):
        self.value = False
        await interaction.response.edit_message(content="İşlem iptal edildi.", view=None)
        self.stop()

class HelpView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=180)
        self.add_item(HelpSelect())
        self.add_item(discord.ui.Button(
            label="Davet / Bilgi", emoji="🔗", style=discord.ButtonStyle.link,
            url="https://discord.com/developers/applications"))

class HelpSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="Moderasyon", emoji="🛡️", value="mod", description="Ban, kick, timeout, uyarı"),
            discord.SelectOption(label="AutoMod", emoji="🤖", value="auto", description="Spam, reklam ve kelime filtresi"),
            discord.SelectOption(label="Hoş geldin", emoji="👋", value="welcome", description="Karşılama ve otomatik rol"),
            discord.SelectOption(label="Çekiliş", emoji="🎉", value="giveaway", description="Çekiliş başlatma ve yönetme"),
            discord.SelectOption(label="Eğlence", emoji="🎮", value="fun", description="Oyunlar ve eğlenceli komutlar"),
            discord.SelectOption(label="Ticket", emoji="🎫", value="ticket", description="Destek talebi sistemi"),
            discord.SelectOption(label="Koruma", emoji="🔒", value="protect", description="Anti-raid ve güvenlik"),
            discord.SelectOption(label="Yönetim", emoji="⚙️", value="manage", description="Ayarlar, duyuru ve reklam"),
        ]
        super().__init__(placeholder="Bir kategori seç...", min_values=1, max_values=1, options=options)
    async def callback(self, interaction):
        pages = {
          "mod": ("🛡️ Moderasyon", "`/ban` `/unban` `/kick` `/timeout` `/untimeout` `/uyar` `/uyarilar` `/uyarisil` `/temizle`"),
          "auto": ("🤖 AutoMod", "`/automod` `/kelimeekle` `/kelimesil` — Spam, davet ve reklam filtresi mesajlarda otomatik çalışır."),
          "welcome": ("👋 Hoş geldin", "`/hosgeldin` `/ayrilma` `/otorol` — Kanal ve mesaj ayarları."),
          "giveaway": ("🎉 Çekiliş", "`/cekilis` `/cekilisbitir` — Katıl butonlu çekiliş oluşturur."),
          "fun": ("🎮 Eğlence", "`/zar` `/yazitura` `/avatar` `/profil` `/sunucu` `/8top`"),
          "ticket": ("🎫 Ticket", "`/ticketpanel` — Destek paneli gönderir. Kullanıcılar butonla özel kanal açar."),
          "protect": ("🔒 Koruma", "`/antiraid` `/koruma` — Yeni hesap dalgası ve kanal/rol değişikliklerini loglar."),
          "manage": ("⚙️ Yönetim", "`/yardim` `/duyuru` `/reklam` `/logkanal` `/otorol`"),
        }
        title, desc = pages[self.values[0]]
        await interaction.response.edit_message(embed=embed(title, desc), view=self.view)

class GiveawayJoin(discord.ui.View):
    def __init__(self, message_id=None):
        super().__init__(timeout=None)
        self.message_id = message_id
    @discord.ui.button(label="Çekilişe Katıl", emoji="🎉", style=discord.ButtonStyle.success,
                       custom_id="nova:giveaway:join")
    async def join(self, interaction, button):
        row = db.execute("SELECT * FROM giveaways WHERE message_id=? AND ended=0",
                         (interaction.message.id,)).fetchone()
        if not row:
            return await interaction.response.send_message("Bu çekiliş sona ermiş.", ephemeral=True)
        users = bot.giveaway_users.setdefault(interaction.message.id, set())
        if interaction.user.id in users:
            users.remove(interaction.user.id)
            await interaction.response.send_message("Çekiliş katılımın kaldırıldı.", ephemeral=True)
        else:
            users.add(interaction.user.id)
            await interaction.response.send_message("Çekilişe katıldın! 🍀", ephemeral=True)

class TicketPanel(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
    @discord.ui.button(label="Destek Talebi Aç", emoji="🎫", style=discord.ButtonStyle.primary,
                       custom_id="nova:ticket:open")
    async def open_ticket(self, interaction, button):
        guild = interaction.guild
        if not guild:
            return await interaction.response.send_message("Bu panel sunucuda kullanılabilir.", ephemeral=True)
        existing = db.execute("SELECT channel_id FROM tickets WHERE guild_id=? AND user_id=? AND status='open'",
                              (guild.id, interaction.user.id)).fetchone()
        if existing and guild.get_channel(existing["channel_id"]):
            return await interaction.response.send_message(f"Açık talebin: <#{existing['channel_id']}>", ephemeral=True)
        s = setting(guild.id)
        category = guild.get_channel(s.get("ticket_category") or 0)
        staff = guild.get_role(s.get("ticket_staff") or 0)
        overwrites = {guild.default_role: discord.PermissionOverwrite(view_channel=False),
                      interaction.user: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True),
                      guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True, manage_channels=True)}
        if staff:
            overwrites[staff] = discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True)
        safe_name = re.sub(r"[^a-z0-9-]", "", interaction.user.name.lower().replace(" ", "-"))[:18] or "uye"
        channel = await guild.create_text_channel(f"ticket-{safe_name}", category=category if isinstance(category, discord.CategoryChannel) else None,
                                                  overwrites=overwrites, reason="Ticket açıldı")
        db.execute("INSERT OR REPLACE INTO tickets(channel_id,guild_id,user_id,status,created_at) VALUES(?,?,?,'open',?)",
                   (channel.id, guild.id, interaction.user.id, int(time.time())))
        db.commit()
        view = TicketClose()
        await channel.send(content=f"{interaction.user.mention} {staff.mention if staff else ''}",
                           embed=embed("🎫 Destek Talebin Açıldı", "Talebini ayrıntılı şekilde yaz. Yetkililer en kısa sürede yardımcı olacaktır."),
                           view=view)
        await interaction.response.send_message(f"Talebin oluşturuldu: {channel.mention}", ephemeral=True)

class TicketClose(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
    @discord.ui.button(label="Talebi Kapat", emoji="🔒", style=discord.ButtonStyle.danger,
                       custom_id="nova:ticket:close")
    async def close(self, interaction, button):
        row = db.execute("SELECT * FROM tickets WHERE channel_id=? AND status='open'",
                         (interaction.channel.id,)).fetchone()
        if not row:
            return await interaction.response.send_message("Bu kanal açık bir ticket değil.", ephemeral=True)
        if interaction.user.id != row["user_id"] and not interaction.user.guild_permissions.manage_channels:
            return await interaction.response.send_message("Bu talebi kapatma yetkin yok.", ephemeral=True)
        db.execute("UPDATE tickets SET status='closed' WHERE channel_id=?", (interaction.channel.id,))
        db.commit()
        await interaction.response.send_message("🔒 Ticket kapatılıyor...")
        await asyncio.sleep(3)
        await interaction.channel.delete(reason="Ticket kapatıldı")

@bot.event
async def on_ready():
    bot.giveaway_users = getattr(bot, "giveaway_users", {})
    if not getattr(bot, "_synced", False):
        bot.add_view(TicketPanel())
        bot.add_view(TicketClose())
        bot.add_view(GiveawayJoin())
        try:
            synced = await bot.tree.sync()
            print(f"{len(synced)} slash komutu senkronize edildi.")
        except Exception as e:
            print("Komut senkronizasyon hatası:", e)
        bot._synced = True
    if not giveaway_loop.is_running():
        giveaway_loop.start()
    print(f"{bot.user} aktif!")

@bot.event
async def on_member_join(member):
    s = setting(member.guild.id)
    if s.get("auto_role"):
        role = member.guild.get_role(s["auto_role"])
        if role:
            try: await member.add_roles(role, reason="Otomatik rol")
            except discord.HTTPException: pass
    ch = member.guild.get_channel(s.get("welcome_channel") or 0)
    if ch:
        msg = s.get("welcome_text") or "🎉 {user} aramıza katıldı! Sunucuda artık **{count}.** kişiyiz."
        try:
            await ch.send(msg.replace("{user}", member.mention).replace("{count}", str(member.guild.member_count)))
        except discord.HTTPException: pass
    await send_log(member.guild, "👋 Yeni üye", f"{member.mention} sunucuya katıldı. Hesap: <t:{int(member.created_at.timestamp())}:R>")

@bot.event
async def on_member_remove(member):
    s = setting(member.guild.id)
    ch = member.guild.get_channel(s.get("leave_channel") or 0)
    if ch:
        msg = s.get("leave_text") or "👋 **{name}** sunucudan ayrıldı."
        try: await ch.send(msg.replace("{name}", discord.utils.escape_markdown(member.name)))
        except discord.HTTPException: pass
    await send_log(member.guild, "🚪 Üye ayrıldı", f"{member} sunucudan ayrıldı.", RED)

@bot.event
async def on_message(message):
    if message.author.bot or not message.guild:
        return await bot.process_commands(message)
    s = setting(message.guild.id)
    if s.get("automod", 1) and not message.author.guild_permissions.manage_messages:
        content = message.content.lower()
        words = json.loads(s.get("bad_words") or "[]")
        invite = re.search(r"(discord\.gg/|discord\.com/invite/)", content)
        spam = len(message.content) > 1500 or (len(message.content) > 8 and len(set(message.content)) <= 3)
        bad = next((w for w in words if w.lower() in content), None)
        if invite or spam or bad:
            try:
                await message.delete()
                await message.channel.send(f"{message.author.mention} mesajın AutoMod tarafından kaldırıldı. ⚠️", delete_after=5)
                await send_log(message.guild, "🤖 AutoMod", f"{message.author.mention} mesajı kaldırıldı. Sebep: {'davet bağlantısı' if invite else 'spam' if spam else 'yasaklı kelime'}", GOLD)
            except discord.HTTPException: pass
            return
    await bot.process_commands(message)

@bot.event
async def on_guild_channel_delete(channel):
    await send_log(channel.guild, "🧱 Kanal silindi", f"**{channel.name}** kanalı silindi.", RED)

@bot.event
async def on_guild_role_delete(role):
    await send_log(role.guild, "🎭 Rol silindi", f"**{role.name}** rolü silindi.", RED)

@bot.event
async def on_member_ban(guild, user):
    await send_log(guild, "🔨 Üye yasaklandı", f"{user} sunucudan yasaklandı.", RED)

# ---------- Moderasyon ----------
@bot.tree.command(name="ban", description="Bir üyeyi sunucudan yasaklar.")
@app_commands.checks.has_permissions(ban_members=True)
async def ban(interaction: discord.Interaction, uye: discord.Member, sebep: str="Belirtilmedi"):
    await uye.ban(reason=f"{interaction.user}: {sebep}")
    await interaction.response.send_message(embed=embed("🔨 Ban uygulandı", f"{uye.mention} yasaklandı.\n**Sebep:** {sebep}", RED), ephemeral=True)

@bot.tree.command(name="unban", description="Kullanıcı ID'si ile ban kaldırır.")
@app_commands.checks.has_permissions(ban_members=True)
async def unban(interaction: discord.Interaction, kullanici_id: str):
    try:
        user = await bot.fetch_user(int(kullanici_id))
        await interaction.guild.unban(user, reason=f"{interaction.user} tarafından")
        await interaction.response.send_message(embed=embed("✅ Ban kaldırıldı", f"{user} artık yasaklı değil.", GREEN), ephemeral=True)
    except (ValueError, discord.NotFound):
        await interaction.response.send_message("Geçerli bir kullanıcı ID'si bulunamadı.", ephemeral=True)

@bot.tree.command(name="kick", description="Bir üyeyi sunucudan atar.")
@app_commands.checks.has_permissions(kick_members=True)
async def kick(interaction: discord.Interaction, uye: discord.Member, sebep: str="Belirtilmedi"):
    await uye.kick(reason=f"{interaction.user}: {sebep}")
    await interaction.response.send_message(embed=embed("👢 Üye atıldı", f"{uye} sunucudan atıldı.\n**Sebep:** {sebep}", RED), ephemeral=True)

@bot.tree.command(name="timeout", description="Üyeye süreli susturma uygular (dakika).")
@app_commands.checks.has_permissions(moderate_members=True)
async def timeout(interaction: discord.Interaction, uye: discord.Member, dakika: app_commands.Range[int,1,40320], sebep: str="Belirtilmedi"):
    await uye.timeout(timedelta(minutes=dakika), reason=f"{interaction.user}: {sebep}")
    await interaction.response.send_message(embed=embed("🔇 Timeout uygulandı", f"{uye.mention} • {dakika} dakika\n**Sebep:** {sebep}", GOLD), ephemeral=True)

@bot.tree.command(name="untimeout", description="Üyenin timeout cezasını kaldırır.")
@app_commands.checks.has_permissions(moderate_members=True)
async def untimeout(interaction: discord.Interaction, uye: discord.Member):
    await uye.timeout(None, reason=f"{interaction.user} tarafından kaldırıldı")
    await interaction.response.send_message(embed=embed("🔊 Timeout kaldırıldı", uye.mention, GREEN), ephemeral=True)

@bot.tree.command(name="uyar", description="Üyeye uyarı verir.")
@app_commands.checks.has_permissions(moderate_members=True)
async def uyar(interaction: discord.Interaction, uye: discord.Member, sebep: str):
    db.execute("INSERT INTO warnings(guild_id,user_id,moderator_id,reason,created_at) VALUES(?,?,?,?,?)",
               (interaction.guild.id, uye.id, interaction.user.id, sebep, int(time.time())))
    db.commit()
    await interaction.response.send_message(embed=embed("⚠️ Uyarı kaydedildi", f"{uye.mention}\n**Sebep:** {sebep}", GOLD), ephemeral=True)
    await send_log(interaction.guild, "⚠️ Üye uyarıldı", f"{uye.mention} • {sebep}", GOLD)

@bot.tree.command(name="uyarilar", description="Üyenin uyarı geçmişini gösterir.")
@app_commands.checks.has_permissions(moderate_members=True)
async def uyarilar(interaction: discord.Interaction, uye: discord.Member):
    rows = db.execute("SELECT reason,created_at FROM warnings WHERE guild_id=? AND user_id=? ORDER BY id DESC LIMIT 10",
                      (interaction.guild.id, uye.id)).fetchall()
    desc = "\n".join(f"• <t:{r['created_at']}:d> — {discord.utils.escape_markdown(r['reason'])}" for r in rows) or "Uyarı bulunamadı."
    await interaction.response.send_message(embed=embed(f"📋 {uye} • Uyarılar", desc), ephemeral=True)

@bot.tree.command(name="uyarisil", description="Üyenin tüm uyarılarını siler.")
@app_commands.checks.has_permissions(moderate_members=True)
async def uyarisil(interaction: discord.Interaction, uye: discord.Member):
    cur = db.execute("DELETE FROM warnings WHERE guild_id=? AND user_id=?", (interaction.guild.id, uye.id))
    db.commit()
    await interaction.response.send_message(embed=embed("🧹 Uyarılar silindi", f"{uye.mention} için {cur.rowcount} kayıt silindi.", GREEN), ephemeral=True)

@bot.tree.command(name="temizle", description="Kanaldan belirtilen sayıda mesaj siler.")
@app_commands.checks.has_permissions(manage_messages=True)
async def temizle(interaction: discord.Interaction, adet: app_commands.Range[int,1,100]):
    await interaction.response.defer(ephemeral=True)
    deleted = await interaction.channel.purge(limit=adet)
    await interaction.followup.send(embed=embed("🧹 Temizlik tamamlandı", f"**{len(deleted)}** mesaj silindi.", GREEN), ephemeral=True)

# ---------- Ayarlar / AutoMod ----------
@bot.tree.command(name="automod", description="Otomatik mesaj denetimini açar veya kapatır.")
@app_commands.checks.has_permissions(manage_guild=True)
async def automod(interaction: discord.Interaction, aktif: bool):
    update_setting(interaction.guild.id, automod=int(aktif))
    await interaction.response.send_message(embed=embed("🤖 AutoMod ayarlandı", f"Durum: {'Açık ✅' if aktif else 'Kapalı ❌'}"), ephemeral=True)

@bot.tree.command(name="kelimeekle", description="AutoMod yasaklı kelime listesine kelime ekler.")
@app_commands.checks.has_permissions(manage_guild=True)
async def kelimeekle(interaction: discord.Interaction, kelime: str):
    s = setting(interaction.guild.id); words = json.loads(s.get("bad_words") or "[]")
    if kelime.lower() not in [w.lower() for w in words]: words.append(kelime.lower())
    update_setting(interaction.guild.id, bad_words=json.dumps(words, ensure_ascii=False))
    await interaction.response.send_message(f"✅ `{kelime}` filtre listesine eklendi.", ephemeral=True)

@bot.tree.command(name="kelimesil", description="Yasaklı kelimeyi listeden çıkarır.")
@app_commands.checks.has_permissions(manage_guild=True)
async def kelimesil(interaction: discord.Interaction, kelime: str):
    s = setting(interaction.guild.id); words = json.loads(s.get("bad_words") or "[]")
    words = [w for w in words if w.lower() != kelime.lower()]
    update_setting(interaction.guild.id, bad_words=json.dumps(words, ensure_ascii=False))
    await interaction.response.send_message(f"✅ `{kelime}` listeden çıkarıldı.", ephemeral=True)

@bot.tree.command(name="hosgeldin", description="Karşılama kanalını ve mesajını ayarlar.")
@app_commands.checks.has_permissions(manage_guild=True)
async def hosgeldin(interaction: discord.Interaction, kanal: discord.TextChannel, mesaj: str="🎉 {user} aramıza katıldı! Sunucuda {count}. kişisin."):
    update_setting(interaction.guild.id, welcome_channel=kanal.id, welcome_text=mesaj)
    await interaction.response.send_message(embed=embed("👋 Hoş geldin ayarlandı", f"Kanal: {kanal.mention}\nDeğişkenler: `{{user}}`, `{{count}}`"), ephemeral=True)

@bot.tree.command(name="ayrilma", description="Ayrılma mesajı kanalını ayarlar.")
@app_commands.checks.has_permissions(manage_guild=True)
async def ayrilma(interaction: discord.Interaction, kanal: discord.TextChannel, mesaj: str="👋 {name} sunucudan ayrıldı."):
    update_setting(interaction.guild.id, leave_channel=kanal.id, leave_text=mesaj)
    await interaction.response.send_message(embed=embed("🚪 Ayrılma mesajı ayarlandı", kanal.mention), ephemeral=True)

@bot.tree.command(name="otorol", description="Yeni üyelere verilecek otomatik rolü ayarlar.")
@app_commands.checks.has_permissions(manage_guild=True)
async def otorol(interaction: discord.Interaction, rol: discord.Role):
    update_setting(interaction.guild.id, auto_role=rol.id)
    await interaction.response.send_message(embed=embed("🎭 Otorol ayarlandı", f"Yeni üyelere {rol.mention} verilecek."), ephemeral=True)

@bot.tree.command(name="logkanal", description="Moderatör ve koruma log kanalını ayarlar.")
@app_commands.checks.has_permissions(manage_guild=True)
async def logkanal(interaction: discord.Interaction, kanal: discord.TextChannel):
    update_setting(interaction.guild.id, log_channel=kanal.id)
    await interaction.response.send_message(embed=embed("🧾 Log kanalı ayarlandı", kanal.mention), ephemeral=True)

# ---------- Çekiliş ----------
@bot.tree.command(name="cekilis", description="Butonlu çekiliş başlatır.")
@app_commands.checks.has_permissions(manage_guild=True)
async def cekilis(interaction: discord.Interaction, sure_dakika: app_commands.Range[int,1,10080], kazanan: app_commands.Range[int,1,20], odul: str, kanal: discord.TextChannel=None):
    ch = kanal or interaction.channel
    ends = int(time.time()) + sure_dakika * 60
    e = embed("🎉 ÇEKİLİŞ BAŞLADI!", f"🎁 **Ödül:** {odul}\n🏆 **Kazanan:** {kazanan}\n⏳ **Bitiş:** <t:{ends}:R>\n\nKatılmak için aşağıdaki butona bas!")
    msg = await ch.send(embed=e, view=GiveawayJoin())
    db.execute("INSERT OR REPLACE INTO giveaways(message_id,guild_id,channel_id,prize,ends_at,winners,ended) VALUES(?,?,?,?,?,?,0)",
               (msg.id, interaction.guild.id, ch.id, odul, ends, kazanan))
    db.commit()
    bot.giveaway_users[msg.id] = set()
    await interaction.response.send_message(f"✅ Çekiliş oluşturuldu: {msg.jump_url}", ephemeral=True)

@bot.tree.command(name="cekilisbitir", description="Bir çekilişi hemen bitirir.")
@app_commands.checks.has_permissions(manage_guild=True)
async def cekilisbitir(interaction: discord.Interaction, mesaj_id: str):
    await interaction.response.defer(ephemeral=True)
    await end_giveaway(int(mesaj_id), force=True)
    await interaction.followup.send("Çekiliş bitirme işlemi tamamlandı.", ephemeral=True)

async def end_giveaway(message_id, force=False):
    row = db.execute("SELECT * FROM giveaways WHERE message_id=? AND ended=0", (message_id,)).fetchone()
    if not row or (not force and row["ends_at"] > int(time.time())):
        return
    users = list(getattr(bot, "giveaway_users", {}).get(message_id, set()))
    winners = random.sample(users, min(len(users), row["winners"])) if users else []
    db.execute("UPDATE giveaways SET ended=1 WHERE message_id=?", (message_id,)); db.commit()
    channel = bot.get_channel(row["channel_id"])
    if channel:
        try:
            msg = await channel.fetch_message(message_id)
            await msg.edit(embed=embed("🎊 ÇEKİLİŞ SONA ERDİ", f"🎁 **Ödül:** {row['prize']}\n🏆 **Kazanan(lar):** {', '.join(f'<@{u}>' for u in winners) if winners else 'Katılımcı bulunamadı.'}", GREEN), view=None)
            if winners: await channel.send(f"🎉 Tebrikler: {', '.join(f'<@{u}>' for u in winners)}! **{row['prize']}** kazandınız.")
        except discord.HTTPException: pass

@tasks.loop(seconds=20)
async def giveaway_loop():
    rows = db.execute("SELECT message_id FROM giveaways WHERE ended=0 AND ends_at<=?", (int(time.time()),)).fetchall()
    for r in rows:
        await end_giveaway(r["message_id"])

# ---------- Ticket ----------
@bot.tree.command(name="ticketpanel", description="Butonlu ticket paneli gönderir.")
@app_commands.checks.has_permissions(manage_guild=True)
async def ticketpanel(interaction: discord.Interaction, kanal: discord.TextChannel, kategori: discord.CategoryChannel=None, yetkili_rol: discord.Role=None):
    update_setting(interaction.guild.id, ticket_category=kategori.id if kategori else None,
                   ticket_staff=yetkili_rol.id if yetkili_rol else None, ticket_panel=kanal.id)
    await kanal.send(embed=embed("🎫 Destek Merkezi", "Yardıma mı ihtiyacın var? Aşağıdaki butona basarak özel destek talebi oluşturabilirsin."), view=TicketPanel())
    await interaction.response.send_message("✅ Ticket paneli gönderildi.", ephemeral=True)

# ---------- Koruma ----------
@bot.tree.command(name="antiraid", description="Anti-raid katılım korumasını açar/kapatır.")
@app_commands.checks.has_permissions(manage_guild=True)
async def antiraid(interaction: discord.Interaction, aktif: bool, limit: app_commands.Range[int,2,30]=8, saniye: app_commands.Range[int,5,60]=10):
    update_setting(interaction.guild.id, anti_raid=int(aktif), raid_limit=limit, raid_window=saniye)
    await interaction.response.send_message(embed=embed("🔒 Anti-raid ayarlandı", f"Durum: {'Açık' if aktif else 'Kapalı'}\nLimit: {limit} üye / {saniye} saniye"), ephemeral=True)

@bot.tree.command(name="koruma", description="Sunucu koruma sisteminin durumunu gösterir.")
@app_commands.checks.has_permissions(manage_guild=True)
async def koruma(interaction: discord.Interaction):
    s = setting(interaction.guild.id)
    await interaction.response.send_message(embed=embed("🔐 Koruma Durumu", f"AutoMod: {'🟢 Açık' if s['automod'] else '🔴 Kapalı'}\nAnti-raid: {'🟢 Açık' if s['anti_raid'] else '🔴 Kapalı'}\nLog: <#{s['log_channel']}>" if s['log_channel'] else f"AutoMod: {'🟢 Açık' if s['automod'] else '🔴 Kapalı'}\nAnti-raid: {'🟢 Açık' if s['anti_raid'] else '🔴 Kapalı'}\nLog: Ayarlanmamış"), ephemeral=True)

raid_joins = {}
@bot.event
async def on_member_join_protection(member):
    pass

# ---------- Eğlence ----------
@bot.tree.command(name="zar", description="Zar atar.")
async def zar(interaction: discord.Interaction):
    await interaction.response.send_message(embed=embed("🎲 Zar Atıldı", f"{interaction.user.mention} **{random.randint(1,6)}** attı!"))

@bot.tree.command(name="yazitura", description="Yazı tura atar.")
async def yazitura(interaction: discord.Interaction):
    await interaction.response.send_message(embed=embed("🪙 Yazı Tura", random.choice(["🟡 **Yazı!**", "⚪ **Tura!**"])))

@bot.tree.command(name="8top", description="Soruna rastgele cevap verir.")
async def sekiztop(interaction: discord.Interaction, soru: str):
    await interaction.response.send_message(embed=embed("🎱 8 Top", f"**Soru:** {soru}\n**Cevap:** {random.choice(['Kesinlikle evet.','Büyük ihtimalle.','Bunu zaman gösterecek.','Şu an söyleyemem.','Pek sanmıyorum.','Kesinlikle hayır.'])}"))

@bot.tree.command(name="avatar", description="Üyenin avatarını gösterir.")
async def avatar(interaction: discord.Interaction, uye: discord.User=None):
    user = uye or interaction.user
    e = embed(f"🖼️ {user} • Avatar")
    e.set_image(url=user.display_avatar.url)
    await interaction.response.send_message(embed=e)

@bot.tree.command(name="profil", description="Üyenin profil bilgilerini gösterir.")
async def profil(interaction: discord.Interaction, uye: discord.Member=None):
    m = uye or interaction.user
    e = embed(f"👤 {m.display_name} • Profil", f"**Kullanıcı:** {m.mention}\n**ID:** `{m.id}`\n**Katılım:** <t:{int(m.joined_at.timestamp())}:R>\n**Hesap:** <t:{int(m.created_at.timestamp())}:R>\n**En üst rol:** {m.top_role.mention}")
    e.set_thumbnail(url=m.display_avatar.url)
    await interaction.response.send_message(embed=e)

@bot.tree.command(name="sunucu", description="Sunucu bilgilerini gösterir.")
async def sunucu(interaction: discord.Interaction):
    g = interaction.guild
    e = embed(f"🏰 {g.name}", f"👥 Üye: **{g.member_count}**\n🎭 Rol: **{len(g.roles)}**\n💬 Metin kanalı: **{len(g.text_channels)}**\n🔊 Ses kanalı: **{len(g.voice_channels)}**\n📅 Kuruluş: <t:{int(g.created_at.timestamp())}:D>")
    if g.icon: e.set_thumbnail(url=g.icon.url)
    await interaction.response.send_message(embed=e)

# ---------- Yönetim ----------
@bot.tree.command(name="yardim", description="Butonlu ve kategorili yardım menüsünü açar.")
async def yardim(interaction: discord.Interaction):
    e = embed("✨ NOVA • Komut Merkezi", "Aşağıdaki menüden bir kategori seçerek komutları görüntüleyebilirsin.\n\n🛡️ Moderasyon  •  🤖 AutoMod  •  👋 Hoş geldin\n🎉 Çekiliş  •  🎮 Eğlence  •  🎫 Ticket\n🔒 Koruma  •  ⚙️ Yönetim")
    await interaction.response.send_message(embed=e, view=HelpView(), ephemeral=True)

@bot.tree.command(name="duyuru", description="Embed biçiminde duyuru gönderir.")
@app_commands.checks.has_permissions(manage_guild=True)
async def duyuru(interaction: discord.Interaction, kanal: discord.TextChannel, baslik: str, mesaj: str):
    await kanal.send(embed=embed(f"📢 {baslik}", mesaj, GOLD))
    await interaction.response.send_message("✅ Duyuru gönderildi.", ephemeral=True)

@bot.tree.command(name="reklam", description="Sunucu reklamını ayarlı kanala gönderir.")
@app_commands.checks.has_permissions(manage_guild=True)
async def reklam(interaction: discord.Interaction, davet: str, aciklama: str):
    if not re.match(r"^https?://", davet):
        return await interaction.response.send_message("Geçerli bir https:// bağlantısı gir.", ephemeral=True)
    e = embed("📣 SUNUCU TANITIMI", f"{aciklama}\n\n🔗 **Davet:** {davet}", GOLD)
    await interaction.channel.send(embed=e)
    await interaction.response.send_message("✅ Reklam mesajı gönderildi.", ephemeral=True)

@bot.tree.command(name="botbilgi", description="Botun çalışma bilgilerini gösterir.")
async def botbilgi(interaction: discord.Interaction):
    e = embed("🤖 NOVA • Bot Bilgisi", f"**Sürüm:** 1.0\n**Kütüphane:** discord.py {discord.__version__}\n**Ping:** {round(bot.latency*1000)} ms\n**Sunucu:** {len(bot.guilds)}")
    await interaction.response.send_message(embed=e, ephemeral=True)

@bot.tree.error
async def on_app_command_error(interaction, error):
    err = getattr(error, "original", error)
    if isinstance(err, app_commands.MissingPermissions):
        msg = "❌ Bu komut için gerekli yetkiye sahip değilsin."
    elif isinstance(err, app_commands.BotMissingPermissions):
        msg = "❌ Botun gerekli Discord yetkileri eksik."
    elif isinstance(err, app_commands.CommandOnCooldown):
        msg = "⏳ Çok hızlı denedin, biraz bekle."
    else:
        print("Slash komut hatası:", repr(err))
        msg = "⚠️ İşlem sırasında hata oluştu. Bot izinlerini ve komut girdilerini kontrol et."
    try:
        if interaction.response.is_done():
            await interaction.followup.send(msg, ephemeral=True)
        else:
            await interaction.response.send_message(msg, ephemeral=True)
    except discord.HTTPException:
        pass

if __name__ == "__main__":
    if not TOKEN:
        raise SystemExit("DISCORD_TOKEN ortam değişkeni tanımlı değil.")
    bot.run(TOKEN)
