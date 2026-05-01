import time
import board
import neopixel
import random
import requests
import threading
from flask import Flask, jsonify
from gpiozero import DigitalInputDevice

API_URL = "http://localhost:5009/api/game"

# Configurações de Hardware
PINO_MATRIZ = board.D24
PINO_PIEZO = 23
NUM_LEDS = 64

pixels = neopixel.NeoPixel(PINO_MATRIZ, NUM_LEDS, auto_write=False)
piezo = DigitalInputDevice(PINO_PIEZO, pull_up=False)

jogo_ativo = False
app = Flask(__name__)

@app.route('/iniciar', methods=['POST'])
def iniciar_jogo():
    global jogo_ativo
    jogo_ativo = True
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
    global jogo_ativo
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
    
    while (time.time() - start_time) < 2.0:
        if piezo.is_active:
            foi_atingido = True
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