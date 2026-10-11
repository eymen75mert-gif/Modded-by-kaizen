# marpel_clone_v2.py
# Eklenen: Yanıt Emoji Sistemi, Half-Owner, Reklam Sistemi

import discord
from discord.ext import commands, tasks
import aiosqlite
import asyncio
import json
import os
import re
import random
from datetime import datetime, timedelta

# ─────────────────────────────────────────────
#   KONFİG
# ─────────────────────────────────────────────
CONFIG_PATH = "config.json"
DEFAULT_CONFIG = {
    "token": "TOKEN_BURAYA",
    "prefix": "m!",
    "owner_ids": []
}

def load_config():
    if not os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(DEFAULT_CONFIG, f, indent=2)
        return dict(DEFAULT_CONFIG)
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return {**DEFAULT_CONFIG, **json.load(f)}

config = load_config()
EMOJI_REGEX = re.compile(r"<a?:(\w+):(\d+)>")

# ─────────────────────────────────────────────
#   VERİTABANI
# ─────────────────────────────────────────────
class Database:
    def __init__(self, path="marpel.db"):
        self.path = path

    async def init(self):
        async with aiosqlite.connect(self.path) as db:
            await db.executescript("""
                CREATE TABLE IF NOT EXISTS guild_settings (
                    guild_id INTEGER PRIMARY KEY,
                    log_channel INTEGER,
                    stats_channel INTEGER,
                    ticket_category INTEGER,
                    temp_room_category INTEGER,
                    welcome_channel INTEGER,
                    ad_channel INTEGER,
                    ad_interval INTEGER DEFAULT 3600,
                    prefix TEXT DEFAULT 'm!'
                );
                CREATE TABLE IF NOT EXISTS ranks (
                    guild_id INTEGER, user_id INTEGER,
                    xp INTEGER DEFAULT 0, level INTEGER DEFAULT 0,
                    messages INTEGER DEFAULT 0,
                    PRIMARY KEY (guild_id, user_id)
                );
                CREATE TABLE IF NOT EXISTS giveaways (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    guild_id INTEGER, channel_id INTEGER, message_id INTEGER,
                    prize TEXT, winners INTEGER, end_time TIMESTAMP,
                    ended BOOLEAN DEFAULT 0, host_id INTEGER
                );
                CREATE TABLE IF NOT EXISTS giveaway_entries (
                    giveaway_id INTEGER, user_id INTEGER,
                    PRIMARY KEY (giveaway_id, user_id)
                );
                CREATE TABLE IF NOT EXISTS tickets (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    guild_id INTEGER, channel_id INTEGER, user_id INTEGER,
                    status TEXT DEFAULT 'open',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                CREATE TABLE IF NOT EXISTS invites (
                    guild_id INTEGER, user_id INTEGER,
                    joins INTEGER DEFAULT 0, leaves INTEGER DEFAULT 0,
                    fake INTEGER DEFAULT 0,
                    PRIMARY KEY (guild_id, user_id)
                );
                CREATE TABLE IF NOT EXISTS reaction_roles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    guild_id INTEGER, message_id INTEGER, channel_id INTEGER,
                    emoji TEXT, role_id INTEGER
                );
                CREATE TABLE IF NOT EXISTS button_roles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    guild_id INTEGER, message_id INTEGER, channel_id INTEGER,
                    label TEXT, role_id INTEGER, emoji TEXT
                );
                CREATE TABLE IF NOT EXISTS temp_rooms (
                    guild_id INTEGER, user_id INTEGER, channel_id INTEGER,
                    PRIMARY KEY (guild_id, user_id)
                );
                CREATE TABLE IF NOT EXISTS birthdays (
                    guild_id INTEGER, user_id INTEGER,
                    day INTEGER, month INTEGER, year INTEGER,
                    PRIMARY KEY (guild_id, user_id)
                );
                CREATE TABLE IF NOT EXISTS notes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    guild_id INTEGER, user_id INTEGER,
                    content TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                CREATE TABLE IF NOT EXISTS nitro_emojis (
                    guild_id INTEGER, name TEXT, url TEXT,
                    PRIMARY KEY (guild_id, name)
                );
                -- ⭐ YENİ: Bot yanıt emojileri (cevap tipi → emoji)
                CREATE TABLE IF NOT EXISTS response_emojis (
                    guild_id INTEGER,
                    response_key TEXT,
                    emoji TEXT,
                    PRIMARY KEY (guild_id, response_key)
                );
                -- ⭐ YENİ: Half-Owner sistemi
                CREATE TABLE IF NOT EXISTS half_owners (
                    guild_id INTEGER,
                    user_id INTEGER,
                    added_by INTEGER,
                    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (guild_id, user_id)
                );
                -- ⭐ YENİ: Reklam sistemi
                CREATE TABLE IF NOT EXISTS ads (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    guild_id INTEGER,
                    author_id INTEGER,
                    content TEXT,
                    channel_id INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    active BOOLEAN DEFAULT 1,
                    views INTEGER DEFAULT 0
                );
                CREATE TABLE IF NOT EXISTS ad_settings (
                    guild_id INTEGER PRIMARY KEY,
                    auto_post_channel INTEGER,
                    auto_post_interval INTEGER DEFAULT 3600,
                    last_posted TIMESTAMP,
                    min_length INTEGER DEFAULT 20,
                    max_length INTEGER DEFAULT 500,
                    cooldown INTEGER DEFAULT 300
                );
                CREATE TABLE IF NOT EXISTS ad_cooldowns (
                    guild_id INTEGER, user_id INTEGER,
                    last_ad TIMESTAMP,
                    PRIMARY KEY (guild_id, user_id)
                );
            """)
            await db.commit()

    async def execute(self, q, *a):
        async with aiosqlite.connect(self.path) as db:
            await db.execute(q, a); await db.commit()

    async def fetchone(self, q, *a):
        async with aiosqlite.connect(self.path) as db:
            async with db.execute(q, a) as c:
                return await c.fetchone()

    async def fetchall(self, q, *a):
        async with aiosqlite.connect(self.path) as db:
            async with db.execute(q, a) as c:
                return await c.fetchall()

