from pathlib import Path
import unittest

from revenue_iq.api.analytics import Filters, dashboard_snapshot, demo_analysis, load_data


ROOT = Path(__file__).resolve().parents[2]
DATA = load_data(ROOT / "revenue_iq" / "data" / "revenue_data.csv")


class AnalyticsTests(unittest.TestCase):
    def test_csv_is_complete(self):
        self.assertEqual(len(DATA), 2402)
        self.assertFalse(DATA.isna().any().any())

    def test_dashboard_snapshot_reconciles(self):
        snapshot = dashboard_snapshot(DATA, Filters())
        monthly_revenue = sum(item["revenue"] for item in snapshot["monthly"])
        region_revenue = sum(item["revenue"] for item in snapshot["regions"])
        self.assertAlmostEqual(monthly_revenue, snapshot["kpis"]["revenue"], places=1)
        self.assertAlmostEqual(region_revenue, snapshot["kpis"]["revenue"], places=1)
        self.assertAlmostEqual(sum(item["share"] for item in snapshot["channels"]), 100.0, delta=0.2)

    def test_filters_change_dashboard(self):
        total = dashboard_snapshot(DATA, Filters())
        south = dashboard_snapshot(DATA, Filters(region="sul", period="6"))
        self.assertLess(south["kpis"]["revenue"], total["kpis"]["revenue"])
        self.assertEqual(len(south["monthly"]), 6)

    def test_march_question_has_verified_evidence(self):
        snapshot = dashboard_snapshot(DATA, Filters())
        response = demo_analysis("Por que a receita caiu em março?", DATA, snapshot)
        ids = {item["id"] for item in response["evidence"]}
        self.assertIn("MARCH_CHANGE", ids)
        self.assertIn("MARCH_REGION", ids)
        self.assertIn("MARCH_PRODUCT", ids)


if __name__ == "__main__":
    unittest.main()
