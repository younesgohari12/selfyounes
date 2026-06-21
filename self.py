# self.py
import os
import re
import asyncio
import json
import random
import time
from datetime import datetime
from telethon import TelegramClient, events, errors, Button
from telethon.sessions import StringSession
from telethon.tl.functions.account import UpdateProfileRequest
from telethon.tl.functions.channels import JoinChannelRequest
from telethon.tl.functions.messages import ImportChatInviteRequest
from config import (
    API_ID, API_HASH, UPDATE_INTERVAL,
    CLOCK_FORMATS, FONT_NAMES, SESSIONS_DIR,
    INLINE_USERNAME, get_tehran_time, get_tehran_datetime
)
from commands_db import (
    get_session_data, get_clock_settings, update_clock_settings,
    get_enemies, update_enemies, get_silences, update_silences,
    init_session, get_ads_settings, update_ads_settings,
    delete_ads_banner, reset_ads_stats, increment_ads_stats
)

METADATA_FILE = os.path.join(SESSIONS_DIR, 'metadata.json')
SELF_DATA_FILE = os.path.join(SESSIONS_DIR, 'self_data.json')
PENDING_FILE = os.path.join(SESSIONS_DIR, 'pending_sessions.json')

running_sessions = {}
session_locks = {}

PATTERN_PING = re.compile(r'^\.(ping|پینگ)$', re.IGNORECASE)
PATTERN_SPAM = re.compile(r'^\.(اسپم|spam)\s+(\d+)\s+(.+)$', re.IGNORECASE)
PATTERN_DELETE = re.compile(r'^\.(حذف پیام|del|delete)\s+(\d+)$', re.IGNORECASE)
PATTERN_ENEMY = re.compile(r'^\.(دشمن|enemy)\s*(.*)?$', re.IGNORECASE)
PATTERN_UNENEMY = re.compile(r'^\.(حذف دشمن|unenemy)\s*(.*)?$', re.IGNORECASE)
PATTERN_LIST_ENEMIES = re.compile(r'^\.(لیست دشمن|listenemy|list_enemies)$', re.IGNORECASE)
PATTERN_SILENCE = re.compile(r'^\.(سکوت|silence)\s*(.*)?$', re.IGNORECASE)
PATTERN_UNSILENCE = re.compile(r'^\.(حذف سکوت|unsilence)\s*(.*)?$', re.IGNORECASE)
PATTERN_LIST_SILENCES = re.compile(r'^\.(لیست سکوت|listsilence|list_silence)$', re.IGNORECASE)
PATTERN_INFO = re.compile(r'^\.(info|اطلاعات)$', re.IGNORECASE)
PATTERN_PANEL = re.compile(r'^\.(panel|پنل)$', re.IGNORECASE)

SWEAR_WORDS = [
    "مادرتو گاییدم 🤬", "ننتو گاییدم کسکش", "خواهرتو گاییدم بی‌شرف",
    "مادرت جنده بود کسخل", "ننت هرزه بود که تو به دنیا اومدی",
    "پدرت دوثوله بود که تو شدی اینجوری", "مادرت رو تو قبر گاییدم",
    "ننت رو ۱۰۰ نفر گاییدن", "خواهرت فاحشه بود", "خانواده‌تون همه جنده‌ان",
    "پدرت بی‌غیرت بود", "ننت رو تو خیابون گاییدن", "مادرت مال همه بود",
    "تو حرومزاده‌ای", "پدرت معلوم نیست کیه", "ننت روسپی بود",
    "تو بچه حرومی", "خواهرت رو گاییدم", "ننت رو گاییدم سگ",
    "مادرت شاش‌خور بود", "پدرت دوثوله‌ترین بود", "ننت رو تو حموم گاییدم",
    "تو کسخل مادر جنده", "مادرت فاحشه خیابونی بود", "ننت با همه می‌پرید",
    "خواهرت جنده بود", "تو بچه صیغه‌ای", "پدرت بی‌پدر بود",
    "ننت رو اسب گایید", "مادرت شاش خودتو می‌خورد", "تو کونی مادر جنده",
    "ننت رو تو توالت گاییدم", "خواهرت فاحشه خونه بود", "پدرت بی‌عرضه بود",
    "ننت هرزگی می‌کرد", "مادرت تو کوچه گاییده شد", "تو حرومزاده کسکش",
    "ننت با سگ می‌پرید", "خواهرت رو ۱۰ نفر گاییدن", "مادرت تو حمام عمومی بود",
    "پدرت معلوم‌الحال بود", "ننت رو گاییدم بی‌پدر", "تو بچه نامشروع",
    "خواهرت فاحشه درجه یک بود", "ننت با اسب می‌پرید", "مادرت جنده محله بود",
    "تو کونی سگ‌صفت", "ننت رو تو زندان گاییدن", "پدرت بی‌شرف‌ترین بود",
    "خانواده‌تون همه فاحشه‌ان", "مادرتو تو گور گاییدم", "خواهرتو گاییدم کسکش",
]