db = Database()

# ─────────────────────────────────────────────
#   YANIT EMOJİ YÖNETİCİSİ
# ─────────────────────────────────────────────
DEFAULT_RESPONSES = {
    "success": "✅",
    "error": "❌",
    "warning": "⚠️",
    "info": "ℹ️",
    "loading": "⏳",
    "ticket": "🎫",
    "giveaway": "🎉",
    "rank": "🏆",
    "log": "📜",
    "ad": "📢",
    "shield": "🛡️",
    "heart": "💖",
}

class ResponseEmoji:
    """Bot cevaplarında kullanılan nitro emojileri yönetir. Kalıcıdır (SQLite)."""
    def __init__(self, bot, db):
        self.bot = bot
        self.db = db
        self.cache = {}  # {guild_id: {key: emoji_str}}

    async def load_guild(self, guild_id):
        rows = await self.db.fetchall(
            "SELECT response_key, emoji FROM response_emojis WHERE guild_id=?", guild_id
        )
        self.cache[guild_id] = {k: v for k, v in rows}

    async def set(self, guild_id, key, emoji):
        await self.db.execute(
            "INSERT OR REPLACE INTO response_emojis (guild_id, response_key, emoji) VALUES (?, ?, ?)",
            guild_id, key, emoji
        )
        self.cache.setdefault(guild_id, {})[key] = emoji

    async def remove(self, guild_id, key):
        await self.db.execute(
            "DELETE FROM response_emojis WHERE guild_id=? AND response_key=?",
            guild_id, key
        )
        if guild_id in self.cache and key in self.cache[guild_id]:
            del self.cache[guild_id][key]

    async def get(self, guild_id, key):
        if guild_id not in self.cache:
            await self.load_guild(guild_id)
        return self.cache[guild_id].get(key, DEFAULT_RESPONSES.get(key, "•"))

    async def all(self, guild_id):
        if guild_id not in self.cache:
            await self.load_guild(guild_id)
        merged = dict(DEFAULT_RESPONSES)
        merged.update(self.cache[guild_id])
        return merged

response_emoji = None  # bot başladıkt_categoryan sonra set edilecek

def E(guild_id, key):
    """Async olmayan yerlerde kullanılmaz, sadece referans."""
    pass

