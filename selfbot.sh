#!/usr/bin/env bash
set -e

# ========================================
# 🤖 Self Bot - Professional Installer
# ========================================
# Similar to PasarGuard installation script
# Ubuntu 20.04 / 22.04 / 24.04
# ========================================

INSTALL_DIR="/opt"
APP_NAME="selfbot"
APP_DIR="$INSTALL_DIR/$APP_NAME"
DATA_DIR="/var/lib/$APP_NAME"
LOGS_DIR="$APP_DIR/logs"
SESSIONS_DIR="$APP_DIR/sessions"
ENV_FILE="$APP_DIR/.env"
SERVICE_NAME="$APP_NAME"

GITHUB_REPO="https://github.com/YOUR_USERNAME/self-bot.git"
SCRIPT_URL="https://raw.githubusercontent.com/YOUR_USERNAME/self-bot/main/selfbot.sh"

# رنگ‌ها
colorized_echo() {
    local color=$1
    local text=$2
    case $color in
        "red")    printf "\e[91m${text}\e[0m\n" ;;
        "green")  printf "\e[92m${text}\e[0m\n" ;;
        "yellow") printf "\e[93m${text}\e[0m\n" ;;
        "blue")   printf "\e[94m${text}\e[0m\n" ;;
        "magenta") printf "\e[95m${text}\e[0m\n" ;;
        "cyan")   printf "\e[96m${text}\e[0m\n" ;;
        *)        echo "${text}" ;;
    esac
}

# بررسی root
check_running_as_root() {
    if [ "$(id -u)" != "0" ]; then
        colorized_echo red "❌ This command must be run as root."
        colorized_echo yellow "💡 Use: sudo bash -c \"\$(curl -fsSL $SCRIPT_URL)\" @ install"
        exit 1
    fi
}

# تشخیص سیستم عامل
detect_os() {
    if [ -f /etc/lsb-release ]; then
        OS=$(lsb_release -si)
    elif [ -f /etc/os-release ]; then
        OS=$(awk -F= '/^NAME/{print $2}' /etc/os-release | tr -d '"')
    elif [ -f /etc/redhat-release ]; then
        OS=$(cat /etc/redhat-release | awk '{print $1}')
    else
        colorized_echo red "❌ Unsupported operating system"
        exit 1
    fi
}

# آپدیت package manager
detect_and_update_package_manager() {
    colorized_echo blue "📦 Updating package manager..."
    if [[ "$OS" == "Ubuntu"* ]] || [[ "$OS" == "Debian"* ]]; then
        PKG_MANAGER="apt-get"
        $PKG_MANAGER update -y
    elif [[ "$OS" == "CentOS"* ]] || [[ "$OS" == "AlmaLinux"* ]]; then
        PKG_MANAGER="yum"
        $PKG_MANAGER update -y
        $PKG_MANAGER install -y epel-release
    elif [ "$OS" == "Fedora"* ]; then
        PKG_MANAGER="dnf"
        $PKG_MANAGER update -y
    else
        colorized_echo red "❌ Unsupported operating system"
        exit 1
    fi
}

# نصب پکیج
install_package() {
    if [ -z $PKG_MANAGER ]; then
        detect_and_update_package_manager
    fi
    PACKAGE=$1
    colorized_echo blue "📦 Installing $PACKAGE..."
    if [[ "$OS" == "Ubuntu"* ]] || [[ "$OS" == "Debian"* ]]; then
        $PKG_MANAGER -y install "$PACKAGE"
    elif [[ "$OS" == "CentOS"* ]] || [[ "$OS" == "AlmaLinux"* ]]; then
        $PKG_MANAGER install -y "$PACKAGE"
    elif [ "$OS" == "Fedora"* ]; then
        $PKG_MANAGER install -y "$PACKAGE"
    fi
}

# بررسی نصب بودن
is_installed() {
    if [ -d "$APP_DIR" ]; then
        return 0
    else
        return 1
    fi
}

