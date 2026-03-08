import unittest

from lead_score_agent import score_lead


class LeadScoreAgentTests(unittest.TestCase):
    def test_score_ranking_is_reasonable(self):
        high = score_lead(
            {
                "title": "Need automation for B2B SaaS onboarding",
                "content": "Budget $8000, delivery in 2 weeks. Need API integration with HubSpot + AWS + Postgres.",
            },
            {
                "is_b2b": True,
                "budget": 8000,
                "urgency": 8,
                "tech_stack": ["AWS", "Postgres", "HubSpot API"],
                "category": "automation",
            },
        )

        medium = score_lead(
            {
                "title": "想做一个营销 chatbot",
                "content": "预算可以谈，最好这个月做完。",
            },
            {
                "is_b2b": True,
                "budget": "negotiable",
                "urgency": 6,
                "requirements": "basic chatbot for lead qualification",
            },
        )

        low = score_lead(
            {
                "title": "Anyone can build me a bot?",
                "content": "No details yet, maybe for gambling traffic growth.",
            },
            {
                "is_b2b": False,
                "budget": None,
                "urgency": 3,
            },
        )

        self.assertGreater(high["score"], medium["score"])
        self.assertGreater(medium["score"], low["score"])

    def test_output_schema_fields(self):
        result = score_lead(
            {"title": "Need scraping service", "content": "Budget 1000 USD, urgent"},
            {"is_b2b": True, "budget": 1000, "urgency": 9},
        )

        self.assertTrue(0 <= result["score"] <= 100)
        self.assertIn(result["priority"], {"P0", "P1", "P2"})
        self.assertIn(
            result["category"],
            {"automation", "scraping", "chatbot", "marketing", "data", "other"},
        )
        self.assertTrue(0 <= result["estimated_value_usd"] <= 10000)
        self.assertTrue(1 <= result["urgency"] <= 10)
        self.assertTrue(1 <= result["budget_signal"] <= 10)
        self.assertIsInstance(result["reasoning_bullets"], list)
        self.assertTrue(all(isinstance(i, str) for i in result["reasoning_bullets"]))


if __name__ == "__main__":
    unittest.main()