async def e(guild_id, key):
    """Kısa helper - await ile kullan."""
    return await response_emoji(".get(guild_id, key)

# ─────────────────────────────────────────────
#   YETKİ KONTROLÜ (Owner + Half-Owner)
# ─────────────────────────────────────────────
async def is_authorized(ctx):
    if ctx.author.id in config["owner_ids"]:
        return True
    if ctx.author.id == ctx.guild.owner_id:
        return True
    if ctx.author.guild_permissions.administrator:
        return True
    row = await db.fetchone(
        "SELECT 1 FROM half_owners WHERE guild_id=? AND user_id=?",
        ctx.guild.id, ctx.author.id
    )
    return row is not None

def check_half_owner():
    async def predicate(ctx):
        return await is_authorized(ctx)
    return commands.check(predicate)

# ─────────────────────────────────────────────
#   BOT
# ─────────────────────────────────────────────
class MarpelBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.all()
        super().__init__(command_prefix=config["prefix"], intents=intents, help_command=None)
        self.ad_task_started = False

    async def setup_hook(self):
        global response_emoji
        await db.init()
        response_emoji = ResponseEmoji(self, db)
        await self.tree.sync()

    async def on_ready(self):
        print(f"[READY] {self.user} - {len(self.guilds)} sunucu")
        await self.change_presence(activity=discord.Activity(
            type=discord.ActivityType.watching, name="m!yardım"))
        if not self.ad_task_started:
            self.ad_loop.start()
            self.ad_task_started = True

    # ─── REKLAM DÖNGÜSÜ ───
    @tasks.loop(minutes=5)
    async def ad_loop(self):
        rows = await db.fetchall("""
            SELECT guild_id, auto_post_channel, auto_post_interval, last_posted
            FROM ad_settings WHERE auto_post_channel IS NOT NULL
        """)
        now = datetime.utcnow()
        for guild_id, channel_id, interval, last_posted in rows:
            guild = self.get_guild(guild_id)
            if not guild: continue
            channel = guild.get_channel(channel_id)
            if not channel: continue
            if last_posted:
                try:
                    last = datetime.fromisoformat(last_posted)
                    if (now - last).total_seconds() < interval:
                        continue
                except Exception:
                    pass
            ads = await db.fetchall(
                "SELECT id, author_id, content FROM ads WHERE guild_id=? AND active=1 ORDER BY RANDOM() LIMIT 1",
                guild_id
            )
            if not ads:
                continue
            aid, author_id, content = ads[0]
            emoji = await response_emoji.get(guild_id, "ad")
            embed = discord.Embed(
                description=f"{emoji} {content}",
                color=0x00BFFF,
                timestamp=now
            )
            embed.set_footer(text=f"Sponsor: {guild.get_member(author_id).display_name if guild.get_member(author_id) else 'Bilinmiyor'}")
            try:
                await channel.send(embed=embed)
                await db.execute("UPDATE ads SET views=views+1 WHERE id=?", aid)
                await db.execute("UPDATE ad_settings SET last_posted=? WHERE guild_id=?",
                                 now.isoformat(), guild_id)
            except Exception as ex:
                print(f"[AD ERROR] {ex}")

bot = MarpelBot()

# ─────────────────────────────────────────────
#   KURULUM - TEK KOMUT
# ─────────────────────────────────────────────
@bot.command(name="kur")
@commands.has_permissions(administrator=True)
async def kur(ctx):
    """
    Tek komutla sunucuyu kurar. Eksik kanalları otomatik oluşturur,
    izinleri ayarlar, her şeyi hazırlar.
    """
    loading = await response_emoji.get(ctx.guild.id, "loading")
    msg = await ctx.send(f"{loading} Kurulum başlatılıyor, boss man...")

    guild = ctx.guild
    me = guild.me

    # 1. Kategoriler ve kanallar
    log_cat = discord.utils.get(guild.categories, name="📜 Marpel Logs")
    if not log_cat:
        log_cat = await guild.create📜 Marpel Logs")

    def find_or_create_channel(name, **kwargs):
        ch = discord.utils.get(guild.text_channels, name=name)
        return ch

    log_ch = find_or_create_channel("marpel-log")
    if not log_ch:
        log_ch = await guild.create_text_channel("marpel-log", category=log_cat)

    stats_ch = find_or_create_channel("marpel-istatistik")
    if not stats_ch:
        stats_ch = await guild.create_text_channel("marpel-istatistik", category=log_cat)

    ad_ch = find_or_create_channel("marpel-reklam")
    if not ad_ch:
        ad_ch = await guild.create_text_channel("marpel-reklam", category=log_cat)

    # Ticket kategorisi
    ticket_cat = discord.utils.get(guild.categories, name="🎫 Destek")
    if not ticket_cat:
        ticket_cat = await guild.create_category("🎫 Destek")

    # Özel oda kategorisi
    room_cat = discord.utils.get(guild.categories, name="🔊 Özel Odalar")
    if not room_cat:
        room_cat = await guild.create_category("🔊 Özel Odalar")
    create_room_ch = discord.utils.get(guild.voice_channels, name="➕ Oda Oluştur")
    if not create_room_ch:
        await guild.create_voice_channel("➕ Oda Oluştur", category=room_cat)

    # 2. Ayarları kaydet
    await db.execute("""
        INSERT OR REPLACE INTO guild_settings
        (guild_id, log_channel, stats_channel, ticket_category, temp_room_category, ad_channel)
        VALUES (?, ?, ?, ?, ?, ?)
    """, guild.id, log_ch.id, stats_ch.id, ticket_cat.id, room_cat.id, ad_ch.id)

    await db.execute("""
        INSERT OR REPLACE INTO ad_settings (guild_id, auto_post_channel, auto_post_interval)
        VALUES (?, ?, ?)
    """, guild.id, ad_ch.id, 3600)

    # 3. Yanıt emojileri varsayılanları yükle
    for key, em in DEFAULT_RESPONSES.items():
        await response_emoji.set(guild.id, key, em)

    success = await response_emoji.get(guild.id, "success")
    embed = discord.Embed(
        title=f"{success} Kurulum Tamamlandı!",
        description=(
            f"**Log:** {log_ch.mention}\n"
            f"**İstatistik:** {stats_ch.mention}\n"
            f"**Reklam:** {ad_ch.mention}\n"
            f"**Destek:** {ticket_cat.name}\n"
            f"**Özel Oda:** {room_cat.name}\n\n"
            f"Kullan: `m!yardım`"
        ),
        color=0x00FFAA
    )
    await msg.edit(content=None, embed=embed)

# ─────────────────────────────────────────────
#   EMOJİ CEVAP AYARLAMA (Owner/Half-Owner)
# ─────────────────────────────────────────────
@bot.group(name="cevapemoji", invoke_without_command=True)
@check_half_owner()
async def cevapemoji(ctx):
    """Bot cevaplarında kullanılan nitro emojileri ayarlar. Kalıcıdır."""
    all_em = await response_emoji.all(ctx.guild.id)
    lines = [f"`{k}` → {v}" for k, v in all_em.items()]
    embed = discord.Embed(
        title="🎨 Yanıt Emojileri",
        description="\n".join(lines),
        color=0x5865F2
    )
    embed.set_footer(text="Ayarla: m!cevapemoji ayarla <anahtar> <emoji>  |  Sıfırla: m!cevapemoji sıfırla <anahtar>")
    await ctx.send(embed=embed)

@cevapemoji.command(name="ayarla")
@check_half_owner()
async def cevapemoji_ayarla(ctx, anahtar: str, *, emoji_input: str):
    """
    Bir cevap tipi için emoji ayarlar.
    Örnek: m!cevapemoji ayarla success <:onay:123456789>
    Örnek: m!cevapemoji ayarla error <a:hata:987654321>
    """
    if anahtar not in DEFAULT_RESPONSES:
        err = await response_emoji.get(ctx.guild.id, "error")
        keys = ", ".join(f"`{k}`" for k in DEFAULT_RESPONSES)
        await ctx.send(f"{err} Geçersiz anahtar. Geçerli: {keys}")
        return

    # Emoji formatı kontrol
    stripped = emoji_input.strip()
    if stripped.startswith("http"):
        emoji_val = stripped
    elif EMOJI_REGEX.match(stripped):
        emoji_val = stripped
    elif len(stripped) <= 5 and not stripped.startswith("<"):
        emoji_val = stripped  # unicode emoji
    else:
        err = await response_emoji.get(ctx.guild.id, "error")
        await ctx.send(f"{err} Geçersiz emoji formatı, boss man.")
        return

    await response_emoji.set(ctx.guild.id, anahtar, emoji_val)
    success = await response_emoji.get(ctx.guild.id, "success")
    await ctx.send(f"{success} `{anahtar}` cevabı artık {emoji_val} olarak görünecek. (Kalıcı)")

@cevapemoji.command(name="sıfırla")
@check_half_owner()
async def cevapemoji_sifirla(ctx, anahtar: str = None):
    if anahtar:
        await response_emoji.remove(ctx.guild.id, anahtar)
        success = await response_emoji.get(ctx.guild.id, "success")
        await ctx.send(f"{success} `{anahtar}` varsayılana döndü.")
    else:
        for k in DEFAULT_RESPONSES:
            await response_emoji.remove(ctx.guild.id, k)
        success = await response_emoji.get(ctx.guild.id, "success")
        await ctx.send(f"{success} Tüm yanıt emojileri sıfırlandı.")

# ─────────────────────────────────────────────
#   HALF-OWNER SİSTEMİ
# ─────────────────────────────────────────────
@bot.group(name="halfowner", aliases=["ho"], invoke_without_command=True)
@commands.has_permissions(administrator=True)
async def halfowner(ctx):
    await ctx.send(
        "**Half-Owner Komutları:**\n"
        "`m!ho ekle @kisi` - Half-owner ekle\n"
        "`m!ho sil @kisi` - Half-owner kaldır\n"
        "`m!ho liste` - Liste\n"
        "`m!ho bilgi @kisi` - Kullanıcı bilgisi"
    )

@halfowner.command(name="ekle")
@commands.has_permissions(administrator=True)
async def ho_ekle(ctx, member: discord.Member):
    row = await db.fetchone("SELECT 1 FROM half_owners WHERE guild_id=? AND user_id=?",
                            ctx.guild.id, member.id)
    if row:
        warn = await response_emoji.get(ctx.guild.id, "warning")
        await ctx.send(f"{warn} {member.mention} zaten half-owner.")
        return
    await db.execute(
        "INSERT INTO half_owners (guild_id, user_id, added_by) VALUES (?, ?, ?)",
        ctx.guild.id, member.id, ctx.author.id
    )
    success = await response_emoji.get(ctx.guild.id, "success")
    await ctx.send(f"{success} {member.mention} artık half-owner. Bot komutlarını kullanabilir.")

@halfowner.command(name="sil")
@commands.has_permissions(administrator=True)
async def ho_sil(ctx, member: discord.Member):
    await db.execute("DELETE FROM half_owners WHERE guild_id=? AND user_id=?",
                     ctx.guild.id, member.id)
    success = await response_emoji.get(ctx.guild.id, "success")
    await ctx.send(f"{success} {member.mention} half-owner listesinden çıkarıldı.")

@halfowner.command(name="liste")
@check_half_owner()
async def ho_liste(ctx):
    rows = await db.fetchall(
        "SELECT user_id, added_by, added_at FROM half_owners WHERE guild_id=?",
        ctx.guild.id
    )
    if not rows:
        info = await response_emoji.get(ctx.guild.id, "info")
        await ctx.send(f"{info} Hiç half-owner yok.")
        return
    desc = "\n".join(
        f"<@{uid}> — <@{ab}> tarafından `{at[:10]}`"
        for uid, ab, at in rows
    )
    embed = discord.Embed(title="🛡️ Half-Owner Listesi", description=desc, color=0xFFAA00)
    await ctx.send(embed=embed)

@halfowner.command(name="bilgi")
@check_half_owner()
async def ho_bilgi(ctx, member: discord.Member):
    row = await db.fetchone(
        "SELECT added_by, added_at FROM half_owners WHERE guild_id=? AND user_id=?",
        ctx.guild.id, member.id
    )
    if not row:
        err = await response_emoji.get(ctx.guild.id, "error")
        await ctx.send(f"{err} {member.mention} half-owner değil.")
        return
    ab, at = row
    embed = discord.Embed(title=f"🛡️ {member.display_name}", color=0x00FFAA)
    embed.add_field(name="Ekleyen", value=f"<@{ab}>")
    embed.add_field(name="Eklendiği Tarih", value=at[:16])
    await ctx.send(embed=embed)

# ─────────────────────────────────────────────
#   REKLAM SİSTEMİ
# ─────────────────────────────────────────────
@bot.group(name="reklam", aliases=["ad"], invoke_without_command=True)
async def reklam(ctx):
    info = await response_emoji.get(ctx.guild.id, "ad")
    await ctx.send(
        f"{info} **Reklam Komutları:**\n"
        "`m!reklam ver <içerik>` - Reklam ver\n"
        "`m!reklam sil <id>` - Reklam sil (yazar/yetkili)\n"
        "`m!reklam liste` - Aktif reklamlar\n"
        "`m!reklam istatistik` - Sunucu istatistikleri\n"
        "`m!reklam kur #kanal <saniye>` - Otomatik paylaşım kanalı"
    )

@reklam.command(name="ver")
async def reklam_ver(ctx, *, icerik: str):
    # Ayar kontrol
    settings = await db.fetchone(
        "SELECT min_length, max_length, cooldown FROM ad_settings WHERE guild_id=?",
        ctx.guild.id
    )
    min_len, max_len, cooldown = (settings if settings else (20, 500, 300))

    if len(icerik) < min_len:
        err = await response_emoji.get(ctx.guild.id, "error")
        await ctx.send(f"{err} Reklam en az {min_len} karakter olmalı.")
        return
    if len(icerik) > max_len:
        err = await response_emoji.get(ctx.guild.id, "error")
        await ctx.send(f"{err} Reklam en fazla {max_len} karakter olabilir.")
        return

    # Cooldown
    row = await db.fetchone(
        "SELECT last_ad FROM ad_cooldowns WHERE guild_id=? AND user_id=?",
        ctx.guild.id, ctx.author.id
    )
    now = datetime.utcnow()
    if row:
        try:
            last = datetime.fromisoformat(row[0])
            diff = (now - last).total_seconds()
            if diff < cooldown:
                warn = await response_emoji.get(ctx.guild.id, "warning")
                await ctx.send(f"{warn} {int(cooldown - diff)} saniye beklemelisin.")
                return
        except Exception:
            pass

    await db.execute(
        "INSERT INTO ads (guild_id, author_id, content, channel_id) VALUES (?, ?, ?, ?)",
        ctx.guild.id, ctx.author.id, icerik, ctx.channel.id
    )
    await db.execute(
        "INSERT OR REPLACE INTO ad_cooldowns (guild_id, user_id, last_ad) VALUES (?, ?, ?)",
        ctx.guild.id, ctx.author.id, now.isoformat()
    )

    ad_em = await response_emoji.get(ctx.guild.id, "ad")
    embed = discord.Embed(
        title=f"{ad_em} Reklam Yayında!",
        description=icerik,
        color=0x00BFFF
    )
    embed.set_footer(text=f"Sponsor: {ctx.author.display_name}")
    success = await response_emoji.get(ctx.guild.id, "success")
    await ctx.send(f"{success} Reklamın onaylandı ve otomatik paylaşım havuzuna eklendi.", embed=embed)

    # Otomatik reklam kanalına hemen at
    ad_settings = await db.fetchone(
        "SELECT auto_post_channel FROM ad_settings WHERE guild_id=?",
        ctx.guild.id
    )
    if ad_settings and ad_settings[0]:
        ch = ctx.guild.get_channel(ad_settings[0])
        if ch and ch.id != ctx.channel.id:
            try:
                await ch.send(embed=embed)
            except Exception:
                pass

@reklam.command(name="sil")
async def reklam_sil(ctx, ad_id: int):
    row = await db.fetchone("SELECT author_id FROM ads WHERE id=? AND guild_id=?",
                            ad_id, ctx.guild.id)
    if not row:
        err = await response_emoji.get(ctx.guild.id, "error")
        await ctx.send(f"{err} Reklam bulunamadı.")
        return
    if row[0] != ctx.author.id and not await is_authorized(ctx):
        err = await response_emoji.get(ctx.guild.id, "error")
        await ctx.send(f"{err} Bu reklamı silme yetkin yok.")
        return
    await db.execute("DELETE FROM ads WHERE id=?", ad_id)
    success = await response_emoji.get(ctx.guild.id, "success")
    await ctx.send(f"{success} Reklam silindi.")

@reklam.command(name="liste")
async def reklam_liste(ctx):
    rows = await db.fetchall("""
        SELECT id, author_id, content, views FROM ads
        WHERE guild_id=? AND active=1 ORDER BY id DESC LIMIT 10
    """, ctx.guild.id)
    if not rows:
        info = await response_emoji.get(ctx.guild.id, "info")
        await ctx.send(f"{info} Aktif reklam yok.")
        return
    desc = "\n\n".join(
        f"`#{aid}` <@{uid}> — {c[:60]}... `{v} görüntülenme`"
        for aid, uid, c, v in rows
    )
    embed = discord.Embed(title="📢 Aktif Reklamlar", description=desc, color=0x00BFFF)
    await ctx.send(embed=embed)

@reklam.command(name="istatistik")
async def reklam_istat(ctx):
    total = (await db.fetchone("SELECT COUNT(*) FROM ads WHERE guild_id=? AND active=1",
                               ctx.guild.id))[0]
    views = (await db.fetchone("SELECT COALESCE(SUM(views),0) FROM ads WHERE guild_id=?",
                               ctx.guild.id))[0]
    authors = (await db.fetchone("SELECT COUNT(DISTINCT author_id) FROM ads WHERE guild_id=?",
                                 ctx.guild.id))[0]
    embed = discord.Embed(title="📊 Reklam İstatistikleri", color=0x00FFAA)
    embed.add_field(name="Aktif Reklam", value=total)
    embed.add_field(name="Toplam Görüntülenme", value=views)
    embed.add_field(name="Reklamveren", value=authors)
    await ctx.send(embed=embed)

@reklam.command(name="kur")
@check_half_owner()
async def reklam_kur(ctx, channel: discord.TextChannel, interval: int = 3600):
    await db.execute("""
        INSERT OR REPLACE INTO ad_settings
        (guild_id, auto_post_channel, auto_post_interval)
        VALUES (?, ?, ?)
    """, ctx.guild.id, channel.id, interval)
    success = await response_emoji.get(ctx.guild.id, "success")
    await ctx.send(f"{success} Otomatik reklam kanalı {channel.mention} — her {interval} saniye bir reklam atılacak.")

# ─────────────────────────────────────────────
#   GENEL / YARDIM
# ─────────────────────────────────────────────
@bot.command(name="yardım", aliases=["help", "y"])
async def yardim(ctx):
    em = await response_emoji.all(ctx.guild.id)
    embed = discord.Embed(title="Marpel Clone - Komut Listesi", color=0x5865F2)
    embed.add_field(name="⚙️ Kurulum", value="`m!kur`, `m!cevapemoji`, `m!ho`, `m!reklam kur`", inline=False)
    embed.add_field(name="🛡️ Half-Owner", value="`m!ho ekle/sil/liste/bilgi`", inline=False)
    embed.add_field(name="📢 Reklam", value="`m!reklam ver/sil/liste/istatistik/kur`", inline=False)
    embed.add_field(name="🎨 Emoji Cevapları", value="`m!cevapemoji ayarla <key> <emoji>`", inline=False)
    embed.add_field(name="😀 Nitro Emoji", value="`m!emoji ekle/sil/liste`", inline=False)
    embed.add_field(name="🏆 Rank", value="`m!rank`, `m!top`", inline=False)
    embed.add_field(name="🎉 Çekiliş", value="`m!çekiliş başlat <süre> <kazanan> <ödül>`", inline=False)
    embed.add_field(name="🎫 Destek", value="`m!destekac`, `m!destekkapat`", inline=False)
    embed.add_field(name="📌 Not / 🎂 Doğum Günü / 🎭 Rol", value="`m!not`, `m!doğumgünü`, `m!tepkirol`, `m!butonrol`", inline=False)
    embed.add_field(name=f"{em['success']} Emoji Anahtarları", value=", ".join(f"`{k}`" for k in em.keys()), inline=False)
    await ctx.send(embed=embed)

# ─────────────────────────────────────────────
#   EMOJI (NITRO) SİSTEMİ - kısaltılmış
# ─────────────────────────────────────────────
@bot.group(name="emoji", invoke_without_command=True)
async def emoji(ctx):
    await ctx.send("`m!emoji ekle <isim> <emoji>` / `m!emoji sil <isim>` / `m!emoji liste`")

@emoji.command(name="ekle")
@check_half_owner()
async def emoji_ekle(ctx, isim: str, *, emoji_input: str):
    if emoji_input.startswith("http"):
        url = emoji_input.strip()
    else:
        m = EMOJI_REGEX.match(emoji_input.strip())
        if not m:
            err = await response_emoji.get(ctx.guild.id, "error")
            await ctx.send(f"{err} Geçersiz emoji.")
            return
        animated = emoji_input.startswith("<a:")
        _, eid = m.group(1), m.group(2)
        url = f"https://cdn.discordapp.com/emojis/{eid}.{'gif' if animated else 'png'}?size=64"
    await db.execute("INSERT OR REPLACE INTO nitro_emojis (guild_id, name, url) VALUES (?, ?, ?)",
                     ctx.guild.id, isim, url)
    success = await response_emoji.get(ctx.guild.id, "success")
    await ctx.send(f"{success} `{isim}` eklendi.")

@emoji.command(name="sil")
@check_half_owner()
async def emoji_sil(ctx, isim: str):
    await db.execute("DELETE FROM nitro_emojis WHERE guild_id=? AND name=?", ctx.guild.id, isim)
    success = await response_emoji.get(ctx.guild.id, "success")
    await ctx.send(f"{success} `{isim}` silindi.")

@emoji.command(name="liste")
async def emoji_liste(ctx):
    rows = await db.fetchall("SELECT name FROM nitro_emojis WHERE guild_id=?", ctx.guild.id)
    if not rows:
        info = await response_emoji.get(ctx.guild.id, "info")
        await ctx.send(f"{info} Hiç emoji yok.")
        return
    await ctx.send("**Nitro Emojiler:** " + ", ".join(f"`{r[0]}`" for r in rows))

# ─────────────────────────────────────────────
#   RANK (kısa)
# ─────────────────────────────────────────────
@bot.event
async def on_message(message):
    if message.author.bot or not message.guild:
        return

    # Nitro emoji kısaltma
    if message.content.startswith(config["prefix"]):
        parts = message.content[len(config["prefix"]):].strip().split(maxsplit=1)
        if parts:
            name = parts[0]
            row = await db.fetchone(
                "SELECT url FROM nitro_emojis WHERE guild_id=? AND name=?",
                message.guild.id, name
            )
            if row:
                try:
                    await message.delete()
                except Exception:
                    pass
                await message.channel.send(row[0])
                return

    await bot.process_commands(message)

    # XP
    row = await db.fetchone(
        "SELECT xp, level, messages FROM ranks WHERE guild_id=? AND user_id=?",
        message.guild.id, message.author.id
    )
    if row:
        xp, level, msgs = row
        xp += random.randint(5, 15); msgs += 1
        new_level = int((xp / 100) ** 0.5)
        if new_level > level:
            level = new_level
            rk = await response_emoji.get(message.guild.id, "rank")
            await message.channel.send(f"{rk} {message.author.mention} seviye atladı! **{level}**")
        await db.execute(
            "UPDATE ranks SET xp=?, level=?, messages=? WHERE guild_id=? AND user_id=?",
            xp, level, msgs, message.guild.id, message.author.id
        )
    else:
        await db.execute(
            "INSERT INTO ranks (guild_id, user_id, xp, level, messages) VALUES (?, ?, ?, ?, ?)",
            message.guild.id, message.author.id, 10, 0, 1
        )

@bot.command(name="rank")
async def rank(ctx, member: discord.Member = None):
    member = member or ctx.author
    row = await db.fetchone(
        "SELECT xp, level, messages FROM ranks WHERE guild_id=? AND user_id=?",
        ctx.guild.id, member.id
    )
    if not row:
        info = await response_emoji.get(ctx.guild.id, "info")
        await ctx.send(f"{info} {member.mention} henüz rank verisi yok.")
        return
    xp, level, msgs = row
    rk = await response_emoji.get(ctx.guild.id, "rank")
    embed = discord.Embed(title=f"{rk} {member.display_name} - Rank", color=0x00FFAA)
    embed.add_field(name="Seviye", value=level)
    embed.add_field(name="XP", value=xp)
    embed.add_field(name="Mesaj", value=msgs)
    await ctx.send(embed=embed)

# ─────────────────────────────────────────────
#   ÇALIŞTIR
# ─────────────────────────────────────────────
if __name__ == "__main__":
    bot.run(config["token"])
