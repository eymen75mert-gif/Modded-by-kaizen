# -*- coding: utf-8 -*-
"""
============================================================
   ÇOK MODÜLLÜ DISCORD BOTU (Tek Dosya - main.py)
============================================================
Modüller (hepsi buton/emoji/menü destekli):
  - Moderasyon   (kick/ban artık ✅/🛑 onay butonlu, mute, warn, purge...)
  - Automod      (yasaklı kelime, link/davet filtresi, spam engeli)
  - Hoşgeldin    (hoşgeldin/ayrılış mesajları, otomatik rol)
  - Çekiliş      (🎉 butonlu katılım, canlı katılımcı sayacı)
  - Eğlence      (8ball, zar, yazı-tura, şaka, soru, 🪨📄✂️ taş-kağıt-makas)
  - Ticket       (🎫🛠️⚠️💡💰 kategori seçmeli açılır menü ile destek sistemi)
  - Koruma       (anti-raid, hesap yaşı kontrolü, spam koruması)
  - Yönetim      (sunucu/kullanıcı bilgisi, rol verme, 🎭 buton ile kendinden rol,
                   📖 açılır menülü yardım paneli)
  - Reklam       (📢 oy butonlu reklam kanalı, 🔔 Disboard bump hatırlatıcı,
                   🏆 davet takip/liderlik sistemi)

Kurulum:
  pip install -U discord.py

Çalıştırma:
  1) Aşağıdaki TOKEN değişkenine bot tokenini yaz
     ya da ortam değişkeni olarak DISCORD_TOKEN ver.
  2) Discord Developer Portal > Bot sekmesinden
     "Server Members Intent" ve "Message Content Intent" aç.
  3) python bot.py
============================================================
"""

import discord
from discord.ext import commands, tasks
import json
import os
import re
import random
import asyncio
import datetime

# ================= AYARLAR =================
TOKEN = os.getenv("DISCORD_TOKEN", "BURAYA_BOT_TOKENINI_YAZ")
PREFIX = "!"
DATA_FILE = "data.json"

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix=PREFIX, intents=intents, help_command=None)

# ================= VERİ YÖNETİMİ =================
def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError:
            return {}
    return {}


data = load_data()


def save_data():
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


def gd(guild_id: int):
    """Sunucuya ait ayar verisini getirir, yoksa oluşturur."""
    gid = str(guild_id)
    if gid not in data:
        data[gid] = {
            "welcome_channel": None,
            "welcome_message": "Sunucuya hoş geldin {mention}! Şu an **{membercount}.** üyeyiz. 🎉",
            "leave_channel": None,
            "leave_message": "**{user}** sunucudan ayrıldı. 👋",
            "autorole": None,
            "log_channel": None,
            "automod": {
                "enabled": False,
                "banned_words": [],
                "anti_invite": False,
                "anti_link": False,
                "anti_spam": False,
            },
            "protection": {
                "anti_raid": False,
                "min_account_age_days": 0,
            },
            "warns": {},
            "ticket_category": None,
            "ticket_log_channel": None,
            "giveaways": {},
            "selfroles": [],
            "ad_channel": None,
            "ad_cooldown_minutes": 60,
            "ad_last_used": {},
            "bump_channel": None,
            "bump_role": None,
            "next_bump_time": None,
            "invite_counts": {},
        }
        save_data()
    return data[gid]


# Bellek içi (kalıcı olmayan) takip verileri
spam_tracker = {}      # {user_id: [timestamps]}
join_tracker = {}      # {guild_id: [timestamps]} - anti raid için
invite_cache = {}      # {guild_id: {invite_code: uses}} - davet takibi için
ad_votes = {}          # {message_id: {"like": set(user_id), "dislike": set(user_id)}} - reklam oyları

DISBOARD_ID = 302050872383242240  # Disboard bot ID'si (bump algılama için)

INVITE_REGEX = re.compile(r"(discord\.gg/|discordapp\.com/invite/|discord\.com/invite/)", re.IGNORECASE)
LINK_REGEX = re.compile(r"(https?://|www\.)", re.IGNORECASE)


def is_mod():
    async def predicate(ctx: commands.Context):
        return ctx.author.guild_permissions.manage_guild or ctx.author.guild_permissions.administrator
    return commands.check(predicate)


def is_admin():
    async def predicate(ctx: commands.Context):
        return ctx.author.guild_permissions.administrator
    return commands.check(predicate)


# ================================================================
#                           EVENTLER
# ================================================================
@bot.event
async def on_ready():
    print(f"[+] Giriş yapıldı: {bot.user} ({bot.user.id})")
    print(f"[+] {len(bot.guilds)} sunucuda aktif.")

    # --- Kalıcı (persistent) buton/menü görünümlerini yeniden bağla ---
    bot.add_view(TicketPanelView())
    bot.add_view(TicketCloseView())

    for guild in bot.guilds:
        g = gd(guild.id)

        # Kendinden rol panelleri
        if g.get("selfroles"):
            bot.add_view(SelfRoleView(guild.id))

        # Aktif çekilişlerin butonlarını yeniden bağla
        for message_id, gw in g.get("giveaways", {}).items():
            if not gw.get("ended"):
                count = len(gw.get("participants", []))
                try:
                    bot.add_view(GiveawayView(message_id, count), message_id=int(message_id))
                except (discord.NotFound, discord.HTTPException, ValueError):
                    pass

        # Davet takibi için mevcut davetleri önbelleğe al
        try:
            invites = await guild.invites()
            invite_cache[guild.id] = {inv.code: inv.uses for inv in invites}
        except (discord.Forbidden, discord.HTTPException):
            invite_cache[guild.id] = {}

    if not check_giveaways.is_running():
        check_giveaways.start()
    if not check_bumps.is_running():
        check_bumps.start()
    await bot.change_presence(activity=discord.Game(name=f"{PREFIX}yardim | 🔘 Buton Menülü Bot"))


@bot.event
async def on_command_error(ctx: commands.Context, error):
    if isinstance(error, commands.CommandNotFound):
        return
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("❌ Bu komutu kullanmak için yetkin yok.")
        return
    if isinstance(error, commands.CheckFailure):
        await ctx.send("❌ Bu komutu kullanmak için yetkin yok.")
        return
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f"❌ Eksik parametre: `{error.param.name}`. `{PREFIX}yardim` yazarak kullanımı görebilirsin.")
        return
    if isinstance(error, commands.BadArgument):
        await ctx.send("❌ Geçersiz parametre girdin. Bahsetme (mention), ID veya sayı kontrolü yap.")
        return
    print(f"[HATA] {ctx.command}: {error}")
    await ctx.send(f"⚠️ Beklenmeyen bir hata oluştu: `{error}`")


@bot.event
async def on_invite_create(invite: discord.Invite):
    invite_cache.setdefault(invite.guild.id, {})[invite.code] = invite.uses


