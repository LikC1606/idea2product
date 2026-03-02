"""Hugging Face Model Search Service - Search and fetch model documentation."""

from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError
from typing import List, Optional, Dict, Any
from src.utils.logger import get_logger

logger = get_logger(__name__)

# Max chars for model card text to avoid token overflow
_CARD_MAX_CHARS = 3000
_MIN_DOWNLOADS = 1000  # Minimum downloads to be considered

# Task type to pipeline_tag mapping (expanded from paper2projecttest)
_TASK_MAPPING = {
    # Image tasks
    "图像生成": "text-to-image",
    "文本生成图像": "text-to-image",
    "图像编辑": "image-to-image",
    "图像到图像": "image-to-image",
    "人脸编辑": "image-to-image",
    "人脸替换": "image-to-image",
    "人像美化": "image-to-image",
    "图像修复": "image-to-image",
    "风格迁移": "image-to-image",
    "超分辨率": "image-to-image",
    # Detection & Classification
    "目标检测": "object-detection",
    "物体检测": "object-detection",
    "图像分类": "image-classification",
    "图像分割": "image-segmentation",
    # NLP tasks
    "翻译": "translation",
    "文本生成": "text-generation",
    "对话": "conversational",
    "问答": "question-answering",
    "文本分类": "text-classification",
    "情感分析": "sentiment-analysis",
    "nlp": "text-classification",
    "自然语言": "text-classification",
    "文本": "text-classification",
    "情感": "sentiment-analysis",
    "sentiment": "sentiment-analysis",
    "分类": "text-classification",
    "classification": "text-classification",
    "embedding": "feature-extraction",
    "图像": "image-classification",
    "image": "image-classification",
    "transformer": "text-classification",
    "bert": "text-classification",
    "summarize": "summarization",
    "摘要": "summarization",
    "问答": "question-answering",
    "question answering": "question-answering",
    "ner": "token-classification",
    "命名实体": "token-classification",
    "翻译": "translation",
    "translation": "translation",
    # Speech
    "语音识别": "automatic-speech-recognition",
    # Other common patterns
    "文字": "text-classification",
    "语言": "text-classification",
}


def _import_hf():
    """Lazy import to avoid hard dependency when feature is disabled."""
    try:
        from huggingface_hub import HfApi
        return HfApi
    except ImportError:
        return None


def _import_hf_hub_download():
    """Lazy import hf_hub_download."""
    try:
        from huggingface_hub import hf_hub_download
        return hf_hub_download
    except ImportError:
        return None


def _import_model_card():
    """Lazy import ModelCard."""
    try:
        from huggingface_hub import ModelCard
        return ModelCard
    except ImportError:
        return None


def get_pipeline_tag(task_name: str, task_description: str = "") -> Optional[str]:
    """Get Hugging Face pipeline_tag for task based on keywords."""
    text = f"{task_name} {task_description}".lower()
    for keyword, tag in _TASK_MAPPING.items():
        if keyword.lower() in text:
            return tag
    return None


