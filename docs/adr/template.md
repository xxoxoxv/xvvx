# ADR-NNN: <Title>

> **قالب قرار العمارة (Architecture Decision Record template)**
> انسخ هذا الملف إلى `NNNN-short-title.md` واملأ الأقسام. كل قرار معماري مهم يُوثّق هنا.
> Copy this file to `NNNN-short-title.md` and fill in the sections. Every significant architecture decision is recorded here.

## الهدف
قالب قرار العمارة (ADR): يُنسخ لكل قرار معماري مهم فيُحفظ سببه وبدائله وأثره، فلا يُنسى لماذا بُني شيء على هذه الصورة.

---

## Title

<Short, descriptive title of the decision>

## Status

<One of: proposed | accepted | deprecated | superseded>

- **proposed** — قُدِّم ولم يُقر بعد (submitted, not yet accepted)
- **accepted** — قُبِّل ونُفِّذ (accepted and in effect)
- **deprecated** — لم يعد ساريًا (no longer in effect)
- **superseded** — حُلَّ محلَّه قرار آخر؛ أشر إلى ADR البديل (replaced by another ADR; link to the superseding ADR)

If superseded, link to the replacing ADR: `Superseded by [ADR-NNNN](./NNNN-short-title.md)`

## Date

<YYYY-MM-DD>

## Authors

- <Author name / role>
- <Author name / role>

## Context

<Why is this decision needed? What is the problem, constraint, or force driving it? Describe the situation, the relevant background, and the requirements. Include any constraints (technical, organizational, political, time) and the options considered at a high level. Be neutral — state facts, not the decision.>

سياق القرار: لماذا نحتاج هذا القرار؟ ما المشكلة أو القيد أو القوة الدافعة؟ صف الموقف والخلفية ذات الصلة والمتطلبات. اذكر أي قيود (تقنية، تنظيمية، سياسية، زمنية) والخيارات المُعتبرة على مستوى عالٍ. كن محايدًا — اذكر الحقائق لا القرار.

## Decision

<What is the decision that was made? State it clearly and unambiguously. Describe what is being done, not just the conclusion.>

القرار: ما القرار الذي اتُّخذ؟ اذكره بوضوح وبدون غموض. صف ما سيُفعَل، لا الخلاصة فقط.

## Consequences

<What are the resulting consequences of this decision? Cover both positive and negative effects. Include impact on: architecture, effort, performance, security, operations, and future options. Note any new risks introduced and any follow-up actions required.>

النتائج: ما تبعات هذا القرار؟ غطِّ التأثيرات الإيجابية والسلبية. اذكر الأثر على: البنية، الجهد، الأداء، الأمان، العمليات، والخيارات المستقبلية. أشر إلى أي مخاطر جديدة وأي إجراءات لاحقة مطلوبة.

- **Positive:** <benefits gained>
- **Negative:** <trade-offs accepted / costs incurred>
- **Risks:** <new risks introduced>
- **Follow-ups:** <follow-up actions or ADRs needed>

## Alternatives

<What other options were considered? For each alternative, briefly describe it and explain why it was not chosen. This prevents revisiting the same debate later.>

البدائل: ما الخيارات الأخرى التي اعتُبرت؟ لكل بديل، صفه بإيجاز واشرح لماذا لم يُختر. هذا يمنع إعادة فتح النقاش نفسه لاحقًا.

### Alternative A: <name>
<description> — **Rejected because:** <reason>

### Alternative B: <name>
<description> — **Rejected because:** <reason>

## Related

<Optional. Link to related ADRs, blueprints, NUCLEUS.md files, or external references.>

- Supersedes: [ADR-NNNN](./NNNN-short-title.md) (if applicable)
- Related blueprint section: <e.g. AMOS-SE_Final_Blueprint §8.3>
- Related nucleus: <e.g. tools/NUCLEUS.md>
- Related schema: <e.g. docs/contracts/schemas/tools.schema.json>
