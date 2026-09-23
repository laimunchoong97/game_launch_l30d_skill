import unittest

from scripts.render_report import render_report


class RenderReportTests(unittest.TestCase):
    def test_report_contains_all_sections_and_escapes_text(self):
        report = {
            "snapshot": {"game": "<Example Game>", "release_phase": "Pre-launch", "data_captured": "2026-09-21"},
            "scores": {"demand_potential": 75, "purchase_intent": 60, "launch_momentum": 80, "reception_health": 70, "market_markdown_risk": 45, "evidence_confidence": "Medium"},
            "recommendation": {"posture": "Test buy", "summary": "Use a controlled allocation.", "primary_reason": "Momentum", "main_risk": "Discounting", "change_trigger": "Review deterioration"},
            "score_breakdown": [],
            "demand_evidence": {},
            "purchase_intent": {},
            "reception": {},
            "comparables": {},
            "price_risk": {},
            "sales_player_evidence": {},
            "inventory": {},
            "reorder_stop": {},
            "coverage": {},
        }
        rendered = render_report(report)
        self.assertIn("&lt;Example Game&gt;", rendered)
        self.assertNotIn("<Example Game>", rendered)
        for heading in ("The decision", "Community pulse", "Score dashboard", "Evidence coverage"):
            self.assertIn(heading, rendered)
        self.assertIn("<!doctype html>", rendered)


if __name__ == "__main__":
    unittest.main()
