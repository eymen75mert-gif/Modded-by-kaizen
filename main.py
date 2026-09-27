"""
Katre Discord Botu
-------------------
Tek dosyalık, Railway Variables ile yapılandırılabilir Discord botu.
Özellikler:
  - Destek sunucusu / davet linki komutları
  - Sunucu bazlı Reklam sistemi (kanal ayarla, aç/kapat, zorunlu sunucu şartı)
  - Süreli Pro üyelik sistemi (bot sahibi tarafından verilir/alınır)
  - Basit JSON tabanlı kalıcı veri (Railway'de kalıcı disk yoksa redeploy'da sıfırlanır,
    kalıcı istiyorsan Railway Volume ekleyebilirsin)

Gerekli paket: discord.py>=2.3.2  (requirements.txt içinde)
Çalıştırma: python katre.py
"""

import os
import re
import json
import time
from datetime import datetime

import discord
from discord.ext import commands, tasks

# ============================================================
# 1) YAPILANDIRMA — Railway Variables sekmesinden ayarlanır
# ============================================================
TOKEN = os.getenv("DISCORD_TOKEN")                       # ZORUNLU: Bot token'ı
PREFIX = os.getenv("PREFIX", ".")                         # Komut ön eki
SUPPORT_SERVER_INVITE = os.getenv("SUPPORT_SERVER_INVITE", "")  # Destek sunucusu davet linki
CLIENT_ID = os.getenv("CLIENT_ID", "")                    # Botun uygulama (client) ID'si -> davet linki üretmek için
BOT_INVITE_URL = os.getenv("BOT_INVITE_URL", "")          # (Opsiyonel) hazır davet linki verirsen bu kullanılır

# Bot sahipleri (senin kullanıcı ID'lerin) - Pro sistemini sadece bunlar yönetebilir
OWNER_IDS = {int(x) for x in os.getenv("OWNER_IDS", "").split(",") if x.strip().isdigit()}

# Emojiler - istersen kendi (animasyonlu/Nitro) özel emojini <a:isim:id> formatında girebilirsin
EMOJI_CHECK = os.getenv("EMOJI_CHECK", "✅")
EMOJI_CROSS = os.getenv("EMOJI_CROSS", "❌")
EMOJI_PRO = os.getenv("EMOJI_PRO", "⭐")
EMOJI_AD = os.getenv("EMOJI_AD", "📢")

try:
    EMBED_COLOR = int(os.getenv("EMBED_COLOR", "2f3136"), 16)
except ValueError:
    EMBED_COLOR = 0x2f3136

DATA_FILE = "katre_data.json"

# ============================================================
# 2) VERİ KATMANI
# ============================================================
def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                d = json.load(f)
        except Exception:
            d = {}
    else:
        d = {}
    d.setdefault("guilds", {})
    d.setdefault("pro_users", {})
    d.setdefault("reklam_cooldown", {})
    return d


def save_data(d):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)


data = load_data()


def get_guild_data(guild_id):
    gid = str(guild_id)
    if gid not in data["guilds"]:
        data["guilds"][gid] = {
            "reklam_kanal": None,
            "reklam_acik": False,
            "reklam_sunucu_id": None,
            "reklam_sunucu_invite": None,
        }
        save_data(data)
    return data["guilds"][gid]


def is_pro(user_id):
    uid = str(user_id)
    if uid not in data["pro_users"]:
        return False
    exp = data["pro_users"][uid]
    if exp is None:
        return True
    if exp <= time.time():
        del data["pro_users"][uid]
        save_data(data)
        return False
    return True


def parse_sure(s: str):
    """'7g' -> 7 gün, '2a' -> 2 ay, '30dk' -> 30 dakika, 'sonsuz' -> süresiz (None)."""
    s = s.lower().strip()
    if s in ("sonsuz", "kalıcı", "kalici", "süresiz", "suresiz"):
        return None
    birimler = {
        "dk": 60, "dakika": 60, "m": 60,
        "s": 3600, "sa": 3600, "saat": 3600, "h": 3600,
        "g": 86400, "gün": 86400, "gun": 86400, "d": 86400,
        "a": 2592000, "ay": 2592000,
        "y": 31536000, "yıl": 31536000, "yil": 31536000,
    }
    m = re.match(r"^(\d+)\s*([a-zçğıöşü]+)$", s)
    if not m:
        return False
    miktar, birim = m.groups()
    if birim not in birimler:
        return False
    return int(miktar) * birimler[birim]


