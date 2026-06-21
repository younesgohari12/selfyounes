# main.py
import os
import asyncio
from pathlib import Path
from bot import run_bot
from inline import run_inline
from self_manager import start_all_sessions

BASE_DIR = Path(__file__).parent.resolve()
SESSIONS_DIR = str((BASE_DIR / 'sessions').resolve())

os.makedirs(SESSIONS_DIR, exist_ok=True)

async def main():
    print("="*60)
    print("🚀 سیستم سلف چندکاربره")
    print("="*60)
    print(f"📁 SESSIONS_DIR: {SESSIONS_DIR}")
    print("="*60)
    
    session_tasks = await start_all_sessions()
    
    bot_task = asyncio.create_task(run_bot())
    inline_task = asyncio.create_task(run_inline())
    
    print("\n✅ همه task ها ساخته شدند:")
    print(f"   - bot_task (ربات اصلی)")
    print(f"   - inline_task (ربات اینلاین)")
    print(f"   - {len(session_tasks)} سشن سلف")
    print("\n🎯 شروع حلقه اصلی...\n")
    
    try:
        all_tasks = [bot_task, inline_task] + session_tasks
        await asyncio.gather(*all_tasks)
    except asyncio.CancelledError:
        pass

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 متوقف شد")