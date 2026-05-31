#!/bin/bash
set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

ok()   { echo -e "${GREEN}[✓]${NC} $1"; }
warn() { echo -e "${YELLOW}[!]${NC} $1"; }
err()  { echo -e "${RED}[✗]${NC} $1"; exit 1; }

echo ""
echo "  Serial TUI — Instalador"
echo "  ========================"
echo ""

# Homebrew
if ! command -v brew &>/dev/null; then
    warn "Homebrew no encontrado. Instalando..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)" || err "No se pudo instalar Homebrew"
    ok "Homebrew instalado"
else
    ok "Homebrew ya instalado"
fi

# minicom
if ! command -v minicom &>/dev/null; then
    warn "minicom no encontrado. Instalando via brew..."
    brew install minicom || err "No se pudo instalar minicom"
    ok "minicom instalado"
else
    ok "minicom ya instalado ($(minicom --version 2>&1 | head -1))"
fi

# Python 3
if ! command -v python3 &>/dev/null; then
    warn "Python3 no encontrado. Instalando via brew..."
    brew install python3 || err "No se pudo instalar Python3"
    ok "Python3 instalado"
else
    ok "Python3 ya instalado ($(python3 --version))"
fi

# Dependencias Python
echo ""
echo "  Instalando dependencias Python..."
echo ""

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if python3 -m pip install -r "$SCRIPT_DIR/requirements.txt" --break-system-packages -q; then
    ok "textual instalado"
    ok "pyserial instalado"
else
    err "Fallo al instalar dependencias Python"
fi

echo ""
ok "Todo listo. Ejecuta con:"
echo ""
echo "     python3 $SCRIPT_DIR/serial_tui.py"
echo ""