@bot.event
async def on_member_join(member: discord.Member):
    g = gd(member.guild.id)

    # --- Davet takibi: kim davet etti? ---
    inviter_mention = "Bilinmiyor"
    try:
        new_invites = await member.guild.invites()
        old_invites = invite_cache.get(member.guild.id, {})
        used_invite = None
        for inv in new_invites:
            if inv.uses is not None and inv.uses > old_invites.get(inv.code, 0):
                used_invite = inv
                break
        invite_cache[member.guild.id] = {inv.code: inv.uses for inv in new_invites}
        if used_invite and used_invite.inviter:
            inviter_mention = used_invite.inviter.mention
            counts = g.setdefault("invite_counts", {})
            uid = str(used_invite.inviter.id)
            counts[uid] = counts.get(uid, 0) + 1
            save_data()
        else:
            inviter_mention = "Bilinmiyor (vanity link / keşfet)"
    except (discord.Forbidden, discord.HTTPException):
        inviter_mention = "Bilinmiyor (izin yok)"

    # --- Anti-raid kontrolü ---
    prot = g["protection"]
    now = datetime.datetime.utcnow().timestamp()
    joins = join_tracker.setdefault(member.guild.id, [])
    joins.append(now)
    join_tracker[member.guild.id] = [t for t in joins if now - t < 10]

    if prot.get("anti_raid") and len(join_tracker[member.guild.id]) >= 8:
        try:
            await member.kick(reason="Anti-raid: Kısa sürede aşırı katılım tespit edildi.")
            if g["log_channel"]:
                ch = member.guild.get_channel(int(g["log_channel"]))
                if ch:
                    await ch.send(f"🛡️ **Anti-Raid:** {member} olası raid saldırısı nedeniyle atıldı.")
            return
        except discord.Forbidden:
            pass

    min_age = prot.get("min_account_age_days", 0)
    if min_age and (datetime.datetime.utcnow() - member.created_at.replace(tzinfo=None)).days < min_age:
        try:
            await member.kick(reason=f"Hesap yaşı {min_age} günden küçük.")
            if g["log_channel"]:
                ch = member.guild.get_channel(int(g["log_channel"]))
                if ch:
                    await ch.send(f"🛡️ **Koruma:** {member} hesap yaşı yetersiz olduğu için atıldı.")
            return
        except discord.Forbidden:
            pass

    # --- Otomatik rol ---
    if g["autorole"]:
        role = member.guild.get_role(int(g["autorole"]))
        if role:
            try:
                await member.add_roles(role, reason="Otomatik rol")
            except discord.Forbidden:
                pass

    # --- Hoşgeldin mesajı ---
    if g["welcome_channel"]:
        channel = member.guild.get_channel(int(g["welcome_channel"]))
        if channel:
            msg = g["welcome_message"].format(
                mention=member.mention,
                user=str(member),
                membercount=member.guild.member_count,
                server=member.guild.name,
                inviter=inviter_mention,
            )
            embed = discord.Embed(description=msg, color=discord.Color.green())
            embed.set_thumbnail(url=member.display_avatar.url)
            embed.set_footer(text=f"Sunucu: {member.guild.name}")
            try:
                await channel.send(embed=embed)
            except discord.Forbidden:
                pass


@bot.event
async def on_member_remove(member: discord.Member):
    g = gd(member.guild.id)
    if g["leave_channel"]:
        channel = member.guild.get_channel(int(g["leave_channel"]))
        if channel:
            msg = g["leave_message"].format(
                user=str(member),
                mention=member.mention,
                membercount=member.guild.member_count,
                server=member.guild.name,
            )
            embed = discord.Embed(description=msg, color=discord.Color.red())
            embed.set_thumbnail(url=member.display_avatar.url)
            try:
                await channel.send(embed=embed)
            except discord.Forbidden:
                pass


async def handle_disboard_message(message: discord.Message):
    """Disboard'un /bump yanıtını algılayıp otomatik hatırlatma zamanlayıcısı kurar."""
    if not message.embeds or not message.guild:
        return
    g = gd(message.guild.id)
    if not g.get("bump_channel") or message.channel.id != int(g["bump_channel"]):
        return
    embed_desc = (message.embeds[0].description or "").lower()
    if "bump" not in embed_desc:
        return

    next_time = datetime.datetime.utcnow() + datetime.timedelta(hours=2)
    g["next_bump_time"] = next_time.timestamp()
    save_data()
    await message.channel.send(
        f"✅ **Bump algılandı!** ⏰ 2 saat sonra tekrar hatırlatacağım: <t:{int(next_time.timestamp())}:R>"
    )


async def handle_ad_message(message: discord.Message, g: dict) -> bool:
    """Reklam kanalındaki mesajı işler. True dönerse mesaj işlendi demektir."""
    if not message.author.guild_permissions.manage_guild:
        cooldown_min = g.get("ad_cooldown_minutes", 60)
        last_used = g.get("ad_last_used", {}).get(str(message.author.id))
        now_ts = datetime.datetime.utcnow().timestamp()
        if last_used and (now_ts - last_used) < cooldown_min * 60:
            kalan = int((cooldown_min * 60 - (now_ts - last_used)) / 60) + 1
            try:
                await message.delete()
            except discord.Forbidden:
                pass
            uyari = await message.channel.send(
                f"⏳ {message.author.mention}, tekrar reklam verebilmek için **{kalan} dakika** daha beklemelisin."
            )
            await asyncio.sleep(6)
            try:
                await uyari.delete()
            except discord.Forbidden:
                pass
            return True

    if not message.content and not message.attachments:
        return False

    embed = discord.Embed(
        description=message.content or None,
        color=discord.Color.gold(),
        timestamp=discord.utils.utcnow(),
    )
    embed.set_author(name=str(message.author), icon_url=message.author.display_avatar.url)
    embed.set_footer(text="📢 Sunucu Reklamı  •  👍 / 👎 ile oy verebilirsin")
    if message.attachments:
        embed.set_image(url=message.attachments[0].url)

    try:
        await message.delete()
    except discord.Forbidden:
        pass

    ad_msg = await message.channel.send(embed=embed)
    view = AdVoteView(str(ad_msg.id))
    await ad_msg.edit(view=view)

    g.setdefault("ad_last_used", {})[str(message.author.id)] = datetime.datetime.utcnow().timestamp()
    save_data()
    return True


@bot.event
async def on_message(message: discord.Message):
    if not message.guild:
        return

    # --- Disboard bump algılama (bot mesajı olduğu için erken işlenir) ---
    if message.author.id == DISBOARD_ID:
        await handle_disboard_message(message)
        return

    if message.author.bot:
        return

    g = gd(message.guild.id)

    # --- Reklam kanalı işleme ---
    if g.get("ad_channel") and message.channel.id == int(g["ad_channel"]):
        handled = await handle_ad_message(message, g)
        if handled:
            return

    am = g["automod"]

    # Yöneticiler automod'dan muaf
    if not message.author.guild_permissions.manage_messages and am.get("enabled"):
        content_lower = message.content.lower()

        # Yasaklı kelime filtresi
        for word in am.get("banned_words", []):
            if word.lower() in content_lower:
                try:
                    await message.delete()
                except discord.Forbidden:
                    pass
                warn_msg = await message.channel.send(
                    f"⚠️ {message.author.mention}, mesajında yasaklı kelime tespit edildi ve silindi."
                )
                await asyncio.sleep(5)
                await warn_msg.delete()
                return

        # Discord davet linki filtresi
        if am.get("anti_invite") and INVITE_REGEX.search(message.content):
            try:
                await message.delete()
            except discord.Forbidden:
                pass
            warn_msg = await message.channel.send(
                f"⚠️ {message.author.mention}, davet linki paylaşımı yasak."
            )
            await asyncio.sleep(5)
            await warn_msg.delete()
            return

        # Genel link filtresi
        if am.get("anti_link") and LINK_REGEX.search(message.content):
            try:
                await message.delete()
            except discord.Forbidden:
                pass
            warn_msg = await message.channel.send(
                f"⚠️ {message.author.mention}, link paylaşımı yasak."
            )
            await asyncio.sleep(5)
            await warn_msg.delete()
            return

        # Spam koruması (5 saniyede 5 mesaj)
        if am.get("anti_spam"):
            now = datetime.datetime.utcnow().timestamp()
            times = spam_tracker.setdefault(message.author.id, [])
            times.append(now)
            spam_tracker[message.author.id] = [t for t in times if now - t < 5]

            if len(spam_tracker[message.author.id]) >= 5:
                try:
                    until = discord.utils.utcnow() + datetime.timedelta(minutes=5)
                    await message.author.timeout(until, reason="Otomatik spam koruması")
                    await message.channel.send(
                        f"🔇 {message.author.mention} spam yaptığı için 5 dakika susturuldu."
                    )
                    spam_tracker[message.author.id] = []
                except discord.Forbidden:
                    pass

    await bot.process_commands(message)


