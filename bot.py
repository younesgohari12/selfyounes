# inline.py
import os
from datetime import datetime
from telethon import TelegramClient, events, Button
from config import (
    API_ID, API_HASH, INLINE_BOT_TOKEN, INLINE_USERNAME,
    CLOCK_FORMATS, FONT_NAMES, BOT_USERNAME, get_tehran_time
)
from commands_db import (
    get_session_data, get_clock_settings, update_clock_settings,
    init_session, session_exists, get_ads_settings, update_ads_settings,
    delete_ads_banner, reset_ads_stats
)

async def run_inline():
    bot = TelegramClient('sessions/inline_bot', API_ID, API_HASH)
    
    try:
        await bot.start(bot_token=INLINE_BOT_TOKEN)
    except Exception as e:
        print(f"❌ خطا Inline Bot: {e}")
        return
    
    print(f"🤖 Inline Bot فعال شد: @{INLINE_USERNAME}")

    def find_session_name(sender_id):
        session_name = f"user_{sender_id}"
        if session_exists(session_name):
            return session_name
        try:
            from config import SESSIONS_DIR
            if os.path.exists(SESSIONS_DIR):
                for f in os.listdir(SESSIONS_DIR):
                    if f.endswith('.txt') and f.startswith('user_'):
                        sname = f[:-4]
                        if session_exists(sname):
                            return sname
        except:
            pass
        init_session(session_name)
        return session_name

    def get_font_preview(font_num, time_str="12:34"):
        if font_num in CLOCK_FORMATS:
            try:
                formatted = CLOCK_FORMATS[font_num]("Ali", time_str)
                return formatted.strip()
            except:
                return f"{font_num}. {FONT_NAMES.get(font_num, 'Unknown')}"
        return f"{font_num}. {FONT_NAMES.get(font_num, 'Unknown')}"

    def build_main_menu():
        text = (
            "🎛 **پنل کنترل سلف**\n\n"
            "یکی از گزینه‌ها را انتخاب کنید:\n\n"
            f"🕐 زمان تهران: `{get_tehran_time('%H:%M:%S')}`"
        )
        buttons = [
            [Button.inline("⏰ ساعت", data=b"clk_menu")],
            [Button.inline("📢 تبچی", data=b"adv_menu"),
             Button.inline("⚔️ دشمن", data=b"enm_menu")],
            [Button.inline("🤫 سکوت", data=b"sil_menu"),
             Button.inline("📨 اسپم", data=b"spm_menu")],
            [Button.inline("🗑 حذف پیام", data=b"del_menu"),
             Button.inline("❓ راهنما", data=b"hlp_menu")],
        ]
        return text, buttons

    def build_clock_menu(session_name):
        settings = get_clock_settings(session_name)
        enabled = settings.get("enabled", False)
        bio_clock = settings.get("bio_clock", False)
        lastname_clock = settings.get("lastname_clock", False)
        font = settings.get("font", 1)
        
        now = datetime.now().strftime("%H:%M")
        preview = get_font_preview(font, now)
        
        main_status = "🟢 **روشن**" if enabled else "🔴 **خاموش**"
        bio_status = "✅ فعال" if bio_clock else "❌ غیرفعال"
        ln_status = "✅ فعال" if lastname_clock else "❌ غیرفعال"
        
        toggle_text = "🔴 خاموش کردن ساعت" if enabled else "🟢 روشن کردن ساعت"
        
        text = (
            f"⏰ **تنظیمات ساعت پروفایل**\n\n"
            f"**وضعیت:** {main_status}\n\n"
            f"📝 **پیش‌نمایش:**\n`{preview}`\n\n"
            f"🕐 تهران: `{get_tehran_time('%H:%M:%S')}`"
        )
        
        buttons = [
            [Button.inline(toggle_text, data=b"clk_toggle")],
            [Button.inline(f"📝 ساعت در بیو: {bio_status}", data=b"clk_bio")],
            [Button.inline(f"👤 ساعت در نام خانوادگی: {ln_status}", data=b"clk_ln")],
            [Button.inline(f"🎨 فونت: {FONT_NAMES.get(font, 'Normal')}", data=b"clk_fnt_menu")],
            [Button.inline("⬅️ بازگشت", data=b"back_main")],
        ]
        return text, buttons

    def build_font_menu(session_name):
        settings = get_clock_settings(session_name)
        current_font = settings.get("font", 1)
        now = datetime.now().strftime("%H:%M")
        
        text = (
            f"🎨 **انتخاب فونت ساعت**\n\n"
            f"📝 زمان نمونه: `{now}`\n"
        )
        
        buttons = []
        for i in range(1, 14):
            tick = "✅" if i == current_font else "  "
            preview = get_font_preview(i, now)
            btn_text = f"{tick} {preview}"
            if len(btn_text) > 60:
                btn_text = btn_text[:57] + "..."
            buttons.append([Button.inline(btn_text, data=f"clk_f{i}".encode())])
        
        buttons.append([Button.inline("⬅️ بازگشت", data=b"clk_menu")])
        return text, buttons

    def build_ads_menu(session_name):
        ads = get_ads_settings(session_name)
        active = ads.get("active", False)
        banner_type = ads.get("banner_type")
        interval = ads.get("interval", 30)
        forward_mode = ads.get("forward_mode", False)
        success = ads.get("success_count", 0)
        failed = ads.get("failed_count", 0)
        last_sent = ads.get("last_sent")
        
        status = "🟢 فعال" if active else "🔴 غیرفعال"
        banner_status = "✅ دارد" if banner_type else "❌ ندارد"
        forward_status = "✅ فوروارد" if forward_mode else "📤 عادی"
        
        last_sent_text = "—"
        if last_sent:
            try:
                last_dt = datetime.fromisoformat(last_sent)
                last_sent_text = last_dt.strftime("%H:%M:%S")
            except:
                last_sent_text = last_sent
        
        toggle_text = "🔴 خاموش کردن تبلیغ" if active else "🟢 روشن کردن تبلیغ"
        
        # 🆕 ساخت لینک Deep Link برای ارسال بنر
        deep_link = f"https://t.me/{BOT_USERNAME}?start=ads_banner"
        
        text = (
            f"📢 **مدیریت تبچی (تبلیغات)**\n\n"
            f"**وضعیت:** {status}\n"
            f"**بنر:** {banner_status}\n"
            f"**حالت ارسال:** {forward_status}\n"
            f"**فاصله:** هر `{interval}` دقیقه\n\n"
            f"📊 **آمار:**\n"
            f"   ✅ موفق: `{success}`\n"
            f"   ❌ ناموفق: `{failed}`\n"
            f"   🕐 آخرین ارسال: `{last_sent_text}`\n\n"
            f"🕐 تهران: `{get_tehran_time('%H:%M:%S')}`"
        )
        
        buttons = [
            [Button.inline(toggle_text, data=b"adv_toggle")],
            # 🆕 دکمه URL به جای inline button - با کلیک مستقیم به ربات می‌رود
            [Button.url("➕ ارسال بنر جدید", deep_link)],
            [Button.inline("🗑 حذف بنر فعلی", data=b"adv_delete")],
            [Button.inline("🔄 ریست آمار", data=b"adv_reset_stats")],
            [Button.inline("⬅️ بازگشت", data=b"back_main")],
        ]
        return text, buttons

    @bot.on(events.InlineQuery)
    async def inline_handler(event):
        try:
            builder = event.builder
            sender_id = event.sender_id
            session_name = find_session_name(sender_id)
            
            text, buttons = build_main_menu()
            
            result = builder.article(
                title="🎛 پنل کنترل سلف",
                description=f"پنل شما | {session_name}",
                text=text,
                buttons=buttons
            )
            
            await event.answer([result], cache_time=0, private=True)
        except Exception as e:
            print(f"⚠️ خطای inline query: {e}")
    
    @bot.on(events.CallbackQuery())
    async def callback_handler(event):
        try:
            d = event.data.decode('utf-8')
            sender_id = event.sender_id
            session_name = find_session_name(sender_id)
            
            if d == "back_main":
                text, buttons = build_main_menu()
                await event.edit(text, buttons=buttons)
                return
            
            if d == "clk_menu":
                text, buttons = build_clock_menu(session_name)
                await event.edit(text, buttons=buttons)
                return
            
            if d == "clk_toggle":
                settings = get_clock_settings(session_name)
                new_state = not settings.get("enabled", False)
                update_clock_settings(session_name, enabled=new_state)
                await event.answer(
                    "🟢 ساعت روشن شد!" if new_state else "🔴 ساعت خاموش شد",
                    alert=True
                )
                text, buttons = build_clock_menu(session_name)
                await event.edit(text, buttons=buttons)
                return
            
            if d == "clk_bio":
                settings = get_clock_settings(session_name)
                new_state = not settings.get("bio_clock", False)
                update_clock_settings(session_name, bio_clock=new_state)
                if new_state and not settings.get("enabled"):
                    update_clock_settings(session_name, enabled=True)
                await event.answer(
                    "✅ بیو فعال شد" if new_state else "❌ بیو غیرفعال شد",
                    alert=True
                )
                text, buttons = build_clock_menu(session_name)
                await event.edit(text, buttons=buttons)
                return
            
            if d == "clk_ln":
                settings = get_clock_settings(session_name)
                new_state = not settings.get("lastname_clock", False)
                update_clock_settings(session_name, lastname_clock=new_state)
                if new_state and not settings.get("enabled"):
                    update_clock_settings(session_name, enabled=True)
                await event.answer(
                    "✅ نام خانوادگی فعال شد" if new_state else "❌ نام خانوادگی غیرفعال شد",
                    alert=True
                )
                text, buttons = build_clock_menu(session_name)
                await event.edit(text, buttons=buttons)
                return
            
            if d == "clk_fnt_menu":
                text, buttons = build_font_menu(session_name)
                await event.edit(text, buttons=buttons)
                return
            
            if d.startswith("clk_f") and d[5:].isdigit():
                font_num = int(d[5:])
                if 1 <= font_num <= 13:
                    update_clock_settings(session_name, font=font_num)
                    await event.answer(
                        f"✅ فونت: {FONT_NAMES[font_num]}", alert=True
                    )
                    text, buttons = build_font_menu(session_name)
                    await event.edit(text, buttons=buttons)
                return
            
            if d == "adv_menu":
                text, buttons = build_ads_menu(session_name)
                await event.edit(text, buttons=buttons)
                return
            
            if d == "adv_toggle":
                ads = get_ads_settings(session_name)
                
                if not ads.get("banner_type"):
                    await event.answer(
                        "❌ ابتدا باید بنر ارسال کنید!\n\nروی دکمه «➕ ارسال بنر جدید» کلیک کنید.",
                        alert=True
                    )
                    return
                
                new_state = not ads.get("active", False)
                update_ads_settings(session_name, active=new_state)
                
                await event.answer(
                    "🟢 تبلیغ روشن شد!" if new_state else "🔴 تبلیغ خاموش شد",
                    alert=True
                )
                text, buttons = build_ads_menu(session_name)
                await event.edit(text, buttons=buttons)
                return
            
            # 🆕 حذف شد - adv_new دیگر نیاز نیست چون از URL استفاده می‌کنیم
            
            if d == "adv_delete":
                delete_ads_banner(session_name)
                await event.answer("🗑 بنر حذف شد", alert=True)
                text, buttons = build_ads_menu(session_name)
                await event.edit(text, buttons=buttons)
                return
            
            if d == "adv_reset_stats":
                reset_ads_stats(session_name)
                await event.answer("🔄 آمار ریست شد", alert=True)
                text, buttons = build_ads_menu(session_name)
                await event.edit(text, buttons=buttons)
                return
            
            if d == "enm_menu":
                from commands_db import get_enemies
                enemies = get_enemies(session_name)
                text = (
                    f"⚔️ **لیست دشمنان**\n\n"
                    f"👥 تعداد: `{len(enemies)}` نفر\n\n"
                    f"💡 **دستورات:**\n"
                    f"• `.دشمن @username`\n"
                    f"• `.حذف دشمن @username`\n"
                    f"• `.لیست دشمن`"
                )
                buttons = [[Button.inline("⬅️ بازگشت", data=b"back_main")]]
                await event.edit(text, buttons=buttons)
                return
            
            if d == "sil_menu":
                from commands_db import get_silences
                silences = get_silences(session_name)
                text = (
                    f"🤫 **لیست سکوت**\n\n"
                    f"👥 تعداد: `{len(silences)}` نفر\n\n"
                    f"💡 **دستورات:**\n"
                    f"• `.سکوت @username`\n"
                    f"• `.حذف سکوت @username`\n"
                    f"• `.لیست سکوت`"
                )
                buttons = [[Button.inline("⬅️ بازگشت", data=b"back_main")]]
                await event.edit(text, buttons=buttons)
                return
            
            if d == "spm_menu":
                text = (
                    "📨 **اسپم پیام**\n\n"
                    "**دستور:**\n`.اسپم (تعداد) (متن)`\n\n"
                    "**مثال:** `.اسپم 20 سلام`\n\n"
                    "⚠️ حداکثر: 1000 پیام"
                )
                buttons = [[Button.inline("⬅️ بازگشت", data=b"back_main")]]
                await event.edit(text, buttons=buttons)
                return
            
            if d == "del_menu":
                text = (
                    "🗑 **حذف پیام**\n\n"
                    "**دستور:**\n`.حذف پیام (تعداد)`\n\n"
                    "**مثال:** `.حذف پیام 20`\n\n"
                    "⚠️ حداکثر: 1000 پیام"
                )
                buttons = [[Button.inline("⬅️ بازگشت", data=b"back_main")]]
                await event.edit(text, buttons=buttons)
                return
            
            if d == "hlp_menu":
                text = (
                    "❓ **راهنمای کامل**\n\n"
                    "⏰ **ساعت:** از منوی مربوطه\n\n"
                    "📢 **تبچی:** منوی جداگانه دارد\n\n"
                    "⚔️ **دشمن:**\n"
                    "• `.دشمن @username`\n"
                    "• `.حذف دشمن @username`\n\n"
                    "🤫 **سکوت:**\n"
                    "• `.سکوت @username`\n"
                    "• `.حذف سکوت @username`\n\n"
                    "📨 **اسپم:** `.اسپم 20 سلام`\n\n"
                    "🗑 **حذف:** `.حذف پیام 20`\n\n"
                    "ℹ️ **اطلاعات:** `.info` • `.پینگ`"
                )
                buttons = [[Button.inline("⬅️ بازگشت", data=b"back_main")]]
                await event.edit(text, buttons=buttons)
                return
        
        except Exception as e:
            print(f"⚠️ inline callback: {e}")
            try:
                await event.answer(f"❌ خطا: {e}", alert=True)
            except:
                pass
    
    try:
        await bot.run_until_disconnected()
    except Exception as e:
        print(f"❌ inline bot قطع شد: {e}")
