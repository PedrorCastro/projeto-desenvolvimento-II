import os
import tempfile
import unittest
from pathlib import Path

import server


class ValidationTests(unittest.TestCase):
    def setUp(self):
        self.valid = {
            "station_id": "campus-centro-01",
            "temperature_c": 25.4,
            "humidity_pct": 64.2,
            "pressure_hpa": 1012.8,
            "air_quality_raw": 390,
            "luminosity_raw": 780,
            "rainfall_mm": 0,
            "latitude": -23.5505,
            "longitude": -46.6333,
            "measured_at": "2026-09-13T15:00:00-03:00",
        }

    def test_accepts_valid_measurement_and_converts_time_to_utc(self):
        result, validation_error = server.validate_measurement(self.valid)
        self.assertIsNone(validation_error)
        self.assertEqual(result["measured_at"], "2026-09-13T18:00:00Z")

    def test_rejects_impossible_humidity(self):
        self.valid["humidity_pct"] = 102
        result, validation_error = server.validate_measurement(self.valid)
        self.assertIsNone(result)
        self.assertEqual(validation_error["field"], "humidity_pct")

    def test_initializes_sqlite_database(self):
        with tempfile.TemporaryDirectory() as directory:
            original_path = server.DATABASE_PATH
            server.DATABASE_PATH = Path(directory) / "test.db"
            try:
                server.initialize_database()
                with server.database_session() as connection:
                    table = connection.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='measurements'").fetchone()
                self.assertIsNotNone(table)
            finally:
                server.DATABASE_PATH = original_path


if __name__ == "__main__":
    unittest.main()
