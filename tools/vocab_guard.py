#!/usr/bin/env python3
"""Machine checks for the structured vocabulary Markdown file."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VOCAB = ROOT / "英语学习.md"
BASELINE = ROOT / ".vocab-baseline.json"
DATE_RE = re.compile(r"^##\s+(\d{4}-\d{2}-\d{2})\s*$")
ENTRY_RE = re.compile(r"^###\s+(?:\d+[.)]\s*)?(.+?)\s*$")
IPA_RE = re.compile(r"音标\s*[:：].*?/[^\n]+/")

REQUIRED = {
    "meaning": "中文意思",
    "pronunciation": "读音",
    "syllables": "分开读",
    "part_of_speech": "词性",
    "word_formation": "构词分析",
    "example": "例句",
    "memory": "记忆提示",
}


def parse_entries(text: str):
    date = None
    current = None
    for line in text.splitlines(keepends=True):
        m = DATE_RE.match(line.rstrip("\r\n"))
        if m:
            if current:
                yield current
                current = None
            date = m.group(1)
            continue
        m = ENTRY_RE.match(line.rstrip("\r\n"))
        if m:
            if current:
                yield current
            current = {"date": date or "unknown", "word": m.group(1).strip(), "lines": [line]}
        elif current:
            current["lines"].append(line)
    if current:
        yield current


def violation(entry, rule_id, detail):
    content = "".join(entry["lines"])
    return {
        "rule_id": rule_id,
        "date": entry["date"],
        "word": entry["word"],
        "content_hash": hashlib.sha256(content.encode("utf-8")).hexdigest(),
        "detail": detail,
    }


def check_entry(entry):
    body = "".join(entry["lines"])
    result = []
    for rule_id, label in REQUIRED.items():
        if not re.search(rf"^-\s*{re.escape(label)}\s*[:：]", body, re.M):
            result.append(violation(entry, f"required_{rule_id}", f"缺少字段：{label}"))
    pronunciation = re.search(r"^-\s*读音\s*[:：](.+)$", body, re.M)
    if pronunciation and not IPA_RE.search("- 读音：" + pronunciation.group(1)):
        result.append(violation(entry, "pronunciation_ipa", "读音字段必须包含 IPA 音标"))
    pos = re.search(r"^-\s*词性\s*[:：](.+)$", body, re.M)
    if pos and ("；" in pos.group(1) or ";" in pos.group(1)) and "不同词性意思" not in body:
        result.append(violation(entry, "polysemy_meanings", "多词性必须分别说明不同词性意思"))
    word = re.sub(r"^\d+[.)]\s*", "", entry["word"]).strip().lower()
    pos_is_verb = bool(re.search(r"^\s*-\s*词性\s*[:：].*(?:verb|动词)", body, re.M | re.I))
    explicit_form = bool(re.search(r"过去式|过去分词|第三人称单数|ing 形式|变化形式|当前形式", body, re.I))
    if (pos_is_verb and re.search(r"(?:s|es|ies|ed|ing)$", word)) or explicit_form:
        form_fields = {
            "current": "当前形式",
            "base": "动词原形",
            "paradigm": "动词变化",
            "passive": "被动常用形式",
        }
        for field_id, label in form_fields.items():
            if not re.search(re.escape(label), body):
                result.append(violation(entry, f"verb_form_{field_id}", f"动词变化形式缺少字段：{label}"))
    core_present = re.search(r"核心(?:动词|形容词|词)\s*[:：]", body) and not re.search(r"核心(?:动词|形容词|词)说明", body)
    if core_present and not re.search(r"核心(?:动词|形容词|词)[\s\S]*?构词分析\s*[:：]", body):
        result.append(violation(entry, "core_formation", "核心词展开必须包含内部构词分析"))
    if "后缀" in body:
        for line in body.splitlines():
            if "后缀" in line and not re.search(r"名词|形容词|动词|副词|表示|功能|作用|含义|意思", line):
                result.append(violation(entry, "suffix_function", "后缀说明必须包含词性功能和大致含义"))
                break
    if not re.search(r"核心(?:动词|形容词|词)(?:说明)?\s*[:：]|这是(?:基础词|基础动词|复合词)", body):
        result.append(violation(entry, "core_word_marker", "必须明确核心词，或说明是基础词、基础动词、复合词"))
    return result


def all_violations():
    return [v for e in parse_entries(VOCAB.read_text(encoding="utf-8")) for v in check_entry(e)]


def key(v):
    return (v["rule_id"], v["date"], v["word"], v["content_hash"])


def load_baseline():
    if not BASELINE.exists():
        return set()
    data = json.loads(BASELINE.read_text(encoding="utf-8"))
    return {key(v) for v in data.get("violations", [])}


def baseline_update_allowed(old_keys, violations):
    """Return whether a new baseline only removes known violation keys."""
    return {key(v) for v in violations}.issubset(old_keys)


def baseline_keys_are_subset(candidate, reference):
    """Pure set check used for both on-disk and HEAD baseline protection."""
    return set(candidate).issubset(set(reference))


def load_head_baseline_keys():
    if not (ROOT / ".git").exists():
        return None
    proc = subprocess.run(
        ["git", "-C", str(ROOT), "show", "HEAD:.vocab-baseline.json"],
        capture_output=True, text=True, encoding="utf-8",
    )
    if proc.returncode == 0:
        data = json.loads(proc.stdout)
        return {key(v) for v in data.get("violations", [])}
    if "does not exist" in proc.stderr or "exists on disk, but not in 'HEAD'" in proc.stderr:
        return None
    raise RuntimeError(proc.stderr.strip() or "unable to read HEAD baseline")


def write_baseline(violations):
    old_keys = load_baseline()
    if BASELINE.exists() and not baseline_update_allowed(old_keys, violations):
        raise ValueError("refusing to expand baseline: new or changed violation key detected")
    head_keys = load_head_baseline_keys()
    if head_keys is not None and not baseline_keys_are_subset((key(v) for v in violations), head_keys):
        raise ValueError("refusing to expand baseline beyond Git HEAD baseline")
    data = {"version": 1, "source": VOCAB.name, "violations": violations}
    BASELINE.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("check", "baseline"))
    args = parser.parse_args()
    violations = all_violations()
    if args.command == "baseline":
        try:
            write_baseline(violations)
        except (ValueError, RuntimeError) as exc:
            print(f"baseline failed: {exc}", file=sys.stderr)
            return 1
        print(f"baseline: recorded {len(violations)} violation(s)")
        return 0
    current_keys = {key(v) for v in violations}
    head_keys = load_head_baseline_keys()
    if head_keys is not None and not baseline_keys_are_subset(current_keys, head_keys):
        print("check failed: current baseline would expand beyond Git HEAD baseline", file=sys.stderr)
        return 1
    fresh = [v for v in violations if key(v) not in load_baseline()]
    if fresh:
        for v in fresh:
            print(f"{v['date']} / {v['word']} / {v['rule_id']}: {v['detail']}", file=sys.stderr)
        print(f"check failed: {len(fresh)} new or changed violation(s)", file=sys.stderr)
        return 1
    print(f"check passed: {len(violations)} known violation(s), 0 new")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
