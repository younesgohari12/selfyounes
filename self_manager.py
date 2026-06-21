# self_manager.py
import os
import asyncio
import glob
from pathlib import Path
from telethon import TelegramClient
from telethon.sessions import StringSession

BASE_DIR = Path(__file__).parent.resolve()
SESSIONS_DIR = str((BASE_DIR / 'sessions').resolve())

running_sessions = {}
session_locks = {}

os.makedirs(SESSIONS_DIR, exist_ok=True)

def get_run_self_function():
    from self import run_self
    return run_self

def get_session_string(session_name):
    txt_file = os.path.join(SESSIONS_DIR, f"{session_name}.txt")
    if os.path.exists(txt_file):
        try:
            with open(txt_file, 'r', encoding='utf-8') as f:
                return f.read().strip()
        except Exception as e:
            print(f"❌ خطا در خواندن {txt_file}: {e}")
    return None

async def migrate_old_session(session_name):
    from config import API_ID, API_HASH
    
    old_file = os.path.join(SESSIONS_DIR, f"{session_name}.session")
    if not os.path.exists(old_file):
        return None
    
    print(f"🔄 در حال migrate کردن سشن قدیمی: {session_name}")
    
    try:
        client = TelegramClient(old_file, API_ID, API_HASH)
        await client.connect()
        
        if not await client.is_user_authorized():
            await client.disconnect()
            print(f"❌ سشن قدیمی {session_name} معتبر نیست")
            try:
                os.remove(old_file)
            except:
                pass
            return None
        
        session_string = client.session.save()
        await client.disconnect()
        
        txt_file = os.path.join(SESSIONS_DIR, f"{session_name}.txt")
        with open(txt_file, 'w', encoding='utf-8') as f:
            f.write(session_string)
            f.flush()
            os.fsync(f.fileno())
        
        print(f"✅ migrate موفق: {session_name}.txt")
        
        await asyncio.sleep(1)
        try:
            os.remove(old_file)
            for suffix in ['-journal', '-wal', '-shm']:
                jf = old_file + suffix
                if os.path.exists(jf):
                    os.remove(jf)
            print(f"🧹 فایل قدیمی پاک شد: {session_name}.session")
        except Exception as e:
            print(f"⚠️ خطا در پاک کردن فایل قدیمی: {e}")
        
        return session_string
        
    except Exception as e:
        print(f"❌ خطا در migrate {session_name}: {e}")
        return None

async def start_session(session_name):
    run_self = get_run_self_function()
    
    if session_name not in session_locks:
        session_locks[session_name] = asyncio.Lock()
    
    if session_locks[session_name].locked():
        print(f"⚠️ سشن {session_name} در حال حاضر در حال اجراست")
        return False
    
    if session_name in running_sessions:
        print(f"🔄 لغو task قبلی سشن {session_name}")
        old_task = running_sessions[session_name]
        old_task.cancel()
        try:
            await old_task
        except asyncio.CancelledError:
            pass
        except Exception as e:
            print(f"⚠️ خطا در لغو task قبلی: {e}")
        
        await asyncio.sleep(1)
    
    session_string = get_session_string(session_name)
    if not session_string:
        session_string = await migrate_old_session(session_name)
    
    if not session_string:
        print(f"❌ سشن معتبر برای {session_name} یافت نشد")
        return False
    
    session_path = os.path.join(SESSIONS_DIR, session_name)
    task = asyncio.create_task(run_self(session_path, session_string))
    running_sessions[session_name] = task
    
    print(f"✅ سشن {session_name} با موفقیت استارت شد")
    return True

async def stop_session(session_name):
    if session_name in running_sessions:
        task = running_sessions[session_name]
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass
        except Exception as e:
            print(f"⚠️ خطا در توقف: {e}")
        del running_sessions[session_name]
        print(f"🛑 سشن {session_name} متوقف شد")
        await asyncio.sleep(1)
        return True
    return False

async def restart_session(session_name):
    print(f"🔄 ری‌استارت سشن {session_name}")
    await stop_session(session_name)
    await asyncio.sleep(1)
    return await start_session(session_name)

async def start_all_sessions():
    print(f"\n{'='*60}")
    print(f"🔍 بارگذاری همه سشن‌های موجود")
    print(f"{'='*60}")
    
    if not os.path.exists(SESSIONS_DIR):
        print(f"❌ پوشه {SESSIONS_DIR} وجود ندارد!")
        os.makedirs(SESSIONS_DIR, exist_ok=True)
        print(f"✅ پوشه ساخته شد")
        return []
    
    journal_files = glob.glob(os.path.join(SESSIONS_DIR, "*.session-journal"))
    for jf in journal_files:
        try:
            os.remove(jf)
        except:
            pass
    
    txt_files = [f[:-4] for f in os.listdir(SESSIONS_DIR) if f.endswith('.txt') and f.startswith('user_')]
    session_files = [f[:-8] for f in os.listdir(SESSIONS_DIR) if f.endswith('.session') and f.startswith('user_')]
    
    all_sessions = list(set(txt_files + session_files))
    
    print(f"✅ یافت شد: {len(txt_files)} StringSession")
    print(f"✅ یافت شد: {len(session_files)} قدیمی")
    print(f"📊 مجموع: {len(all_sessions)} سشن")
    
    try:
        from login_manager import login_states
    except:
        login_states = {}
    
    tasks = []
    for session_name in all_sessions:
        try:
            uid = int(session_name.replace('user_', ''))
            if uid in login_states:
                print(f"⏭️ سشن {session_name} در حال لاگین است، رد شد.")
                continue
        except ValueError:
            pass
            
        print(f"📁 استارت: {session_name}")
        
        success = await start_session(session_name)
        if success:
            tasks.append(running_sessions[session_name])
    
    print(f"\n{'='*60}")
    print(f"🚀 {len(tasks)} سلف فعال شد")
    print(f"{'='*60}\n")
    
    return tasks