#include <ESP8266WiFi.h>
#include <ESP8266HTTPClient.h>

const char* ssid = "ArenaCocaCola";
const char* password = "ArenaCocaCola";

const char* server = "http://192.168.0.100:5000";

int leds[3] = {27, 26, 25};
int sensores[3] = {33, 32, 35};

int alvoAtual = -1;
unsigned long tempoInicio = 0;

WiFiClient client;

void setup() {
  Serial.begin(115200);

  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
  }

  for (int i = 0; i < 3; i++) {
    pinMode(leds[i], OUTPUT);
  }
}

void loop() {

  if (alvoAtual == -1) {
    alvoAtual = random(0, 3);
    digitalWrite(leds[alvoAtual], HIGH);
    tempoInicio = millis();
  }

  int leitura = analogRead(A0);

  if (leitura > 500) { // threshold piezo
    enviarHit(alvoAtual);
    resetar();
  }

  if (millis() - tempoInicio > 3000) {
    resetar();
  }
}

void enviarHit(int targetId) {
  if (WiFi.status() == WL_CONNECTED) {
    HTTPClient http;

    http.begin(client, String(server) + "/hit");
    http.addHeader("Content-Type", "application/json");

    String body = "{\"targetId\":" + String(targetId) + ",\"hit\":true}";

    http.POST(body);
    http.end();
  }
}

void resetar() {
  digitalWrite(leds[alvoAtual], LOW);
  alvoAtual = -1;
}