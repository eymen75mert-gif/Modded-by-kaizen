
# KATRE — tek dosyalı, public Discord botu
# Python 3.10+ / discord.py 2.7.x
#
# Railway Variables:
#   BOT_TOKEN  -> zorunlu
#   OWNER_ID   -> zorunlu (virgülle birden fazla ID yazılabilir)
#   SUPPORT_URL -> opsiyonel
#
# Veri dosyası:
#   Railway Volume /data bağlıysa otomatik /data/katre.json kullanılır.
#
# Discord Developer Portal:
#   MESSAGE CONTENT INTENT + SERVER MEMBERS INTENT + PRESENCE INTENT açılması önerilir.
#
# Kurulum:
#   pip install -U discord.py==2.7.1
#   python main.py
#
# Not: Katre özgün bir bottur; başka bir botun kaynak kodunu veya markasını kopyalamaz.

import os
import sys
import json
import time
import math
import random
import asyncio
import inspect
import shlex
import typing
import logging
import secrets
import subprocess
from datetime import datetime, timezone, timedelta
from pathlib import Path
from collections import defaultdict, deque
from typing import Optional

# Tek dosya rahatlığı: dependency yoksa otomatik kurmayı dener.
try:
    import discord
    from discord import app_commands
    from discord.ext import commands, tasks
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-U", "discord.py==2.7.1"])
    import discord
    from discord import app_commands
    from discord.ext import commands, tasks

try:
    from aiohttp import web
except Exception:
    web = None

# ----------------------------- AYARLAR -----------------------------

TOKEN = os.getenv("BOT_TOKEN", "").strip()
OWNER_IDS = {
    int(x.strip()) for x in os.getenv("OWNER_ID", "").split(",")
    if x.strip().isdigit()
}
SUPPORT_URL = os.getenv("SUPPORT_URL", "").strip()

if not TOKEN:
    raise RuntimeError("BOT_TOKEN Railway Variable eksik.")
if not OWNER_IDS:
    raise RuntimeError("OWNER_ID Railway Variable eksik.")

APP_NAME = "Katre"
VERSION = "5.0.0"
PREFIX = "k!"
KATRE_AVATAR_PATH = os.path.join(os.path.dirname(__file__), "assets", "katre_pp.png")
START = time.time()

DATA_PATH = Path("/data/katre.json") if Path("/data").exists() else Path("katre.json")
DATA_PATH.parent.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | KATRE | %(levelname)s | %(message)s"
)
log = logging.getLogger("katre")

# ----------------------------- JSON DB -----------------------------

DEFAULT_GUILD = {
    "prefix": "k!",
    "log_channel": None,
    "modlog_channel": None,
    "welcome_channel": None,
    "welcome_text": "Hoş geldin {member}! 🎉 {server} sunucusuna katıldın.",
    "leave_channel": None,
    "leave_text": "{member} sunucudan ayrıldı.",
    "autorole": None,
    "rules_channel": None,
    "ticket_category": None,
    "ticket_staff_role": None,
    "suggest_channel": None,
    "starboard_channel": None,
    "starboard_threshold": 3,
    "level_channel": None,
    "level_enabled": True,
    "xp_cooldown": 60,
    "automod_enabled": False,
    "automod_links": False,
    "automod_invites": True,
    "automod_caps": False,
    "automod_spam": True,
    "automod_badwords": [],
    "badword_action": "delete",
    "anti_raid": False,
    "anti_raid_limit": 8,
    "anti_raid_window": 10,
    "advertising": {
        "enabled": False,
        "guild_id": None,
        "invite": None,
        "channel": None,
        "message": "Bu komutu kullanmak için reklam sunucusuna katılmalısın."
    },
    "command_ads": {},
    "custom_commands": {},
    "tags": {},
    "reaction_roles": {},
    "temp_roles": {},
    "giveaways": {},
    "tickets": {},
    "suggestions": {},
    "polls": {},
    "auto_messages": {},
    "roles_on_level": {},
    "economy_enabled": True,
}

DEFAULT_USER = {
    "xp": 0,
    "level": 0,
    "coins": 0,
    "afk": None,
    "warnings": [],
    "notes": [],
    "rep": 0,
    "daily": 0,
    "work": 0,
    "inventory": [],
    "pro_until": 0,
}

EMOJI_DEFAULTS = {
    "ok": "✅",
    "no": "❌",
    "info": "ℹ️",
    "warn": "⚠️",
    "owner": "👑",
    "pro": "💎",
    "bot": "🤖",
    "settings": "⚙️",
    "moderation": "🛡️",
    "security": "🔐",
    "ticket": "🎫",
    "giveaway": "🎉",
    "economy": "🪙",
    "level": "✨",
    "user": "👤",
    "server": "🏠",
    "log": "📋",
    "gift": "🎁",
    "link": "🔗",
    "bell": "🔔",
    "lock": "🔒",
    "unlock": "🔓",
    "star": "⭐",
    "heart": "❤️",
    "search": "🔎",
    "home": "🏠",
    "back": "◀️",
    "next": "▶️",
    "close": "✖️",
}

DB = {"guilds": {}, "users": {}, "global": {
    "pro_users": {},
    "blacklist": [],
    "maintenance": False,
    "emojis": dict(EMOJI_DEFAULTS),
}}

DB_LOCK = asyncio.Lock()

def load_db():
    global DB
    if not DATA_PATH.exists():
        save_db()
        return
    try:
        DB = json.loads(DATA_PATH.read_text("utf-8"))
        DB.setdefault("guilds", {})
        DB.setdefault("users", {})
        DB.setdefault("global", {"pro_users": {}, "blacklist": [], "maintenance": False})
    except Exception as e:
        log.exception("DB okunamadı: %s", e)

def save_db():
    tmp = DATA_PATH.with_suffix(".tmp")
    tmp.write_text(json.dumps(DB, ensure_ascii=False, indent=2), "utf-8")
    tmp.replace(DATA_PATH)

async def persist():
    async with DB_LOCK:
        save_db()

def guild_data(gid: int):
    key = str(gid)
    if key not in DB["guilds"]:
        DB["guilds"][key] = json.loads(json.dumps(DEFAULT_GUILD))
    else:
        # Sonradan eklenen ayarları mevcut sunuculara ekle.
        for k, v in DEFAULT_GUILD.items():
            if k not in DB["guilds"][key]:
                DB["guilds"][key][k] = json.loads(json.dumps(v))
    return DB["guilds"][key]

def user_data(uid: int, gid: int):
    g = str(gid)
    u = str(uid)
    DB["users"].setdefault(g, {})
    if u not in DB["users"][g]:
        DB["users"][g][u] = json.loads(json.dumps(DEFAULT_USER))
    else:
        for k, v in DEFAULT_USER.items():
            DB["users"][g][u].setdefault(k, json.loads(json.dumps(v)))
    return DB["users"][g][u]

DB["global"].setdefault("emojis", {})
for _ek, _ev in EMOJI_DEFAULTS.items():
    DB["global"]["emojis"].setdefault(_ek, _ev)

def E(key):
    return DB["global"].get("emojis", {}).get(key, EMOJI_DEFAULTS.get(key, ""))

# ----------------------------- HELPERS -----------------------------

def now_ts():
    return int(time.time())

def fmt_seconds(s: int):
    s = max(0, int(s))
    d, s = divmod(s, 86400)
    h, s = divmod(s, 3600)
    m, s = divmod(s, 60)
    parts = []
    if d: parts.append(f"{d}g")
    if h: parts.append(f"{h}s")
    if m: parts.append(f"{m}dk")
    if s or not parts: parts.append(f"{s}sn")
    return " ".join(parts)

def embed(title, description="", color=discord.Color.blurple()):
    e = discord.Embed(title=f"✦ {title}", description=description, color=color, timestamp=datetime.now(timezone.utc))
    # Katre'nin güncel Discord avatarını tüm standart embedlerde marka olarak kullan.
    try:
        if globals().get("bot") and bot.user:
            avatar_url = bot.user.display_avatar.url
            e.set_author(name="Katre", icon_url=avatar_url)
            e.set_thumbnail(url=avatar_url)
            e.set_footer(text="Katre • Modern Discord deneyimi", icon_url=avatar_url)
        else:
            e.set_footer(text="Katre • Modern Discord deneyimi")
    except Exception:
        e.set_footer(text="Katre • Modern Discord deneyimi")
    return e

def ok(text): return f"{E('ok')} {text}"
def no(text): return f"{E('no')} {text}"

def is_owner(user):
    return user.id in OWNER_IDS

def is_pro(uid: int):
    rec = DB["global"]["pro_users"].get(str(uid))
    if not rec:
        return False
    until = int(rec.get("until", 0))
    if until == 0:
        return True
    if until <= now_ts():
        DB["global"]["pro_users"].pop(str(uid), None)
        return False
    return True

def pro_left(uid: int):
    rec = DB["global"]["pro_users"].get(str(uid))
    if not rec: return 0
    until = int(rec.get("until", 0))
    return 0 if until == 0 else max(0, until - now_ts())

def command_ad(gid, command_name):
    cfg = guild_data(gid)
    if is_pro(gid):  # no-op; kept for clarity
        pass
    return cfg["command_ads"].get(command_name, cfg["advertising"])

def ad_config(gid):
    return guild_data(gid)["advertising"]

async def has_ad_access(interaction: discord.Interaction, command_name: str):
    if is_owner(interaction.user) or is_pro(interaction.user.id):
        return True
    cfg = guild_data(interaction.guild.id)
    specific = cfg["command_ads"].get(command_name)
    if specific is None:
        specific = cfg["advertising"]
    if not specific.get("enabled"):
        return True
    guild_id = specific.get("guild_id")
    if not guild_id:
        return True
    try:
        member = interaction.guild.get_member(interaction.user.id)
        if member is None:
            member = await interaction.guild.fetch_member(interaction.user.id)
        if member and int(guild_id) in [g.id for g in member.mutual_guilds]:
            return True
    except Exception:
        pass
    invite = specific.get("invite") or "Reklam sunucusunun davet linki ayarlanmamış."
    await interaction.response.send_message(
        embed("Sunucu Katılımı Gerekli",
              f"{specific.get('message', 'Bu komutu kullanmak için reklam sunucusuna katılmalısın.')}\n\n"
              f"🔗 {invite}\n\n**Pro üyeler bu şarttan muaftır.**",
              discord.Color.orange()),
        ephemeral=True
    )
    return False

def human_duration(text: str) -> int:
    text = text.lower().replace(" ", "")
    if text.isdigit():
        return int(text)
    units = {"s": 1, "sn": 1, "m": 60, "dk": 60, "h": 3600, "sa": 3600, "d": 86400, "g": 86400, "w": 604800}
    for u, mul in sorted(units.items(), key=lambda x: -len(x[0])):
        if text.endswith(u):
            try: return int(float(text[:-len(u)]) * mul)
            except: return 0
    return 0

def level_for_xp(xp):
    return int(math.sqrt(max(0, xp) / 100))

def xp_needed(level):
    return ((level + 1) ** 2) * 100

async def send_log(guild, title, description, color=discord.Color.blurple(), mod=False):
    cfg = guild_data(guild.id)
    cid = cfg["modlog_channel"] if mod else cfg["log_channel"]
    if not cid:
        cid = cfg["log_channel"] or cfg["modlog_channel"]
    if not cid: return
    ch = guild.get_channel(int(cid))
    if ch:
        try:
            await ch.send(embed=embed(title, description, color))
        except: pass

async def safe_dm(member, message):
    try:
        await member.send(message)
    except: pass

def role_targetable(guild, role, actor):
    return role != guild.default_role and role < guild.me.top_role and role < actor.top_role

# ----------------------------- BOT -----------------------------

intents = discord.Intents.all()

COMMAND_HELP_META = {}

class Katre(commands.Bot):
    async def setup_hook(self):
        # Discord global slash komut limiti nedeniyle yalnızca /yardim yayınlanır.
        # Diğer tüm komutlar aynı callback üzerinden k! ile çalışmaya devam eder.
        existing_commands = list(self.tree.get_commands())
        for cmd in existing_commands:
            if isinstance(cmd, app_commands.Command):
                params = []
                for p in cmd.parameters:
                    token = f"<{p.name}>" if p.required else f"[{p.name}]"
                    params.append(token)
                COMMAND_HELP_META[cmd.name] = (cmd.description or "Katre komutu.", params)
                if cmd.name != "yardim":
                    PREFIX_ONLY_COMMANDS.setdefault(cmd.name, cmd.callback)

        yardim_command = self.tree.get_command("yardim")
        self.tree.clear_commands(guild=None)
        if yardim_command is not None:
            self.tree.add_command(yardim_command)
        await self.tree.sync()
        self.reminder_loop.start()
        self.temporary_role_loop.start()
        self.giveaway_loop.start()
        self.auto_message_loop.start()
        self.cleanup_loop.start()

    async def on_ready(self):
        log.info("Katre hazır: %s | %s guild", self.user, len(self.guilds))
        # İlk kurulumda pakete eklenen Katre PP'sini otomatik olarak bot avatarı yap.
        # Avatar zaten özelleştirilmişse tekrar yükleyip rate-limit'e girmeyiz.
        if not getattr(self, "_katre_avatar_checked", False):
            self._katre_avatar_checked = True
            try:
                if self.user and self.user.avatar is None and os.path.isfile(KATRE_AVATAR_PATH):
                    with open(KATRE_AVATAR_PATH, "rb") as fp:
                        await self.user.edit(avatar=fp.read(), reason="Katre varsayılan profil görseli")
                    log.info("Katre profil görseli otomatik uygulandı.")
            except Exception as exc:
                log.warning("Katre PP otomatik uygulanamadı: %s", exc)
        await self.change_presence(
            activity=discord.Activity(type=discord.ActivityType.watching, name=f"k!yardim • {len(self.guilds)} sunucu")
        )

    @tasks.loop(seconds=30)
    async def reminder_loop(self):
        due = DB.get("reminders", [])
        if not due: return
        remaining = []
        for r in due:
            if r["at"] > now_ts():
                remaining.append(r); continue
            ch = self.get_channel(r["channel"])
            if ch:
                try: await ch.send(f"⏰ <@{r['user']}> **Hatırlatıcı:** {r['text']}")
                except: pass
        DB["reminders"] = remaining
        await persist()

    @tasks.loop(seconds=30)
    async def temporary_role_loop(self):
        changed = False
        for gid, cfg in list(DB["guilds"].items()):
            for uid, roles in list(cfg.get("temp_roles", {}).items()):
                member = self.get_guild(int(gid))
                if not member: continue
                user = member.get_member(int(uid))
                if not user: continue
                for rid, until in list(roles.items()):
                    if int(until) <= now_ts():
                        role = member.get_role(int(rid))
                        if role:
                            try: await user.remove_roles(role, reason="Katre süreli rol süresi doldu")
                            except: pass
                        del roles[rid]
                        changed = True
        if changed: await persist()

    @tasks.loop(seconds=20)
    async def giveaway_loop(self):
        changed = False
        for gid, cfg in list(DB["guilds"].items()):
            for wid, g in list(cfg.get("giveaways", {}).items()):
                if g.get("ended"): continue
                if int(g["end"]) <= now_ts():
                    ch = self.get_channel(int(g["channel"]))
                    if ch:
                        try:
                            msg = await ch.fetch_message(int(g["message"]))
                            users = [u async for u in msg.reactions[0].users()] if msg.reactions else []
                            users = [u for u in users if not u.bot]
                            if users:
                                # Normal kullanıcı = 1x, Pro/owner = 2x ağırlık.
                                # Aynı kullanıcı aynı çekilişte birden fazla kez kazanamaz.
                                weighted_pool = []
                                for user in users:
                                    weight = 2 if (is_owner(user) or is_pro(user.id)) else 1
                                    weighted_pool.extend([user] * weight)

                                selected = []
                                available = list(weighted_pool)
                                winner_count = min(int(g["winners"]), len(users))

                                while available and len(selected) < winner_count:
                                    winner = random.choice(available)
                                    selected.append(winner)
                                    available = [u for u in available if u.id != winner.id]

                                names = ", ".join(u.mention for u in selected)
                                await ch.send(
                                    embed=embed(
                                        "Çekiliş Bitti! 🎉",
                                        f"**Ödül:** {g['prize']}\n**Kazanan:** {names}\n\n"
                                        "💎 Pro / 👑 Katre sahibi kullanıcıların kazanma ağırlığı **2x**.",
                                        discord.Color.green()
                                    )
                                )
                            else:
                                await ch.send(embed=embed("Çekiliş Bitti", "Yeterli katılım olmadı.", discord.Color.orange()))
                        except Exception as e:
                            log.warning("Giveaway: %s", e)
                    g["ended"] = True
                    changed = True
        if changed: await persist()

    @tasks.loop(seconds=60)
    async def auto_message_loop(self):
        for gid, cfg in list(DB["guilds"].items()):
            for aid, a in list(cfg.get("auto_messages", {}).items()):
                if int(a.get("next", 0)) <= now_ts():
                    ch = self.get_channel(int(a["channel"]))
                    if ch:
                        try: await ch.send(a["text"])
                        except: pass
                    a["next"] = now_ts() + int(a["interval"])
        await persist()

    @tasks.loop(minutes=5)
    async def cleanup_loop(self):
        changed = False
        # süresi dolmuş Pro kayıtlarını temizle
        for uid, rec in list(DB["global"]["pro_users"].items()):
            if rec.get("until", 0) and int(rec["until"]) <= now_ts():
                del DB["global"]["pro_users"][uid]; changed = True
        if changed: await persist()

