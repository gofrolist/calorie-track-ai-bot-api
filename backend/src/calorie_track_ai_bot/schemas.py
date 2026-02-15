from __future__ import annotations

from datetime import date as date_aliased
from enum import StrEnum
from typing import Annotated, Any
from uuid import UUID

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field


class Status(StrEnum):
    queued = "queued"
    running = "running"
    done = "done"
    failed = "failed"


class MealType(StrEnum):
    breakfast = "breakfast"
    lunch = "lunch"
    dinner = "dinner"
    snack = "snack"


class FeedbackMessageType(StrEnum):
    feedback = "feedback"
    bug = "bug"
    question = "question"
    support = "support"


class FeedbackStatus(StrEnum):
    new = "new"
    reviewed = "reviewed"
    resolved = "resolved"


class ConnectionStatus(StrEnum):
    connected = "connected"
    disconnected = "disconnected"
    error = "error"


class HealthResponse(BaseModel):
    status: str


class ErrorResponse(BaseModel):
    detail: str


class Macronutrients(BaseModel):
    protein: Annotated[float, Field(ge=0.0)]
    carbs: Annotated[float, Field(ge=0.0)]
    fats: Annotated[float, Field(ge=0.0)]


class EstimateItem(BaseModel):
    label: str
    kcal: float
    confidence: float


class PhotoCreateRequest(BaseModel):
    content_type: Annotated[str, Field(description="MIME type of the image (e.g., image/jpeg)")]


class MultiPhotoCreateRequest(BaseModel):
    photos: Annotated[
        list[PhotoCreateRequest],
        Field(
            description="List of photos to upload (1-5 photos)",
            max_length=5,
            min_length=1,
        ),
    ]


class PhotoInfo(BaseModel):
    id: str
    upload_url: str
    file_key: str


class MultiPhotoResponse(BaseModel):
    photos: list[PhotoInfo]


class PresignResponse(BaseModel):
    photo_id: str
    upload_url: str


class EstimateQueuedResponse(BaseModel):
    estimate_id: str
    status: Status


class EstimateResponse(BaseModel):
    id: Annotated[str, Field(description="Estimate ID")]
    photo_id: str
    kcal_mean: float
    kcal_min: float
    kcal_max: float
    confidence: float
    breakdown: list[EstimateItem]
    status: Status | None = None


class MealCreateManualRequest(BaseModel):
    meal_date: date_aliased
    meal_type: MealType
    kcal_total: float
    macros: Macronutrients | None = None


class MealCreateFromEstimateRequest(BaseModel):
    meal_date: date_aliased
    meal_type: MealType
    estimate_id: UUID
    overrides: dict[str, Any] | None = None


class MealCreateResponse(BaseModel):
    meal_id: UUID


class MealPhotoInfo(BaseModel):
    id: UUID
    thumbnailUrl: Annotated[str, Field(description="Presigned URL for thumbnail")]
    fullUrl: Annotated[str, Field(description="Presigned URL for full-size image")]
    displayOrder: Annotated[int, Field(description="Position in carousel (0-4)", ge=0, le=4)]


class MealWithPhotos(BaseModel):
    id: UUID
    userId: UUID
    createdAt: AwareDatetime
    description: Annotated[str | None, Field(max_length=1000)] = None
    calories: Annotated[float, Field(ge=0.0)]
    macronutrients: Macronutrients
    photos: Annotated[list[MealPhotoInfo] | None, Field(default_factory=list)]
    confidenceScore: Annotated[
        float | None, Field(description="AI confidence (0-1)", ge=0.0, le=1.0)
    ] = None


