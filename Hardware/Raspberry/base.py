import time
import random
import requests
import threading
from flask import Flask, jsonify
from gpiozero import Button, OutputDevice

API_URL = "http://localhost:5009/api/game"

ARDUINO_CHANNELS = [
    {"name": "Placa 1", "out_pin": 5,  "in_pin": 17},
    {"name": "Placa 2", "out_pin": 6,  "in_pin": 27},
    {"name": "Placa 3", "out_pin": 13, "in_pin": 22},
    {"name": "Placa 4", "out_pin": 19, "in_pin": 10},
    {"name": "Placa 5", "out_pin": 26, "in_pin": 9},
]

arduino_outputs = [
    OutputDevice(cfg["out_pin"], active_high=True, initial_value=False)
    for cfg in ARDUINO_CHANNELS
]
arduino_inputs = [
    Button(cfg["in_pin"], pull_up=False, bounce_time=None)
    for cfg in ARDUINO_CHANNELS
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
    placa = ARDUINO_CHANNELS[selected_index]

    print(f"Placa selecionada: {placa['name']} (out_pin={placa['out_pin']}, in_pin={placa['in_pin']})")

    selected_output.on()
    time.sleep(0.1)
    selected_output.off()

    start_time = time.time()
    foi_atingido = False

    while (time.time() - start_time) < 2.0:
        if not jogo_ativo:
            desligar_todos_outputs()
            return

        if selected_input.is_pressed:
            foi_atingido = True
            break

        time.sleep(0.01)

    if not jogo_ativo:
        desligar_todos_outputs()
        return

    if foi_atingido:
        try:
            requests.post(f"{API_URL}/hit", timeout=2)
            print("Acerto registrado!")
        except Exception as e:
            print(f"Erro ao notificar acerto: {e}")
    else:
        try:
            resposta = requests.post(f"{API_URL}/miss", timeout=2)
            if resposta.status_code == 200:
                dados = resposta.json()
                if dados.get("isGameOver", False) == True:
                    print("Fim de jogo! O jogador perdeu todas as vidas.")
                    jogo_ativo = False
        except Exception as e:
            print(f"Erro ao notificar erro: {e}")

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