bot = Katre(command_prefix=lambda b, m: guild_data(m.guild.id)["prefix"] if m.guild else PREFIX,
            intents=intents, help_command=None)

# ----------------------------- GLOBAL CHECKS -----------------------------

@bot.check
async def global_check(ctx):
    if not ctx.guild:
        return True
    if ctx.author.id in DB["global"].get("blacklist", []):
        return False
    return True

# ----------------------------- EVENTS -----------------------------

@bot.event
async def on_guild_join(guild):
    guild_data(guild.id)
    await persist()
    try:
        ch = next((c for c in guild.text_channels if c.permissions_for(guild.me).send_messages), None)
        if ch:
            await ch.send(embed=embed("Katre burada! ✦", "Kurulum için `/ayarlar` ve komut listesi için `/yardim` kullanabilirsin."))
    except: pass

@bot.event
async def on_guild_remove(guild):
    # Veriyi silme; bot tekrar eklenirse ayarlar korunur.
    await persist()

@bot.event
async def on_member_join(member):
    cfg = guild_data(member.guild.id)
    if cfg.get("autorole"):
        role = member.guild.get_role(int(cfg["autorole"]))
        if role:
            try: await member.add_roles(role, reason="Katre otomatik rol")
            except: pass
    if cfg.get("welcome_channel"):
        ch = member.guild.get_channel(int(cfg["welcome_channel"]))
        if ch:
            text = cfg.get("welcome_text", "").replace("{member}", member.mention).replace("{user}", member.name).replace("{server}", member.guild.name)
            try: await ch.send(embed=embed("Yeni üye! 👋", text, discord.Color.green()))
            except: pass
    await send_log(member.guild, "Üye Katıldı", f"{member.mention} sunucuya katıldı.")

@bot.event
async def on_member_remove(member):
    cfg = guild_data(member.guild.id)
    if cfg.get("leave_channel"):
        ch = member.guild.get_channel(int(cfg["leave_channel"]))
        if ch:
            text = cfg.get("leave_text", "").replace("{member}", member.name).replace("{user}", member.name).replace("{server}", member.guild.name)
            try: await ch.send(embed=embed("Üye Ayrıldı", text, discord.Color.orange()))
            except: pass
    await send_log(member.guild, "Üye Ayrıldı", f"**{member}** sunucudan ayrıldı.", discord.Color.orange())

# ─────────────────────────────────────────────────────────────────────────────
# PREFIX BRIDGE
# Every top-level slash command also has a k! equivalent.
# Example: /ban @User spam  ->  k!ban @User spam
# This bridge calls the same command logic instead of maintaining duplicate code.
# ─────────────────────────────────────────────────────────────────────────────

class _PrefixResponse:
    def __init__(self, ctx):
        self.ctx = ctx

    async def send_message(self, content=None, **kwargs):
        # Prefix komutları da slash komutlarıyla aynı modern arayüzü kullanır.
        if content is not None and not kwargs.get("embed") and not kwargs.get("embeds"):
            kwargs["embed"] = embed("Katre", str(content), discord.Color.blurple())
            content = None
        if kwargs.get("view") is None:
            kwargs["view"] = KatreActionView(getattr(self.ctx.author, "id", None))
        return await self.ctx.send(content=content, **kwargs)

    async def defer(self, **kwargs):
        return await self.ctx.typing()


class _PrefixFollowup:
    def __init__(self, ctx):
        self.ctx = ctx

    async def send(self, content=None, **kwargs):
        if content is not None and not kwargs.get("embed") and not kwargs.get("embeds"):
            kwargs["embed"] = embed("Katre", str(content), discord.Color.blurple())
            content = None
        if kwargs.get("view") is None:
            kwargs["view"] = KatreActionView(getattr(self.ctx.author, "id", None))
        return await self.ctx.send(content=content, **kwargs)


class _PrefixInteraction:
    def __init__(self, ctx):
        self.user = ctx.author
        self.guild = ctx.guild
        self.channel = ctx.channel
        self.response = _PrefixResponse(ctx)
        self.followup = _PrefixFollowup(ctx)


def _prefix_clean(value: str) -> str:
    return value.strip().strip("<>@!#&")


async def _prefix_resolve_member(ctx, value):
    if not ctx.guild:
        return None
    value = _prefix_clean(value)
    if value.isdigit():
        return ctx.guild.get_member(int(value))
    for m in ctx.guild.members:
        if m.name.lower() == value.lower() or m.display_name.lower() == value.lower():
            return m
    return None


async def _prefix_resolve_user(ctx, value):
    member = await _prefix_resolve_member(ctx, value)
    if member:
        return member
    value = _prefix_clean(value)
    if value.isdigit():
        try:
            return await bot.fetch_user(int(value))
        except Exception:
            return None
    return None


async def _prefix_resolve_role(ctx, value):
    if not ctx.guild:
        return None
    value = _prefix_clean(value)
    if value.isdigit():
        return ctx.guild.get_role(int(value))
    for role in ctx.guild.roles:
        if role.name.lower() == value.lower():
            return role
    return None


async def _prefix_resolve_channel(ctx, value):
    if not ctx.guild:
        return None
    value = _prefix_clean(value)
    if value.isdigit():
        return ctx.guild.get_channel(int(value))
    for ch in ctx.guild.channels:
        if ch.name.lower() == value.lower():
            return ch
    return None


def _prefix_annotation(annotation):
    if annotation is inspect.Parameter.empty:
        return str, False
    origin = typing.get_origin(annotation)
    if origin in (typing.Union, getattr(typing, "UnionType", object())):
        args = [x for x in typing.get_args(annotation) if x is not type(None)]
        return (args[0] if args else str), True
    return annotation, False


async def _prefix_convert(ctx, raw, annotation):
    annotation, _ = _prefix_annotation(annotation)
    if annotation is str or annotation is inspect.Parameter.empty:
        return raw
    if annotation is int:
        return int(raw)
    if annotation is float:
        return float(raw)
    if annotation is bool:
        low = raw.lower()
        if low in ("1", "true", "on", "evet", "aç", "ac", "yes"):
            return True
        if low in ("0", "false", "off", "hayır", "hayir", "kapat", "no"):
            return False
        raise ValueError("boolean")
    if annotation is discord.Member:
        return await _prefix_resolve_member(ctx, raw)
    if annotation is discord.User:
        return await _prefix_resolve_user(ctx, raw)
    if annotation is discord.Role:
        return await _prefix_resolve_role(ctx, raw)
    if annotation in (discord.TextChannel, discord.VoiceChannel, discord.StageChannel, discord.CategoryChannel):
        return await _prefix_resolve_channel(ctx, raw)
    return raw


async def _dispatch_prefix_slash(ctx, command_name, raw_args):
    # Native prefix commands keep priority where they already exist.
    native = bot.get_command(command_name)
    if native is not None:
        return False

    command = bot.tree.get_command(command_name)
    if command is not None and isinstance(command, app_commands.Command):
        callback = command.callback
    else:
        # Slash'a çıkarılmayan komutlar k! ile çalışmaya devam eder.
        callback = PREFIX_ONLY_COMMANDS.get(command_name)
        if callback is None:
            return False
    sig = inspect.signature(callback)
    params = list(sig.parameters.values())[1:]  # skip interaction
    tokens = list(raw_args)
    values = []

    try:
        for index, param in enumerate(params):
            ann, optional = _prefix_annotation(param.annotation)
            is_last = index == len(params) - 1

            if is_last and ann is str and tokens:
                raw = " ".join(tokens)
                tokens.clear()
            elif tokens:
                raw = tokens.pop(0)
            else:
                if param.default is not inspect.Parameter.empty:
                    values.append(param.default)
                    continue
                if optional:
                    values.append(None)
                    continue
                await ctx.send(f"❌ Eksik kullanım. `/{" + command_name + "}` komutunun gerekli parametrelerini gir.")
                return True

            converted = await _prefix_convert(ctx, raw, param.annotation)

            # Discord's slash converters return objects; if resolution fails,
            # show a useful error rather than calling the callback with None.
            if ann in (discord.Member, discord.User, discord.Role,
                       discord.TextChannel, discord.VoiceChannel,
                       discord.StageChannel, discord.CategoryChannel) and converted is None:
                await ctx.send(f"❌ `{raw}` bulunamadı.")
                return True

            values.append(converted)

        if tokens:
            await ctx.send(f"❌ Fazla parametre girdin. Kullanım: `k!{command_name}`")
            return True

        # Slash komutlarındaki yetki kontrolleri k! tarafında da uygulanır.
        required_permissions = PREFIX_PERMISSION_REQUIREMENTS.get(command_name, ())
        if required_permissions:
            if ctx.guild is None:
                return True
            permissions = ctx.author.guild_permissions
            if not all(getattr(permissions, permission, False) for permission in required_permissions):
                if command_name == "cekilis":
                    return True  # Yetkisiz k!cekilis tamamen sessiz.
                await ctx.send("❌ Bu komut için gerekli Discord yetkisine sahip değilsin.")
                return True

        interaction = _PrefixInteraction(ctx)
        await callback(interaction, *values)
        return True

    except (ValueError, TypeError):
        await ctx.send(f"❌ Parametre biçimi hatalı. Kullanım: `k!{command_name}`")
        return True
    except discord.Forbidden:
        await ctx.send("❌ Bu işlem için Discord yetkisi yeterli değil.")
        return True
    except Exception:
        # Do not leak internals to public channels.
        await ctx.send("❌ Komut çalıştırılırken bir hata oluştu.")
        return True


@bot.event
async def on_message(message):
    if message.author.bot or not message.guild:
        return

    cfg = guild_data(message.guild.id)
    ud = user_data(message.author.id, message.guild.id)

    # AFK
    if ud.get("afk"):
        ud["afk"] = None
        await message.channel.send(f"👋 {message.author.mention}, AFK durumun kaldırıldı.", delete_after=5)
        await persist()

    for m in message.mentions:
        if m.bot: continue
        mud = user_data(m.id, message.guild.id)
        if mud.get("afk"):
            await message.channel.send(f"💤 **{m.display_name}** şu anda AFK: {mud['afk']}", delete_after=8)

    # Custom commands
    key = message.content.lower().strip()
    if key in cfg["custom_commands"]:
        cc = cfg["custom_commands"][key]
        text = cc["text"].replace("{user}", message.author.mention).replace("{server}", message.guild.name)
        await message.channel.send(text)
        if cc.get("delete_trigger"):
            try: await message.delete()
            except: pass

    # Automod
    if cfg["automod_enabled"]:
        content = message.content.lower()
        violations = []
        if cfg.get("automod_invites") and ("discord.gg/" in content or "discord.com/invite/" in content):
            violations.append("Discord davet linki")
        if cfg.get("automod_links") and ("http://" in content or "https://" in content):
            violations.append("link")
        if cfg.get("automod_caps"):
            letters = [c for c in message.content if c.isalpha()]
            if len(letters) >= 10 and sum(c.isupper() for c in letters) / len(letters) >= .75:
                violations.append("aşırı büyük harf")
        if cfg.get("automod_spam"):
            recent = getattr(bot, "_spam", defaultdict(lambda: deque(maxlen=6)))
            setattr(bot, "_spam", recent)
            q = recent[(message.guild.id, message.author.id)]
            q.append(now_ts())
            if len(q) >= 5 and q[-1] - q[0] <= 5:
                violations.append("spam")
        if any(w.lower() in content for w in cfg.get("automod_badwords", [])):
            violations.append("yasaklı kelime")
        if violations and not message.author.guild_permissions.manage_messages:
            try: await message.delete()
            except: pass
            await send_log(message.guild, "AutoMod", f"{message.author.mention} mesajı kaldırıldı: {', '.join(violations)}", discord.Color.red(), True)

    # XP / economy
    if cfg.get("level_enabled") and random.random() < 0.55:
        cooldowns = getattr(bot, "_xp_cd", {})
        setattr(bot, "_xp_cd", cooldowns)
        keycd = (message.guild.id, message.author.id)
        if now_ts() - cooldowns.get(keycd, 0) >= int(cfg.get("xp_cooldown", 60)):
            cooldowns[keycd] = now_ts()
            gain = random.randint(12, 25) + (5 if is_pro(message.author.id) else 0)
            old = ud["xp"]
            ud["xp"] += gain
            oldlvl = level_for_xp(old)
            newlvl = level_for_xp(ud["xp"])
            if newlvl > oldlvl:
                ud["level"] = newlvl
                ch_id = cfg.get("level_channel")
                ch = message.guild.get_channel(int(ch_id)) if ch_id else message.channel
                if ch:
                    await ch.send(embed=embed("Seviye Atladın! ✨", f"{message.author.mention} **{newlvl}. seviyeye** ulaştı!", discord.Color.gold()))
                role_id = cfg.get("roles_on_level", {}).get(str(newlvl))
                if role_id:
                    role = message.guild.get_role(int(role_id))
                    if role:
                        try: await message.author.add_roles(role, reason="Katre level rolü")
                        except: pass
            if random.random() < .25:
                ud["coins"] += random.randint(1, 5)
            await persist()

    await bot.process_commands(message)

# ----------------------------- ERROR -----------------------------

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        return
    if isinstance(error, commands.MissingPermissions):
        await ctx.send(embed=embed("Yetki Yetersiz", "Bu işlem için gerekli yetkiye sahip değilsin.", discord.Color.red()), delete_after=8)
        return
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(embed=embed("Eksik Bilgi", "Komutun zorunlu bir parametresi eksik.", discord.Color.orange()), delete_after=8)
        return
    log.exception("Prefix command error", exc_info=error)

# ----------------------------- BASIC SLASH -----------------------------

# ----------------------------- ADVANCED HELP CENTER -----------------------------

HELP_CATEGORIES = {
    "temel": ("🏠 Temel & Katre", ["yardim", "ping", "davet", "bot", "sunucu", "kullanici", "avatar", "istatistik", "support", "shard"]),
    "profil": ("👤 Profil & Sosyal", ["afk", "rep", "profile", "rank", "leaderboard", "dogumgunu", "tag", "bugun"]),
    "ekonomi": ("💰 Ekonomi", ["bakiye", "gunluk", "calis", "transfer", "kredi", "magaza", "envanter"]),
    "seviye": ("⭐ Seviye & Görev", ["seviye", "gorev", "levelrol", "istatistik-kur", "gorevli", "gorevliler"]),
    "moderasyon": ("🛡️ Moderasyon", ["ban", "unban", "kick", "timeout", "untimeout", "sil", "kilit", "uyar", "uyarilar", "yavasmod", "yasaklilar", "yasaklari-temizle"]),
    "sunucu": ("⚙️ Sunucu Ayarları", ["prefix", "ayarlar", "log", "modlog", "hosgeldin", "otorol", "istatistik-kur", "logkur", "logkaldir", "reset"]),
    "roller": ("🎭 Rol & Kanal", ["rol-ver", "rol-al", "süreli-rol", "rol", "roller", "kanallar", "herkese-rolver", "herkesten-rolal", "isimdeğiştir", "isimleri-sifirla", "butonrol", "menurol"]),
    "koruma": ("🔒 Koruma & AutoMod", ["otomod", "otomod-link", "otomod-davet", "yasakli-kelime", "yasakli-kelimeler", "yasakli-kanal", "yasakli-komut", "capslock", "koruma"]),
    "topluluk": ("🎉 Topluluk", ["ticket-panel", "ticket-ayarla", "cekilis", "anket", "oneri", "oneri-kanal", "hatirlat", "davetlink", "davetler", "ozeloda", "oda-kapat"]),
    "eglence": ("🎮 Eğlence & Oyun", ["tkm", "yazitura", "zar", "slot", "terscevir", "pet", "ciftlik", "mayintarlasi", "adamasmaca", "kelimebulmaca", "xox", "sudoku"]),
    "araclar": ("🧰 Araçlar", ["hesap", "surecevir", "rastgele", "renk", "id", "metin", "qr", "say", "embed", "konustur", "tweet", "pankart", "clyde", "music"]),
    "notlar": ("📝 Not & Özel Komut", ["not-ekle", "notlar", "not-sil", "komut-ekle", "komut-sil", "tag-ekle", "goal"]),
    "pro": ("💎 Pro", ["pro", "pro-ver", "pro-al", "pro-liste", "reklam-sunucu", "reklam", "reklam-komut", "reklam-mesaj"]),
    "owner": ("👑 Owner", ["owner", "blacklist", "maintenance", "sunucu-listesi", "duyuru", "emoji", "sahip", "pp-ayarla"]),
}

