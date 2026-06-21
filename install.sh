#!/bin/bash

# ========================================
# 🚀 Self Bot - Ultimate Auto Installer
# ========================================
# نصب‌کننده کامل با دانلود از GitHub
# Ubuntu 22.04 / 24.04
# ========================================

set -e

# رنگ‌ها
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
NC='\033[0m'

# تنظیمات - این URL را تغییر دهید
GITHUB_REPO="https://github.com/YOUR_USERNAME/self-bot.git"
PROJECT_DIR="/root/self-bot"
SERVICE_NAME="selfbot"

# توابع نمایش
print_header() {
    clear
    echo -e "${CYAN}"
    echo "╔═══════════════════════════════════════════════════════════╗"
    echo "║                                                           ║"
    echo "║   🤖  Self Bot - سیستم سلف‌بات چندکاربره تلگرام          ║"
    echo "║   📦  نسخه 8.0 - نصب‌کننده خودکار                         ║"
    echo "║                                                           ║"
    echo "╚═══════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

print_step() {
    echo -e "\n${YELLOW}╔═══════════════════════════════════════════════════════════╗${NC}"
    echo -e "${YELLOW}║  ▶ $1${NC}"
    echo -e "${YELLOW}╚═══════════════════════════════════════════════════════════╝${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# بررسی root
check_root() {
    if [ "$EUID" -ne 0 ]; then
        print_error "این اسکریپت نیاز به دسترسی root دارد"
        print_info "لطفاً با sudo اجرا کنید: sudo bash install.sh"
        exit 1
    fi
}

# بررسی اینترنت
check_internet() {
    print_info "بررسی اتصال اینترنت..."
    if ! ping -c 1 google.com &> /dev/null; then
        print_error "اتصال اینترنت برقرار نیست!"
        exit 1
    fi
    print_success "اتصال اینترنت برقرار است"
}

# بررسی Git
check_git() {
    if ! command -v git &> /dev/null; then
        print_warning "Git نصب نیست، در حال نصب..."
        apt install -y git
    fi
    print_success "Git آماده است"
}

# ========================================
# مرحله 1: نصب پیش‌نیازهای سیستم
# ========================================
install_system_deps() {
    print_step "نصب پیش‌نیازهای سیستم..."
    
    apt update -y
    apt upgrade -y
    
    apt install -y \
        python3 \
        python3-pip \
        python3-venv \
        python3-dev \
        build-essential \
        libssl-dev \
        libffi-dev \
        wget \
        curl \
        nano \
        htop \
        tmux \
        screen \
        jq \
        unzip \
        git \
        software-properties-common
    
    print_success "پیش‌نیازهای سیستم نصب شدند"
}

# ========================================
# مرحله 2: کلون پروژه از GitHub
# ========================================
clone_project() {
    print_step "دانلود پروژه از GitHub..."
    
    # اگر پوشه وجود دارد، بک‌آپ بگیر
    if [ -d "$PROJECT_DIR" ]; then
        BACKUP_DIR="${PROJECT_DIR}_backup_$(date +%Y%m%d_%H%M%S)"
        print_warning "پوشه قبلی وجود دارد"
        print_info "بک‌آپ گرفته می‌شود: $BACKUP_DIR"
        mv "$PROJECT_DIR" "$BACKUP_DIR"
        print_success "بک‌آپ ساخته شد"
    fi
    
    print_info "در حال کلون پروژه از: $GITHUB_REPO"
    
    if git clone "$GITHUB_REPO" "$PROJECT_DIR"; then
        print_success "پروژه با موفقیت کلون شد"
    else
        print_error "خطا در کلون پروژه!"
        print_info "لطفاً URL مخزن GitHub را در اسکریپت بررسی کنید"
        print_info "متغیر GITHUB_REPO را تغییر دهید"
        exit 1
    fi
    
    cd "$PROJECT_DIR"
    
    # بررسی فایل‌های اصلی
    REQUIRED_FILES=("main.py" "config.py" "bot.py" "self.py" "inline.py" "login_manager.py" "self_manager.py" "commands_db.py")
    
    for file in "${REQUIRED_FILES[@]}"; do
        if [ ! -f "$file" ]; then
            print_error "فایل ضروری یافت نشد: $file"
            print_info "لطفاً مطمئن شوید همه فایل‌ها در مخزن GitHub موجود هستند"
            exit 1
        fi
    done
    
    print_success "همه فایل‌های ضروری موجود هستند"
}

# ========================================
# مرحله 3: ساخت پوشه‌های مورد نیاز
# ========================================
create_directories() {
    print_step "ساخت پوشه‌های پروژه..."
    
    cd "$PROJECT_DIR"
    
    mkdir -p sessions
    mkdir -p logs
    mkdir -p db
    mkdir -p backups
    
    # تنظیم دسترسی‌ها
    chmod -R 755 "$PROJECT_DIR"
    
    print_success "پوشه‌ها ساخته شدند"
}

# ========================================
# مرحله 4: ساخت Virtual Environment
# ========================================
setup_venv() {
    print_step "ساخت محیط مجازی Python..."
    
    cd "$PROJECT_DIR"
    
    # حذف venv قبلی اگر وجود دارد
    if [ -d "venv" ]; then
        rm -rf venv
    fi
    
    python3 -m venv venv
    source venv/bin/activate
    
    pip install --upgrade pip setuptools wheel
    
    print_success "محیط مجازی ساخته شد"
}

# ========================================
# مرحله 5: نصب کتابخانه‌های Python
# ========================================
install_python_deps() {
    print_step "نصب کتابخانه‌های Python..."
    
    cd "$PROJECT_DIR"
    source venv/bin/activate
    
    if [ -f "requirements.txt" ]; then
        pip install -r requirements.txt
        print_success "کتابخانه‌ها از requirements.txt نصب شدند"
    else
        print_warning "requirements.txt یافت نشد، نصب دستی..."
        pip install telethon==1.36.0
        pip install cryptg==0.4.0
        pip install hachoir==3.3.0
        pip install Pillow==10.3.0
        pip install tzdata==2024.1
        pip install python-dotenv==1.0.1
        pip install requests==2.31.0
        pip install aiohttp==3.9.5
        pip install psutil==5.9.8
        print_success "کتابخانه‌ها نصب شدند"
    fi
}

# ========================================
# مرحله 6: پیکربندی توکن‌ها
# ========================================
configure_tokens() {
    print_step "پیکربندی API و توکن‌ها..."
    
    cd "$PROJECT_DIR"
    
    echo ""
    echo -e "${CYAN}╔═══════════════════════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}║  📝 لطفاً اطلاعات زیر را وارد کنید                       ║${NC}"
    echo -e "${CYAN}║  (اگر خالی بگذارید، مقادیر پیش‌فرض استفاده می‌شود)        ║${NC}"
    echo -e "${CYAN}╚═══════════════════════════════════════════════════════════╝${NC}"
    echo ""
    
    # خواندن مقادیر فعلی از config.py
    CURRENT_API_ID=$(grep "^API_ID = " config.py | cut -d'=' -f2 | tr -d ' ' || echo "25177467")
    CURRENT_API_HASH=$(grep "^API_HASH = " config.py | cut -d"'" -f2 || echo "d28f79d0afd5a6c3ed5d3efd3f61e56f")
    CURRENT_BOT_TOKEN=$(grep "^BOT_TOKEN = " config.py | cut -d"'" -f2 || echo "")
    CURRENT_INLINE_TOKEN=$(grep "^INLINE_BOT_TOKEN = " config.py | cut -d"'" -f2 || echo "")
    CURRENT_INLINE_USER=$(grep "^INLINE_USERNAME = " config.py | cut -d"'" -f2 || echo "helperproselfbot")
    
    echo -e "${YELLOW}1️⃣  API_ID (از my.telegram.org):${NC}"
    echo -e "   ${BLUE}فعلی: ${CURRENT_API_ID}${NC}"
    read -p "   جدید (Enter برای استفاده از فعلی): " api_id
    api_id=${api_id:-$CURRENT_API_ID}
    
    echo ""
    echo -e "${YELLOW}2️⃣  API_HASH (از my.telegram.org):${NC}"
    echo -e "   ${BLUE}فعلی: ${CURRENT_API_HASH}${NC}"
    read -p "   جدید (Enter برای استفاده از فعلی): " api_hash
    api_hash=${api_hash:-$CURRENT_API_HASH}
    
    echo ""
    echo -e "${YELLOW}3️⃣  BOT_TOKEN (از @BotFather - ربات اصلی):${NC}"
    echo -e "   ${BLUE}فعلی: ${CURRENT_BOT_TOKEN:0:20}...${NC}"
    read -p "   جدید (Enter برای استفاده از فعلی): " bot_token
    bot_token=${bot_token:-$CURRENT_BOT_TOKEN}
    
    echo ""
    echo -e "${YELLOW}4️⃣  INLINE_BOT_TOKEN (از @BotFather - ربات اینلاین):${NC}"
    echo -e "   ${BLUE}فعلی: ${CURRENT_INLINE_TOKEN:0:20}...${NC}"
    read -p "   جدید (Enter برای استفاده از فعلی): " inline_bot_token
    inline_bot_token=${inline_bot_token:-$CURRENT_INLINE_TOKEN}
    
    echo ""
    echo -e "${YELLOW}5️⃣  INLINE_USERNAME (username ربات اینلاین بدون @):${NC}"
    echo -e "   ${BLUE}فعلی: ${CURRENT_INLINE_USER}${NC}"
    read -p "   جدید (Enter برای استفاده از فعلی): " inline_username
    inline_username=${inline_username:-$CURRENT_INLINE_USER}
    
    # بک‌آپ از config.py اصلی
    cp config.py config.py.backup
    
    # بازنویسی config.py با مقادیر جدید
    sed -i "s|^API_ID = .*|API_ID = ${api_id}|" config.py
    sed -i "s|^API_HASH = .*|API_HASH = '${api_hash}'|" config.py
    sed -i "s|^BOT_TOKEN = .*|BOT_TOKEN = '${bot_token}'|" config.py
    sed -i "s|^INLINE_BOT_TOKEN = .*|INLINE_BOT_TOKEN = '${inline_bot_token}'|" config.py
    sed -i "s|^INLINE_USERNAME = .*|INLINE_USERNAME = '${inline_username}'|" config.py
    sed -i "s|^BOT_USERNAME = .*|BOT_USERNAME = '${inline_username}'|" config.py
    
    print_success "config.py پیکربندی شد"
}

# ========================================
# مرحله 7: ساخت systemd service
# ========================================
create_systemd_service() {
    print_step "ساخت سرویس systemd..."
    
    cat > /etc/systemd/system/${SERVICE_NAME}.service << SVCEOF
[Unit]
Description=Telegram Self Bot Service
After=network.target
Wants=network-online.target

[Service]
Type=simple
User=root
WorkingDirectory=${PROJECT_DIR}
ExecStart=${PROJECT_DIR}/venv/bin/python3 ${PROJECT_DIR}/main.py
Restart=always
RestartSec=10
StandardOutput=append:${PROJECT_DIR}/logs/bot.log
StandardError=append:${PROJECT_DIR}/logs/error.log
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
SVCEOF
    
    systemctl daemon-reload
    systemctl enable ${SERVICE_NAME}
    
    print_success "سرویس systemd ساخته و فعال شد"
}

# ========================================
# مرحله 8: ساخت اسکریپت‌های کنترلی
# ========================================
create_control_scripts() {
    print_step "ساخت اسکریپت‌های کنترلی..."
    
    cd "$PROJECT_DIR"
    
    # start.sh
    cat > start.sh << 'STARTEOF'
#!/bin/bash
cd /root/self-bot
source venv/bin/activate
echo "🟢 شروع ربات..."
python3 main.py
STARTEOF
    chmod +x start.sh
    
    # stop.sh
    cat > stop.sh << 'STOPEOF'
#!/bin/bash
echo "🔴 توقف ربات..."
sudo systemctl stop selfbot 2>/dev/null
pkill -f "python3 main.py" 2>/dev/null
echo "✅ ربات متوقف شد"
STOPEOF
    chmod +x stop.sh
    
    # restart.sh
    cat > restart.sh << 'RESTARTEOF'
#!/bin/bash
echo "🔄 ری‌استارت ربات..."
sudo systemctl restart selfbot
echo "✅ ربات ری‌استارت شد"
RESTARTEOF
    chmod +x restart.sh
    
    # logs.sh
    cat > logs.sh << 'LOGSEOF'
#!/bin/bash
echo "📋 نمایش لاگ‌ها (Ctrl+C برای خروج)..."
tail -f /root/self-bot/logs/bot.log
LOGSEOF
    chmod +x logs.sh
    
    # status.sh
    cat > status.sh << 'STATUSEOF'
#!/bin/bash
echo "📊 وضعیت ربات:"
sudo systemctl status selfbot --no-pager
STATUSEOF
    chmod +x status.sh
    
    # backup.sh
    cat > backup.sh << 'BACKUPEOF'
#!/bin/bash
cd /root/self-bot
BACKUP_NAME="backups/self-bot-backup-$(date +%Y%m%d_%H%M%S).tar.gz"
tar -czvf "$BACKUP_NAME" \
    --exclude='venv' \
    --exclude='logs' \
    --exclude='backups' \
    --exclude='__pycache__' \
    --exclude='.git' \
    .
echo "💾 بک‌آپ ساخته شد: $BACKUP_NAME"
BACKUPEOF
    chmod +x backup.sh
    
    # update.sh
    cat > update.sh << 'UPDATEEOF'
#!/bin/bash
cd /root/self-bot
echo "🔄 در حال آپدیت از GitHub..."
git pull origin main
source venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart selfbot
echo "✅ آپدیت کامل شد"
UPDATEEOF
    chmod +x update.sh
    
    # reset.sh
    cat > reset.sh << 'RESETEOF'
#!/bin/bash
echo "⚠️  این عملیات همه سشن‌ها و تنظیمات را پاک می‌کند!"
read -p "ادامه می‌دهید؟ (yes/no): " confirm
if [ "$confirm" = "yes" ]; then
    sudo systemctl stop selfbot
    rm -rf sessions/*
    rm -f commands.json
    rm -f db/*
    echo "✅ ریست کامل شد"
else
    echo "❌ لغو شد"
fi
RESETEOF
    chmod +x reset.sh
    
    print_success "اسکریپت‌های کنترلی ساخته شدند"
}

# ========================================
# مرحله 9: تنظیم فایروال
# ========================================
setup_firewall() {
    print_step "تنظیم فایروال..."
    
    if command -v ufw &> /dev/null; then
        ufw allow OpenSSH
        ufw allow 443/tcp
        ufw allow 80/tcp
        ufw --force enable
        print_success "فایروال تنظیم شد"
    else
        print_warning "ufw نصب نیست، از فایروال رد می‌شویم"
    fi
}

# ========================================
# مرحله 10: بهینه‌سازی سیستم
# ========================================
optimize_system() {
    print_step "بهینه‌سازی سیستم..."
    
    # افزایش محدودیت فایل‌های باز
    echo "* soft nofile 65535" >> /etc/security/limits.conf
    echo "* hard nofile 65535" >> /etc/security/limits.conf
    
    # تنظیم swap (اگر وجود ندارد)
    if [ ! -f /swapfile ]; then
        fallocate -l 2G /swapfile 2>/dev/null || true
        if [ -f /swapfile ]; then
            chmod 600 /swapfile
            mkswap /swapfile
            swapon /swapfile
            echo '/swapfile none swap sw 0 0' >> /etc/fstab
            print_success "Swap 2GB ساخته شد"
        fi
    fi
    
    print_success "بهینه‌سازی کامل شد"
}

# ========================================
# مرحله 11: تست نصب
# ========================================
test_installation() {
    print_step "تست نصب..."
    
    cd "$PROJECT_DIR"
    source venv/bin/activate
    
    # تست import های اصلی
    python3 -c "import telethon; print('✅ Telethon OK')" || print_error "Telethon نصب نیست"
    python3 -c "from telethon.sessions import StringSession; print('✅ StringSession OK')" || print_error "StringSession مشکل دارد"
    python3 -c "import config; print('✅ Config OK')" || print_error "Config مشکل دارد"
    
    print_success "تست‌ها پاس شدند"
}

# ========================================
# مرحله 12: شروع ربات
# ========================================
start_bot() {
    print_step "شروع ربات..."
    
    echo ""
    echo -e "${CYAN}╔═══════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║  🎉 نصب با موفقیت کامل شد!                                ║${NC}"
    echo -e "${CYAN}╚═══════════════════════════════════════════════════════════╝${NC}"
    echo ""
    
    echo -e "${YELLOW}📂 مسیر پروژه:${NC} $PROJECT_DIR"
    echo -e "${YELLOW}📋 لاگ‌ها:${NC} $PROJECT_DIR/logs/"
    echo -e "${YELLOW}💾 بک‌آپ‌ها:${NC} $PROJECT_DIR/backups/"
    echo ""
    
    echo -e "${CYAN}╔═══════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║  🎯 دستورات systemd:                                      ║${NC}"
    echo -e "${CYAN}╚═══════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo "  🟢 شروع:      sudo systemctl start $SERVICE_NAME"
    echo "  🔴 توقف:      sudo systemctl stop $SERVICE_NAME"
    echo "  🔄 ری‌استارت:  sudo systemctl restart $SERVICE_NAME"
    echo "  📊 وضعیت:     sudo systemctl status $SERVICE_NAME"
    echo "  📋 لاگ زنده:  sudo journalctl -u $SERVICE_NAME -f"
    echo ""
    
    echo -e "${CYAN}╔═══════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║  💡 دستورات میانبر (در پوشه پروژه):                      ║${NC}"
    echo -e "${CYAN}╚═══════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo "  cd $PROJECT_DIR"
    echo "  ./start.sh      - شروع دستی"
    echo "  ./stop.sh       - توقف"
    echo "  ./restart.sh    - ری‌استارت"
    echo "  ./logs.sh       - مشاهده لاگ‌ها"
    echo "  ./status.sh     - بررسی وضعیت"
    echo "  ./backup.sh     - ساخت بک‌آپ"
    echo "  ./update.sh     - آپدیت از GitHub"
    echo "  ./reset.sh      - ریست کامل"
    echo ""
    
    echo -e "${CYAN}╔═══════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║  📖 راهنمای استفاده:                                      ║${NC}"
    echo -e "${CYAN}╚═══════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo "  1️⃣  در ربات اصلی: /install"
    echo "  2️⃣  شماره تلفن را وارد کنید"
    echo "  3️⃣  کد 5 رقمی را وارد کنید"
    echo "  4️⃣  در هر چتی: .پنل"
    echo ""
    
    echo ""
    read -p "آیا می‌خواهید ربات را الان شروع کنید؟ (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        sudo systemctl start $SERVICE_NAME
        print_success "ربات شروع شد!"
        echo ""
        echo -e "${YELLOW}برای دیدن لاگ‌ها:${NC}"
        echo "  sudo journalctl -u $SERVICE_NAME -f"
        echo ""
        echo -e "${YELLOW}یا:${NC}"
        echo "  cd $PROJECT_DIR && ./logs.sh"
    else
        print_info "ربات شروع نشد. برای شروع:"
        echo "  sudo systemctl start $SERVICE_NAME"
    fi
}

# ========================================
# مرحله 13: نکات امنیتی
# ========================================
security_tips() {
    echo ""
    echo -e "${CYAN}╔═══════════════════════════════════════════════════════════╗${NC}"
    echo -e "${YELLOW}║  🔐 نکات امنیتی مهم:                                      ║${NC}"
    echo -e "${CYAN}╚═══════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "${YELLOW}1. حذف فایل install.sh:${NC}"
    echo "   rm ~/install.sh"
    echo ""
    echo -e "${YELLOW}2. تغییر پورت SSH (توصیه شده):${NC}"
    echo "   nano /etc/ssh/sshd_config"
    echo "   Port 22 را به مثلاً Port 2222 تغییر دهید"
    echo "   sudo systemctl restart ssh"
    echo ""
    echo -e "${YELLOW}3. نصب fail2ban:${NC}"
    echo "   sudo apt install fail2ban"
    echo "   sudo systemctl enable fail2ban"
    echo ""
    echo -e "${YELLOW}4. فعال کردن Inline Mode در BotFather:${NC}"
    echo "   /setinline → ربات اینلاین را انتخاب → پیام placeholder"
    echo ""
}

# ========================================
# تابع اصلی
# ========================================
main() {
    print_header
    check_root
    check_internet
    install_system_deps
    check_git
    clone_project
    create_directories
    setup_venv
    install_python_deps
    configure_tokens
    create_systemd_service
    create_control_scripts
    setup_firewall
    optimize_system
    test_installation
    start_bot
    security_tips
    
    echo ""
    echo -e "${GREEN}╔═══════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║                                                           ║${NC}"
    echo -e "${GREEN}║   ✨ نصب کامل شد! موفق باشید ✨                          ║${NC}"
    echo -e "${GREEN}║                                                           ║${NC}"
    echo -e "${GREEN}╚═══════════════════════════════════════════════════════════╝${NC}"
    echo ""
}

# اجرای اصلی
main "$@"
