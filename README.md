# MeteoCidade

### Sistema meteorológico para monitoramento ambiental urbano

O **MeteoCidade** é o projeto desenvolvido no **Projeto Desenvolvimento II** para coletar, validar, armazenar e apresentar dados ambientais de uma estação meteorológica.

```text
ESP32 / sensores  →  API Python  →  SQLite  →  Dashboard React
       coleta          validação       dados       visualização
```

| Componente | Tecnologia | Situação |
|---|---|---|
| Estação | ESP32-S3 / C++ | Validada em simulação |
| Backend | Python + HTTP + SQLite | Publicado no Render |
| Frontend | React + Vite | Dashboard implementado |
| Deploy | Render | API online e frontend preparado |

## Acesso rápido

- **API em produção:** [projeto-desenvolvimento-ii.onrender.com](https://projeto-desenvolvimento-ii.onrender.com)
- **Health check:** [/health](https://projeto-desenvolvimento-ii.onrender.com/health)
- **Branch de desenvolvimento:** `codex/organizar-dashboard`

## Dashboard

O dashboard apresenta a leitura mais recente da estação e o histórico de medições em uma interface responsiva.

- Temperatura, umidade e pressão atmosférica.
- Qualidade do ar, luminosidade e chuva acumulada.
- Gráficos de tendência de temperatura e umidade.
- Tabela de leituras recentes.
- Status da estação e horário da última sincronização.
- Atualização automática a cada 30 segundos.
- Estados de carregamento, erro e API indisponível.

O frontend não possui uma tela separada de estações neste momento. O foco atual é a estação do campus e a visualização clara dos seus dados.

## Estrutura do projeto

```text
projeto-desenvolvimento-II/
├── back/
│   ├── api/
│   │   ├── server.py
│   │   ├── requirements.txt
│   │   └── test_server.py
│   └── firmware/
│       └── ESP32.cpp
├── front/
│   ├── src/
│   │   ├── main.jsx
│   │   └── styles.css
│   ├── index.html
│   ├── package.json
│   └── vite.config.js
├── render.yaml
└── README.md
```

## API

| Método | Rota | Uso |
|---|---|---|
| `GET` | `/health` | Verifica a disponibilidade da API |
| `POST` | `/api/v1/measurements` | Registra uma medição do ESP32 |
| `GET` | `/api/v1/measurements?station_id=esp32-campus-01&limit=50` | Lista medições recentes |
| `GET` | `/api/v1/stations/esp32-campus-01/latest` | Retorna a última medição |
| `GET` | `/api/v1/stations` | Lista estações e quantidade de registros |

Os campos obrigatórios de uma medição são `station_id`, `temperature_c`, `humidity_pct` e `pressure_hpa`. Os demais sensores são opcionais. A API valida faixas físicas, datas ISO 8601 e converte os horários para UTC.

### Exemplo de medição

```json
{
  "station_id": "esp32-campus-01",
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

## Como executar localmente

### API

No PowerShell, dentro de `back/api`:

```powershell
python server.py
```

A API ficará disponível em `http://127.0.0.1:8000`. O banco `meteo.db` será criado automaticamente.

Para permitir acesso pela rede local:

```powershell
$env:METEO_HOST = "0.0.0.0"
python server.py
```

### Dashboard

No PowerShell, dentro de `front`:

```powershell
npm install
npm run dev
```

Por padrão, o dashboard usa a API do Render. Para usar a API local, crie `front/.env`:

```env
VITE_API_URL=http://127.0.0.1:8000
```

Para gerar a versão de produção:

```powershell
npm run build
```

## Testes

Dentro de `back/api`:

```powershell
python -m unittest -v
```

Os testes cobrem a aceitação de medições válidas, conversão de horário, rejeição de umidade impossível e inicialização do banco SQLite.

## Publicação no Render

### API existente

A API está configurada como **Web Service**:

| Campo | Valor |
|---|---|
| Root Directory | `back/api` |
| Build Command | `pip install -r requirements.txt` |
| Start Command | `python server.py` |
| Health Check Path | `/health` |

### Frontend

O frontend deve ser publicado como **Static Site** no mesmo workspace do Render:

| Campo | Valor |
|---|---|
| Branch | `main` |
| Root Directory | `front` |
| Build Command | `npm install && npm run build` |
| Publish Directory | `dist` |
| Environment Variable | `VITE_API_URL=https://projeto-desenvolvimento-ii.onrender.com` |

O arquivo `render.yaml` contém uma configuração de Blueprint para os dois serviços. Como a API já existe, a publicação manual do Static Site evita criar uma segunda API e duplicar o armazenamento.

O plano gratuito do Render pode suspender serviços após um período de inatividade. A primeira requisição depois disso pode levar alguns segundos. O SQLite também utiliza disco efêmero no plano gratuito; os dados não são permanentes após reinicializações ou novos deploys.

## Integração com ESP32

O firmware em `back/firmware/ESP32.cpp` conecta o ESP32 ao Wi-Fi e envia as medições para:

```text
https://projeto-desenvolvimento-ii.onrender.com/api/v1/measurements
```

A comunicação foi validada com um ESP32-S3 simulado no Cirkit Designer, utilizando a rede virtual `CirkitWifi`. Os valores atuais do firmware ainda são fixos para teste; a integração com os sensores físicos será feita em uma etapa posterior.

## Situação atual

| Item | Status |
|---|---|
| Organização em backend e frontend | ✅ Concluída |
| Comunicação ESP32 → API | ✅ Validada em simulação |
| API Python | ✅ Publicada |
| Validação de medições | ✅ Implementada |
| Banco SQLite | ✅ Implementado |
| Dashboard React | ✅ Implementado |
| Histórico e gráficos | ✅ Implementados |
| Sensores físicos | ⚠️ Próxima etapa |
| MQTT | ⚠️ Ainda não implementado |
| Persistência definitiva | ⚠️ Avaliar PostgreSQL ou Render Disk |

## Próximas etapas

- Integrar DHT22, BMP280, MQ-135, LDR e pluviômetro reais.
- Implementar o fluxo `ESP32 → MQTT → broker → backend`.
- Adicionar autenticação ou chave de API por estação.
- Avaliar PostgreSQL para manter as medições em produção.
- Adicionar filtros de período e análises mais detalhadas no histórico.

## Documentação complementar

- [Guia de publicação do frontend no Render](Guia_publicacao_frontend_Render.docx)
- [Relatório acadêmico do projeto](Relatorio_Projeto_Desenvolvimento_II_MeteoCidade.docx)

## Créditos

Projeto acadêmico desenvolvido para o **Projeto Desenvolvimento II - UNIP**.