PREFIX_HELP_DESCRIPTIONS = {
    "prefix": "Sunucunun özel komut önekini ayarlar.", "log": "Genel log kanalını ve log sistemini yönetir.",
    "modlog": "Moderasyon olaylarının gönderileceği kanalı ayarlar.", "hosgeldin": "Yeni üyeler için karşılama mesajını yönetir.",
    "otorol": "Yeni üyelere otomatik verilecek rolü ayarlar.", "reklam-sunucu": "Owner tarafından reklam sunucusunu tanımlar.",
    "reklam": "Global reklam katılım şartını açar veya kapatır.", "reklam-komut": "Reklam şartını belirli komutlara uygular veya kaldırır.",
    "reklam-mesaj": "Reklam katılımında gösterilecek özel mesajı ayarlar.", "pro-ver": "Bir kullanıcıya süreli veya kalıcı Pro verir.",
    "pro-al": "Kullanıcının Pro üyeliğini kaldırır.", "emoji": "Katre'nin sistem emojilerini owner olarak yönetir.",
    "oneri-kanal": "Önerilerin gönderileceği kanalı belirler.", "not-ekle": "Kendine veya sunucuya hızlı not kaydeder.",
    "notlar": "Kayıtlı notlarını listeler.", "not-sil": "Seçtiğin notu siler.", "komut-ekle": "Sunucuya özel bir k! özel komutu oluşturur.",
    "komut-sil": "Sunucuya özel özel komutu kaldırır.", "tag-ekle": "Sunucu tag sistemine yeni tag ekler.", "tag": "Sunucu tag bilgisini gösterir veya yönetir.",
    "süreli-rol": "Bir üyeye belirli süreli rol verir.", "levelrol": "Seviyelere göre otomatik rol dağıtımını ayarlar.",
    "roller": "Sunucudaki rolleri düzenli biçimde listeler.", "kanallar": "Sunucudaki kanalları kategorileriyle listeler.",
    "herkese-rolver": "Belirlenen rolü uygun üyelere topluca verir.", "herkesten-rolal": "Belirlenen rolü üyelerden topluca alır.",
    "isimdeğiştir": "Bir üyenin sunucu takma adını değiştirir.", "isimleri-sifirla": "Üyelerin takma adlarını sıfırlamak için yönetim aracı sunar.",
    "yavasmod": "Kanal için yavaş mod süresini ayarlar.", "yasaklilar": "Sunucunun banlı kullanıcılarını listeler.",
    "yasaklari-temizle": "Ban listesini toplu yönetmek için yönetici aracıdır.", "yasakli-kanal": "Belirli kanallarda komut kullanımını kısıtlar.",
    "yasakli-komut": "Sunucuda belirli komutları yasaklar veya açar.", "yasakli-kelimeler": "Yasaklı kelime listesini görüntüler ve yönetir.",
    "capslock": "Aşırı büyük harf filtresini yönetir.", "koruma": "Sunucunun güvenlik/koruma ayarlarını yönetir.",
    "dogumgunu": "Doğum günü bilgisini kaydeder veya görüntüler.", "gorevli": "Sunucu görevli rol/ayar sistemini yönetir.",
    "gorevliler": "Sunucudaki görevli yapılandırmasını gösterir.", "davetlink": "Sunucu için kullanılabilir davet bağlantısı oluşturur.",
    "davetler": "Sunucunun davet bilgilerini ve istatistiklerini gösterir.", "ozeloda": "Kullanıcıya özel geçici ses/oda sistemi başlatır.",
    "oda-kapat": "Açılmış özel odayı kapatır.", "tkm": "Taş-kâğıt-makas oyunu oynatır.", "yazitura": "Yazı-tura atar.", "zar": "Zar atar.",
    "slot": "Basit slot/şans oyunu çalıştırır.", "terscevir": "Verilen metni tersine çevirir.", "hesap": "Basit matematik hesaplamaları yapar.",
    "surecevir": "Süre birimlerini birbirine dönüştürür.", "rastgele": "Verilen seçeneklerden rastgele seçim yapar.", "renk": "Renk kodları ve renk yardımcı aracını gösterir.",
    "id": "Kullanıcı, rol, kanal veya sunucu ID'sini bulmaya yardımcı olur.", "metin": "Metin üzerinde çeşitli biçimlendirme işlemleri yapar.",
    "shard": "Bot shard durumunu gösterir.", "music": "Müzik sistemi hakkında bilgi/komut arayüzünü açar.",
    "istatistik-kur": "Sunucu istatistik kanal sistemini kurar.", "logkur": "Log sistemini hızlı biçimde kurar.", "logkaldir": "Log sistemini kaldırır.",
    "reset": "Sunucu Katre ayarlarını yönetici olarak sıfırlar.", "embed": "Özel embed mesajı oluşturur.", "say": "Botun belirlenen metni embedli biçimde söylemesini sağlar.",
    "butonrol": "Buton üzerinden rol alma paneli oluşturur.", "menurol": "Select menü üzerinden rol alma paneli oluşturur.",
    "konustur": "Botun belirlenen kanalda mesaj göndermesini sağlar.", "tweet": "Tweet benzeri görsel/metin içeriği oluşturur.",
    "pankart": "Pankart tarzı metin görseli oluşturur.", "clyde": "Clyde tarzı eğlenceli mesaj üretir.", "pet": "Sanal pet sistemini yönetir.",
    "ciftlik": "Basit çiftlik/eşya yönetim oyununu açar.", "mayintarlasi": "Mayın tarlası mini oyunu oynatır.", "adamasmaca": "Adam asmaca oyunu başlatır.",
    "kelimebulmaca": "Kelime bulmaca oyunu başlatır.", "xox": "XOX oyunu başlatır.", "sudoku": "Sudoku mini oyununu açar.", "qr": "Metinden QR kod oluşturur.",
    "bugun": "Günün bilgisini veya günlük içeriği gösterir.", "goal": "Kişisel hedef ekleme ve takip aracını kullanır.",
    "owner": "Owner yönetim panelini açar; yalnızca bot owner'ları kullanabilir.", "blacklist": "Global blacklist sistemini owner olarak yönetir.",
    "maintenance": "Botun global bakım modunu owner olarak açıp kapatır.", "sunucu-listesi": "Botun bulunduğu sunucuları owner panelinde listeler.",
    "duyuru": "Botun bulunduğu sunuculara owner duyurusu gönderir.", "sahip": "Owner'a özel butonlu Katre kontrol merkezini açar.", "pp-ayarla": "Paket içindeki Katre profil görselini bot avatarına uygular; yalnızca owner kullanabilir.",
}


def help_command_info(name: str):
    meta = COMMAND_HELP_META.get(name)
    if meta:
        desc, params = meta
        usage = f"k!{name}" + (" " + " ".join(params) if params else "")
        return desc, usage, name == "yardim"
    desc = PREFIX_HELP_DESCRIPTIONS.get(name, "Katre özelliğini çalıştırır; sonucu modern embed arayüzüyle gösterir.")
    return desc, f"k!{name}", False



OWNER_ONLY_HELP = {
    "owner", "blacklist", "maintenance", "sunucu-listesi", "duyuru", "emoji", "sahip", "pp-ayarla",
    "pro-ver", "pro-al", "pro-liste",
    "reklam-sunucu", "reklam", "reklam-komut", "reklam-mesaj"
}

def help_access_note(name: str):
    if name in OWNER_ONLY_HELP:
        return "👑 Yalnızca Katre owner"
    perms = PREFIX_PERMISSION_REQUIREMENTS.get(name) if "PREFIX_PERMISSION_REQUIREMENTS" in globals() else None
    if perms:
        return "🛡️ " + ", ".join(p.replace("_", " ").title() for p in perms)
    if name == "pro":
        return "💎 Herkes görebilir; Pro durumu kişiye özeldir"
    return "🆓 Tüm üyeler (komuta özel kurallar olabilir)"

def help_visible_categories(user_id=None):
    owner = user_id in OWNER_IDS if user_id is not None else False
    result = {}
    known = set()
    for key, (title, names) in HELP_CATEGORIES.items():
        visible = [n for n in names if owner or n not in OWNER_ONLY_HELP]
        known.update(names)
        if visible:
            result[key] = (title, visible)
    # Yeni eklenen bir komut yardım listesinden asla kaybolmasın.
    all_commands = set(COMMAND_HELP_META) | set(PREFIX_ONLY_COMMANDS) | {"sahip", "emoji", "pp-ayarla"}
    missing = sorted(all_commands - known)
    if missing:
        visible_missing = [n for n in missing if owner or n not in OWNER_ONLY_HELP]
        if visible_missing:
            result["diger"] = ("🧩 Diğer Katre Komutları", visible_missing)
    return result


def help_category_commands(key):
    return HELP_CATEGORIES[key][1]


