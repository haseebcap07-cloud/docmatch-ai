from __future__ import annotations

from app.services.generation_policy import MIN_BULLETS_PER_EMPLOYER, MAX_BULLETS_PER_EMPLOYER


def enforce_bullet_count(bullets: list[str], source_bullets: list[str] | None = None) -> tuple[list[str], list[str]]:
    warnings: list[str] = []
    source_bullets = source_bullets or []
    cleaned = [str(b).strip() for b in bullets if str(b).strip()]

    if len(cleaned) > MAX_BULLETS_PER_EMPLOYER:
        cleaned = cleaned[:MAX_BULLETS_PER_EMPLOYER]
        warnings.append("Condensed bullets to maximum 8 per employer/client.")

    if len(cleaned) < MIN_BULLETS_PER_EMPLOYER:
        for item in source_bullets:
            item = str(item).strip()
            if item and item not in cleaned:
                cleaned.append(item)
            if len(cleaned) >= MIN_BULLETS_PER_EMPLOYER:
                break

    if len(cleaned) < MIN_BULLETS_PER_EMPLOYER:
        warnings.append("Could not truthfully expand to 7 bullets because source evidence was limited.")

    return cleaned[:MAX_BULLETS_PER_EMPLOYER], warnings
