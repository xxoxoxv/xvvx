"""
AMOS-Federation State Registry
الهدف: السجل الفدرالي للمؤسسات والإدارات والمسؤولين — أول نظام دولة فوق العمود التنفيذي
النطاق: services/state_registry
المالك: federal/executive/services
تاريخ الإنشاء: 2026-08-17 (R7-A)
"""

from amos_federation.services.state_registry.service import (
    StateRegistry,
    get_state_registry,
    reset_state_registry,
)

__all__ = ["StateRegistry", "get_state_registry", "reset_state_registry"]
