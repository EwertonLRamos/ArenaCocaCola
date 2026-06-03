#!/bin/bash

echo "=== Iniciando Arena Chute-bate ==="

cd ..

HARDWARE_PID=""
BACKEND_PID=""
FRONTEND_PID=""

# ---------------------------------------------------------
# UI HELPERS
# ---------------------------------------------------------
spinner() {
    local pid=$1
    local delay=0.1
    local spinstr='|/-\'

    while kill -0 $pid 2>/dev/null; do
        for i in $(seq 0 3); do
            printf "\r[%c] Carregando..." "${spinstr:$i:1}"
            sleep $delay
        done
    done

    printf "\r✔ Concluído!        \n"
}

run_step() {
    local name=$1
    shift

    echo -e "\n➡ $name"

    "$@" &
    local pid=$!

    spinner $pid

    wait $pid
    local status=$?

    if [ $status -ne 0 ]; then
        echo "❌ ERRO em: $name"
        read -p "Pressione ENTER para sair..."
        limpar_processos
    else
        echo "✅ $name finalizado"
    fi
}

print_header() {
    echo -e "\n======================================"
    echo "$1"
    echo "======================================"
}

# ---------------------------------------------------------
# CLEANUP
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
print_header "Autenticação"

sudo -k
sudo -v &
spinner $!

if [ $? -ne 0 ]; then
    echo "❌ Falha na autenticação"
    exit 1
fi

echo "🔐 Autenticado com sucesso"

# ---------------------------------------------------------
# HARDWARE
# ---------------------------------------------------------
print_header "Iniciando Hardware"

cd Hardware/Raspberry

sudo python3 base.py &
HARDWARE_PID=$!

spinner $HARDWARE_PID

sleep 2

if ! kill -0 $HARDWARE_PID 2>/dev/null; then
    echo "❌ Hardware falhou"
    limpar_processos
fi

echo "✅ Hardware rodando (PID: $HARDWARE_PID)"
cd ..

# ---------------------------------------------------------
# BACKEND
# ---------------------------------------------------------
print_header "Iniciando Backend"

cd Backend

dotnet run &
BACKEND_PID=$!

spinner $BACKEND_PID

sleep 2

if ! kill -0 $BACKEND_PID 2>/dev/null; then
    echo "❌ Backend falhou"
    limpar_processos
fi

echo "✅ Backend rodando (PID: $BACKEND_PID)"

cd ..

# ---------------------------------------------------------
# FRONTEND
# ---------------------------------------------------------
print_header "Iniciando Frontend"

cd Frontend

if [ ! -d "node_modules" ]; then
    run_step "Instalando dependências do Frontend" npm install
fi

npm run dev &
FRONTEND_PID=$!

spinner $FRONTEND_PID

sleep 2

if ! kill -0 $FRONTEND_PID 2>/dev/null; then
    echo "❌ Frontend falhou"
    limpar_processos
fi

echo "✅ Frontend rodando (PID: $FRONTEND_PID)"

cd ..

# ---------------------------------------------------------
# FINAL
# ---------------------------------------------------------
print_header "Sistema Pronto"

echo "🚀 Arena Chute-bate ONLINE"
echo "Pressione CTRL+C para encerrar com segurança"

xdg-open "http://localhost:5173/" 2>/dev/null &

wait