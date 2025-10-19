"""Rendering helpers for inline placeholders and result messages."""

from __future__ import annotations

from typing import Any

from ..schemas import InlineChatType, InlineTriggerType

PRIVACY_NOTICE_LINE = (
    "Privacy notice: We only retain anonymised aggregates and purge inline photos within 24 hours."
)
INLINE_USAGE_GUIDE_LINE = (
    "View the inline usage guide in quickstart.md for manual verification steps."
)


def _as_float(value: Any, default: float = 0.0) -> float:
    if isinstance(value, int | float):
        return float(value)
    return default


def build_inline_placeholder(*, trigger_type: InlineTriggerType, chat_type: InlineChatType) -> str:
    """Return placeholder text shown while inline analysis is running."""
    lines: list[str] = ["🔄 <b>Analyzing meal photo…</b>"]

    if chat_type == InlineChatType.private:
        lines.append(PRIVACY_NOTICE_LINE)
        lines.append(INLINE_USAGE_GUIDE_LINE)

    if trigger_type == InlineTriggerType.reply_mention and chat_type == InlineChatType.group:
        lines.append("We'll reply to this thread as soon as the summary is ready.")

    return "\n".join(lines)


def build_inline_result_text(
    *,
    estimation: dict[str, Any],
    chat_type: InlineChatType,
    accuracy_tolerance_pct: float = 5.0,
) -> str:
    """Format the final inline summary message."""
    lines: list[str] = ["✅ <b>Meal analysis ready!</b>"]

    kcal_mean = estimation.get("kcal_mean")
    kcal_min = estimation.get("kcal_min")
    kcal_max = estimation.get("kcal_max")
    confidence = estimation.get("confidence")
    macros = estimation.get("macronutrients") or {}
    items = estimation.get("items") or []

    if isinstance(kcal_mean, int | float):
        range_text = ""
        if isinstance(kcal_min, int | float) and isinstance(kcal_max, int | float):
            range_text = f" ({kcal_min:.0f}-{kcal_max:.0f})"
        lines.append(f"🔥 <b>{kcal_mean:.0f} kcal</b>{range_text}")

    if isinstance(confidence, int | float):
        lines.append(f"📊 Confidence: {confidence:.0%}")

    if macros:
        lines.append(
            "⚖️ Macros — "
            f"Protein: {_as_float(macros.get('protein')):.1f}g | "
            f"Carbs: {_as_float(macros.get('carbs')):.1f}g | "
            f"Fats: {_as_float(macros.get('fats')):.1f}g"
        )

    if items:
        lines.append("")
        lines.append("<b>Top items:</b>")
        for item in items[:3]:
            label = item.get("label", "Unknown")
            kcal = item.get("kcal")
            item_confidence = item.get("confidence")
            detail_parts: list[str] = []
            if isinstance(kcal, int | float):
                detail_parts.append(f"{kcal:.0f} kcal")
            if isinstance(item_confidence, int | float):
                detail_parts.append(f"{item_confidence:.0%}")
            detail = f": {' · '.join(detail_parts)}" if detail_parts else ""
            lines.append(f"• {label}{detail}")

    lines.append(
        f"\nInfo: Results stay within ±{accuracy_tolerance_pct:.0f}% of our benchmark dataset."
    )

    if chat_type == InlineChatType.private:
        lines.append("")
        lines.append(PRIVACY_NOTICE_LINE)
        lines.append(INLINE_USAGE_GUIDE_LINE)

    return "\n".join(lines)
