#include <ESP8266WiFi.h>
#include <ESP8266HTTPClient.h>

// Credenciais da rede que o ESP vai CRIAR
const char* ssid = "ArenaCocaCola";
const char* password = "ArenaCocaCola";

// ATENÇÃO AO IP: Como o ESP é o roteador, o seu computador vai se conectar a ele.
// O ESP será o 192.168.4.1. O seu computador (onde a API roda) ganhará um IP novo.
// Geralmente será 192.168.4.2, mas você precisa confirmar no seu terminal.
const char* server = "http://192.168.4.2:5009"; 

// Pinos embutidos no NodeMCU Amica
const int ledPin = LED_BUILTIN; 
const int buttonPin = 0; // O botão "Flash" no NodeMCU está ligado ao GPIO 0

// Variáveis de controle de estado
unsigned long tempoUltimoEvento = 0;
unsigned long intervaloAleatorio = 0;
bool esperandoAcao = false;

WiFiClient client;

void setup() {
  Serial.begin(115200);
  
  // Configuração dos Pinos
  pinMode(ledPin, OUTPUT);
  pinMode(buttonPin, INPUT_PULLUP); // O botão precisa do pull-up interno

  // No NodeMCU, o LED_BUILTIN funciona com lógica invertida (LOW = Aceso, HIGH = Apagado)
  digitalWrite(ledPin, HIGH); 

  // Configura o modo Access Point (Roteador)
  Serial.println("\nIniciando rede Wi-Fi (Modo AP)...");
  WiFi.softAP(ssid, password);
  
  Serial.print("Rede criada! IP do ESP8266: ");
  Serial.println(WiFi.softAPIP());

  // Gera uma semente verdadeira para os números aleatórios usando o ruído do pino analógico
  randomSeed(analogRead(A0));
  
  // Define o primeiro intervalo aleatório (entre 2 e 5 segundos)
  intervaloAleatorio = random(2000, 5000);
  tempoUltimoEvento = millis();
}

void loop() {
  // LÓGICA 1: Acender o LED após um intervalo aleatório
  if (!esperandoAcao && (millis() - tempoUltimoEvento > intervaloAleatorio)) {
    esperandoAcao = true;
    digitalWrite(ledPin, LOW); // Acende o LED interno
    Serial.println("LED Aceso! Pressione o botao Flash.");
  }

  // LÓGICA 2: Detectar o clique no botão ENQUANTO o LED está aceso
  // O botão lê LOW quando pressionado
  if (esperandoAcao && digitalRead(buttonPin) == LOW) {
    
    // Pequeno delay para evitar efeito "bouncing" (múltiplos cliques físicos)
    delay(50); 
    // Trava o código aqui até você soltar o botão
    while(digitalRead(buttonPin) == LOW) { 
      delay(10); 
    }

    Serial.println("Botao pressionado! Gerando sensor aleatorio...");
    
    // Sorteia um número de 0 a 4 para simular o ID do sensor
    int sensorSimulado = random(0, 5); 
    
    // Envia para a API
    enviarHit(sensorSimulado);

    // Reseta o estado para o próximo ciclo
    esperandoAcao = false;
    digitalWrite(ledPin, HIGH); // Apaga o LED
    intervaloAleatorio = random(2000, 5000); // Sorteia novo tempo de espera
    tempoUltimoEvento = millis();
  }
}

void enviarHit(int targetId) {
  HTTPClient http;

  Serial.print("Enviando POST para a API... ID: ");
  Serial.println(targetId);

  // Inicia a conexão HTTP
  http.begin(client, String(server) + "/hit");
  http.addHeader("Content-Type", "application/json");

  // Monta o payload JSON
  String body = "{\"targetId\":" + String(targetId) + ",\"hit\":true}";

  // Executa o POST
  int httpCode = http.POST(body);
  
  // Trata a resposta no console para debug
  if (httpCode > 0) {
    Serial.printf("Sucesso! HTTP Code: %d\n", httpCode);
  } else {
    Serial.printf("Falha na requisicao: %s\n", http.errorToString(httpCode).c_str());
  }
  
  http.end(); // Libera os recursos
}