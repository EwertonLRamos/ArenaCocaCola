import time
import random
import requests
import threading
from flask import Flask, jsonify

API_URL = "http://localhost:5009/api/game"

MODULOS = [
    {"name": "Módulo 1", "out_pin": 5,  "in_pin": 17},
    {"name": "Módulo 2", "out_pin": 6,  "in_pin": 27},
    {"name": "Módulo 3", "out_pin": 13, "in_pin": 22},
    {"name": "Módulo 4", "out_pin": 19, "in_pin": 10},
    {"name": "Módulo 5", "out_pin": 26, "in_pin": 9},
]

# --- INÍCIO DAS CLASSES MOCK ---
class MockOutputDevice:
    def __init__(self, pin):
        self.pin = pin

    def on(self):
        print(f"[MOCK LUZ] 🟢 LED LIGADO no pino {self.pin}")

    def off(self):
        print(f"[MOCK LUZ] ⚪ LED DESLIGADO no pino {self.pin}")

class MockButton:
    def __init__(self, pin):
        self.pin = pin
        self._hit_time = None

    def preparar_simulacao(self):
        if random.random() < 0.75:
            self._hit_time = time.time() + random.uniform(0.5, 2.5)
        else:
            self._hit_time = None 

    @property
    def is_pressed(self):
        
        if self._hit_time and time.time() >= self._hit_time:
            self._hit_time = None  
            return True
        return False
# --- FIM DAS CLASSES MOCK ---

arduino_outputs = [MockOutputDevice(cfg["out_pin"]) for cfg in MODULOS]
arduino_inputs = [MockButton(cfg["in_pin"]) for cfg in MODULOS]

jogo_ativo = False
app = Flask(__name__)

def desligar_todos_outputs():
    for output in arduino_outputs:
        output.off()

@app.route('/iniciar', methods=['POST'])
def iniciar_jogo():
    global jogo_ativo
    jogo_ativo = True
    print("\n>>> Comando da API recebido: INICIAR JOGO! <<<")
    return jsonify({"mensagem": "Hardware (Mock) ativado!"}), 200

@app.route('/parar', methods=['POST'])
def parar_jogo():
    global jogo_ativo
    jogo_ativo = False
    desligar_todos_outputs()
    print("\n>>> Comando da API recebido: PARAR JOGO! <<<")
    return jsonify({"mensagem": "Hardware (Mock) desativado!"}), 200

def rodar_servidor_flask():
    
    import logging
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.ERROR)
    app.run(host='0.0.0.0', port=5010, debug=False, use_reloader=False)

def rodar_rodada():
    global jogo_ativo
    tempo_espera = random.randint(2, 5)
    
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

    print(f"\n[{modulo['name']} Sorteado] | Pino out: {modulo['out_pin']} | Pino in: {modulo['in_pin']}")

    selected_input.preparar_simulacao()

    selected_output.on()
    time.sleep(0.05)

    start_time = time.time()
    foi_atingido = False
    response_deadline = start_time + 3.0

    while time.time() < response_deadline:
        if not jogo_ativo:
            desligar_todos_outputs()
            return

        if selected_input.is_pressed:
            foi_atingido = True
            print(f"[SENSOR MOCK] Impacto detectado no pino {modulo['in_pin']}!")
            break

        time.sleep(0.01)

    selected_output.off()

    if not jogo_ativo:
        desligar_todos_outputs()
        return

    if foi_atingido:
        try:
            requests.post(f"{API_URL}/hit", timeout=2)
            print("=> Sucesso: Acerto enviado para a API!")
        except Exception as e:
            print(f"=> Falha de Conexão: Erro ao notificar a API (A API está ligada?): {e}")
    else:
        print(f"=> O tempo expirou: Jogador fantasma errou o {modulo['name']}.")

    time.sleep(0.5)

if __name__ == "__main__":
    desligar_todos_outputs()
    
    print("===================================================")
    print("MOCK DO HARDWARE ARENA COCA-COLA INICIADO")
    print("===================================================")
    print("Aguardando comando /iniciar na porta 5010...")
    
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
        print("\nEncerrando script Mock...")