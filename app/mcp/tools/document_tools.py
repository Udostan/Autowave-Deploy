"""
Document Tools for MCP Server.
These tools handle document generation, analysis, and formatting.
"""

import logging
import json
import base64
import re
import os
import tempfile
import subprocess
import time
from typing import Dict, List, Any, Optional
import requests
from bs4 import BeautifulSoup
from datetime import datetime

logger = logging.getLogger(__name__)

class DocumentTools:
    """
    Tools for generating, analyzing, and formatting documents.
    """

    def __init__(self):
        """Initialize the document tools."""
        self.logger = logging.getLogger(__name__)

        # Load API keys from environment
        from dotenv import load_dotenv
        load_dotenv()

        # Initialize LLM API clients
        try:
            from app.api.gemini import GeminiAPI
            self.gemini_api = GeminiAPI()
            self.has_llm_api = True
        except Exception as e:
            self.logger.warning(f"Failed to initialize Gemini API: {str(e)}")
            self.has_llm_api = False

        try:
            from app.utils.groq_api import GroqAPI
            self.groq_api = GroqAPI()
            self.has_groq_api = True
        except Exception as e:
            self.logger.warning(f"Failed to initialize Groq API: {str(e)}")
            self.has_groq_api = False

        # Initialize supported document types
        self.document_types = {
            "report": self._generate_report_template,
            "essay": self._generate_essay_template,
            "legal": self._generate_legal_template,
            "business": self._generate_business_template,
            "academic": self._generate_academic_template,
            "letter": self._generate_letter_template,
        }

        # Initialize citation styles
        self.citation_styles = {
            "apa": self._format_apa_citation,
            "mla": self._format_mla_citation,
            "chicago": self._format_chicago_citation,
            "harvard": self._format_harvard_citation,
            "ieee": self._format_ieee_citation,
        }

    def generate_document(self, content: str, document_type: str = "report",
                         title: str = "", citation_style: str = "apa",
                         include_references: bool = True, page_count: Optional[int] = None) -> Dict[str, Any]:
        """
        Generate a document based on content and type.

        Args:
            content: The main content for the document
            document_type: Type of document (report, essay, legal, etc.)
            title: Title of the document
            citation_style: Citation style to use (apa, mla, chicago, etc.)
            include_references: Whether to include references section
            page_count: Optional number of pages to generate (None for auto)

        Returns:
            Dictionary containing document data and preview image
        """
        self.logger.info(f"Generating {document_type} document: {title}")

        # Normalize document type
        document_type = document_type.lower().strip()

        # Map common terms to supported types
        document_type_mapping = {
            "business report": "business",
            "academic paper": "academic",
            "research paper": "academic",
            "legal document": "legal",
            "contract": "legal",
            "cover letter": "letter",
            "recommendation letter": "letter",
        }

        # Apply mapping if needed
        if document_type in document_type_mapping:
            document_type = document_type_mapping[document_type]

        # Default to report if type not supported
        if document_type not in self.document_types:
            self.logger.warning(f"Document type '{document_type}' not supported, defaulting to report")
            document_type = "report"

        # Normalize citation style
        citation_style = citation_style.lower().strip()
        if citation_style not in self.citation_styles:
            self.logger.warning(f"Citation style '{citation_style}' not supported, defaulting to APA")
            citation_style = "apa"

        # Try to generate document using LLM API with enhanced error handling
        try:
            self.logger.info(f"Attempting to generate {document_type} document with LLM API")
            formatted_document = self._generate_document_with_llm(
                content, document_type, title, citation_style, include_references, page_count
            )

            # Check if we got a valid document with sufficient content
            if formatted_document and len(formatted_document) > 1000:
                self.logger.info(f"Successfully generated document with LLM API: {len(formatted_document)} characters")
            else:
                self.logger.warning(f"Generated document is too short ({len(formatted_document) if formatted_document else 0} characters). Falling back to template.")
                raise ValueError("Generated document is too short or empty")
        except Exception as e:
            self.logger.warning(f"Failed to generate document with LLM API: {str(e)}. Falling back to template.")
            # Format the document based on type (fallback)
            generator_func = self.document_types[document_type]
            formatted_document = generator_func(content, title, citation_style, include_references)
            self.logger.info(f"Generated fallback template document: {len(formatted_document)} characters")

        # Convert to PDF
        pdf_data = self._convert_to_pdf(formatted_document, document_type)

        # Generate a preview image
        preview_image = self._generate_document_preview(pdf_data, document_type)

        return {
            "document": formatted_document,
            "pdf_base64": base64.b64encode(pdf_data).decode('utf-8'),
            "preview": preview_image,
            "title": title,
            "type": document_type
        }

    def analyze_document(self, document: str) -> Dict[str, Any]:
        """
        Analyze a document and provide insights.

        Args:
            document: The document content to analyze

        Returns:
            Dictionary containing analysis results
        """
        self.logger.info("Analyzing document")

        # Calculate basic metrics
        word_count = len(re.findall(r'\b\w+\b', document))
        sentence_count = len(re.findall(r'[.!?]+', document))
        paragraph_count = len(re.split(r'\n\s*\n', document))

        # Calculate readability scores
        flesch_reading_ease = self._calculate_flesch_reading_ease(document)
        flesch_kincaid_grade = self._calculate_flesch_kincaid_grade(document)

        # Identify potential issues
        issues = self._identify_document_issues(document)

        # Generate improvement suggestions
        suggestions = self._generate_improvement_suggestions(document, issues)

        return {
            "metrics": {
                "word_count": word_count,
                "sentence_count": sentence_count,
                "paragraph_count": paragraph_count,
                "avg_words_per_sentence": word_count / max(1, sentence_count),
                "avg_sentences_per_paragraph": sentence_count / max(1, paragraph_count)
            },
            "readability": {
                "flesch_reading_ease": flesch_reading_ease,
                "flesch_kincaid_grade": flesch_kincaid_grade,
                "readability_level": self._interpret_readability(flesch_reading_ease)
            },
            "issues": issues,
            "suggestions": suggestions
        }

    def _generate_report_template(self, content: str, title: str,
                                citation_style: str, include_references: bool) -> str:
        """Generate a report template with the given content."""
        current_date = datetime.now().strftime("%B %d, %Y")

        # Extract citations from content if needed
        citations = []
        if include_references:
            citations = self._extract_citations(content)

        # Format the report
        report = f"""
# {title}

**Date:** {current_date}

## Executive Summary

{self._extract_or_generate_summary(content)}

## Introduction

{self._extract_or_generate_introduction(content)}

## Main Content

{content}

## Conclusion

{self._extract_or_generate_conclusion(content)}
"""

        # Add references if needed
        if include_references and citations:
            citation_formatter = self.citation_styles[citation_style]
            references = "\n\n".join([citation_formatter(citation) for citation in citations])
            report += f"""
## References

{references}
"""

        return report

    def _generate_essay_template(self, content: str, title: str,
                               citation_style: str, include_references: bool) -> str:
        """Generate an essay template with the given content."""
        current_date = datetime.now().strftime("%B %d, %Y")

        # Extract citations from content if needed
        citations = []
        if include_references:
            citations = self._extract_citations(content)

        # Format the essay
        essay = f"""
# {title}

**Date:** {current_date}

## Introduction

{self._extract_or_generate_introduction(content)}

## Body

{content}

## Conclusion

{self._extract_or_generate_conclusion(content)}
"""

        # Add references if needed
        if include_references and citations:
            citation_formatter = self.citation_styles[citation_style]
            references = "\n\n".join([citation_formatter(citation) for citation in citations])
            essay += f"""
## Works Cited

{references}
"""

        return essay

    def _generate_legal_template(self, content: str, title: str,
                               citation_style: str, include_references: bool) -> str:
        """Generate a legal document template with the given content."""
        current_date = datetime.now().strftime("%B %d, %Y")

        # Format the legal document
        legal_doc = f"""
# {title}

**Date:** {current_date}

## AGREEMENT

THIS AGREEMENT is made and entered into as of {current_date}, by and between the parties.

## TERMS AND CONDITIONS

{content}

## SIGNATURES

IN WITNESS WHEREOF, the parties hereto have executed this Agreement as of the date first above written.

________________________
Party 1

________________________
Party 2
"""

        return legal_doc

    def _generate_business_template(self, content: str, title: str,
                                  citation_style: str, include_references: bool) -> str:
        """Generate a business document template with the given content."""
        current_date = datetime.now().strftime("%B %d, %Y")

        # Format the business document
        business_doc = f"""
# {title}

**Date:** {current_date}

## Executive Summary

{self._extract_or_generate_summary(content)}

## Business Overview

{self._extract_or_generate_introduction(content)}

## Detailed Analysis

{content}

## Recommendations

{self._extract_or_generate_recommendations(content)}

## Implementation Plan

{self._extract_or_generate_implementation(content)}
"""

        return business_doc

    def _generate_academic_template(self, content: str, title: str,
                                  citation_style: str, include_references: bool) -> str:
        """Generate an academic paper template with the given content."""
        current_date = datetime.now().strftime("%B %d, %Y")

        # Extract citations from content if needed
        citations = []
        if include_references:
            citations = self._extract_citations(content)

        # Format the academic paper
        academic_doc = f"""
# {title}

**Date:** {current_date}

## Abstract

{self._extract_or_generate_summary(content)}

## Introduction

{self._extract_or_generate_introduction(content)}

## Literature Review

{self._extract_or_generate_literature_review(content)}

## Methodology

{self._extract_or_generate_methodology(content)}

## Results

{self._extract_or_generate_results(content)}

## Discussion

{content}

## Conclusion

{self._extract_or_generate_conclusion(content)}
"""

        # Add references if needed
        if include_references and citations:
            citation_formatter = self.citation_styles[citation_style]
            references = "\n\n".join([citation_formatter(citation) for citation in citations])
            academic_doc += f"""
## References

{references}
"""

        return academic_doc

    def _generate_letter_template(self, content: str, title: str,
                                citation_style: str, include_references: bool) -> str:
        """Generate a letter template with the given content."""
        current_date = datetime.now().strftime("%B %d, %Y")

        # Format the letter
        letter = f"""
# {title}

**Date:** {current_date}

Dear [Recipient],

{content}

Sincerely,

[Your Name]
[Your Title]
[Your Contact Information]
"""

        return letter

    def _convert_to_pdf(self, document: str, document_type: str) -> bytes:
        """
        Convert a document to PDF format.

        Args:
            document: The document content
            document_type: The type of document

        Returns:
            PDF data as bytes
        """
        # For now, return a placeholder PDF
        # In a production system, this would use a PDF generation library

        # Create a minimal PDF
        pdf_data = b'%PDF-1.4\n1 0 obj\n<</Type/Catalog/Pages 2 0 R>>\nendobj\n2 0 obj\n<</Type/Pages/Kids[3 0 R]/Count 1>>\nendobj\n3 0 obj\n<</Type/Page/MediaBox[0 0 612 792]/Resources<<>>/Contents 4 0 R/Parent 2 0 R>>\nendobj\n4 0 obj\n<</Length 22>>\nstream\nBT\n/F1 12 Tf\n100 700 Td\n(Placeholder PDF) Tj\nET\nendstream\nendobj\nxref\n0 5\n0000000000 65535 f\n0000000009 00000 n\n0000000056 00000 n\n0000000111 00000 n\n0000000212 00000 n\ntrailer\n<</Size 5/Root 1 0 R>>\nstartxref\n284\n%%EOF'

        return pdf_data

    def _generate_document_with_llm(self, content: str, document_type: str,
                                title: str, citation_style: str, include_references: bool,
                                page_count: Optional[int] = None) -> str:
        """
        Generate a document using LLM API.

        Args:
            content: The main content for the document
            document_type: Type of document (report, essay, legal, etc.)
            title: Title of the document
            citation_style: Citation style to use (apa, mla, chicago, etc.)
            include_references: Whether to include references section
            page_count: Optional number of pages to generate (None for auto)

        Returns:
            Formatted document content
        """
        if not hasattr(self, 'has_llm_api') or not self.has_llm_api:
            raise Exception("LLM API not available")

        # Create a prompt for the LLM
        current_date = datetime.now().strftime("%B %d, %Y")

        if not title:
            title_prompt = f"Create a title for a {document_type} about: {content}"
            try:
                if hasattr(self, 'gemini_api') and self.has_llm_api:
                    title_response = self.gemini_api.generate_text(title_prompt)
                    title = title_response.strip().replace('"', '').replace("'", "")
                elif hasattr(self, 'groq_api') and self.has_groq_api:
                    title_response = self.groq_api.generate_text(title_prompt)
                    title = title_response.strip().replace('"', '').replace("'", "")
                else:
                    title = f"{document_type.capitalize()} about {content[:30]}..."
            except Exception as e:
                self.logger.warning(f"Failed to generate title: {str(e)}")
                title = f"{document_type.capitalize()} about {content[:30]}..."

        # Create the main document prompt
        # Adjust content length based on page count
        content_length = "1500-2000 words"
        if page_count:
            if page_count == 1:
                content_length = "800-1000 words"
            elif page_count == 2:
                content_length = "1500-2000 words"
            elif page_count == 3:
                content_length = "2000-2500 words"
            elif page_count <= 5:
                content_length = "3000-4000 words"
            elif page_count <= 10:
                content_length = "5000-7000 words"
            elif page_count <= 15:
                content_length = "8000-10000 words"
            else:
                content_length = "10000-15000 words"

        page_instruction = ""
        if page_count:
            page_instruction = f"Create enough content to fill approximately {page_count} pages. "

        prompt = f"""Generate a comprehensive, professional, and highly detailed {document_type} document with the title "{title}" about the following topic:

{content}

The document should be formatted in Markdown and include the following sections:
- Title: {title}
- Date: {current_date}

IMPORTANT GUIDELINES FOR PROFESSIONAL CONTENT:
1. {page_instruction}Create EXTENSIVE, DETAILED content with rich information and thorough analysis
2. Include at least {content_length} of substantive content
3. Use professional, authoritative language appropriate for business or academic contexts
4. Incorporate relevant statistics, data points, and specific examples to support key points
5. Include proper citations and references to industry experts or research when appropriate
6. Organize content with clear section headings, subheadings, and bullet points for readability
7. Ensure comprehensive coverage of all relevant aspects of the topic
8. Provide actionable insights and practical recommendations
9. Use proper formatting including bold text for emphasis on key points
10. Include tables or structured data representations where appropriate

The final document should be publication-ready and demonstrate expert-level knowledge of the subject matter.
"""

        # Add document type specific instructions
        if document_type == "report":
            prompt += """
REQUIRED SECTIONS (each with substantial content):
- Executive Summary (comprehensive overview of key findings and recommendations)
- Introduction (detailed context, purpose, scope, and methodology)
- Background (thorough historical context and relevant information)
- Current Situation Analysis (in-depth examination with supporting data)
- Key Findings (detailed analysis with multiple subsections)
- Discussion (thorough interpretation of findings with implications)
- Recommendations (specific, actionable items with implementation details)
- Conclusion (synthesis of key points and future outlook)
- References (properly formatted citations)
- Appendices (supporting materials, data tables, charts)

Include at least 3-4 detailed subsections under each main section with rich content.
"""
        elif document_type == "essay":
            prompt += """
REQUIRED SECTIONS (each with substantial content):
- Abstract (concise summary of the entire essay)
- Introduction (compelling hook, comprehensive context, clear thesis statement)
- Background (thorough historical or contextual information)
- Main Body (at least 4-5 major sections with multiple subsections)
  * Each section should thoroughly explore a distinct aspect of the topic
  * Include counterarguments and rebuttals where appropriate
  * Support claims with specific examples, data, and expert opinions
- Analysis (critical examination of implications and significance)
- Conclusion (synthesis of arguments, broader implications, call to action)
- References (properly formatted citations)

Ensure logical flow between sections with clear transitions and progressive development of ideas.
"""
        elif document_type == "legal":
            prompt += """
REQUIRED SECTIONS (each with substantial content):
- Preamble (detailed identification of parties and effective date)
- Definitions (comprehensive glossary of all relevant terms)
- Recitals (thorough background and purpose)
- Agreement Terms (detailed clauses with multiple subsections)
  * Rights and Obligations (comprehensive coverage of all parties)
  * Term and Termination (detailed conditions and procedures)
  * Representations and Warranties (extensive coverage)
  * Indemnification (detailed provisions)
  * Confidentiality (comprehensive protection measures)
  * Dispute Resolution (detailed procedures)
- General Provisions (thorough coverage of standard clauses)
- Execution (signature blocks with attestation provisions)
- Schedules and Exhibits (referenced throughout document)

Use precise legal language while maintaining clarity. Include detailed provisions addressing various contingencies.
"""
        elif document_type == "business":
            prompt += """
REQUIRED SECTIONS (each with substantial content):
- Executive Summary (comprehensive overview with key highlights and recommendations)
- Business Overview (detailed company background, mission, vision, and objectives)
- Market Analysis (comprehensive industry trends, competitive landscape, SWOT analysis)
- Customer Analysis (detailed customer segments, needs, and behaviors)
- Product/Service Analysis (comprehensive features, benefits, and competitive advantages)
- Financial Analysis (detailed projections, metrics, and performance indicators)
- Strategic Recommendations (specific, actionable items with implementation details)
- Implementation Plan (detailed timeline, resource requirements, and milestones)
- Risk Assessment (comprehensive analysis of potential challenges and mitigation strategies)
- Conclusion (synthesis of key points and future outlook)
- Appendices (supporting materials, data tables, charts)

Include relevant business metrics, KPIs, and data visualizations throughout the document.
"""
        elif document_type == "academic":
            prompt += """
REQUIRED SECTIONS (each with substantial content):
- Abstract (comprehensive summary of research question, methodology, findings, and significance)
- Introduction (detailed research context, problem statement, significance, and research questions)
- Literature Review (extensive review of relevant research organized thematically)
- Theoretical Framework (detailed explanation of underlying theories and conceptual models)
- Methodology (comprehensive description of research design, participants, instruments, procedures, and analysis)
- Results (detailed presentation of findings with statistical analysis where appropriate)
- Discussion (thorough interpretation of results, comparison with existing literature)
- Limitations (honest assessment of study constraints)
- Implications (detailed discussion of theoretical and practical implications)
- Future Research (specific recommendations for subsequent studies)
- Conclusion (synthesis of key contributions)
- References (comprehensive bibliography in appropriate academic format)
- Appendices (supporting materials, instruments, additional data)

Use formal academic language and proper citation throughout. Include tables and figures to illustrate key data.
"""
        elif document_type == "letter":
            prompt += """
REQUIRED SECTIONS (each with substantial content):
- Letterhead (professional header with complete contact information)
- Date (formatted professionally)
- Recipient Information (complete name, title, organization, and address)
- Formal Greeting (appropriate salutation)
- Introduction (clear purpose statement and context)
- Main Body (detailed, well-structured paragraphs with comprehensive content)
  * Include at least 3-4 substantive paragraphs
  * Provide specific details, examples, and supporting information
  * Maintain professional tone and language throughout
- Conclusion (clear summary and specific next steps or call to action)
- Formal Closing (appropriate closing phrase)
- Signature Block (complete with name, title, and contact information)
- Enclosures/Attachments (if applicable)
- CC/BCC (if applicable)
"""

        # Add citation style instructions
        if include_references:
            prompt += f"""
Include references in {citation_style.upper()} citation style.
"""

        # Generate the document using LLM API with increased token limit for detailed content
        try:
            # Prefer Groq for document generation as it handles longer content better
            if hasattr(self, 'groq_api') and self.has_groq_api:
                self.logger.info("Using Groq API for document generation")
                # System prompt to guide the generation of detailed, multi-page documents
                system_prompt = """You are an expert document creator specializing in professional, detailed, and comprehensive content.
                Your task is to create publication-quality documents with rich, detailed information.
                Always include multiple sections with detailed subsections.
                Create content that spans multiple pages (at least 5-10 pages) with thorough coverage of the topic.
                Use professional language, proper citations, and include relevant data and examples."""

                # Generate with Groq using maximum context length and longer timeout
                document_content = self.groq_api.generate_text(
                    prompt=prompt,
                    max_tokens=8192,  # Maximum tokens for Llama3-70B-8192
                    temperature=0.7,
                    system_prompt=system_prompt,
                    timeout=300  # 5 minutes timeout for very long generations
                )
                self.logger.info(f"Groq API generated document with {len(document_content)} characters")
            elif hasattr(self, 'gemini_api') and self.has_llm_api:
                self.logger.info("Using Gemini API for document generation")
                document_content = self.gemini_api.generate_text(prompt, max_tokens=8192, temperature=0.7)
            else:
                raise Exception("No LLM API available")

            # Clean up the document content
            document_content = document_content.strip()

            # Ensure the document has a title
            if not document_content.startswith("# "):
                document_content = f"# {title}\n\n{document_content}"

            return document_content
        except Exception as e:
            self.logger.error(f"Error generating document with LLM: {str(e)}")
            raise

    def _generate_document_preview(self, pdf_data: bytes, document_type: str) -> str:
        """
        Generate a preview image of a document.

        Args:
            pdf_data: PDF data
            document_type: The type of document

        Returns:
            Base64-encoded image data
        """
        # For now, return a placeholder image
        # In a production system, this would use a PDF rendering library

        # Create a simplified preview
        preview_svg = f"""<svg width="800" height="600" xmlns="http://www.w3.org/2000/svg">
            <rect width="100%" height="100%" fill="#1e1e1e"/>
            <rect x="0" y="0" width="100%" height="60" fill="#2d2d2d"/>
            <text x="20" y="35" font-family="Arial" font-size="16" fill="#e0e0e0">{document_type.capitalize()} Document Preview</text>
            <rect x="20" y="80" width="760" height="500" fill="#2d2d2d" stroke="#444444" stroke-width="1"/>
            <text x="400" y="300" font-family="Arial" font-size="24" fill="#e0e0e0" text-anchor="middle">Document Preview</text>
        </svg>"""

        # Convert SVG to base64
        svg_bytes = preview_svg.encode('utf-8')
        base64_svg = base64.b64encode(svg_bytes).decode('utf-8')

        return f"data:image/svg+xml;base64,{base64_svg}"

    def _extract_or_generate_summary(self, content: str) -> str:
        """Extract or generate a summary from the content."""
        # Look for summary or abstract section
        summary_match = re.search(r'(?i)(?:summary|abstract|executive\s+summary)[:\s]*([^\n]+(?:\n(?!\#\#)[^\n]+)*)', content)
        if summary_match:
            return summary_match.group(1).strip()

        # If no summary found, generate a simple one
        sentences = re.findall(r'[^.!?]+[.!?]', content)
        if sentences:
            # Use the first 2-3 sentences as a summary
            summary_length = min(3, len(sentences))
            return ' '.join(sentences[:summary_length]).strip()

        return "This document provides a comprehensive analysis and detailed information on the subject matter."

    def _extract_or_generate_introduction(self, content: str) -> str:
        """Extract or generate an introduction from the content."""
        # Look for introduction section
        intro_match = re.search(r'(?i)(?:introduction|overview)[:\s]*([^\n]+(?:\n(?!\#\#)[^\n]+)*)', content)
        if intro_match:
            return intro_match.group(1).strip()

        # If no introduction found, use the first paragraph
        paragraphs = re.split(r'\n\s*\n', content)
        if paragraphs:
            return paragraphs[0].strip()

        return "This document addresses key aspects of the subject matter and provides valuable insights."

    def _extract_or_generate_conclusion(self, content: str) -> str:
        """Extract or generate a conclusion from the content."""
        # Look for conclusion section
        conclusion_match = re.search(r'(?i)(?:conclusion|summary|final\s+thoughts)[:\s]*([^\n]+(?:\n(?!\#\#)[^\n]+)*)', content)
        if conclusion_match:
            return conclusion_match.group(1).strip()

        # If no conclusion found, use the last paragraph
        paragraphs = re.split(r'\n\s*\n', content)
        if paragraphs and len(paragraphs) > 1:
            return paragraphs[-1].strip()

        return "In conclusion, this document has presented key findings and insights that can be applied to address the subject matter effectively."

    def _extract_or_generate_recommendations(self, content: str) -> str:
        """Extract or generate recommendations from the content."""
        # Look for recommendations section
        recommendations_match = re.search(r'(?i)(?:recommendations|suggested\s+actions)[:\s]*([^\n]+(?:\n(?!\#\#)[^\n]+)*)', content)
        if recommendations_match:
            return recommendations_match.group(1).strip()

        return "Based on the analysis, the following recommendations are proposed:\n\n1. Implement a comprehensive strategy\n2. Allocate resources effectively\n3. Monitor progress and adjust as needed"

    def _extract_or_generate_implementation(self, content: str) -> str:
        """Extract or generate implementation plan from the content."""
        # Look for implementation section
        implementation_match = re.search(r'(?i)(?:implementation|action\s+plan|next\s+steps)[:\s]*([^\n]+(?:\n(?!\#\#)[^\n]+)*)', content)
        if implementation_match:
            return implementation_match.group(1).strip()

        return "Implementation Timeline:\n\n1. Phase 1 (Months 1-3): Initial setup and planning\n2. Phase 2 (Months 4-6): Execution of core components\n3. Phase 3 (Months 7-9): Evaluation and adjustments\n4. Phase 4 (Months 10-12): Full implementation and review"

    def _extract_or_generate_literature_review(self, content: str) -> str:
        """Extract or generate literature review from the content."""
        # Look for literature review section
        lit_review_match = re.search(r'(?i)(?:literature\s+review|previous\s+research|related\s+work)[:\s]*([^\n]+(?:\n(?!\#\#)[^\n]+)*)', content)
        if lit_review_match:
            return lit_review_match.group(1).strip()

        return "Previous research in this field has established several key findings. Smith (2020) demonstrated the importance of systematic approaches, while Jones (2021) highlighted the role of innovative methodologies. The current study builds upon these foundations while addressing gaps in the existing literature."

    def _extract_or_generate_methodology(self, content: str) -> str:
        """Extract or generate methodology from the content."""
        # Look for methodology section
        methodology_match = re.search(r'(?i)(?:methodology|methods|research\s+design)[:\s]*([^\n]+(?:\n(?!\#\#)[^\n]+)*)', content)
        if methodology_match:
            return methodology_match.group(1).strip()

        return "This study employed a mixed-methods approach combining qualitative and quantitative data collection. Participants were selected using stratified random sampling to ensure representativeness. Data analysis was conducted using statistical software and thematic analysis techniques."

    def _extract_or_generate_results(self, content: str) -> str:
        """Extract or generate results from the content."""
        # Look for results section
        results_match = re.search(r'(?i)(?:results|findings|outcomes)[:\s]*([^\n]+(?:\n(?!\#\#)[^\n]+)*)', content)
        if results_match:
            return results_match.group(1).strip()

        return "The analysis revealed several significant findings. First, there was a strong correlation between variables X and Y (r=0.78, p<0.01). Second, participants in the experimental group showed a 45% improvement compared to the control group. These results support the primary hypothesis of the study."

    def _extract_citations(self, content: str) -> List[Dict[str, str]]:
        """Extract citations from the content."""
        citations = []

        # Look for APA style citations (Author, Year)
        apa_citations = re.findall(r'\(([A-Za-z\s]+),\s*(\d{4})\)', content)
        for author, year in apa_citations:
            citations.append({
                "author": author.strip(),
                "year": year,
                "title": f"Article by {author.strip()}",
                "source": "Journal"
            })

        # Look for MLA style citations (Author page)
        mla_citations = re.findall(r'\(([A-Za-z\s]+)\s+(\d+)\)', content)
        for author, page in mla_citations:
            citations.append({
                "author": author.strip(),
                "year": "N/A",
                "title": f"Work by {author.strip()}",
                "source": "Book",
                "page": page
            })

        return citations

    def _format_apa_citation(self, citation: Dict[str, str]) -> str:
        """Format a citation in APA style."""
        author = citation.get("author", "Unknown Author")
        year = citation.get("year", "n.d.")
        title = citation.get("title", "Untitled")
        source = citation.get("source", "Unknown Source")

        return f"{author}. ({year}). {title}. {source}."

    def _format_mla_citation(self, citation: Dict[str, str]) -> str:
        """Format a citation in MLA style."""
        author = citation.get("author", "Unknown Author")
        title = citation.get("title", "Untitled")
        source = citation.get("source", "Unknown Source")
        year = citation.get("year", "n.d.")

        return f"{author}. \"{title}.\" {source}, {year}."

    def _format_chicago_citation(self, citation: Dict[str, str]) -> str:
        """Format a citation in Chicago style."""
        author = citation.get("author", "Unknown Author")
        year = citation.get("year", "n.d.")
        title = citation.get("title", "Untitled")
        source = citation.get("source", "Unknown Source")

        return f"{author}. {title}. {source}, {year}."

    def _format_harvard_citation(self, citation: Dict[str, str]) -> str:
        """Format a citation in Harvard style."""
        author = citation.get("author", "Unknown Author")
        year = citation.get("year", "n.d.")
        title = citation.get("title", "Untitled")
        source = citation.get("source", "Unknown Source")

        return f"{author} ({year}) {title}, {source}."

    def _format_ieee_citation(self, citation: Dict[str, str]) -> str:
        """Format a citation in IEEE style."""
        author = citation.get("author", "Unknown Author")
        title = citation.get("title", "Untitled")
        source = citation.get("source", "Unknown Source")
        year = citation.get("year", "n.d.")

        return f"{author}, \"{title},\" {source}, {year}."

    def _calculate_flesch_reading_ease(self, text: str) -> float:
        """Calculate the Flesch Reading Ease score."""
        # Count sentences
        sentences = len(re.findall(r'[.!?]+', text))
        if sentences == 0:
            return 0

        # Count words
        words = len(re.findall(r'\b\w+\b', text))
        if words == 0:
            return 0

        # Count syllables (simplified)
        syllables = 0
        for word in re.findall(r'\b\w+\b', text.lower()):
            # Count vowel groups as syllables (simplified)
            vowel_groups = len(re.findall(r'[aeiouy]+', word))
            # Adjust for common patterns
            if word.endswith('e'):
                vowel_groups -= 1
            if vowel_groups <= 0:
                vowel_groups = 1
            syllables += vowel_groups

        # Calculate score
        words_per_sentence = words / sentences
        syllables_per_word = syllables / words

        return 206.835 - (1.015 * words_per_sentence) - (84.6 * syllables_per_word)

    def _calculate_flesch_kincaid_grade(self, text: str) -> float:
        """Calculate the Flesch-Kincaid Grade Level."""
        # Count sentences
        sentences = len(re.findall(r'[.!?]+', text))
        if sentences == 0:
            return 0

        # Count words
        words = len(re.findall(r'\b\w+\b', text))
        if words == 0:
            return 0

        # Count syllables (simplified)
        syllables = 0
        for word in re.findall(r'\b\w+\b', text.lower()):
            # Count vowel groups as syllables (simplified)
            vowel_groups = len(re.findall(r'[aeiouy]+', word))
            # Adjust for common patterns
            if word.endswith('e'):
                vowel_groups -= 1
            if vowel_groups <= 0:
                vowel_groups = 1
            syllables += vowel_groups

        # Calculate grade level
        words_per_sentence = words / sentences
        syllables_per_word = syllables / words

        return (0.39 * words_per_sentence) + (11.8 * syllables_per_word) - 15.59

    def _interpret_readability(self, score: float) -> str:
        """Interpret the Flesch Reading Ease score."""
        if score >= 90:
            return "Very Easy - 5th Grade"
        elif score >= 80:
            return "Easy - 6th Grade"
        elif score >= 70:
            return "Fairly Easy - 7th Grade"
        elif score >= 60:
            return "Standard - 8th-9th Grade"
        elif score >= 50:
            return "Fairly Difficult - 10th-12th Grade"
        elif score >= 30:
            return "Difficult - College Level"
        else:
            return "Very Difficult - College Graduate Level"

    def _identify_document_issues(self, document: str) -> List[Dict[str, Any]]:
        """Identify potential issues in the document."""
        issues = []

        # Check for very long sentences
        sentences = re.findall(r'[^.!?]+[.!?]', document)
        for i, sentence in enumerate(sentences):
            words = len(re.findall(r'\b\w+\b', sentence))
            if words > 30:
                issues.append({
                    "type": "long_sentence",
                    "severity": "medium",
                    "description": f"Sentence {i+1} is very long ({words} words)",
                    "suggestion": "Consider breaking this sentence into smaller ones for better readability"
                })

        # Check for passive voice (simplified)
        passive_voice = re.findall(r'\b(?:is|are|was|were|be|been|being)\s+\w+ed\b', document)
        if len(passive_voice) > 5:
            issues.append({
                "type": "passive_voice",
                "severity": "low",
                "description": f"Document contains {len(passive_voice)} instances of passive voice",
                "suggestion": "Consider using active voice for clearer, more direct writing"
            })

        # Check for repeated words
        words = re.findall(r'\b\w+\b', document.lower())
        word_counts = {}
        for word in words:
            if len(word) > 3:  # Ignore short words
                word_counts[word] = word_counts.get(word, 0) + 1

        for word, count in word_counts.items():
            if count > 10 and word not in ["this", "that", "with", "from", "have", "their", "about"]:
                issues.append({
                    "type": "word_repetition",
                    "severity": "low",
                    "description": f"The word '{word}' appears {count} times",
                    "suggestion": f"Consider using synonyms for '{word}' to improve variety"
                })

        return issues

    def _generate_improvement_suggestions(self, document: str, issues: List[Dict[str, Any]]) -> List[str]:
        """Generate improvement suggestions based on issues."""
        suggestions = []

        # Add issue-specific suggestions
        for issue in issues:
            suggestions.append(issue["suggestion"])

        # Add general suggestions based on document analysis
        flesch_score = self._calculate_flesch_reading_ease(document)
        if flesch_score < 50:
            suggestions.append("Consider simplifying language to improve readability")

        # Check document structure
        if not re.search(r'(?i)(?:introduction|overview)', document):
            suggestions.append("Add an introduction section to provide context")

        if not re.search(r'(?i)(?:conclusion|summary)', document):
            suggestions.append("Add a conclusion section to summarize key points")

        # Check for citations
        citations = self._extract_citations(document)
        if not citations:
            suggestions.append("Consider adding citations to support key claims")

        return suggestions
