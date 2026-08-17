"""الهدف: مفردات واحدة لصدق التنفيذ — REAL و SIMULATION و UNAVAILABLE.

النطاق: federal/executive/services — النواة التنفيذية
المالك: federal/executive/services
تاريخ الإنشاء: 2026-08-16

قبل هذه الوحدة كانت كلمة `"SIMULATION"` نصًّا حرًّا مكتوبًا في مكان واحد
(`engine.EXECUTION_FIDELITY`)، وبقية الخدمات لا تُعلن صدق مخرَجها إطلاقًا: بوابة
النماذج تُرجع نصًّا محليًّا حتميًّا بلا أن تقول إنه ليس نموذجًا، وخدمة التدريب
تُرجع `accuracy` مشتقًّا من hash بلا أن تقول إنه ليس تدريبًا.

القاعدة التي تفرضها هذه الوحدة:

- **REAL** — العمل وقع فعلًا على منظومة حقيقية خارج العملية.
- **SIMULATION** — المخرَج مُصطنَع بقصد ومُعلَن. لا يُستخدم لتغطية فشل.
- **UNAVAILABLE** — القدرة غائبة. الغياب يُقال ولا يُبدَّل بمخرَج يبدو ناجحًا.

الفرق بين الأخيرتين هو بالضبط ما يمنع الكذب التشغيلي: نموذج لم يُستدعَ لأن
المفتاح غائب حالتُه `UNAVAILABLE` مع سبب مُسمّى، لا `SIMULATION` صامتة.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Any


class ExecutionFidelity(StrEnum):
    """صدق المخرَج — تُرفَق بكل نتيجة تنفيذ تُعلَن للخارج."""

    REAL = "REAL"
    SIMULATION = "SIMULATION"
    UNAVAILABLE = "UNAVAILABLE"


def declare(
    fidelity: ExecutionFidelity,
    *,
    reason: str | None = None,
    detail: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """إعلان صدق مخرَج مع سببه — السبب إلزامي لكل ما ليس REAL.

    Raises:
        ValueError: إن أُعلنت محاكاة أو غياب بلا سبب مُسمّى. سببٌ مجهول معناه
            أن الإعلان زينة، وأن الفشل قد يُخفى تحت كلمة `SIMULATION`.
    """
    if fidelity is not ExecutionFidelity.REAL and not reason:
        raise ValueError(f"إعلان {fidelity.value} يلزمه سبب مُسمّى")
    declaration: dict[str, Any] = {"execution_fidelity": fidelity.value}
    if reason:
        declaration["fidelity_reason"] = reason
    if detail:
        declaration["fidelity_detail"] = detail
    return declaration
