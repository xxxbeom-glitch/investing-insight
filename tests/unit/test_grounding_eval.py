from __future__ import annotations

import importlib.util
import json
import shutil
import sys
from pathlib import Path
from types import ModuleType

import pytest

from app.agents.claim_support import claim_is_supported, factual_payload

ROOT = Path(__file__).resolve().parents[2]
GDIR = ROOT / "scripts" / "evals" / "grounding"
if str(GDIR) not in sys.path:
    sys.path.insert(0, str(GDIR))


def _load(name: str) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, GDIR / f"{name}.py")
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


compare = _load("compare")
redteam = _load("redteam")
runner = _load("runner")


class FakeClient:
    def __init__(self, responses: list[dict]) -> None:
        self.responses = list(responses)
        self.calls: list[str] = []
        self.payloads: list[dict] = []
        self.usage_totals = {"input_tokens": 0, "output_tokens": 0, "requests": 0}

    def create_json(self, system_prompt, user_payload, *, output_schema, schema_name, **kwargs):
        del system_prompt, output_schema, kwargs
        self.calls.append(schema_name)
        self.payloads.append(user_payload)
        self.usage_totals["requests"] += 1
        if not self.responses:
            raise AssertionError(f"unexpected LLM call {schema_name}")
        return self.responses.pop(0)


def test_seed_replay_matches_claim_is_supported():
    evidence = runner.load_evidence()
    seed = runner.load_seed(evidence)
    assert len(seed) >= 40
    replay = runner.replay_seed(seed)
    assert replay["failed"] == 0, replay["mismatches"]
    for row in seed:
        actual = claim_is_supported(row["claim"], row["evidence_id"], [row["evidence_item"]])
        assert compare.gate_label(actual) == row["expected_gate"]


def test_classify_matrix():
    assert compare.classify(judge_expected="UNSUPPORTED", gate_actual="SUPPORTED") == "FP"
    assert compare.severity("FP") == "CRITICAL"
    assert compare.classify(judge_expected="SUPPORTED", gate_actual="UNSUPPORTED") == "FN"
    assert compare.classify(judge_expected="SUPPORTED", gate_actual="SUPPORTED") == "TP"
    assert compare.classify(judge_expected="UNSUPPORTED", gate_actual="UNSUPPORTED") == "TN"
    assert compare.classify(judge_expected=None, gate_actual="UNSUPPORTED") == "TN"


def test_duplicate_claim_key():
    a = compare.claim_key("Regime is expansion", "regime")
    b = compare.claim_key("  regime   is   expansion  ", "regime")
    assert a == b


def test_runner_replay_only(tmp_path: Path):
    report = runner.run(llm=False, out_dir=tmp_path)
    assert report["ok"] is True
    assert report["exit_code"] == 0
    assert report["llm"] is None
    assert report["replay"]["failed"] == 0
    assert (tmp_path / "report.json").is_file()
    assert (tmp_path / "report.md").is_file()
    text = (tmp_path / "report.md").read_text(encoding="utf-8")
    assert "OPENAI" not in text
    assert "sk-" not in text


def test_unsupported_skips_judge(tmp_path: Path):
    client = FakeClient(
        [
            {
                "attacks": [
                    {"claim": "expansion is as_of and revenue surged", "attack_class": "leftover_fact"}
                ]
            }
        ]
    )
    report = runner.run(llm=True, max_attacks=1, out_dir=tmp_path, client=client)
    assert report["ok"] is True
    assert report["llm"]["judge_calls"] == 0
    assert report["llm"]["gate_supported"] == 0
    assert "grounding_judge" not in client.calls
    assert report["llm"]["matrix"]["TN"] >= 1


