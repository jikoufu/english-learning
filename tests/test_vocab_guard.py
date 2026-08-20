import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "tools"))
import vocab_guard


def entry(word, body):
    return {"date": "2026-08-20", "word": word, "lines": [f"### {word}\n", *[x + "\n" for x in body.splitlines()]]}


LEGAL = """- 中文意思：测试
- 读音：TES-t；音标：/test/
- 分开读：test，重音在 TES
- 词性：名词 noun；动词 verb
- 不同词性意思：名词：测试；动词：测试
- 构词分析：这是基础词，没有单独的核心动词。
- 核心词说明：这是基础词，核心意思是测试。
- 例句：This is a test. 这是测试。
- 记忆提示：test 就是测试。
"""


class VocabGuardTests(unittest.TestCase):
    def test_legal_entry_passes(self):
        self.assertEqual(vocab_guard.check_entry(entry("test", LEGAL)), [])

    def test_missing_field_fails(self):
        self.assertTrue(any(v["rule_id"] == "required_memory" for v in vocab_guard.check_entry(entry("test", LEGAL.replace("- 记忆提示：test 就是测试。\n", "")))))

    def test_polysemy_must_be_defined(self):
        body = LEGAL.replace("- 不同词性意思：名词：测试；动词：测试\n", "")
        self.assertTrue(any(v["rule_id"] == "polysemy_meanings" for v in vocab_guard.check_entry(entry("test", body))))

    def test_changed_baseline_hash_is_not_allowed(self):
        e = entry("test", LEGAL.replace("- 记忆提示：test 就是测试。\n", ""))
        v = vocab_guard.check_entry(e)
        changed = dict(v[0], content_hash="changed")
        self.assertNotEqual(vocab_guard.key(changed), vocab_guard.key(v[0]))

    def test_baseline_cannot_expand(self):
        old = {("rule", "2026-08-20", "test", "old")}
        new = [{"rule_id": "rule", "date": "2026-08-20", "word": "test", "content_hash": "new"}]
        self.assertFalse(vocab_guard.baseline_update_allowed(old, new))
        self.assertTrue(vocab_guard.baseline_update_allowed(old, []))

    def test_verb_form_requires_every_field(self):
        body = LEGAL.replace("词性：名词 noun；动词 verb", "词性：动词 verb").replace("不同词性意思：名词：测试；动词：测试", "")
        body += "- 当前形式：made 的过去式\n"
        errors = {v["rule_id"] for v in vocab_guard.check_entry(entry("made", body))}
        self.assertIn("verb_form_base", errors)
        self.assertIn("verb_form_paradigm", errors)
        self.assertIn("verb_form_passive", errors)

    def test_noun_plural_is_not_verb_form(self):
        body = LEGAL.replace("词性：名词 noun；动词 verb", "词性：名词 noun").replace("不同词性意思：名词：测试；动词：测试", "")
        self.assertFalse(any(v["rule_id"].startswith("verb_form_") for v in vocab_guard.check_entry(entry("tests", body))))

    def test_date_ends_previous_entry(self):
        entries = list(vocab_guard.parse_entries("## 2026-08-19\n### old\n- x\n## 2026-08-20\n### new\n- y\n"))
        self.assertEqual([e["date"] for e in entries], ["2026-08-19", "2026-08-20"])
        self.assertNotIn("- y", "".join(entries[0]["lines"]))

    def test_nested_meaning_does_not_satisfy_outer_field(self):
        body = LEGAL.replace("- 中文意思：测试\n", "  - 中文意思：内部测试\n")
        self.assertTrue(any(v["rule_id"] == "required_meaning" for v in vocab_guard.check_entry(entry("test", body))))

    def test_nested_ipa_does_not_satisfy_outer_pronunciation(self):
        body = LEGAL.replace("- 读音：TES-t；音标：/test/\n", "- 读音：TES-t\n  - 读音：内部；音标：/test/\n")
        self.assertTrue(any(v["rule_id"] == "pronunciation_ipa" for v in vocab_guard.check_entry(entry("test", body))))

    def test_baseline_candidate_must_be_head_subset(self):
        self.assertTrue(vocab_guard.baseline_keys_are_subset({("a",)}, {("a",), ("b",)}))
        self.assertFalse(vocab_guard.baseline_keys_are_subset({("c",)}, {("a",), ("b",)}))


if __name__ == "__main__":
    unittest.main()
