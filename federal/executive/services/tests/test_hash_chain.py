"""
اختبارات Hash Chain
الهدف: التحقق من سلامة سلسلة الكتل للتدقيق
النطاق: common/events.py
المالك: federal/executive/services
تاريخ الإنشاء: 2026-08-15
"""

import hashlib
import json

from amos_federation.common.events import GENESIS_HASH, compute_chain_hash


class TestChainHash:
    """اختبارات حساب بصمة السلسلة"""

    def test_genesis_hash_is_sha256(self):
        """الصورة الأولى يجب أن تكون بصمة صفرية صحيحة"""
        assert GENESIS_HASH.startswith("sha256:")
        assert len(GENESIS_HASH) == 71  # sha256: + 64 hex chars

    def test_chain_hash_is_deterministic(self):
        """نفس المدخلات تنتج نفس البصمة دائمًا"""
        prev = "sha256:abc123"
        data = {"event_id": "test-001", "event_type": "task.created"}
        h1 = compute_chain_hash(prev, data)
        h2 = compute_chain_hash(prev, data)
        assert h1 == h2

    def test_different_input_produces_different_hash(self):
        """مدخلات مختلفة تنتج بصمة مختلفة"""
        prev = "sha256:abc123"
        data1 = {"event_id": "test-001", "event_type": "task.created"}
        data2 = {"event_id": "test-002", "event_type": "task.created"}
        h1 = compute_chain_hash(prev, data1)
        h2 = compute_chain_hash(prev, data2)
        assert h1 != h2

    def test_order_matters(self):
        """ترتيب المفاتيح لا يؤثر (canonical JSON)"""
        prev = "sha256:abc123"
        h1 = compute_chain_hash(prev, {"a": 1, "b": 2})
        h2 = compute_chain_hash(prev, {"b": 2, "a": 1})
        assert h1 == h2

    def test_hash_format(self):
        """البصمة يجب أن تبدأ بـ sha256: وتحتوي 64 حرفًا سداسيًا"""
        h = compute_chain_hash(GENESIS_HASH, {"test": True})
        assert h.startswith("sha256:")
        hex_part = h.split(":")[1]
        assert len(hex_part) == 64
        int(hex_part, 16)  # يجب أن تكون سداسي عشري صالح

    def test_manual_verification(self):
        """تحقق يدوي: البصمة = SHA256(prev:canonical_json)"""
        prev = GENESIS_HASH
        data = {"event_id": "e1", "event_type": "test"}
        canonical = json.dumps(data, sort_keys=True, ensure_ascii=False)
        expected = f"sha256:{hashlib.sha256(f'{prev}:{canonical}'.encode()).hexdigest()}"
        actual = compute_chain_hash(prev, data)
        assert actual == expected