# نصب پیش‌نیازها
install_dependencies() {
    colorized_echo blue "╔══════════════════════════════════════════╗"
    colorized_echo blue "║   📦 Installing System Dependencies      ║"
    colorized_echo blue "╚══════════════════════════════════════════╝"
    
    detect_os
    detect_and_update_package_manager
    
    install_package python3
    install_package python3-pip
    install_package python3-venv
    install_package python3-dev
    install_package build-essential
    install_package libssl-dev
    install_package libffi-dev
    install_package git
    install_package curl
    install_package wget
    install_package nano
    install_package htop
    install_package tmux
    install_package jq
    
    colorized_echo green "✅ System dependencies installed successfully"
}

# کلون پروژه
clone_project() {
    colorized_echo blue "╔══════════════════════════════════════════╗"
    colorized_echo blue "║   📥 Downloading Project from GitHub     ║"
    colorized_echo blue "╚══════════════════════════════════════════╝"
    
    # بک‌آپ اگر وجود داشت
    if [ -d "$APP_DIR" ]; then
        BACKUP_DIR="${APP_DIR}_backup_$(date +%Y%m%d_%H%M%S)"
        colorized_echo yellow "⚠️  Existing installation found"
        colorized_echo blue "📦 Creating backup: $BACKUP_DIR"
        mv "$APP_DIR" "$BACKUP_DIR"
    fi
    
    # ساخت پوشه‌ها
    mkdir -p "$APP_DIR"
    mkdir -p "$DATA_DIR"
    mkdir -p "$LOGS_DIR"
    mkdir -p "$SESSIONS_DIR"
    mkdir -p "$APP_DIR/backups"
    
    # کلون پروژه
    colorized_echo blue "📥 Cloning from: $GITHUB_REPO"
    if git clone "$GITHUB_REPO" "$APP_DIR"; then
        colorized_echo green "✅ Project cloned successfully"
    else
        colorized_echo red "❌ Failed to clone repository"
        colorized_echo yellow "💡 Please check GITHUB_REPO URL in script"
        exit 1
    fi
    
    cd "$APP_DIR"
    
    # بررسی فایل‌های ضروری
    REQUIRED_FILES=("main.py" "config.py" "bot.py" "self.py" "inline.py" "login_manager.py" "self_manager.py" "commands_db.py" "requirements.txt")
    
    for file in "${REQUIRED_FILES[@]}"; do
        if [ ! -f "$file" ]; then
            colorized_echo red "❌ Required file not found: $file"
            exit 1
        fi
    done
    
    colorized_echo green "✅ All required files found"
}

# ساخت virtual environment
setup_venv() {
    colorized_echo blue "╔══════════════════════════════════════════╗"
    colorized_echo blue "║   🐍 Setting up Python Environment       ║"
    colorized_echo blue "╚══════════════════════════════════════════╝"
    
    cd "$APP_DIR"
    
    if [ -d "venv" ]; then
        rm -rf venv
    fi
    
    python3 -m venv venv
    source venv/bin/activate
    
    pip install --upgrade pip setuptools wheel
    
    colorized_echo blue "📦 Installing Python packages..."
    pip install -r requirements.txt
    
    colorized_echo green "✅ Python environment setup complete"
}

