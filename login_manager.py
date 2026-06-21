# login_manager.py
import os
import json
import time
import asyncio
from telethon import TelegramClient, errors, Button
from telethon.sessions import StringSession
from telethon.tl.types import (
    KeyboardButtonRequestPhone, ReplyKeyboardMarkup,
    KeyboardButtonRow, KeyboardButton, ReplyKeyboardHide
)
from config import API_ID, API_HASH, SESSIONS_DIR, INLINE_USERNAME, get_tehran_time
from commands_db import init_session

login_states = {}
PHONES_FILE = os.path.join(SESSIONS_DIR, "phones.json")
os.makedirs(SESSIONS_DIR, exist_ok=True)

def load_phones():
    if os.path.exists(PHONES_FILE):
        try:
            with open(PHONES_FILE, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                return json.loads(content) if content else {}
        except:
            pass
    return {}

def save_phone(user_id, phone):
    phones = load_phones()
    phones[str(user_id)] = {"phone": phone, "saved_at": get_tehran_time()}
    try:
        with open(PHONES_FILE, 'w', encoding='utf-8') as f:
            json.dump(phones, f, ensure_ascii=False, indent=2)
            f.flush()
            os.fsync(f.fileno())
    except Exception as e:
        print(f"❌ خطا ذخیره شماره: {e}")

def get_saved_phone(user_id):
    phones = load_phones()
    data = phones.get(str(user_id))
    return data.get("phone") if data else None

def number_keyboard(uid):
    return [
        [Button.inline("1", f"login_1_{uid}"),
         Button.inline("2", f"login_2_{uid}"),
         Button.inline("3", f"login_3_{uid}")],
        [Button.inline("4", f"login_4_{uid}"),
         Button.inline("5", f"login_5_{uid}"),
         Button.inline("6", f"login_6_{uid}")],
        [Button.inline("7", f"login_7_{uid}"),
         Button.inline("8", f"login_8_{uid}"),
         Button.inline("9", f"login_9_{uid}")],
        [Button.inline("❌ پاک کردن", f"login_del_{uid}"),
         Button.inline("0", f"login_0_{uid}"),
         Button.inline("🔄 از اول", f"login_reset_{uid}")],
        [Button.inline("✅ تایید کد", f"login_ok_{uid}")],
        [Button.inline("❌ لغو کل عملیات", f"login_cancel_{uid}")]
    ]

async def start_login(event):
    uid = event.sender_id
    
    try:
        from self_manager import stop_session
        session_name = f"user_{uid}"
        await stop_session(session_name)
        await asyncio.sleep(1)
    except Exception as e:
        print(f"⚠️ خطا در توقف سشن قبلی: {e}")
    
    if uid in login_states:
        if login_states[uid].get("client"):
            try:
                await login_states[uid]["client"].disconnect()
            except:
                pass
        del login_states[uid]
    
    saved_phone = get_saved_phone(uid)
    
    if saved_phone:
        print(f"✅ شماره کاربر {uid} قبلاً ذخیره شده: {saved_phone}")
        await send_code_directly(event, saved_phone)
        return
    
    login_states[uid] = {
        "step": "ASK_PHONE", "phone": None, "client": None, "hash": None, "code": ""
    }
    
    phone_keyboard = ReplyKeyboardMarkup(
        rows=[
            KeyboardButtonRow(buttons=[KeyboardButtonRequestPhone(text='📱 اشتراک‌گذاری شماره من')]),
            KeyboardButtonRow(buttons=[KeyboardButton(text='❌ لغو نصب')])
        ],
        resize=True, single_use=False
    )
    
    try:
        await event.edit("⏳ در حال آماده‌سازی...")
    except:
        pass
    
    await event.respond(
        "🔐 **شروع نصب ربات سلف**\n\n"
        "👇 **روی دکمه زیر (در پایین صفحه کیبورد) کلیک کنید:**\n\n"
        f"🕐 **زمان فعلی (تهران):** `{get_tehran_time()}`\n\n"
        "💡 **توجه:**\n"
        "• دکمه 📱 در **پایین صفحه کیبورد** ظاهر می‌شود\n"
        "• اگر نمی‌بینید، روی آیکون کیبورد کلیک کنید\n\n"
        "💡 **امنیت:**\n"
        "• شماره فقط برای ورود استفاده می‌شود",
        buttons=phone_keyboard
    )

async def send_code_directly(event, phone):
    uid = event.sender_id
    
    try:
        msg = await event.edit(f"⏳ در حال ارسال کد به `{phone}`...")
    except:
        msg = await event.respond(f"⏳ در حال ارسال کد به `{phone}`...")
    
    client = TelegramClient(
        StringSession(), API_ID, API_HASH,
        device_model="Desktop", system_version="Windows 10", app_version="1.0"
    )
    
    try:
        await client.connect()
        
        if await client.is_user_authorized():
            await complete_login(msg, {
                "client": client, "phone": phone, "hash": None, "code": ""
            }, uid, already_logged_in=True)
            return
        
        result = await client.send_code_request(phone)
        
        login_states[uid] = {
            "step": "WAIT_CODE", "phone": phone, "client": client,
            "hash": result.phone_code_hash, "code": ""
        }
        
        await msg.edit(
            f"✅ **کد ارسال شد!**\n\n"
            f"📱 شماره: `{phone}`\n"
            f"🕐 زمان: `{get_tehran_time()}`\n\n"
            f"📩 کد 5 رقمی را وارد کنید:",
            buttons=number_keyboard(uid)
        )
    
    except errors.PhoneNumberInvalidError:
        await msg.edit("❌ شماره نامعتبر")
        await client.disconnect()
    except errors.PhoneNumberBannedError:
        await msg.edit("❌ شماره مسدود شده")
        await client.disconnect()
    except errors.FloodWaitError as e:
        await msg.edit(f"⏳ {e.seconds} ثانیه صبر کنید")
        await client.disconnect()
    except errors.SessionPasswordNeededError:
        login_states[uid] = {
            "step": "WAIT_2FA", "phone": phone, "client": client, "hash": None, "code": ""
        }
        await msg.edit(
            "🔒 **رمز دو مرحله‌ای فعال است**\n\n"
            "لطفاً رمز را ارسال کنید:",
            buttons=[[Button.inline("❌ لغو", f"login_cancel_{uid}")]]
        )
    except Exception as e:
        await msg.edit(f"❌ خطا: {e}")
        try:
            await client.disconnect()
        except:
            pass

async def handle_login_button(event):
    data = event.data.decode()
    parts = data.split("_")
    
    if len(parts) < 3:
        return
    
    action = parts[1]
    uid = int(parts[2])
    
    if uid not in login_states:
        await event.answer("❌ Session منقضی", alert=True)
        return
    
    state = login_states[uid]
    
    if action == "cancel":
        if state.get("client"):
            try:
                await state["client"].disconnect()
            except:
                pass
        del login_states[uid]
        await event.edit("❌ عملیات لغو شد", buttons=ReplyKeyboardHide())
        return
    
    if action == "reset":
        if state.get("client"):
            try:
                await state["client"].disconnect()
            except:
                pass
        del login_states[uid]
        await start_login(event)
        return
    
    if state["step"] == "WAIT_CODE":
        if action.isdigit():
            state["code"] += action
            await update_code_display(event, state, uid)
        elif action == "del":
            state["code"] = state["code"][:-1]
            await update_code_display(event, state, uid)
        elif action == "ok":
            if len(state["code"]) < 5:
                await event.answer("❌ کد باید 5 رقم باشد", alert=True)
                return
            await verify_code(event, state, uid)

async def update_code_display(event, state, uid):
    masked = "*" * len(state["code"]) if state["code"] else "—"
    await event.edit(
        f"🔢 **کد تایید**\n\n"
        f"📱 شماره: `{state['phone']}`\n"
        f"🔢 کد: `{masked}`\n"
        f"🕐 زمان: `{get_tehran_time()}`",
        buttons=number_keyboard(uid)
    )

async def handle_phone_contact(event):
    uid = event.sender_id
    
    if uid not in login_states:
        return
    
    state = login_states[uid]
    if state["step"] != "ASK_PHONE":
        return
    
    if not event.contact:
        return
    
    phone = event.contact.phone_number
    if not phone.startswith("+"):
        phone = "+" + phone
    
    save_phone(uid, phone)
    print(f"✅ شماره کاربر {uid} ذخیره شد: {phone}")
    
    try:
        await event.delete()
    except:
        pass
    
    msg = await event.respond("⏳ در حال ارسال کد...")
    await send_code_to_phone(msg, state, uid, phone)

async def handle_cancel_text(event):
    uid = event.sender_id
    if uid not in login_states:
        return
    state = login_states[uid]
    if state["step"] != "ASK_PHONE":
        return
    if event.text and event.text.strip() == "❌ لغو نصب":
        if state.get("client"):
            try:
                await state["client"].disconnect()
            except:
                pass
        del login_states[uid]
        await event.reply("❌ عملیات لغو شد", buttons=ReplyKeyboardHide())

async def send_code_to_phone(msg, state, uid, phone):
    client = TelegramClient(
        StringSession(), API_ID, API_HASH,
        device_model="Desktop", system_version="Windows 10", app_version="1.0"
    )
    
    try:
        await client.connect()
        result = await client.send_code_request(phone)
        
        state["step"] = "WAIT_CODE"
        state["phone"] = phone
        state["client"] = client
        state["hash"] = result.phone_code_hash
        state["code"] = ""
        
        await msg.edit(
            f"✅ **کد ارسال شد!**\n\n"
            f"📱 شماره: `{phone}`\n"
            f"🕐 زمان: `{get_tehran_time()}`\n\n"
            f"📩 کد 5 رقمی:",
            buttons=number_keyboard(uid)
        )
    except Exception as e:
        await msg.edit(f"❌ خطا: {e}")
        try:
            await client.disconnect()
        except:
            pass

async def handle_2fa_message(event):
    uid = event.sender_id
    if uid not in login_states:
        return
    state = login_states[uid]
    if state["step"] != "WAIT_2FA":
        return
    
    password = event.text.strip()
    
    try:
        await event.delete()
    except:
        pass
    
    msg = await event.reply("⏳ بررسی رمز...")
    
    try:
        await state["client"].sign_in(
            phone=state["phone"],
            password=password
        )
        await complete_login(msg, state, uid)
    except errors.PasswordHashInvalidError:
        await msg.edit(
            "❌ **رمز اشتباه!**\n\nدوباره ارسال کنید:",
            buttons=[[Button.inline("❌ لغو", f"login_cancel_{uid}")]]
        )
    except Exception as e:
        await msg.edit(f"❌ خطا: {e}")

async def verify_code(event, state, uid):
    try:
        msg = await event.edit("⏳ تایید کد...")
    except:
        msg = await event.respond("⏳ تایید کد...")
    
    try:
        await state["client"].sign_in(
            phone=state["phone"],
            code=state["code"],
            phone_code_hash=state["hash"]
        )
        await complete_login(msg, state, uid)
    except errors.SessionPasswordNeededError:
        state["step"] = "WAIT_2FA"
        await msg.edit(
            "🔒 **رمز دو مرحله‌ای فعال است**\n\nرمز را ارسال کنید:",
            buttons=[[Button.inline("❌ لغو", f"login_cancel_{uid}")]]
        )
    except errors.PhoneCodeInvalidError:
        state["code"] = ""
        await msg.edit("❌ کد نامعتبر. دوباره:", buttons=number_keyboard(uid))
    except errors.PhoneCodeExpiredError:
        await msg.edit(
            "⏰ کد منقضی. دوباره /install بزنید",
            buttons=[[Button.inline("🔄 شروع", b"install")]]
        )
    except Exception as e:
        await msg.edit(f"❌ خطا: {e}")

async def complete_login(msg, state, uid, already_logged_in=False):
    try:
        me = await state["client"].get_me()
        session_name = f"user_{uid}"
        
        session_string = state["client"].session.save()
        session_file = os.path.join(SESSIONS_DIR, f"{session_name}.txt")
        
        with open(session_file, 'w', encoding='utf-8') as f:
            f.write(session_string)
            f.flush()
            os.fsync(f.fileno())
        
        print(f"✅ StringSession ذخیره شد: {session_name}.txt")
        
        old_session_file = os.path.join(SESSIONS_DIR, f"{session_name}.session")
        if os.path.exists(old_session_file):
            try:
                os.remove(old_session_file)
                print(f"🧹 فایل قدیمی پاک شد: {session_name}.session")
            except Exception as e:
                print(f"⚠️ خطا در پاک کردن فایل قدیمی: {e}")
        
        first_name = me.first_name or ""
        last_name = me.last_name or ""
        bio = ""
        try:
            from telethon.tl.functions.users import GetFullUserRequest
            full = await state["client"](GetFullUserRequest(me))
            if hasattr(full, 'full_user') and hasattr(full.full_user, 'about'):
                bio = full.full_user.about or ""
        except:
            pass
        
        init_session(session_name, first_name=first_name, last_name=last_name, bio=bio)
        
        create_install_file(session_name, uid, first_name)
        
        success_msg = "✅ **از قبل متصل!**\n\n" if already_logged_in else "🎉 **نصب موفق!**\n\n"
        
        await msg.edit(
            success_msg +
            f"👤 `{first_name} {last_name}`\n"
            f"🆔 `{me.id}`\n"
            f"🏷 `@{me.username or '-'}`\n"
            f"🕐 `{get_tehran_time()}`\n\n"
            f"✅ سلف فعال شد!\n\n"
            f"💡 **برای باز کردن پنل کنترل:**\n"
            f"در هر چتی دستور `.پنل` را ارسال کنید.\n\n"
            f"📋 **سایر دستورات:**\n"
            f"• `.ساعت روشن 1-13`\n"
            f"• `.اسپم 20 سلام`\n"
            f"• `.دشمن` • `.سکوت`\n"
            f"• `.info` • `.پینگ`",
            buttons=ReplyKeyboardHide()
        )
        
        if uid in login_states:
            del login_states[uid]
        
        print(f"🔌 قطع اتصال: {session_name}")
        try:
            await state["client"].disconnect()
        except Exception as e:
            print(f"⚠️ خطا در disconnect: {e}")
        
        await asyncio.sleep(1)
        
        print(f"🚀 استارت سلف: {session_name}")
        from self_manager import start_session
        await start_session(session_name)
        
    except Exception as e:
        await msg.edit(f"❌ خطا: {e}")
        print(f"⚠️ خطا در complete_login: {e}")

def create_install_file(session_name, installer_uid, account_name):
    file = os.path.join(SESSIONS_DIR, "installs.json")
    
    data = {}
    if os.path.exists(file):
        try:
            with open(file, "r", encoding="utf-8") as f:
                content = f.read().strip()
                data = json.loads(content) if content else {}
        except:
            data = {}
    
    data[session_name] = {
        "status": "pending",
        "installer_uid": installer_uid,
        "account_name": account_name,
        "time": get_tehran_time()
    }
    
    with open(file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.flush()
        os.fsync(f.fileno())
    
    print(f"✅ نصب ثبت شد: {session_name}")