"""
AMOS-Federation Configuration
الهدف: إعدادات النظام الموحدة
النطاق: كل الخدمات
المالك: federal/executive/services
تاريخ الإنشاء: 2026-08-15
"""

from pydantic_settings import BaseSettings


class InsecureConfigurationError(RuntimeError):
    """إعداد لا يجوز الإقلاع به: سرٌّ ناقص أو نائب في بيئة إنتاج."""


#: الحقول التي لا يجوز أن تحمل قيمة مكتوبة في الكود.
SECRET_FIELDS: tuple[str, ...] = (
    "postgres_password",
    "minio_secret_key",
    "jwt_secret",
    "king_login_secret",
)

#: قيم نائبة تاريخية — وجودها في الإنتاج كوجود الفراغ.
PLACEHOLDER_SECRETS: frozenset[str] = frozenset(
    {
        "dev_password_change_me",
        "dev_secret_change_me",
        "dev_secret_change_me_at_least_32_characters",
        "changeme",
        "change_me",
    }
)

#: أسماء البيئات التي تُعامَل معاملة الإنتاج.
PRODUCTION_ENVIRONMENTS: frozenset[str] = frozenset({"production", "prod", "staging"})


class Settings(BaseSettings):
    """إعدادات النظام — تُقرأ من متغيرات البيئة أو .env"""

    # التطبيق
    app_name: str = "amos-federation"
    environment: str = "development"
    debug: bool = True

    # PostgreSQL
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "amos_federation"
    postgres_user: str = "amos"
    postgres_password: str = ""

    # Redis
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0

    # NATS
    nats_url: str = "nats://localhost:4222"
    nats_stream: str = "amos_federation"
    nats_retention_days: int = 365

    # Qdrant
    qdrant_host: str = "localhost"
    qdrant_port: int = 6333

    # MinIO
    minio_endpoint: str = "localhost:9000"
    minio_access_key: str = "amos"
    minio_secret_key: str = ""
    minio_bucket: str = "amos-federation"

    # JWT
    jwt_secret: str = ""
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60

    # OpenTelemetry
    otlp_endpoint: str = "http://localhost:4317"
    service_name: str = "amos-federation"
    service_port: int = 8000

    # بوابة النماذج
    claude_api_key: str = ""
    default_model: str = "claude-sonnet-4-20250514"

    # Database URL (مباشر للـ SQLAlchemy)
    database_url: str = ""

    # سرّ دخول الملك — يُقرأ من البيئة ولا قيمة افتراضية له.
    king_login_secret: str = ""

    def secret_violations(self) -> list[str]:
        """أسماء الحقول السرّية غير المهيّأة أو الحاملة قيمة نائبة معروفة.

        لا تُرجع القيم نفسها — الأسماء وحدها تكفي للتشخيص، وإخراج السرّ في رسالة
        خطأ تسريبٌ آخر.
        """
        violations: list[str] = []
        for field in SECRET_FIELDS:
            value = getattr(self, field, "")
            if not value or value in PLACEHOLDER_SECRETS:
                violations.append(field)
        return violations

    def assert_secrets_configured(self) -> None:
        """ارفض الإقلاع في الإنتاج بسرّ ناقص أو نائب.

        القيمة الافتراضية المكتوبة في الكود سرٌّ منشور: من قرأ المستودع عرفها.
        فلا افتراضي هنا، والبيئة وحدها مصدر السرّ، والإنتاج يسقط صراحةً بدلًا من
        أن يعمل بأمان موهوم.
        """
        if self.environment.strip().lower() not in PRODUCTION_ENVIRONMENTS:
            return
        missing = self.secret_violations()
        if missing:
            raise InsecureConfigurationError("أسرار غير مهيّأة في بيئة إنتاج: " + "، ".join(missing))

    @property
    def postgres_dsn(self) -> str:
        return (
            f"postgresql://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def redis_url(self) -> str:
        return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"

    model_config = {"env_file": ".env", "env_prefix": "AMOS_", "extra": "ignore"}


settings = Settings()
