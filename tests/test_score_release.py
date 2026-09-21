import unittest

from scripts.score_release import score


class ScoreReleaseTests(unittest.TestCase):
    def test_missing_data_reduces_coverage_not_score_to_zero(self):
        result = score(
            {
                "phase": "prelaunch",
                "signals": {"audience_intent": 5, "momentum": None},
                "source_count": 2,
                "source_agreement": "medium",
            }
        )
        self.assertGreater(result["demand_or_reception_score"]["score"], 0)
        self.assertLess(result["demand_or_reception_score"]["coverage"], 100)
        self.assertEqual(result["evidence_confidence"], "Low")

    def test_high_coverage_and_agreement(self):
        signals = {
            "audience_intent": 5,
            "momentum": 4,
            "developer_franchise": 4,
            "comparables": 4,
            "creator_community": 4,
            "price_fit": 4,
            "competition": 4,
        }
        result = score(
            {"phase": "prelaunch", "signals": signals, "source_count": 5, "source_agreement": "high"}
        )
        self.assertEqual(result["demand_or_reception_score"]["coverage"], 100.0)
        self.assertEqual(result["evidence_confidence"], "High")


if __name__ == "__main__":
    unittest.main()
