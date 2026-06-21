# bot.py
import os
import json
import time
from telethon import TelegramClient, events, Button, errors
from config import API_ID, API_HASH, BOT_TOKEN, SESSIONS_DIR, get_tehran_time, BOT_USERNAME
from login_manager import (
    start_login, handle_login_button, handle_phone_contact,
    handle_2fa_message, login_states
)

SELF_DATA_FILE = os.path.join(SESSIONS_DIR, 'self_data.json')
os.makedirs(SESSIONS_DIR, exist_ok=True)

user_states = {}

def load_self_data():
    if os.path.exists(SELF_DATA_FILE):
        try:
            with open(SELF_DATA_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            pass
    return {'ads': {}, 'users': {}}

def save_self_data(data):
    with open(SELF_DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

async def run_bot():
    bot = TelegramClient('sessions/bot_main', API_ID, API_HASH)
    try:
        await bot.start(bot_token=BOT_TOKEN)
    except Exception as e:
        print(f"❌ خطا ربات: {e}")
        return
    print("🤖 ربات اصلی فعال شد")
    
    async def send_main_menu(event, edit=False):
        text = (
            "🎛 **منوی اصلی ربات**\n\n"
            "یکی از گزینه‌ها را انتخاب کنید:"
        )
        buttons = [
            [Button.inline("🔧 نصب ربات سلف", data=b"install")],
            [Button.inline("📖 راهنمای دستورات", data=b"commands"),
             Button.inline("🎯 قابلیت تبچی", data=b"ad_menu")],
            [Button.inline("ℹ️ درباره ربات", data=b"about"),
             Button.inline("❌ بستن", data=b"close")],
        ]
        if edit:
            await event.edit(text, buttons=buttons)
        else:
            await event.reply(text, buttons=buttons)
    
    # ========================================
    # 🆕 /start با Deep Link Handler
    # ========================================
    @bot.on(events.NewMessage(pattern='/start'))
    async def start(event):
        uid = event.sender_id
        
        # 🆕 بررسی Deep Link parameters
        if event.raw_text and len(event.raw_text.split()) > 1:
            deep_param = event.raw_text.split()[1]
            
            # 🎯 Deep Link برای ارسال بنر
            if deep_param == "ads_banner":
                session_name = f"user_{uid}"
                
                # بررسی اینکه کاربر سشن فعال دارد
                from commands_db import session_exists, get_ads_settings, update_ads_settings
                
                if not session_exists(session_name):
                    await event.reply(
                        "❌ **ابتدا باید سلف‌بات خود را نصب کنید!**\n\n"
                        "لطفاً از دکمه زیر استفاده کنید:",
                        buttons=[[Button.inline("🔧 نصب ربات سلف", data=b"install")]]
                    )
                    return
                
                # ست کردن state برای شروع فرایند
                user_states[uid] = {
                    'step': 'ADV_WAITING_BANNER',
                    'data': {}
                }
                
                # علامت‌گذاری در دیتابیس
                update_ads_settings(session_name, _waiting_banner=True)
                
                await event.reply(
                    "📢 **ارسال بنر جدید**\n\n"
                    "لطفاً بنر خود را ارسال کنید.\n"
                    "می‌تواند **متن، عکس، فیلم یا فایل** باشد.\n\n"
                    "💡 برای لغو: `/cancel`\n\n"
                    "👇 **همین الان بنر را بفرستید:**"
                )
                return
            
            # سایر Deep Link ها اینجا قابل اضافه شدن هستند
            # elif deep_param == "other_feature": ...
        
        # حالت عادی /start
        from commands_db import get_ads_settings
        session_name = f"user_{uid}"
        ads = get_ads_settings(session_name)
        
        if ads.get('_waiting_banner'):
            user_states[uid] = {
                'step': 'ADV_WAITING_BANNER',
                'data': {}
            }
            await event.reply(
                "📢 **ارسال بنر جدید**\n\n"
                "لطفاً بنر خود را ارسال کنید.\n"
                "می‌تواند **متن، عکس، فیلم یا فایل** باشد.\n\n"
                "💡 برای لغو: `/cancel`"
            )
            return
        
        if uid in user_states:
            del user_states[uid]
        await send_main_menu(event)
    
    @bot.on(events.NewMessage(pattern='/install'))
    async def install_cmd(event):
        class EventWrapper:
            def __init__(self, original):
                self.sender_id = original.sender_id
                self.chat_id = original.chat_id
                self.original = original
            
            async def edit(self, *args, **kwargs):
                return await self.original.respond(*args, **kwargs)
                
            async def respond(self, *args, **kwargs):
                return await self.original.respond(*args, **kwargs)
        
        wrapped = EventWrapper(event)
        await start_login(wrapped)
    
    @bot.on(events.NewMessage(func=lambda e: e.is_private))
    async def message_handler(event):
        uid = event.sender_id
        
        if event.contact:
            if uid in login_states and login_states[uid]["step"] == "ASK_PHONE":
                await handle_phone_contact(event)
                return
        
        if uid in login_states:
            state = login_states[uid]
            
            if state["step"] == "WAIT_2FA":
                if event.text:
                    await handle_2fa_message(event)
                    return
        
        if uid not in user_states:
            return
        
        state = user_states[uid]
        step = state.get('step')
        session_name = f"user_{uid}"
        
        if event.text and event.text.strip() in ['/cancel', 'لغو', '❌ لغو']:
            del user_states[uid]
            await event.reply("❌ عملیات لغو شد")
            await send_main_menu(event)
            return
        
        try:
            if step == 'ADV_WAITING_BANNER':
                from commands_db import update_ads_settings
                
                banner_data = {
                    'type': None, 'text': '', 'media_id': None, 'caption': ''
                }
                
                if event.photo:
                    banner_data['type'] = 'photo'
                    banner_data['media_id'] = event.photo.id
                    banner_data['caption'] = event.text or ''
                elif event.video:
                    banner_data['type'] = 'video'
                    banner_data['media_id'] = event.video.id
                    banner_data['caption'] = event.text or ''
                elif event.document:
                    banner_data['type'] = 'document'
                    banner_data['media_id'] = event.document.id
                    banner_data['caption'] = event.text or ''
                elif event.text:
                    banner_data['type'] = 'text'
                    banner_data['text'] = event.text
                else:
                    await event.reply("❌ نوع پیام پشتیبانی نمی‌شود")
                    return
                
                state['data']['banner'] = banner_data
                state['step'] = 'ADV_WAITING_INTERVAL'
                
                preview = ""
                if banner_data['type'] == 'text':
                    preview = f"📝 متن:\n{banner_data['text'][:200]}"
                else:
                    preview = f"📎 نوع: {banner_data['type']}\n📝 کپشن: {banner_data['caption'][:200] or '—'}"
                
                await event.reply(
                    f"✅ **بنر دریافت شد!**\n\n"
                    f"{preview}\n\n"
                    f"⏱ **حالا فاصله زمانی را به دقیقه وارد کنید:**\n"
                    f"(مثلاً `30` برای هر 30 دقیقه)\n\n"
                    f"💡 برای لغو: `/cancel`"
                )
                return
            
            elif step == 'ADV_WAITING_INTERVAL':
                text = (event.text or '').strip()
                if not text.isdigit():
                    await event.reply("❌ فقط عدد وارد کنید (به دقیقه)")
                    return
                
                interval = int(text)
                if interval < 1 or interval > 1440:
                    await event.reply("❌ بین 1 تا 1440 دقیقه")
                    return
                
                state['data']['interval'] = interval
                state['step'] = 'ADV_WAITING_FORWARD'
                
                await event.reply(
                    f"✅ فاصله: **{interval} دقیقه**\n\n"
                    f"📤 **حالت ارسال:**\n"
                    f"آیا بنر به صورت **فوروارد** ارسال شود؟\n\n"
                    f"💡 فوروارد = بدون کپی (بهتر برای جلوگیری از اسپم)\n"
                    f"💡 عادی = کپی کامل پیام\n\n"
                    f"👇 یکی از دکمه‌ها را بزنید:",
                    buttons=[
                        [Button.inline("📤 فوروارد", data=b"adv_fwd_yes"),
                         Button.inline("✉️ عادی", data=b"adv_fwd_no")],
                        [Button.inline("❌ لغو", data=b"adv_cancel")]
                    ]
                )
                return
            
            elif step == 'ADV_WAITING_FORWARD':
                text = (event.text or '').strip().lower()
                forward_mode = False
                if text in ['بله', 'yes', 'فوروارد', '1']:
                    forward_mode = True
                elif text in ['نه', 'no', 'خیر', 'عادی', '0']:
                    forward_mode = False
                else:
                    await event.reply("❌ لطفاً از دکمه‌ها استفاده کنید")
                    return
                
                await finalize_ads(event, uid, session_name, state, forward_mode)
                return
        
        except Exception as e:
            print(f"⚠️ خطا در ads_flow_handler: {e}")
            await event.reply(f"❌ خطا: {e}")
            return
    
    async def finalize_ads(event, uid, session_name, state, forward_mode):
        from commands_db import update_ads_settings
        
        banner = state['data']['banner']
        interval = state['data']['interval']
        
        update_ads_settings(
            session_name,
            active=True,
            interval=interval,
            forward_mode=forward_mode,
            banner_type=banner['type'],
            banner_text=banner['text'],
            banner_media_id=banner['media_id'],
            banner_caption=banner['caption'],
            success_count=0,
            failed_count=0,
            sent_count=0,
            last_sent=None,
            _waiting_banner=False
        )
        
        if uid in user_states:
            del user_states[uid]
        
        forward_text = "📤 فوروارد" if forward_mode else "✉️ عادی"
        
        # 🆕 لینک بازگشت به پنل اینلاین
        inline_link = f"https://t.me/{INLINE_USERNAME}"
        
        await event.reply(
            f"🎉 **تبلیغ فعال شد!**\n\n"
            f"⏱ فاصله: `{interval}` دقیقه\n"
            f"📤 حالت: {forward_text}\n"
            f"📎 نوع بنر: `{banner['type']}`\n\n"
            f"💡 **گزارش‌ها در پیام‌های ذخیره (Saved Messages)** ارسال می‌شوند.\n\n"
            f"📊 برای مشاهده آمار، از دستور `.پنل` در چت استفاده کنید.",
            buttons=[[Button.url("🎛 بازگشت به پنل", inline_link)]]
        )
    
    @bot.on(events.CallbackQuery(data=b"adv_fwd_yes"))
    async def adv_fwd_yes(event):
        uid = event.sender_id
        if uid not in user_states:
            await event.answer("❌ Session منقضی", alert=True)
            return
        state = user_states[uid]
        if state.get('step') != 'ADV_WAITING_FORWARD':
            return
        session_name = f"user_{uid}"
        await finalize_ads(event, uid, session_name, state, forward_mode=True)

    @bot.on(events.CallbackQuery(data=b"adv_fwd_no"))
    async def adv_fwd_no(event):
        uid = event.sender_id
        if uid not in user_states:
            await event.answer("❌ Session منقضی", alert=True)
            return
        state = user_states[uid]
        if state.get('step') != 'ADV_WAITING_FORWARD':
            return
        session_name = f"user_{uid}"
        await finalize_ads(event, uid, session_name, state, forward_mode=False)

    @bot.on(events.CallbackQuery(data=b"adv_cancel"))
    async def adv_cancel(event):
        uid = event.sender_id
        if uid in user_states:
            del user_states[uid]
        await event.edit("❌ عملیات لغو شد")
    
    @bot.on(events.CallbackQuery())
    async def callback(event):
        data = event.data.decode('utf-8')
        uid = event.sender_id
        
        try:
            if data.startswith("login_"):
                await handle_login_button(event)
                return
            
            if data == "install":
                class EventWrapper:
                    def __init__(self, original):
                        self.sender_id = original.sender_id
                        self.chat_id = original.chat_id
                        self.original = original
                    
                    async def edit(self, *args, **kwargs):
                        try:
                            return await self.original.edit(*args, **kwargs)
                        except errors.MessageNotModifiedError:
                            pass
                        except:
                            return await self.original.respond(*args, **kwargs)
                            
                    async def respond(self, *args, **kwargs):
                        return await self.original.respond(*args, **kwargs)
                
                wrapped = EventWrapper(event)
                await start_login(wrapped)
                return
            
            elif data == "ad_menu":
                sdata = load_self_data()
                ad = sdata.get('ads', {}).get(str(uid))
                
                if ad and ad.get('active'):
                    count_text = "بی‌نهایت" if ad.get('total_count', 0) == 0 else f"{ad.get('total_count')} بار"
                    await event.edit(
                        f"🎯 **تبلیغات فعال**\n\n"
                        f"⏱ فاصله: `{ad.get('interval')}` دقیقه\n"
                        f"📊 کل: {count_text}\n"
                        f"✅ ارسال شده: `{ad.get('sent_count', 0)}` بار",
                        buttons=[
                            [Button.inline("⏸ توقف", data=b"ad_pause"),
                             Button.inline("▶️ ادامه", data=b"ad_resume")],
                            [Button.inline("🗑 حذف", data=b"ad_delete")],
                            [Button.inline("🆕 جدید", data=b"ad_new")],
                            [Button.inline("⬅️ بازگشت", data=b"back")],
                        ]
                    )
                else:
                    deep_link = f"https://t.me/{BOT_USERNAME}?start=ads_banner"
                    await event.edit(
                        "🎯 **قابلیت‌های تبچی**\n\n"
                        "📢 ارسال تبلیغ به همه گروه‌ها\n\n"
                        "💡 **برای ارسال بنر جدید:**\n"
                        "روی دکمه زیر کلیک کنید",
                        buttons=[
                            [Button.url("➕ ارسال بنر جدید", deep_link)],
                            [Button.inline("⬅️ بازگشت", data=b"back")],
                        ]
                    )
            
            elif data == "ad_new":
                # هدایت با Deep Link
                deep_link = f"https://t.me/{BOT_USERNAME}?start=ads_banner"
                await event.edit(
                    "🎯 **ارسال بنر جدید**\n\n"
                    "برای شروع، روی دکمه زیر کلیک کنید:",
                    buttons=[[Button.url("➕ شروع ارسال بنر", deep_link)]]
                )
            
            elif data == "ad_confirm":
                state = user_states.get(uid)
                if not state:
                    await event.edit("❌ منقضی")
                    return
                ad_data = state['data']
                sdata = load_self_data()
                sdata.setdefault('ads', {})[str(uid)] = {
                    'user_id': uid,
                    'interval': ad_data['interval'],
                    'total_count': ad_data['total_count'],
                    'text': ad_data.get('text', ''),
                    'media_type': ad_data.get('media_type'),
                    'media_id': ad_data.get('media_id'),
                    'active': True,
                    'sent_count': 0,
                    'created_at': time.time(),
                    'last_sent': None,
                }
                save_self_data(sdata)
                del user_states[uid]
                
                count_text = "بی‌نهایت" if ad_data['total_count'] == 0 else f"{ad_data['total_count']} بار"
                await event.edit(
                    f"✅ **فعال شد!**\n\n⏱ {ad_data['interval']} دقیقه\n📊 {count_text}",
                    buttons=[
                        [Button.inline("⏸ توقف", data=b"ad_pause"),
                         Button.inline("🗑 حذف", data=b"ad_delete")],
                        [Button.inline("⬅️ منو", data=b"back")],
                    ]
                )
            
            elif data == "ad_cancel":
                if uid in user_states:
                    del user_states[uid]
                await event.edit("❌ لغو شد",
                    buttons=[[Button.inline("⬅️ بازگشت", data=b"ad_menu")]])
            
            elif data == "ad_pause":
                sdata = load_self_data()
                if str(uid) in sdata.get('ads', {}):
                    sdata['ads'][str(uid)]['active'] = False
                    save_self_data(sdata)
                await event.answer("⏸ متوقف شد", alert=True)
            
            elif data == "ad_resume":
                sdata = load_self_data()
                if str(uid) in sdata.get('ads', {}):
                    sdata['ads'][str(uid)]['active'] = True
                    save_self_data(sdata)
                await event.answer("▶️ ادامه یافت", alert=True)
            
            elif data == "ad_delete":
                sdata = load_self_data()
                if str(uid) in sdata.get('ads', {}):
                    del sdata['ads'][str(uid)]
                    save_self_data(sdata)
                await event.edit("🗑 حذف شد",
                    buttons=[[Button.inline("⬅️ بازگشت", data=b"ad_menu")]])
            
            elif data == "commands":
                await event.edit(
                    "📖 **راهنما**",
                    buttons=[
                        [Button.inline("⏰ ساعت", data=b"cmd_clock"),
                         Button.inline("📨 اسپم", data=b"cmd_spam")],
                        [Button.inline("🗑 حذف", data=b"cmd_delete"),
                         Button.inline("⚔️ دشمن", data=b"cmd_enemy")],
                        [Button.inline("🤫 سکوت", data=b"cmd_silence"),
                         Button.inline("🎛 سایر", data=b"cmd_other")],
                        [Button.inline("⬅️ بازگشت", data=b"back")],
                    ]
                )
            
            elif data in ["cmd_clock", "cmd_spam", "cmd_delete", "cmd_enemy", "cmd_silence", "cmd_other"]:
                texts = {
                    "cmd_clock": "⏰ `.ساعت روشن 1` تا `.ساعت روشن 13`\n`.ساعت خاموش`\n\n💡 **پیشنهاد:** دستور `.پنل` را بزنید",
                    "cmd_spam": "📨 `.اسپم 20 سلام`",
                    "cmd_delete": "🗑 `.حذف پیام 20`",
                    "cmd_enemy": "⚔️ `.دشمن` `.حذف دشمن` `.لیست دشمن`",
                    "cmd_silence": "🤫 `.سکوت` `.حذف سکوت` `.لیست سکوت`",
                    "cmd_other": "🎛 `.پنل` `.info` `.پینگ`"
                }
                await event.edit(
                    texts.get(data, ""),
                    buttons=[[Button.inline("⬅️ بازگشت", data=b"commands")]]
                )
            
            elif data == "about":
                await event.edit(
                    "ℹ️ **درباره ربات**\n\n"
                    "📦 نسخه 8.0 - معماری StringSession\n\n"
                    "✨ نصب با یک کلیک\n"
                    "✨ Share Contact تلگرام\n"
                    "✨ 13 فونت Unicode\n"
                    "✨ تبلیغات خودکار با Deep Link\n"
                    "✨ دستور `.پنل` برای کنترل کامل",
                    buttons=[[Button.inline("⬅️ بازگشت", data=b"back")]]
                )
            
            elif data == "back":
                if uid in user_states:
                    del user_states[uid]
                await send_main_menu(event, edit=True)
            
            elif data == "close":
                await event.delete()
        
        except errors.MessageNotModifiedError:
            pass
        except Exception as e:
            print(f"⚠️ callback: {e}")
            try:
                await event.answer(f"❌ خطا: {e}", alert=True)
            except:
                pass
    
    await bot.run_until_disconnected()
