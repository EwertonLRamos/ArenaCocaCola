const int pinosPiezo[] = {A0, A1, A2, A3, A4}; 
const int numPiezos = 5;
const int pinoRpiIn = A5;
const int pinoRpiOut = 9;
const int pinoFitaLed = 8;

void setup() {
  Serial.begin(115200); 

  for(int i = 0; i < numPiezos; i++) {
    pinMode(pinosPiezo[i], INPUT);
  }

  pinMode(pinoRpiIn, INPUT);
  pinMode(pinoRpiOut, OUTPUT);
  pinMode(pinoFitaLed, OUTPUT);

  digitalWrite(pinoRpiOut, LOW);
  digitalWrite(pinoFitaLed, LOW);
}

void loop() {
  if (digitalRead(pinoRpiIn) == HIGH) {
    
    digitalWrite(pinoFitaLed, HIGH);
    
    unsigned long tempoInicio = millis();
    bool atingiuMeta = false;

    while (millis() - tempoInicio <= 2000) {
      float soma = 0;
      
      for (int i = 0; i < numPiezos; i++) {
        soma += analogRead(pinosPiezo[i]);
      }
      
      float media = soma / numPiezos;

      if (media > 700) {
        atingiuMeta = true;
        break; 
      }
    }

    if (atingiuMeta) {
      digitalWrite(pinoRpiOut, HIGH);
      delay(50);
      digitalWrite(pinoRpiOut, LOW);
    }

    digitalWrite(pinoFitaLed, LOW);

    while(digitalRead(pinoRpiIn) == HIGH) {
      delay(10);
    }   
  }
}