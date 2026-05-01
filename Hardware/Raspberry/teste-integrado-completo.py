import time
import random
import requests
import threading
from flask import Flask, jsonify
from gpiozero import Button, LED # Adicionado LED, removido neopixel e board

API_URL = "http://localhost:5009/api/game"

# Configurações de Hardware
PINO_LED = 24 # Usando o pino 24 (antigo PINO_MATRIZ) para o LED simples
PINO_KY002 = 23

led = LED(PINO_LED)

# Configuração do KY-002 (com pull-up ligado e sem filtro interno)
sensor_ky002 = Button(PINO_KY002, pull_up=True, bounce_time=None)

jogo_ativo = False
app = Flask(__name__)

# Variáveis globais para o controle de repique (debounce) e bandeira do jogo
ultimo_acionamento = 0
intervalo_ignorado = 0.5
impacto_detectado_flag = False

def detectou_vibracao():
    """Esta função roda em segundo plano capturando qualquer micro-impacto instantaneamente."""
    global ultimo_acionamento, impacto_detectado_flag, jogo_ativo
    
    # Se o jogo não estiver ativo, ignoramos a batida
    if not jogo_ativo:
        return
        
    agora = time.time()
    # Aplica o nosso filtro de debounce manual
    if (agora - ultimo_acionamento) > intervalo_ignorado:
        ultimo_acionamento = agora
        impacto_detectado_flag = True # Levanta a bandeira para o loop do jogo ver

# Ativa a interrupção de hardware
sensor_ky002.when_pressed = detectou_vibracao


@app.route('/iniciar', methods=['POST'])
def iniciar_jogo():
    global jogo_ativo, impacto_detectado_flag
    jogo_ativo = True
    impacto_detectado_flag = False # Limpa qualquer batida acidental antes de começar
    print("Comando recebido: Iniciando o jogo!")
    return jsonify({"mensagem": "Hardware ativado!"}), 200

@app.route('/parar', methods=['POST'])
def parar_jogo():
    global jogo_ativo
    jogo_ativo = False
    led.off()
    print("Comando recebido: Parando o jogo!")
    return jsonify({"mensagem": "Hardware desativado!"}), 200

def rodar_servidor_flask():
    app.run(host='0.0.0.0', port=5010, debug=False, use_reloader=False)

def rodar_rodada():
    global jogo_ativo, impacto_detectado_flag
    tempo_espera = random.randint(2, 5)
    
    inicio_espera = time.time()
    while (time.time() - inicio_espera) < tempo_espera:
        if not jogo_ativo:
            led.off()
            return
        time.sleep(0.1)

    led.on() # Acende o LED indicando a janela de ação

    start_time = time.time()
    foi_atingido = False
    impacto_detectado_flag = False # Zera a bandeira exatamente quando a janela de chute abre
    
    # Janela de 2 segundos para o jogador acertar
    while (time.time() - start_time) < 2.0:
        # Lemos a bandeira deixada pela interrupção
        if impacto_detectado_flag:
            foi_atingido = True
            impacto_detectado_flag = False # Consome a bandeira
            break
        
        if not jogo_ativo:
            led.off()
            return
            
        time.sleep(0.01)

    # O LED apaga independentemente se houve toque (break) ou se os 2s passaram
    led.off()

    if not jogo_ativo:
        return

    if foi_atingido:
        try:
            requests.post(f"{API_URL}/hit", timeout=2)
            print("Acerto registrado!")
        except Exception as e: 
            print(f"Erro ao notificar acerto: {e}")
    else:
        try:
            # Envia o erro e aguarda a resposta da API
            resposta = requests.post(f"{API_URL}/miss", timeout=2)
            
            if resposta.status_code == 200:
                dados = resposta.json()
                
                # Verifica se a API informou que as vidas acabaram
                if dados.get("isGameOver", False) == True:
                    print("Fim de jogo! O jogador perdeu todas as vidas.")
                    jogo_ativo = False # Interrompe o fluxo e aguarda novo /iniciar
                    
        except Exception as e: 
            print(f"Erro ao notificar erro: {e}")

    # Mantive um pequeno delay de meio segundo para que as rodadas não fiquem
    # instantaneamente coladas umas nas outras.
    time.sleep(0.5)

if __name__ == "__main__":
    led.off()
    
    print("Iniciando servidor do hardware na porta 5010...")
    thread_api = threading.Thread(target=rodar_servidor_flask, daemon=True)
    thread_api.start()
    
    try:
        while True:
            if jogo_ativo:
                rodar_rodada()
            else:
                time.sleep(0.1) 
                
    except KeyboardInterrupt:
        led.off()
        print("\nEncerrando script...")