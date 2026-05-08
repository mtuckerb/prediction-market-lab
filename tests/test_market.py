import unittest

from prediction_market_lab import MarketQuestion


class MarketQuestionTests(unittest.TestCase):
    def test_question_tracks_evidence_count(self) -> None:
        question = MarketQuestion(
            title="Will the sample event resolve yes?",
            current_probability=0.42,
            evidence=("source A", "source B"),
        )

        self.assertEqual(question.evidence_count(), 2)

    def test_probability_must_be_between_zero_and_one(self) -> None:
        with self.assertRaises(ValueError):
            MarketQuestion(title="Invalid", current_probability=1.01)

    def test_title_must_not_be_blank(self) -> None:
        with self.assertRaises(ValueError):
            MarketQuestion(title="   ", current_probability=0.5)


if __name__ == "__main__":
    unittest.main()
