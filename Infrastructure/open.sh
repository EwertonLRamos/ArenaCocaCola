#!/bin/bash

set -e

echo "=== Iniciando Arena Chute-bate ==="

# ---------------------------------------------------------
# GARANTIR DOTNET DISPONÍVEL
# ---------------------------------------------------------
export DOTNET_ROOT="$HOME/.dotnet"
export PATH="$PATH:$HOME/.dotnet:$HOME/.dotnet/tools"

DOTNET_CMD="dotnet"

if ! command -v dotnet >/dev/null 2>&1; then
    if [ -x "$HOME/.dotnet/dotnet" ]; then
        DOTNET_CMD="$HOME/.dotnet/dotnet"
    else
        zenity --error --text="❌ .NET não encontrado."
        exit 1
    fi
fi

# ---------------------------------------------------------
# VARIÁVEIS
# ---------------------------------------------------------
BASE_DIR="$(cd "$(dirname "$0")" && pwd)/.."

HARDWARE_PID=""
BACKEND_PID=""
FRONTEND_PID=""

# ---------------------------------------------------------
# FUNÇÃO DE LIMPEZA
# ---------------------------------------------------------
limpar_processos() {
    [ -n "$FRONTEND_PID" ] && kill $FRONTEND_PID 2>/dev/null
    [ -n "$BACKEND_PID" ] && kill $BACKEND_PID 2>/dev/null
    [ -n "$HARDWARE_PID" ] && kill $HARDWARE_PID 2>/dev/null
    exit 0
}

trap limpar_processos INT TERM

# ---------------------------------------------------------
# UI INICIAL
# ---------------------------------------------------------
zenity --info --text="Iniciando Arena Chute-bate..."

# ---------------------------------------------------------
# HARDWARE
# ---------------------------------------------------------
cd "$BASE_DIR/Hardware/Raspberry" || {
    zenity --error --text="❌ Pasta de hardware não encontrada"
    exit 1
}

python3 base.py &
HARDWARE_PID=$!

sleep 3

if ! kill -0 $HARDWARE_PID 2>/dev/null; then
    zenity --error --text="❌ Falha ao iniciar hardware"
    limpar_processos
fi

# ---------------------------------------------------------
# BACKEND
# ---------------------------------------------------------
cd "$BASE_DIR/Backend" || {
    zenity --error --text="❌ Backend não encontrado"
    exit 1
}

$DOTNET_CMD run &
BACKEND_PID=$!

sleep 3

if ! kill -0 $BACKEND_PID 2>/dev/null; then
    zenity --error --text="❌ Falha ao iniciar backend"
    limpar_processos
fi

# ---------------------------------------------------------
# FRONTEND
# ---------------------------------------------------------
cd "$BASE_DIR/Frontend" || {
    zenity --error --text="❌ Frontend não encontrado"
    exit 1
}

if [ ! -d "node_modules" ]; then
    npm install
fi

npm run dev &
FRONTEND_PID=$!

sleep 3

if ! kill -0 $FRONTEND_PID 2>/dev/null; then
    zenity --error --text="❌ Falha ao iniciar frontend"
    limpar_processos
fi

# ---------------------------------------------------------
# FINALIZAÇÃO
# ---------------------------------------------------------
zenity --info --text="🚀 Sistema iniciado com sucesso!"

xdg-open "http://localhost:5173/" 2>/dev/null &

wait