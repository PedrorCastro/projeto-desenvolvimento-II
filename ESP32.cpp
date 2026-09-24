#include <WiFi.h>
#include <HTTPClient.h>
#include <WiFiClientSecure.h>

// ===============================
// CONFIGURAÇÕES DO WIFI
// ===============================
const char* WIFI_SSID = "CirkitWifi";
const char* WIFI_PASSWORD = "";

// ===============================
// CONFIGURAÇÃO DA API (Render)
// ===============================
const char* API_HOST = "projeto-desenvolvimento-ii.onrender.com";
const char* API_PATH = "/api/v1/measurements";
const int API_PORT = 443;
const char* API_URL = "https://projeto-desenvolvimento-ii.onrender.com/api/v1/measurements";

// ===============================
// ESTAÇÃO
// ===============================
const char* STATION_ID = "esp32-campus-01";

void conectarWiFi() {
    Serial.println();
    Serial.print("Conectando ao Wi-Fi: ");
    Serial.println(WIFI_SSID);

    WiFi.mode(WIFI_STA);
    WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

    int tentativas = 0;
    while (WiFi.status() != WL_CONNECTED && tentativas < 30) {
        delay(500);
        Serial.print(".");
        tentativas++;
    }
    Serial.println();

    if (WiFi.status() == WL_CONNECTED) {
        Serial.println("Wi-Fi conectado!");
        Serial.print("IP do ESP32: ");
        Serial.println(WiFi.localIP());
    } else {
        Serial.println("FALHA ao conectar ao Wi-Fi.");
    }
}

void testarDNS(const char* host) {
    Serial.print("Resolvendo DNS para: ");
    Serial.println(host);

    IPAddress resolvedIP;
    unsigned long inicio = millis();
    bool ok = WiFi.hostByName(host, resolvedIP);
    unsigned long duracao = millis() - inicio;

    if (ok) {
        Serial.print("DNS resolvido: ");
        Serial.print(resolvedIP);
        Serial.print(" (levou ");
        Serial.print(duracao);
        Serial.println(" ms)");
    } else {
        Serial.print("FALHA na resolução DNS! (levou ");
        Serial.print(duracao);
        Serial.println(" ms)");
    }
}

void testarConexaoTLS(const char* host, int port) {
    Serial.print("Heap livre antes do teste: ");
    Serial.println(ESP.getFreeHeap());

    WiFiClientSecure client;
    client.setInsecure();

    Serial.print("Testando conexão TCP/TLS direta a ");
    Serial.print(host);
    Serial.print(":");
    Serial.println(port);

    unsigned long inicio = millis();
    bool ok = client.connect(host, port);
    unsigned long duracao = millis() - inicio;

    if (ok) {
        Serial.print("Conectou! (levou ");
        Serial.print(duracao);
        Serial.println(" ms)");
        client.stop();
    } else {
        Serial.print("FALHOU ao conectar (levou ");
        Serial.print(duracao);
        Serial.println(" ms)");
    }

    Serial.print("Heap livre depois do teste: ");
    Serial.println(ESP.getFreeHeap());
    Serial.println();
}

void enviarMedicao() {
    if (WiFi.status() != WL_CONNECTED) {
        Serial.println("Wi-Fi desconectado!");
        return;
    }

    WiFiClientSecure client;
    client.setInsecure();

    HTTPClient http;
    http.setConnectTimeout(15000); // Render pode demorar no "cold start"
    http.setTimeout(15000);
    http.begin(client, API_URL);
    http.addHeader("Content-Type", "application/json");

    // Dados de teste
    float temperatura = 25.5;
    float umidade = 68.0;
    float pressao = 1013.2;
    int qualidadeAr = 500;
    int luminosidade = 1500;
    float chuva = 0.0;

    String json = "{";
    json += "\"station_id\":\"" + String(STATION_ID) + "\",";
    json += "\"temperature_c\":" + String(temperatura, 2) + ",";
    json += "\"humidity_pct\":" + String(umidade, 2) + ",";
    json += "\"pressure_hpa\":" + String(pressao, 2) + ",";
    json += "\"air_quality_raw\":" + String(qualidadeAr) + ",";
    json += "\"luminosity_raw\":" + String(luminosidade) + ",";
    json += "\"rainfall_mm\":" + String(chuva);
    json += "}";

    Serial.println("Enviando dados:");
    Serial.println(json);

    int httpCode = http.POST(json);
    Serial.print("HTTP Status: ");
    Serial.println(httpCode);

    if (httpCode > 0) {
        String resposta = http.getString();
        Serial.println("Resposta da API:");
        Serial.println(resposta);
    } else {
        Serial.print("Erro ao enviar: ");
        Serial.println(http.errorToString(httpCode));
    }

    http.end();
}

void setup() {
    Serial.begin(115200);
    delay(1000);

    conectarWiFi();

    Serial.println("=== TESTE: conexão com a API no Render ===");
    testarDNS(API_HOST);
    testarConexaoTLS(API_HOST, API_PORT);
}

void loop() {
    enviarMedicao();
    delay(10000);
}