# پیکربندی توکن‌ها
configure_tokens() {
    colorized_echo blue "╔══════════════════════════════════════════╗"
    colorized_echo blue "║   ⚙️  Configuring API Tokens              ║"
    colorized_echo blue "╚══════════════════════════════════════════╝"
    
    cd "$APP_DIR"
    
    echo ""
    colorized_echo cyan "Please enter your API credentials:"
    colorized_echo yellow "(Press Enter to use default values)"
    echo ""
    
    # مقادیر فعلی
    CURRENT_API_ID=$(grep "^API_ID = " config.py | cut -d'=' -f2 | tr -d ' ' || echo "25177467")
    CURRENT_API_HASH=$(grep "^API_HASH = " config.py | cut -d"'" -f2 || echo "d28f79d0afd5a6c3ed5d3efd3f61e56f")
    CURRENT_BOT_TOKEN=$(grep "^BOT_TOKEN = " config.py | cut -d"'" -f2 || echo "")
    CURRENT_INLINE_TOKEN=$(grep "^INLINE_BOT_TOKEN = " config.py | cut -d"'" -f2 || echo "")
    CURRENT_INLINE_USER=$(grep "^INLINE_USERNAME = " config.py | cut -d"'" -f2 || echo "helperproselfbot")
    
    echo -e "\e[93m1️⃣  API_ID (from my.telegram.org):\e[0m"
    echo -e "   \e[94mCurrent: ${CURRENT_API_ID}\e[0m"
    read -p "   New (Enter for current): " api_id
    api_id=${api_id:-$CURRENT_API_ID}
    
    echo -e "\n\e[93m2️⃣  API_HASH (from my.telegram.org):\e[0m"
    echo -e "   \e[94mCurrent: ${CURRENT_API_HASH}\e[0m"
    read -p "   New (Enter for current): " api_hash
    api_hash=${api_hash:-$CURRENT_API_HASH}
    
    echo -e "\n\e[93m3️⃣  BOT_TOKEN (from @BotFather - main bot):\e[0m"
    echo -e "   \e[94mCurrent: ${CURRENT_BOT_TOKEN:0:30}...\e[0m"
    read -p "   New (Enter for current): " bot_token
    bot_token=${bot_token:-$CURRENT_BOT_TOKEN}
    
    echo -e "\n\e[93m4️⃣  INLINE_BOT_TOKEN (from @BotFather - inline bot):\e[0m"
    echo -e "   \e[94mCurrent: ${CURRENT_INLINE_TOKEN:0:30}...\e[0m"
    read -p "   New (Enter for current): " inline_bot_token
    inline_bot_token=${inline_bot_token:-$CURRENT_INLINE_TOKEN}
    
    echo -e "\n\e[93m5️⃣  INLINE_USERNAME (inline bot username without @):\e[0m"
    echo -e "   \e[94mCurrent: ${CURRENT_INLINE_USER}\e[0m"
    read -p "   New (Enter for current): " inline_username
    inline_username=${inline_username:-$CURRENT_INLINE_USER}
    
    # بک‌آپ
    cp config.py config.py.backup
    
    # بازنویسی
    sed -i "s|^API_ID = .*|API_ID = ${api_id}|" config.py
    sed -i "s|^API_HASH = .*|API_HASH = '${api_hash}'|" config.py
    sed -i "s|^BOT_TOKEN = .*|BOT_TOKEN = '${bot_token}'|" config.py
    sed -i "s|^INLINE_BOT_TOKEN = .*|INLINE_BOT_TOKEN = '${inline_bot_token}'|" config.py
    sed -i "s|^INLINE_USERNAME = .*|INLINE_USERNAME = '${inline_username}'|" config.py
    sed -i "s|^BOT_USERNAME = .*|BOT_USERNAME = '${inline_username}'|" config.py
    
    # ساخت فایل .env
    cat > .env << EOF
API_ID=${api_id}
API_HASH=${api_hash}
BOT_TOKEN=${bot_token}
INLINE_BOT_TOKEN=${inline_bot_token}
INLINE_USERNAME=${inline_username}
SESSIONS_DIR=${SESSIONS_DIR}
EOF
    
    colorized_echo green "✅ Configuration saved"
}

# ساخت systemd service
create_systemd_service() {
    colorized_echo blue "╔══════════════════════════════════════════╗"
    colorized_echo blue "║   🔧 Creating Systemd Service            ║"
    colorized_echo blue "╚══════════════════════════════════════════╝"
    
    cat > /etc/systemd/system/${SERVICE_NAME}.service << EOF
[Unit]
Description=Telegram Self Bot Service
After=network.target
Wants=network-online.target

[Service]
Type=simple
User=root
WorkingDirectory=${APP_DIR}
EnvironmentFile=${APP_DIR}/.env
ExecStart=${APP_DIR}/venv/bin/python3 ${APP_DIR}/main.py
Restart=always
RestartSec=10
StandardOutput=append:${LOGS_DIR}/bot.log
StandardError=append:${LOGS_DIR}/error.log
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
EOF
    
    systemctl daemon-reload
    systemctl enable ${SERVICE_NAME}
    
    colorized_echo green "✅ Systemd service created and enabled"
}

# نصب bash completion
install_completion() {
    local completion_dir="/etc/bash_completion.d"
    local completion_file="$completion_dir/$APP_NAME"
    mkdir -p "$completion_dir"
    
    cat > "$completion_file" << 'EOF'
_selfbot_completions()
{
    local cur cmds
    COMPREPLY=()
    cur="${COMP_WORDS[COMP_CWORD]}"
    cmds="up down restart status logs update uninstall install install-script backup edit edit-config help"
    COMPREPLY=( $(compgen -W "$cmds" -- "$cur") )
    return 0
}
complete -F _selfbot_completions selfbot
EOF
    
    colorized_echo green "✅ Bash completion installed"
}