def format_sure(saniye):
    saniye = int(saniye)
    saat, kalan = divmod(saniye, 3600)
    dakika, sn = divmod(kalan, 60)
    parcalar = []
    if saat:
        parcalar.append(f"{saat} saat")
    if dakika:
        parcalar.append(f"{dakika} dakika")
    if sn and not saat:
        parcalar.append(f"{sn} saniye")
    return " ".join(parcalar) if parcalar else "birkaç saniye"


def success_embed(msg):
    return discord.Embed(description=f"{EMOJI_CHECK} {msg}", color=EMBED_COLOR)


def error_embed(msg):
    return discord.Embed(description=f"{EMOJI_CROSS} {msg}", color=EMBED_COLOR)


# ============================================================
# 3) BOT KURULUMU
# ============================================================
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix=PREFIX, intents=intents, help_command=None)


@bot.event
async def on_ready():
    if not pro_expiry_check.is_running():
        pro_expiry_check.start()
    try:
        await bot.change_presence(activity=discord.Game(name=f"{PREFIX}yardım | Katre"))
    except Exception:
        pass
    print(f"[Katre] {bot.user} olarak giriş yapıldı. {len(bot.guilds)} sunucuda aktif.")


@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        return await ctx.send(embed=error_embed("Bu komutu kullanmak için yeterli yetkin yok."))
    if isinstance(error, commands.CommandNotFound):
        return
    if isinstance(error, commands.MemberNotFound):
        return await ctx.send(embed=error_embed("Kullanıcı bulunamadı."))
    if isinstance(error, commands.ChannelNotFound):
        return await ctx.send(embed=error_embed("Kanal bulunamadı."))
    if isinstance(error, commands.MissingRequiredArgument):
        return await ctx.send(embed=error_embed(f"Eksik parametre. Yardım için `{PREFIX}yardım` yaz."))
    if isinstance(error, commands.NoPrivateMessage):
        return await ctx.send(embed=error_embed("Bu komut sadece sunucularda kullanılabilir."))
    print(f"[Katre] Beklenmeyen hata: {error!r}")


# ============================================================
# 4) GENEL KOMUTLAR
# ============================================================
@bot.command(name="yardim", aliases=["yardım", "help"])
async def yardim(ctx):
    embed = discord.Embed(title="📖 Katre Komutları", color=EMBED_COLOR)
    embed.add_field(name="Genel", value=f"`{PREFIX}destek`, `{PREFIX}davet`, `{PREFIX}ping`, `{PREFIX}pro [@kullanıcı]`", inline=False)
    embed.add_field(
        name="Reklam Sistemi (Yetkili)",
        value=f"`{PREFIX}reklamayarla #kanal`, `{PREFIX}reklamac`, `{PREFIX}reklamkapat`, `{PREFIX}reklamsunucu <link>`, `{PREFIX}reklamdurum`",
        inline=False,
    )
    embed.add_field(name="Reklam (Herkes)", value=f"`{PREFIX}reklam <mesaj>`", inline=False)
    embed.add_field(
        name="Pro Yönetimi (Bot Sahibi)",
        value=f"`{PREFIX}proekle @kullanıcı <süre>`, `{PREFIX}prosil @kullanıcı`, `{PREFIX}prolist`",
        inline=False,
    )
    embed.set_footer(text="Katre Bot")
    await ctx.send(embed=embed)


@bot.command(name="ping")
async def ping(ctx):
    await ctx.send(embed=discord.Embed(description=f"🏓 Pong! `{round(bot.latency * 1000)}ms`", color=EMBED_COLOR))


@bot.command(name="destek")
async def destek(ctx):
    if not SUPPORT_SERVER_INVITE:
        return await ctx.send(embed=error_embed("Destek sunucusu ayarlanmamış. (SUPPORT_SERVER_INVITE değişkenini gir)"))
    embed = discord.Embed(title="🛠️ Destek Sunucusu", description=f"Sorularınız / önerileriniz için: {SUPPORT_SERVER_INVITE}", color=EMBED_COLOR)
    await ctx.send(embed=embed)


