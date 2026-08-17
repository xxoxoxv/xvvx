"""
AMOS-Federation Tool Catalog — Phase 4
الهدف: توسيع كتالوج الأدوات إلى 100+ أداة موزعة على 12 فئة
النطاق: services/tool_registry/catalog
المالك: federal/executive/services
تاريخ الإنشاء: 2026-08-15

الفئات الـ12: استخراج بيانات، معالجة نصوص، تحليل، إنشاء محتوى،
بحث، اتصالات، أمان، وسائط، بنية تحتية، حوكمة، تعليم، مالية
"""

from typing import Any

# === الفئات الـ12 ===

TOOL_CATEGORIES = {
    "data_extraction": "استخراج بيانات",
    "text_processing": "معالجة نصوص",
    "analysis": "تحليل",
    "content_creation": "إنشاء محتوى",
    "search": "بحث",
    "communication": "اتصالات",
    "security": "أمان",
    "media": "وسائط",
    "infrastructure": "بنية تحتية",
    "governance": "حوكمة",
    "education": "تعليم",
    "finance": "مالية",
}


# === تعريف الأدوات ===

TOOL_CATALOG = {
    # === استخراج بيانات (8) ===
    "python_execute": {"category": "data_extraction", "risk": "high", "desc": "تنفيذ كود Python"},
    "sql_query": {"category": "data_extraction", "risk": "high", "desc": "استعلام SQL للقراءة فقط"},
    "csv_parse": {"category": "data_extraction", "risk": "low", "desc": "تحليل ملفات CSV"},
    "json_extract": {
        "category": "data_extraction",
        "risk": "low",
        "desc": "استخراج بيانات من JSON",
    },
    "regex_extract": {"category": "data_extraction", "risk": "low", "desc": "استخراج بأنماط regex"},
    "web_scrape": {"category": "data_extraction", "risk": "medium", "desc": "قراءة صفحة ويب"},
    "api_call": {"category": "data_extraction", "risk": "medium", "desc": "استدعاء API خارجي"},
    "file_read": {"category": "data_extraction", "risk": "low", "desc": "قراءة ملف"},
    # === معالجة نصوص (10) ===
    "text_summary": {"category": "text_processing", "risk": "low", "desc": "تلخيص نص"},
    "text_translate": {"category": "text_processing", "risk": "low", "desc": "ترجمة نص"},
    "text_sentiment": {"category": "text_processing", "risk": "low", "desc": "تحليل المشاعر"},
    "text_clean": {"category": "text_processing", "risk": "low", "desc": "تنظيف نص"},
    "text_tokenize": {"category": "text_processing", "risk": "low", "desc": "تقسيم نص إلى رموز"},
    "text_count": {"category": "text_processing", "risk": "low", "desc": "عد كلمات و أحرف"},
    "text_replace": {"category": "text_processing", "risk": "low", "desc": "استبدال في نص"},
    "text_case": {"category": "text_processing", "risk": "low", "desc": "تحويل حالة الأحرف"},
    "text_hash": {"category": "text_processing", "risk": "low", "desc": "توليد hash للنص"},
    "text_diff": {"category": "text_processing", "risk": "low", "desc": "مقارنة نصين"},
    # === تحليل (10) ===
    "stats_basic": {"category": "analysis", "risk": "low", "desc": "إحصائيات أساسية"},
    "stats_correlation": {"category": "analysis", "risk": "low", "desc": "تحليل ارتباط"},
    "data_sort": {"category": "analysis", "risk": "low", "desc": "ترتيب بيانات"},
    "data_filter": {"category": "analysis", "risk": "low", "desc": "تصفية بيانات"},
    "data_group": {"category": "analysis", "risk": "low", "desc": "تجميع بيانات"},
    "data_aggregate": {"category": "analysis", "risk": "low", "desc": "تجميع بيانات"},
    "data_pivot": {"category": "analysis", "risk": "medium", "desc": "جدول محوري"},
    "trend_analyze": {"category": "analysis", "risk": "low", "desc": "تحليل اتجاهات"},
    "anomaly_detect": {"category": "analysis", "risk": "medium", "desc": "كشف شذوذ"},
    "data_validate": {"category": "analysis", "risk": "low", "desc": "التحقق من صحة بيانات"},
    # === إنشاء محتوى (8) ===
    "content_article": {"category": "content_creation", "risk": "low", "desc": "كتابة مقال"},
    "content_report": {"category": "content_creation", "risk": "low", "desc": "إنشاء تقرير"},
    "content_email": {"category": "content_creation", "risk": "low", "desc": "صياغة بريد"},
    "content_summary_doc": {"category": "content_creation", "risk": "low", "desc": "ملخص تنفيذي"},
    "content_list": {"category": "content_creation", "risk": "low", "desc": "إنشاء قائمة"},
    "content_outline": {"category": "content_creation", "risk": "low", "desc": "مخطط محتوى"},
    "content_template": {"category": "content_creation", "risk": "low", "desc": "توليد من قالب"},
    "content_format": {"category": "content_creation", "risk": "low", "desc": "تنسيق محتوى"},
    # === بحث (6) ===
    "search_keyword": {"category": "search", "risk": "low", "desc": "بحث بكلمة مفتاحية"},
    "search_index": {"category": "search", "risk": "low", "desc": "بحث في فهرس"},
    "search_fuzzy": {"category": "search", "risk": "low", "desc": "بحث تقريبي"},
    "search_regex": {"category": "search", "risk": "low", "desc": "بحث بـ regex"},
    "search_metadata": {"category": "search", "risk": "low", "desc": "بحث في بيانات وصفية"},
    "searchsemantic": {"category": "search", "risk": "medium", "desc": "بحث دلالي"},
    # === اتصالات (6) ===
    "http_request": {"category": "communication", "risk": "high", "desc": "طلب HTTP"},
    "webhook_send": {"category": "communication", "risk": "medium", "desc": "إرسال webhook"},
    "email_send": {"category": "communication", "risk": "medium", "desc": "إرسال بريد"},
    "message_format": {"category": "communication", "risk": "low", "desc": "تنسيق رسالة"},
    "notification_create": {"category": "communication", "risk": "low", "desc": "إنشاء إشعار"},
    "api_document": {"category": "communication", "risk": "low", "desc": "توثيق API"},
    # === أمان (8) ===
    "hash_generate": {"category": "security", "risk": "low", "desc": "توليد hash"},
    "hash_verify": {"category": "security", "risk": "low", "desc": "التحقق من hash"},
    "token_generate": {"category": "security", "risk": "medium", "desc": "توليد رمز"},
    "password_strength": {"category": "security", "risk": "low", "desc": "فحص قوة كلمة مرور"},
    "encrypt_text": {"category": "security", "risk": "medium", "desc": "تشفير نص"},
    "decrypt_text": {"category": "security", "risk": "high", "desc": "فك تشفير نص"},
    "audit_check": {"category": "security", "risk": "low", "desc": "فحص سجل تدقيق"},
    "permission_check": {"category": "security", "risk": "low", "desc": "فحص صلاحية"},
    # === وسائط (8) ===
    "chart_generate": {"category": "media", "risk": "low", "desc": "إنشاء رسم بياني"},
    "image_metadata": {"category": "media", "risk": "low", "desc": "بيانات وصفية للصورة"},
    "image_resize": {"category": "media", "risk": "low", "desc": "تغيير حجم صورة"},
    "image_convert": {"category": "media", "risk": "low", "desc": "تحويل صيغة صورة"},
    "audio_transcribe": {"category": "media", "risk": "medium", "desc": "تفريغ صوت"},
    "video_metadata": {"category": "media", "risk": "low", "desc": "بيانات فيديو"},
    "pdf_extract": {"category": "media", "risk": "low", "desc": "استخراج نص PDF"},
    "qr_generate": {"category": "media", "risk": "low", "desc": "توليد QR code"},
    # === بنية تحتية (8) ===
    "file_write": {"category": "infrastructure", "risk": "medium", "desc": "كتابة ملف"},
    "file_copy": {"category": "infrastructure", "risk": "low", "desc": "نسخ ملف"},
    "file_move": {"category": "infrastructure", "risk": "low", "desc": "نقل ملف"},
    "file_delete": {"category": "infrastructure", "risk": "medium", "desc": "حذف ملف"},
    "dir_list": {"category": "infrastructure", "risk": "low", "desc": "سرد مجلد"},
    "dir_create": {"category": "infrastructure", "risk": "low", "desc": "إنشاء مجلد"},
    "system_info": {"category": "infrastructure", "risk": "low", "desc": "معلومات النظام"},
    "process_status": {"category": "infrastructure", "risk": "low", "desc": "حالة العمليات"},
    # === حوكمة (8) ===
    "policy_check": {"category": "governance", "risk": "low", "desc": "فحص سياسة"},
    "audit_query": {"category": "governance", "risk": "low", "desc": "استعلام تدقيق"},
    "decree_list": {"category": "governance", "risk": "low", "desc": "قائمة مراسيم"},
    "agent_status": {"category": "governance", "risk": "low", "desc": "حالة وكيل"},
    "kill_switch_status": {"category": "governance", "risk": "low", "desc": "حالة Kill Switch"},
    "budget_check": {"category": "governance", "risk": "low", "desc": "فحص ميزانية"},
    "compliance_check": {"category": "governance", "risk": "low", "desc": "فحص امتثال"},
    "vote_tally": {"category": "governance", "risk": "low", "desc": "عد أصوات"},
    # === تعليم (6) ===
    "quiz_generate": {"category": "education", "risk": "low", "desc": "توليد اختبار"},
    "quiz_grade": {"category": "education", "risk": "low", "desc": "تصحيح اختبار"},
    "curriculum_outline": {"category": "education", "risk": "low", "desc": "مخطط منهج"},
    "flashcard_create": {"category": "education", "risk": "low", "desc": "إنشاء بطاقة تعليمية"},
    "progress_track": {"category": "education", "risk": "low", "desc": "تتبع تقدم"},
    "lesson_plan": {"category": "education", "risk": "low", "desc": "خطة درس"},
    # === مالية (8) ===
    "budget_calculate": {"category": "finance", "risk": "low", "desc": "حساب ميزانية"},
    "cost_estimate": {"category": "finance", "risk": "low", "desc": "تقدير تكلفة"},
    "invoice_generate": {"category": "finance", "risk": "low", "desc": "توليد فاتورة"},
    "tax_calculate": {"category": "finance", "risk": "low", "desc": "حساب ضريبة"},
    "balance_check": {"category": "finance", "risk": "low", "desc": "فحص رصيد"},
    "transaction_log": {"category": "finance", "risk": "medium", "desc": "تسجيل معاملة"},
    "financial_report": {"category": "finance", "risk": "low", "desc": "تقرير مالي"},
    "roi_calculate": {"category": "finance", "risk": "low", "desc": "حساب العائد على الاستثمار"},
}