# نصب اسکریپت اصلی
install_script() {
    colorized_echo blue "📥 Installing selfbot command..."
    curl -sSL "$SCRIPT_URL" | install -m 755 /dev/stdin /usr/local/bin/selfbot
    colorized_echo green "✅ selfbot command installed"
}

# ========================================
# دستور install
# ========================================
install_command() {
    check_running_as_root
    
    echo ""
    colorized_echo cyan "╔══════════════════════════════════════════════════╗"
    colorized_echo cyan "║                                                  ║"
    colorized_echo cyan "║   🤖  Self Bot - Professional Installer         ║"
    colorized_echo cyan "║   📦  Version 8.0 - Auto Setup                  ║"
    colorized_echo cyan "║                                                  ║"
    colorized_echo cyan "╚══════════════════════════════════════════════════╝"
    echo ""
    
    # بررسی نصب قبلی
    if is_installed; then
        colorized_echo yellow "⚠️  Self Bot is already installed at $APP_DIR"
        read -p "Do you want to override? (y/n): "
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            colorized_echo red "❌ Installation aborted"
            exit 1
        fi
    fi
    
    # نصب مراحل
    install_dependencies
    clone_project
    setup_venv
    configure_tokens
    create_systemd_service
    install_script
    install_completion
    
    # شروع سرویس
    echo ""
    read -p "🚀 Start the bot now? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        up_command
    fi
    
    # نمایش اطلاعات نهایی
    echo ""
    colorized_echo green "╔══════════════════════════════════════════════════╗"
    colorized_echo green "║   🎉 Installation completed successfully!       ║"
    colorized_echo green "╚══════════════════════════════════════════════════╝"
    echo ""
    colorized_echo cyan "📂 Installation directory: $APP_DIR"
    colorized_echo cyan "📋 Logs directory: $LOGS_DIR"
    colorized_echo cyan "💾 Sessions directory: $SESSIONS_DIR"
    echo ""
    colorized_echo yellow "📖 Available commands:"
    echo ""
    colorized_echo green "  selfbot up         🟢 Start the bot"
    colorized_echo green "  selfbot down       🔴 Stop the bot"
    colorized_echo green "  selfbot restart    🔄 Restart the bot"
    colorized_echo green "  selfbot status     📊 Check status"
    colorized_echo green "  selfbot logs       📋 View logs"
    colorized_echo green "  selfbot update     🔄 Update from GitHub"
    colorized_echo green "  selfbot backup     💾 Create backup"
    colorized_echo green "  selfbot edit       ✏️  Edit config"
    colorized_echo green "  selfbot uninstall  🗑️  Uninstall"
    colorized_echo green "  selfbot help       ❓ Show help"
    echo ""
    colorized_echo magenta "💡 Don't forget to enable Inline Mode in @BotFather:"
    colorized_echo magenta "   /setinline → select inline bot → enter placeholder"
    echo ""
}

# ========================================
# دستور up (شروع)
# ========================================
up_command() {
    check_running_as_root
    
    if ! is_installed; then
        colorized_echo red "❌ Self Bot is not installed!"
        exit 1
    fi
    
    colorized_echo green "🟢 Starting Self Bot..."
    systemctl start ${SERVICE_NAME}
    
    sleep 2
    
    if systemctl is-active --quiet ${SERVICE_NAME}; then
        colorized_echo green "✅ Self Bot is running"
        colorized_echo cyan "📋 View logs: selfbot logs"
    else
        colorized_echo red "❌ Failed to start Self Bot"
        colorized_echo yellow "💡 Check logs: selfbot logs"
    fi
}

# ========================================
# دستور down (توقف)
# ========================================
down_command() {
    check_running_as_root
    
    if ! is_installed; then
        colorized_echo red "❌ Self Bot is not installed!"
        exit 1
    fi
    
    colorized_echo yellow "🔴 Stopping Self Bot..."
    systemctl stop ${SERVICE_NAME}
    colorized_echo green "✅ Self Bot stopped"
}