@bot.command(name="davet")
async def davet(ctx):
    if BOT_INVITE_URL:
        link = BOT_INVITE_URL
    elif CLIENT_ID:
        link = f"https://discord.com/oauth2/authorize?client_id={CLIENT_ID}&permissions=8&scope=bot%20applications.commands"
    elif bot.user:
        link = f"https://discord.com/oauth2/authorize?client_id={bot.user.id}&permissions=8&scope=bot%20applications.commands"
    else:
        return await ctx.send(embed=error_embed("Davet linki oluşturulamadı, CLIENT_ID değişkenini gir."))
    embed = discord.Embed(title="🔗 Katre'yi Sunucuna Davet Et", description=f"[Buraya tıkla]({link})", color=EMBED_COLOR)
    await ctx.send(embed=embed)


# ============================================================
# 5) REKLAM SİSTEMİ
# ============================================================
@bot.command(name="reklamayarla")
@commands.has_permissions(manage_guild=True)
@commands.guild_only()
async def reklamayarla(ctx, kanal: discord.TextChannel = None):
    if not kanal:
        return await ctx.send(embed=error_embed(f"Kullanım: `{PREFIX}reklamayarla #kanal`"))
    gdata = get_guild_data(ctx.guild.id)
    gdata["reklam_kanal"] = kanal.id
    save_data(data)
    await ctx.send(embed=success_embed(f"Reklam kanalı {kanal.mention} olarak ayarlandı."))


@bot.command(name="reklamac", aliases=["reklamaç"])
@commands.has_permissions(manage_guild=True)
@commands.guild_only()
async def reklamac(ctx):
    gdata = get_guild_data(ctx.guild.id)
    gdata["reklam_acik"] = True
    save_data(data)
    await ctx.send(embed=success_embed("Reklam sistemi bu sunucuda açıldı."))


@bot.command(name="reklamkapat")
@commands.has_permissions(manage_guild=True)
@commands.guild_only()
async def reklamkapat(ctx):
    gdata = get_guild_data(ctx.guild.id)
    gdata["reklam_acik"] = False
    save_data(data)
    await ctx.send(embed=success_embed("Reklam sistemi bu sunucuda kapatıldı."))


@bot.command(name="reklamsunucu")
@commands.has_permissions(manage_guild=True)
@commands.guild_only()
async def reklamsunucu(ctx, invite_link: str = None):
    """Reklam vermek için kullanıcıların katılması zorunlu sunucuyu ayarlar."""
    gdata = get_guild_data(ctx.guild.id)
    if not invite_link or invite_link.lower() == "kapat":
        gdata["reklam_sunucu_id"] = None
        gdata["reklam_sunucu_invite"] = None
        save_data(data)
        return await ctx.send(embed=success_embed("Reklam için zorunlu sunucu şartı kaldırıldı."))

    try:
        invite = await bot.fetch_invite(invite_link)
    except Exception:
        return await ctx.send(embed=error_embed("Geçersiz davet linki."))

    if not invite.guild:
        return await ctx.send(embed=error_embed("Bu linkten sunucu bilgisi alınamadı."))

    gdata["reklam_sunucu_id"] = invite.guild.id
    gdata["reklam_sunucu_invite"] = invite_link
    save_data(data)

    uyari = ""
    if not bot.get_guild(invite.guild.id):
        uyari = "\n⚠️ Uyarı: Katre bu sunucuda üye değil, üyelik kontrolü doğru çalışmayabilir. Botu o sunucuya da ekle."

    await ctx.send(embed=success_embed(
        f"Reklam şartı ayarlandı. Artık kullanıcılar **{invite.guild.name}** sunucusuna katılmadan reklam veremeyecek.{uyari}"
    ))


@bot.command(name="reklamdurum")
@commands.guild_only()
async def reklamdurum(ctx):
    gdata = get_guild_data(ctx.guild.id)
    kanal = ctx.guild.get_channel(gdata["reklam_kanal"]) if gdata["reklam_kanal"] else None
    sunucu_adi = "Yok"
    if gdata.get("reklam_sunucu_id"):
        g = bot.get_guild(gdata["reklam_sunucu_id"])
        sunucu_adi = g.name if g else f"ID: {gdata['reklam_sunucu_id']}"
    embed = discord.Embed(title="📋 Reklam Sistemi Durumu", color=EMBED_COLOR)
    embed.add_field(name="Durum", value="✅ Açık" if gdata["reklam_acik"] else "❌ Kapalı", inline=True)
    embed.add_field(name="Kanal", value=kanal.mention if kanal else "Ayarlanmadı", inline=True)
    embed.add_field(name="Zorunlu Sunucu", value=sunucu_adi, inline=True)
    await ctx.send(embed=embed)


