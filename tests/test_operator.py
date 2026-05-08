import json
from pathlib import Path
import tempfile
import unittest

from prediction_market_lab.operator import CandidateMarket, OperatorStore, Thesis, validate_thesis


class OperatorWorkflowTests(unittest.TestCase):
    def make_store(self) -> OperatorStore:
        self.tempdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tempdir.cleanup)
        return OperatorStore(Path(self.tempdir.name) / "operator_store.json")

    def seed_candidate(self, store: OperatorStore) -> None:
        store.upsert_candidate(CandidateMarket(candidate_id="cand-1", title="Will event resolve yes?", market_probability=0.4))

    def seed_actionable_thesis(self, store: OperatorStore) -> None:
        self.seed_candidate(store)
        store.upsert_thesis(
            Thesis(
                thesis_id="thesis-1",
                candidate_id="cand-1",
                question="Will event resolve yes?",
                belief_probability=0.55,
                market_probability=0.4,
                evidence=("primary source",),
                risks=("resolution ambiguity",),
                resolution_criteria="Official resolver says yes.",
                time_horizon="2026-06-01",
                expected_value_notes="Belief exceeds market by 15 points.",
            )
        )

    def test_incomplete_thesis_is_labeled_non_actionable(self) -> None:
        result = validate_thesis({"thesis_id": "t", "candidate_id": "c", "question": "?"})

        self.assertFalse(result.actionable)
        self.assertEqual(result.status, "non-actionable")
        self.assertIn("belief_probability is required", result.errors)
        self.assertIn("at least one risk/caveat is required", result.errors)

    def test_trade_recommendation_rejects_non_actionable_thesis(self) -> None:
        store = self.make_store()
        self.seed_candidate(store)
        store.upsert_thesis(Thesis(thesis_id="thesis-1", candidate_id="cand-1", question="Will event resolve yes?"))

        with self.assertRaisesRegex(ValueError, "non-actionable"):
            store.record_recommendation("thesis-1", "trade", "not enough information")

    def test_no_trade_can_be_recorded_for_non_actionable_thesis(self) -> None:
        store = self.make_store()
        self.seed_candidate(store)
        store.upsert_thesis(Thesis(thesis_id="thesis-1", candidate_id="cand-1", question="Will event resolve yes?"))

        record = store.record_recommendation("thesis-1", "no-trade", "missing evidence")

        self.assertEqual(record["recommendation"], "no-trade")
        self.assertEqual(record["thesis_status"], "non-actionable")

    def test_weekly_review_includes_scale_gate_status(self) -> None:
        store = self.make_store()
        self.seed_actionable_thesis(store)
        store.record_recommendation("thesis-1", "trade", "edge is documented")
        store.record_decision("thesis-1", "approved", "human accepts risk")
        store.record_position_event("thesis-1", "entry", 10, 0.41, "manual external action recorded")

        review = store.weekly_review("2026-05-04", "2026-05-10")

        self.assertEqual(review["summary"]["trade_recommendation_count"], 1)
        self.assertEqual(review["scale_gate_status"]["status"], "hold")
        self.assertIn("mark-to-market", review["scale_gate_status"]["blockers"][0])
        self.assertIn("no exchange/betting APIs called", review["safety_boundary"])

    def test_import_candidates_from_json_shape(self) -> None:
        store = self.make_store()
        count = store.import_candidates([
            {"candidate_id": "cand-1", "title": "Will imported market resolve yes?", "market_probability": 0.51}
        ])

        self.assertEqual(count, 1)
        self.assertEqual(store.data["candidates"]["cand-1"]["title"], "Will imported market resolve yes?")
        json.dumps(store.data)


if __name__ == "__main__":
    unittest.main()
