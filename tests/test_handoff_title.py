import importlib.util
import unittest
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "plugins" / "context-handoff" / "scripts" / "context_handoff.py"
spec = importlib.util.spec_from_file_location("context_handoff", SCRIPT)
context_handoff = importlib.util.module_from_spec(spec)
spec.loader.exec_module(context_handoff)


class ContinuationTitleTests(unittest.TestCase):
    def test_number_follows_source_conversation_not_handoff_file(self):
        self.assertEqual(
            context_handoff.continuation_title("继续开发7 自有服务器版本", "继续开发 1｜正式测试并发稳定性"),
            "继续开发 8｜正式测试并发稳定性",
        )

    def test_unknown_source_cannot_invent_number(self):
        with self.assertRaisesRegex(RuntimeError, "source task title"):
            context_handoff.continuation_title("", "继续开发 1｜下一阶段")

    def test_unnumbered_title_is_preserved(self):
        self.assertEqual(context_handoff.continuation_title("新功能", "下一阶段｜正式测试"), "下一阶段｜正式测试")


if __name__ == "__main__":
    unittest.main()
