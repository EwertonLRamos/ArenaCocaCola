#!/bin/bash
echo "=== Iniciando Arena Chute-bate ==="

cd ..

HARDWARE_PID=""
BACKEND_PID=""
FRONTEND_PID=""

limpar_processos() {
    echo -e "\n🛑 Encerrando sistema..."
    [ -n "$FRONTEND_PID" ] && kill $FRONTEND_PID 2>/dev/null
    [ -n "$BACKEND_PID" ] && kill $BACKEND_PID 2>/dev/null
    [ -n "$HARDWARE_PID" ] && sudo kill $HARDWARE_PID 2>/dev/null
    exit 0
}
trap limpar_processos INT TERM

# ---------------------------------------------------------
# Autenticação
# ---------------------------------------------------------
echo -e "\n\nAutenticação"

sudo -k 

sudo -v || { 
    echo "❌ ERRO: Falha ao obter permissão (Senha incorreta ou cancelada)."
    read -p "Pressione ENTER para fechar..."
    exit 1; 
}
echo "Autenticado"

# ---------------------------------------------------------
# Hardware
# ---------------------------------------------------------
echo -e "\n\nIniciando Hardware"

cd Hardware/Raspberry

sudo python3 base.py & HARDWARE_PID=$!

sleep 5

if ! kill -0 $HARDWARE_PID 2>/dev/null; then
    echo "❌ ERRO: O script do Hardware falhou ou parou inesperadamente."
    read -p "Pressione ENTER para fechar..."
    limpar_processos
fi

cd ..
echo "Hardware iniciado (PID: $HARDWARE_PID)."

sleep 5

# ---------------------------------------------------------
# Backend
# ---------------------------------------------------------
echo -e "\n\nIniciando Backend"
cd ../Backend
dotnet run &
BACKEND_PID=$!

sleep 5
if ! kill -0 $BACKEND_PID 2>/dev/null; then
    echo "❌ ERRO: O Backend falhou ao iniciar. Verifique o código .NET."
    read -p "Pressione ENTER para fechar..."
    limpar_processos
fi
echo "Backend iniciado (PID: $BACKEND_PID)."

sleep 5

# ---------------------------------------------------------
# Frontend
# ---------------------------------------------------------
echo -e "\n\nIniciando Frontend"
cd ../Frontend
if [ ! -d "node_modules" ]; then
    echo "📦 Instalando dependências do Frontend (isso pode demorar um pouco na primeira vez)..."
    npm install
fi
npm run dev &
FRONTEND_PID=$!

sleep 5
if ! kill -0 $FRONTEND_PID 2>/dev/null; then
    echo "❌ ERRO: O Frontend falhou ao iniciar."
    read -p "Pressione ENTER para fechar..."
    limpar_processos
fi
echo "Frontend iniciado (PID: $FRONTEND_PID)."

sleep 5

# ---------------------------------------------------------
# FINALIZAÇÃO
# ---------------------------------------------------------
echo -e "\n================================================="
echo "TUDO PRONTO! A Arena Chute-bate está online."
echo "Mantenha esta janela aberta. Pressione CTRL+C para desligar tudo de forma segura."
echo "================================================="

xdg-open "http://localhost:5173/?" 2>/dev/null &

wait