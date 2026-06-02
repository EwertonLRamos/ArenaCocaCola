#!/bin/bash

set -e

echo "=== Iniciando Arena Chute-bate ==="

# ---------------------------------------------------------
# GARANTIR DOTNET DISPONÍVEL
# ---------------------------------------------------------
export DOTNET_ROOT="$HOME/.dotnet"
export PATH="$PATH:$HOME/.dotnet:$HOME/.dotnet/tools"

DOTNET_CMD="dotnet"

# fallback caso não esteja no PATH
if ! command -v dotnet >/dev/null 2>&1; then
    if [ -x "$HOME/.dotnet/dotnet" ]; then
        DOTNET_CMD="$HOME/.dotnet/dotnet"
    else
        echo "❌ ERRO: .NET não encontrado. Verifique a instalação."
        exit 1
    fi
fi

echo "✔ .NET encontrado em: $(command -v $DOTNET_CMD || echo $DOTNET_CMD)"
$DOTNET_CMD --version

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
    echo -e "\n🛑 Encerrando sistema..."
    [ -n "$FRONTEND_PID" ] && kill $FRONTEND_PID 2>/dev/null
    [ -n "$BACKEND_PID" ] && kill $BACKEND_PID 2>/dev/null
    [ -n "$HARDWARE_PID" ] && sudo kill $HARDWARE_PID 2>/dev/null
    exit 0
}

trap limpar_processos INT TERM

# ---------------------------------------------------------
# AUTENTICAÇÃO
# ---------------------------------------------------------
echo -e "\n\nAutenticação"

sudo -k 
sudo -v || { 
    echo "❌ ERRO: Falha na autenticação."
    read -p "Pressione ENTER para fechar..."
    exit 1
}

echo "✔ Autenticado"

# ---------------------------------------------------------
# HARDWARE
# ---------------------------------------------------------
echo -e "\n\nIniciando Hardware"

cd "$BASE_DIR/Hardware/Raspberry" || { echo "❌ Pasta de hardware não encontrada"; exit 1; }

sudo python3 base.py & 
HARDWARE_PID=$!

sleep 5

if ! kill -0 $HARDWARE_PID 2>/dev/null; then
    echo "❌ ERRO: Hardware não iniciou corretamente."
    limpar_processos
fi

echo "✔ Hardware iniciado (PID: $HARDWARE_PID)"

# ---------------------------------------------------------
# BACKEND
# ---------------------------------------------------------
echo -e "\n\nIniciando Backend"

cd "$BASE_DIR/Backend" || { echo "❌ Pasta Backend não encontrada"; exit 1; }

$DOTNET_CMD run &
BACKEND_PID=$!

sleep 5

if ! kill -0 $BACKEND_PID 2>/dev/null; then
    echo "❌ ERRO: Backend falhou ao iniciar."
    limpar_processos
fi

echo "✔ Backend iniciado (PID: $BACKEND_PID)"

# ---------------------------------------------------------
# FRONTEND
# ---------------------------------------------------------
echo -e "\n\nIniciando Frontend"

cd "$BASE_DIR/Frontend" || { echo "❌ Pasta Frontend não encontrada"; exit 1; }

if [ ! -d "node_modules" ]; then
    echo "📦 Instalando dependências do Frontend..."
    npm install
fi

npm run dev &
FRONTEND_PID=$!

sleep 5

if ! kill -0 $FRONTEND_PID 2>/dev/null; then
    echo "❌ ERRO: Frontend falhou ao iniciar."
    limpar_processos
fi

echo "✔ Frontend iniciado (PID: $FRONTEND_PID)"

# ---------------------------------------------------------
# FINALIZAÇÃO
# ---------------------------------------------------------
echo -e "\n================================================="
echo "🚀 TUDO PRONTO! Sistema online."
echo "Pressione CTRL+C para encerrar com segurança."
echo "================================================="

xdg-open "http://localhost:5173/" 2>/dev/null &

wait