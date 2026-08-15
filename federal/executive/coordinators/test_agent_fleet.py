# -*- coding: utf-8 -*-
"""
الهدف: إثبات أن طبقة تنسيق أسطول الوكلاء تسجّل الوكلاء وتوزّع المهام وتحترم سعتها
       المستهدفة فعلًا — لا وصفًا في وثيقة.
النطاق: `agent_fleet.py` وحدها: التسجيل، التوزيع، حدود السعة.
المالك: federal/executive/coordinators
تاريخ الإنشاء: 2026-08-15
تاريخ آخر تعديل: 2026-08-16

اختبارات طبقة تنسيق أسطول الوكلاء (2800+).
"""
import os
import importlib.util

_HERE = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location("agent_fleet", os.path.join(_HERE, "agent_fleet.py"))
agent_fleet = importlib.util.module_from_spec(_spec)
import sys as _sys  # noqa: E402  — يلزم تحميل الوحدة أعلاه أولًا

_sys.modules["agent_fleet"] = agent_fleet
_spec.loader.exec_module(agent_fleet)

# استيراد بعد التحميل الديناميكي: `agent_fleet` ملف مجاور لا حزمة مثبَّتة.
from agent_fleet import (  # noqa: E402
    FleetRegistry, FleetCoordinator, FleetAgent, FleetTask, CAPACITY_TARGET,
)


def _make_agent(i, specialty="coding", state="federal", status="active"):
    return FleetAgent(
        agent_id=f"agent-{state}-{i:04d}", name=f"Agent {i}", specialty=specialty,
        state=state, role="worker", status=status, capacity=2,
    )


def test_register_and_count():
    r = FleetRegistry()
    for i in range(100):
        r.register(_make_agent(i))
    assert r.count() == 100
    assert r.count("active") == 100
    assert r.count("paused") == 0
    print("OK test_register_and_count")


def test_dispatch_assigns_least_loaded():
    r = FleetRegistry()
    for i in range(5):
        r.register(_make_agent(i))
    res = r.dispatch(FleetTask(task_id="t1", specialty="coding"))
    assert res.assigned_to is not None
    # 5 وكلاء سعة 2 = 10 مهام قابلة للتوزيع، الحادية عشرة تنتظر
    for i in range(10):
        r.dispatch(FleetTask(task_id=f"t{i+2}", specialty="coding"))
    backlog = r.dispatch(FleetTask(task_id="t12", specialty="coding"))
    assert backlog.queued, "11th task should be backlogged"
    # لا وكيل يتجاوز سعته
    assert all(r.get(f"agent-federal-{i:04d}").load <= 2 for i in range(5))
    print("OK test_dispatch_assigns_least_loaded")


def test_backpressure_and_drain():
    r = FleetRegistry()
    r.register(_make_agent(0, status="active"))
    # capacity=2 → المهمة الثالثة تذهب لقائمة الانتظار
    r.dispatch(FleetTask(task_id="t1", specialty="coding"))
    r.dispatch(FleetTask(task_id="t2", specialty="coding"))
    res = r.dispatch(FleetTask(task_id="t3", specialty="coding"))
    assert res.queued, "should be backlogged"
    # إكمال مهمة يصرف المؤجلة
    r.complete("agent-federal-0000", "t1")
    a0 = r.get("agent-federal-0000")
    assert a0.load == 2, a0.load  # t3 drained
    print("OK test_backpressure_and_drain")


def test_state_isolation():
    r = FleetRegistry()
    for s in ["finance", "science"]:
        for i in range(3):
            r.register(_make_agent(i, state=s))
    # مهمة موجهة لولاية المال لا تذهب لولاية العلم
    res = r.dispatch(FleetTask(task_id="tf", specialty="coding", state="finance"))
    assert res.assigned_to is not None
    assert r.get(res.assigned_to).state == "finance"
    print("OK test_state_isolation")


def test_capacity_2800_plus():
    """المعيار: قدرة على إدارة 2800+ وكيل بلا أخطاء."""
    r = FleetRegistry()
    for i in range(CAPACITY_TARGET + 50):
        r.register(_make_agent(i, specialty=["coding","research","security","memory"][i % 4]))
    s = r.stats()
    assert s["total"] == CAPACITY_TARGET + 50, s["total"]
    # توجيه دفعة كبيرة
    tasks = [FleetTask(task_id=f"tk{i}", specialty=["coding","research","security","memory"][i % 4]) for i in range(2000)]
    coord = FleetCoordinator(r)
    out = coord.bulk_dispatch(tasks)
    assert out["assigned"] + out["backlogged"] == 2000
    assert s["fill_rate"] >= 1.0
    rep = coord.capacity_report()
    assert rep["ready_for_2800"] is True
    assert rep["active_agents"] == CAPACITY_TARGET + 50
    print(f"OK test_capacity_2800_plus (total={s['total']}, dispatched={out['assigned']}, backlog={out['backlogged']})")


def test_audit_log_chain():
    r = FleetRegistry()
    for i in range(3):
        r.register(_make_agent(i))
    r.dispatch(FleetTask(task_id="t1", specialty="coding"))
    log = r.audit_log()
    assert len(log) > 0
    assert all(e["hash"] for e in log)
    print("OK test_audit_log_chain")


def test_ingest_imported():
    coord = FleetCoordinator()
    citizens = [
        {"id": "imported-fedexecutive-autogpt", "name": "AutoGPT", "specialty": "orchestration", "assigned_place": "federal/executive"},
        {"id": "imported-statesinfrastructure-aider", "name": "Aider", "specialty": "coding", "assigned_place": "states/infrastructure"},
    ]
    n = coord.ingest_imported(citizens)
    assert n == 2
    assert coord.registry.count() == 2
    assert coord.registry.count("active") == 0  # كلهم candidate
    coord.activate_approved(["imported-fedexecutive-autogpt"])
    assert coord.registry.count("active") == 1
    print("OK test_ingest_imported")


if __name__ == "__main__":
    test_register_and_count()
    test_dispatch_assigns_least_loaded()
    test_backpressure_and_drain()
    test_state_isolation()
    test_capacity_2800_plus()
    test_audit_log_chain()
    test_ingest_imported()
    print("\nALL FLEET TESTS PASSED")