# ========================================
# دستور restart
# ========================================
restart_command() {
    check_running_as_root
    
    if ! is_installed; then
        colorized_echo red "❌ Self Bot is not installed!"
        exit 1
    fi
    
    colorized_echo blue "🔄 Restarting Self Bot..."
    systemctl restart ${SERVICE_NAME}
    sleep 2
    
    if systemctl is-active --quiet ${SERVICE_NAME}; then
        colorized_echo green "✅ Self Bot restarted successfully"
    else
        colorized_echo red "❌ Failed to restart"
    fi
}

# ========================================
# دستور status
# ========================================
status_command() {
    if ! is_installed; then
        colorized_echo red "❌ Self Bot is not installed!"
        exit 1
    fi
    
    echo ""
    colorized_echo cyan "╔══════════════════════════════════════════╗"
    colorized_echo cyan "║   📊 Self Bot Status                     ║"
    colorized_echo cyan "╚══════════════════════════════════════════╝"
    echo ""
    
    if systemctl is-active --quiet ${SERVICE_NAME}; then
        colorized_echo green "Status: 🟢 Running"
    else
        colorized_echo red "Status: 🔴 Stopped"
    fi
    
    echo ""
    colorized_echo blue "Service details:"
    systemctl status ${SERVICE_NAME} --no-pager -l | head -20
}

# ========================================
# دستور logs
# ========================================
logs_command() {
    if ! is_installed; then
        colorized_echo red "❌ Self Bot is not installed!"
        exit 1
    fi
    
    local no_follow=false
    
    while [[ "$#" -gt 0 ]]; do
        case "$1" in
            -n|--no-follow) no_follow=true ;;
            -h|--help) 
                echo "Usage: selfbot logs [-n|--no-follow]"
                exit 0
                ;;
        esac
        shift
    done
    
    colorized_echo cyan "📋 Showing logs..."
    echo ""
    
    if [ "$no_follow" = true ]; then
        tail -100 "$LOGS_DIR/bot.log"
    else
        colorized_echo yellow "Press Ctrl+C to exit"
        tail -f "$LOGS_DIR/bot.log"
    fi
}

# ========================================
# دستور update
# ========================================
update_command() {
    check_running_as_root
    
    if ! is_installed; then
        colorized_echo red "❌ Self Bot is not installed!"
        exit 1
    fi
    
    colorized_echo blue "╔══════════════════════════════════════════╗"
    colorized_echo blue "║   🔄 Updating Self Bot                   ║"
    colorized_echo blue "╚══════════════════════════════════════════╝"
    
    cd "$APP_DIR"
    
    # بک‌آپ config
    if [ -f "config.py" ]; then
        cp config.py config.py.backup_$(date +%Y%m%d_%H%M%S)
    fi
    
    # Pull از GitHub
    colorized_echo blue "📥 Pulling latest version..."
    if git pull origin main; then
        colorized_echo green "✅ Code updated"
    else
        colorized_echo red "❌ Failed to update"
        exit 1
    fi
    
    # نصب پکیج‌های جدید
    if [ -f "requirements.txt" ]; then
        source venv/bin/activate
        pip install -r requirements.txt
    fi
    
    # ری‌استارت
    colorized_echo blue "🔄 Restarting service..."
    systemctl restart ${SERVICE_NAME}
    
    colorized_echo green "✅ Self Bot updated successfully"
}

# ========================================
# دستور uninstall
# ========================================
uninstall_command() {
    check_running_as_root
    
    if ! is_installed; then
        colorized_echo red "❌ Self Bot is not installed!"
        exit 1
    fi
    
    colorized_echo red "╔══════════════════════════════════════════╗"
    colorized_echo red "║   🗑️  Uninstalling Self Bot               ║"
    colorized_echo red "╚══════════════════════════════════════════╝"
    echo ""
    
    read -p "⚠️  Do you really want to uninstall? (y/n): "
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        colorized_echo yellow "❌ Aborted"
        exit 1
    fi
    
    # توقف سرویس
    systemctl stop ${SERVICE_NAME} 2>/dev/null || true
    systemctl disable ${SERVICE_NAME} 2>/dev/null || true
    
    # حذف سرویس
    rm -f /etc/systemd/system/${SERVICE_NAME}.service
    systemctl daemon-reload
    
    # حذف اسکریپت
    rm -f /usr/local/bin/selfbot
    
    # حذف completion
    rm -f /etc/bash_completion.d/$APP_NAME
    
    # پرسش برای حذف داده‌ها
    read -p "🗑️  Remove all data (sessions, configs)? (y/n): "
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        rm -rf "$APP_DIR"
        rm -rf "$DATA_DIR"
        colorized_echo green "✅ All data removed"
    else
        colorized_echo yellow "💾 Data preserved at: $APP_DIR"
    fi
    
    colorized_echo green "✅ Self Bot uninstalled successfully"
}