# ================================================================
#                        MODERASYON
# ================================================================
class ConfirmView(discord.ui.View):
    """Kick/ban gibi kritik işlemler öncesi ✅/🛑 onay butonları gösterir."""

    def __init__(self, author_id: int, timeout: float = 20):
        super().__init__(timeout=timeout)
        self.value = None
        self.author_id = author_id

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.author_id:
            await interaction.response.send_message("❌ Bu buton sana ait değil.", ephemeral=True)
            return False
        return True

    async def on_timeout(self):
        for child in self.children:
            child.disabled = True

    @discord.ui.button(label="Evet, onaylıyorum", style=discord.ButtonStyle.green, emoji="✅")
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.value = True
        for child in self.children:
            child.disabled = True
        await interaction.response.edit_message(view=self)
        self.stop()

    @discord.ui.button(label="Hayır, iptal et", style=discord.ButtonStyle.red, emoji="🛑")
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.value = False
        for child in self.children:
            child.disabled = True
        await interaction.response.edit_message(content="🛑 İşlem iptal edildi.", view=self)
        self.stop()


@bot.hybrid_command(name="kick", description="Bir üyeyi sunucudan atar. (Onay butonlu)")
@commands.has_permissions(kick_members=True)
async def kick_cmd(ctx: commands.Context, member: discord.Member, *, reason: str = "Sebep belirtilmedi"):
    if member.top_role >= ctx.author.top_role and ctx.author.id != ctx.guild.owner_id:
        return await ctx.send("❌ Bu üyeyi atamazsın, rolü seninkinden yüksek veya eşit.")

    view = ConfirmView(ctx.author.id)
    confirm_msg = await ctx.send(
        f"⚠️ **{member}** kullanıcısını atmak istediğine emin misin?\nSebep: {reason}", view=view
    )
    await view.wait()

    if view.value is None:
        return await confirm_msg.edit(content="⏱️ Süre doldu, işlem iptal edildi.", view=view)
    if not view.value:
        return

    await member.kick(reason=reason)
    embed = discord.Embed(title="👢 Üye Atıldı", color=discord.Color.orange())
    embed.add_field(name="👤 Üye", value=str(member), inline=True)
    embed.add_field(name="🛡️ Yetkili", value=str(ctx.author), inline=True)
    embed.add_field(name="📝 Sebep", value=reason, inline=False)
    await confirm_msg.edit(content=None, embed=embed, view=None)


@bot.hybrid_command(name="ban", description="Bir üyeyi sunucudan yasaklar. (Onay butonlu)")
@commands.has_permissions(ban_members=True)
async def ban_cmd(ctx: commands.Context, member: discord.Member, *, reason: str = "Sebep belirtilmedi"):
    if member.top_role >= ctx.author.top_role and ctx.author.id != ctx.guild.owner_id:
        return await ctx.send("❌ Bu üyeyi yasaklayamazsın, rolü seninkinden yüksek veya eşit.")

    view = ConfirmView(ctx.author.id)
    confirm_msg = await ctx.send(
        f"⚠️ **{member}** kullanıcısını yasaklamak istediğine emin misin?\nSebep: {reason}", view=view
    )
    await view.wait()

    if view.value is None:
        return await confirm_msg.edit(content="⏱️ Süre doldu, işlem iptal edildi.", view=view)
    if not view.value:
        return

    await member.ban(reason=reason, delete_message_days=0)
    embed = discord.Embed(title="🔨 Üye Yasaklandı", color=discord.Color.red())
    embed.add_field(name="👤 Üye", value=str(member), inline=True)
    embed.add_field(name="🛡️ Yetkili", value=str(ctx.author), inline=True)
    embed.add_field(name="📝 Sebep", value=reason, inline=False)
    await confirm_msg.edit(content=None, embed=embed, view=None)


@bot.hybrid_command(name="unban", description="Bir kullanıcının yasağını kaldırır. (ID gerekir)")
@commands.has_permissions(ban_members=True)
async def unban_cmd(ctx: commands.Context, user_id: str):
    try:
        user = await bot.fetch_user(int(user_id))
        await ctx.guild.unban(user)
        await ctx.send(f"✅ **{user}** kullanıcısının yasağı kaldırıldı.")
    except (discord.NotFound, ValueError):
        await ctx.send("❌ Kullanıcı bulunamadı veya yasaklı değil.")


@bot.hybrid_command(name="mute", description="Bir üyeyi belirtilen dakika kadar susturur.")
@commands.has_permissions(moderate_members=True)
async def mute_cmd(ctx: commands.Context, member: discord.Member, minutes: int = 10, *, reason: str = "Sebep belirtilmedi"):
    until = discord.utils.utcnow() + datetime.timedelta(minutes=minutes)
    await member.timeout(until, reason=reason)
    await ctx.send(f"🔇 **{member}** {minutes} dakika susturuldu. Sebep: {reason}")


@bot.hybrid_command(name="unmute", description="Bir üyenin susturmasını kaldırır.")
@commands.has_permissions(moderate_members=True)
async def unmute_cmd(ctx: commands.Context, member: discord.Member):
    await member.timeout(None)
    await ctx.send(f"🔊 **{member}** kullanıcısının susturması kaldırıldı.")


@bot.hybrid_command(name="warn", description="Bir üyeye uyarı verir.")
@commands.has_permissions(manage_messages=True)
async def warn_cmd(ctx: commands.Context, member: discord.Member, *, reason: str = "Sebep belirtilmedi"):
    g = gd(ctx.guild.id)
    uid = str(member.id)
    g["warns"].setdefault(uid, [])
    g["warns"][uid].append({"reason": reason, "by": str(ctx.author), "date": str(datetime.date.today())})
    save_data()
    count = len(g["warns"][uid])
    await ctx.send(f"⚠️ **{member}** uyarıldı. (Toplam uyarı: {count})\nSebep: {reason}")


@bot.hybrid_command(name="uyarilar", description="Bir üyenin uyarılarını listeler.")
async def warnings_cmd(ctx: commands.Context, member: discord.Member):
    g = gd(ctx.guild.id)
    warns = g["warns"].get(str(member.id), [])
    if not warns:
        return await ctx.send(f"✅ **{member}** kullanıcısının hiç uyarısı yok.")
    embed = discord.Embed(title=f"{member} — Uyarılar ({len(warns)})", color=discord.Color.yellow())
    for i, w in enumerate(warns, 1):
        embed.add_field(name=f"#{i} - {w['date']}", value=f"Sebep: {w['reason']}\nYetkili: {w['by']}", inline=False)
    await ctx.send(embed=embed)


@bot.hybrid_command(name="uyarisil", description="Bir üyenin tüm uyarılarını temizler.")
@commands.has_permissions(manage_messages=True)
async def clearwarns_cmd(ctx: commands.Context, member: discord.Member):
    g = gd(ctx.guild.id)
    g["warns"][str(member.id)] = []
    save_data()
    await ctx.send(f"🧹 **{member}** kullanıcısının uyarıları temizlendi.")


@bot.hybrid_command(name="temizle", description="Belirtilen sayıda mesajı siler.")
@commands.has_permissions(manage_messages=True)
async def purge_cmd(ctx: commands.Context, amount: int = 10):
    if amount < 1 or amount > 200:
        return await ctx.send("❌ 1 ile 200 arasında bir sayı gir.")
    deleted = await ctx.channel.purge(limit=amount + 1)
    msg = await ctx.send(f"🧹 {len(deleted) - 1} mesaj silindi.")
    await asyncio.sleep(3)
    await msg.delete()


# ================================================================
#                          AUTOMOD
# ================================================================
@bot.hybrid_command(name="automod_ac", description="Automod sistemini açar.")
@is_mod()
async def automod_on(ctx: commands.Context):
    gd(ctx.guild.id)["automod"]["enabled"] = True
    save_data()
    await ctx.send("✅ Automod sistemi **açıldı**.")


@bot.hybrid_command(name="automod_kapat", description="Automod sistemini kapatır.")
@is_mod()
async def automod_off(ctx: commands.Context):
    gd(ctx.guild.id)["automod"]["enabled"] = False
    save_data()
    await ctx.send("🛑 Automod sistemi **kapatıldı**.")


@bot.hybrid_command(name="kelime_ekle", description="Automod yasaklı kelime listesine kelime ekler.")
@is_mod()
async def add_word(ctx: commands.Context, *, word: str):
    g = gd(ctx.guild.id)
    if word.lower() not in [w.lower() for w in g["automod"]["banned_words"]]:
        g["automod"]["banned_words"].append(word)
        save_data()
    await ctx.send(f"✅ `{word}` yasaklı kelime listesine eklendi.")


