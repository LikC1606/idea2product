"""
Paper to Project Agent - Analyze academic papers and generate application ideas.

This agent takes a research paper (PDF or text) and generates a structured
application idea that can be built using the Idea2Product pipeline.
"""

from pathlib import Path
from typing import Optional, Union, List, Dict, Any
from src.core.data_models import Requirements, Feature
from src.services.llm_service import LLMService
from src.utils.logger import get_logger

logger = get_logger(__name__)

# Try to import PDF parsing libraries
def _import_pdf_reader():
    """Try to import pdf libraries, return None if not available."""
    try:
        from pypdf import PdfReader
        return "pypdf"
    except ImportError:
        pass

    try:
        import pdfplumber
        return "pdfplumber"
    except ImportError:
        pass

    return None


def extract_text_from_pdf(file_path: str) -> str:
    """Extract text from PDF file."""
    pdf_lib = _import_pdf_reader()

    if pdf_lib is None:
        raise ImportError(
            "No PDF library available. Install pypdf: pip install pypdf"
        )

    text_parts = []

    if pdf_lib == "pypdf":
        reader = PdfReader(file_path)
        for page in reader.pages:
            text = page.extract_text()
            if text:
                text_parts.append(text)
    elif pdf_lib == "pdfplumber":
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    text_parts.append(text)

    return "\n\n".join(text_parts)


class PaperToProjectAgent:
    """
    Agent that analyzes academic papers and generates application ideas.

    Workflow:
    1. Extract text from PDF or use provided text
    2. Use LLM to analyze paper (abstract, methods, contributions)
    3. Generate application ideas based on the paper
    4. Output structured Requirements (compatible with Stage 2)
    """

    def __init__(self, llm_service: LLMService):
        self.llm_service = llm_service

    def analyze_paper(
        self,
        paper_text: str,
        max_chars: int = 15000,
    ) -> Dict[str, Any]:
        """
        Analyze paper content and extract key information.

        Args:
            paper_text: Full text of the paper
            max_chars: Maximum characters to send to LLM

        Returns:
            Dict with paper analysis
        """
        # Truncate if too long
        if len(paper_text) > max_chars:
            paper_text = paper_text[:max_chars] + "\n\n[... truncated ...]"

        prompt = f"""You are an expert at analyzing academic research papers.
Analyze the following paper and extract key information that could be used to build a practical application.

Paper Content:
{paper_text}

Respond in JSON format:
{{
    "title": "Paper title",
    "abstract_summary": "2-3 sentence summary of the paper's main contribution",
    "methods": ["method1", "method2", ...],
    "key_technologies": ["technology1", "technology2", ...],
    "potential_applications": [
        {{
            "name": "Application name/idea",
            "description": "How this paper's technology could be turned into an app",
            "target_users": "Who would use this application"
        }}
    ],
    "technical_requirements": ["requirement1", "requirement2", ...],
    "innovative_features": ["feature1", "feature2", ...]
}}

Focus on extracting information that can be turned into a practical software application.
"""
        try:
            result = self.llm_service.generate_json(prompt)
            if isinstance(result, dict):
                return result
            logger.warning(f"Unexpected result type: {type(result)}")
            return {}
        except Exception as e:
            logger.error(f"Paper analysis failed: {e}")
            return {}

    def generate_idea(
        self,
        paper_analysis: Dict[str, Any],
        user_context: Optional[str] = None,
    ) -> Requirements:
        """
        Generate application idea from paper analysis.

        Args:
            paper_analysis: Result from analyze_paper()
            user_context: Optional user context/preferences

        Returns:
            Requirements object ready for Stage 2
        """
        context_section = ""
        if user_context:
            context_section = f"\nUser context: {user_context}"

        prompt = f"""Based on this paper analysis, generate a structured application idea.

Paper Analysis:
- Title: {paper_analysis.get('title', 'Unknown')}
- Abstract: {paper_analysis.get('abstract_summary', '')}
- Methods: {', '.join(paper_analysis.get('methods', []))}
- Technologies: {', '.join(paper_analysis.get('key_technologies', []))}
- Potential Applications: {paper_analysis.get('potential_applications', [])}
{context_section}

Generate a complete application Requirements in JSON format:

{{
    "title": "Application title (creative, appealing)",
    "description": "High-level description of the application (2-3 sentences)",
    "features": [
        {{
            "name": "Feature name",
            "description": "What this feature does",
            "priority": "must-have | should-have | nice-to-have"
        }}
    ],
    "constraints": ["Technical constraint 1", ...],
    "target_users": "Who is the target user group",
    "data_requirements": "What data does the app need to store"
}}

Make the application practical, buildable, and appealing. Focus on a specific use case.
"""

        try:
            result = self.llm_service.generate_json(prompt)
            if isinstance(result, dict):
                # Convert to Requirements
                features = []
                for f in result.get("features", []):
                    features.append(Feature(
                        name=f.get("name", "Unnamed feature"),
                        description=f.get("description", ""),
                        priority=f.get("priority", "should-have")
                    ))

                requirements = Requirements(
                    title=result.get("title", "Untitled Application"),
                    description=result.get("description", ""),
                    features=features,
                    constraints=result.get("constraints", []),
                    target_users=result.get("target_users"),
                    data_requirements=result.get("data_requirements"),
                )
                return requirements
            else:
                raise ValueError(f"Unexpected result type: {type(result)}")

        except Exception as e:
            logger.error(f"Requirements generation failed: {e}")
            # Return a minimal requirements
            return Requirements(
                title="Application from Paper",
                description=paper_analysis.get("abstract_summary", "An application based on the provided paper."),
                features=[],
            )

    def execute(
        self,
        paper_input: Union[str, Path],
        input_type: str = "auto",
        user_context: Optional[str] = None,
    ) -> Requirements:
        """
        Main entry point: analyze paper and generate requirements.

        Args:
            paper_input: PDF file path or text content
            input_type: "pdf", "text", or "auto" (detect)
            user_context: Optional user context

        Returns:
            Requirements object ready for Stage 2
        """
        logger.info("Starting paper analysis...")

        # Extract text based on input type
        if input_type == "auto":
            if isinstance(paper_input, str):
                # Check if it's a file path
                if Path(paper_input).suffix.lower() in [".pdf", ".txt"]:
                    input_type = "pdf" if paper_input.endswith(".pdf") else "text"
                else:
                    # Try to treat as text first
                    input_type = "text"
            elif isinstance(paper_input, Path):
                input_type = "pdf" if paper_input.suffix.lower() == ".pdf" else "text"

        # Extract text
        if input_type == "pdf":
            logger.info(f"Extracting text from PDF: {paper_input}")
            paper_text = extract_text_from_pdf(str(paper_input))
        else:
            logger.info("Using provided text")
            paper_text = str(paper_input)

        logger.info(f"Extracted {len(paper_text)} characters")

        # Analyze paper
        logger.info("Analyzing paper content...")
        analysis = self.analyze_paper(paper_text)
        logger.info(f"Paper title: {analysis.get('title', 'Unknown')}")

        # Generate idea
        logger.info("Generating application idea...")
        requirements = self.generate_idea(analysis, user_context)
        logger.info(f"Generated: {requirements.title}")

        return requirements

    def execute_from_file(
        self,
        file_path: str,
        user_context: Optional[str] = None,
    ) -> Requirements:
        """Convenience method for file input."""
        return self.execute(file_path, input_type="pdf", user_context=user_context)

    def execute_from_text(
        self,
        text: str,
        user_context: Optional[str] = None,
    ) -> Requirements:
        """Convenience method for text input."""
        return self.execute(text, input_type="text", user_context=user_context)