def load_self_data():
    if os.path.exists(SELF_DATA_FILE):
        try:
            with open(SELF_DATA_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except: pass
    return {'ads': {}, 'users': {}}

def save_self_data(data):
    try:
        with open(SELF_DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except: pass

async def resolve_user(client, identifier):
    if not identifier: return None
    identifier = identifier.strip()
    if identifier.startswith('@'): identifier = identifier[1:]
    try:
        if identifier.isdigit(): return await client.get_entity(int(identifier))
        return await client.get_entity(identifier)
    except: return None

def get_user_info(entity):
    if not entity: return None
    name = getattr(entity, 'first_name', '') or ''
    if getattr(entity, 'last_name', None): name += f" {entity.last_name}"
    return {'name': name.strip(), 'username': getattr(entity, 'username', None), 'id': getattr(entity, 'id', None)}

pending_channel_joins = {}

async def join_from_inline_button(client, event):
    if not event.message.reply_markup:
        return False
    for row in event.message.reply_markup.rows:
        for btn in row.buttons:
            if hasattr(btn, 'url') and ('t.me/' in btn.url or 'telegram.me/' in btn.url):
                url = btn.url
                try:
                    entity = await client.get_entity(url)
                    await client(JoinChannelRequest(entity))
                    return True
                except:
                    return False
    return False

def load_pending():
    if not os.path.exists(PENDING_FILE):
        return []
    try:
        with open(PENDING_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, list):
            return data
    except:
        return []

def remove_pending(session_name):
    try:
        pending = load_pending()
        if session_name in pending:
            pending.remove(session_name)
            with open(PENDING_FILE, "w", encoding="utf-8") as f:
                json.dump(pending, f, ensure_ascii=False, indent=2)
    except:
        pass

def get_session_string(session_name):
    txt_file = os.path.join(SESSIONS_DIR, f"{session_name}.txt")
    if os.path.exists(txt_file):
        try:
            with open(txt_file, 'r', encoding='utf-8') as f:
                return f.read().strip()
        except:
            pass
    return None

async def pending_watcher():
    print("👀 pending_watcher شروع به کار کرد")
    
    while True:
        try:
            pending = load_pending()
            
            try:
                from login_manager import login_states
            except:
                login_states = {}
            
            for session_name in pending:
                if session_name in running_sessions:
                    continue
                
                try:
                    uid = int(session_name.replace('user_', ''))
                    if uid in login_states:
                        continue
                except ValueError:
                    pass
                
                session_path = os.path.join(SESSIONS_DIR, session_name)
                
                txt_file = session_path + '.txt'
                session_file = session_path + '.session'
                
                if not os.path.exists(txt_file) and not os.path.exists(session_file):
                    remove_pending(session_name)
                    continue
                
                print(f"🚀 اجرای خودکار سشن جدید: {session_name}")
                
                session_string = get_session_string(session_name)
                if not session_string:
                    from self_manager import migrate_old_session
                    session_string = await migrate_old_session(session_name)
                
                if not session_string:
                    remove_pending(session_name)
                    continue
                
                task = asyncio.create_task(run_self(session_path, session_string))
                running_sessions[session_name] = task
                
                remove_pending(session_name)
        
        except asyncio.CancelledError:
            break
        except Exception as e:
            print(f"❌ خطا در pending_watcher: {e}")
        
        await asyncio.sleep(5)

async def clock_updater(client, session_name, sid):
    last_bio_time = None
    last_ln_time = None
    last_state = None
    
    while True:
        try:
            settings = get_clock_settings(session_name)
            
            enabled = settings.get("enabled", False)
            bio_clock = settings.get("bio_clock", False)
            lastname_clock = settings.get("lastname_clock", False)
            font = settings.get("font", 1)
            base_first = settings.get("base_first_name", "")
            base_last = settings.get("base_last_name", "")
            base_bio = settings.get("base_bio", "")
            
            if not base_first:
                try:
                    me = await client.get_me()
                    base_first = me.first_name or ""
                    base_last = me.last_name or ""
                    update_clock_settings(session_name,
                        base_first_name=base_first,
                        base_last_name=base_last
                    )
                    print(f"📝 base names ذخیره شد: {base_first} | {base_last}")
                except Exception as e:
                    print(f"⚠️ خطا در گرفتن base: {e}")
            
            if not base_bio:
                try:
                    from telethon.tl.functions.users import GetFullUserRequest
                    me = await client.get_me()
                    full = await client(GetFullUserRequest(me))
                    if hasattr(full, 'full_user') and hasattr(full.full_user, 'about'):
                        base_bio = full.full_user.about or ""
                        update_clock_settings(session_name, base_bio=base_bio)
                except:
                    pass
            
            now = get_tehran_datetime()
            time_str = now.strftime("%H:%M")
            
            if enabled and (bio_clock or lastname_clock):
                if font in CLOCK_FORMATS:
                    formatted = CLOCK_FORMATS[font]("", time_str).strip()
                else:
                    formatted = time_str
                
                should_update = False
                if bio_clock and formatted != last_bio_time:
                    should_update = True
                if lastname_clock and formatted != last_ln_time:
                    should_update = True
                
                if should_update:
                    try:
                        new_first = base_first[:64] if base_first else None
                        new_last = formatted[:64] if lastname_clock else (base_last[:64] if base_last else None)
                        new_about = formatted[:70] if bio_clock else (base_bio[:70] if base_bio else None)
                        
                        await client(UpdateProfileRequest(
                            first_name=new_first,
                            last_name=new_last,
                            about=new_about
                        ))
                        
                        if bio_clock: last_bio_time = formatted
                        if lastname_clock: last_ln_time = formatted
                        
                        print(f"🔄 {sid}: ✅ ساعت آپدیت شد | 📝 {new_about or '-'} | 👤 {new_last or '-'}")
                    except errors.FloodWaitError as e:
                        print(f"⏳ Flood wait: {e.seconds}s")
                        await asyncio.sleep(e.seconds)
                    except Exception as e:
                        print(f"⚠️ خطای UpdateProfile: {e}")
            
            elif not enabled and last_state == True:
                try:
                    await client(UpdateProfileRequest(
                        first_name=base_first[:64] if base_first else None,
                        last_name=base_last[:64] if base_last else None,
                        about=base_bio[:70] if base_bio else None
                    ))
                    print(f"🔄 {sid}: 🔴 ساعت خاموش شد - برگشت به مقادیر اصلی")
                    last_bio_time = None
                    last_ln_time = None
                except Exception as e:
                    print(f"⚠️ خطا در بازگشت به base: {e}")
            
            last_state = enabled
            await asyncio.sleep(UPDATE_INTERVAL)
        
        except asyncio.CancelledError:
            break
        except Exception as e:
            print(f"⚠️ خطای کلی clock_updater: {e}")
            await asyncio.sleep(60)

async def advertiser(client, session_name, sid):
    CHECK_INTERVAL = 15
    
    while True:
        try:
            await asyncio.sleep(CHECK_INTERVAL)
            
            ads = get_ads_settings(session_name)
            
            if not ads.get('active', False):
                continue
            
            if not ads.get('banner_type'):
                continue
            
            last_sent = ads.get('last_sent')
            interval = ads.get('interval', 30) * 60
            now_ts = get_tehran_datetime().timestamp()
            
            if last_sent:
                try:
                    last_dt = datetime.fromisoformat(last_sent)
                    last_ts = last_dt.timestamp()
                    if now_ts - last_ts < interval:
                        continue
                except:
                    pass
            
            banner_type = ads.get('banner_type')
            banner_text = ads.get('banner_text', '')
            banner_media_id = ads.get('banner_media_id')
            banner_caption = ads.get('banner_caption', '')
            forward_mode = ads.get('forward_mode', False)
            
            groups = []
            try:
                async for d in client.iter_dialogs():
                    if d.is_group or (d.is_channel and not d.entity.broadcast):
                        groups.append(d)
            except Exception as e:
                print(f"⚠️ خطا در گرفتن گروه‌ها: {e}")
                continue
            
            if not groups:
                print(f"⚠️ {sid}: هیچ گروهی یافت نشد")
                continue
            
            success = 0
            failed = 0
            failed_reasons = []
            
            for dialog in groups:
                try:
                    if banner_type == 'text':
                        await client.send_message(dialog.id, banner_text)
                        success += 1
                    else:
                        await client.send_file(
                            dialog.id,
                            banner_media_id,
                            caption=banner_caption
                        )
                        success += 1
                    
                    await asyncio.sleep(1.5)
                
                except errors.FloodWaitError as e:
                    print(f"⏳ FloodWait: {e.seconds}s")
                    await asyncio.sleep(e.seconds)
                    failed += 1
                    failed_reasons.append(f"{dialog.id}: FloodWait")
                except errors.UserNotParticipantError:
                    failed += 1
                    failed_reasons.append(f"{dialog.id}: NotParticipant")
                except errors.UserBannedInChannelError:
                    failed += 1
                    failed_reasons.append(f"{dialog.id}: Banned")
                except errors.ChatWriteForbiddenError:
                    failed += 1
                    failed_reasons.append(f"{dialog.id}: WriteForbidden")
                except Exception as e:
                    failed += 1
                    err = str(e)[:50]
                    failed_reasons.append(f"{dialog.id}: {err}")
            
            increment_ads_stats(session_name, success, failed)
            
            try:
                now_tehran = get_tehran_datetime()
                report_time = now_tehran.strftime("%Y/%m/%d %H:%M:%S")
                
                if banner_type == 'text':
                    banner_preview = f"📝 متن: {banner_text[:100]}"
                else:
                    banner_preview = f"📎 {banner_type}"
                    if banner_caption:
                        banner_preview += f"\n📄 کپشن: {banner_caption[:100]}"
                
                mode_text = "📤 فوروارد" if forward_mode else "✉️ عادی"
                
                total = success + failed
                success_rate = (success / total * 100) if total > 0 else 0
                
                report = (
                    f"📢 **گزارش تبلیغ**\n"
                    f"━━━━━━━━━━━━━━\n"
                    f"🕐 **زمان:** `{report_time}`\n"
                    f"⏱ **فاصله:** `{ads.get('interval')}` دقیقه\n"
                    f"📤 **حالت:** {mode_text}\n\n"
                    f"📊 **آمار این چرخه:**\n"
                    f"   ✅ موفق: `{success}`\n"
                    f"   ❌ ناموفق: `{failed}`\n"
                    f"   📈 کل: `{total}`\n"
                    f"   📉 نرخ موفقیت: `{success_rate:.1f}%`\n\n"
                )
                
                total_success = ads.get('success_count', 0) + success
                total_failed = ads.get('failed_count', 0) + failed
                total_sent = ads.get('sent_count', 0) + 1
                
                report += (
                    f"📊 **آمار کل:**\n"
                    f"   🔄 تعداد چرخه: `{total_sent}`\n"
                    f"   ✅ کل موفق: `{total_success}`\n"
                    f"   ❌ کل ناموفق: `{total_failed}`\n"
                )
                
                if failed_reasons:
                    report += f"\n⚠️ **نمونه خطاها:**\n"
                    for i, reason in enumerate(failed_reasons[:5]):
                        report += f"   • {reason}\n"
                    if len(failed_reasons) > 5:
                        report += f"   ... و {len(failed_reasons) - 5} مورد دیگر\n"
                
                report += f"\n{banner_preview}"
                
                await client.send_message('me', report)
                print(f"📢 {sid}: تبلیغ انجام شد | ✅ {success} | ❌ {failed}")
            
            except Exception as e:
                print(f"⚠️ خطا در ارسال گزارش: {e}")
        
        except asyncio.CancelledError:
            break
        except Exception as e:
            print(f"⚠️ خطای advertiser: {e}")
            await asyncio.sleep(30)

async def run_self(session_path, session_string=None):
    global pending_channel_joins
    sid = os.path.basename(session_path)
    session_name = sid
    
    if sid not in session_locks:
        session_locks[sid] = asyncio.Lock()
    
    if session_locks[sid].locked():
        print(f"⚠️ سشن {sid} در حال اجراست")
        return
    
    async with session_locks[sid]:
        print(f"🚀 درحال اجرای سشن: {sid}")
        
        if session_string:
            client = TelegramClient(StringSession(session_string), API_ID, API_HASH)
        else:
            session_string = get_session_string(sid)
            if session_string:
                client = TelegramClient(StringSession(session_string), API_ID, API_HASH)
            else:
                print(f"❌ StringSession برای {sid} یافت نشد")
                return
        
        try:
            await client.connect()
            if not await client.is_user_authorized():
                print(f"❌ سشن {sid} معتبر نیست")
                await client.disconnect()
                return
        except Exception as e:
            print(f"❌ خطا در اتصال {sid}: {e}")
            try: await client.disconnect()
            except: pass
            return
        
        me = await client.get_me()
        me_id = me.id
        
        print(f"✅ سلف فعال شد: {me.id} | {me.first_name}")
        
        try:
            from telethon.tl.functions.users import GetFullUserRequest
            full = await client(GetFullUserRequest(me))
            bio = ""
            if hasattr(full, 'full_user') and hasattr(full.full_user, 'about'):
                bio = full.full_user.about or ""
            
            init_session(
                session_name,
                first_name=me.first_name or "",
                last_name=me.last_name or "",
                bio=bio
            )
        except Exception as e:
            print(f"⚠️ خطا در init: {e}")
            init_session(session_name, 
                        first_name=me.first_name or "",
                        last_name=me.last_name or "",
                        bio="")
        
        enemies = set(get_enemies(session_name))
        silences = set(get_silences(session_name))
        
        def save_enemies():
            update_enemies(session_name, list(enemies))
        
        def save_silences():
            update_silences(session_name, list(silences))
        
        try:
            await client.send_message('me',
                f"🎉 **ربات فعال شد!**\n\n"
                f"💡 **برای باز کردن پنل کنترل:**\n"
                f"دستور `.پنل` را در هر چتی ارسال کنید.\n\n"
                f"⚔️ `.دشمن` | 🤫 `.سکوت`\n"
                f"📨 `.اسپم` | 🗑 `.حذف پیام`\n"
                f"📊 `.info` | `.پینگ`"
            )
        except: pass
        
        @client.on(events.NewMessage(incoming=True))
        async def join_button_interceptor(event):
            chat_id = event.chat_id
            if pending_channel_joins.get(chat_id, False):
                if await join_from_inline_button(client, event):
                    pending_channel_joins[chat_id] = False

        @client.on(events.NewMessage(incoming=True))
        async def incoming_handler(event):
            try:
                chat_id = event.chat_id
                if chat_id in silences:
                    await event.delete()
                    return
                if chat_id in enemies:
                    await event.reply(random.choice(SWEAR_WORDS))
            except: pass
        
        @client.on(events.NewMessage(outgoing=True, pattern=PATTERN_PANEL))
        async def panel_handler(event):
            try:
                result = await client.inline_query(INLINE_USERNAME, "")
                print(f"🔍 نتیجه inline_query: {result}")
                
                if not result or len(result) == 0:
                    await event.reply(
                        "❌ ربات اینلاین پاسخی نداد.\n\n"
                        "**راه‌حل‌ها:**\n"
                        "1. `inline.py` در حال اجراست؟\n"
                        "2. `/setinline` فعال است؟\n"
                        f"3. `INLINE_USERNAME = '{INLINE_USERNAME}'` درست است؟"
                    )
                    await event.delete()
                    return
                
                try:
                    await result[0].click(event.chat_id)
                except Exception as click_error:
                    print(f"⚠️ click کار نکرد: {click_error}, امتحان send...")
                    try:
                        await result[0].send(event.chat_id)
                    except Exception as send_error:
                        print(f"⚠️ send هم کار نکرد: {send_error}")
                        await event.reply(f"❌ خطا در ارسال:\n{send_error}")
                
                await event.delete()
                
            except errors.BotResponseTimeoutError:
                await event.reply("❌ Timeout - `inline.py` را چک کنید")
                await event.delete()
            except errors.BotInlineDisabledError:
                await event.reply("❌ Inline Mode خاموش است.")
                await event.delete()
            except Exception as e:
                err_str = str(e)
                if "bot_invalid" in err_str.lower() or "peer_id_invalid" in err_str.lower():
                    await event.reply(f"❌ ربات یافت نشد. `{INLINE_USERNAME}`")
                else:
                    await event.reply(f"❌ خطا: `{e}`")
                try:
                    await event.delete()
                except:
                    pass
        
        @client.on(events.NewMessage(outgoing=True, pattern=PATTERN_PING))
        async def ping_command(event):
            try:
                await event.delete()
                msg = await client.send_message(event.chat_id, "📡 **در حال اندازه‌گیری پینگ...**")
                start = time.time()
                try:
                    await client.get_me()
                    ping_ms = (time.time() - start) * 1000
                    
                    if ping_ms < 100: status, emoji = "🟢 عالی", "🚀"
                    elif ping_ms < 200: status, emoji = "🟡 خوب", "✅"
                    elif ping_ms < 400: status, emoji = "🟠 متوسط", "⚡"
                    elif ping_ms < 800: status, emoji = "🔴 ضعیف", "⚠️"
                    else: status, emoji = "⛔ بسیار ضعیف", "❌"
                    
                    now = get_tehran_datetime()
                    await msg.edit(
                        f"📡 **نتیجه پینگ سرور**\n\n"
                        f"🔹 **پینگ:** `{ping_ms:.2f}` ms\n"
                        f"🔹 **وضعیت:** {status} {emoji}\n\n"
                        f"📅 `{now.strftime('%H:%M:%S')}` | 📆 `{now.strftime('%Y/%m/%d')}`"
                    )
                    await asyncio.sleep(15)
                    await msg.delete()
                except Exception as e:
                    await msg.edit(f"❌ خطا: {e}")
                    await asyncio.sleep(5)
                    await msg.delete()
            except Exception as e:
                print(f"⚠️ خطای پینگ: {e}")
        
        @client.on(events.NewMessage(outgoing=True, pattern=PATTERN_SPAM))
        async def spam(event):
            try:
                count = int(event.pattern_match.group(2))
                text = event.pattern_match.group(3).strip()
                if not (1 <= count <= 1000):
                    msg = await event.respond("❌ تعداد بین 1 تا 1000")
                    await asyncio.sleep(3); await msg.delete(); await event.delete(); return
                await event.delete()
                for _ in range(count):
                    await client.send_message(event.chat_id, text)
                    await asyncio.sleep(0.3)
            except: pass
        
        @client.on(events.NewMessage(outgoing=True, pattern=PATTERN_DELETE))
        async def delete_messages(event):
            try:
                count = int(event.pattern_match.group(2))
                if not (1 <= count <= 1000):
                    msg = await event.respond("❌ تعداد بین 1 تا 1000")
                    await asyncio.sleep(3); await msg.delete(); await event.delete(); return
                await event.delete()
                deleted = 0
                async for msg in client.iter_messages(event.chat_id, from_user='me'):
                    if deleted >= count: break
                    try:
                        await msg.delete()
                        deleted += 1
                        await asyncio.sleep(0.1)
                    except: pass
                confirm = await client.send_message(event.chat_id, f"✅ {deleted} پیام حذف شد!")
                await asyncio.sleep(3); await confirm.delete()
            except: pass
        
        @client.on(events.NewMessage(outgoing=True, pattern=PATTERN_ENEMY))
        async def add_enemy(event):
            try:
                arg = (event.pattern_match.group(2) or '').strip()
                if arg:
                    entity = await resolve_user(client, arg)
                    if not entity: return
                    chat_id = entity.id
                else:
                    if not event.is_private: return
                    chat_id = event.chat_id
                    entity = await event.get_chat()
                if chat_id == me_id: return
                enemies.add(chat_id)
                save_enemies()
                info = get_user_info(entity)
                msg = await event.respond(
                    f"⚔️ **دشمن اضافه شد:**\n"
                    f"👤 `{info['name'] or chat_id}`\n"
                    f"🆔 `{chat_id}`\n"
                    f"🔢 تعداد: `{len(enemies)}`"
                )
                await asyncio.sleep(4); await msg.delete(); await event.delete()
            except: pass

        @client.on(events.NewMessage(outgoing=True, pattern=PATTERN_UNENEMY))
        async def remove_enemy(event):
            try:
                arg = (event.pattern_match.group(2) or '').strip()
                if arg:
                    entity = await resolve_user(client, arg)
                    chat_id = entity.id if entity else event.chat_id
                else:
                    chat_id = event.chat_id
                if chat_id in enemies:
                    enemies.discard(chat_id)
                    save_enemies()
                    msg = await event.respond(f"✅ حذف شد! 🔢 `{len(enemies)}`")
                else:
                    msg = await event.respond("❌ در لیست نیست")
                await asyncio.sleep(3); await msg.delete(); await event.delete()
            except: pass

        @client.on(events.NewMessage(outgoing=True, pattern=PATTERN_LIST_ENEMIES))
        async def list_enemies(event):
            try:
                await event.delete()
                if not enemies:
                    msg = await client.send_message(event.chat_id, "📭 لیست خالی است")
                    await asyncio.sleep(3); await msg.delete(); return
                lines = ["⚔️ **لیست دشمنان:**\n"]
                for i, cid in enumerate(enemies, 1):
                    try:
                        ent = await client.get_entity(cid)
                        inf = get_user_info(ent)
                        lines.append(f"`{i}`. 👤 {inf['name'] or 'ناشناس'}\n   🆔 `{cid}` | 🏷 @{inf['username'] or 'ندارد'}\n")
                    except:
                        lines.append(f"`{i}`. 🆔 `{cid}`\n")
                msg = await client.send_message(event.chat_id, "\n".join(lines))
                await asyncio.sleep(15); await msg.delete()
            except: pass

        @client.on(events.NewMessage(outgoing=True, pattern=PATTERN_SILENCE))
        async def add_silence(event):
            try:
                arg = (event.pattern_match.group(2) or '').strip()
                if arg:
                    entity = await resolve_user(client, arg)
                    if not entity: return
                    chat_id = entity.id
                else:
                    if not event.is_private: return
                    chat_id = event.chat_id
                    entity = await event.get_chat()
                if chat_id == me_id: return
                silences.add(chat_id)
                save_silences()
                info = get_user_info(entity)
                msg = await event.respond(
                    f"🤫 **سکوت فعال شد:**\n"
                    f"👤 `{info['name'] or chat_id}`\n"
                    f"🆔 `{chat_id}`\n"
                    f"🔢 تعداد: `{len(silences)}`"
                )
                await asyncio.sleep(4); await msg.delete(); await event.delete()
            except: pass

        @client.on(events.NewMessage(outgoing=True, pattern=PATTERN_UNSILENCE))
        async def remove_silence(event):
            try:
                arg = (event.pattern_match.group(2) or '').strip()
                if arg:
                    entity = await resolve_user(client, arg)
                    chat_id = entity.id if entity else event.chat_id
                else:
                    chat_id = event.chat_id
                if chat_id in silences:
                    silences.discard(chat_id)
                    save_silences()
                    msg = await event.respond(f"✅ غیرفعال شد! 🔢 `{len(silences)}`")
                else:
                    msg = await event.respond("❌ در لیست نیست")
                await asyncio.sleep(3); await msg.delete(); await event.delete()
            except: pass

        @client.on(events.NewMessage(outgoing=True, pattern=PATTERN_LIST_SILENCES))
        async def list_silences(event):
            try:
                await event.delete()
                if not silences:
                    msg = await client.send_message(event.chat_id, "📭 لیست خالی است")
                    await asyncio.sleep(3); await msg.delete(); return
                lines = ["🤫 **لیست کاربران ساکت:**\n"]
                for i, cid in enumerate(silences, 1):
                    try:
                        ent = await client.get_entity(cid)
                        inf = get_user_info(ent)
                        lines.append(f"`{i}`. 👤 {inf['name'] or 'ناشناس'}\n   🆔 `{cid}` | 🏷 @{inf['username'] or 'ندارد'}\n")
                    except:
                        lines.append(f"`{i}`. 🆔 `{cid}`\n")
                msg = await client.send_message(event.chat_id, "\n".join(lines))
                await asyncio.sleep(15); await msg.delete()
            except: pass

        @client.on(events.NewMessage(outgoing=True, pattern=PATTERN_INFO))
        async def info(event):
            try:
                await event.delete()
                m = await client.get_me()
                settings = get_clock_settings(session_name)
                
                bio_status = "🟢 فعال" if settings.get("bio_clock") else "🔴 غیرفعال"
                ln_status = "🟢 فعال" if settings.get("lastname_clock") else "🔴 غیرفعال"
                main_status = "🟢 روشن" if settings.get("enabled") else "🔴 خاموش"
                
                now = get_tehran_datetime().strftime("%H:%M")
                font = settings.get("font", 1)
                if font in CLOCK_FORMATS:
                    preview = CLOCK_FORMATS[font]("", now).strip()
                else:
                    preview = now
                
                msg = await client.send_message(event.chat_id,
                    f"👤 **اطلاعات**\n\n"
                    f"📛 `{m.first_name or '-'} {m.last_name or ''}`\n"
                    f"🆔 `@{m.username or '-'}`\n"
                    f"🔢 `{m.id}`\n\n"
                    f"⏰ **ساعت:**\n"
                    f"   • وضعیت: {main_status}\n"
                    f"   • بیو: {bio_status}\n"
                    f"   • نام خانوادگی: {ln_status}\n"
                    f"   • فونت: {FONT_NAMES.get(font, 'Normal')}\n"
                    f"   • پیش‌نمایش: `{preview}`\n\n"
                    f"⚔️ دشمنان: `{len(enemies)}`\n"
                    f"🤫 سکوت‌ها: `{len(silences)}`"
                )
                await asyncio.sleep(15)
                await msg.delete()
            except Exception as e:
                print(f"⚠️ خطای info: {e}")
        
        clock_task = asyncio.create_task(clock_updater(client, session_name, sid))
        ad_task = asyncio.create_task(advertiser(client, session_name, sid))
        
        try:
            await client.run_until_disconnected()
        except asyncio.CancelledError:
            pass
        except Exception as e:
            print(f"❌ سشن {sid} قطع شد: {e}")
        finally:
            clock_task.cancel()
            ad_task.cancel()
            
            if sid in running_sessions:
                del running_sessions[sid]
            
            try:
                await client.disconnect()
            except:
                pass

async def start_all_selfs():
    print(f"\n{'='*60}")
    print(f"🔍 بررسی پوشه سشن‌ها")
    print(f"{'='*60}")
    print(f"📁 مسیر: {os.path.abspath(SESSIONS_DIR)}")
    
    if not os.path.exists(SESSIONS_DIR):
        os.makedirs(SESSIONS_DIR, exist_ok=True)
    
    all_files = os.listdir(SESSIONS_DIR)
    
    txt_files = [f[:-4] for f in all_files if f.endswith('.txt') and f.startswith('user_')]
    session_files = [f[:-8] for f in all_files if f.endswith('.session') and f.startswith('user_')]
    all_sessions = list(set(txt_files + session_files))
    
    print(f"✅ StringSessions: {len(txt_files)}")
    print(f"✅ قدیمی: {len(session_files)}")
    print(f"📊 مجموع: {len(all_sessions)}")
    
    tasks = []
    
    for session_name in all_sessions:
        session_path = os.path.join(SESSIONS_DIR, session_name)
        
        session_string = get_session_string(session_name)
        if not session_string:
            from self_manager import migrate_old_session
            session_string = await migrate_old_session(session_name)
        
        if not session_string:
            continue
        
        task = asyncio.create_task(run_self(session_path, session_string))
        running_sessions[session_name] = task
        tasks.append(task)
    
    watcher_task = asyncio.create_task(pending_watcher())
    tasks.append(watcher_task)
    
    print(f"\n🚀 {len(all_sessions)} سلف + 1 watcher")
    
    await asyncio.gather(*tasks)

if __name__ == "__main__":
    try:
        asyncio.run(start_all_selfs())
    except KeyboardInterrupt:
        print("\n👋 متوقف شد")