@bot.hybrid_command(name="kelime_sil", description="Automod yasaklı kelime listesinden kelime siler.")
@is_mod()
async def remove_word(ctx: commands.Context, *, word: str):
    g = gd(ctx.guild.id)
    g["automod"]["banned_words"] = [w for w in g["automod"]["banned_words"] if w.lower() != word.lower()]
    save_data()
    await ctx.send(f"🗑️ `{word}` yasaklı kelime listesinden silindi.")


@bot.hybrid_command(name="automod_ayar", description="Automod alt özelliklerini açar/kapatır. (davet/link/spam)")
@is_mod()
async def automod_settings(ctx: commands.Context, ozellik: str, durum: bool):
    ozellik = ozellik.lower()
    mapping = {"davet": "anti_invite", "link": "anti_link", "spam": "anti_spam"}
    if ozellik not in mapping:
        return await ctx.send("❌ Geçerli seçenekler: `davet`, `link`, `spam`")
    g = gd(ctx.guild.id)
    g["automod"][mapping[ozellik]] = durum
    save_data()
    await ctx.send(f"✅ Automod **{ozellik}** koruması {'açıldı' if durum else 'kapatıldı'}.")


# ================================================================
#                         HOŞGELDİN
# ================================================================
@bot.hybrid_command(name="hosgeldin_kanal", description="Hoşgeldin mesajlarının gönderileceği kanalı ayarlar.")
@is_mod()
async def set_welcome_channel(ctx: commands.Context, channel: discord.TextChannel):
    gd(ctx.guild.id)["welcome_channel"] = str(channel.id)
    save_data()
    await ctx.send(f"✅ Hoşgeldin kanalı {channel.mention} olarak ayarlandı.")


@bot.hybrid_command(name="hosgeldin_mesaj", description="Hoşgeldin mesajını özelleştirir. Değişkenler: {mention} {user} {membercount} {server} {inviter}")
@is_mod()
async def set_welcome_message(ctx: commands.Context, *, message: str):
    gd(ctx.guild.id)["welcome_message"] = message
    save_data()
    await ctx.send("✅ Hoşgeldin mesajı güncellendi.")


@bot.hybrid_command(name="ayrilis_kanal", description="Ayrılış mesajlarının gönderileceği kanalı ayarlar.")
@is_mod()
async def set_leave_channel(ctx: commands.Context, channel: discord.TextChannel):
    gd(ctx.guild.id)["leave_channel"] = str(channel.id)
    save_data()
    await ctx.send(f"✅ Ayrılış kanalı {channel.mention} olarak ayarlandı.")


@bot.hybrid_command(name="ayrilis_mesaj", description="Ayrılış mesajını özelleştirir. Değişkenler: {user} {membercount} {server}")
@is_mod()
async def set_leave_message(ctx: commands.Context, *, message: str):
    gd(ctx.guild.id)["leave_message"] = message
    save_data()
    await ctx.send("✅ Ayrılış mesajı güncellendi.")


@bot.hybrid_command(name="otorol", description="Katılan üyelere otomatik verilecek rolü ayarlar.")
@is_mod()
async def set_autorole(ctx: commands.Context, role: discord.Role):
    gd(ctx.guild.id)["autorole"] = str(role.id)
    save_data()
    await ctx.send(f"✅ Otomatik rol **{role.name}** olarak ayarlandı.")


# ================================================================
#                          ÇEKİLİŞ
# ================================================================
def parse_duration(text: str) -> int:
    """'10d' -> 10 dakika, '2s' -> 2 saat, '1g' -> 1 gün gibi süreleri saniyeye çevirir."""
    match = re.match(r"^(\d+)([sdg])$", text.lower())
    if not match:
        raise ValueError("Geçersiz süre formatı")
    amount, unit = int(match.group(1)), match.group(2)
    if unit == "d":
        return amount * 60
    if unit == "s":
        return amount * 3600
    if unit == "g":
        return amount * 86400
    raise ValueError("Geçersiz birim")


class GiveawayJoinButton(discord.ui.Button):
    """Her çekiliş mesajına özel, katılımcı sayısını canlı gösteren buton."""

    def __init__(self, message_id: str, count: int = 0):
        super().__init__(
            label=f"Katıl ({count})",
            style=discord.ButtonStyle.green,
            emoji="🎉",
            custom_id=f"giveaway_join_{message_id}",
        )
        self.message_id = str(message_id)

    async def callback(self, interaction: discord.Interaction):
        g = gd(interaction.guild.id)
        gw = g["giveaways"].get(self.message_id)
        if not gw or gw.get("ended"):
            return await interaction.response.send_message("❌ Bu çekiliş artık aktif değil.", ephemeral=True)

        participants = gw.setdefault("participants", [])
        uid = interaction.user.id
        if uid in participants:
            participants.remove(uid)
            await interaction.response.send_message("🚪 Çekilişten ayrıldın.", ephemeral=True)
        else:
            participants.append(uid)
            await interaction.response.send_message("🎉 Çekilişe katıldın! Bol şans dilerim.", ephemeral=True)

        save_data()
        self.label = f"Katıl ({len(participants)})"
        try:
            await interaction.message.edit(view=self.view)
        except discord.HTTPException:
            pass


class GiveawayView(discord.ui.View):
    def __init__(self, message_id: str, count: int = 0):
        super().__init__(timeout=None)
        self.add_item(GiveawayJoinButton(message_id, count))


@bot.hybrid_command(name="cekilis_baslat", description="Buton ile katılınan bir çekiliş başlatır. Süre örnekleri: 10d(dakika) 2s(saat) 1g(gün)")
@is_mod()
async def start_giveaway(ctx: commands.Context, sure: str, kazanan_sayisi: int, *, odul: str):
    try:
        seconds = parse_duration(sure)
    except ValueError:
        return await ctx.send("❌ Süre formatı geçersiz. Örnek: `10d`, `2s`, `1g`")

    end_time = datetime.datetime.utcnow() + datetime.timedelta(seconds=seconds)
    embed = discord.Embed(
        title="🎉 ÇEKİLİŞ 🎉",
        description=f"🏆 **Ödül:** {odul}\n👥 **Kazanan sayısı:** {kazanan_sayisi}\n"
                    f"⏰ **Bitiş:** <t:{int(end_time.timestamp())}:R>\n\n🔘 Katılmak için aşağıdaki butona tıkla!",
        color=discord.Color.blurple(),
    )
    embed.set_footer(text=f"Başlatan: {ctx.author}")
    msg = await ctx.send(embed=embed)

    view = GiveawayView(str(msg.id))
    await msg.edit(view=view)

    g = gd(ctx.guild.id)
    g["giveaways"][str(msg.id)] = {
        "channel_id": msg.channel.id,
        "end_time": end_time.timestamp(),
        "winners": kazanan_sayisi,
        "prize": odul,
        "ended": False,
        "participants": [],
    }
    save_data()


async def finish_giveaway(guild: discord.Guild, message_id: str, gw: dict):
    channel = guild.get_channel(gw["channel_id"])
    if not channel:
        return
    try:
        msg = await channel.fetch_message(int(message_id))
    except discord.NotFound:
        return

    participant_ids = gw.get("participants", [])
    users = [guild.get_member(uid) for uid in participant_ids]
    users = [u for u in users if u is not None]

    if not users:
        await channel.send("😢 Çekilişe kimse katılmadığı için kazanan belirlenemedi.")
    else:
        winners = random.sample(users, min(gw["winners"], len(users)))
        winners_text = ", ".join(w.mention for w in winners)
        await channel.send(f"🎉 Tebrikler {winners_text}! 🏆 **{gw['prize']}** ödülünü kazandınız!")

    gw["ended"] = True
    try:
        await msg.edit(view=None)
    except discord.HTTPException:
        pass


@tasks.loop(seconds=30)
async def check_giveaways():
    now = datetime.datetime.utcnow().timestamp()
    for guild in bot.guilds:
        g = gd(guild.id)
        for message_id, gw in list(g["giveaways"].items()):
            if not gw["ended"] and now >= gw["end_time"]:
                await finish_giveaway(guild, message_id, gw)
    save_data()


