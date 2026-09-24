# API Meteorológica - MeteoCidade

API em Python para receber dados enviados pelo ESP32, validá-los e armazená-los em SQLite. Ela atende à etapa de **backend** do PD-II (estação meteorológica inteligente para monitoramento ambiental urbano) e já permite que o dashboard consuma dados reais.

A API está publicada em produção via **Render** e recebendo medições reais de um ESP32-S3 simulado no **Cirkit Designer**.

🔗 **URL pública:** `https://projeto-desenvolvimento-ii.onrender.com`

---

## Como executar localmente

No PowerShell, dentro desta pasta:

```powershell
python server.py
```

O serviço ficará disponível em `http://127.0.0.1:8000`. O arquivo `meteo.db` será criado automaticamente.

Para permitir acesso pela rede local (por exemplo, por um ESP32 conectado no mesmo Wi-Fi), defina o host antes de iniciar:

```powershell
$env:METEO_HOST = "0.0.0.0"
python server.py
```

A API também lê a variável de ambiente `PORT` (usada automaticamente pelo Render em produção), com fallback para `METEO_PORT` e depois `8000`.

---

## Deploy em produção (Render)

O serviço está hospedado como **Web Service** no [Render](https://render.com), free tier, conectado diretamente ao repositório GitHub.

| Configuração | Valor |
|---|---|
| Build Command | `pip install -r requirements.txt` |
| Start Command | `python3 server.py` |
| Runtime | Python 3 |

**Limitações do plano free (importantes para o relatório):**
- **Disco efêmero**: o arquivo `meteo.db` é recriado do zero a cada redeploy ou reinício do serviço. Os dados não persistem entre reinicializações — adequado para testes de integração, não para armazenamento definitivo. Para persistência real, é necessário um Render Disk (pago) ou migrar para um banco gerenciado (ex.: PostgreSQL).
- **Cold start**: após ~15 minutos de inatividade, o serviço "dorme". A primeira requisição seguinte pode levar 30-50 segundos para responder; as próximas voltam ao normal.

---

## Endpoints

| Método | Rota | Uso |
|---|---|---|
| GET | `/health` | Verifica se a API está disponível. |
| POST | `/api/v1/measurements` | Registra uma medição do ESP32. |
| GET | `/api/v1/measurements?station_id=campus-centro-01&limit=50` | Lista medições, da mais recente para a mais antiga. |
| GET | `/api/v1/stations/campus-centro-01/latest` | Retorna a leitura mais recente da estação. |
| GET | `/api/v1/stations` | Lista estações e quantidade de registros. |

---

## Exemplo de envio do ESP32

Faça uma requisição `POST` com cabeçalho `Content-Type: application/json` para `/api/v1/measurements`.

```json
{
  "station_id": "campus-centro-01",
  "temperature_c": 25.4,
  "humidity_pct": 64.2,
  "pressure_hpa": 1012.8,
  "air_quality_raw": 390,
  "luminosity_raw": 780,
  "rainfall_mm": 0.0,
  "latitude": -23.5505,
  "longitude": -46.6333,
  "measured_at": "2026-09-13T15:00:00-03:00"
}
```

Os campos obrigatórios são `station_id`, `temperature_c`, `humidity_pct` e `pressure_hpa`. Os demais podem ser enviados quando o sensor estiver conectado. A API recusa leituras fisicamente improváveis, como umidade acima de 100%, e armazena as datas em UTC.

---

## Integração com ESP32 (validada em simulação)

A comunicação ESP32 → API foi validada usando o simulador **ESP32-S3 do Cirkit Designer**, conectado à rede virtual `CirkitWifi` (aberta, sem senha), com requisições HTTPS via `WiFiClientSecure` apontando para a URL pública do Render.

Trecho essencial do firmware (Arduino/C++):

```cpp
#include <WiFi.h>
#include <HTTPClient.h>
#include <WiFiClientSecure.h>

const char* WIFI_SSID = "CirkitWifi";
const char* WIFI_PASSWORD = "";
const char* API_URL = "https://projeto-desenvolvimento-ii.onrender.com/api/v1/measurements";

void enviarMedicao() {
    WiFiClientSecure client;
    client.setInsecure();

    HTTPClient http;
    http.setConnectTimeout(15000); // cobre o cold start do Render
    http.setTimeout(15000);
    http.begin(client, API_URL);
    http.addHeader("Content-Type", "application/json");

    // monta o JSON com as leituras dos sensores e faz o POST
    int httpCode = http.POST(json);
    http.end();
}
```

**Teste realizado com sucesso:** `HTTP Status: 201`, medição registrada no banco (`id: 1`).

> ⚠️ Em hardware físico (fora do simulador), o ESP32 se conecta normalmente à rede Wi-Fi real e pode usar tanto a URL do Render quanto um IP local (ex. `192.168.0.x`), sem necessidade de HTTPS/`WiFiClientSecure`, se preferir rodar a API localmente em vez de na nuvem.

---

## Testes

```powershell
python -m unittest -v
```

---

## Situação atual frente ao manual do PD-II

| Exigência do PD-II | Status |
|---|---|
| ESP32 | ✅ Validado em simulação (Cirkit Designer), pendente hardware físico |
| Sensores ambientais | ⚠️ Dados de teste fixos no firmware; falta integrar sensores reais (DHT22, BMP280, MQ-135, LDR, pluviômetro) |
| Comunicação com servidor | ✅ HTTP/HTTPS funcionando ponta a ponta |
| Backend em Python | ✅ `server.py`, publicado em produção |
| API para receber dados | ✅ `POST /api/v1/measurements` |
| Banco de dados | ✅ SQLite (local) — atenção à persistência em produção (ver seção de deploy) |
| Validação dos dados | ✅ Faixas de valores e validação ISO 8601 |
| Consulta dos dados | ✅ Endpoints GET |
| Estações meteorológicas | ✅ `/api/v1/stations` |
| Última medição | ✅ `/latest` |
| Dashboard | ⚠️ Ainda precisa ser desenvolvido |
| MQTT | ⚠️ Ainda não implementado (exigido pelo manual na etapa de firmware) |
| Geolocalização | ✅ Latitude/longitude já existem no modelo |
| Testes | ✅ `test_server.py` |
| Integração final | ⚠️ Falta juntar sensores reais + MQTT + dashboard |

---

## Próximas integrações

- **Sensores reais**: substituir os valores fixos de teste no firmware por leituras de DHT22, BMP280, MQ-135, LDR e pluviômetro.
- **MQTT**: implementar a etapa de firmware conforme exigido pelo manual (`ESP32 → MQTT → Broker → Backend Python`), mantendo a API REST atual para o consumo do dashboard.
- **Dashboard**: consumir `/latest` para cartões de status e `/api/v1/measurements` para gráficos históricos.
- **Segurança**: antes de uma publicação definitiva, adicionar uma chave de API por estação.
- **Persistência**: avaliar Render Disk ou migração para PostgreSQL se o volume de leituras crescer ou se a persistência entre deploys for necessária para a apresentação final.
