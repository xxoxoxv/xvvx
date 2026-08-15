"""الهدف: إثبات أن بوابات CLI السيادية تفشل فعلًا عند المخالفة لا تكتفي بالطبع.

المالك: tests/sovereignty/ — التاج
تاريخ الإنشاء: 2026-08-16
تاريخ آخر تعديل: 2026-08-16

رمز الخروج هو الدليل: 0 سليم · 2 مرفوض دستوريًا · 1 فشل بوابة.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from core.sovereignty import cli
from core.sovereignty.cli import main

REPO_ROOT = Path(__file__).resolve().parents[2]


class TestSovereigntyCheckGate:
    def test_gate_passes_on_a_healthy_state(self, capsys: pytest.CaptureFixture[str]) -> None:
        assert main(["sovereignty-check"]) == 0
        out = capsys.readouterr().out
        assert "المادة العاشرة سارية" in out
        assert "بلا راية تجاوز" in out

    def test_gate_fails_when_article_010_is_removed(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        monkeypatch.setattr(cli, "_ARTICLE_010", REPO_ROOT / "does-not-exist.md")
        assert main(["sovereignty-check"]) == 1
        assert "المادة العاشرة مفقودة" in capsys.readouterr().err

    def test_gate_fails_when_royal_rules_are_weakened(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """حذف قاعدة ملكية واحدة يجب أن يُفشل CI — لا يمر بصمت."""
        from core.constitutional_engine.engine import ConstitutionalEngine

        real = ConstitutionalEngine.coverage

        def weakened(self: ConstitutionalEngine) -> dict[str, int]:
            data = dict(real(self))
            data["A010"] = 3
            return data

        monkeypatch.setattr(ConstitutionalEngine, "coverage", weakened)
        assert main(["sovereignty-check"]) == 1
        assert "قواعد المادة العاشرة 3" in capsys.readouterr().err

    def test_gate_fails_when_an_immune_clause_disappears(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        monkeypatch.setattr(cli, "IMMUNE_CLAUSES", frozenset({"memory_preservation"}))
        assert main(["sovereignty-check"]) == 1
        assert "فُقد من قائمة النصوص المحصَّنة" in capsys.readouterr().err

    def test_gate_fails_when_gateway_gains_a_bypass_flag(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """محاكاة مبرمج يضيف force=True إلى البوابة — البوابة تكشفه."""
        from core.sovereignty.gateway import SovereignGateway

        def tainted(self, request, executor, force: bool = False):  # noqa: ANN001, ANN202
            return executor()

        monkeypatch.setattr(SovereignGateway, "execute", tainted)
        assert main(["sovereignty-check"]) == 1
        assert "راية تجاوز" in capsys.readouterr().err

    def test_gate_fails_when_an_article_loses_its_guard(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        from core.constitutional_engine.engine import ConstitutionalEngine

        monkeypatch.setattr(
            ConstitutionalEngine, "unguarded_articles", lambda self: ("A007",)
        )
        assert main(["sovereignty-check"]) == 1
        assert "مواد بلا حراسة" in capsys.readouterr().err


class TestGateCommand:
    def test_forbidden_action_exits_two_and_names_the_article(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        code = main(["gate", "--actor", "agent", "--action", "amend_constitution"])
        assert code == 2
        out = capsys.readouterr().out
        assert "A010" in out
        assert "لم يُستدعَ المُنفِّذ" in out

    def test_bypass_attempt_exits_two(self, capsys: pytest.CaptureFixture[str]) -> None:
        assert main(["gate", "--actor", "system", "--action", "bypass_gateway"]) == 2
        assert "R-010-4" in capsys.readouterr().out

    def test_royal_action_without_decree_exits_two(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        assert main(["gate", "--actor", "royal", "--action", "create_state"]) == 2
        assert "A010" in capsys.readouterr().out

    def test_lawful_action_exits_zero(self, capsys: pytest.CaptureFixture[str]) -> None:
        assert main(["gate", "--actor", "executive", "--action", "orchestrate"]) == 0
        assert "ALLOW" in capsys.readouterr().out


class TestCrownCommands:
    def test_status_reports_unprovisioned_repository(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        assert main(["crown-status"]) == 0
        assert "التاج" in capsys.readouterr().out

    def test_status_reports_a_provisioned_crown(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        from core.sovereignty import crown as crown_module

        registry = tmp_path / "CROWN_KEYS.json"
        monkeypatch.setattr(crown_module, "CROWN_KEYS_PATH", registry)
        crown_module.provision_crown(tmp_path / "outside" / "k.pem", registry_path=registry)
        assert main(["crown-status"]) == 0
        assert "✓ مُنصَّب" in capsys.readouterr().out

    def test_provision_succeeds_outside_the_repository(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        from core.sovereignty import crown as crown_module

        monkeypatch.setattr(crown_module, "CROWN_KEYS_PATH", tmp_path / "CROWN_KEYS.json")
        out_key = tmp_path / "vault" / "crown.pem"
        assert main(["provision-crown", "--out", str(out_key)]) == 0
        out = capsys.readouterr().out
        assert "نُصِّب التاج" in out
        assert "انقل المفتاح الخاص" in out
        assert out_key.exists()

    def test_provision_inside_the_repository_exits_one(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        from core.sovereignty import crown as crown_module

        monkeypatch.setattr(crown_module, "CROWN_KEYS_PATH", tmp_path / "CROWN_KEYS.json")
        leaked = REPO_ROOT / "royal" / "crown" / "leaked.pem"
        assert main(["provision-crown", "--out", str(leaked)]) == 1
        assert "داخل المستودع" in capsys.readouterr().err
        assert not leaked.exists()


class TestPrerogativesCommand:
    def test_prints_valid_json_with_all_four_vocabularies(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        assert main(["prerogatives"]) == 0
        payload = json.loads(capsys.readouterr().out)
        assert "amend_constitution" in payload["royal_exclusive_actions"]
        assert "abolish_royal_authority" in payload["royal_authority_erosion_actions"]
        assert "bypass_gateway" in payload["federalism_bypass_actions"]
        assert "royal_sovereignty" in payload["immune_clauses"]


class TestParser:
    def test_missing_command_exits(self) -> None:
        with pytest.raises(SystemExit):
            main([])

    def test_unknown_actor_is_rejected(self) -> None:
        with pytest.raises(SystemExit):
            main(["gate", "--actor", "emperor", "--action", "execute_task"])
