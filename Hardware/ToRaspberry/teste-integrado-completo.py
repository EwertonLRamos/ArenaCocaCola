import time
import board
import neopixel
import random
import requests # Importante: pip install requests
from gpiozero import DigitalInputDevice

API_URL = "http://localhost:5000/api/game"

# Configurações de Hardware
PINO_MATRIZ = board.D24
PINO_PIEZO = 23
NUM_LEDS = 64

pixels = neopixel.NeoPixel(PINO_MATRIZ, NUM_LEDS, auto_write=False)
piezo = DigitalInputDevice(PINO_PIEZO, pull_up=False)

def limpar_matriz():
    pixels.fill((0, 0, 0))
    pixels.show()

def rodar_rodada():
    tempo_espera = random.randint(2, 5)
    time.sleep(tempo_espera)

    pixels.fill((255, 255, 255)) # Branco: Chute!
    pixels.show()

    start_time = time.time()
    foi_atingido = False
    
    while (time.time() - start_time) < 2.0:
        if piezo.is_active:
            foi_atingido = True
            break
        time.sleep(0.01)

    if foi_atingido:
        pixels.fill((0, 255, 0)) # Verde
        try:
            requests.post(f"{API_URL}/hit") # Notifica API do acerto
        except: pass
    else:
        pixels.fill((255, 0, 0)) # Vermelho
        try:
            requests.post(f"{API_URL}/miss") # Notifica API do erro
        except: pass

    pixels.show()
    time.sleep(0.5)
    limpar_matriz()

if __name__ == "__main__":
    try:
        while True:
            # O Python pode esperar um comando da API para começar, 
            # ou rodar continuamente e a API decide se ignora os hits.
            rodar_rodada()
    except KeyboardInterrupt:
        limpar_matriz()