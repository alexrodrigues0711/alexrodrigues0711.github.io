import os
import unittest

from fastapi.testclient import TestClient

os.environ.pop("GROQ_API_KEY", None)

from revenue_iq.api.app import app  # noqa: E402


class ApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def test_health(self):
        response = self.client.get("/api/health")
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["status"], "ok")
        self.assertEqual(payload["rows"], 2402)

    def test_dashboard(self):
        response = self.client.get("/api/dashboard", params={"region": "sul", "period": "6"})
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(len(payload["monthly"]), 6)
        self.assertGreater(payload["kpis"]["revenue"], 0)

    def test_analysis_uses_demo_without_key(self):
        original_key = os.environ.pop("GROQ_API_KEY", None)
        try:
            response = self.client.post(
                "/api/analyze",
                json={
                    "question": "Por que a receita caiu em março?",
                    "filters": {"segment": "all", "region": "brasil", "period": "12"},
                },
            )
        finally:
            if original_key is not None:
                os.environ["GROQ_API_KEY"] = original_key
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["mode"], "demo")
        self.assertEqual(len(payload["evidence"]), 3)


if __name__ == "__main__":
    unittest.main()
