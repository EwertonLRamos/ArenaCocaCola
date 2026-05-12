#include <Adafruit_NeoPixel.h>

const int pinosPiezo[] = {A1, A2, A3, A4, A5}; 
const int numPiezos = 5;
const int pinoRpiIn = A0;
const int pinoRpiOut = 9;
const int pinoFitaLed = 12;
const int numLeds = 17;

Adafruit_NeoPixel fita(numLeds, pinoFitaLed, NEO_GRB + NEO_KHZ800);

void setup() {
  Serial.begin(115200); 

  for(int i = 0; i < numPiezos; i++) {
    pinMode(pinosPiezo[i], INPUT);
  }

  pinMode(pinoRpiIn, INPUT_PULLUP);
  pinMode(pinoRpiOut, OUTPUT);

  digitalWrite(pinoRpiOut, LOW);
  
  fita.begin();
  fita.show();
}

void loop() {
  if (analogRead(pinoRpiIn) <= 700) {
    preencherCor(255, 255, 255);
    
    unsigned long tempoInicio = millis();
    bool atingiuMeta = false;

    while (millis() - tempoInicio <= 2000) {
      float soma = 0;
      
      for (int i = 0; i < numPiezos; i++) {
        soma += analogRead(pinosPiezo[i]);
      }
      
      float media = soma / numPiezos;

      if (media > 400) {
        atingiuMeta = true;
        break; 
      }
    }

    if (atingiuMeta) {
      preencherCor(0, 255, 0);
    } else {
      preencherCor(255, 0, 0);
    }
    
    delay(500);

    preencherCor(0, 0, 0);

    if (atingiuMeta) {
      digitalWrite(pinoRpiOut, HIGH);
      delay(500);
      digitalWrite(pinoRpiOut, LOW);
    }

    while(analogRead(pinoRpiIn) <= 700) {
      delay(10);
    }
  }
}

void preencherCor(uint8_t r, uint8_t g, uint8_t b) {
  for (int i = 0; i < numLeds; i++) {
    fita.setPixelColor(i, fita.Color(r, g, b));
  }
  fita.show();
}