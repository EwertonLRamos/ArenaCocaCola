import time
import random
import requests
import threading
import os
import logging
from flask import Flask, jsonify
from gpiozero import DigitalInputDevice, OutputDevice

# URL base para a API
API_URL = os.environ.get("API_URL", "http://localhost:5009")

def build_api_url(path: str) -> str:
    return API_URL.rstrip('/') + '/api/game/' + path.lstrip('/')

MODULOS = [
    {"name": "Módulo 1", "out_pin": 24,  "in_pin": 23}#,
    # {"name": "Módulo 2", "out_pin": 6,  "in_pin": 27},
    # {"name": "Módulo 3", "out_pin": 13, "in_pin": 22},
    # {"name": "Módulo 4", "out_pin": 19, "in_pin": 10},
    # {"name": "Módulo 5", "out_pin": 26, "in_pin": 9},
]

# Inicialização direta do Hardware (Raspberry Pi)
arduino_outputs = [
    OutputDevice(cfg["out_pin"], active_high=True, initial_value=False)
    for cfg in MODULOS
]

arduino_inputs = [
    DigitalInputDevice(cfg["in_pin"], pull_up=True)
    for cfg in MODULOS
]

jogo_ativo = False
app = Flask(__name__)

def desligar_todos_outputs():
    for output in arduino_outputs:
        output.off()

@app.route('/iniciar', methods=['POST'])
def iniciar_jogo():
    global jogo_ativo
    jogo_ativo = True
    print("Comando recebido: INICIAR JOGO!")
    return jsonify({"mensagem": "Hardware ativado!"}), 200

@app.route('/parar', methods=['POST'])
def parar_jogo():
    global jogo_ativo
    jogo_ativo = False
    desligar_todos_outputs()
    print("Comando recebido: PARAR JOGO!")
    return jsonify({"mensagem": "Hardware desativado!"}), 200

def rodar_servidor_flask():
    # reduzir verbosidade do werkzeug
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.ERROR)
    app.run(host='0.0.0.0', port=5010, debug=False, use_reloader=False)

def rodar_rodada():
    global jogo_ativo
    tempo_espera = random.randint(2, 3)
    
    inicio_espera = time.time()
    while (time.time() - inicio_espera) < tempo_espera:
        if not jogo_ativo:
            desligar_todos_outputs()
            return
        time.sleep(0.1)

    selected_index = random.randrange(len(arduino_outputs))
    selected_output = arduino_outputs[selected_index]
    selected_input = arduino_inputs[selected_index]
    modulo = MODULOS[selected_index]

    print(f"{modulo['name']} selecionado | Pino out - {modulo['out_pin']} Pino in - ({modulo['in_pin']})")
    

    selected_output.on()
    time.sleep(0.05)

    start_time = time.time()
    foi_atingido = False
    response_deadline = start_time + 3.0

    while time.time() < response_deadline:
        if not jogo_ativo:
            desligar_todos_outputs()
            return
        
        try:
            if selected_input.value:
                foi_atingido = True
                print(f"[SENSOR] Impacto detectado no pino {modulo['in_pin']}!")
                break
        except Exception:
            # Protege contra falhas de leitura do hardware
            pass

        #time.sleep(0.01)

    selected_output.off()

    if not jogo_ativo:
        desligar_todos_outputs()
        return

    if foi_atingido:
        try:
            url = build_api_url('/hit')
            print(url)
            payload = {"targetId": selected_index, "hit": True}
            resp = requests.post(url, json=payload, timeout=2)
            if resp.ok:
                print("=> Sucesso: Acerto enviado para a API!")
            else:
                print(f"=> Falha: API retornou {resp.status_code} - {resp.text}")
                print(url)
        except Exception as e:
            print(f"=> Falha de Conexão: Erro ao notificar a API (A API está ligada?): {e}")
    else:
        print(f"=> O tempo expirou: {modulo['name']} não foi acertado.")

    time.sleep(0.5)

if __name__ == "__main__":
    desligar_todos_outputs()
    
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
        desligar_todos_outputs()
        print("\nEncerrando script...")