class HfModelService:
    """
    Service for searching Hugging Face models and fetching their documentation.

    Used by AlgorithmAnalysisAgent when tasks involve ML/NLP/CV to suggest
    suitable models and design algorithms based on their API documentation.

    Features (enhanced from paper2projecttest):
    - Task type mapping to pipeline_tag
    - Inference Available filtering
    - Relevance scoring based on keywords
    - Diversity filtering (same series max N models)
    """

    def __init__(
        self,
        token: Optional[str] = None,
        search_limit: int = 5,
        timeout: int = 30,
        min_downloads: int = _MIN_DOWNLOADS,
    ):
        """
        Initialize the HF model service.

        Args:
            token: Hugging Face API token (optional, for private models)
            search_limit: Maximum number of models to return per search
            timeout: Request timeout in seconds
            min_downloads: Minimum downloads to consider (default 1000)
        """
        self.token = token
        self.search_limit = search_limit
        self.timeout = timeout
        self.min_downloads = min_downloads

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
            List of dicts with model_id, pipeline_tag, downloads, likes
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
                direction=-1,
                limit=limit * 10,  # Get more for filtering
            )
            results = []
            for m in models_iter:
                model_id = getattr(m, "id", None) or getattr(m, "modelId", None)
                if not model_id:
                    continue
                # Filter by minimum downloads
                downloads = getattr(m, "downloads", None) or 0
                if downloads < self.min_downloads:
                    continue
                pipeline = getattr(m, "pipeline_tag", None) or ""
                likes = getattr(m, "likes", None) or 0
                results.append({
                    "model_id": model_id,
                    "pipeline_tag": pipeline,
                    "downloads": downloads,
                    "likes": likes,
                })
                if len(results) >= limit * 5:
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

    def check_inference_available(self, model_id: str) -> bool:
        """
        Check if model supports Inference API.

        Args:
            model_id: Full model ID (e.g., "bert-base-uncased")

        Returns:
            True if Inference is available
        """
        HfApi = _import_hf()
        if HfApi is None:
            return True  # Assume available if can't check

        try:
            api = HfApi(token=self.token)
            model_info = api.model_info(model_id)
            # Check if model has Inference API (siblings contain inference endpoints)
            siblings = getattr(model_info, "siblings", None) or []
            for s in siblings:
                if "onnx" in (getattr(s, "rfilename", "") or "").lower():
                    return True
            # Also check model card for inference examples
            card = self.get_model_docs(model_id)
            if card and any(kw in card.lower() for kw in ["pipeline", "inference", "example", "from transformers import"]):
                return True
            return False
        except Exception as e:
            logger.debug(f"Could not check inference for {model_id}: {e}")
            return True  # Assume available on error

    def get_model_docs(self, model_id: str) -> Optional[str]:
        """
        Fetch model card (README) text for a given model.

        Args:
            model_id: Full model ID (e.g., "bert-base-uncased")

        Returns:
            Model card text (truncated) or None if failed
        """
        # Try hf_hub_download first (faster)
        hf_hub_download = _import_hf_hub_download()
        if hf_hub_download is not None:
            try:
                readme_path = hf_hub_download(
                    repo_id=model_id,
                    filename="README.md",
                    repo_type="model",
                    token=self.token,
                )
                with open(readme_path, 'r', encoding='utf-8', errors='ignore') as f:
                    text = f.read()
                if len(text) > _CARD_MAX_CHARS:
                    text = text[:_CARD_MAX_CHARS] + "\n\n[... truncated ...]"
                return text
            except Exception:
                pass  # Fall back to ModelCard

        # Fallback to ModelCard
        ModelCard = _import_model_card()
        if ModelCard is None:
            return None

        def _do_fetch():
            card = ModelCard.load(model_id, token=self.token)
            text = getattr(card, "text", None) or getattr(card, "content", "") or ""
            if len(text) > _CARD_MAX_CHARS:
                text = text[:_CARD_MAX_CHARS] + "\n\n[... truncated ...]"
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

    def calculate_relevance_score(
        self,
        model: Dict[str, Any],
        keywords: List[str],
    ) -> float:
        """Calculate relevance score based on keywords in model_id."""
        if not keywords:
            return 0.0

        model_id = model.get("model_id", "").lower()
        score = 0.0
        for kw in keywords:
            kw_lower = kw.lower()
            if kw_lower in model_id:
                score += 2.0  # Higher weight for exact match in model_id

        # Also check card text if available
        card_text = model.get("card_text", "") or ""
        if card_text:
            for kw in keywords[:5]:  # Limit to top 5 keywords
                kw_lower = kw.lower()
                if kw_lower in card_text.lower():
                    score += 0.5

        return score

    def apply_diversity_filter(
        self,
        models: List[Dict[str, Any]],
        max_per_series: int = 3,
        target_count: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        Apply diversity filter to keep models from same series.

        E.g., "bert-base", "bert-large" are same series.
        """
        if len(models) <= target_count:
            return models

        selected = []
        series_seen = set()

        for model in models:
            model_id = model.get("model_id", "")
            # Extract series (e.g., "bert" from "bert-base-uncased")
            parts = model_id.split("-")
            if len(parts) >= 2:
                series = parts[0]
            else:
                series = model_id

            if series in series_seen:
                continue

            series_seen.add(series)
            selected.append(model)

            if len(selected) >= target_count:
                break

        return selected

    def search_and_fetch_docs(
        self,
        query: str,
        pipeline_tag: Optional[str] = None,
        limit: Optional[int] = None,
        keywords: Optional[List[str]] = None,
        check_inference: bool = False,
    ) -> List[Dict[str, Any]]:
        """
        Search models with enhanced filtering and ranking.

        Args:
            query: Search query
            pipeline_tag: Optional pipeline filter
            limit: Max models to return
            keywords: Keywords for relevance scoring
            check_inference: Whether to filter by Inference Available

        Returns:
            List of dicts with model_id, pipeline_tag, downloads, card_text
        """
        limit = limit or self.search_limit
        keywords = keywords or []

        # Step 1: Search models
        models = self.search_models(query=query, pipeline_tag=pipeline_tag, limit=limit * 5)

        if not models:
            return []

        # Step 2: Optionally check Inference Available
        if check_inference:
            filtered = []
            for m in models[:50]:  # Check top 50
                if self.check_inference_available(m["model_id"]):
                    filtered.append(m)
            models = filtered
            logger.info(f"After Inference filter: {len(models)} models")

        # Step 3: Fetch docs for scoring
        for m in models:
            doc = self.get_model_docs(m.get("model_id", ""))
            m["card_text"] = doc or "(No documentation available)"

        # Step 4: Calculate relevance scores
        if keywords:
            for m in models:
                m["relevance_score"] = self.calculate_relevance_score(m, keywords)

            # Sort by combined score: relevance + quality
            def combined_score(m):
                relevance = m.get("relevance_score", 0)
                downloads = m.get("downloads", 0)
                quality = min(10, downloads / 100000)  # Normalize to 0-10
                # 60% relevance, 40% quality
                return relevance * 0.6 + quality * 0.4

            models.sort(key=combined_score, reverse=True)

        # Step 5: Apply diversity filter
        models = self.apply_diversity_filter(models, target_count=limit)

        # Clean up internal fields
        for m in models:
            m.pop("relevance_score", None)
            m.pop("likes", None)

        return models[:limit]
