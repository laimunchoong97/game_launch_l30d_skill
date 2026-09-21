import unittest

from scripts.steam_public import normalize_appdetails, normalize_reviews


class SteamPublicTests(unittest.TestCase):
    def test_normalize_appdetails(self):
        payload = {
            "123": {
                "success": True,
                "data": {
                    "name": "Example Game",
                    "type": "game",
                    "developers": ["Studio"],
                    "publishers": ["Publisher"],
                    "genres": [{"description": "Action"}],
                    "categories": [{"description": "Single-player"}],
                    "release_date": {"date": "1 Jan, 2026", "coming_soon": True},
                    "platforms": {"windows": True, "mac": False, "linux": False},
                    "price_overview": {
                        "currency": "USD",
                        "initial": 1999,
                        "final": 1499,
                        "discount_percent": 25,
                        "initial_formatted": "$19.99",
                        "final_formatted": "$14.99",
                    },
                },
            }
        }
        normalized = normalize_appdetails(payload, 123)
        self.assertEqual(normalized["name"], "Example Game")
        self.assertEqual(normalized["price"]["discount_percent"], 25)
        self.assertTrue(normalized["coming_soon"])

    def test_normalize_reviews(self):
        normalized = normalize_reviews(
            {
                "success": 1,
                "query_summary": {
                    "review_score": 8,
                    "review_score_desc": "Very Positive",
                    "total_reviews": 100,
                    "total_positive": 80,
                    "total_negative": 20,
                },
                "reviews": [],
            }
        )
        self.assertEqual(normalized["positive_percent"], 80.0)
        self.assertEqual(normalized["total_reviews"], 100)


if __name__ == "__main__":
    unittest.main()
