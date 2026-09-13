# API Meteorológica - MeteoCidade

API em Python para receber dados enviados pelo ESP32, validá-los e armazená-los em SQLite. Ela atende à etapa de backend do PD-II e já permite que o dashboard consuma dados reais.

## Como executar

No PowerShell, dentro desta pasta:

```powershell
python server.py
```

O serviço ficará disponível em `http://127.0.0.1:8000`. O arquivo `meteo.db` será criado automaticamente. Para permitir acesso pela rede local (por exemplo, por um ESP32 conectado no mesmo Wi-Fi), defina o host antes de iniciar:

```powershell
$env:METEO_HOST = "0.0.0.0"
python server.py
```

## Endpoints

| Método | Rota | Uso |
|---|---|---|
| GET | `/health` | Verifica se a API está disponível. |
| POST | `/api/v1/measurements` | Registra uma medição do ESP32. |
| GET | `/api/v1/measurements?station_id=campus-centro-01&limit=50` | Lista medições, da mais recente para a mais antiga. |
| GET | `/api/v1/stations/campus-centro-01/latest` | Retorna a leitura mais recente da estação. |
| GET | `/api/v1/stations` | Lista estações e quantidade de registros. |

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

## Testes

```powershell
python -m unittest -v
```

## Próximas integrações

1. No ESP32, use `HTTPClient` para realizar o POST do JSON a cada intervalo de coleta.
2. No dashboard, consulte o endpoint `latest` para os cartões e `measurements` para os gráficos.
3. Antes da publicação, adicione uma chave de API por estação e troque SQLite por PostgreSQL se houver muitas leituras simultâneas.