def help_embed_for(category=None, page=0, user_id=None):
    categories = help_visible_categories(user_id)
    if category not in categories:
        category = None
    if category is None:
        total = sum(len(v[1]) for v in categories.values())
        e = embed(
            "Katre • Yardım Merkezi",
            "Katre'nin **tüm komutlarını** kategoriler üzerinden ayrıntılı biçimde inceleyebilirsin.\n\n"
            "🔹 Botta yayınlanan **tek slash komutu:** **`/yardim`**\n"
            "🔹 Diğer **tüm komutlar yalnızca `k!`** ile çalışır.\n"
            "🔹 Her komutun açıklaması, kullanım şekli, örneği ve erişim bilgisi aşağıdadır.",
            discord.Color.blurple()
        )
        for key, (title, names) in categories.items():
            e.add_field(name=title, value=f"**{len(names)} komut**\nMenüden ayrıntıları aç.", inline=True)
        e.add_field(
            name="📌 Kullanım Sözlüğü",
            value="`<zorunlu>` = mutlaka yazılmalı\n`[opsiyonel]` = yazılması isteğe bağlı\n`k!yardim` = bu menüyü prefix ile açar",
            inline=False
        )
        e.set_footer(text=f"Katre {VERSION} • {total} kullanıcıya açık komut + owner'a özel komutlar")
        return e

    title, names = categories[category]
    per_page = 5
    total_pages = max(1, (len(names) + per_page - 1) // per_page)
    page = max(0, min(page, total_pages - 1))
    chunk = names[page * per_page:(page + 1) * per_page]
    e = embed(f"Katre • {title}", f"Bu kategoride **{len(names)} komut** var • Sayfa **{page + 1}/{total_pages}**", discord.Color.blurple())
    for name in chunk:
        desc, usage, slash = help_command_info(name)
        access = "`/yardim` üzerinden açıklanır" if name == "yardim" else "`k!`"
        access_note = help_access_note(name)
        e.add_field(
            name=f"{access} {name}",
            value=f"**Açıklama:** {desc}\n**Kullanım:** `{usage}`\n**Erişim:** {access_note}\n**Komut biçimi:** `k!{name}`",
            inline=False
        )
    e.set_footer(text=f"Katre {VERSION} • Tüm özellikler prefix: k!")
    return e


class HelpCategorySelect(discord.ui.Select):
    def __init__(self, view_ref):
        categories = help_visible_categories(view_ref.author_id)
        options = [discord.SelectOption(label=title.replace("🏠 ", "").replace("👤 ", "").replace("💰 ", "").replace("⭐ ", "").replace("🛡️ ", "").replace("⚙️ ", "").replace("🎭 ", "").replace("🔒 ", "").replace("🎉 ", "").replace("🎮 ", "").replace("🧰 ", "").replace("📝 ", "").replace("💎 ", "").replace("👑 ", ""), value=key, description=f"{len(names)} komut", emoji=title.split()[0]) for key, (title, names) in categories.items()]
        super().__init__(placeholder="📚 Bir kategori seç...", min_values=1, max_values=1, options=options)
        self.view_ref = view_ref

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.view_ref.author_id:
            return await interaction.response.send_message("Bu yardım menüsünü yalnızca komutu açan kişi kullanabilir.", ephemeral=True)
        self.view_ref.category = self.values[0]
        self.view_ref.page = 0
        self.view_ref.refresh()
        await interaction.response.edit_message(embed=help_embed_for(self.view_ref.category, 0, self.view_ref.author_id), view=self.view_ref)


class HelpHomeButton(discord.ui.Button):
    def __init__(self):
        super().__init__(label="Ana Sayfa", style=discord.ButtonStyle.primary, emoji="🏠")
    async def callback(self, interaction: discord.Interaction):
        v = self.view
        if interaction.user.id != v.author_id:
            return await interaction.response.send_message("Bu yardım menüsünü yalnızca komutu açan kişi kullanabilir.", ephemeral=True)
        v.category = None
        v.page = 0
        v.refresh()
        await interaction.response.edit_message(embed=help_embed_for(user_id=v.author_id), view=v)


class HelpPrevButton(discord.ui.Button):
    def __init__(self):
        super().__init__(label="Önceki", style=discord.ButtonStyle.secondary, emoji="◀️")
    async def callback(self, interaction: discord.Interaction):
        v = self.view
        if interaction.user.id != v.author_id:
            return await interaction.response.send_message("Bu yardım menüsünü yalnızca komutu açan kişi kullanabilir.", ephemeral=True)
        if not v.category:
            return await interaction.response.defer()
        v.page = max(0, v.page - 1)
        v.refresh()
        await interaction.response.edit_message(embed=help_embed_for(v.category, v.page, v.author_id), view=v)


class HelpNextButton(discord.ui.Button):
    def __init__(self):
        super().__init__(label="Sonraki", style=discord.ButtonStyle.secondary, emoji="▶️")
    async def callback(self, interaction: discord.Interaction):
        v = self.view
        if interaction.user.id != v.author_id:
            return await interaction.response.send_message("Bu yardım menüsünü yalnızca komutu açan kişi kullanabilir.", ephemeral=True)
        if not v.category:
            return await interaction.response.defer()
        categories = help_visible_categories(v.author_id)
        total = max(1, (len(categories[v.category][1]) + 4) // 5)
        v.page = min(total - 1, v.page + 1)
        v.refresh()
        await interaction.response.edit_message(embed=help_embed_for(v.category, v.page, v.author_id), view=v)


class HelpCloseButton(discord.ui.Button):
    def __init__(self):
        super().__init__(label="Kapat", style=discord.ButtonStyle.danger, emoji="✖️")
    async def callback(self, interaction: discord.Interaction):
        v = self.view
        if interaction.user.id != v.author_id:
            return await interaction.response.send_message("Bu yardım menüsünü yalnızca komutu açan kişi kullanabilir.", ephemeral=True)
        await interaction.response.edit_message(content="Katre yardım merkezi kapatıldı.", embed=None, view=None)


class HelpView(discord.ui.View):
    def __init__(self, author_id):
        super().__init__(timeout=300)
        self.author_id = author_id
        self.category = None
        self.page = 0
        self.refresh()

    def refresh(self):
        self.clear_items()
        self.add_item(HelpCategorySelect(self))
        self.add_item(HelpHomeButton())
        prev = HelpPrevButton(); prev.disabled = self.category is None or self.page <= 0
        nxt = HelpNextButton()
        categories = help_visible_categories(self.author_id)
        if self.category and self.category in categories:
            total = max(1, (len(categories[self.category][1]) + 4) // 5)
            nxt.disabled = self.page >= total - 1
        else:
            nxt.disabled = True
        self.add_item(prev); self.add_item(nxt); self.add_item(HelpCloseButton())

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True


# ----------------------------- KATRE V5 GLOBAL UI -----------------------------

class KatreActionView(discord.ui.View):
    """Komutların çoğunda ortak, hafif ve işlevsel alt menü."""
    def __init__(self, author_id=None, timeout=180):
        super().__init__(timeout=timeout)
        self.author_id = author_id
        self.add_item(KatreHelpButton())
        self.add_item(KatreHomeButton())
        self.add_item(KatreCloseButton())

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if self.author_id is None or interaction.user.id == self.author_id:
            return True
        await interaction.response.send_message(
            embed=embed("Katre", "Bu paneli yalnızca komutu kullanan kişi kontrol edebilir.", discord.Color.orange()),
            ephemeral=True
        )
        return False

class KatreHelpButton(discord.ui.Button):
    def __init__(self):
        super().__init__(label="Yardım", style=discord.ButtonStyle.secondary, emoji=E("info"))
    async def callback(self, interaction: discord.Interaction):
        await send_help(interaction, interaction.user.id)

class KatreHomeButton(discord.ui.Button):
    def __init__(self):
        super().__init__(label="Ana Menü", style=discord.ButtonStyle.primary, emoji=E("home"))
    async def callback(self, interaction: discord.Interaction):
        await interaction.response.edit_message(
            embed=help_embed_for(user_id=interaction.user.id),
            view=HelpView(interaction.user.id)
        )

class KatreCloseButton(discord.ui.Button):
    def __init__(self):
        super().__init__(label="Kapat", style=discord.ButtonStyle.danger, emoji=E("close"))
    async def callback(self, interaction: discord.Interaction):
        await interaction.response.edit_message(
            content=None,
            embed=embed("Katre", "Panel kapatıldı. Yeniden açmak için `/yardim` veya `k!yardim` kullanabilirsin.", discord.Color.dark_grey()),
            view=None
        )

# Slash callback'lerinin tek tek değiştirilmesine gerek kalmadan, düz metin
# cevaplarını da embed + ortak buton arayüzüne yükseltir. Özel View kullanan
# komutların kendi butonları aynen korunur.
_original_interaction_send_message = discord.InteractionResponse.send_message

async def _katre_interaction_send_message(self, content=None, *args, **kwargs):
    if content is not None and not kwargs.get("embed") and not kwargs.get("embeds"):
        kwargs["embed"] = embed("Katre", str(content), discord.Color.blurple())
        content = None
    if kwargs.get("view") is None:
        parent = getattr(self, "_parent", None)
        kwargs["view"] = KatreActionView(getattr(getattr(parent, "user", None), "id", None))
    return await _original_interaction_send_message(self, content, *args, **kwargs)

discord.InteractionResponse.send_message = _katre_interaction_send_message

async def katre_followup(interaction, content=None, **kwargs):
    """Defer + followup kullanan komutları da ortak Katre UI'sına taşır."""
    if content is not None and not kwargs.get("embed") and not kwargs.get("embeds"):
        kwargs["embed"] = embed("Katre", str(content), discord.Color.blurple())
        content = None
    if kwargs.get("view") is None:
        kwargs["view"] = KatreActionView(getattr(interaction.user, "id", None))
    return await interaction.followup.send(content=content, **kwargs)


async def send_help(target, user_id):
    view = HelpView(user_id)
    if isinstance(target, discord.Interaction):
        await target.response.send_message(embed=help_embed_for(user_id=user_id), view=view)
    else:
        await target.send(embed=help_embed_for(user_id=user_id), view=view)


@bot.tree.command(name="yardim", description="Katre'nin kategorili, butonlu ve ayrıntılı yardım merkezini açar.")
async def yardim(i: discord.Interaction):
    await send_help(i, i.user.id)

@bot.tree.command(name="ping", description="Bot gecikmesini gösterir.")
async def ping(i):
    await i.response.send_message(embed=embed("Pong! 🏓", f"Gateway: **{round(bot.latency*1000)}ms**\nUptime: **{fmt_seconds(time.time()-START)}**", discord.Color.green()))

@bot.tree.command(name="davet", description="Katre'yi sunucuna eklemek için davet linkini verir.")
async def davet(i):
    app_id = bot.user.id if bot.user else 0
    url = f"https://discord.com/oauth2/authorize?client_id={app_id}&permissions=8&scope=bot%20applications.commands"
    desc = f"**Katre'yi sunucuna ekle:**\n[✦ Davet Et]({url})"
    if SUPPORT_URL: desc += f"\n[✦ Destek Sunucusu]({SUPPORT_URL})"
    await i.response.send_message(embed=embed("Katre Davet", desc))

@bot.tree.command(name="bot", description="Katre hakkında bilgi.")
async def bot_info(i):
    e = embed("Katre", "Public Discord botu • güvenli, hızlı ve geliştirilebilir.")
    e.add_field(name="Sürüm", value=VERSION)
    e.add_field(name="Sunucular", value=str(len(bot.guilds)))
    e.add_field(name="Kullanıcılar", value=f"{sum(g.member_count or 0 for g in bot.guilds):,}")
    e.add_field(name="Pro", value="Aktif" if is_pro(i.user.id) else "Pasif")
    await i.response.send_message(embed=e)

@bot.tree.command(name="sunucu", description="Sunucu bilgilerini gösterir.")
async def sunucu(i):
    g = i.guild
    e = embed(g.name, f"**ID:** `{g.id}`\n**Sahip:** <@{g.owner_id}>\n**Üye:** `{g.member_count}`\n**Kanal:** `{len(g.channels)}`\n**Rol:** `{len(g.roles)}`\n**Kuruluş:** <t:{int(g.created_at.timestamp())}:F>")
    if g.icon: e.set_thumbnail(url=g.icon.url)
    await i.response.send_message(embed=e)

@bot.tree.command(name="kullanici", description="Kullanıcı bilgilerini gösterir.")
@app_commands.describe(member="Bilgileri gösterilecek kullanıcı")
async def kullanici(i, member: Optional[discord.Member] = None):
    m = member or i.user
    u = user_data(m.id, i.guild.id)
    e = embed(f"{m.display_name}", f"**ID:** `{m.id}`\n**Katılma:** <t:{int(m.joined_at.timestamp())}:R>\n**Hesap:** <t:{int(m.created_at.timestamp())}:R>\n**Seviye:** `{level_for_xp(u['xp'])}`\n**XP:** `{u['xp']}`\n**Coin:** `{u['coins']}`\n**Pro:** `{'Evet' if is_pro(m.id) else 'Hayır'}`")
    e.set_thumbnail(url=m.display_avatar.url)
    await i.response.send_message(embed=e)

@bot.tree.command(name="avatar", description="Kullanıcının avatarını gösterir.")
async def avatar(i, member: Optional[discord.Member] = None):
    m = member or i.user
    e = embed(f"{m.display_name} • Avatar")
    e.set_image(url=m.display_avatar.url)
    await i.response.send_message(embed=e)

@bot.tree.command(name="istatistik", description="Katre istatistiklerini gösterir.")
async def istatistik(i):
    await i.response.send_message(embed=embed("Katre İstatistikleri",
        f"**Sunucu:** `{len(bot.guilds)}`\n**Kullanıcı:** `{sum(g.member_count or 0 for g in bot.guilds):,}`\n"
        f"**Ping:** `{round(bot.latency*1000)}ms`\n**Uptime:** `{fmt_seconds(time.time()-START)}`"))

# ----------------------------- USER -----------------------------

@bot.tree.command(name="afk", description="AFK durumunu ayarlar.")
@app_commands.describe(reason="AFK sebebi")
async def afk(i, reason: str = "Belirtilmedi"):
    user_data(i.user.id, i.guild.id)["afk"] = reason
    await persist()
    await i.response.send_message(embed=embed("AFK", f"AFK modun açıldı.\n**Sebep:** {reason}", discord.Color.green()))

@bot.tree.command(name="rep", description="Bir kullanıcıya itibar puanı verir.")
async def rep(i, member: discord.Member):
    if member.id == i.user.id:
        return await i.response.send_message("Kendine rep veremezsin.", ephemeral=True)
    # Günlük basit cooldown
    cd = getattr(bot, "_rep_cd", {})
    setattr(bot, "_rep_cd", cd)
    key = (i.guild.id, i.user.id)
    if now_ts() - cd.get(key, 0) < 86400:
        return await i.response.send_message("Bugün zaten rep verdin.", ephemeral=True)
    cd[key] = now_ts()
    user_data(member.id, i.guild.id)["rep"] += 1
    await persist()
    await i.response.send_message(embed=embed("İtibar +1", f"{member.mention} artık **{user_data(member.id,i.guild.id)['rep']} rep** puanına sahip.", discord.Color.green()))

@bot.tree.command(name="rank", description="Seviye kartı yerine temiz bir rank bilgisi gösterir.")
async def rank(i, member: Optional[discord.Member] = None):
    m = member or i.user
    u = user_data(m.id, i.guild.id)
    lvl = level_for_xp(u["xp"])
    need = xp_needed(lvl)
    await i.response.send_message(embed=embed("Rank", f"{m.mention}\n\n**Seviye:** `{lvl}`\n**XP:** `{u['xp']}/{need}`\n**Rep:** `{u['rep']}`\n**Coin:** `{u['coins']}`"))

@bot.tree.command(name="leaderboard", description="XP sıralamasını gösterir.")
async def leaderboard(i):
    users = DB["users"].get(str(i.guild.id), {})
    rows = sorted(users.items(), key=lambda x: x[1].get("xp", 0), reverse=True)[:10]
    text = "\n".join(f"**{n}.** <@{uid}> — `{d.get('xp',0)} XP` • `{level_for_xp(d.get('xp',0))}. lvl`" for n,(uid,d) in enumerate(rows,1))
    await i.response.send_message(embed=embed("XP Leaderboard", text or "Henüz veri yok."))

# ----------------------------- ECONOMY -----------------------------

@bot.tree.command(name="bakiye", description="Coin bakiyeni gösterir.")
async def bakiye(i, member: Optional[discord.Member] = None):
    m = member or i.user
    await i.response.send_message(embed=embed("Cüzdan", f"{m.mention} • **{user_data(m.id,i.guild.id)['coins']:,}** Katre Coin 🪙"))

@bot.tree.command(name="gunluk", description="Günlük coin ödülünü al.")
async def gunluk(i):
    u = user_data(i.user.id, i.guild.id)
    if now_ts() - u.get("daily", 0) < 86400:
        return await i.response.send_message(f"⏳ Tekrar alabilmek için **{fmt_seconds(86400-(now_ts()-u['daily']))}** beklemelisin.", ephemeral=True)
    amount = 250 + (100 if is_pro(i.user.id) else 0)
    u["coins"] += amount; u["daily"] = now_ts()
    await persist()
    await i.response.send_message(embed=embed("Günlük Ödül 🎁", f"**+{amount} Coin** aldın!"))

@bot.tree.command(name="calis", description="Çalışıp coin kazan.")
async def calis(i):
    u = user_data(i.user.id, i.guild.id)
    if now_ts() - u.get("work", 0) < 3600:
        return await i.response.send_message("⏳ Saatlik çalışma hakkını kullandın.", ephemeral=True)
    amount = random.randint(100, 350) + (100 if is_pro(i.user.id) else 0)
    u["coins"] += amount; u["work"] = now_ts()
    await persist()
    jobs = ["kod yazdın", "bir proje tasarladın", "sunucu yönettin", "müşteri desteği verdin"]
    await i.response.send_message(embed=embed("Çalışma", f"Bugün **{random.choice(jobs)}** ve **{amount} Coin** kazandın. 🪙"))

@bot.tree.command(name="transfer", description="Başka kullanıcıya coin gönder.")
async def transfer(i, member: discord.Member, amount: app_commands.Range[int, 1, 1_000_000]):
    if member.id == i.user.id:
        return await i.response.send_message("Kendine coin gönderemezsin.", ephemeral=True)
    u = user_data(i.user.id, i.guild.id); t = user_data(member.id, i.guild.id)
    if u["coins"] < amount:
        return await i.response.send_message("Yeterli bakiyen yok.", ephemeral=True)
    u["coins"] -= amount; t["coins"] += amount
    await persist()
    await i.response.send_message(embed=embed("Transfer", f"{member.mention} kullanıcısına **{amount:,} Coin** gönderildi.", discord.Color.green()))

# ----------------------------- MODERATION -----------------------------

@bot.tree.command(name="ban", description="Kullanıcıyı yasaklar.")
@app_commands.checks.has_permissions(ban_members=True)
async def ban(i, member: discord.Member, reason: str = "Belirtilmedi"):
    if not role_targetable(i.guild, member, i.user):
        return await i.response.send_message("Bu kullanıcıyı yönetemiyorum.", ephemeral=True)
    await safe_dm(member, f"**{i.guild.name}** sunucusundan banlandın.\nSebep: {reason}")
    await member.ban(reason=reason)
    await send_log(i.guild, "Ban", f"{member} **banlandı**.\nYetkili: {i.user.mention}\nSebep: {reason}", discord.Color.red(), True)
    await i.response.send_message(embed=embed("Banlandı", f"{member} başarıyla banlandı.", discord.Color.red()))

@bot.tree.command(name="unban", description="Ban kaldırır.")
@app_commands.checks.has_permissions(ban_members=True)
async def unban(i, user_id: str):
    try: uid = int(user_id)
    except: return await i.response.send_message("Geçerli bir ID gir.", ephemeral=True)
    try:
        user = await bot.fetch_user(uid)
        await i.guild.unban(user)
        await i.response.send_message(embed=embed("Ban Kaldırıldı", f"{user} tekrar davet edilebilir.", discord.Color.green()))
    except Exception as e:
        await i.response.send_message(f"Ban kaldırılamadı: `{e}`", ephemeral=True)

@bot.tree.command(name="kick", description="Kullanıcıyı sunucudan atar.")
@app_commands.checks.has_permissions(kick_members=True)
async def kick(i, member: discord.Member, reason: str = "Belirtilmedi"):
    if not role_targetable(i.guild, member, i.user):
        return await i.response.send_message("Bu kullanıcıyı yönetemiyorum.", ephemeral=True)
    await safe_dm(member, f"**{i.guild.name}** sunucusundan atıldın.\nSebep: {reason}")
    await member.kick(reason=reason)
    await send_log(i.guild, "Kick", f"{member} **atıldı**.\nYetkili: {i.user.mention}\nSebep: {reason}", discord.Color.orange(), True)
    await i.response.send_message(embed=embed("Atıldı", f"{member} sunucudan atıldı.", discord.Color.orange()))

@bot.tree.command(name="timeout", description="Kullanıcıya süreli timeout verir.")
@app_commands.checks.has_permissions(moderate_members=True)
async def timeout(i, member: discord.Member, duration: str, reason: str = "Belirtilmedi"):
    seconds = human_duration(duration)
    if seconds < 1 or seconds > 28*86400:
        return await i.response.send_message("Süre 1 saniye ile 28 gün arasında olmalı. Örnek: `10m`, `2h`, `1d`.", ephemeral=True)
    if not role_targetable(i.guild, member, i.user):
        return await i.response.send_message("Bu kullanıcıyı yönetemiyorum.", ephemeral=True)
    await member.timeout(timedelta(seconds=seconds), reason=reason)
    await send_log(i.guild, "Timeout", f"{member.mention} **{fmt_seconds(seconds)}** timeout.\nSebep: {reason}", discord.Color.orange(), True)
    await i.response.send_message(embed=embed("Timeout", f"{member.mention} **{fmt_seconds(seconds)}** susturuldu.", discord.Color.orange()))

@bot.tree.command(name="untimeout", description="Timeout kaldırır.")
@app_commands.checks.has_permissions(moderate_members=True)
async def untimeout(i, member: discord.Member):
    await member.timeout(None, reason="Katre untimeout")
    await i.response.send_message(embed=embed("Timeout Kaldırıldı", member.mention, discord.Color.green()))

@bot.tree.command(name="sil", description="Mesaj siler.")
@app_commands.checks.has_permissions(manage_messages=True)
async def sil(i, amount: app_commands.Range[int, 1, 100]):
    await i.response.defer(ephemeral=True)
    deleted = await i.channel.purge(limit=amount)
    await katre_followup(i, embed=embed("Temizlendi", f"**{len(deleted)}** mesaj silindi.", discord.Color.green()), ephemeral=True)

@bot.tree.command(name="kilit", description="Kanalı kilitler/açar.")
@app_commands.checks.has_permissions(manage_channels=True)
async def kilit(i, durum: str):
    durum = durum.lower()
    overwrite = i.channel.overwrites_for(i.guild.default_role)
    overwrite.send_messages = False if durum in ("aç", "ac", "kilit", "lock") else None
    await i.channel.set_permissions(i.guild.default_role, overwrite=overwrite)
    await i.response.send_message(embed=embed("Kanal", "Kanal kilitlendi. 🔒" if overwrite.send_messages is False else "Kanalın kilidi açıldı. 🔓"))

@bot.tree.command(name="uyar", description="Kullanıcıyı uyarır.")
@app_commands.checks.has_permissions(moderate_members=True)
async def uyar(i, member: discord.Member, reason: str = "Belirtilmedi"):
    u = user_data(member.id, i.guild.id)
    u["warnings"].append({"reason": reason, "moderator": i.user.id, "at": now_ts()})
    await persist()
    await safe_dm(member, f"**{i.guild.name}** sunucusunda uyarıldın.\nSebep: {reason}")
    await i.response.send_message(embed=embed("Uyarı", f"{member.mention} uyarıldı.\nToplam uyarı: **{len(u['warnings'])}**", discord.Color.orange()))

@bot.tree.command(name="uyarilar", description="Kullanıcının uyarılarını gösterir.")
@app_commands.checks.has_permissions(moderate_members=True)
async def uyarilar(i, member: discord.Member):
    rows = user_data(member.id, i.guild.id)["warnings"]
    text = "\n".join(f"`{n}` <t:{x['at']}:R> — {x['reason']} — <@{x['moderator']}>" for n,x in enumerate(rows[-15:],1))
    await i.response.send_message(embed=embed("Uyarılar", text or "Uyarı yok."), ephemeral=True)

# ----------------------------- SERVER SETTINGS -----------------------------

@app_commands.checks.has_permissions(manage_guild=True)
async def prefix(i, value: str):
    if len(value) > 5: return await i.response.send_message("Prefix en fazla 5 karakter.", ephemeral=True)
    guild_data(i.guild.id)["prefix"] = value
    await persist()
    await i.response.send_message(embed=embed("Prefix", f"Yeni prefix: `{value}`"))

@app_commands.checks.has_permissions(manage_guild=True)
async def log_cmd(i, channel: Optional[discord.TextChannel] = None):
    guild_data(i.guild.id)["log_channel"] = channel.id if channel else None
    await persist()
    await i.response.send_message(ok(f"Log kanalı {'#'+channel.name if channel else 'kapatıldı'}."))

@app_commands.checks.has_permissions(manage_guild=True)
async def modlog(i, channel: Optional[discord.TextChannel] = None):
    guild_data(i.guild.id)["modlog_channel"] = channel.id if channel else None
    await persist()
    await i.response.send_message(ok("Moderasyon logu güncellendi."))

@app_commands.checks.has_permissions(manage_guild=True)
async def hosgeldin(i, channel: Optional[discord.TextChannel] = None, text: Optional[str] = None):
    cfg = guild_data(i.guild.id)
    cfg["welcome_channel"] = channel.id if channel else None
    if text: cfg["welcome_text"] = text
    await persist()
    await i.response.send_message(ok("Hoş geldin sistemi güncellendi."))

@app_commands.checks.has_permissions(manage_roles=True)
async def otorol(i, role: Optional[discord.Role] = None):
    cfg = guild_data(i.guild.id)
    if role and not role_targetable(i.guild, role, i.user):
        return await i.response.send_message("Bu rolü veremiyorum; bot rolü rolün üstünde olmalı.", ephemeral=True)
    cfg["autorole"] = role.id if role else None
    await persist()
    await i.response.send_message(ok(f"Otorol {'@'+role.name if role else 'kapatıldı'}."))

@bot.tree.command(name="ayarlar", description="Sunucunun Katre ayar özetini gösterir.")
@app_commands.checks.has_permissions(manage_guild=True)
async def ayarlar(i):
    c = guild_data(i.guild.id)
    e = embed("Sunucu Ayarları")
    e.add_field(name="Prefix", value=f"`{c['prefix']}`")
    e.add_field(name="Log", value=f"<#{c['log_channel']}>" if c["log_channel"] else "Kapalı")
    e.add_field(name="ModLog", value=f"<#{c['modlog_channel']}>" if c["modlog_channel"] else "Kapalı")
    e.add_field(name="Hoş Geldin", value=f"<#{c['welcome_channel']}>" if c["welcome_channel"] else "Kapalı")
    e.add_field(name="Otorol", value=f"<@&{c['autorole']}>" if c["autorole"] else "Kapalı")
    e.add_field(name="AutoMod", value="Açık" if c["automod_enabled"] else "Kapalı")
    e.add_field(name="Reklam Şartı", value="Açık" if c["advertising"]["enabled"] else "Kapalı")
    await i.response.send_message(embed=e, ephemeral=True)

# ----------------------------- AUTOMOD -----------------------------

@bot.tree.command(name="otomod", description="AutoMod'u açar/kapatır.")
@app_commands.checks.has_permissions(manage_guild=True)
async def otomod(i, durum: str):
    val = durum.lower() in ("aç","ac","on","true","1")
    guild_data(i.guild.id)["automod_enabled"] = val
    await persist()
    await i.response.send_message(ok(f"AutoMod {'açıldı' if val else 'kapatıldı'}."))

@bot.tree.command(name="otomod-link", description="Link filtresini aç/kapat.")
@app_commands.checks.has_permissions(manage_guild=True)
async def otomod_link(i, durum: str):
    guild_data(i.guild.id)["automod_links"] = durum.lower() in ("aç","ac","on","true","1")
    await persist(); await i.response.send_message(ok("Link filtresi güncellendi."))

@bot.tree.command(name="otomod-davet", description="Discord davet filtresini aç/kapat.")
@app_commands.checks.has_permissions(manage_guild=True)
async def otomod_davet(i, durum: str):
    guild_data(i.guild.id)["automod_invites"] = durum.lower() in ("aç","ac","on","true","1")
    await persist(); await i.response.send_message(ok("Davet filtresi güncellendi."))

@bot.tree.command(name="yasakli-kelime", description="Yasaklı kelime ekler.")
@app_commands.checks.has_permissions(manage_guild=True)
async def yasakli_kelime(i, kelime: str):
    cfg = guild_data(i.guild.id)
    if kelime.lower() not in cfg["automod_badwords"]:
        cfg["automod_badwords"].append(kelime.lower())
    await persist(); await i.response.send_message(ok(f"`{kelime}` eklendi."))

# ----------------------------- ADVERTISING / PRO -----------------------------

async def reklam_sunucu(i, guild_id: str, invite: str):
    if not is_owner(i.user): return await i.response.send_message("Bu komut sadece Katre owner'ı içindir.", ephemeral=True)
    try: int(guild_id)
    except: return await i.response.send_message("Geçerli bir sunucu ID gir.", ephemeral=True)
    cfg = guild_data(i.guild.id)
    cfg["advertising"]["guild_id"] = guild_id
    cfg["advertising"]["invite"] = invite
    await persist()
    await i.response.send_message(ok("Reklam sunucusu ayarlandı."), ephemeral=True)

async def reklam(i, durum: str):
    if not is_owner(i.user): return await i.response.send_message("Owner komutu.", ephemeral=True)
    val = durum.lower() in ("aç","ac","on","true","1")
    guild_data(i.guild.id)["advertising"]["enabled"] = val
    await persist()
    await i.response.send_message(ok(f"Genel reklam şartı {'açıldı' if val else 'kapatıldı'}."))

async def reklam_komut(i, komut: str, durum: str):
    if not is_owner(i.user): return await i.response.send_message("Owner komutu.", ephemeral=True)
    val = durum.lower() in ("aç","ac","on","true","1")
    cfg = guild_data(i.guild.id)
    cfg["command_ads"][komut.lower().lstrip("/")] = {
        "enabled": val,
        "guild_id": cfg["advertising"].get("guild_id"),
        "invite": cfg["advertising"].get("invite"),
        "message": cfg["advertising"].get("message"),
    }
    await persist()
    await i.response.send_message(ok(f"`/{komut}` reklam şartı {'açıldı' if val else 'kapatıldı'}."))

async def reklam_mesaj(i, *, message: str):
    if not is_owner(i.user): return await i.response.send_message("Owner komutu.", ephemeral=True)
    guild_data(i.guild.id)["advertising"]["message"] = message
    await persist(); await i.response.send_message(ok("Reklam mesajı güncellendi."))

@bot.tree.command(name="pro", description="Pro durumunu gösterir.")
async def pro(i):
    left = pro_left(i.user.id)
    text = "∞ Süresiz Pro" if is_pro(i.user.id) and left == 0 else (f"{fmt_seconds(left)} kaldı" if left else "Pro aktif değil.")
    await i.response.send_message(embed=embed("Katre Pro ✦", f"Durum: **{text}**\n\nPro üyeler reklam katılım şartından muaftır ve bonus XP/coin kazanır.", discord.Color.gold()))

async def pro_ver(i, member: discord.Member, sure: str = "30d"):
    if not is_owner(i.user): return await i.response.send_message("Owner komutu.", ephemeral=True)
    seconds = 0 if sure.lower() in ("süresiz","suresiz","permanent","∞","0") else human_duration(sure)
    if seconds < 0: seconds = 0
    DB["global"]["pro_users"][str(member.id)] = {"until": 0 if seconds == 0 else now_ts()+seconds, "by": i.user.id}
    await persist()
    await i.response.send_message(ok(f"{member.mention} için **{'süresiz' if seconds==0 else fmt_seconds(seconds)} Pro** aktif edildi."))

async def pro_al(i, member: discord.Member):
    if not is_owner(i.user): return await i.response.send_message("Owner komutu.", ephemeral=True)
    DB["global"]["pro_users"].pop(str(member.id), None)
    await persist()
    await i.response.send_message(ok(f"{member.mention} Pro'dan çıkarıldı."))

@bot.tree.command(name="pro-liste", description="Owner: aktif Pro kullanıcılarını listeler.")
async def pro_liste(i):
    if not is_owner(i.user): return await i.response.send_message("Owner komutu.", ephemeral=True)
    rows=[]
    for uid, rec in DB["global"]["pro_users"].items():
        until=rec.get("until",0)
        rows.append(f"<@{uid}> — {'Süresiz' if until==0 else '<t:'+str(until)+':R>'}")
    await i.response.send_message(embed=embed("Pro Kullanıcıları", "\n".join(rows) or "Aktif Pro yok."), ephemeral=True)


async def emoji_slash(i, islem: str = "liste", anahtar: Optional[str] = None, *, emoji: Optional[str] = None):
    if not is_owner(i.user):
        return  # Sessiz.
    islem = islem.lower()
    if islem == "liste":
        lines = [f"`{k}` → {E(k)}" for k in sorted(EMOJI_DEFAULTS)]
        return await i.response.send_message(embed=embed("Emoji Merkezi", "\n".join(lines)))
    if islem in ("sıfırla", "sifirla", "reset"):
        DB["global"]["emojis"] = dict(EMOJI_DEFAULTS)
        await persist()
        return await i.response.send_message(ok("Tüm bot emojileri varsayılanlara döndürüldü."))
    if islem in ("ayarla", "set"):
        if not anahtar or not emoji or anahtar.lower() not in EMOJI_DEFAULTS:
            return await i.response.send_message(f"{E('warn')} Geçerli bir anahtar ve emoji gir.", ephemeral=True)
        DB["global"]["emojis"][anahtar.lower()] = emoji
        await persist()
        return await i.response.send_message(ok(f"`{anahtar.lower()}` emojisi güncellendi: {emoji}"))
    await i.response.send_message(f"{E('info')} `liste`, `ayarla`, `sıfırla` kullanılabilir.", ephemeral=True)


# ----------------------------- TICKETS -----------------------------

class TicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Destek Talebi Aç", style=discord.ButtonStyle.primary, emoji="🎫", custom_id="katre_ticket_open")
    async def open_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        cfg = guild_data(interaction.guild.id)
        category = interaction.guild.get_channel(cfg.get("ticket_category")) if cfg.get("ticket_category") else None
        existing = next((c for c in interaction.guild.text_channels if c.name == f"ticket-{interaction.user.id}"), None)
        if existing:
            return await interaction.response.send_message(f"Zaten açık ticket'ın var: {existing.mention}", ephemeral=True)
        overwrites = {
            interaction.guild.default_role: discord.PermissionOverwrite(view_channel=False),
            interaction.user: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True),
            interaction.guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True, manage_channels=True),
        }
        role = interaction.guild.get_role(cfg.get("ticket_staff_role")) if cfg.get("ticket_staff_role") else None
        if role: overwrites[role] = discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True)
        ch = await interaction.guild.create_text_channel(f"ticket-{interaction.user.id}", category=category, overwrites=overwrites, reason="Katre ticket")
        cfg["tickets"][str(ch.id)] = {"owner": interaction.user.id, "created": now_ts()}
        await persist()
        await ch.send(embed=embed("Katre Destek 🎫", f"{interaction.user.mention}, destek ekibi birazdan ilgilenecek."), view=CloseTicketView())
        await interaction.response.send_message(f"Ticket açıldı: {ch.mention}", ephemeral=True)

class CloseTicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
    @discord.ui.button(label="Ticket Kapat", style=discord.ButtonStyle.danger, emoji="🔒", custom_id="katre_ticket_close")
    async def close_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        cfg = guild_data(interaction.guild.id)
        if str(interaction.channel.id) in cfg["tickets"]:
            cfg["tickets"].pop(str(interaction.channel.id), None)
            await persist()
        await interaction.response.send_message("Ticket 3 saniye içinde kapanıyor.")
        await asyncio.sleep(3)
        try: await interaction.channel.delete(reason="Katre ticket kapatma")
        except: pass

@bot.tree.command(name="ticket-panel", description="Ticket paneli gönderir.")
@app_commands.checks.has_permissions(manage_guild=True)
async def ticket_panel(i):
    await i.response.send_message(embed=embed("Katre Destek Merkezi 🎫", "Destek almak için aşağıdaki butona tıkla."), view=TicketView())

@bot.tree.command(name="ticket-ayarla", description="Ticket kategori/personel rolünü ayarlar.")
@app_commands.checks.has_permissions(manage_guild=True)
async def ticket_ayarla(i, category: Optional[discord.CategoryChannel] = None, staff_role: Optional[discord.Role] = None):
    cfg=guild_data(i.guild.id); cfg["ticket_category"]=category.id if category else None; cfg["ticket_staff_role"]=staff_role.id if staff_role else None
    await persist(); await i.response.send_message(ok("Ticket ayarları güncellendi."))

# ----------------------------- GIVEAWAY / POLL / SUGGESTION -----------------------------

@bot.tree.command(name="cekilis", description="Çekiliş başlatır.")
@app_commands.checks.has_permissions(manage_guild=True)
async def cekilis(i, sure: str, winners: app_commands.Range[int,1,20], *, prize: str):
    seconds=human_duration(sure)
    if seconds < 10: return await i.response.send_message("Çekiliş en az 10 saniye olmalı.", ephemeral=True)
    await i.response.defer()
    end=now_ts()+seconds
    msg=await i.channel.send(embed=embed("ÇEKİLİŞ 🎉", f"**Ödül:** {prize}\n**Kazanan:** `{winners}`\n**Bitiş:** <t:{end}:R>\n\nKatılmak için 🎉 tepkisine bas!"))
    await msg.add_reaction("🎉")
    guild_data(i.guild.id)["giveaways"][str(msg.id)]={"message":msg.id,"channel":i.channel.id,"end":end,"winners":winners,"prize":prize,"ended":False}
    await persist()
    await katre_followup(i, ok("Çekiliş oluşturuldu."), ephemeral=True)

@bot.tree.command(name="anket", description="Anket oluşturur.")
async def anket(i, soru: str, secenek1: str, secenek2: str, secenek3: Optional[str] = None, secenek4: Optional[str] = None):
    opts=[x for x in [secenek1,secenek2,secenek3,secenek4] if x]
    nums=["1️⃣","2️⃣","3️⃣","4️⃣"]
    text=f"**{soru}**\n\n"+"\n".join(f"{nums[n]} {v}" for n,v in enumerate(opts))
    msg=await i.channel.send(embed=embed("Anket 📊", text))
    for n in range(len(opts)): await msg.add_reaction(nums[n])
    await i.response.send_message(ok("Anket oluşturuldu."), ephemeral=True)

@bot.tree.command(name="oneri", description="Sunucuya öneri gönderir.")
async def oneri(i, *, suggestion: str):
    cfg=guild_data(i.guild.id)
    ch=i.guild.get_channel(cfg["suggest_channel"]) if cfg["suggest_channel"] else i.channel
    msg=await ch.send(embed=embed("Yeni Öneri 💡", f"**Gönderen:** {i.user.mention}\n\n{suggestion}", discord.Color.blue()))
    await msg.add_reaction("👍"); await msg.add_reaction("👎")
    await i.response.send_message(ok("Önerin gönderildi."), ephemeral=True)

@app_commands.checks.has_permissions(manage_guild=True)
async def oneri_kanal(i, channel: Optional[discord.TextChannel] = None):
    guild_data(i.guild.id)["suggest_channel"]=channel.id if channel else None
    await persist(); await i.response.send_message(ok("Öneri kanalı güncellendi."))

# ----------------------------- NOTES / CUSTOM / TAGS -----------------------------