@tasks.loop(seconds=60)
async def check_bumps():
    now = datetime.datetime.utcnow().timestamp()
    for guild in bot.guilds:
        g = gd(guild.id)
        next_time = g.get("next_bump_time")
        if not next_time or now < next_time:
            continue
        channel = None
        if g.get("bump_channel"):
            channel = guild.get_channel(int(g["bump_channel"]))
        if channel:
            role_mention = ""
            if g.get("bump_role"):
                role = guild.get_role(int(g["bump_role"]))
                if role:
                    role_mention = f"{role.mention} "
            try:
                await channel.send(
                    f"🔔 {role_mention}Sunucuyu tekrar **bump** etme zamanı geldi! `/bump` yazarak tanıtımı destekleyebilirsin. 📢"
                )
            except discord.Forbidden:
                pass
        g["next_bump_time"] = None
    save_data()


@bot.hybrid_command(name="cekilis_bitir", description="Bir çekilişi erken bitirir. (Mesaj ID gerekir)")
@is_mod()
async def end_giveaway(ctx: commands.Context, message_id: str):
    g = gd(ctx.guild.id)
    gw = g["giveaways"].get(message_id)
    if not gw or gw["ended"]:
        return await ctx.send("❌ Bu ID'ye ait aktif bir çekiliş bulunamadı.")
    await finish_giveaway(ctx.guild, message_id, gw)
    save_data()
    await ctx.send("✅ Çekiliş erken bitirildi.")


@bot.hybrid_command(name="cekilis_yenidencek", description="Bitmiş bir çekilişte kazananı yeniden çeker.")
@is_mod()
async def reroll_giveaway(ctx: commands.Context, message_id: str):
    g = gd(ctx.guild.id)
    gw = g["giveaways"].get(message_id)
    if not gw:
        return await ctx.send("❌ Bu ID'ye ait bir çekiliş bulunamadı.")
    gw["ended"] = False
    await finish_giveaway(ctx.guild, message_id, gw)
    save_data()
    await ctx.send("🔄 Kazanan yeniden çekildi.")


# ================================================================
#                     REKLAM & BÜYÜME 📢
# ================================================================
class AdVoteButton(discord.ui.Button):
    """Reklam mesajları için 👍/👎 oy butonu, canlı sayaç gösterir."""

    def __init__(self, message_id: str, tur: str, count: int = 0):
        emoji = "👍" if tur == "like" else "👎"
        label_text = "Beğen" if tur == "like" else "Beğenme"
        super().__init__(
            label=f"{label_text} ({count})",
            emoji=emoji,
            style=discord.ButtonStyle.gray,
            custom_id=f"ad_{tur}_{message_id}",
        )
        self.message_id = message_id
        self.tur = tur

    async def callback(self, interaction: discord.Interaction):
        votes = ad_votes.setdefault(self.message_id, {"like": set(), "dislike": set()})
        uid = interaction.user.id
        diger = "dislike" if self.tur == "like" else "like"
        votes[diger].discard(uid)

        if uid in votes[self.tur]:
            votes[self.tur].discard(uid)
            await interaction.response.send_message("↩️ Oyun geri alındı.", ephemeral=True)
        else:
            votes[self.tur].add(uid)
            await interaction.response.send_message("✅ Oyun kaydedildi, teşekkürler!", ephemeral=True)

        view: discord.ui.View = self.view
        for child in view.children:
            if isinstance(child, AdVoteButton):
                label_text = "Beğen" if child.tur == "like" else "Beğenme"
                child.label = f"{label_text} ({len(votes[child.tur])})"
        try:
            await interaction.message.edit(view=view)
        except discord.HTTPException:
            pass


class AdVoteView(discord.ui.View):
    def __init__(self, message_id: str):
        super().__init__(timeout=None)
        self.add_item(AdVoteButton(message_id, "like"))
        self.add_item(AdVoteButton(message_id, "dislike"))


@bot.hybrid_command(name="reklam_kanal", description="Otomatik reklam/tanıtım kanalını ayarlar.")
@is_mod()
async def set_ad_channel(ctx: commands.Context, channel: discord.TextChannel):
    gd(ctx.guild.id)["ad_channel"] = str(channel.id)
    save_data()
    await ctx.send(
        f"✅ Reklam kanalı {channel.mention} olarak ayarlandı.\n"
        f"📢 Bu kanala atılan her mesaj otomatik olarak şık bir embed'e çevrilip 👍/👎 oylama butonu eklenecek."
    )


@bot.hybrid_command(name="reklam_cooldown", description="Kullanıcıların ne sıklıkla reklam verebileceğini (dakika) ayarlar.")
@is_mod()
async def set_ad_cooldown(ctx: commands.Context, dakika: int):
    if dakika < 0:
        return await ctx.send("❌ Süre 0 veya daha büyük olmalı.")
    gd(ctx.guild.id)["ad_cooldown_minutes"] = dakika
    save_data()
    await ctx.send(f"⏳ Reklam bekleme süresi **{dakika} dakika** olarak ayarlandı.")


@bot.hybrid_command(name="bump_kanal", description="Disboard bump hatırlatmalarının yapılacağı kanalı ayarlar.")
@is_mod()
async def set_bump_channel(ctx: commands.Context, channel: discord.TextChannel):
    gd(ctx.guild.id)["bump_channel"] = str(channel.id)
    save_data()
    await ctx.send(
        f"✅ Bump kanalı {channel.mention} olarak ayarlandı.\n"
        f"🔔 Bu kanalda Disboard ile `/bump` yapıldığında algılanıp 2 saat sonra otomatik hatırlatılacak."
    )


@bot.hybrid_command(name="bump_rol", description="Bump hatırlatmasında etiketlenecek rolü ayarlar.")
@is_mod()
async def set_bump_role(ctx: commands.Context, role: discord.Role):
    gd(ctx.guild.id)["bump_role"] = str(role.id)
    save_data()
    await ctx.send(f"✅ Bump hatırlatma rolü **{role.name}** olarak ayarlandı.")


@bot.hybrid_command(name="bump_baslat", description="Disboard'a bağlı olmadan manuel 2 saatlik bump sayacı başlatır.")
@is_mod()
async def start_bump_timer(ctx: commands.Context):
    g = gd(ctx.guild.id)
    next_time = datetime.datetime.utcnow() + datetime.timedelta(hours=2)
    g["next_bump_time"] = next_time.timestamp()
    save_data()
    await ctx.send(f"⏰ Bump hatırlatıcı kuruldu, <t:{int(next_time.timestamp())}:R> hatırlatacağım.")


@bot.hybrid_command(name="davet_liderlik", description="En çok üye davet edenlerin listesini gösterir.")
async def invite_leaderboard(ctx: commands.Context):
    g = gd(ctx.guild.id)
    counts = g.get("invite_counts", {})
    if not counts:
        return await ctx.send("📭 Henüz kaydedilmiş bir davet verisi yok.")

    sirali = sorted(counts.items(), key=lambda x: x[1], reverse=True)[:10]
    embed = discord.Embed(title="🏆 Davet Liderlik Tablosu", color=discord.Color.gold())
    madalyalar = ["🥇", "🥈", "🥉"]
    lines = []
    for i, (uid, count) in enumerate(sirali):
        madalya = madalyalar[i] if i < 3 else f"#{i + 1}"
        member = ctx.guild.get_member(int(uid))
        isim = member.mention if member else f"Kullanıcı ({uid})"
        lines.append(f"{madalya} {isim} — **{count}** davet")
    embed.description = "\n".join(lines)
    await ctx.send(embed=embed)


@bot.hybrid_command(name="davetlerim", description="Kendinizin veya başka bir üyenin davet sayısını gösterir.")
async def my_invites(ctx: commands.Context, member: discord.Member = None):
    member = member or ctx.author
    g = gd(ctx.guild.id)
    count = g.get("invite_counts", {}).get(str(member.id), 0)
    await ctx.send(f"📨 **{member}** şu ana kadar **{count}** kişi davet etti.")