@bot.command(name="reklam")
@commands.guild_only()
async def reklam(ctx, *, mesaj: str = None):
    gdata = get_guild_data(ctx.guild.id)

    if not gdata["reklam_acik"]:
        return await ctx.send(embed=error_embed("Bu sunucuda reklam sistemi kapalı."))
    if not gdata["reklam_kanal"]:
        return await ctx.send(embed=error_embed(f"Reklam kanalı ayarlanmamış. Bir yetkili `{PREFIX}reklamayarla #kanal` komutunu kullanmalı."))
    if not mesaj:
        return await ctx.send(embed=error_embed(f"Kullanım: `{PREFIX}reklam <mesajınız>`"))

    pro = is_pro(ctx.author.id)

    # Zorunlu sunucu kontrolü (Pro üyeler muaf)
    required_guild_id = gdata.get("reklam_sunucu_id")
    if required_guild_id and not pro:
        required_guild = bot.get_guild(required_guild_id)
        member = required_guild.get_member(ctx.author.id) if required_guild else None
        if not member:
            invite = gdata.get("reklam_sunucu_invite") or SUPPORT_SERVER_INVITE or "(link ayarlanmamış)"
            return await ctx.send(embed=error_embed(
                f"Reklam verebilmek için önce şu sunucuya katılmalısın:\n{invite}"
            ))

    # Bekleme süresi (Pro üyeler için daha kısa)
    now = time.time()
    cooldown_seconds = 1800 if pro else 3600
    last = data["reklam_cooldown"].get(str(ctx.author.id), 0)
    if now - last < cooldown_seconds:
        kalan = cooldown_seconds - (now - last)
        return await ctx.send(embed=error_embed(f"Tekrar reklam verebilmek için {format_sure(kalan)} beklemelisin."))

    kanal = ctx.guild.get_channel(gdata["reklam_kanal"])
    if not kanal:
        return await ctx.send(embed=error_embed("Ayarlanan reklam kanalı bulunamıyor, bir yetkili tekrar ayarlamalı."))

    embed = discord.Embed(title=f"{EMOJI_AD} Yeni Reklam", description=mesaj, color=EMBED_COLOR, timestamp=datetime.utcnow())
    embed.set_author(name=str(ctx.author), icon_url=ctx.author.display_avatar.url)
    if pro:
        embed.set_footer(text=f"{EMOJI_PRO} Pro Üye")

    try:
        await kanal.send(embed=embed)
    except discord.Forbidden:
        return await ctx.send(embed=error_embed("Reklam kanalına mesaj gönderme yetkim yok."))

    data["reklam_cooldown"][str(ctx.author.id)] = now
    save_data(data)
    try:
        await ctx.message.add_reaction(EMOJI_CHECK)
    except Exception:
        pass


# ============================================================
# 6) PRO ÜYELİK SİSTEMİ (bot sahibi tarafından yönetilir)
# ============================================================
def owner_only(ctx):
    return ctx.author.id in OWNER_IDS


@bot.command(name="proekle")
async def proekle(ctx, member: discord.Member = None, sure: str = None):
    if not owner_only(ctx):
        return await ctx.send(embed=error_embed("Bu komutu sadece bot sahipleri kullanabilir."))
    if not member or not sure:
        return await ctx.send(embed=error_embed(f"Kullanım: `{PREFIX}proekle @kullanıcı <süre>` (örnek: 7g, 1a, 30dk, sonsuz)"))

    saniye = parse_sure(sure)
    if saniye is False:
        return await ctx.send(embed=error_embed("Geçersiz süre formatı. Örnek: `7g`, `2a`, `30dk`, `sonsuz`"))

    expiry = None if saniye is None else time.time() + saniye
    data["pro_users"][str(member.id)] = expiry
    save_data(data)

    bitis = "Süresiz ♾️" if expiry is None else datetime.fromtimestamp(expiry).strftime("%d.%m.%Y %H:%M")
    await ctx.send(embed=success_embed(f"{member.mention} artık **Pro** üye! Bitiş: {bitis}"))

    try:
        await member.send(embed=discord.Embed(
            title=f"{EMOJI_PRO} Pro Üyelik Aktifleşti",
            description=f"Katre botunda Pro üyeliğin başladı!\nBitiş: {bitis}",
            color=EMBED_COLOR,
        ))
    except discord.Forbidden:
        pass


