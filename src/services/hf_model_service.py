"""Hugging Face Model Search Service - Search and fetch model documentation."""

from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError
from typing import List, Optional, Dict, Any
from src.utils.logger import get_logger

logger = get_logger(__name__)

# Max chars for model card text to avoid token overflow
_CARD_MAX_CHARS = 3000


def _import_hf():
    """Lazy import to avoid hard dependency when feature is disabled."""
    try:
        from huggingface_hub import HfApi
        return HfApi
    except ImportError:
        return None


def _import_model_card():
    """Lazy import ModelCard."""
    try:
        from huggingface_hub import ModelCard
        return ModelCard
    except ImportError:
        return None


class HfModelService:
    """
    Service for searching Hugging Face models and fetching their documentation.

    Used by AlgorithmAnalysisAgent when tasks involve ML/NLP/CV to suggest
    suitable models and design algorithms based on their API documentation.
    """

    def __init__(
        self,
        token: Optional[str] = None,
        search_limit: int = 5,
        timeout: int = 30,
    ):
        """
        Initialize the HF model service.

        Args:
            token: Hugging Face API token (optional, for private models)
            search_limit: Maximum number of models to return per search
            timeout: Request timeout in seconds
        """
        self.token = token
        self.search_limit = search_limit
        self.timeout = timeout

    def search_models(
        self,
        query: str,
        pipeline_tag: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Search Hugging Face for models matching the query.

        Args:
            query: Free-text search (e.g., "sentiment analysis", "image classification")
            pipeline_tag: Optional pipeline tag filter (e.g., "text-classification")
            limit: Max results (default: self.search_limit)

        Returns:
            List of dicts with model_id, pipeline_tag, downloads, card_text (truncated)
        """
        HfApi = _import_hf()
        if HfApi is None:
            logger.warning("huggingface_hub not installed; HF model search disabled")
            return []

        limit = limit or self.search_limit

        def _do_search():
            api = HfApi(token=self.token)
            models_iter = api.list_models(
                search=query if query else None,
                pipeline_tag=pipeline_tag,
                sort="downloads",
                limit=limit,
            )
            results = []
            for m in models_iter:
                model_id = getattr(m, "id", None) or getattr(m, "modelId", None)
                if not model_id:
                    continue
                pipeline = getattr(m, "pipeline_tag", None) or ""
                downloads = getattr(m, "downloads", None) or 0
                results.append({
                    "model_id": model_id,
                    "pipeline_tag": pipeline,
                    "downloads": downloads,
                })
                if len(results) >= limit:
                    break
            return results

        try:
            with ThreadPoolExecutor(max_workers=1) as ex:
                fut = ex.submit(_do_search)
                results = fut.result(timeout=self.timeout)
            logger.info(f"HF search '{query}' found {len(results)} models")
            return results
        except FuturesTimeoutError:
            logger.warning(f"HF model search timed out after {self.timeout}s")
            return []
        except Exception as e:
            logger.warning(f"HF model search failed: {e}")
            return []

    def get_model_docs(self, model_id: str) -> Optional[str]:
        """
        Fetch model card (README) text for a given model.

        Args:
            model_id: Full model ID (e.g., "bert-base-uncased")

        Returns:
            Model card text (truncated) or None if failed
        """
        ModelCard = _import_model_card()
        if ModelCard is None:
            return None

        def _do_fetch():
            card = ModelCard.load(model_id, token=self.token)
            text = getattr(card, "text", None) or getattr(card, "content", "") or ""
            if len(text) > _CARD_MAX_CHARS:
                text = text[: _CARD_MAX_CHARS] + "\n\n[... truncated ...]"
            return text

        try:
            with ThreadPoolExecutor(max_workers=1) as ex:
                fut = ex.submit(_do_fetch)
                return fut.result(timeout=self.timeout)
        except FuturesTimeoutError:
            logger.debug(f"Model card fetch for {model_id} timed out")
            return None
        except Exception as e:
            logger.debug(f"Could not fetch model card for {model_id}: {e}")
            return None

    def search_and_fetch_docs(
        self,
        query: str,
        pipeline_tag: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Search models and enrich each with model card documentation.

        Args:
            query: Search query
            pipeline_tag: Optional pipeline filter
            limit: Max models to return

        Returns:
            List of dicts with model_id, pipeline_tag, downloads, card_text
        """
        models = self.search_models(query=query, pipeline_tag=pipeline_tag, limit=limit)
        for m in models:
            model_id = m.get("model_id", "")
            if model_id:
                doc = self.get_model_docs(model_id)
                m["card_text"] = doc or "(No documentation available)"
            else:
                m["card_text"] = ""
        return models
