from pathlib import Path
import tempfile
import unittest

from prediction_market_lab.operator import CandidateMarket, OperatorStore, Thesis
from prediction_market_lab.tui import OperatorTUI, PromptIO, evaluate_candidate


class ScriptedIO(PromptIO):
    def __init__(self, responses: list[str]) -> None:
        self.responses = responses
        self.outputs: list[str] = []
        super().__init__(self._input, self.outputs.append)

    def _input(self, prompt: str) -> str:
        self.outputs.append(prompt)
        if not self.responses:
            raise AssertionError(f"no scripted response for prompt: {prompt}")
        return self.responses.pop(0)

    def pause(self) -> None:
        self.outputs.append("pause")


class OperatorTUITests(unittest.TestCase):
    def make_store(self) -> OperatorStore:
        self.tempdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tempdir.cleanup)
        return OperatorStore(Path(self.tempdir.name) / "operator_store.json")

    def test_create_candidate_guides_and_saves_record(self) -> None:
        store = self.make_store()
        io = ScriptedIO([
            "",  # default candidate id
            "Will a sample event resolve YES?",
            "https://example.invalid/market",
            "manual",
            "0.42",
            "human supplied candidate",
        ])
        tui = OperatorTUI(store, io)

        record = tui.create_candidate()

        self.assertEqual(record["candidate_id"], "cand-001")
        self.assertEqual(record["market_probability"], 0.42)
        self.assertTrue(any("Autonomous mode would ingest candidate markets" in line for line in io.outputs))

    def test_preview_agent_loop_names_human_stop_before_trade(self) -> None:
        store = self.make_store()
        io = ScriptedIO([])
        tui = OperatorTUI(store, io)

        steps = tui.preview_agent_loop()

        self.assertTrue(any("Wait for the human final decision" in step for step in steps))
        self.assertTrue(any("without executing anything" in step for step in steps))

    def test_evaluate_candidate_rejects_missing_settlement_source(self) -> None:
        result = evaluate_candidate(
            title="Will event resolve yes?",
            settlement_source="",
            criteria="YES if official result is posted.",
            resolution_date="2026-06-01",
            spread_ok="yes",
            why_wrong="Market may be ignoring the published schedule.",
            evidence=("schedule page",),
        )

        self.assertEqual(result.status, "reject")
        self.assertIn("missing named primary settlement source", result.blockers)

    def test_thesis_wizard_saves_thesis_and_default_watchlist_recommendation(self) -> None:
        store = self.make_store()
        store.upsert_candidate(CandidateMarket(candidate_id="cand-1", title="Will event resolve yes?", market_probability=0.4))
        io = ScriptedIO([
            "cand-1",
            "",  # default thesis id
            "",  # default question
            "0.50",
            "0.57",
            "0.57",
            "0.40",
            "Official resolver posts YES by deadline.",
            "2026-06-01",
            "official schedule says event is planned",
            "",  # finish evidence
            "resolution criteria could be interpreted narrowly",
            "",  # finish risks
            "",  # default EV note
        ])
        tui = OperatorTUI(store, io)

        payload = tui.thesis_wizard()

        self.assertEqual(payload["thesis_status"], "actionable")
        self.assertEqual(payload["default_recommendation"]["recommendation"], "watchlist")
        self.assertEqual(store.data["theses"]["thesis-001"]["belief_probability"], 0.57)

    def test_autonomous_market_wizard_plans_saves_and_starts_thesis(self) -> None:
        store = self.make_store()
        io = ScriptedIO([
            "weather in Austin next week",
            "Kalshi",  # platform answer
            "near-term",  # time horizon answer
            "NOAA",  # trusted source answer
            "1",  # choose first idea
            "https://example.invalid/market",  # actual URL
            "0.40",  # market probability
            "yes",  # save candidate
            "",  # default candidate id
            "no",  # do not continue to thesis in this unit test
        ])
        tui = OperatorTUI(store, io)

        payload = tui.autonomous_market_wizard()

        self.assertIn("saved_candidate", payload)
        self.assertEqual(store.data["candidates"]["cand-001"]["platform"], "llm-assisted")
        self.assertTrue(any("What kind of market would you like to predict" in line for line in io.outputs))

    def test_record_recommendation_from_existing_thesis(self) -> None:
        store = self.make_store()
        store.upsert_candidate(CandidateMarket(candidate_id="cand-1", title="Will event resolve yes?", market_probability=0.4))
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
        io = ScriptedIO(["thesis-1", "watchlist", "need stronger confirmation"])
        tui = OperatorTUI(store, io)

        payload = tui.record_recommendation()

        self.assertEqual(payload["recommendation"]["recommendation"], "watchlist")
        self.assertEqual(payload["recommendation"]["thesis_status"], "actionable")


if __name__ == "__main__":
    unittest.main()
