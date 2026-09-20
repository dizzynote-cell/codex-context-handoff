from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

HOOKS = Path(__file__).resolve().parents[1] / "plugins" / "context-handoff" / "hooks"
sys.path.insert(0, str(HOOKS))

from hook_state import backfill_current_session, inspect_transcript, load_state, save_bootstrap_state


class HookBackfillTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        root = Path(self.temp.name)
        self.old_plugin_data = os.environ.get("PLUGIN_DATA")
        self.old_bootstrap = os.environ.get("CONTEXT_HANDOFF_BOOTSTRAP_DATA")
        os.environ["PLUGIN_DATA"] = str(root / "plugin-data")
        os.environ["CONTEXT_HANDOFF_BOOTSTRAP_DATA"] = str(root / "bootstrap")
        self.transcript = root / "rollout.jsonl"
        rows = [
            {"type": "session_meta", "payload": {"id": "session-1", "cwd": "C:/work"}},
            {"type": "event_msg", "payload": {"type": "compacted"}},
            {"type": "compacted"},
            {"type": "response_item", "item": {"type": "compacted"}},
            {"type": "message", "payload": {"text": "the word compacted is not an event"}},
        ]
        self.transcript.write_text(
            "\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8"
        )

    def tearDown(self) -> None:
        if self.old_plugin_data is None:
            os.environ.pop("PLUGIN_DATA", None)
        else:
            os.environ["PLUGIN_DATA"] = self.old_plugin_data
        if self.old_bootstrap is None:
            os.environ.pop("CONTEXT_HANDOFF_BOOTSTRAP_DATA", None)
        else:
            os.environ["CONTEXT_HANDOFF_BOOTSTRAP_DATA"] = self.old_bootstrap
        self.temp.cleanup()

    def test_inspect_counts_only_structured_compaction_events(self) -> None:
        result = inspect_transcript(self.transcript)
        self.assertEqual(result["session_id"], "session-1")
        self.assertEqual(result["compaction_count"], 3)

    def test_backfill_is_idempotent_and_uses_maximum(self) -> None:
        first = backfill_current_session("session-1", self.transcript)
        second = backfill_current_session("session-1", self.transcript)
        self.assertEqual(first["compaction_count"], 3)
        self.assertEqual(second["compaction_count"], 3)

    def test_bootstrap_count_is_merged_into_live_state(self) -> None:
        save_bootstrap_state("session-2", {
            "session_id": "session-2",
            "compaction_count": 7,
            "eligible": True,
            "cwd": "C:/old",
            "compact_turn_ids": [],
        })
        state = load_state("session-2")
        self.assertEqual(state["compaction_count"], 7)
        self.assertTrue(state["eligible"])

    def test_wrong_session_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            backfill_current_session("another-session", self.transcript)


if __name__ == "__main__":
    unittest.main()
