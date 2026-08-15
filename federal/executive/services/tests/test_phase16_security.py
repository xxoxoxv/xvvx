"""
AMOS-Federation Phase 16 — Production Security Tests
الهدف: اختبار أمان الإنتاج
النطاق: tests/test_phase16_security.py
"""


class TestRBAC:
    """16.1: RBAC."""

    def test_roles_initialized(self):
        from amos_federation.services.governance.security import get_rbac

        rbac = get_rbac()
        roles = rbac.list_roles()
        role_ids = {r["role_id"] for r in roles}
        assert "king" in role_ids
        assert "royal" in role_ids
        assert "agent" in role_ids
        assert "public" in role_ids

    def test_create_session(self):
        from amos_federation.services.governance.security import get_rbac

        rbac = get_rbac()
        result = rbac.create_session("king", "king", ip="127.0.0.1")
        assert "session_token" in result
        assert result["level"] == 5

    def test_check_permission_king(self):
        from amos_federation.services.governance.security import get_rbac

        rbac = get_rbac()
        session = rbac.create_session("king_user", "king")
        # king has wildcard permission
        assert rbac.check_permission(session["session_token"], "execute:all") is True
        assert rbac.check_permission(session["session_token"], "anything") is True

    def test_check_permission_agent(self):
        from amos_federation.services.governance.security import get_rbac

        rbac = get_rbac()
        session = rbac.create_session("agent_user", "agent")
        assert rbac.check_permission(session["session_token"], "execute:tools") is True
        assert rbac.check_permission(session["session_token"], "manage:all") is False

    def test_check_permission_public(self):
        from amos_federation.services.governance.security import get_rbac

        rbac = get_rbac()
        session = rbac.create_session("public_user", "public")
        assert rbac.check_permission(session["session_token"], "read:public") is True
        assert rbac.check_permission(session["session_token"], "execute:tools") is False

    def test_invalid_session(self):
        from amos_federation.services.governance.security import get_rbac

        rbac = get_rbac()
        assert rbac.check_permission("invalid-token", "read:public") is False

    def test_role_levels(self):
        from amos_federation.services.governance.security import get_rbac

        rbac = get_rbac()
        assert rbac.get_role_level("king") == 5
        assert rbac.get_role_level("public") == 0
        assert rbac.get_role_level("agent") == 2


class TestSecretVault:
    """16.2: Secret Vault."""

    def test_store_and_verify(self):
        from amos_federation.services.governance.security import get_secret_vault

        vault = get_secret_vault()
        vault.store_secret("test-api-key", "secret123")
        assert vault.verify_secret("test-api-key", "secret123") is True
        assert vault.verify_secret("test-api-key", "wrong") is False

    def test_store_with_scope(self):
        from amos_federation.services.governance.security import get_secret_vault

        vault = get_secret_vault()
        vault.store_secret("state-finance-key", "fin-secret", scope="finance")
        secrets = vault.list_secrets()
        assert any(s["key"] == "state-finance-key" for s in secrets)

    def test_rotate_secret(self):
        from amos_federation.services.governance.security import get_secret_vault

        vault = get_secret_vault()
        vault.store_secret("rotate-key", "old-value")
        vault.store_secret("rotate-key", "new-value")  # rotation
        assert vault.verify_secret("rotate-key", "new-value") is True
        assert vault.verify_secret("rotate-key", "old-value") is False


class TestRateLimiter:
    """16.4: Rate Limiting."""

    def test_first_request_allowed(self):
        from amos_federation.services.governance.security import get_rate_limiter

        limiter = get_rate_limiter()
        result = limiter.check_rate("test-ip-1", "/api/test", max_requests=5)
        assert result["allowed"] is True
        assert result["count"] == 1

    def test_rate_limit_exceeded(self):
        from amos_federation.services.governance.security import get_rate_limiter

        limiter = get_rate_limiter()
        identifier = "test-ip-exceed"
        for _i in range(5):
            limiter.check_rate(identifier, "/api/limited", max_requests=5)
        result = limiter.check_rate(identifier, "/api/limited", max_requests=5)
        assert result["allowed"] is False

    def test_different_endpoints_independent(self):
        from amos_federation.services.governance.security import get_rate_limiter

        limiter = get_rate_limiter()
        for _i in range(3):
            limiter.check_rate("test-ip-multi", "/api/a", max_requests=3)
        result = limiter.check_rate("test-ip-multi", "/api/b", max_requests=3)
        assert result["allowed"] is True


class TestTLSCertificates:
    """16.3: TLS Certificates."""

    def test_issue_certificate(self):
        from amos_federation.services.governance.security import get_tls_manager

        tls = get_tls_manager()
        result = tls.issue_certificate("amos-federation.gov")
        assert "cert_id" in result
        assert result["common_name"] == "amos-federation.gov"

    def test_verify_certificate(self):
        from amos_federation.services.governance.security import get_tls_manager

        tls = get_tls_manager()
        cert = tls.issue_certificate("test.gov")
        result = tls.verify_certificate(cert["cert_id"])
        assert result["valid"] is True

    def test_verify_nonexistent_cert(self):
        from amos_federation.services.governance.security import get_tls_manager

        tls = get_tls_manager()
        result = tls.verify_certificate("nonexistent-cert")
        assert result["valid"] is False