async def not_ekle(i, *, text: str):
    user_data(i.user.id,i.guild.id)["notes"].append({"text":text,"at":now_ts()})
    await persist(); await i.response.send_message(ok("Not kaydedildi."), ephemeral=True)

async def notlar(i):
    rows=user_data(i.user.id,i.guild.id)["notes"][-20:]
    text="\n".join(f"`{n}` <t:{x['at']}:R> — {x['text']}" for n,x in enumerate(rows,1))
    await i.response.send_message(embed=embed("Notlar",text or "Not yok."),ephemeral=True)

async def not_sil(i):
    notes=user_data(i.user.id,i.guild.id)["notes"]
    if not notes: return await i.response.send_message("Not yok.",ephemeral=True)
    notes.pop(); await persist(); await i.response.send_message(ok("Son not silindi."),ephemeral=True)

@app_commands.checks.has_permissions(manage_guild=True)
async def komut_ekle(i, name: str, response: str):
    guild_data(i.guild.id)["custom_commands"][name.lower()]={"text":response,"delete_trigger":False}
    await persist(); await i.response.send_message(ok(f"`{name}` özel komutu eklendi."))

@app_commands.checks.has_permissions(manage_guild=True)
async def komut_sil(i, name: str):
    guild_data(i.guild.id)["custom_commands"].pop(name.lower(),None)
    await persist(); await i.response.send_message(ok("Özel komut silindi."))

@app_commands.checks.has_permissions(manage_guild=True)
async def tag_ekle(i, name: str, text: str):
    guild_data(i.guild.id)["tags"][name.lower()] = text
    await persist(); await i.response.send_message(ok(f"`{name}` tag'i kaydedildi."))

async def tag(i, name: str):
    val=guild_data(i.guild.id)["tags"].get(name.lower())
    await i.response.send_message(val or "Bu tag bulunamadı.")

# ----------------------------- ROLES -----------------------------

@bot.tree.command(name="rol-ver", description="Kullanıcıya rol verir.")
@app_commands.checks.has_permissions(manage_roles=True)
async def rol_ver(i, member: discord.Member, role: discord.Role):
    if not role_targetable(i.guild, role, i.user): return await i.response.send_message("Bu rolü veremem.",ephemeral=True)
    await member.add_roles(role, reason=f"Katre • {i.user}")
    await i.response.send_message(ok(f"{member.mention} → {role.mention} verildi."))

@bot.tree.command(name="rol-al", description="Kullanıcıdan rol alır.")
@app_commands.checks.has_permissions(manage_roles=True)
async def rol_al(i, member: discord.Member, role: discord.Role):
    if not role_targetable(i.guild, role, i.user): return await i.response.send_message("Bu rolü yönetemem.",ephemeral=True)
    await member.remove_roles(role, reason=f"Katre • {i.user}")
    await i.response.send_message(ok(f"{member.mention} → {role.mention} alındı."))

@app_commands.checks.has_permissions(manage_roles=True)
async def sureli_rol(i, member: discord.Member, role: discord.Role, sure: str):
    if not role_targetable(i.guild, role, i.user): return await i.response.send_message("Bu rolü veremem.",ephemeral=True)
    seconds=human_duration(sure)
    if seconds < 1: return await i.response.send_message("Geçerli bir süre gir.",ephemeral=True)
    await member.add_roles(role, reason="Katre süreli rol")
    cfg=guild_data(i.guild.id); cfg["temp_roles"].setdefault(str(member.id),{})[str(role.id)]=now_ts()+seconds
    await persist()
    await i.response.send_message(ok(f"{member.mention} → {role.mention} **{fmt_seconds(seconds)}** verildi."))

@app_commands.checks.has_permissions(manage_guild=True)
async def levelrol(i, level: app_commands.Range[int,1,1000], role: Optional[discord.Role] = None):
    if role and not role_targetable(i.guild,role,i.user): return await i.response.send_message("Bu rolü veremem.",ephemeral=True)
    cfg=guild_data(i.guild.id)
    if role: cfg["roles_on_level"][str(level)]=role.id
    else: cfg["roles_on_level"].pop(str(level),None)
    await persist(); await i.response.send_message(ok("Seviye rolü güncellendi."))

# ----------------------------- GENİŞLETİLMİŞ SİSTEMLER -----------------------------

async def roller(i):
    roles=[f"{r.mention} — `{r.id}`" for r in reversed(i.guild.roles) if r != i.guild.default_role]
    text="\n".join(roles[:50]) or "Rol yok."
    await i.response.send_message(embed=embed("Sunucu Rolleri", text))

async def kanallar(i):
    cats={}
    for c in i.guild.channels:
        cats.setdefault(getattr(c.category,"name","Kategorisiz"),[]).append(c.mention)
    text="\n".join(f"**{k}**\n"+" • ".join(v[:20]) for k,v in cats.items())
    await i.response.send_message(embed=embed("Kanallar", text[:3900] or "Kanal yok."))

@bot.tree.command(name="rol", description="Bir üyeye rol verir veya rolünü alır.")
@app_commands.checks.has_permissions(manage_roles=True)
async def rol(i, member: discord.Member, role: discord.Role, islem: str="ver"):
    if not role_targetable(i.guild, role, i.user): return await i.response.send_message(no("Bu role işlem yapamam."), ephemeral=True)
    if islem.lower() in ("al","çıkar","cikar","remove"):
        await member.remove_roles(role, reason=f"Katre /rol • {i.user}")
        text=f"{role.mention} rolü {member.mention} kullanıcısından alındı."
    else:
        await member.add_roles(role, reason=f"Katre /rol • {i.user}")
        text=f"{role.mention} rolü {member.mention} kullanıcısına verildi."
    await persist(); await i.response.send_message(ok(text))

@app_commands.checks.has_permissions(manage_roles=True)
async def herkese_rolver(i, role: discord.Role):
    if not role_targetable(i.guild, role, i.user): return await i.response.send_message(no("Bu rolü veremem."), ephemeral=True)
    await i.response.defer()
    count=0
    for m in i.guild.members:
        if not m.bot and role not in m.roles:
            try: await m.add_roles(role, reason=f"Katre /herkese-rolver • {i.user}"); count+=1
            except: pass
    await katre_followup(i, ok(f"**{count}** üyeye {role.mention} verildi."))

@app_commands.checks.has_permissions(manage_roles=True)
async def herkesten_rolal(i, role: discord.Role):
    if not role_targetable(i.guild, role, i.user): return await i.response.send_message(no("Bu role işlem yapamam."), ephemeral=True)
    await i.response.defer(); count=0
    for m in i.guild.members:
        if role in m.roles:
            try: await m.remove_roles(role, reason=f"Katre /herkesten-rolal • {i.user}"); count+=1
            except: pass
    await katre_followup(i, ok(f"**{count}** üyeden {role.mention} alındı."))

@app_commands.checks.has_permissions(manage_nicknames=True)
async def isimdegistir(i, member: discord.Member, isim: str):
    try:
        await member.edit(nick=isim[:32], reason=f"Katre /isimdeğiştir • {i.user}")
        await i.response.send_message(ok(f"{member.mention} yeni ada sahip: **{discord.utils.escape_markdown(isim[:32])}**"))
    except discord.Forbidden:
        await i.response.send_message(no("Bu kullanıcının adını değiştiremiyorum."), ephemeral=True)

@app_commands.checks.has_permissions(manage_nicknames=True)
async def isimleri_sifirla(i):
    await i.response.defer(); count=0
    for m in i.guild.members:
        if m.nick:
            try: await m.edit(nick=None, reason=f"Katre /isimleri-sifirla • {i.user}"); count+=1
            except: pass
    await katre_followup(i, ok(f"**{count}** takma ad sıfırlandı."))

@app_commands.checks.has_permissions(manage_channels=True)
async def yavasmod(i, saniye: app_commands.Range[int,0,21600], channel: Optional[discord.TextChannel]=None):
    ch=channel or i.channel
    await ch.edit(slowmode_delay=saniye, reason=f"Katre /yavasmod • {i.user}")
    await i.response.send_message(ok(f"{ch.mention} yavaş modu **{saniye} saniye** olarak ayarlandı."))

@app_commands.checks.has_permissions(ban_members=True)
async def yasaklilar(i):
    bans=[entry async for entry in i.guild.bans(limit=100)]
    text="\n".join(f"• `{e.user.id}` — {e.user} — {e.reason or 'Sebep yok'}" for e in bans) or "Banlı kullanıcı yok."
    await i.response.send_message(embed=embed("Ban Listesi", text[:3900]))

@app_commands.checks.has_permissions(administrator=True)
async def yasaklari_temizle(i):
    await i.response.defer(); count=0
    async for entry in i.guild.bans(limit=None):
        try: await i.guild.unban(entry.user, reason=f"Katre /yasaklari-temizle • {i.user}"); count+=1
        except: pass
    await katre_followup(i, ok(f"**{count}** ban kaldırıldı."))

@app_commands.checks.has_permissions(manage_guild=True)
async def yasakli_kanal(i, durum: str, channel: Optional[discord.TextChannel]=None):
    cfg=guild_data(i.guild.id); arr=cfg.setdefault("blocked_channels",[]); cid=(channel or i.channel).id
    ac=durum.lower() in ("ac","aç","on","true","1")
    if ac and cid in arr: arr.remove(cid)
    elif not ac and cid not in arr: arr.append(cid)
    await persist(); await i.response.send_message(ok(f"{(channel or i.channel).mention} kanal ayarı güncellendi."))

@app_commands.checks.has_permissions(manage_guild=True)
async def yasakli_komut(i, komut: str, durum: str):
    cfg=guild_data(i.guild.id); arr=cfg.setdefault("blocked_commands",[]); name=komut.lower().lstrip("/")
    ac=durum.lower() in ("ac","aç","on","true","1")
    if ac and name in arr: arr.remove(name)
    elif not ac and name not in arr: arr.append(name)
    await persist(); await i.response.send_message(ok(f"`/{name}` komut ayarı güncellendi."))

@app_commands.checks.has_permissions(manage_guild=True)
async def yasakli_kelimeler(i):
    words=guild_data(i.guild.id).get("automod_badwords",[])
    await i.response.send_message(embed=embed("Yasaklı Kelimeler", "\n".join(f"• `{w}`" for w in words) or "Yok."))

@app_commands.checks.has_permissions(manage_guild=True)
async def capslock(i, durum: str):
    guild_data(i.guild.id)["automod_caps"]=durum.lower() in ("ac","aç","on","true","1")
    await persist(); await i.response.send_message(ok("Capslock koruması güncellendi."))

@app_commands.checks.has_permissions(administrator=True)
async def koruma(i, durum: str):
    cfg=guild_data(i.guild.id); cfg["anti_raid"]=durum.lower() in ("ac","aç","on","true","1")
    await persist(); await i.response.send_message(ok(f"Anti-raid koruması **{'açık' if cfg['anti_raid'] else 'kapalı'}**."))

async def dogumgunu(i, tarih: Optional[str]=None, member: Optional[discord.Member]=None):
    m=member or i.user; u=user_data(m.id,i.guild.id)
    if member and member.id!=i.user.id and tarih: return await i.response.send_message(no("Başkasının doğum gününü değiştiremezsin."),ephemeral=True)
    if tarih:
        try: datetime.strptime(tarih,"%d.%m"); u["birthday"]=tarih; await persist()
        except ValueError: return await i.response.send_message(no("Tarih biçimi `GG.AA` olmalı."),ephemeral=True)
    await i.response.send_message(embed=embed("Doğum Günü",f"{m.mention} • **{u.get('birthday','Ayarlanmadı')}**"))

@app_commands.checks.has_permissions(manage_guild=True)
async def gorevli(i, role: Optional[discord.Role]=None):
    guild_data(i.guild.id)["staff_role"]=role.id if role else None
    await persist(); await i.response.send_message(ok("Görevli rolü güncellendi."))

async def gorevliler(i):
    rid=guild_data(i.guild.id).get("staff_role")
    role=i.guild.get_role(rid) if rid else None
    members=role.members if role else [m for m in i.guild.members if m.guild_permissions.manage_guild]
    text="\n".join(f"• {m.mention}" for m in members[:50]) or "Görevli yok."
    await i.response.send_message(embed=embed("Görevliler",text))

@app_commands.checks.has_permissions(create_instant_invite=True)
async def davetlink(i, channel: Optional[discord.TextChannel]=None):
    ch=channel or i.guild.system_channel or next((c for c in i.guild.text_channels if c.permissions_for(i.guild.me).create_instant_invite),None)
    if not ch: return await i.response.send_message(no("Davet oluşturabileceğim kanal yok."),ephemeral=True)
    inv=await ch.create_invite(max_age=0,max_uses=0,reason=f"Katre /davetlink • {i.user}")
    await i.response.send_message(f"🔗 **Davet:** {inv.url}")

@app_commands.checks.has_permissions(manage_guild=True)
async def davetler(i):
    try:
        invs=await i.guild.invites()
        rows=sorted(invs,key=lambda x:x.uses or 0,reverse=True)[:20]
        text="\n".join(f"• `{x.code}` — {x.inviter.mention if x.inviter else 'Bilinmiyor'} — **{x.uses or 0}** kullanım" for x in rows) or "Davet yok."
    except discord.Forbidden: text="Davetleri okumak için gerekli yetki yok."
    await i.response.send_message(embed=embed("Davetler",text))

async def ozeloda(i, isim: str="Özel Odam"):
    overwrites={i.guild.default_role: discord.PermissionOverwrite(connect=False), i.user: discord.PermissionOverwrite(connect=True,manage_channels=True)}
    ch=await i.guild.create_voice_channel(isim[:100],overwrites=overwrites,reason=f"Katre /ozeloda • {i.user}")
    await i.response.send_message(ok(f"Özel odan oluşturuldu: {ch.mention}"))

async def oda_kapat(i):
    ch=i.user.voice.channel if i.user.voice else None
    if not ch or not ch.overwrites_for(i.user).manage_channels: return await i.response.send_message(no("Sahibi olduğun bir özel odada değilsin."),ephemeral=True)
    await ch.delete(reason=f"Katre /oda-kapat • {i.user}")

async def tkm(i, secim: str):
    choices=["taş","kağıt","makas"]; s=secim.lower(); botc=random.choice(choices)
    if s not in choices: return await i.response.send_message(no("Taş, kağıt veya makas yaz."),ephemeral=True)
    win=(s==botc) and "Berabere!" or (s,botc) in [("taş","makas"),("kağıt","taş"),("makas","kağıt")] and "Kazandın!" or "Kaybettin!"
    await i.response.send_message(embed=embed("Taş • Kağıt • Makas",f"Sen: **{s}**\nKatre: **{botc}**\n\n**{win}**"))

async def yazitura(i, tahmin: str):
    result=random.choice(["yazı","tura"]); t=tahmin.lower(); correct=t==result
    u=user_data(i.user.id,i.guild.id); amount=50 if correct else -25; u["coins"]=max(0,u["coins"]+amount); await persist()
    await i.response.send_message(embed=embed("Yazı Tura",f"Sonuç: **{result}**\n{'Kazandın' if correct else 'Kaybettin'} → **{amount:+} Coin**"))

async def zar(i, tahmin: Optional[int]=None):
    n=random.randint(1,6); text=f"🎲 Zar: **{n}**"
    if tahmin: text+=f"\nTahminin: **{tahmin}** → {'Doğru!' if tahmin==n else 'Yanlış.'}"
    await i.response.send_message(text)

async def slot(i):
    u=user_data(i.user.id,i.guild.id)
    if u["coins"]<10: return await i.response.send_message(no("Slot için en az 10 Coin gerekli."),ephemeral=True)
    u["coins"]-=10; a=[random.choice("🍒🍋🔔⭐7️⃣") for _ in range(3)]
    if a[0]==a[1]==a[2]: win=100; u["coins"]+=win
    elif len(set(a))==2: win=20; u["coins"]+=win
    else: win=0
    await persist(); await i.response.send_message(embed=embed("Slot", " | ".join(a)+f"\n\nÖdül: **{win} Coin**"))

async def terscevir(i, metin: str):
    await i.response.send_message(metin[::-1])

async def hesap(i, ifade: str):
    allowed=set("0123456789+-*/(). %")
    if len(ifade)>100 or any(c not in allowed for c in ifade): return await i.response.send_message(no("Sadece temel matematik işlemleri kullanılabilir."),ephemeral=True)
    try: result=eval(ifade,{"__builtins__":{}},{})
    except: return await i.response.send_message(no("İfade hesaplanamadı."),ephemeral=True)
    await i.response.send_message(f"🧮 `{ifade}` = **{result}**")