# ================================================================
#                          EĞLENCE
# ================================================================
EIGHTBALL_ANSWERS = [
    "Kesinlikle evet.", "Evet.", "Büyük ihtimalle evet.", "Görünüşe göre evet.",
    "Emin değilim, tekrar sor.", "Şu an söyleyemem.", "Odaklan ve tekrar sor.",
    "Güvenme buna.", "Hayır.", "Kaynaklarım hayır diyor.", "Pek olası değil.", "Kesinlikle hayır.",
]

JOKES = [
    "Elektrik faturası neden hiç şaşırmaz? Çünkü her ay aynı şoku yaşar.",
    "Bilgisayar neden üşür? Çünkü pencereleri (Windows) açık kalır.",
    "Matematik kitabı neden üzgündü? Çünkü bir sürü problemi vardı.",
    "Kod neden çalışmadı? Çünkü noktalı virgülü unuttum, klasik.",
    "Balık neden bilgisayar kullanmaz? İnternette takılmaktan korkar.",
]

QUESTIONS = [
    "En sevdiğin oyun hangisi?", "Hayatında keşke demediğin bir şey var mı?",
    "En son ne zaman gerçekten güldün?", "Bir süper gücün olsaydı ne olurdu?",
    "En sevdiğin yemek nedir?",
]


@bot.hybrid_command(name="8top", description="Sihirli 8 topa bir soru sor.")
async def eightball_cmd(ctx: commands.Context, *, soru: str):
    embed = discord.Embed(title="🎱 Sihirli 8 Top", color=discord.Color.dark_purple())
    embed.add_field(name="Soru", value=soru, inline=False)
    embed.add_field(name="Cevap", value=random.choice(EIGHTBALL_ANSWERS), inline=False)
    await ctx.send(embed=embed)


@bot.hybrid_command(name="zar", description="Belirtilen taraflı zar atar. (Varsayılan 6)")
async def dice_cmd(ctx: commands.Context, taraf: int = 6):
    if taraf < 2:
        return await ctx.send("❌ Zar en az 2 taraflı olmalı.")
    await ctx.send(f"🎲 Zar döndü ve **{random.randint(1, taraf)}** geldi!")


@bot.hybrid_command(name="yaziturra", description="Yazı tura atar.")
async def coinflip_cmd(ctx: commands.Context):
    await ctx.send(f"🪙 Sonuç: **{random.choice(['Yazı', 'Tura'])}**")


@bot.hybrid_command(name="saka", description="Rastgele bir şaka anlatır.")
async def joke_cmd(ctx: commands.Context):
    await ctx.send(f"😂 {random.choice(JOKES)}")


@bot.hybrid_command(name="soru", description="Rastgele bir sohbet sorusu sorar.")
async def question_cmd(ctx: commands.Context):
    await ctx.send(f"❓ {random.choice(QUESTIONS)}")


class RPSView(discord.ui.View):
    """Butonlarla oynanan Taş-Kağıt-Makas oyunu."""

    def __init__(self, author_id: int):
        super().__init__(timeout=30)
        self.author_id = author_id

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.author_id:
            await interaction.response.send_message("❌ Bu oyun sana ait değil.", ephemeral=True)
            return False
        return True

    async def play(self, interaction: discord.Interaction, secim: str):
        secenekler = ["taş", "kağıt", "makas"]
        emojiler = {"taş": "🪨", "kağıt": "📄", "makas": "✂️"}
        bot_secim = random.choice(secenekler)

        if secim == bot_secim:
            sonuc = "🤝 **Berabere!**"
        elif (secim, bot_secim) in [("taş", "makas"), ("kağıt", "taş"), ("makas", "kağıt")]:
            sonuc = "🎉 **Kazandın!**"
        else:
            sonuc = "😢 **Kaybettin!**"

        for child in self.children:
            child.disabled = True

        await interaction.response.edit_message(
            content=f"Sen: {emojiler[secim]} **{secim}**  —  Bot: {emojiler[bot_secim]} **{bot_secim}**\n{sonuc}",
            view=self,
        )
        self.stop()

    @discord.ui.button(label="Taş", emoji="🪨", style=discord.ButtonStyle.secondary)
    async def tas(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.play(interaction, "taş")

    @discord.ui.button(label="Kağıt", emoji="📄", style=discord.ButtonStyle.secondary)
    async def kagit(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.play(interaction, "kağıt")

    @discord.ui.button(label="Makas", emoji="✂️", style=discord.ButtonStyle.secondary)
    async def makas(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.play(interaction, "makas")


@bot.hybrid_command(name="tkm", description="Bot ile taş-kağıt-makas oyna! (buton ile)")
async def rps_cmd(ctx: commands.Context):
    view = RPSView(ctx.author.id)
    await ctx.send("🎮 Bir seçim yap:", view=view)


# ================================================================
#                           TICKET
# ================================================================
class TicketCloseView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Ticket'ı Kapat", style=discord.ButtonStyle.red, custom_id="ticket_close_btn", emoji="🔒")
    async def close_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("🔒 Ticket 5 saniye içinde kapatılıyor...", ephemeral=False)
        await asyncio.sleep(5)
        try:
            await interaction.channel.delete()
        except discord.Forbidden:
            pass


TICKET_CATEGORIES = {
    "genel": {"label": "Genel Destek", "emoji": "🎫", "desc": "Aklına takılan herhangi bir konu"},
    "teknik": {"label": "Teknik Sorun", "emoji": "🛠️", "desc": "Hata, bug veya teknik problem"},
    "sikayet": {"label": "Şikayet", "emoji": "⚠️", "desc": "Bir üye/durum hakkında şikayet"},
    "oneri": {"label": "Öneri", "emoji": "💡", "desc": "Sunucu için fikir ve önerilerin"},
    "satinalma": {"label": "Satın Alma", "emoji": "💰", "desc": "Ürün/hizmet satın alma talebi"},
}


class TicketCategorySelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label=info["label"], emoji=info["emoji"], value=key, description=info["desc"])
            for key, info in TICKET_CATEGORIES.items()
        ]
        super().__init__(
            placeholder="🎫 Destek talebi türünü seç...",
            options=options,
            custom_id="ticket_category_select",
            min_values=1,
            max_values=1,
        )

    async def callback(self, interaction: discord.Interaction):
        guild = interaction.guild
        g = gd(guild.id)
        secim = self.values[0]
        info = TICKET_CATEGORIES[secim]

        category = None
        if g["ticket_category"]:
            category = guild.get_channel(int(g["ticket_category"]))

        chan_name = f"{secim}-{interaction.user.name}".lower()
        existing = discord.utils.get(guild.text_channels, name=chan_name)
        if existing:
            return await interaction.response.send_message(
                f"❌ Bu kategoride zaten açık bir ticket'ın var: {existing.mention}", ephemeral=True
            )

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            interaction.user: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True),
            guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True),
        }
        channel = await guild.create_text_channel(
            name=chan_name,
            category=category,
            overwrites=overwrites,
            topic=f"{info['label']} — {interaction.user}",
            reason=f"{interaction.user} '{info['label']}' ticket'ı açtı.",
        )
        embed = discord.Embed(
            title=f"{info['emoji']} {info['label']}",
            description=f"Merhaba {interaction.user.mention}, talebini buraya detaylı şekilde yaz.\n"
                        f"Yetkililer en kısa sürede sana yardımcı olacak. 🙌",
            color=discord.Color.green(),
        )
        await channel.send(embed=embed, view=TicketCloseView())
        await interaction.response.send_message(f"✅ Ticket oluşturuldu: {channel.mention}", ephemeral=True)

        if g["ticket_log_channel"]:
            log_ch = guild.get_channel(int(g["ticket_log_channel"]))
            if log_ch:
                await log_ch.send(f"{info['emoji']} {interaction.user} **{info['label']}** talebi açtı: {channel.mention}")


class TicketPanelView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(TicketCategorySelect())


