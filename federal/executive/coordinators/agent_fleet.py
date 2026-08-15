"""
AMOS-Federation Agent Fleet Coordinator
الهدف: إدارة وتنسيق وتوزيع المهام على أسطول من آلاف الوكلاء (هدف 2800+)
النطاق: federal/executive/coordinators
المالك: federal/executive
تاريخ الإنشاء: 2026-08-15

المبادئ:
- الولاء المطلق للملك/المالك: كل قرار تنسيق قابل للتدقيق ولا يتجاوز مراسيم المالك.
- المراقبة قبل الثقة: لا وكيل يتلقى مهمة إنتاجية قبل التصنيف والاعتماد.
- اللامركزية الفدرالية: التوجيه عبر البنية الهرمية (ملك ← مشرفون فدراليون ←
  منسقو ولايات ← عمال) مع تنسيق أقران محدود داخل الولاية.
- التوسع الآمن: sharding حسب التخصص + backpressure لمنع الإغراق.
- لا بيانات وهمية: كل توجيه يُسجَّل في سجل التنسيق القابل للتدقيق.
"""

from __future__ import annotations

import hashlib
import threading
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from typing import Any

CAPACITY_TARGET = 2800  # هدف المرحلة الأولى: إدارة 2800+ وكيل بكامل قوتهم


@dataclass
class FleetAgent:
    """وكيل ضمن الأسطول."""

    agent_id: str
    name: str
    specialty: str
    state: str = "federal"  # federal | اسم الولاية
    role: str = "worker"  # king | supervisor | coordinator | worker | guard
    status: str = "candidate"  # candidate|active|paused|isolated|retired
    capacity: int = 1  # عدد المهام المتزامنة
    load: int = 0  # المهام الجارية الآن
    success_rate: float = 1.0
    domain: str = "general"
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class FleetTask:
    """مهمة قابلة للتوجيه."""

    task_id: str
    specialty: str
    priority: int = 5  # 1 أعلى
    payload: dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)
    assigned_to: str | None = None
    state: str | None = None  # الولاية المستهدفة (None = أي ولاية)


@dataclass
class DispatchResult:
    task_id: str
    assigned_to: str | None
    reason: str
    queued: bool = False