def test_fp_from_judge_fails(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    bait = "as_of equals expansion yesterday"
    real = runner.claim_is_supported

    def wrapped(text, evidence_id, evidence):
        if text == bait:
            return True
        return real(text, evidence_id, evidence)

    monkeypatch.setattr(runner, "claim_is_supported", wrapped)
    client = FakeClient(
        [
            {"attacks": [{"claim": bait, "attack_class": "reverse_relation"}]},
            {
                "expected": "UNSUPPORTED",
                "reason_code": "reverse_relation",
                "reason": "value bound to the wrong field",
            },
        ]
    )
    report = runner.run(llm=True, max_attacks=1, out_dir=tmp_path, client=client)
    assert report["ok"] is False
    assert report["exit_code"] == 1
    fp = report["llm"]["false_positives"][0]
    assert fp["gate_actual"] == "SUPPORTED"
    assert fp["judge_expected"] == "UNSUPPORTED"
    assert fp["matrix"] == "FP"
    assert fp["severity"] == "CRITICAL"
    assert report["llm"]["matrix"]["FP"] == 1
    md = (tmp_path / "report.md").read_text(encoding="utf-8")
    assert "FP / CRITICAL" in md
    assert bait in md
    judge_payload = client.payloads[1]
    assert "gate" not in judge_payload
    assert "claim_is_supported" not in str(judge_payload)
    assert "missing" not in judge_payload
    assert set(judge_payload.keys()) == {"evidence_id", "factual_payload", "claim"}


def test_redteam_payload_is_factual_only():
    evidence = runner.load_evidence()
    item = evidence["daily_price"]
    payload = factual_payload(item)
    assert "ref" not in payload
    assert "kind" not in payload
    user = redteam.user_payload(
        evidence_id="price:1",
        factual_payload=payload,
        known_attacks=["2026 is close"],
        max_new=2,
    )
    assert set(user.keys()) == {"evidence_id", "factual_payload", "known_attacks", "max_new", "instruction"}
    assert "claim_is_supported" not in str(user)
    assert user["factual_payload"] == payload


pre_rereview = _load("pre_rereview")
self_remediate = _load("self_remediate")


def test_web_build_uses_resolvable_npm():
    cmd = next(c for name, c, _cwd in pre_rereview.steps(llm=False) if name == "web_build")
    assert Path(cmd[0]).name.lower() in {"npm.cmd", "npm.exe", "npm"}
    assert shutil.which(cmd[0]) or Path(cmd[0]).is_file()


def test_web_build_env_forces_production(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("NODE_ENV", "development")
    env = pre_rereview._step_env("web_build")
    assert env["NODE_ENV"] == "production"
    other = pre_rereview._step_env("pytest")
    assert other["NODE_ENV"] == "development"


def test_self_remediate_pass_resets(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(self_remediate, "STATE_PATH", tmp_path / "loop_state.json")

    def verify(*, llm: bool = True):
        del llm
        return {"ok": True, "fp_count": 0, "fp_fingerprint": None, "failed_step": None}

    result = self_remediate.run(verify_fn=verify)
    assert result["exit_code"] == 0
    assert result["action"] == "pass"
    state = json.loads((tmp_path / "loop_state.json").read_text(encoding="utf-8"))
    assert state["attempts"] == 0


def test_self_remediate_same_fp_stops(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(self_remediate, "STATE_PATH", tmp_path / "loop_state.json")
    fp = compare.fp_fingerprint([{"claim": "expansion is as_of", "evidence_id": "regime"}])

    def verify(*, llm: bool = True):
        del llm
        return {"ok": False, "fp_count": 1, "fp_fingerprint": fp, "failed_step": "grounding_llm"}

    first = self_remediate.run(verify_fn=verify)
    assert first["exit_code"] == 1
    assert first["action"] == "continue"
    second = self_remediate.run(verify_fn=verify)
    assert second["exit_code"] == 2
    assert second["action"] == "stop_repeat"


def test_self_remediate_max_attempts_stops(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(self_remediate, "STATE_PATH", tmp_path / "loop_state.json")
    monkeypatch.setattr(self_remediate, "_max_attempts", lambda path=None: 3)
    n = {"i": 0}

    def verify(*, llm: bool = True):
        del llm
        n["i"] += 1
        return {
            "ok": False,
            "fp_count": 1,
            "fp_fingerprint": f"fp-{n['i']}",
            "failed_step": "grounding_llm",
        }

    codes = [self_remediate.run(verify_fn=verify)["action"] for _ in range(3)]
    assert codes[0] == "continue"
    assert codes[1] == "continue"
    assert codes[2] == "stop_max"
    fourth = self_remediate.run(verify_fn=verify)
    assert fourth["exit_code"] == 2
    assert fourth["action"] == "stop_max"
