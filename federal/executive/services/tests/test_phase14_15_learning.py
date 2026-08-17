"""
AMOS-Federation Phase 14-15 — Learning Loop + Evaluation Tests
الهدف: اختبار حلقة التعلم والتقييم ودورة Alpha/Beta/Gamma
النطاق: tests/test_phase14_15_learning.py
"""


class TestExperienceCollection:
    """14.1-14.4: تجميع الخبرات وإزالة التكرار."""

    def test_collect_experiences(self):
        from amos_federation.services.governance.learning_cycle import get_learning_cycle

        cycle = get_learning_cycle()
        experiences = [
            {"task": "analyze", "outcome": {"success": True}, "data": "a"},
            {"task": "analyze", "outcome": {"success": False}, "data": "b"},
        ]
        result = cycle.collect_experiences(experiences)
        assert result["total_samples"] == 2
        assert result["success"] == 1
        assert result["failure"] == 1
        assert result["deduplicated"] is True
        assert "bom_hash" in result

    def test_deduplication(self):
        """14.3: إزالة التكرار بـ SHA-256."""
        from amos_federation.services.governance.learning_cycle import get_learning_cycle

        cycle = get_learning_cycle()
        duplicate_exp = {"task": "same", "outcome": {"success": True}, "data": "x"}
        experiences = [duplicate_exp, duplicate_exp, duplicate_exp]
        result = cycle.collect_experiences(experiences)
        assert result["total_samples"] == 1  # deduped to 1

    def test_bom_hash(self):
        """14.4: Data BOM hash."""
        from amos_federation.services.governance.learning_cycle import get_learning_cycle

        cycle = get_learning_cycle()
        result = cycle.collect_experiences([{"task": "x", "outcome": {"success": True}}])
        assert len(result["bom_hash"]) == 64  # SHA-256 hex


class TestTrainingRun:
    """14.5-14.9: تدريب LoRA."""

    def test_start_training(self):
        from amos_federation.services.governance.learning_cycle import get_learning_cycle

        cycle = get_learning_cycle()
        dataset = cycle.collect_experiences([{"task": "x", "outcome": {"success": True}}])
        result = cycle.start_training(dataset["dataset_id"], "amos-alpha")
        assert result["status"] == "running"
        assert result["initial_loss"] == 2.5

    def test_complete_training(self):
        from amos_federation.services.governance.learning_cycle import get_learning_cycle

        cycle = get_learning_cycle()
        dataset = cycle.collect_experiences([{"task": "x", "outcome": {"success": True}}])
        train = cycle.start_training(dataset["dataset_id"])
        result = cycle.complete_training(train["run_id"], final_loss=0.5, epochs=3)
        assert result["status"] == "completed"
        assert result["final_loss"] == 0.5
        assert result["epochs"] == 3
        assert result["improvement"] > 0
        assert "artifact_path" in result
        assert result["knowledge_injection"] is True

    def test_stop_threshold_converged(self):
        """14.9: عتبة التوقف عند التقارب."""
        from amos_federation.services.governance.learning_cycle import get_learning_cycle

        cycle = get_learning_cycle()
        dataset = cycle.collect_experiences([{"task": "x", "outcome": {"success": True}}])
        train = cycle.start_training(dataset["dataset_id"])
        result = cycle.complete_training(train["run_id"], final_loss=0.05, epochs=3)
        assert result["status"] == "stopped"
        assert result["stopped_reason"] == "converged"

    def test_stop_threshold_no_improvement(self):
        """14.9: عتبة التوقف عند عدم التحسن."""
        from amos_federation.services.governance.learning_cycle import get_learning_cycle

        cycle = get_learning_cycle()
        dataset = cycle.collect_experiences([{"task": "x", "outcome": {"success": True}}])
        train = cycle.start_training(dataset["dataset_id"])
        result = cycle.complete_training(train["run_id"], final_loss=2.49, epochs=3)
        assert result["improvement"] < 0.01


class TestEvaluation:
    """15.1-15.6: التقييم والنقد."""

    def test_evaluate_model(self):
        from amos_federation.services.governance.learning_cycle import get_evaluation_system

        eval_sys = get_evaluation_system()
        result = eval_sys.evaluate_model(
            "amos-alpha", "bench-001", score=85, safety=95, critic_notes="أداء جيد"
        )
        assert result["score"] == 85
        assert result["safety_score"] == 95
        assert result["regression"] is False

    def test_regression_detection(self):
        """15.3: كشف النسيان الكارثي."""
        from amos_federation.services.governance.learning_cycle import get_evaluation_system

        eval_sys = get_evaluation_system()
        # تقييم أول
        eval_sys.evaluate_model("amos-regression-test", "bench-001", score=90)
        # تقييم ثاني أقل
        result = eval_sys.check_regression("amos-regression-test", current_score=80)
        assert result["regression"] is True

    def test_no_regression(self):
        from amos_federation.services.governance.learning_cycle import get_evaluation_system

        eval_sys = get_evaluation_system()
        eval_sys.evaluate_model("amos-no-regression", "bench-001", score=85)
        result = eval_sys.check_regression("amos-no-regression", current_score=88)
        assert result["regression"] is False


class TestModelPromotion:
    """15.7-15.13: Alpha/Beta/Gamma."""

    def test_three_tracks_initialized(self):
        """15.7: ثلاثة مسارات مهيأة."""
        from amos_federation.services.governance.learning_cycle import get_promotion_cycle

        cycle = get_promotion_cycle()
        versions = cycle.list_versions()
        tracks = {v["track"] for v in versions}
        assert "alpha" in tracks
        assert "beta" in tracks
        assert "gamma" in tracks

    def test_shadow_testing(self):
        """15.9: Shadow Testing."""
        from amos_federation.services.governance.learning_cycle import get_promotion_cycle

        cycle = get_promotion_cycle()
        versions = cycle.list_versions()
        alpha = next(v for v in versions if v["track"] == "alpha")
        beta = next(v for v in versions if v["track"] == "beta")
        result = cycle.start_shadow(alpha["version_id"], beta["version_id"])
        assert result["status"] == "shadow"

    def test_canary_deployment(self):
        """15.11: Canary Deployment."""
        from amos_federation.services.governance.learning_cycle import get_promotion_cycle

        cycle = get_promotion_cycle()
        versions = cycle.list_versions()
        beta = next(v for v in versions if v["track"] == "beta")
        result = cycle.start_canary(beta["version_id"], percentage=10)
        assert result["status"] == "canary"
        assert result["percentage"] == 10

    def test_promote_beta_to_alpha(self):
        """15.12: ترقية Beta إلى Alpha."""
        from amos_federation.services.governance.learning_cycle import get_promotion_cycle

        cycle = get_promotion_cycle()
        versions = cycle.list_versions()
        beta = next(v for v in versions if v["track"] == "beta")
        result = cycle.promote_beta_to_alpha(beta["version_id"], approved_by="king")
        assert result["promoted_to"] == "alpha"
        assert result["approved_by"] == "king"