@bot.command(name="prosil")
async def prosil(ctx, member: discord.Member = None):
    if not owner_only(ctx):
        return await ctx.send(embed=error_embed("Bu komutu sadece bot sahipleri kullanabilir."))
    if not member:
        return await ctx.send(embed=error_embed(f"Kullanım: `{PREFIX}prosil @kullanıcı`"))
    if str(member.id) not in data["pro_users"]:
        return await ctx.send(embed=error_embed(f"{member.mention} zaten Pro üye değil."))
    del data["pro_users"][str(member.id)]
    save_data(data)
    await ctx.send(embed=success_embed(f"{member.mention} kullanıcısının Pro üyeliği kaldırıldı."))


@bot.command(name="prolist")
async def prolist(ctx):
    if not owner_only(ctx):
        return await ctx.send(embed=error_embed("Bu komutu sadece bot sahipleri kullanabilir."))
    if not data["pro_users"]:
        return await ctx.send(embed=error_embed("Henüz Pro üye yok."))
    satirlar = []
    for uid, exp in data["pro_users"].items():
        bitis = "Süresiz" if exp is None else datetime.fromtimestamp(exp).strftime("%d.%m.%Y %H:%M")
        satirlar.append(f"<@{uid}> — {bitis}")
    embed = discord.Embed(title=f"{EMOJI_PRO} Pro Üyeler", description="\n".join(satirlar)[:4000], color=EMBED_COLOR)
    await ctx.send(embed=embed)


@bot.command(name="pro")
async def pro_bilgi(ctx, member: discord.Member = None):
    member = member or ctx.author
    if str(member.id) not in data["pro_users"] or not is_pro(member.id):
        return await ctx.send(embed=error_embed(f"{member.mention} Pro üye değil."))
    exp = data["pro_users"][str(member.id)]
    bitis = "Süresiz ♾️" if exp is None else datetime.fromtimestamp(exp).strftime("%d.%m.%Y %H:%M")
    embed = discord.Embed(title=f"{EMOJI_PRO} Pro Üyelik Bilgisi", color=EMBED_COLOR)
    embed.add_field(name="Kullanıcı", value=member.mention)
    embed.add_field(name="Bitiş Tarihi", value=bitis)
    await ctx.send(embed=embed)


@tasks.loop(minutes=5)
async def pro_expiry_check():
    now = time.time()
    expired = [uid for uid, exp in list(data["pro_users"].items()) if exp is not None and exp <= now]
    for uid in expired:
        del data["pro_users"][uid]
        user = bot.get_user(int(uid))
        if user:
            try:
                await user.send(embed=discord.Embed(
                    title="Pro Üyelik Sona Erdi",
                    description="Katre botundaki Pro üyeliğin sona erdi.",
                    color=EMBED_COLOR,
                ))
            except discord.Forbidden:
                pass
    if expired:
        save_data(data)


# ============================================================
# 7) BOT SAHİBİ GENEL KOMUTLAR
# ============================================================
@bot.command(name="sunucular")
async def sunucular(ctx):
    if not owner_only(ctx):
        return
    isimler = "\n".join(f"{g.name} — {g.member_count} üye" for g in bot.guilds) or "Yok"
    await ctx.send(embed=discord.Embed(title=f"Katre {len(bot.guilds)} sunucuda", description=isimler[:4000], color=EMBED_COLOR))


@bot.command(name="duyuru")
async def duyuru(ctx, *, mesaj: str = None):
    if not owner_only(ctx):
        return
    if not mesaj:
        return await ctx.send(embed=error_embed(f"Kullanım: `{PREFIX}duyuru <mesaj>`"))
    gonderildi = 0
    for g in bot.guilds:
        kanal = g.system_channel
        if kanal:
            try:
                await kanal.send(embed=discord.Embed(title="📢 Katre Duyurusu", description=mesaj, color=EMBED_COLOR))
                gonderildi += 1
            except Exception:
                pass
    await ctx.send(embed=success_embed(f"Duyuru {gonderildi} sunucuya gönderildi."))


# ============================================================
# 8) BAŞLAT
# ============================================================
if __name__ == "__main__":
    if not TOKEN:
        raise SystemExit("HATA: DISCORD_TOKEN ortam değişkeni ayarlanmamış! Railway > Variables kısmına ekle.")
    bot.run(TOKEN)
