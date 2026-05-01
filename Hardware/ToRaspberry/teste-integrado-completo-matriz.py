import time
import board
import neopixel
import random
import requests
import threading
from flask import Flask, jsonify
from gpiozero import Button # Mudamos para Button para usar interrupções

API_URL = "http://localhost:5009/api/game"

# Configurações de Hardware
PINO_MATRIZ = board.D24
PINO_KY002 = 23
NUM_LEDS = 64

pixels = neopixel.NeoPixel(PINO_MATRIZ, NUM_LEDS, auto_write=False)

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
    limpar_matriz()
    print("Comando recebido: Parando o jogo!")
    return jsonify({"mensagem": "Hardware desativado!"}), 200

def rodar_servidor_flask():
    app.run(host='0.0.0.0', port=5010, debug=False, use_reloader=False)

def limpar_matriz():
    pixels.fill((0, 0, 0))
    pixels.show()

def rodar_rodada():
    global jogo_ativo, impacto_detectado_flag
    tempo_espera = random.randint(2, 5)
    
    inicio_espera = time.time()
    while (time.time() - inicio_espera) < tempo_espera:
        if not jogo_ativo:
            limpar_matriz()
            return
        time.sleep(0.1)

    pixels.fill((255, 255, 255)) # Branco: Chute!
    pixels.show()

    start_time = time.time()
    foi_atingido = False
    impacto_detectado_flag = False # Zera a bandeira exatamente quando a janela de chute abre
    
    # Janela de 2 segundos para o jogador acertar
    while (time.time() - start_time) < 2.0:
        # Em vez de ler o pino diretamente, lemos a bandeira deixada pela interrupção
        if impacto_detectado_flag:
            foi_atingido = True
            impacto_detectado_flag = False # Consome a bandeira
            break
        
        if not jogo_ativo:
            limpar_matriz()
            return
            
        time.sleep(0.01)

    if not jogo_ativo:
        return

    if foi_atingido:
        pixels.fill((0, 255, 0)) # Verde
        try:
            requests.post(f"{API_URL}/hit", timeout=2)
            print("Acerto registrado!")
        except Exception as e: 
            print(f"Erro ao notificar acerto: {e}")
    else:
        pixels.fill((255, 0, 0)) # Vermelho
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

    pixels.show()
    time.sleep(0.5)
    limpar_matriz()

if __name__ == "__main__":
    limpar_matriz()
    
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
        limpar_matriz()
        print("\nEncerrando script...")