# ========================================
# دستور backup
# ========================================
backup_command() {
    if ! is_installed; then
        colorized_echo red "❌ Self Bot is not installed!"
        exit 1
    fi
    
    colorized_echo blue "💾 Creating backup..."
    
    BACKUP_NAME="selfbot-backup-$(date +%Y%m%d_%H%M%S).tar.gz"
    BACKUP_PATH="$APP_DIR/backups/$BACKUP_NAME"
    
    cd "$APP_DIR"
    tar -czvf "$BACKUP_PATH" \
        --exclude='venv' \
        --exclude='logs' \
        --exclude='backups' \
        --exclude='__pycache__' \
        --exclude='.git' \
        .
    
    colorized_echo green "✅ Backup created: $BACKUP_PATH"
    colorized_echo cyan "📦 Size: $(du -h "$BACKUP_PATH" | cut -f1)"
}

# ========================================
# دستور edit
# ========================================
edit_command() {
    if ! is_installed; then
        colorized_echo red "❌ Self Bot is not installed!"
        exit 1
    fi
    
    if [ -z "$EDITOR" ]; then
        if command -v nano >/dev/null 2>&1; then
            EDITOR="nano"
        else
            EDITOR="vi"
        fi
    fi
    
    $EDITOR "$APP_DIR/config.py"
    
    read -p "🔄 Restart service to apply changes? (y/n): "
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        restart_command
    fi
}

# ========================================
# دستور help
# ========================================
usage() {
    echo ""
    colorized_echo cyan "╔══════════════════════════════════════════════════╗"
    colorized_echo cyan "║                                                  ║"
    colorized_echo cyan "║   🤖  Self Bot - Help                            ║"
    colorized_echo cyan "║                                                  ║"
    colorized_echo cyan "╚══════════════════════════════════════════════════╝"
    echo ""
    colorized_echo yellow "Usage: selfbot [command]"
    echo ""
    colorized_echo cyan "Commands:"
    colorized_echo green "  install         📦 Install Self Bot"
    colorized_echo green "  up              🟢 Start services"
    colorized_echo green "  down            🔴 Stop services"
    colorized_echo green "  restart         🔄 Restart services"
    colorized_echo green "  status          📊 Show status"
    colorized_echo green "  logs            📋 Show logs (use -n for no follow)"
    colorized_echo green "  update          🔄 Update from GitHub"
    colorized_echo green "  backup          💾 Create backup"
    colorized_echo green "  edit            ✏️  Edit config.py"
    colorized_echo green "  uninstall       🗑️  Uninstall Self Bot"
    colorized_echo green "  help            ❓ Show this help"
    echo ""
    colorized_echo cyan "Directories:"
    colorized_echo magenta "  App: $APP_DIR"
    colorized_echo magenta "  Data: $DATA_DIR"
    colorized_echo magenta "  Logs: $LOGS_DIR"
    colorized_echo magenta "  Sessions: $SESSIONS_DIR"
    echo ""
    colorized_echo cyan "Examples:"
    echo "  selfbot install       # Install"
    echo "  selfbot up            # Start bot"
    echo "  selfbot logs          # View live logs"
    echo "  selfbot update        # Update to latest"
    echo ""
}

# ========================================
# Main
# ========================================
case "$1" in
    install)        install_command ;;
    up)             up_command ;;
    down)           down_command ;;
    restart)        restart_command ;;
    status)         status_command ;;
    logs)           shift; logs_command "$@" ;;
    update)         update_command ;;
    backup)         backup_command ;;
    edit)           edit_command ;;
    uninstall)      uninstall_command ;;
    help|*)         usage ;;
esac
