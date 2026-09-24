"""API HTTP para a estação meteorológica inteligente.

Não depende de bibliotecas externas: pode ser executada em qualquer instalação
recente do Python. Para produção, substitua o servidor embutido por um servidor
WSGI/ASGI e configure autenticação para cada estação.
"""

from __future__ import annotations

import json
import os
import sqlite3
from contextlib import contextmanager
from datetime import UTC, datetime
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

BASE_DIR = Path(__file__).resolve().parent
DATABASE_PATH = Path(os.environ.get("METEO_DATABASE", BASE_DIR / "meteo.db"))
MAX_LIMIT = 200


def utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def database_connection() -> sqlite3.Connection:
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    return connection


@contextmanager
def database_session():
    """Abre, confirma e fecha a conexão, inclusive no Windows."""
    connection = database_connection()
    try:
        yield connection
        connection.commit()
    finally:
        connection.close()


def initialize_database() -> None:
    with database_session() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS measurements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                station_id TEXT NOT NULL,
                measured_at TEXT NOT NULL,
                received_at TEXT NOT NULL,
                temperature_c REAL NOT NULL,
                humidity_pct REAL NOT NULL,
                pressure_hpa REAL NOT NULL,
                air_quality_raw REAL,
                luminosity_raw REAL,
                rainfall_mm REAL,
                latitude REAL,
                longitude REAL
            )
            """
        )
        connection.execute(
            "CREATE INDEX IF NOT EXISTS idx_measurements_station_time "
            "ON measurements(station_id, measured_at DESC)"
        )


def error(message: str, field: str | None = None) -> dict:
    result = {"error": message}
    if field:
        result["field"] = field
    return result


def validate_measurement(payload: object) -> tuple[dict | None, dict | None]:
    if not isinstance(payload, dict):
        return None, error("O corpo da requisição deve ser um objeto JSON.")

    station_id = payload.get("station_id")
    if not isinstance(station_id, str) or not station_id.strip() or len(station_id) > 64:
        return None, error("Informe station_id com até 64 caracteres.", "station_id")

    fields = {
        "temperature_c": (-50, 70, True),
        "humidity_pct": (0, 100, True),
        "pressure_hpa": (300, 1200, True),
        "air_quality_raw": (0, 4095, False),
        "luminosity_raw": (0, 4095, False),
        "rainfall_mm": (0, 500, False),
        "latitude": (-90, 90, False),
        "longitude": (-180, 180, False),
    }
    data = {"station_id": station_id.strip()}
    for name, (minimum, maximum, required) in fields.items():
        value = payload.get(name)
        if value is None and not required:
            data[name] = None
            continue
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            return None, error("O valor deve ser numérico.", name)
        if not minimum <= value <= maximum:
            return None, error(f"O valor deve estar entre {minimum} e {maximum}.", name)
        data[name] = float(value)

    measured_at = payload.get("measured_at", utc_now())
    if not isinstance(measured_at, str):
        return None, error("A data deve ser uma string ISO 8601.", "measured_at")
    try:
        parsed = datetime.fromisoformat(measured_at.replace("Z", "+00:00"))
    except ValueError:
        return None, error("Use data no formato ISO 8601, por exemplo 2026-09-13T14:30:00Z.", "measured_at")
    if parsed.tzinfo is None:
        return None, error("A data precisa informar o fuso horário (Z ou -03:00).", "measured_at")
    data["measured_at"] = parsed.astimezone(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    return data, None


def row_to_dict(row: sqlite3.Row) -> dict:
    return dict(row)


class MeteoRequestHandler(BaseHTTPRequestHandler):
    server_version = "MeteoCidade/1.0"

    def log_message(self, format: str, *args: object) -> None:
        # Mantém o log de requisições útil sem expor conteúdo de medições.
        print(f"[{utc_now()}] {self.address_string()} - {format % args}")

    def send_json(self, status: HTTPStatus, data: object) -> None:
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, X-API-Key")
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self) -> None:
        self.send_json(HTTPStatus.NO_CONTENT, {})

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        route = parsed.path.rstrip("/") or "/"
        query = parse_qs(parsed.query)
        if route == "/health":
            self.send_json(HTTPStatus.OK, {"status": "ok", "service": "api-meteorologica", "time": utc_now()})
            return
        if route == "/api/v1/stations":
            with database_session() as connection:
                rows = connection.execute(
                    "SELECT station_id, MAX(measured_at) AS last_measurement_at, COUNT(*) AS measurement_count "
                    "FROM measurements GROUP BY station_id ORDER BY station_id"
                ).fetchall()
            self.send_json(HTTPStatus.OK, {"stations": [row_to_dict(row) for row in rows]})
            return
        if route == "/api/v1/measurements":
            self.list_measurements(query)
            return
        prefix = "/api/v1/stations/"
        if route.startswith(prefix) and route.endswith("/latest"):
            station_id = route[len(prefix):-len("/latest")].strip("/")
            self.latest_measurement(station_id)
            return
        self.send_json(HTTPStatus.NOT_FOUND, error("Rota não encontrada."))

    def list_measurements(self, query: dict[str, list[str]]) -> None:
        try:
            limit = int(query.get("limit", ["50"])[0])
            if not 1 <= limit <= MAX_LIMIT:
                raise ValueError
        except ValueError:
            self.send_json(HTTPStatus.BAD_REQUEST, error(f"limit deve ser um inteiro de 1 a {MAX_LIMIT}.", "limit"))
            return
        station_id = query.get("station_id", [None])[0]
        sql = "SELECT * FROM measurements"
        params: list[object] = []
        if station_id:
            sql += " WHERE station_id = ?"
            params.append(station_id)
        sql += " ORDER BY measured_at DESC LIMIT ?"
        params.append(limit)
        with database_session() as connection:
            rows = connection.execute(sql, params).fetchall()
        self.send_json(HTTPStatus.OK, {"measurements": [row_to_dict(row) for row in rows], "count": len(rows)})

    def latest_measurement(self, station_id: str) -> None:
        if not station_id:
            self.send_json(HTTPStatus.BAD_REQUEST, error("Informe o identificador da estação."))
            return
        with database_session() as connection:
            row = connection.execute(
                "SELECT * FROM measurements WHERE station_id = ? ORDER BY measured_at DESC LIMIT 1", (station_id,)
            ).fetchone()
        if row is None:
            self.send_json(HTTPStatus.NOT_FOUND, error("Nenhuma medição encontrada para esta estação."))
            return
        self.send_json(HTTPStatus.OK, row_to_dict(row))

    def do_POST(self) -> None:
        if urlparse(self.path).path.rstrip("/") != "/api/v1/measurements":
            self.send_json(HTTPStatus.NOT_FOUND, error("Rota não encontrada."))
            return
        try:
            content_length = int(self.headers.get("Content-Length", "0"))
            if not 0 < content_length <= 16_384:
                raise ValueError
            payload = json.loads(self.rfile.read(content_length).decode("utf-8"))
        except (ValueError, UnicodeDecodeError, json.JSONDecodeError):
            self.send_json(HTTPStatus.BAD_REQUEST, error("Envie um JSON UTF-8 válido de até 16 KB."))
            return
        measurement, validation_error = validate_measurement(payload)
        if validation_error:
            self.send_json(HTTPStatus.UNPROCESSABLE_ENTITY, validation_error)
            return
        assert measurement is not None
        received_at = utc_now()
        columns = ["station_id", "measured_at", "received_at", "temperature_c", "humidity_pct", "pressure_hpa", "air_quality_raw", "luminosity_raw", "rainfall_mm", "latitude", "longitude"]
        values = [measurement["station_id"], measurement["measured_at"], received_at] + [measurement[column] for column in columns[3:]]
        with database_session() as connection:
            cursor = connection.execute(
                f"INSERT INTO measurements ({', '.join(columns)}) VALUES ({', '.join('?' for _ in columns)})", values
            )
            row = connection.execute("SELECT * FROM measurements WHERE id = ?", (cursor.lastrowid,)).fetchone()
        self.send_json(HTTPStatus.CREATED, row_to_dict(row))


def run(host: str = "127.0.0.1", port: int = 8000) -> None:
    initialize_database()
    print(f"API meteorológica disponível em http://{host}:{port}")
    ThreadingHTTPServer((host, port), MeteoRequestHandler).serve_forever()


if __name__ == "__main__":
    run(host=os.environ.get("METEO_HOST", "0.0.0.0"), port=int(os.environ.get("METEO_PORT", "8000")))