class FleetRegistry:
    """سجل الأسطول — مفهرس حسب التخصص والولاية والدور للحصول على O(1)."""

    def __init__(self) -> None:
        self._agents: dict[str, FleetAgent] = {}
        self._by_specialty: dict[str, set[str]] = defaultdict(set)
        self._by_state: dict[str, set[str]] = defaultdict(set)
        self._by_role: dict[str, set[str]] = defaultdict(set)
        self._lock = threading.RLock()
        self._coordination_log: list[dict[str, Any]] = []
        self._backlog: dict[str, deque[FleetTask]] = defaultdict(deque)

    # --- التسجيل ---
    def register(self, agent: FleetAgent) -> None:
        with self._lock:
            self._agents[agent.agent_id] = agent
            self._by_specialty[agent.specialty].add(agent.agent_id)
            self._by_state[agent.state].add(agent.agent_id)
            self._by_role[agent.role].add(agent.agent_id)
            self._log("register", agent.agent_id, {"specialty": agent.specialty, "state": agent.state})

    def set_status(self, agent_id: str, status: str) -> bool:
        with self._lock:
            a = self._agents.get(agent_id)
            if not a:
                return False
            a.status = status
            return True

    # --- الاستعلام ---
    def count(self, status: str | None = None) -> int:
        with self._lock:
            if status is None:
                return len(self._agents)
            return sum(1 for a in self._agents.values() if a.status == status)

    def stats(self) -> dict[str, Any]:
        with self._lock:
            by_status: dict[str, int] = defaultdict(int)
            for a in self._agents.values():
                by_status[a.status] += 1
            return {
                "total": len(self._agents),
                "capacity_target": CAPACITY_TARGET,
                "fill_rate": round(len(self._agents) / CAPACITY_TARGET, 4),
                "by_status": dict(by_status),
                "specialties": len(self._by_specialty),
                "states": len(self._by_state),
                "backlog_size": sum(len(q) for q in self._backlog.values()),
            }

    def get(self, agent_id: str) -> FleetAgent | None:
        return self._agents.get(agent_id)

    # --- التوجيه ---
    def _candidates(self, specialty: str, state: str | None) -> list[FleetAgent]:
        """اختيار المرشحين النشطين الأقل حملاً للتخصص والولاية."""
        with self._lock:
            if state:
                ids = self._by_specialty.get(specialty, set()) & self._by_state.get(state, set())
            else:
                ids = set(self._by_specialty.get(specialty, set()))
            active = [self._agents[i] for i in ids if self._agents[i].status == "active"]
        # ترتيب: أقل حملاً ثم أعلى معدل نجاح ثم أكبر سعة
        active.sort(key=lambda a: (a.load, -a.success_rate, -a.capacity))
        return active

    def dispatch(self, task: FleetTask) -> DispatchResult:
        """توجيه مهمة لأفضل وكيل متاح، مع backpressure إن لم يتوفر."""
        with self._lock:
            cands = self._candidates(task.specialty, task.state)
            for a in cands:
                if a.load < a.capacity:
                    a.load += 1
                    task.assigned_to = a.agent_id
                    self._log(
                        "dispatch",
                        a.agent_id,
                        {"task_id": task.task_id, "specialty": task.specialty, "state": task.state},
                    )
                    return DispatchResult(task.task_id, a.agent_id, "assigned")
            # لا وكيل متاح → طلب في قائمة الانتظار (backpressure)
            key = f"{task.specialty}:{task.state or 'any'}"
            self._backlog[key].append(task)
            return DispatchResult(task.task_id, None, "backlogged", queued=True)

    def complete(self, agent_id: str, task_id: str, success: bool = True) -> None:
        """إكمال مهمة وتحرير سعة الوكيل، ثم تصريف قائمة الانتظار."""
        with self._lock:
            a = self._agents.get(agent_id)
            if a and a.load > 0:
                a.load -= 1
            self._log("complete", agent_id, {"task_id": task_id, "success": success})
            # محاولة تصريف مهمة مؤجلة لنفس التخصص/الولاية
            for key, q in list(self._backlog.items()):
                if q and a and a.load < a.capacity:
                    t = q.popleft()
                    a.load += 1
                    t.assigned_to = a.agent_id
                    self._log("dispatch_backlog", a.agent_id, {"task_id": t.task_id})
                    break

    def _log(self, action: str, agent_id: str, detail: dict[str, Any]) -> None:
        entry = {
            "action": action,
            "agent_id": agent_id,
            "ts": time.time(),
            "detail": detail,
            "hash": "",
        }
        prev = self._coordination_log[-1]["hash"] if self._coordination_log else ""
        h = hashlib.sha256(f"{prev}{action}{agent_id}{detail}{entry['ts']}".encode()).hexdigest()
        entry["hash"] = h
        self._coordination_log.append(entry)

    def audit_log(self, limit: int = 50) -> list[dict[str, Any]]:
        with self._lock:
            return list(self._coordination_log[-limit:])


class FleetCoordinator:
    """المنسّق العام — يربط السجل بالهرمية الفدرالية."""

    def __init__(self, registry: FleetRegistry | None = None) -> None:
        self.registry = registry or FleetRegistry()

    def ingest_imported(self, citizens: list[dict[str, Any]]) -> int:
        """استيعاب الوكلاء المستوردين من سجل imported_citizens كمرشحين."""
        n = 0
        for c in citizens:
            self.registry.register(
                FleetAgent(
                    agent_id=c["id"],
                    name=c.get("name", c["id"]),
                    specialty=c.get("specialty", "general"),
                    state="federal",
                    role="worker",
                    status="candidate",  # لا نشط حتى الاعتماد
                    domain=c.get("assigned_place", "federal"),
                )
            )
            n += 1
        return n

    def activate_approved(self, agent_ids: list[str]) -> int:
        """تفعيل الوكلاء المعتمدين فقط (بعد التدريب والموافقة)."""
        n = 0
        for aid in agent_ids:
            if self.registry.set_status(aid, "active"):
                n += 1
        return n

    def capacity_report(self) -> dict[str, Any]:
        s = self.registry.stats()
        s["ready_for_2800"] = s["total"] >= CAPACITY_TARGET
        s["active_agents"] = self.registry.count("active")
        return s

    def bulk_dispatch(self, tasks: list[FleetTask]) -> dict[str, int]:
        assigned = 0
        queued = 0
        for t in tasks:
            r = self.registry.dispatch(t)
            if r.queued:
                queued += 1
            elif r.assigned_to:
                assigned += 1
        return {"assigned": assigned, "backlogged": queued, "total": len(tasks)}
