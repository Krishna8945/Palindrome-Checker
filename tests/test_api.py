"""
Integration Tests for Flask Web Application Endpoints
"""

import unittest
import json
from app import app
from database.db import db_instance


class TestFlaskAPI(unittest.TestCase):

    def setUp(self):
        app.config["TESTING"] = True
        self.client = app.test_client()
        db_instance.initialize_seed_data()

    def test_get_batches(self):
        res = self.client.get("/api/batches")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertGreaterEqual(len(data), 5)
        self.assertIn("batch_id", data[0])

    def test_simulate_telemetry(self):
        res = self.client.post(
            "/api/batches/BATCH-DAIRY-101/simulate",
            json={"temp_delta_c": 4.5, "duration_min": 30.0}
        )
        self.assertEqual(res.status_code, 200)
        updated = res.get_json()
        self.assertGreaterEqual(updated["telemetry_history"][-1]["temperature_c"], 6.0)

    def test_run_pipeline_single(self):
        res = self.client.post("/api/pipeline/run/BATCH-FISH-202")
        self.assertEqual(res.status_code, 200)
        trace = res.get_json()
        self.assertIn("stages", trace)
        self.assertIn("final_plan", trace)
        self.assertGreater(trace["total_latency_ms"], 0)

    def test_audit_ledger_verification(self):
        res = self.client.get("/api/audit-ledger/verify")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data["integrity_intact"])

    def test_bigquery_export(self):
        # Run a pipeline first to populate rows
        self.client.post("/api/pipeline/run/BATCH-DAIRY-101")
        res = self.client.get("/api/bigquery/export")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertIn("streaming_rows", data)
        self.assertIn("bigquery_ddl", data)
        self.assertIn("analytical_sql", data)


if __name__ == "__main__":
    unittest.main()