async def surecevir(i, saniye: app_commands.Range[int,0,999999999]):
    await i.response.send_message(f"⏱️ **{fmt_seconds(saniye)}**")

async def rastgele(i, minimum: int=1, maksimum: int=100):
    if minimum>maksimum: minimum,maksimum=maksimum,minimum
    await i.response.send_message(f"🎲 Sonuç: **{random.randint(minimum,maksimum)}**")

async def renk(i, hexkod: str):
    h=hexkod.strip().lstrip("#")
    if len(h)!=6 or any(c not in "0123456789abcdefABCDEF" for c in h): return await i.response.send_message(no("Örnek: `#5865F2`"),ephemeral=True)
    c=discord.Color(int(h,16)); await i.response.send_message(embed=embed("Renk",f"**HEX:** `#{h.upper()}`\n**RGB:** `{c.r}, {c.g}, {c.b}`",c))

async def id_cmd(i, member: Optional[discord.Member]=None, role: Optional[discord.Role]=None, channel: Optional[discord.TextChannel]=None):
    obj=member or role or channel or i.user
    await i.response.send_message(f"🔎 **{getattr(obj,'name',getattr(obj,'display_name',str(obj)))}** → `{obj.id}`")

async def metin(i, member: Optional[discord.Member]=None):
    m=member or i.user; u=user_data(m.id,i.guild.id)
    await i.response.send_message(embed=embed("Kullanıcı İstatistikleri",f"{m.mention}\nXP: **{u['xp']}**\nSeviye: **{level_for_xp(u['xp'])}**\nRep: **{u['rep']}**\nCoin: **{u['coins']}**"))

@bot.tree.command(name="profile", description="Detaylı profilini gösterir.")
async def profile(i, member: Optional[discord.Member]=None):
    m=member or i.user; u=user_data(m.id,i.guild.id)
    e=embed(f"{m.display_name} Profili",f"Seviye **{level_for_xp(u['xp'])}** • `{u['xp']} XP`\nRep **{u['rep']}** • Coin **{u['coins']:,}**\nPro: **{'Evet' if is_pro(m.id) else 'Hayır'}**")
    e.set_thumbnail(url=m.display_avatar.url); await i.response.send_message(embed=e)

async def shard(i):
    await i.response.send_message(embed=embed("Shard",f"Shard ID: `{i.guild.shard_id}`\nPing: `{round(bot.latency*1000)}ms`\nShard sayısı: `{bot.shard_count or 1}`"))

@bot.tree.command(name="support", description="Katre destek bağlantısını gösterir.")
async def support(i):
    await i.response.send_message(embed=embed("Katre Destek",SUPPORT_URL or "Destek bağlantısı henüz ayarlanmadı."))

async def music(i):
    await i.response.send_message(embed=embed("Müzik", "Katre'nin müzik altyapısı için ses kanalında olman gerekir. Bu sürümde müzik kuyruğu henüz aktif değil."))

@bot.tree.command(name="seviye", description="Seviye sistemini gösterir.")
async def seviye(i, member: Optional[discord.Member]=None):
    await rank(i,member)

@bot.tree.command(name="gorev", description="Günlük görev ve ilerleme bilgisini gösterir.")
async def gorev(i):
    u=user_data(i.user.id,i.guild.id); xp=u["xp"]%1000; coins=u["coins"]
    await i.response.send_message(embed=embed("Günlük Görev",f"XP ilerlemesi: **{xp}/1000**\nCoin bakiyesi: **{coins:,}**\n\nGörev: Sohbete katıl ve XP kazan."))

@bot.tree.command(name="kredi", description="Günlük kredi ödülü verir.")
async def kredi(i):
    await gunluk(i)

@bot.tree.command(name="magaza", description="Coin mağazasını gösterir.")
async def magaza(i):
    await i.response.send_message(embed=embed("Katre Mağaza", "🎁 **100 Coin** → Rastgele ödül\n⭐ **500 Coin** → Profil rozeti\n💎 **1000 Coin** → Özel destek mesajı\n\nMağaza altyapısı genişletilebilir."))

@bot.tree.command(name="envanter", description="Envanterini gösterir.")
async def envanter(i):
    inv=user_data(i.user.id,i.guild.id).get("inventory",[])
    await i.response.send_message(embed=embed("Envanter", "\n".join(f"• {x}" for x in inv) or "Envanter boş."))

@app_commands.checks.has_permissions(manage_guild=True)
async def istatistik_kur(i, channel: Optional[discord.TextChannel]=None):
    guild_data(i.guild.id)["stats_channel"]= (channel or i.channel).id
    await persist(); await i.response.send_message(ok("İstatistik kanalı ayarlandı."))

@app_commands.checks.has_permissions(manage_guild=True)
async def logkur(i, channel: Optional[discord.TextChannel]=None):
    guild_data(i.guild.id)["log_channel"]=(channel or i.channel).id
    await persist(); await i.response.send_message(ok("Log kanalı ayarlandı."))

@app_commands.checks.has_permissions(manage_guild=True)
async def logkaldir(i):
    guild_data(i.guild.id)["log_channel"]=None; await persist(); await i.response.send_message(ok("Log kapatıldı."))

@app_commands.checks.has_permissions(administrator=True)
async def reset(i, hedef: str):
    cfg=guild_data(i.guild.id)
    allowed={"log":"log_channel","modlog":"modlog_channel","hosgeldin":"welcome_channel","otorol":"autorole","ticket":"ticket_category","oneri":"suggest_channel"}
    key=allowed.get(hedef.lower())
    if not key: return await i.response.send_message(no("Geçerli hedef: `log`, `modlog`, `hosgeldin`, `otorol`, `ticket`, `oneri`"),ephemeral=True)
    cfg[key]=None; await persist(); await i.response.send_message(ok(f"`{hedef}` ayarı sıfırlandı."))

@app_commands.checks.has_permissions(manage_messages=True)
async def embed_cmd(i, baslik: str, mesaj: str):
    await i.response.send_message(embed=embed(baslik,mesaj))

async def say(i, member: Optional[discord.Member]=None):
    if member: text=f"{member.mention} • katılma sırası bilgisi mevcut üye sayısı: **{i.guild.member_count}**"
    else: text=f"👥 Bu sunucuda **{i.guild.member_count}** üye var."
    await i.response.send_message(text)


# ----------------------------- ROL PANELLERİ / EĞLENCE EKLERİ -----------------------------

class KatreRoleButton(discord.ui.Button):
    def __init__(self, role_id):
        super().__init__(label="Rol Al / Bırak", style=discord.ButtonStyle.primary, custom_id=f"katre:role:{role_id}")
        self.role_id=role_id
    async def callback(self, interaction: discord.Interaction):
        role=interaction.guild.get_role(self.role_id)
        if not role: return await interaction.response.send_message(no("Rol artık mevcut değil."),ephemeral=True)
        if role in interaction.user.roles:
            await interaction.user.remove_roles(role,reason="Katre buton rol")
            await interaction.response.send_message(ok(f"{role.mention} rolü alındı."),ephemeral=True)
        else:
            if role >= interaction.guild.me.top_role: return await interaction.response.send_message(no("Bu rolü veremiyorum."),ephemeral=True)
            await interaction.user.add_roles(role,reason="Katre buton rol")
            await interaction.response.send_message(ok(f"{role.mention} rolü verildi."),ephemeral=True)

class KatreRoleView(discord.ui.View):
    def __init__(self, role_id):
        super().__init__(timeout=180)
        self.add_item(KatreRoleButton(role_id))

@app_commands.checks.has_permissions(manage_roles=True)
async def butonrol(i, role: discord.Role, baslik: str="Rol Seçimi"):
    if not role_targetable(i.guild,role,i.user): return await i.response.send_message(no("Bu rolü veremem."),ephemeral=True)
    await i.response.send_message(embed=embed(baslik,f"{role.mention} rolünü almak veya bırakmak için butona bas."),view=KatreRoleView(role.id))

class KatreSelect(discord.ui.Select):
    def __init__(self, role_ids):
        opts=[]
        for rid in role_ids[:25]:
            role=None
            # guild callback içinde bulunacak; burada sadece ID taşıyoruz.
            opts.append(discord.SelectOption(label=f"Rol {rid}",value=str(rid)))
        super().__init__(placeholder="Bir rol seç...",min_values=1,max_values=1,options=opts,custom_id="katre:menu_role")
    async def callback(self, interaction: discord.Interaction):
        rid=int(self.values[0]); role=interaction.guild.get_role(rid)
        if not role: return await interaction.response.send_message(no("Rol bulunamadı."),ephemeral=True)
        if role in interaction.user.roles:
            await interaction.user.remove_roles(role,reason="Katre menü rol")
            text=f"{role.mention} rolü alındı."
        else:
            if role >= interaction.guild.me.top_role: return await interaction.response.send_message(no("Bu rolü veremiyorum."),ephemeral=True)
            await interaction.user.add_roles(role,reason="Katre menü rol")
            text=f"{role.mention} rolü verildi."
        await interaction.response.send_message(ok(text),ephemeral=True)

class KatreMenuView(discord.ui.View):
    def __init__(self, role_ids):
        super().__init__(timeout=180); self.add_item(KatreSelect(role_ids))

@app_commands.checks.has_permissions(manage_roles=True)
async def menurol(i, rol1: discord.Role, rol2: Optional[discord.Role]=None, rol3: Optional[discord.Role]=None, rol4: Optional[discord.Role]=None, rol5: Optional[discord.Role]=None):
    roles=[r for r in [rol1,rol2,rol3,rol4,rol5] if r]
    if any(not role_targetable(i.guild,r,i.user) for r in roles): return await i.response.send_message(no("Rollerden biri yönetilebilir değil."),ephemeral=True)
    e=embed("Rol Menüsü","Aşağıdaki menüden rolünü seçebilirsin.\n\n"+"\n".join(f"• {r.mention}" for r in roles))
    await i.response.send_message(embed=e,view=KatreMenuView([r.id for r in roles]))

@app_commands.checks.has_permissions(manage_messages=True)
async def konustur(i, metin: str):
    await i.response.send_message(ok("Mesaj gönderildi."),ephemeral=True); await i.channel.send(metin)

async def tweet(i, metin: str):
    await i.response.send_message(embed=embed("𝕏 Tweet",f"**{i.user.display_name}**\n\n{metin}"))

async def pankart(i, metin: str):
    await i.response.send_message(f"╔════════════════════╗\n║  **{discord.utils.escape_markdown(metin[:50])}**  ║\n╚════════════════════╝")

async def clyde(i, metin: str):
    await i.response.send_message(embed=embed("Clyde",f"**{i.user.display_name}** adlı kullanıcı için sahte mesaj:\n\n> {metin}"))

async def pet(i, isim: Optional[str]=None):
    u=user_data(i.user.id,i.guild.id); p=u.get("pet")
    if isim:
        u["pet"]={"name":isim[:24],"level":1}; await persist(); p=u["pet"]
    if not p: return await i.response.send_message("🐾 Henüz petin yok. `/pet isim:Kedi` ile sahiplen.")
    await i.response.send_message(embed=embed("Pet",f"🐾 **{p['name']}**\nSeviye: **{p['level']}**"))

async def ciftlik(i):
    u=user_data(i.user.id,i.guild.id); farm=u.setdefault("farm",{"level":1,"wheat":0})
    farm["wheat"]+=1; await persist()
    await i.response.send_message(embed=embed("Çiftlik",f"🌾 Çiftlik seviyesi: **{farm['level']}**\nBu işlemle buğday: **{farm['wheat']}**"))

async def mayintarlasi(i, secim: Optional[int]=None):
    mine=random.randint(1,25); pick=secim or random.randint(1,25)
    if pick<1 or pick>25: return await i.response.send_message(no("1-25 arasında seçim yap."),ephemeral=True)
    await i.response.send_message(embed=embed("Mayın Tarlası",f"Seçimin: **{pick}**\n{'💥 Mayına bastın!' if pick==mine else '🟩 Güvenli!'}"))

async def adamasmaca(i, harf: str):
    word=random.choice(["discord","katre","sunucu","bot","merhaba"]); h=harf.lower()[:1]
    mask=" ".join(c if c==h else "_" for c in word)
    await i.response.send_message(embed=embed("Adam Asmaca",f"Kelime: `{mask}`\nİpucu: **{len(word)} harf**"))

async def kelimebulmaca(i, tahmin: str):
    word=random.choice(["katre","discord","botcu","sunucu"]); t=tahmin.lower()
    if len(t)!=len(word): return await i.response.send_message(no(f"Kelime **{len(word)} harf** olmalı."),ephemeral=True)
    out=" ".join("🟩" if a==b else ("🟨" if a in word else "⬛") for a,b in zip(t,word))
    await i.response.send_message(embed=embed("Kelime Bulmaca",f"Tahmin: `{t}`\n{out}"))

async def xox(i):
    board=["⬜"]*9
    await i.response.send_message(embed=embed("XOX", " | ".join(board[:3])+"\n"+" | ".join(board[3:6])+"\n"+" | ".join(board[6:])))

async def sudoku(i):
    await i.response.send_message(embed=embed("Sudoku","Katre Sudoku mini oyunu: kolay / orta / zor seviyeleri için oyun altyapısı hazırlandı; bu sürümde çözüm paneli yerine mini oyun bilgilendirmesi gösterilir."))

async def qr(i, metin: str):
    from urllib.parse import quote
    url=f"https://api.qrserver.com/v1/create-qr-code/?size=300x300&data={quote(metin)}"
    await i.response.send_message(embed=embed("QR Kod",f"[QR görselini aç]({url})"))

async def bugun(i):
    await i.response.send_message(f"📅 Bugün: **{datetime.now().strftime('%d.%m.%Y')}**")

async def goal(i):
    hedef=guild_data(i.guild.id).get("member_goal",1000)
    await i.response.send_message(embed=embed("Üye Hedefi",f"Mevcut: **{i.guild.member_count}**\nHedef: **{hedef}**\nİlerleme: **{min(100,i.guild.member_count/hesdef*100 if (hesdef:=hedef) else 0):.1f}%**"))


# ----------------------------- REMINDER -----------------------------

@bot.tree.command(name="hatirlat", description="Belirtilen sürede hatırlatıcı kurar.")
async def hatirlat(i, sure: str, *, text: str):
    seconds=human_duration(sure)
    if seconds < 5: return await i.response.send_message("En az 5 saniye.",ephemeral=True)
    DB.setdefault("reminders",[]).append({"user":i.user.id,"channel":i.channel.id,"at":now_ts()+seconds,"text":text})
    await persist(); await i.response.send_message(ok(f"**{fmt_seconds(seconds)}** sonra hatırlatacağım."))

# ----------------------------- OWNER -----------------------------

@bot.tree.command(name="owner", description="Owner: butonlu sahip panelini açar.")
async def owner(i):
    if not is_owner(i.user):
        return  # Kesinlikle uyarı yok.
    view = OwnerPanelWithHome()
    view.build_buttons()
    e = embed("Katre Owner Merkezi", f"{E('owner')} Sahip paneli hazır. Bir kategori seç.", discord.Color.gold())
    await i.response.send_message(embed=e, view=view, ephemeral=True)

@bot.tree.command(name="blacklist", description="Owner: kullanıcıyı blacklist'e ekler/çıkarır.")
async def blacklist(i, member: discord.User):
    if not is_owner(i.user): return await i.response.send_message("Owner komutu.",ephemeral=True)
    arr=DB["global"]["blacklist"]
    if member.id in arr: arr.remove(member.id); text="çıkarıldı"
    else: arr.append(member.id); text="eklendi"
    await persist(); await i.response.send_message(ok(f"{member} blacklist'ten {text}."),ephemeral=True)

@bot.tree.command(name="maintenance", description="Owner: global bakım modunu açar/kapatır.")
async def maintenance(i, durum: str):
    if not is_owner(i.user): return await i.response.send_message("Owner komutu.",ephemeral=True)
    DB["global"]["maintenance"]=durum.lower() in ("aç","ac","on","true","1")
    await persist(); await i.response.send_message(ok("Bakım modu güncellendi."),ephemeral=True)

@bot.tree.command(name="sunucu-listesi", description="Owner: botun bulunduğu sunucuları listeler.")
async def sunucu_listesi(i):
    if not is_owner(i.user): return await i.response.send_message("Owner komutu.",ephemeral=True)
    rows=[f"`{g.id}` • **{discord.utils.escape_markdown(g.name)}** • `{g.member_count}` üye" for g in bot.guilds]
    text="\n".join(rows[:50])
    await i.response.send_message(embed=embed("Sunucular",text or "Yok."),ephemeral=True)