class MealUpdate(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    description: Annotated[str | None, Field(max_length=1000)] = None
    protein_grams: Annotated[float | None, Field(ge=0.0)] = None
    carbs_grams: Annotated[float | None, Field(ge=0.0)] = None
    fats_grams: Annotated[float | None, Field(ge=0.0)] = None


class MealCalendarDay(BaseModel):
    meal_date: date_aliased
    meal_count: Annotated[int, Field(ge=0)]
    total_calories: Annotated[float, Field(ge=0.0)]
    total_protein: Annotated[float, Field(ge=0.0)]
    total_carbs: Annotated[float, Field(ge=0.0)]
    total_fats: Annotated[float, Field(ge=0.0)]


class MealsListResponse(BaseModel):
    meals: list[MealWithPhotos]
    total: Annotated[int, Field(ge=0)]


class MealsCalendarResponse(BaseModel):
    dates: list[MealCalendarDay]


class MacrosTotals(BaseModel):
    protein_g: Annotated[float, Field(ge=0.0)]
    fat_g: Annotated[float, Field(ge=0.0)]
    carbs_g: Annotated[float, Field(ge=0.0)]


class DailySummary(BaseModel):
    user_id: str
    date: date_aliased
    kcal_total: Annotated[float, Field(ge=0.0)]
    macros_totals: MacrosTotals


class TodayResponse(BaseModel):
    meals: list[dict[str, Any]]
    daily_summary: DailySummary


class GoalRequest(BaseModel):
    daily_kcal_target: int


class GoalResponse(BaseModel):
    id: UUID
    user_id: UUID
    daily_kcal_target: int
    created_at: AwareDatetime | None = None
    updated_at: AwareDatetime | None = None


class DailyDataPoint(BaseModel):
    date: date_aliased
    total_calories: Annotated[float, Field(ge=0.0)]
    total_protein: Annotated[float, Field(ge=0.0)]
    total_fat: Annotated[float, Field(ge=0.0)]
    total_carbs: Annotated[float, Field(ge=0.0)]
    meal_count: Annotated[int, Field(ge=0)]
    goal_calories: Annotated[float | None, Field(ge=0.0)] = None
    goal_achievement: float | None = None


class StatisticsPeriod(BaseModel):
    start_date: date_aliased
    end_date: date_aliased
    total_days: Annotated[int, Field(ge=1)]


class StatisticsSummary(BaseModel):
    total_meals: Annotated[int, Field(ge=0)]
    average_daily_calories: Annotated[float, Field(ge=0.0)]
    average_goal_achievement: float | None = None


class DailyStatisticsResponse(BaseModel):
    data: list[DailyDataPoint]
    period: StatisticsPeriod
    summary: StatisticsSummary


class MacroStatisticsResponse(BaseModel):
    protein_percent: Annotated[float, Field(ge=0.0, le=100.0)]
    fat_percent: Annotated[float, Field(ge=0.0, le=100.0)]
    carbs_percent: Annotated[float, Field(ge=0.0, le=100.0)]
    protein_grams: Annotated[float, Field(ge=0.0)]
    fat_grams: Annotated[float, Field(ge=0.0)]
    carbs_grams: Annotated[float, Field(ge=0.0)]
    total_calories: Annotated[float, Field(ge=0.0)]
    period: StatisticsPeriod


class FeedbackSubmissionRequest(BaseModel):
    message_type: FeedbackMessageType
    message_content: Annotated[str, Field(max_length=5000, min_length=1)]
    user_context: dict[str, Any] | None = None


class FeedbackSubmissionResponse(BaseModel):
    id: UUID
    status: FeedbackStatus
    created_at: AwareDatetime
    message: str


class FeedbackSubmission(BaseModel):
    id: UUID
    user_id: str
    message_type: FeedbackMessageType
    message_content: str
    user_context: dict[str, Any] | None = None
    status: FeedbackStatus
    admin_notes: str | None = None
    created_at: AwareDatetime
    updated_at: AwareDatetime


class ConnectivityResponse(BaseModel):
    status: ConnectionStatus
    services: dict[str, Any]
    response_time_ms: float
    correlation_id: UUID
    timestamp: AwareDatetime


class InlineTriggerType(StrEnum):
    inline_query = "inline_query"
    reply_mention = "reply_mention"
    tagged_photo = "tagged_photo"


class InlineChatType(StrEnum):
    private = "private"
    group = "group"


class InlineInteractionJob(BaseModel):
    job_id: UUID
    trigger_type: InlineTriggerType
    chat_type: InlineChatType
    chat_id: int | None = None
    chat_id_hash: str | None = None
    thread_id: int | None = None
    reply_to_message_id: int | None = None
    inline_message_id: str | None = None
    file_id: str
    origin_message_id: str | None = None
    source_user_id: int | None = None
    source_user_hash: str | None = None
    requested_at: AwareDatetime


class InlinePermissionNotification(BaseModel):
    chat_id_hash: str
    source_user_hash: str
    last_notified_at: AwareDatetime


class InlineFailureReason(BaseModel):
    reason: str
    count: Annotated[int, Field(ge=0)]


class InlineAnalyticsDaily(BaseModel):
    id: UUID
    date: date_aliased
    chat_type: InlineChatType
    trigger_counts: dict[str, int]
    request_count: Annotated[int, Field(ge=0)]
    success_count: Annotated[int, Field(ge=0)]
    failure_count: Annotated[int, Field(ge=0)]
    permission_block_count: Annotated[int, Field(ge=0)]
    avg_ack_latency_ms: Annotated[int, Field(ge=0)]
    p95_result_latency_ms: Annotated[int, Field(ge=0)]
    accuracy_within_tolerance_pct: Annotated[float, Field(ge=0.0, le=100.0)]
    failure_reasons: list[InlineFailureReason] | None = None
    last_updated_at: AwareDatetime


class Environment(StrEnum):
    development = "development"
    production = "production"


class Theme(StrEnum):
    light = "light"
    dark = "dark"
    auto = "auto"


class ThemeSource(StrEnum):
    telegram = "telegram"
    system = "system"
    manual = "manual"


class LanguageSource(StrEnum):
    telegram = "telegram"
    browser = "browser"
    manual = "manual"


class UIConfiguration(BaseModel):
    id: UUID
    environment: Environment
    api_base_url: str
    safe_area_top: int | None = 0
    safe_area_bottom: int | None = 0
    safe_area_left: int | None = 0
    safe_area_right: int | None = 0
    theme: Theme | None = None
    theme_source: ThemeSource | None = None
    language: str | None = "en"
    language_source: LanguageSource | None = None
    features: dict[str, bool] | None = None
    created_at: AwareDatetime
    updated_at: AwareDatetime


class UIConfigurationUpdate(BaseModel):
    environment: Environment | None = None
    api_base_url: str | None = None
    safe_area_top: int | None = None
    safe_area_bottom: int | None = None
    safe_area_left: int | None = None
    safe_area_right: int | None = None
    theme: Theme | None = None
    theme_source: ThemeSource | None = None
    language: str | None = None
    language_source: LanguageSource | None = None
    features: dict[str, bool] | None = None


class ThemeDetectionResponse(BaseModel):
    theme: Theme
    theme_source: ThemeSource
    telegram_color_scheme: str | None = None
    system_prefers_dark: bool | None = None
    detected_at: AwareDatetime


class LanguageDetectionResponse(BaseModel):
    language: str
    language_source: LanguageSource
    telegram_language_code: str | None = None
    browser_language: str | None = None
    detected_at: AwareDatetime
    supported_languages: list[str]


class LogLevel(StrEnum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class LogEntry(BaseModel):
    id: UUID
    timestamp: AwareDatetime
    level: LogLevel
    message: str
    correlation_id: UUID | None = None
    module: str | None = None
    function: str | None = None
    user_id: str | None = None
    request_id: str | None = None
    context: dict[str, Any] | None = None
    error_details: dict[str, Any] | None = None


class LogEntryCreate(BaseModel):
    level: LogLevel
    message: str
    correlation_id: UUID | None = None
    module: str | None = None
    function: str | None = None
    context: dict[str, Any] | None = None
    inline_trigger: str | None = None
    inline_stage: str | None = None


class DevelopmentEnvironment(BaseModel):
    id: UUID
    name: str
    frontend_port: int
    backend_port: int
    supabase_db_url: str
    supabase_db_password: str
    redis_url: str
    storage_endpoint: str
    cors_origins: list[str]
    log_level: str
    hot_reload: bool
    supabase_cli_version: str
    created_at: AwareDatetime
    updated_at: AwareDatetime
