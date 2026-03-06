"""Stage 2 planning for non-web products: PDF, video, audio.

Provides plan_pdf, plan_video, plan_audio that take Requirements and LLMService
and return type-specific spec dicts (latex_specs, video_specs, audio_specs).
"""

import json
import re
from typing import Dict, Any

from src.core.data_models import Requirements
from src.services.llm_service import LLMService
from src.utils.logger import get_logger

logger = get_logger(__name__)


def _features_text(requirements: Requirements) -> str:
    if not requirements.features:
        return requirements.description or ""
    return "\n".join(f"- {f.name}: {f.description}" for f in requirements.features[:15])


def _parse_json_spec(raw: str) -> Dict[str, Any]:
    """Extract JSON object from LLM response, with fallback to empty dict."""
    raw = raw.strip()
    # Strip markdown code block if present
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[-1].rsplit("```", 1)[0]
    try:
        obj = json.loads(raw)
        return obj if isinstance(obj, dict) else {"content": obj}
    except json.JSONDecodeError:
        # Try to find first {...}
        match = re.search(r"\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}", raw, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(0))
            except json.JSONDecodeError:
                pass
        logger.warning("Could not parse JSON spec from LLM response, using placeholder")
        return {"raw_preview": raw[:500] if len(raw) > 500 else raw}


def plan_pdf(requirements: Requirements, llm: LLMService) -> Dict[str, Any]:
    """Produce LaTeX/PDF document specs from requirements (sections, template, placeholders)."""
    features = _features_text(requirements)
    prompt = f"""You are planning a PDF/document output. Given the following requirements, output a JSON object with:
- "title": document title
- "sections": list of section objects, each with "heading", "content_summary", "placeholder_charts" (optional list)
- "template": suggested template style (e.g. report, article, minimal)
- "notes": any LaTeX or export notes

Requirements:
Title: {requirements.title}
Description: {requirements.description or 'N/A'}

Features:
{features}

Return only a single JSON object, no markdown or explanation."""

    try:
        raw = llm.generate(prompt, max_tokens=2000)
        return _parse_json_spec(raw)
    except Exception as e:
        logger.warning("plan_pdf LLM call failed: %s", e)
        return {
            "title": requirements.title,
            "sections": [{"heading": "Content", "content_summary": requirements.description or "To be generated"}],
            "template": "article",
            "notes": "Fallback spec due to LLM error",
        }


def plan_video(requirements: Requirements, llm: LLMService) -> Dict[str, Any]:
    """Produce video specs: script outline, scenes, duration, narration."""
    features = _features_text(requirements)
    prompt = f"""You are planning a video output. Given the following requirements, output a JSON object with:
- "title": video title
- "duration_seconds": estimated duration (integer)
- "script_outline": short narrative or bullet outline
- "scenes": list of scene objects with "sequence", "description", "visual_notes", "narration" (optional)
- "format": e.g. mp4, aspect ratio note

Requirements:
Title: {requirements.title}
Description: {requirements.description or 'N/A'}

Features:
{features}

Return only a single JSON object, no markdown or explanation."""

    try:
        raw = llm.generate(prompt, max_tokens=2000)
        return _parse_json_spec(raw)
    except Exception as e:
        logger.warning("plan_video LLM call failed: %s", e)
        return {
            "title": requirements.title,
            "duration_seconds": 60,
            "script_outline": requirements.description or "To be generated",
            "scenes": [{"sequence": 1, "description": "Main content", "visual_notes": "", "narration": ""}],
            "format": "mp4",
        }


def plan_audio(requirements: Requirements, llm: LLMService) -> Dict[str, Any]:
    """Produce audio specs: script, voice, format."""
    features = _features_text(requirements)
    prompt = f"""You are planning an audio output (e.g. TTS, podcast segment). Given the following requirements, output a JSON object with:
- "title": audio title
- "script": full or outline script text
- "voice": suggested voice style (e.g. neutral, professional, warm)
- "format": e.g. mp3, wav
- "duration_estimate_seconds": optional estimate
- "notes": any production notes

Requirements:
Title: {requirements.title}
Description: {requirements.description or 'N/A'}

Features:
{features}

Return only a single JSON object, no markdown or explanation."""

    try:
        raw = llm.generate(prompt, max_tokens=2000)
        return _parse_json_spec(raw)
    except Exception as e:
        logger.warning("plan_audio LLM call failed: %s", e)
        return {
            "title": requirements.title,
            "script": requirements.description or "To be generated",
            "voice": "neutral",
            "format": "mp3",
            "notes": "Fallback spec due to LLM error",
        }