def get_catalog_stats() -> dict[str, Any]:
    """إحصائيات الكتالوج."""
    categories = {}
    risk_levels = {"low": 0, "medium": 0, "high": 0}
    for _tool_id, info in TOOL_CATALOG.items():
        cat = info["category"]
        categories[cat] = categories.get(cat, 0) + 1
        risk_levels[info["risk"]] = risk_levels.get(info["risk"], 0) + 1

    return {
        "total_tools": len(TOOL_CATALOG),
        "categories": categories,
        "risk_levels": risk_levels,
        "category_names": TOOL_CATEGORIES,
    }


def list_tools_by_category(category: str) -> list[dict[str, Any]]:
    """سرد الأدوات في فئة معينة."""
    return [
        {
            "tool_id": tid,
            "name": tid,
            "category": info["category"],
            "risk_level": info["risk"],
            "description": info["desc"],
        }
        for tid, info in TOOL_CATALOG.items()
        if info["category"] == category
    ]


def list_all_tools() -> list[dict[str, Any]]:
    """سرد كل الأدوات."""
    return [
        {
            "tool_id": tid,
            "name": tid,
            "category": info["category"],
            "risk_level": info["risk"],
            "description": info["desc"],
        }
        for tid, info in TOOL_CATALOG.items()
    ]