@bot.hybrid_command(name="ticket_panel", description="Kategori seçmeli ticket açma panelini gönderir.")
@is_mod()
async def ticket_panel_cmd(ctx: commands.Context):
    embed = discord.Embed(
        title="🎫 Destek Sistemi",
        description="Bir sorunuz mu var? Aşağıdaki menüden uygun kategoriyi seçerek destek talebi oluşturabilirsin. 👇",
        color=discord.Color.blurple(),
    )
    embed.add_field(
        name="Kategoriler",
        value="\n".join(f"{v['emoji']} **{v['label']}** — {v['desc']}" for v in TICKET_CATEGORIES.values()),
        inline=False,
    )
    await ctx.send(embed=embed, view=TicketPanelView())


@bot.hybrid_command(name="ticket_kategori", description="Ticket kanallarının açılacağı kategoriyi ayarlar.")
@is_mod()
async def set_ticket_category(ctx: commands.Context, category: discord.CategoryChannel):
    gd(ctx.guild.id)["ticket_category"] = str(category.id)
    save_data()
    await ctx.send(f"✅ Ticket kategorisi **{category.name}** olarak ayarlandı.")


@bot.hybrid_command(name="ticket_log", description="Ticket işlemlerinin loglanacağı kanalı ayarlar.")
@is_mod()
async def set_ticket_log(ctx: commands.Context, channel: discord.TextChannel):
    gd(ctx.guild.id)["ticket_log_channel"] = str(channel.id)
    save_data()
    await ctx.send(f"✅ Ticket log kanalı {channel.mention} olarak ayarlandı.")


# ================================================================
#                           KORUMA
# ================================================================
@bot.hybrid_command(name="koruma_raid", description="Anti-raid korumasını açar/kapatır.")
@is_admin()
async def toggle_antiraid(ctx: commands.Context, durum: bool):
    gd(ctx.guild.id)["protection"]["anti_raid"] = durum
    save_data()
    await ctx.send(f"🛡️ Anti-raid koruması {'açıldı' if durum else 'kapatıldı'}.")


@bot.hybrid_command(name="koruma_hesapyasi", description="Katılabilecek minimum hesap yaşını (gün) ayarlar. 0 = kapalı")
@is_admin()
async def set_min_account_age(ctx: commands.Context, gun: int):
    gd(ctx.guild.id)["protection"]["min_account_age_days"] = max(0, gun)
    save_data()
    if gun <= 0:
        await ctx.send("🛡️ Hesap yaşı koruması kapatıldı.")
    else:
        await ctx.send(f"🛡️ Artık en az **{gun} günlük** hesaplar katılabilir.")


@bot.hybrid_command(name="koruma_durum", description="Sunucudaki koruma ayarlarını gösterir.")
@is_mod()
async def protection_status(ctx: commands.Context):
    g = gd(ctx.guild.id)
    prot = g["protection"]
    am = g["automod"]
    embed = discord.Embed(title="🛡️ Koruma Durumu", color=discord.Color.teal())
    embed.add_field(name="Anti-Raid", value="✅ Açık" if prot["anti_raid"] else "❌ Kapalı")
    embed.add_field(name="Min. Hesap Yaşı", value=f"{prot['min_account_age_days']} gün")
    embed.add_field(name="Automod", value="✅ Açık" if am["enabled"] else "❌ Kapalı")
    embed.add_field(name="Anti-Davet", value="✅ Açık" if am["anti_invite"] else "❌ Kapalı")
    embed.add_field(name="Anti-Link", value="✅ Açık" if am["anti_link"] else "❌ Kapalı")
    embed.add_field(name="Anti-Spam", value="✅ Açık" if am["anti_spam"] else "❌ Kapalı")
    await ctx.send(embed=embed)


# ================================================================
#                           YÖNETİM
# ================================================================
@bot.hybrid_command(name="sunucubilgi", description="Sunucu hakkında bilgi verir.")
async def server_info(ctx: commands.Context):
    guild = ctx.guild
    embed = discord.Embed(title=f"📊 {guild.name}", color=discord.Color.blue())
    if guild.icon:
        embed.set_thumbnail(url=guild.icon.url)
    embed.add_field(name="Sahibi", value=str(guild.owner), inline=True)
    embed.add_field(name="Üye Sayısı", value=str(guild.member_count), inline=True)
    embed.add_field(name="Kanal Sayısı", value=str(len(guild.channels)), inline=True)
    embed.add_field(name="Rol Sayısı", value=str(len(guild.roles)), inline=True)
    embed.add_field(name="Oluşturulma", value=f"<t:{int(guild.created_at.timestamp())}:D>", inline=True)
    embed.add_field(name="Sunucu ID", value=str(guild.id), inline=True)
    await ctx.send(embed=embed)


@bot.hybrid_command(name="kullanicibilgi", description="Bir kullanıcı hakkında bilgi verir.")
async def user_info(ctx: commands.Context, member: discord.Member = None):
    member = member or ctx.author
    embed = discord.Embed(title=f"👤 {member}", color=member.color if member.color.value else discord.Color.blue())
    embed.set_thumbnail(url=member.display_avatar.url)
    embed.add_field(name="Kullanıcı ID", value=str(member.id), inline=True)
    embed.add_field(name="Hesap Oluşturma", value=f"<t:{int(member.created_at.timestamp())}:D>", inline=True)
    embed.add_field(name="Sunucuya Katılma", value=f"<t:{int(member.joined_at.timestamp())}:D>", inline=True)
    roles = [r.mention for r in member.roles if r.name != "@everyone"]
    embed.add_field(name=f"Roller ({len(roles)})", value=", ".join(roles) if roles else "Yok", inline=False)
    await ctx.send(embed=embed)


@bot.hybrid_command(name="rolver", description="Bir üyeye rol verir.")
@commands.has_permissions(manage_roles=True)
async def give_role(ctx: commands.Context, member: discord.Member, role: discord.Role):
    if role >= ctx.author.top_role and ctx.author.id != ctx.guild.owner_id:
        return await ctx.send("❌ Bu rolü veremezsin, senin rolünden yüksek veya eşit.")
    await member.add_roles(role)
    await ctx.send(f"✅ **{role.name}** rolü **{member}** kullanıcısına verildi.")


@bot.hybrid_command(name="rolal", description="Bir üyeden rol alır.")
@commands.has_permissions(manage_roles=True)
async def remove_role(ctx: commands.Context, member: discord.Member, role: discord.Role):
    if role >= ctx.author.top_role and ctx.author.id != ctx.guild.owner_id:
        return await ctx.send("❌ Bu rolü alamazsın, senin rolünden yüksek veya eşit.")
    await member.remove_roles(role)
    await ctx.send(f"✅ **{role.name}** rolü **{member}** kullanıcısından alındı.")


@bot.hybrid_command(name="isimdegistir", description="Bir üyenin sunucu takma adını değiştirir.")
@commands.has_permissions(manage_nicknames=True)
async def set_nick(ctx: commands.Context, member: discord.Member, *, nick: str):
    await member.edit(nick=nick)
    await ctx.send(f"✅ **{member}** kullanıcısının ismi **{nick}** olarak değiştirildi.")


@bot.hybrid_command(name="logkanal", description="Genel bot loglarının gönderileceği kanalı ayarlar.")
@is_admin()
async def set_log_channel(ctx: commands.Context, channel: discord.TextChannel):
    gd(ctx.guild.id)["log_channel"] = str(channel.id)
    save_data()
    await ctx.send(f"✅ Log kanalı {channel.mention} olarak ayarlandı.")


class SelfRoleButton(discord.ui.Button):
    """Kendinden rol alma/çıkarma butonu — tıklayınca rolü toggle eder."""

    def __init__(self, role_id: int, emoji: str, label: str = None):
        super().__init__(
            label=label,
            emoji=emoji,
            style=discord.ButtonStyle.blurple,
            custom_id=f"selfrole_{role_id}",
        )
        self.role_id = role_id

    async def callback(self, interaction: discord.Interaction):
        role = interaction.guild.get_role(self.role_id)
        if not role:
            return await interaction.response.send_message("❌ Rol bulunamadı, silinmiş olabilir.", ephemeral=True)
        member = interaction.user
        if role in member.roles:
            await member.remove_roles(role)
            await interaction.response.send_message(f"➖ **{role.name}** rolü senden alındı.", ephemeral=True)
        else:
            await member.add_roles(role)
            await interaction.response.send_message(f"➕ **{role.name}** rolü sana verildi.", ephemeral=True)


