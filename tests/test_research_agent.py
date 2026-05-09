import unittest

from prediction_market_lab.research_agent import offline_research_plan, plan_from_mapping


class ResearchAgentTests(unittest.TestCase):
    def test_offline_plan_proposes_search_urls_and_questions(self) -> None:
        plan = offline_research_plan("weather in Austin next week")

        self.assertEqual(plan.source, "offline")
        self.assertTrue(plan.clarifying_questions)
        self.assertTrue(plan.market_ideas)
        self.assertIn("kalshi", plan.market_ideas[0].search_urls[0])
        self.assertIn("settlement criteria are clear", plan.no_trade_warnings[0])

    def test_plan_from_mapping_bounds_untrusted_llm_json(self) -> None:
        raw = {
            "teaching_note": "Use primary sources.",
            "clarifying_questions": [{"prompt": "Which platform?", "why_it_matters": "Scope."}],
            "market_ideas": [
                {
                    "title": "A market",
                    "market_type": "deadline",
                    "why_promising": "Clear date.",
                    "what_to_verify": ["rules"],
                    "search_urls": ["https://example.invalid"],
                    "risks": ["spread"],
                }
            ],
            "no_trade_warnings": ["No source, no trade."],
            "next_action": "Choose one.",
        }

        plan = plan_from_mapping("topic", raw, source="llm")

        self.assertEqual(plan.source, "llm")
        self.assertEqual(plan.market_ideas[0].title, "A market")
        self.assertEqual(plan.clarifying_questions[0].prompt, "Which platform?")


if __name__ == "__main__":
    unittest.main()