@bot.tree.command(name="duyuru", description="Owner: botun bulunduğu sunuculara duyuru yollar.")
async def duyuru(i, *, text: str):
    if not is_owner(i.user): return await i.response.send_message("Owner komutu.",ephemeral=True)
    await i.response.defer(ephemeral=True)
    sent=0
    for g in bot.guilds:
        ch=next((c for c in g.text_channels if c.permissions_for(g.me).send_messages),None)
        if ch:
            try: await ch.send(embed=embed("Katre Duyuru",text)); sent+=1
            except: pass
        await asyncio.sleep(.4)
    await i.followup.send(ok(f"{sent} sunucuya gönderildi."),ephemeral=True)


# ----------------------------- OWNER PANEL / EMOJI CONTROL -----------------------------

OWNER_CATEGORIES = {
    "pro": ("💎 Pro", [
        "`/pro-ver` — süreli/süresiz Pro ver",
        "`/pro-al` — Pro kaldır",
        "`/pro-liste` — Pro kullanıcıları",
    ]),
    "reklam": ("📢 Reklam", [
        "`/reklam-sunucu` — reklam sunucusu",
        "`/reklam` — genel şartı aç/kapat",
        "`/reklam-komut` — komut bazlı şart",
        "`/reklam-mesaj` — katılım mesajı",
    ]),
    "bot": ("🤖 Bot", [
        "`k!pp-ayarla` — Katre profil görselini uygula",
        "`k!duyuru` — tüm sunuculara duyuru",
        "`/sunucu-listesi` — sunucu listesi",
        "`/maintenance` — bakım modu",
        "`/blacklist` — global blacklist",
    ]),
    "emojiler": ("🎨 Emojiler", [
        "`k!emoji liste` — tüm emoji anahtarları",
        "`k!emoji ayarla <anahtar> <emoji>` — emoji değiştir",
        "`k!emoji sıfırla` — varsayılanlara dön",
    ]),
    "yardim": ("📚 Yardım", [
        "`/yardim` — normal kullanıcı yardım menüsü",
        "`k!sahip` — yalnızca owner paneli",
    ]),
}

class OwnerPanel(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=180)
        self.message = None

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        # Owner panelindeki butonları da yalnızca owner kullanabilir.
        if not is_owner(interaction.user):
            return False
        return True

    def clear_dynamic(self):
        for item in list(self.children):
            self.remove_item(item)

    def build_buttons(self):
        self.clear_dynamic()
        for key, (label, _) in OWNER_CATEGORIES.items():
            self.add_item(OwnerCategoryButton(key, label))

class OwnerCategoryButton(discord.ui.Button):
    def __init__(self, key, label):
        super().__init__(label=label, style=discord.ButtonStyle.secondary, custom_id=f"katre_owner_{key}")
        self.key = key

    async def callback(self, interaction: discord.Interaction):
        if not is_owner(interaction.user):
            return  # Sessiz.
        title, lines = OWNER_CATEGORIES[self.key]
        desc = "\n".join(lines)
        e = embed(f"Katre Owner • {title}", desc, discord.Color.gold())
        e.set_footer(text="Bu menü yalnızca Katre owner'larına görünür/kullanılabilir.")
        await interaction.response.edit_message(embed=e, view=self.view)

class OwnerHomeButton(discord.ui.Button):
    def __init__(self):
        super().__init__(label="Ana Menü", style=discord.ButtonStyle.primary, emoji=E("home"))
    async def callback(self, interaction: discord.Interaction):
        if not is_owner(interaction.user):
            return
        self.view.build_buttons()
        e = embed("Katre Owner Merkezi", "Bir kategori seç.\n\n" +
                  f"{E('owner')} **Sahip:** <@{interaction.user.id}>\n"
                  f"{E('bot')} **Sürüm:** {VERSION}\n"
                  f"{E('server')} **Sunucu:** {len(bot.guilds)}\n"
                  f"{E('pro')} **Aktif Pro:** {sum(1 for uid in DB['global']['pro_users'] if is_pro(int(uid)))}",
                  discord.Color.gold())
        await interaction.response.edit_message(embed=e, view=self.view)

class OwnerPanelWithHome(OwnerPanel):
    def build_buttons(self):
        super().build_buttons()
        self.add_item(OwnerHomeButton())

@bot.command(name="sahip")
async def sahip(ctx):
    # KRİTİK: Owner olmayan kişi için hiçbir çıktı yok.
    if not is_owner(ctx.author):
        return

    # Komutu kanalda bırakmak istemiyorsan silinir; başarısızsa sessizce devam eder.
    try:
        await ctx.message.delete()
    except Exception:
        pass

    view = OwnerPanelWithHome()
    view.build_buttons()
    e = embed(
        "Katre Owner Merkezi",
        f"{E('owner')} **Sahip:** {ctx.author.mention}\n"
        f"{E('bot')} **Sürüm:** `{VERSION}`\n"
        f"{E('server')} **Sunucu:** `{len(bot.guilds)}`\n"
        f"{E('user')} **Kullanıcı:** `{sum(g.member_count or 0 for g in bot.guilds):,}`\n\n"
        "Aşağıdaki kategorilerden birini seç.",
        discord.Color.gold()
    )
    e.set_footer(text="Katre • Owner Control Center")
    await ctx.send(embed=e, view=view)

@bot.command(name="emoji")
async def emoji_command(ctx, action: str = "liste", key: str = None, *, value: str = None):
    # Emoji sistemi globaldir ve sadece bot owner yönetebilir.
    if not is_owner(ctx.author):
        return

    action = action.lower()
    if action in ("liste", "list"):
        lines = []
        for k in sorted(EMOJI_DEFAULTS):
            lines.append(f"`{k}` → {E(k)}")
        e = embed("Katre Emoji Merkezi", "\n".join(lines), discord.Color.blurple())
        e.set_footer(text="Değiştirmek: k!emoji ayarla <anahtar> <emoji>")
        return await ctx.send(embed=e)

    if action in ("ayarla", "set"):
        if not key or not value:
            return await ctx.send(f"{E('warn')} Kullanım: `k!emoji ayarla <anahtar> <emoji>`")
        key = key.lower()
        if key not in EMOJI_DEFAULTS:
            return await ctx.send(f"{E('no')} Geçersiz anahtar. `k!emoji liste` yaz.")
        DB["global"]["emojis"][key] = value.strip()
        await persist()
        return await ctx.send(embed=embed("Emoji Güncellendi",
            f"{E('ok')} `{key}` artık **{value.strip()}** kullanıyor.", discord.Color.green()))

    if action in ("sıfırla", "sifirla", "reset"):
        DB["global"]["emojis"] = dict(EMOJI_DEFAULTS)
        await persist()
        return await ctx.send(embed=embed("Emojiler Sıfırlandı",
            f"{E('ok')} Tüm emojiler varsayılan değerlerine döndü.", discord.Color.green()))

    await ctx.send(f"{E('info')} Kullanım: `k!emoji liste` • `k!emoji ayarla <anahtar> <emoji>` • `k!emoji sıfırla`")


@bot.command(name="pp-ayarla")
async def pp_ayarla(ctx):
    """Owner: paketteki Katre PP'sini Discord bot avatarı olarak uygular."""
    if not is_owner(ctx.author):
        return
    if not os.path.isfile(KATRE_AVATAR_PATH):
        return await ctx.send(embed=embed("Katre PP", "Profil görseli pakette bulunamadı.", discord.Color.red()))
    try:
        with open(KATRE_AVATAR_PATH, "rb") as fp:
            await bot.user.edit(avatar=fp.read(), reason=f"Owner tarafından Katre PP güncellendi: {ctx.author}")
        await ctx.send(embed=embed("Katre PP Güncellendi", "Katre'nin profil görseli başarıyla uygulandı.", discord.Color.green()))
    except discord.HTTPException as exc:
        await ctx.send(embed=embed("Katre PP", f"Discord avatar güncellemesini kabul etmedi: `{exc}`", discord.Color.orange()))


# ----------------------------- PREFIX COMMAND REGISTRY -----------------------------
# Slash sayısı düşük tutulur; diğer komutlar k! ile kullanılmaya devam eder.
PREFIX_ONLY_COMMANDS = {
    'prefix': globals()['prefix'],
    'log': globals()['log_cmd'],
    'modlog': globals()['modlog'],
    'hosgeldin': globals()['hosgeldin'],
    'otorol': globals()['otorol'],
    'reklam-sunucu': globals()['reklam_sunucu'],
    'reklam': globals()['reklam'],
    'reklam-komut': globals()['reklam_komut'],
    'reklam-mesaj': globals()['reklam_mesaj'],
    'pro-ver': globals()['pro_ver'],
    'pro-al': globals()['pro_al'],
    'emoji': globals()['emoji_slash'],
    'pp-ayarla': globals()['pp_ayarla'],
    'oneri-kanal': globals()['oneri_kanal'],
    'not-ekle': globals()['not_ekle'],
    'notlar': globals()['notlar'],
    'not-sil': globals()['not_sil'],
    'komut-ekle': globals()['komut_ekle'],
    'komut-sil': globals()['komut_sil'],
    'tag-ekle': globals()['tag_ekle'],
    'tag': globals()['tag'],
    'süreli-rol': globals()['sureli_rol'],
    'levelrol': globals()['levelrol'],
    'roller': globals()['roller'],
    'kanallar': globals()['kanallar'],
    'herkese-rolver': globals()['herkese_rolver'],
    'herkesten-rolal': globals()['herkesten_rolal'],
    'isimdeğiştir': globals()['isimdegistir'],
    'isimleri-sifirla': globals()['isimleri_sifirla'],
    'yavasmod': globals()['yavasmod'],
    'yasaklilar': globals()['yasaklilar'],
    'yasaklari-temizle': globals()['yasaklari_temizle'],
    'yasakli-kanal': globals()['yasakli_kanal'],
    'yasakli-komut': globals()['yasakli_komut'],
    'yasakli-kelimeler': globals()['yasakli_kelimeler'],
    'capslock': globals()['capslock'],
    'koruma': globals()['koruma'],
    'dogumgunu': globals()['dogumgunu'],
    'gorevli': globals()['gorevli'],
    'gorevliler': globals()['gorevliler'],
    'davetlink': globals()['davetlink'],
    'davetler': globals()['davetler'],
    'ozeloda': globals()['ozeloda'],
    'oda-kapat': globals()['oda_kapat'],
    'tkm': globals()['tkm'],
    'yazitura': globals()['yazitura'],
    'zar': globals()['zar'],
    'slot': globals()['slot'],
    'terscevir': globals()['terscevir'],
    'hesap': globals()['hesap'],
    'surecevir': globals()['surecevir'],
    'rastgele': globals()['rastgele'],
    'renk': globals()['renk'],
    'id': globals()['id_cmd'],
    'metin': globals()['metin'],
    'shard': globals()['shard'],
    'music': globals()['music'],
    'istatistik-kur': globals()['istatistik_kur'],
    'logkur': globals()['logkur'],
    'logkaldir': globals()['logkaldir'],
    'reset': globals()['reset'],
    'embed': globals()['embed_cmd'],
    'say': globals()['say'],
    'butonrol': globals()['butonrol'],
    'menurol': globals()['menurol'],
    'konustur': globals()['konustur'],
    'tweet': globals()['tweet'],
    'pankart': globals()['pankart'],
    'clyde': globals()['clyde'],
    'pet': globals()['pet'],
    'ciftlik': globals()['ciftlik'],
    'mayintarlasi': globals()['mayintarlasi'],
    'adamasmaca': globals()['adamasmaca'],
    'kelimebulmaca': globals()['kelimebulmaca'],
    'xox': globals()['xox'],
    'sudoku': globals()['sudoku'],
    'qr': globals()['qr'],
    'bugun': globals()['bugun'],
    'goal': globals()['goal'],
}

# Slash komutlarındaki Discord yetkilerini k! köprüsüne de uygularız.
PREFIX_PERMISSION_REQUIREMENTS = {
    'ban': ('ban_members',),
    'unban': ('ban_members',),
    'kick': ('kick_members',),
    'timeout': ('moderate_members',),
    'untimeout': ('moderate_members',),
    'sil': ('manage_messages',),
    'kilit': ('manage_channels',),
    'uyar': ('moderate_members',),
    'uyarilar': ('moderate_members',),
    'prefix': ('manage_guild',),
    'log': ('manage_guild',),
    'modlog': ('manage_guild',),
    'hosgeldin': ('manage_guild',),
    'otorol': ('manage_roles',),
    'ayarlar': ('manage_guild',),
    'otomod': ('manage_guild',),
    'otomod-link': ('manage_guild',),
    'otomod-davet': ('manage_guild',),
    'yasakli-kelime': ('manage_guild',),
    'ticket-panel': ('manage_guild',),
    'ticket-ayarla': ('manage_guild',),
    'cekilis': ('manage_guild',),
    'oneri-kanal': ('manage_guild',),
    'komut-ekle': ('manage_guild',),
    'komut-sil': ('manage_guild',),
    'tag-ekle': ('manage_guild',),
    'rol-ver': ('manage_roles',),
    'rol-al': ('manage_roles',),
    'süreli-rol': ('manage_roles',),
    'levelrol': ('manage_guild',),
    'rol': ('manage_roles',),
    'herkese-rolver': ('manage_roles',),
    'herkesten-rolal': ('manage_roles',),
    'isimdeğiştir': ('manage_nicknames',),
    'isimleri-sifirla': ('manage_nicknames',),
    'yavasmod': ('manage_channels',),
    'yasaklilar': ('ban_members',),
    'yasaklari-temizle': ('administrator',),
    'yasakli-kanal': ('manage_guild',),
    'yasakli-komut': ('manage_guild',),
    'yasakli-kelimeler': ('manage_guild',),
    'capslock': ('manage_guild',),
    'koruma': ('administrator',),
    'gorevli': ('manage_guild',),
    'davetlink': ('create_instant_invite',),
    'davetler': ('manage_guild',),
    'istatistik-kur': ('manage_guild',),
    'logkur': ('manage_guild',),
    'logkaldir': ('manage_guild',),
    'reset': ('administrator',),
    'embed': ('manage_messages',),
    'butonrol': ('manage_roles',),
    'menurol': ('manage_roles',),
    'konustur': ('manage_messages',),
}

# ----------------------------- PREFIX QUICK COMMANDS -----------------------------

@bot.command(name="ping")
async def prefix_ping(ctx):
    await ctx.send(f"🏓 `{round(bot.latency*1000)}ms`")

@bot.command(name="yardim")
async def prefix_help(ctx):
    await send_help(ctx, ctx.author.id)

# ----------------------------- PREFIX CHECKS -----------------------------

@bot.event
async def on_interaction(interaction: discord.Interaction):
    # Bakım modu yalnızca owner dışındaki application command'ları engeller.
    if interaction.type == discord.InteractionType.application_command and DB["global"].get("maintenance"):
        if not is_owner(interaction.user):
            # Slash komut callback'i henüz çalışmadan müdahale etmek discord.py event akışında güvenilir değildir.
            # Bu nedenle bilgi amaçlı tutulur; gerçek bakım kontrolü kritik komutlara eklenebilir.
            pass

# ----------------------------- ERROR HANDLER FOR APP COMMANDS -----------------------------

@bot.tree.error
async def on_app_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    if interaction.response.is_done():
        sender = interaction.followup.send
    else:
        sender = interaction.response.send_message

    if isinstance(error, app_commands.MissingPermissions):
        await sender(embed=embed("Yetki Yetersiz","Bu komut için gerekli Discord yetkisine sahip değilsin.",discord.Color.red()),ephemeral=True)
    elif isinstance(error, app_commands.CommandOnCooldown):
        await sender(f"⏳ Tekrar denemek için `{error.retry_after:.1f}` saniye bekle.",ephemeral=True)
    else:
        log.exception("Slash command error", exc_info=error)
        try: await sender(embed=embed("Bir Hata Oluştu","İşlem tamamlanamadı. Bot loglarında hata kaydedildi.",discord.Color.red()),ephemeral=True)
        except: pass

# ----------------------------- RAILWAY HEALTH -----------------------------

async def health_handler(request):
    return web.json_response({
        "name": APP_NAME, "version": VERSION, "status": "online",
        "guilds": len(bot.guilds), "latency_ms": round(bot.latency*1000),
        "uptime": int(time.time()-START)
    })

async def run_health_server():
    if not web: return
    port=int(os.getenv("PORT","8080"))
    app=web.Application()
    app.router.add_get("/",health_handler)
    app.router.add_get("/health",health_handler)
    runner=web.AppRunner(app)
    await runner.setup()
    site=web.TCPSite(runner,"0.0.0.0",port)
    await site.start()
    log.info("Health server :%s",port)

async def main():
    await run_health_server()
    await bot.start(TOKEN)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