class SelfRoleView(discord.ui.View):
    def __init__(self, guild_id: int):
        super().__init__(timeout=None)
        g = gd(guild_id)
        for item in g.get("selfroles", []):
            self.add_item(SelfRoleButton(int(item["role_id"]), item["emoji"], item.get("label")))


@bot.hybrid_command(name="selfrol_ekle", description="Kendinden rol alma panelina yeni bir rol ekler.")
@is_mod()
async def add_selfrole(ctx: commands.Context, emoji: str, role: discord.Role, *, etiket: str = None):
    g = gd(ctx.guild.id)
    g.setdefault("selfroles", [])
    g["selfroles"].append({"emoji": emoji, "role_id": str(role.id), "label": etiket or role.name})
    save_data()
    await ctx.send(f"✅ {emoji} **{role.name}** kendinden rol listesine eklendi.")


@bot.hybrid_command(name="selfrol_sil", description="Kendinden rol listesinden bir rolü kaldırır.")
@is_mod()
async def remove_selfrole(ctx: commands.Context, role: discord.Role):
    g = gd(ctx.guild.id)
    g["selfroles"] = [i for i in g.get("selfroles", []) if str(i["role_id"]) != str(role.id)]
    save_data()
    await ctx.send(f"🗑️ **{role.name}** kendinden rol listesinden kaldırıldı.")


@bot.hybrid_command(name="selfrol_panel", description="Butonlu kendinden rol alma panelini gönderir.")
@is_mod()
async def selfrole_panel_cmd(ctx: commands.Context):
    g = gd(ctx.guild.id)
    if not g.get("selfroles"):
        return await ctx.send("❌ Henüz eklenmiş bir kendinden rol yok. Önce `selfrol_ekle` ile rol ekle.")
    embed = discord.Embed(
        title="🎭 Rol Seç",
        description="Aşağıdaki butonlara tıklayarak ilgili rolü alabilir ya da çıkarabilirsin.",
        color=discord.Color.purple(),
    )
    await ctx.send(embed=embed, view=SelfRoleView(ctx.guild.id))


HELP_EMBEDS = {
    "moderasyon": discord.Embed(
        title="🛡️ Moderasyon",
        description="`kick` `ban` `unban` `mute` `unmute` `warn` `uyarilar` `uyarisil` `temizle`\n\n"
                    "*Kick ve ban komutları artık ✅/🛑 onay butonlarıyla çalışır.*",
        color=discord.Color.orange(),
    ),
    "automod": discord.Embed(
        title="🤖 Automod",
        description="`automod_ac` `automod_kapat` `kelime_ekle` `kelime_sil` `automod_ayar`\n\n"
                    "*automod_ayar ile `davet`, `link`, `spam` korumalarını aç/kapat.*",
        color=discord.Color.dark_teal(),
    ),
    "hosgeldin": discord.Embed(
        title="👋 Hoşgeldin",
        description="`hosgeldin_kanal` `hosgeldin_mesaj` `ayrilis_kanal` `ayrilis_mesaj` `otorol`",
        color=discord.Color.green(),
    ),
    "cekilis": discord.Embed(
        title="🎉 Çekiliş",
        description="`cekilis_baslat` `cekilis_bitir` `cekilis_yenidencek`\n\n"
                    "*Artık katılım 🎉 emojili buton ile yapılır, canlı katılımcı sayısı görünür.*",
        color=discord.Color.blurple(),
    ),
    "eglence": discord.Embed(
        title="🎮 Eğlence",
        description="`8top` `zar` `yaziturra` `saka` `soru` `tkm` (🪨📄✂️ buton ile taş-kağıt-makas)",
        color=discord.Color.magenta(),
    ),
    "ticket": discord.Embed(
        title="🎫 Ticket",
        description="`ticket_panel` `ticket_kategori` `ticket_log`\n\n"
                    "*Panel artık 🎫🛠️⚠️💡💰 kategorili açılır menü ile çalışır.*",
        color=discord.Color.teal(),
    ),
    "koruma": discord.Embed(
        title="🔒 Koruma",
        description="`koruma_raid` `koruma_hesapyasi` `koruma_durum`",
        color=discord.Color.dark_red(),
    ),
    "yonetim": discord.Embed(
        title="⚙️ Yönetim",
        description="`sunucubilgi` `kullanicibilgi` `rolver` `rolal` `isimdegistir` `logkanal`\n"
                    "`selfrol_ekle` `selfrol_sil` `selfrol_panel` (🎭 buton ile kendinden rol alma)",
        color=discord.Color.blue(),
    ),
    "reklam": discord.Embed(
        title="📢 Reklam & Büyüme",
        description="`reklam_kanal` `reklam_cooldown` — reklam kanalındaki mesajlar otomatik embed'e çevrilir, 👍/👎 oy butonu eklenir.\n"
                    "`bump_kanal` `bump_rol` `bump_baslat` — Disboard `/bump` algılanır, 2 saat sonra 🔔 hatırlatılır.\n"
                    "`davet_liderlik` `davetlerim` — 🏆 kim kaç kişi davet etti, liderlik tablosu.",
        color=discord.Color.dark_gold(),
    ),
}


class HelpSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="Moderasyon", emoji="🛡️", value="moderasyon", description="Kick, ban, mute, warn..."),
            discord.SelectOption(label="Automod", emoji="🤖", value="automod", description="Yasaklı kelime, filtreler"),
            discord.SelectOption(label="Hoşgeldin", emoji="👋", value="hosgeldin", description="Karşılama/ayrılış ayarları"),
            discord.SelectOption(label="Çekiliş", emoji="🎉", value="cekilis", description="Buton ile çekiliş sistemi"),
            discord.SelectOption(label="Eğlence", emoji="🎮", value="eglence", description="Mini oyunlar ve eğlence"),
            discord.SelectOption(label="Ticket", emoji="🎫", value="ticket", description="Kategorili destek sistemi"),
            discord.SelectOption(label="Koruma", emoji="🔒", value="koruma", description="Anti-raid ve koruma"),
            discord.SelectOption(label="Yönetim", emoji="⚙️", value="yonetim", description="Sunucu yönetim komutları"),
            discord.SelectOption(label="Reklam & Büyüme", emoji="📢", value="reklam", description="Reklam kanalı, bump, davet takibi"),
        ]
        super().__init__(placeholder="📖 Bir modül seç...", options=options, min_values=1, max_values=1)

    async def callback(self, interaction: discord.Interaction):
        embed = HELP_EMBEDS[self.values[0]]
        await interaction.response.edit_message(embed=embed, view=self.view)


class HelpView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=60)
        self.add_item(HelpSelect())


@bot.hybrid_command(name="yardim", description="Açılır menülü komut/modül listesini gösterir.")
async def help_cmd(ctx: commands.Context):
    embed = discord.Embed(
        title="📖 Komut Menüsü",
        description=f"Prefix: `{PREFIX}` — Komutlar hem `{PREFIX}komut` hem de `/komut` şeklinde kullanılabilir.\n\n"
                    "👇 Aşağıdaki menüden bir modül seçerek o modülün komutlarını görebilirsin.",
        color=discord.Color.gold(),
    )
    embed.add_field(
        name="Modüller",
        value="🛡️ Moderasyon · 🤖 Automod · 👋 Hoşgeldin · 🎉 Çekiliş\n🎮 Eğlence · 🎫 Ticket · 🔒 Koruma · ⚙️ Yönetim · 📢 Reklam & Büyüme",
        inline=False,
    )
    await ctx.send(embed=embed, view=HelpView())


# ================================================================
#                            ÇALIŞTIR
# ================================================================
if __name__ == "__main__":
    if TOKEN == "BURAYA_BOT_TOKENINI_YAZ":
        print("[!] Lütfen TOKEN değişkenine bot tokenini yaz ya da DISCORD_TOKEN ortam değişkenini ayarla.")
    bot.run(TOKEN)

