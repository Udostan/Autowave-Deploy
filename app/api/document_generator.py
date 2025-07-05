"""
Designer Agent API

This module provides API endpoints for document generation, data analysis, and other design tasks.
"""

import logging
import re
import json
import random
import markdown
import time
import uuid
from datetime import datetime
from flask import Blueprint, request, jsonify
from app.mcp.tools.document_tools import DocumentTools
from app.mcp.tools.social_media_tools import SocialMediaTools
from app.mcp.tools.email_tools import EmailTools
from app.mcp.tools.seo_tools import SEOTools
from app.mcp.tools.learning_tools import LearningTools
from app.services.activity_logger import activity_logger

# Optional data analysis tools (requires numpy, pandas, matplotlib, seaborn)
try:
    from app.mcp.tools.data_analysis_tools import DataAnalysisTools
    DATA_ANALYSIS_AVAILABLE = True
except ImportError as e:
    print(f"⚠️  Data analysis tools not available: {e}")
    DataAnalysisTools = None
    DATA_ANALYSIS_AVAILABLE = False

# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Create blueprint
document_generator_bp = Blueprint('document_generator', __name__)

# Initialize tools
document_tools = DocumentTools()
data_analysis_tools = DataAnalysisTools() if DATA_ANALYSIS_AVAILABLE else None
social_media_tools = SocialMediaTools()
email_tools = EmailTools()
seo_tools = SEOTools()
learning_tools = LearningTools()

def is_data_analysis_request(content):
    """
    Determine if the content is requesting data analysis.

    Args:
        content: The user's prompt content

    Returns:
        bool: True if the content is requesting data analysis
    """
    # Log the content for debugging
    logger.info(f"Checking if content is a data analysis request: {content[:100]}...")

    content_lower = content.lower()

    # Check for data patterns in the content first - this is the strongest signal
    lines = content.split('\n')
    csv_line_count = 0
    for line in lines:
        if re.match(r'^[^,\t]+(?:[,\t][^,\t]+)+$', line.strip()):
            csv_line_count += 1

    if csv_line_count >= 2:  # At least header and one data row
        logger.info(f"CSV-like data pattern found: {csv_line_count} lines")
        return True

    # Data analysis keywords
    data_analysis_keywords = [
        'analyze data', 'data analysis', 'analyze dataset', 'visualize data',
        'create chart', 'create graph', 'plot data', 'data visualization',
        'create visualization', 'generate chart', 'generate graph', 'data insights',
        'correlation analysis', 'statistical analysis', 'analyze statistics',
        'create dashboard', 'data dashboard', 'analyze survey', 'analyze results',
        'create histogram', 'create bar chart', 'create pie chart', 'create scatter plot',
        'create line chart', 'create heatmap', 'create box plot', 'analyze this data'
    ]

    # Check for data analysis keywords
    for keyword in data_analysis_keywords:
        if keyword in content_lower:
            logger.info(f"Data analysis keyword found: {keyword}")
            return True

    # Check for CSV or tabular data in the content
    if ('csv' in content_lower or 'excel' in content_lower or
        'spreadsheet' in content_lower or 'dataset' in content_lower or
        'data set' in content_lower or 'table' in content_lower):
        logger.info("Data format indicator found (CSV, Excel, etc.)")
        return True

    # Check for data-like patterns in the content
    if re.search(r'\b\d+[.,]\d+[KMB]?\b', content) and re.search(r'%', content) and len(lines) > 3:
        logger.info("Found numeric data patterns with percentages")
        return True

    return False

def is_visual_presentation_request(content):
    """
    Determine if the content is requesting a visual presentation.

    Args:
        content: The user's prompt content

    Returns:
        bool: True if the content is requesting a visual presentation
    """
    # Log the content for debugging
    logger.info(f"Checking if content is a visual presentation request: {content[:100]}...")

    content_lower = content.lower()

    # Direct presentation indicators
    presentation_indicators = [
        'visual presentation', 'data visualization', 'presentation slides',
        'slide deck', 'powerpoint', 'presentation design', 'infographic',
        'data presentation', 'chart presentation', 'graph presentation',
        'visual analysis', 'data analysis presentation', 'statistical presentation',
        'financial presentation', 'sales presentation', 'marketing presentation',
        'business presentation', 'executive presentation', 'investor presentation'
    ]

    # Check for direct presentation indicators
    for indicator in presentation_indicators:
        if indicator in content_lower:
            logger.info(f"Direct presentation indicator found: {indicator}")
            return True

    # Presentation-specific elements
    presentation_elements = [
        'slides', 'charts', 'graphs', 'infographics', 'diagrams', 'data visualization',
        'statistics', 'metrics', 'kpis', 'quarterly results', 'annual report',
        'financial results', 'market analysis', 'competitor analysis', 'swot analysis',
        'product launch', 'executive summary', 'dashboard'
    ]

    # Count presentation elements
    element_count = 0
    for element in presentation_elements:
        if element in content_lower:
            element_count += 1

    # If multiple presentation elements are mentioned, it's likely a presentation request
    if element_count >= 2:
        logger.info(f"Presentation elements found: {element_count}")
        return True

    # Check for specific data visualization terms
    data_viz_terms = [
        'bar chart', 'line graph', 'pie chart', 'scatter plot', 'histogram',
        'heatmap', 'box plot', 'area chart', 'bubble chart', 'radar chart',
        'gantt chart', 'flowchart', 'org chart', 'tree map', 'funnel chart'
    ]

    # Count data visualization terms
    viz_count = 0
    for term in data_viz_terms:
        if term in content_lower:
            viz_count += 1

    # If multiple data visualization terms are mentioned, it's likely a presentation request
    if viz_count >= 1:
        logger.info(f"Data visualization terms found: {viz_count}")
        return True

    # If none of the above conditions are met, it's not a visual presentation request
    return False

def is_portfolio_request(content):
    """
    Determine if the content is requesting a portfolio.

    Args:
        content: The user's prompt content

    Returns:
        bool: True if the content is requesting a portfolio
    """
    # Log the content for debugging
    logger.info(f"Checking if content is a portfolio request: {content[:100]}...")

    content_lower = content.lower()

    # Direct portfolio indicators
    portfolio_indicators = [
        "portfolio website", "portfolio page", "portfolio site", "portfolio design",
        "professional portfolio", "creative portfolio", "design portfolio", "art portfolio",
        "photography portfolio", "developer portfolio", "artist portfolio", "work portfolio",
        "showcase portfolio", "personal portfolio", "project portfolio", "portfolio showcase"
    ]

    # Check for direct portfolio indicators
    for indicator in portfolio_indicators:
        if indicator in content_lower:
            logger.info(f"Direct portfolio indicator found: {indicator}")
            return True

    # Portfolio-specific professions
    portfolio_professions = [
        "photographer", "designer", "artist", "illustrator", "graphic designer",
        "web designer", "ux designer", "ui designer", "developer", "architect",
        "interior designer", "fashion designer", "model", "writer", "copywriter",
        "creative director", "art director", "filmmaker", "videographer"
    ]

    # Check for portfolio professions
    for profession in portfolio_professions:
        if profession in content_lower and "portfolio" in content_lower:
            logger.info(f"Portfolio profession found: {profession}")
            return True

    # Portfolio-specific elements
    portfolio_elements = [
        "gallery", "work samples", "projects", "case studies", "showcase",
        "portfolio pieces", "creative work", "design samples", "photography samples"
    ]

    # Count portfolio elements
    element_count = 0
    for element in portfolio_elements:
        if element in content_lower:
            element_count += 1

    # If multiple portfolio elements are mentioned, it's likely a portfolio request
    if element_count >= 1 and "portfolio" in content_lower:
        logger.info(f"Portfolio elements found: {element_count}")
        return True

    # If none of the above conditions are met, it's not a portfolio request
    return False

def is_social_media_request(content):
    """
    Determine if the content is requesting social media content generation.

    Args:
        content: The user's prompt content

    Returns:
        bool: True if the content is requesting social media content
    """
    # Log the content for debugging
    logger.info(f"Checking if content is a social media request: {content[:100]}...")
    logger.info("DEBUG: Checking social media request detection")

    content_lower = content.lower()

    # Direct social media indicators
    social_media_indicators = [
        "social media", "social post", "social content", "social campaign",
        "instagram post", "facebook post", "twitter post", "linkedin post",
        "tiktok", "instagram", "facebook", "twitter", "linkedin", "pinterest",
        "social media content", "social media campaign", "social media strategy",
        "social media calendar", "social media schedule", "social media plan",
        "hashtags", "posting schedule", "content calendar", "social content strategy"
    ]

    # Check for direct social media indicators
    for indicator in social_media_indicators:
        if indicator in content_lower:
            logger.info(f"Direct social media indicator found: {indicator}")
            return True

    # Social media action verbs
    social_media_verbs = [
        "post", "share", "tweet", "create content for", "generate content for",
        "write content for", "create posts for", "generate posts for", "write posts for"
    ]

    # Social media platforms
    platforms = ["instagram", "facebook", "twitter", "linkedin", "tiktok", "pinterest", "social media"]

    # Check for verb + platform combinations
    for verb in social_media_verbs:
        for platform in platforms:
            if f"{verb} {platform}" in content_lower:
                logger.info(f"Social media verb+platform found: {verb} {platform}")
                return True

    # Check for hashtag requests
    if "hashtag" in content_lower and ("recommend" in content_lower or "suggest" in content_lower or "generate" in content_lower):
        logger.info("Hashtag recommendation request found")
        return True

    # Check for content scheduling requests
    if "when to post" in content_lower or "best time to post" in content_lower or "posting schedule" in content_lower:
        logger.info("Social media scheduling request found")
        return True

    return False

def is_email_campaign_request(content):
    """
    Determine if the content is requesting an email campaign.

    Args:
        content: The user's prompt content

    Returns:
        bool: True if the content is requesting an email campaign
    """
    # Log the content for debugging
    logger.info(f"Checking if content is an email campaign request: {content[:100]}...")

    content_lower = content.lower()

    # Direct email campaign indicators
    email_campaign_indicators = [
        "email campaign", "email marketing", "email newsletter", "email blast",
        "marketing email", "promotional email", "email sequence", "email automation",
        "email template", "email subject line", "email content", "email strategy",
        "create email", "generate email", "write email", "design email",
        "email a/b test", "email testing", "email optimization"
    ]

    # Check for direct email campaign indicators
    for indicator in email_campaign_indicators:
        if indicator in content_lower:
            logger.info(f"Email campaign indicator found: {indicator}")
            return True

    # Email-specific terms
    email_terms = ["subject line", "email body", "unsubscribe", "open rate", "click rate", "newsletter"]
    email_term_count = sum(1 for term in email_terms if term in content_lower)

    if email_term_count >= 2:
        logger.info(f"Multiple email terms found: {email_term_count}")
        return True

    return False

def is_seo_optimization_request(content):
    """
    Determine if the content is requesting SEO optimization.

    Args:
        content: The user's prompt content

    Returns:
        bool: True if the content is requesting SEO optimization
    """
    # Log the content for debugging
    logger.info(f"Checking if content is an SEO optimization request: {content[:100]}...")

    content_lower = content.lower()

    # Direct SEO indicators
    seo_indicators = [
        "seo optimization", "seo optimize", "search engine optimization",
        "seo content", "seo analysis", "keyword optimization", "keyword research",
        "meta tags", "meta description", "search ranking", "google ranking",
        "optimize for seo", "seo friendly", "seo audit", "seo review",
        "readability score", "keyword density", "seo recommendations",
        "optimize this content", "optimize content", "seo", "keywords:"
    ]

    # Check for direct SEO indicators
    for indicator in seo_indicators:
        if indicator in content_lower:
            logger.info(f"SEO indicator found: {indicator}")
            return True

    # SEO-specific terms
    seo_terms = ["keywords", "meta", "ranking", "search engine", "readability", "optimization"]
    seo_term_count = sum(1 for term in seo_terms if term in content_lower)

    if seo_term_count >= 2:
        logger.info(f"Multiple SEO terms found: {seo_term_count}")
        return True

    return False

def is_learning_path_request(content):
    """
    Determine if the content is requesting a learning path.

    Args:
        content: The user's prompt content

    Returns:
        bool: True if the content is requesting a learning path
    """
    # Log the content for debugging
    logger.info(f"Checking if content is a learning path request: {content[:100]}...")

    content_lower = content.lower()

    # Direct learning path indicators
    learning_indicators = [
        "learning path", "learning plan", "study plan", "curriculum", "course outline",
        "learning roadmap", "study roadmap", "learning journey", "study guide",
        "training plan", "education plan", "skill development", "learning schedule",
        "create learning", "generate learning", "design curriculum", "study curriculum",
        "learning resources", "study resources", "learning materials"
    ]

    # Check for direct learning indicators
    for indicator in learning_indicators:
        if indicator in content_lower:
            logger.info(f"Learning path indicator found: {indicator}")
            return True

    # Learning-specific terms
    learning_terms = ["learn", "study", "course", "curriculum", "training", "education", "skill", "tutorial"]
    learning_term_count = sum(1 for term in learning_terms if term in content_lower)

    # Check for learning phrases
    learning_phrases = ["how to learn", "want to learn", "need to learn", "study", "master"]
    learning_phrase_count = sum(1 for phrase in learning_phrases if phrase in content_lower)

    if learning_term_count >= 2 or learning_phrase_count >= 1:
        logger.info(f"Learning terms found: {learning_term_count}, phrases: {learning_phrase_count}")
        return True

    return False

def is_document_request(content):
    """
    Determine if the content is requesting a standard document (not a webpage, portfolio, etc.).

    Args:
        content: The user's prompt content

    Returns:
        bool: True if the content is requesting a standard document
    """
    # Log the content for debugging
    logger.info(f"Checking if content is a document request: {content[:100]}...")

    content_lower = content.lower()

    # Document-specific keywords
    document_keywords = [
        'report', 'essay', 'paper', 'document', 'article', 'memo', 'letter',
        'proposal', 'business plan', 'research paper', 'thesis', 'dissertation',
        'case study', 'white paper', 'policy brief', 'executive summary',
        'business report', 'academic paper', 'technical report', 'literature review',
        'create a report', 'write a report', 'generate a report', 'create a document',
        'write a document', 'generate a document', 'create an essay', 'write an essay'
    ]

    # Check for document keywords
    for keyword in document_keywords:
        if keyword in content_lower:
            logger.info(f"Document keyword found: {keyword}")
            return True

    # If the content doesn't match any other specific type, it's likely a document
    if (not is_data_analysis_request(content) and
        not is_visual_presentation_request(content) and
        not is_portfolio_request(content) and
        not is_webpage_request(content) and
        not is_social_media_request(content)):
        logger.info("No specific content type detected, treating as document")
        return True

    return False

def extract_page_count_from_content(content):
    """
    Extract page count from the content if specified.

    Args:
        content: The user's prompt content

    Returns:
        int or None: The extracted page count, or None if not specified
    """
    # Look for explicit page count mentions
    page_patterns = [
        r'(\d+)[\s-]*page',
        r'(\d+)[\s-]*pages',
        r'create[\s\w]+(\d+)[\s-]*page',
        r'generate[\s\w]+(\d+)[\s-]*page',
        r'write[\s\w]+(\d+)[\s-]*page',
        r'produce[\s\w]+(\d+)[\s-]*page',
        r'about[\s\w]+(\d+)[\s-]*page',
        r'approximately[\s\w]+(\d+)[\s-]*page',
        r'around[\s\w]+(\d+)[\s-]*page'
    ]

    content_lower = content.lower()

    for pattern in page_patterns:
        match = re.search(pattern, content_lower)
        if match:
            try:
                page_count = int(match.group(1))
                logger.info(f"Extracted page count from content: {page_count}")
                return page_count
            except ValueError:
                continue

    # If no explicit page count found, return None
    return None

@document_generator_bp.route('/api/document/generate', methods=['POST'])
def generate_document():
    """
    Generate a document, webpage, portfolio, visual presentation, or perform data analysis based on the provided prompt.

    Returns:
        Response: JSON response with the generated content.
    """
    start_time = time.time()
    session_id = str(uuid.uuid4())

    # Get user_id from session for credit consumption
    from flask import session
    user_id = session.get('user_id', 'anonymous')

    try:
        data = request.get_json()

        # Extract content from the prompt
        content = data.get('content', '')
        page_count = data.get('page_count')

        # If page_count is not provided, try to extract it from the content
        if page_count is None:
            page_count = extract_page_count_from_content(content)
            logger.info(f"Extracted page count: {page_count}")

        if not content:
            # Log failed activity
            activity_logger.log_activity(
                user_id=user_id,
                agent_type='agent_wave',
                activity_type='document_generation',
                input_data={'content': content, 'page_count': page_count},
                output_data={'error': 'No content provided'},
                processing_time_ms=int((time.time() - start_time) * 1000),
                success=False,
                error_message='No content provided',
                session_id=session_id
            )
            return jsonify({
                'success': False,
                'error': 'No content provided'
            })

        # Initialize credit service for token-based consumption
        from ..services.credit_service import CreditService
        credit_service = CreditService()

        # Determine task type for minimum charge calculation
        if len(content) > 1000 or any(keyword in content.lower() for keyword in ['complex', 'comprehensive', 'detailed', 'advanced']):
            task_type = 'design_complex'
        else:
            task_type = 'design_basic'

        # Pre-consume minimum credits (will be adjusted after execution)
        pre_credit_result = credit_service.consume_credits(
            user_id=user_id,
            task_type=task_type,
            input_text=content,
            output_text="",  # Will update after execution
            use_token_based=True
        )

        if not pre_credit_result['success']:
            return jsonify({
                'success': False,
                'error': pre_credit_result.get('error', 'Insufficient credits'),
                'credits_needed': pre_credit_result.get('credits_needed'),
                'credits_available': pre_credit_result.get('credits_available')
            }), 402  # Payment Required

        # Log the request for debugging
        logger.info(f"Processing document generation request: {content[:100]}...")

        # FORCE DATA ANALYSIS CHECK FIRST - Look for CSV-like data patterns
        lines = content.split('\n')
        csv_line_count = 0
        for line in lines:
            if re.match(r'^[^,\t]+(?:[,\t][^,\t]+)+$', line.strip()):
                csv_line_count += 1

        if csv_line_count >= 2:  # At least header and one data row
            logger.info(f"CSV-like data pattern found: {csv_line_count} lines - FORCING data analysis")
            return handle_data_analysis_request(content)

        # Check for explicit data analysis keywords
        content_lower = content.lower()
        if content_lower.startswith("analyze this data") or content_lower.startswith("analyze data") or "data analysis" in content_lower:
            logger.info("Explicit data analysis request found - FORCING data analysis")
            return handle_data_analysis_request(content)

        # Check request types in a specific order to prioritize correctly

        # First check for data analysis - this has the most specific patterns
        if is_data_analysis_request(content):
            logger.info("Identified as data analysis request")
            return handle_data_analysis_request(content)

        # Then check for visual presentation - these are more specific than general webpages
        if is_visual_presentation_request(content):
            logger.info("Identified as visual presentation request")
            return handle_visual_presentation_request(content)

        # Then check for portfolio - these are more specific than general webpages
        if is_portfolio_request(content):
            logger.info("Identified as portfolio request")
            return handle_portfolio_request(content)

        # Check for social media content request
        if is_social_media_request(content):
            logger.info("Identified as social media content request")
            return handle_social_media_request(content)

        # Check for email campaign request
        if is_email_campaign_request(content):
            logger.info("Identified as email campaign request")
            return handle_email_campaign_request(content)

        # Check for SEO optimization request
        if is_seo_optimization_request(content):
            logger.info("Identified as SEO optimization request")
            return handle_seo_optimization_request(content)

        # Check for learning path request
        if is_learning_path_request(content):
            logger.info("Identified as learning path request")
            return handle_learning_path_request(content)

        # Then check for webpage - this is more specific than general documents
        if is_webpage_request(content):
            logger.info("Identified as webpage request")
            return handle_webpage_request(content)

        # Finally, if none of the above, it's a standard document
        logger.info("Identified as standard document request")

        # Extract document type from content
        document_type = 'report'  # Default
        title = 'Generated Document'
        citation_style = 'apa'
        include_references = True

        # Check for document type in content
        if 'report' in content.lower() or 'business report' in content.lower():
            document_type = 'report'
        elif 'essay' in content.lower() or 'academic essay' in content.lower():
            document_type = 'essay'
        elif 'legal' in content.lower() or 'contract' in content.lower() or 'agreement' in content.lower():
            document_type = 'legal'
        elif 'business' in content.lower() or 'proposal' in content.lower() or 'plan' in content.lower():
            document_type = 'business'
        elif 'academic' in content.lower() or 'research paper' in content.lower() or 'thesis' in content.lower():
            document_type = 'academic'
        elif 'letter' in content.lower() or 'cover letter' in content.lower() or 'recommendation' in content.lower():
            document_type = 'letter'

        # Check for citation style in content
        if 'apa' in content.lower():
            citation_style = 'apa'
        elif 'mla' in content.lower():
            citation_style = 'mla'
        elif 'chicago' in content.lower():
            citation_style = 'chicago'
        elif 'harvard' in content.lower():
            citation_style = 'harvard'
        elif 'ieee' in content.lower():
            citation_style = 'ieee'

        # Extract title from content if possible
        title_match = re.search(r'(?:title|about|on|for|about|regarding)\s*["\']?([^"\']+)["\']?', content, re.IGNORECASE)
        if title_match:
            title = title_match.group(1).strip()

        logger.info(f"Generating standard document of type: {document_type}, title: {title}")

        # Generate the document
        document_result = document_tools.generate_document(
            content=content,
            document_type=document_type,
            title=title,
            citation_style=citation_style,
            include_references=include_references,
            page_count=page_count
        )

        # Analyze the document
        analysis_result = document_tools.analyze_document(document_result['document'])

        # Format the document HTML
        document_html = format_document_html(document_result, analysis_result)

        # Ensure we have a valid PDF
        pdf_base64 = document_result.get('pdf_base64', '')

        # Log successful activity
        processing_time_ms = int((time.time() - start_time) * 1000)
        activity_logger.log_activity(
            user_id=user_id,
            agent_type='agent_wave',
            activity_type='document_generation',
            input_data={'content': content, 'page_count': page_count, 'document_type': document_type},
            output_data={'preview': document_result.get('preview', ''), 'has_pdf': bool(pdf_base64)},
            processing_time_ms=processing_time_ms,
            success=True,
            session_id=session_id
        )

        # Calculate final token-based credits after document generation
        if user_id and user_id != 'anonymous':
            try:
                # Get the generated content for token counting
                output_text = document_html
                execution_time = processing_time_ms / 60000  # Convert to minutes

                # Calculate actual credits consumed based on tokens
                final_credit_result = credit_service.calculate_token_based_credits(
                    input_text=content,
                    output_text=output_text,
                    task_type=task_type,
                    execution_time_minutes=execution_time,
                    tool_calls=1,  # Document generation counts as 1 tool call
                    image_count=0
                )

                # Add credit breakdown to response
                response_data = {
                    'success': True,
                    'document_html': document_html,
                    'pdf_base64': pdf_base64,
                    'preview': document_result.get('preview', ''),
                    'session_id': session_id,
                    'credits_consumed': pre_credit_result['credits_consumed'],
                    'credit_breakdown': final_credit_result
                }
                return jsonify(response_data)
            except Exception as e:
                logger.error(f"Error calculating final credits: {e}")

        return jsonify({
            'success': True,
            'document_html': document_html,
            'pdf_base64': pdf_base64,
            'preview': document_result.get('preview', ''),
            'session_id': session_id
        })
    except Exception as e:
        logger.error(f"Error generating document: {str(e)}")

        # Log failed activity
        processing_time_ms = int((time.time() - start_time) * 1000)
        activity_logger.log_activity(
            user_id=user_id,
            agent_type='agent_wave',
            activity_type='document_generation',
            input_data={'content': content, 'page_count': page_count},
            output_data={'error': str(e)},
            processing_time_ms=processing_time_ms,
            success=False,
            error_message=str(e),
            session_id=session_id
        )

        return jsonify({
            'success': False,
            'error': str(e)
        })

def is_webpage_request(content):
    """
    ARCHIVED: Webpage detection disabled - use Code Wave for webpage creation.

    This function has been archived because Code Wave now handles webpage design.
    All webpage requests should be directed to Code Wave instead.

    Args:
        content: The user's prompt content

    Returns:
        bool: Always returns False (webpage detection disabled)
    """
    # Webpage functionality archived - always return False
    logger.info("Webpage detection disabled - use Code Wave for webpage creation")
    return False

# ARCHIVED WEBPAGE DETECTION LOGIC (for reference only):
# Original function disabled to redirect webpage requests to Code Wave
# def is_webpage_request_ARCHIVED(content):
#     content_lower = content.lower()
#     # Direct webpage indicators
#     direct_indicators = ["website", "webpage", "web page", "landing page", "site", "homepage", "web design"]
#     # Website creation phrases
#     website_phrases = ["create a website", "design a website", "build a website", "make a website", "develop a website", "create a webpage", "design a webpage", "build a webpage", "create a web page"]
#     # Website types
#     website_types = ["travel website", "business website", "corporate website", "agency website", "personal website", "blog website", "e-commerce website", "online store website", "company website"]
#     # ... rest of archived detection logic

def handle_webpage_request(content):
    """
    ARCHIVED: Webpage generation disabled - use Code Wave for webpage creation.

    This function has been archived because Code Wave now handles webpage design.
    All webpage requests should be directed to Code Wave instead.

    Args:
        content: The user's prompt content

    Returns:
        Response: JSON response directing user to Code Wave
    """
    logger.info("Webpage generation disabled - redirecting to Code Wave")
    return jsonify({
        'success': False,
        'error': 'Webpage generation has been moved to Code Wave. Please use Code Wave for creating websites and webpages.',
        'redirect_to': 'code-wave'
    })

# ARCHIVED WEBPAGE GENERATION LOGIC (for reference only):
# Original function disabled to redirect webpage requests to Code Wave
# def handle_webpage_request_ARCHIVED(content):
#     # Extract title, format HTML, return webpage
#     # ... rest of archived generation logic

def handle_portfolio_request(content):
    """
    Handle a portfolio generation request.

    Args:
        content: The user's prompt content

    Returns:
        Response: JSON response with the portfolio HTML
    """
    try:
        # Log that we're handling a portfolio request
        logger.info(f"Handling portfolio request: {content[:100]}...")

        # Extract name from content if possible
        name_match = re.search(r'(?:for|by|of)\s+([A-Z][a-z]+\s+[A-Z][a-z]+)', content)

        # Extract profession from content
        profession_match = re.search(r'(?:photographer|designer|artist|illustrator|graphic designer|web designer|ux designer|ui designer|developer|architect|interior designer|fashion designer|model|writer|copywriter|creative director|art director|filmmaker|videographer)', content.lower())

        # Use the extracted name or a default
        if name_match:
            name = name_match.group(1).strip()
        else:
            name = "Alex Morgan"

        # Use the extracted profession or a default
        if profession_match:
            profession = profession_match.group(0).strip()
            profession = profession[0].upper() + profession[1:]  # Capitalize first letter
        else:
            profession = "Professional"

        title = f"{name}'s {profession} Portfolio"

        # Format the portfolio HTML using the format_webpage_html function with content_type='portfolio'
        portfolio_html = format_webpage_html(content, title, content_type='portfolio')

        logger.info(f"Successfully generated portfolio HTML for: {title}")

        return jsonify({
            'success': True,
            'document_html': portfolio_html,
            'is_portfolio': True,
            'preview': f"Portfolio: {title}"
        })
    except Exception as e:
        logger.error(f"Error handling portfolio request: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        })

def handle_visual_presentation_request(content):
    """
    Handle a visual presentation generation request.

    Args:
        content: The user's prompt content

    Returns:
        Response: JSON response with the visual presentation HTML
    """
    try:
        # Log that we're handling a visual presentation request
        logger.info(f"Handling visual presentation request: {content[:100]}...")

        # Extract title from content if possible
        title_match = re.search(r'(?:titled|title[d]?|named|called|about|for|on)\s*["\']?([^"\']+)["\']?', content, re.IGNORECASE)

        # Extract subject matter
        subject_matches = [
            re.search(r'(?:climate change|global warming|environment|sustainability)', content.lower()),
            re.search(r'(?:financial|finance|quarterly|annual|results|performance|revenue|profit)', content.lower()),
            re.search(r'(?:product launch|marketing|strategy|campaign|sales|market analysis)', content.lower()),
            re.search(r'(?:data|statistics|metrics|analysis|research|study|survey)', content.lower())
        ]

        # Use the extracted title or subject, or a default
        if title_match:
            title = title_match.group(1).strip()
        else:
            # Try to use a subject match
            for match in subject_matches:
                if match:
                    subject = match.group(0).strip()
                    title = f"{subject.capitalize()} Analysis"
                    break
            else:
                # If no subject match, use a default
                title = "Data Visualization"

        # Format the visual presentation HTML using the format_webpage_html function with content_type='presentation'
        presentation_html = format_webpage_html(content, title, content_type='presentation')

        logger.info(f"Successfully generated visual presentation HTML for: {title}")

        return jsonify({
            'success': True,
            'document_html': presentation_html,
            'is_presentation': True,
            'preview': f"Presentation: {title}"
        })
    except Exception as e:
        logger.error(f"Error handling visual presentation request: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        })

def handle_data_analysis_request(content):
    """
    Handle a data analysis request.

    Args:
        content: The user's prompt content

    Returns:
        Response: JSON response with the analysis results
    """
    try:
        # Log that we're handling a data analysis request
        logger.info(f"Handling data analysis request: {content[:100]}...")

        # Extract data from the content if possible
        data = extract_data_from_content(content)

        # Determine analysis type
        analysis_type = determine_analysis_type(content)

        # Determine chart type
        chart_type = determine_chart_type(content)

        # Extract title
        title = extract_title_from_content(content) or "Data Analysis"

        # If no data was found in the content, generate a sample dataset
        if not data:
            data = generate_sample_data(content)

        # Check if data analysis tools are available
        if not DATA_ANALYSIS_AVAILABLE or data_analysis_tools is None:
            return jsonify({
                'success': False,
                'error': 'Data analysis tools are not available. Please install required dependencies: numpy, pandas, matplotlib, seaborn'
            }), 500

        # Perform the analysis
        analysis_result = data_analysis_tools.analyze_data(
            data=data,
            analysis_type=analysis_type,
            chart_type=chart_type,
            title=title
        )

        # Format the analysis HTML
        analysis_html = format_analysis_html(analysis_result)

        logger.info(f"Successfully generated data analysis HTML for: {title}")

        return jsonify({
            'success': True,
            'document_html': analysis_html,
            'is_data_analysis': True,
            'preview': analysis_result.get('summary', '')
        })
    except Exception as e:
        logger.error(f"Error handling data analysis request: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        })

def extract_data_from_content(content):
    """
    Extract data from the content if possible.

    Args:
        content: The user's prompt content

    Returns:
        dict or str: Extracted data or empty string if no data found
    """
    # Look for CSV-like data in the content
    lines = content.split('\n')
    csv_lines = []

    # Find consecutive lines that look like CSV data
    in_csv_block = False
    for line in lines:
        # Check if line has comma-separated values or tab-separated values
        if re.match(r'^[^,\t]+(?:[,\t][^,\t]+)+$', line.strip()):
            csv_lines.append(line.strip())
            in_csv_block = True
        elif in_csv_block and line.strip() == '':
            # Empty line might be part of CSV data
            continue
        elif in_csv_block:
            # End of CSV block
            in_csv_block = False

    if len(csv_lines) >= 2:  # At least header and one data row
        return '\n'.join(csv_lines)

    # Look for JSON-like data in the content
    json_match = re.search(r'(\{.*\}|\[.*\])', content, re.DOTALL)
    if json_match:
        try:
            json_data = json.loads(json_match.group(0))
            return json_data
        except:
            pass

    return ""

def determine_analysis_type(content):
    """
    Determine the type of analysis to perform based on the content.

    Args:
        content: The user's prompt content

    Returns:
        str: Analysis type
    """
    content_lower = content.lower()

    if 'correlation' in content_lower or 'relationship' in content_lower:
        return 'correlation'
    elif 'distribution' in content_lower or 'histogram' in content_lower:
        return 'distribution'
    elif 'group' in content_lower or 'compare groups' in content_lower:
        return 'group_analysis'
    else:
        return 'summary'  # Default

def determine_chart_type(content):
    """
    Determine the type of chart to generate based on the content.

    Args:
        content: The user's prompt content

    Returns:
        str: Chart type
    """
    content_lower = content.lower()

    if 'bar chart' in content_lower or 'bar graph' in content_lower:
        return 'bar'
    elif 'line chart' in content_lower or 'line graph' in content_lower:
        return 'line'
    elif 'scatter' in content_lower or 'scatter plot' in content_lower:
        return 'scatter'
    elif 'histogram' in content_lower:
        return 'histogram'
    elif 'pie chart' in content_lower or 'pie graph' in content_lower:
        return 'pie'
    elif 'heatmap' in content_lower:
        return 'heatmap'
    elif 'box plot' in content_lower or 'box and whisker' in content_lower:
        return 'box'
    elif 'correlation' in content_lower or 'matrix' in content_lower:
        return 'correlation'
    else:
        return 'bar'  # Default

def extract_title_from_content(content):
    """
    Extract a title from the content.

    Args:
        content: The user's prompt content

    Returns:
        str: Extracted title or None if no title found
    """
    # Try to extract title from phrases like "Create a chart titled X" or "Generate a graph of X"
    title_patterns = [
        r'(?:titled|title[d]?|named|called)\s*["\']?([^"\']+)["\']?',
        r'(?:chart|graph|plot|visualization|analysis) (?:of|for|about|on)\s*["\']?([^"\']+)["\']?',
        r'(?:analyze|visualize|plot)\s*["\']?([^"\']+)["\']?'
    ]

    for pattern in title_patterns:
        match = re.search(pattern, content, re.IGNORECASE)
        if match:
            return match.group(1).strip()

    return None

def generate_sample_data(content):
    """
    Generate a sample dataset based on the content.

    Args:
        content: The user's prompt content

    Returns:
        dict: Sample data
    """
    content_lower = content.lower()

    # Check for specific data types in the content
    if 'sales' in content_lower or 'revenue' in content_lower or 'business' in content_lower:
        return {
            'date': ['2023-01', '2023-02', '2023-03', '2023-04', '2023-05', '2023-06'],
            'sales': [12500, 13200, 15100, 14300, 16700, 18200],
            'expenses': [8700, 8900, 9200, 9100, 9500, 10100],
            'profit': [3800, 4300, 5900, 5200, 7200, 8100],
            'category': ['Electronics', 'Clothing', 'Electronics', 'Home', 'Clothing', 'Electronics']
        }
    elif 'weather' in content_lower or 'temperature' in content_lower or 'climate' in content_lower:
        return {
            'month': ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'],
            'temperature': [32, 35, 42, 53, 62, 72, 78, 76, 68, 55, 45, 36],
            'precipitation': [3.2, 2.8, 3.1, 3.6, 3.9, 3.5, 3.2, 3.0, 3.3, 3.4, 3.5, 3.6],
            'humidity': [65, 62, 63, 66, 70, 72, 75, 74, 71, 68, 67, 66]
        }
    elif 'population' in content_lower or 'demographic' in content_lower:
        return {
            'age_group': ['0-10', '11-20', '21-30', '31-40', '41-50', '51-60', '61-70', '71-80', '81+'],
            'population': [12.5, 13.2, 15.1, 14.3, 12.7, 10.2, 8.5, 5.2, 2.1],
            'growth_rate': [1.2, 1.1, 0.9, 0.7, 0.3, -0.1, -0.4, -0.8, -1.2],
            'gender_ratio': [1.05, 1.03, 1.01, 0.99, 0.97, 0.95, 0.9, 0.85, 0.75]
        }
    else:
        # Generic sample data
        return {
            'category': ['A', 'B', 'C', 'D', 'E', 'F'],
            'value1': [25, 40, 30, 50, 45, 60],
            'value2': [15, 30, 35, 40, 50, 45],
            'value3': [35, 25, 45, 30, 20, 40]
        }

def handle_social_media_request(content):
    """
    Handle a social media content generation request.

    Args:
        content: The user's prompt content

    Returns:
        Response: JSON response with the social media content
    """
    try:
        # Log that we're handling a social media request
        logger.info(f"Handling social media request: {content[:100]}...")
        logger.info("DEBUG: Starting social media content generation")

        # Extract topic from content
        topic = extract_topic_from_content(content)

        # Extract platforms from content
        platforms = extract_platforms_from_content(content)

        # Extract tone from content
        tone = extract_tone_from_content(content)

        # Determine if hashtags should be included
        include_hashtags = "no hashtag" not in content.lower() and "without hashtag" not in content.lower()

        # Determine if schedule should be included
        include_schedule = "no schedule" not in content.lower() and "without schedule" not in content.lower()

        # Generate social media content
        social_media_result = social_media_tools.generate_content(
            topic=topic,
            platforms=platforms,
            tone=tone,
            include_hashtags=include_hashtags,
            include_schedule=include_schedule
        )

        # Format the social media content HTML
        social_media_html = format_social_media_html(social_media_result)

        logger.info(f"Successfully generated social media content for: {topic}")

        return jsonify({
            'success': True,
            'document_html': social_media_html,
            'is_social_media': True,
            'preview': f"Social Media Content: {topic}"
        })
    except Exception as e:
        logger.error(f"Error handling social media request: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        })

def extract_topic_from_content(content):
    """
    Extract the main topic from the content.

    Args:
        content: The user's prompt content

    Returns:
        str: The extracted topic
    """
    content_lower = content.lower()

    # Try to extract topic from phrases like "Create social media posts about X" or "Generate content for X"
    topic_patterns = [
        r'(?:about|for|on|regarding|related to|focusing on|centered on)\s+([^.,;!?]+)',
        r'(?:create|generate|write|make|produce)\s+(?:content|posts|social media posts|social media content)\s+(?:about|for|on|regarding)\s+([^.,;!?]+)',
        r'(?:content|posts|social media posts|social media content)\s+(?:about|for|on|regarding)\s+([^.,;!?]+)'
    ]

    for pattern in topic_patterns:
        match = re.search(pattern, content_lower)
        if match:
            topic = match.group(1).strip()
            # Remove any platform names from the topic
            platforms = ["instagram", "facebook", "twitter", "linkedin", "tiktok", "pinterest", "social media"]
            for platform in platforms:
                topic = topic.replace(platform, "").strip()
            return topic

    # If no topic found, use a generic one
    return "our brand"

def extract_platforms_from_content(content):
    """
    Extract the platforms from the content.

    Args:
        content: The user's prompt content

    Returns:
        list: The extracted platforms
    """
    content_lower = content.lower()

    platforms = []

    # Check for specific platforms
    if "instagram" in content_lower:
        platforms.append("instagram")
    if "facebook" in content_lower:
        platforms.append("facebook")
    if "twitter" in content_lower:
        platforms.append("twitter")
    if "linkedin" in content_lower:
        platforms.append("linkedin")
    if "tiktok" in content_lower:
        platforms.append("tiktok")

    # If no specific platforms found, return None (will use defaults)
    return platforms if platforms else None

def extract_tone_from_content(content):
    """
    Extract the tone from the content.

    Args:
        content: The user's prompt content

    Returns:
        str: The extracted tone or None if not specified
    """
    content_lower = content.lower()

    # Try to extract tone from phrases like "with a professional tone" or "in a casual tone"
    tone_patterns = [
        r'(?:with|in|using|having)\s+(?:a|an)\s+([a-z]+)\s+tone',
        r'tone\s+(?:should be|being|is)\s+([a-z]+)',
        r'([a-z]+)\s+tone'
    ]

    for pattern in tone_patterns:
        match = re.search(pattern, content_lower)
        if match:
            tone = match.group(1).strip()
            # Check if it's a valid tone
            valid_tones = ["professional", "casual", "formal", "informal", "friendly", "serious",
                          "humorous", "inspirational", "motivational", "educational", "promotional"]
            if tone in valid_tones:
                return tone

    # If no valid tone found, return None (will use defaults)
    return None

def format_social_media_html(social_media_result):
    """
    Format the social media content as HTML with Tailwind CSS.

    Args:
        social_media_result: The social media content generation result

    Returns:
        str: HTML representation of the social media content with Tailwind CSS
    """
    # Get data from the social media result
    topic = social_media_result.get('topic', 'Social Media Content')
    content_by_platform = social_media_result.get('content', {})
    schedule = social_media_result.get('schedule', {})

    # Generate a random accent color for the social media content
    accent_colors = ['primary', 'blue', 'indigo', 'purple', 'pink', 'rose', 'orange', 'amber', 'emerald', 'teal', 'cyan']
    accent_color = random.choice(accent_colors)

    # Platform icons and colors
    platform_info = {
        'twitter': {
            'icon': '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 4s-.7 2.1-2 3.4c1.6 10-9.4 17.3-18 11.6 2.2.1 4.4-.6 6-2C3 15.5.5 9.6 3 5c2.2 2.6 5.6 4.1 9 4-.9-4.2 4-6.6 7-3.8 1.1 0 3-1.2 3-1.2z"></path></svg>',
            'color': 'blue'
        },
        'linkedin': {
            'icon': '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M16 8a6 6 0 0 1 6 6v7h-4v-7a2 2 0 0 0-2-2 2 2 0 0 0-2 2v7h-4v-7a6 6 0 0 1 6-6z"></path><rect x="2" y="9" width="4" height="12"></rect><circle cx="4" cy="4" r="2"></circle></svg>',
            'color': 'blue'
        },
        'instagram': {
            'icon': '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="2" y="2" width="20" height="20" rx="5" ry="5"></rect><path d="M16 11.37A4 4 0 1 1 12.63 8 4 4 0 0 1 16 11.37z"></path><line x1="17.5" y1="6.5" x2="17.51" y2="6.5"></line></svg>',
            'color': 'pink'
        },
        'facebook': {
            'icon': '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M18 2h-3a5 5 0 0 0-5 5v3H7v4h3v8h4v-8h3l1-4h-4V7a1 1 0 0 1 1-1h3z"></path></svg>',
            'color': 'blue'
        },
        'tiktok': {
            'icon': '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M9 12a4 4 0 1 0 0 8 4 4 0 0 0 0-8z"></path><path d="M16 8v8"></path><path d="M12 16v-8"></path><path d="M20 12V8a4 4 0 0 0-4-4h-4"></path></svg>',
            'color': 'purple'
        }
    }

    # Create a Tailwind CSS styled HTML structure for the social media content
    html = f"""
    <div class="bg-dark-600 rounded-lg shadow-lg overflow-hidden transition-all duration-300 hover:shadow-xl">
        <div class="flex items-center justify-between p-5 border-b border-dark-500">
            <h2 class="text-2xl font-bold text-dark-100">Social Media Content: {topic}</h2>
            <span class="bg-{accent_color}-600 text-white px-3 py-1 rounded-full text-sm font-medium">Social Media</span>
        </div>

        <div class="p-5 space-y-6">
    """

    # Add content for each platform
    for platform, content_data in content_by_platform.items():
        platform_display = platform.capitalize()
        platform_icon = platform_info.get(platform, {'icon': '', 'color': accent_color}).get('icon')
        platform_color = platform_info.get(platform, {'icon': '', 'color': accent_color}).get('color')

        content_text = content_data.get('content', '')
        hashtags = content_data.get('hashtags', [])
        character_count = content_data.get('character_count', 0)

        html += f"""
            <div class="bg-dark-500 rounded-lg p-5 shadow-inner overflow-hidden transition-all duration-300 hover:shadow-md">
                <div class="flex items-center mb-3">
                    <div class="bg-{platform_color}-600 p-2 rounded-full mr-3">
                        {platform_icon}
                    </div>
                    <h3 class="text-xl font-bold text-dark-100">{platform_display}</h3>
                    <span class="ml-auto text-dark-200 text-sm">{character_count} characters</span>
                </div>

                <div class="bg-dark-600 rounded-lg p-4 mb-3 border border-dark-400">
                    <p class="text-dark-100 whitespace-pre-wrap">{content_text}</p>
                </div>
        """

        # Add hashtags if available
        if hashtags:
            html += f"""
                <div class="flex flex-wrap gap-2 mb-3">
            """

            for hashtag in hashtags:
                html += f"""
                    <span class="bg-{platform_color}-900 text-{platform_color}-100 px-2 py-1 rounded text-sm">{hashtag}</span>
                """

            html += f"""
                </div>
            """

        html += f"""
            </div>
        """

    # Add posting schedule if available
    if schedule:
        html += f"""
            <div class="bg-dark-500 rounded-lg p-5 shadow-inner">
                <h3 class="text-xl font-bold text-dark-100 mb-3">Recommended Posting Schedule</h3>
                <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        """

        for platform, schedule_data in schedule.items():
            platform_display = platform.capitalize()
            platform_icon = platform_info.get(platform, {'icon': '', 'color': accent_color}).get('icon')
            platform_color = platform_info.get(platform, {'icon': '', 'color': accent_color}).get('color')

            html += f"""
                <div class="bg-dark-600 rounded-lg p-4 border border-dark-400">
                    <div class="flex items-center mb-2">
                        <div class="bg-{platform_color}-600 p-1 rounded-full mr-2">
                            {platform_icon}
                        </div>
                        <h4 class="font-bold text-dark-100">{platform_display}</h4>
                    </div>
                    <ul class="space-y-2">
            """

            for post_time in schedule_data:
                day = post_time.get('day', '')
                time = post_time.get('time', '')

                html += f"""
                    <li class="text-dark-200 text-sm flex items-center">
                        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="mr-2"><circle cx="12" cy="12" r="10"></circle><polyline points="12 6 12 12 16 14"></polyline></svg>
                        {day}, {time}
                    </li>
                """

            html += f"""
                    </ul>
                </div>
            """

        html += f"""
                </div>
            </div>
        """

    # Close the main container
    html += f"""
        </div>
    </div>
    """

    return html

def format_analysis_html(analysis_result):
    """
    Format the analysis results as HTML with Tailwind CSS.

    Args:
        analysis_result: The analysis results

    Returns:
        str: HTML representation of the analysis with Tailwind CSS
    """
    # Get data from the analysis result
    title = analysis_result.get('title', 'Data Analysis')
    summary = analysis_result.get('summary', '')
    visualizations = analysis_result.get('visualizations', {})
    image_data = visualizations.get('image', '')

    # Log what we're formatting
    logger.info(f"Formatting data analysis HTML for: {title}")

    # Process the summary to properly format Markdown
    # Replace Markdown headings with HTML headings
    processed_summary = summary
    processed_summary = processed_summary.replace('## ', '<h2 class="text-xl font-bold text-dark-100 mt-6 mb-3">').replace('\n## ', '\n<h2 class="text-xl font-bold text-dark-100 mt-6 mb-3">')
    processed_summary = processed_summary.replace('### ', '<h3 class="text-lg font-bold text-dark-100 mt-5 mb-2">').replace('\n### ', '\n<h3 class="text-lg font-bold text-dark-100 mt-5 mb-2">')

    # Close heading tags
    lines = processed_summary.split('\n')
    for i, line in enumerate(lines):
        if line.startswith('<h2 class='):
            lines[i] = line + '</h2>'
        elif line.startswith('<h3 class='):
            lines[i] = line + '</h3>'

    # Replace bold text
    processed_text = '\n'.join(lines)
    processed_text = processed_text.replace('**', '<strong class="font-bold">', 1)
    while '**' in processed_text:
        processed_text = processed_text.replace('**', '</strong>', 1)
        if '**' in processed_text:
            processed_text = processed_text.replace('**', '<strong class="font-bold">', 1)

    # Replace line breaks with <br> tags
    processed_text = processed_text.replace('\n', '<br>')

    # Generate a random accent color for the analysis
    accent_colors = ['primary', 'blue', 'indigo', 'purple', 'pink', 'rose', 'orange', 'amber', 'emerald', 'teal', 'cyan']
    accent_color = random.choice(accent_colors)

    # Create a Tailwind CSS styled HTML structure for the analysis
    html = f"""
    <div class="bg-dark-600 rounded-lg shadow-lg overflow-hidden transition-all duration-300 hover:shadow-xl">
        <div class="flex items-center justify-between p-5 border-b border-dark-500">
            <h2 class="text-2xl font-bold text-dark-100">{title}</h2>
            <span class="bg-{accent_color}-600 text-white px-3 py-1 rounded-full text-sm font-medium">Data Analysis</span>
        </div>

        <div class="p-5">
            <div class="bg-dark-500 rounded-lg p-5 mb-5 shadow-inner overflow-hidden transition-all duration-300 hover:shadow-md">
                <img src="data:image/png;base64,{image_data}" alt="Data Visualization" class="max-w-full h-auto rounded mx-auto transition-transform duration-300 hover:scale-105">
            </div>

            <div class="bg-dark-500 rounded-lg p-5 shadow-inner">
                <div class="text-dark-100 leading-relaxed space-y-4">
                    {processed_text}
                </div>
            </div>
        </div>
    </div>
    """

    # Return the HTML without any JavaScript (we don't need it for data analysis)
    return html

def format_document_html(document_result, _):
    """
    Format the document and analysis results as HTML with Tailwind CSS.
    Creates A4-sized pages for a PDF-like experience.

    Args:
        document_result: The document generation result
        analysis_result: The document analysis result

    Returns:
        str: HTML representation of the document and analysis with Tailwind CSS
    """
    document = document_result['document']
    title = document_result['title']
    doc_type = document_result['type'].capitalize()
    current_date = datetime.now().strftime("%B %d, %Y")

    # Convert Markdown to HTML
    document_html = markdown.markdown(document, extensions=['extra'])

    # Remove the first heading (with lowercase letters) from the document
    # First convert to HTML
    document_html = markdown.markdown(document, extensions=['extra'])

    # Remove the first h1 heading if it starts with lowercase
    document_html = re.sub(r'<h1>([a-z].*?)</h1>', '', document_html, count=1)

    # Process document HTML to add Tailwind classes
    # Add classes to headings with black text color for better visibility on white background
    document_html = re.sub(r'<h1>(.*?)</h1>', r'<h1 class="text-3xl font-bold mt-8 mb-4 text-black">\1</h1>', document_html)
    document_html = re.sub(r'<h2>(.*?)</h2>', r'<h2 class="text-2xl font-bold mt-6 mb-3 text-black">\1</h2>', document_html)
    document_html = re.sub(r'<h3>(.*?)</h3>', r'<h3 class="text-xl font-bold mt-5 mb-2 text-black">\1</h3>', document_html)

    # Add classes to paragraphs with dark text for better readability
    document_html = re.sub(r'<p>(.*?)</p>', r'<p class="mb-4 leading-relaxed text-gray-900">\1</p>', document_html)

    # Add classes to lists with dark text
    document_html = re.sub(r'<ul>', r'<ul class="list-disc pl-6 mb-4 space-y-2 text-gray-900">', document_html)
    document_html = re.sub(r'<ol>', r'<ol class="list-decimal pl-6 mb-4 space-y-2 text-gray-900">', document_html)
    document_html = re.sub(r'<li>', r'<li class="mb-1">', document_html)

    # Split content into pages (approximately 1000 characters per page)
    # This is a simple approach - a more sophisticated approach would consider actual page breaks
    content_parts = []

    # First, try to split at major section headings (h1, h2)
    sections = re.split(r'(<h1.*?</h1>|<h2.*?</h2>)', document_html)

    current_page = ""
    page_count = 1

    # Process sections to create pages
    for i, section in enumerate(sections):
        # If this is a heading, we'll use it to start a new page if the current page is getting full
        if re.match(r'<h1.*?</h1>|<h2.*?</h2>', section):
            # If current page is already substantial, start a new page
            if len(current_page) > 2000:  # Approximate size for a page
                content_parts.append(current_page)
                current_page = section
                page_count += 1
            else:
                # Otherwise add the heading to the current page
                current_page += section
        else:
            # For content sections, check if adding would make the page too long
            if len(current_page) + len(section) > 3000:  # Approximate max size for a page
                # If the section itself is very long, we need to split it further
                if len(section) > 3000:
                    # Add what we have so far as a page
                    content_parts.append(current_page)

                    # Split the long section into multiple pages
                    paragraphs = re.split(r'(<p.*?</p>|<ul.*?</ul>|<ol.*?</ol>)', section)
                    sub_page = ""

                    for paragraph in paragraphs:
                        if len(sub_page) + len(paragraph) > 3000:
                            content_parts.append(sub_page)
                            sub_page = paragraph
                            page_count += 1
                        else:
                            sub_page += paragraph

                    # Add any remaining content as the start of the next page
                    current_page = sub_page if sub_page else ""
                else:
                    # Add current page and start a new one with this section
                    content_parts.append(current_page)
                    current_page = section
                    page_count += 1
            else:
                # Add to current page
                current_page += section

    # Add the last page if it has content
    if current_page:
        content_parts.append(current_page)

    # Create A4 pages with the content
    pages_html = ""
    for i, content in enumerate(content_parts):
        page_num = i + 1
        pages_html += f"""
        <div class="document-page dark-theme" data-page="{page_num}">
            <div class="page-header">{title} - {current_date}</div>
            {content}
            <div class="page-footer">Page {page_num} of {len(content_parts)}</div>
        </div>
        """

    # If no pages were created (very short document), create a single page
    if not pages_html:
        pages_html = f"""
        <div class="document-page dark-theme" data-page="1">
            <div class="page-header">{title} - {current_date}</div>
            {document_html}
            <div class="page-footer">Page 1 of 1</div>
        </div>
        """

    # Create HTML with proper document structure using Tailwind CSS
    html = f"""
    <div class="bg-dark-600 rounded-lg shadow-lg overflow-hidden transition-all duration-300 hover:shadow-xl">
        <div class="flex items-center justify-between p-5 border-b border-dark-500">
            <h2 class="text-2xl font-bold text-dark-100">{title}</h2>
            <div class="flex items-center space-x-3">
                <span class="bg-primary-600 text-white px-3 py-1 rounded-full text-sm font-medium">{doc_type}</span>
                <button id="downloadButton" class="text-primary-400 hover:text-primary-300 transition-colors duration-200" title="Download document" onclick="downloadDocument()">
                    <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="animate-bounce-slow">
                        <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
                        <polyline points="7 10 12 15 17 10"></polyline>
                        <line x1="12" y1="15" x2="12" y2="3"></line>
                    </svg>
                </button>
            </div>
        </div>
        <div class="p-5 bg-dark-600 document-content">
            {pages_html}
        </div>
    </div>
    """

    # Add JavaScript for download functionality with Tailwind styling
    js_script = """
    <script>
        function downloadDocument() {
            // Create a blob from the document content
            const content = document.querySelector('.document-content').innerHTML;
            const title = document.querySelector('.text-2xl.font-bold').textContent;
            const docType = document.querySelector('.bg-primary-600').textContent;

            // Create a dropdown menu for format selection
            const formats = [
                { name: 'PDF', ext: 'pdf', mime: 'application/pdf' },
                { name: 'Word', ext: 'docx', mime: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' },
                { name: 'HTML', ext: 'html', mime: 'text/html' },
                { name: 'Text', ext: 'txt', mime: 'text/plain' }
            ];

            const menu = document.createElement('div');
            menu.className = 'absolute right-5 top-16 bg-dark-600 border border-dark-500 rounded-md py-2 z-50 shadow-lg';

            formats.forEach(format => {
                const option = document.createElement('div');
                option.className = 'px-4 py-2 hover:bg-dark-500 cursor-pointer text-dark-100 transition-colors duration-200';
                option.textContent = format.name;

                option.addEventListener('click', () => {
                    // For now, we'll just simulate the download
                    const filename = title.replace(/[^a-z0-9]/gi, '_').toLowerCase() + '.' + format.ext;

                    // Create a dummy download link
                    const link = document.createElement('a');

                    // For HTML, we can actually create a real download
                    if (format.ext === 'html') {
                        const htmlContent = `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>${title}</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        body {
            font-family: Arial, sans-serif;
            line-height: 1.6;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
        }
    </style>
</head>
<body class="bg-white dark:bg-gray-900">
    <div class="max-w-4xl mx-auto p-5">
        <h1 class="text-3xl font-bold mb-6">${title}</h1>
        ${content}
    </div>
</body>
</html>`;

                        const blob = new Blob([htmlContent], { type: 'text/html' });
                        link.href = URL.createObjectURL(blob);
                        link.download = filename;
                        link.click();
                    } else {
                        // For other formats, show a message
                        const notification = document.createElement('div');
                        notification.className = 'fixed top-4 right-4 bg-dark-700 text-white px-4 py-2 rounded-md shadow-lg z-50 animate-pulse-slow';
                        notification.textContent = 'Downloading as ' + format.name + ' would be implemented with server-side conversion.';
                        document.body.appendChild(notification);

                        setTimeout(() => {
                            document.body.removeChild(notification);
                        }, 3000);
                    }

                    // Remove the menu
                    document.body.removeChild(menu);
                });

                menu.appendChild(option);
            });

            document.body.appendChild(menu);

            // Close the menu when clicking outside
            document.addEventListener('click', function closeMenu(e) {
                if (!menu.contains(e.target) && e.target !== document.getElementById('downloadButton')) {
                    document.body.removeChild(menu);
                    document.removeEventListener('click', closeMenu);
                }
            });
        }
    </script>
    """

    # Append the JavaScript to the HTML
    html += js_script

    return html

def format_webpage_html(content, title="Webpage"):
    """
    ARCHIVED: Webpage formatting disabled - use Code Wave for webpage creation.

    This function has been archived because Code Wave now handles webpage design.
    This function is kept for reference only and should not be used for new development.

    Args:
        content: The webpage content
        title: The webpage title

    Returns:
        str: HTML representation of the webpage with Tailwind CSS
    """
    # Process content to extract sections
    sections = []

    # Simple section extraction based on headings
    section_pattern = r'(?:^|\n)#+\s+(.*?)(?:\n|$)((?:.+?)(?:(?=\n#+\s+)|$))'
    section_matches = re.finditer(section_pattern, content, re.DOTALL)

    for match in section_matches:
        section_title = match.group(1).strip()
        section_content = match.group(2).strip()
        sections.append({
            'title': section_title,
            'content': section_content
        })

    # If no sections found, create a single section
    if not sections:
        sections.append({
            'title': title,
            'content': content
        })

    # Generate a random accent color for the webpage
    accent_colors = ['primary', 'blue', 'indigo', 'purple', 'pink', 'rose', 'orange', 'amber', 'emerald', 'teal', 'cyan']
    accent_color = random.choice(accent_colors)

    # Create the webpage HTML with Tailwind CSS - Part 1 (Header)
    html = f"""
    <div class="bg-dark-600 rounded-lg shadow-lg overflow-hidden transition-all duration-300 hover:shadow-xl">
        <div class="flex items-center justify-between p-5 border-b border-dark-500">
            <h2 class="text-2xl font-bold text-dark-100">{title}</h2>
            <div class="flex items-center space-x-3">
                <span class="bg-{accent_color}-600 text-white px-3 py-1 rounded-full text-sm font-medium">Webpage</span>
                <button id="downloadButton" class="text-{accent_color}-400 hover:text-{accent_color}-300 transition-colors duration-200" title="Download webpage" onclick="downloadWebpage()">
                    <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="animate-bounce-slow">
                        <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
                        <polyline points="7 10 12 15 17 10"></polyline>
                        <line x1="12" y1="15" x2="12" y2="3"></line>
                    </svg>
                </button>
            </div>
        </div>

        <div class="p-5 bg-dark-600">
            <div class="webpage-preview bg-white dark:bg-gray-900 rounded-lg overflow-hidden shadow-lg">
                <!-- Webpage Navigation Bar Only -->
                <nav class="bg-{accent_color}-600 text-white py-4 px-6">
                    <div class="max-w-6xl mx-auto flex flex-wrap justify-between items-center">
                        <div class="flex space-x-8">
                            <a href="#" class="hover:text-{accent_color}-200 transition-colors duration-200 font-medium">Home</a>
                            <a href="#" class="hover:text-{accent_color}-200 transition-colors duration-200 font-medium">About</a>
                            <a href="#" class="hover:text-{accent_color}-200 transition-colors duration-200 font-medium">Services</a>
                            <a href="#" class="hover:text-{accent_color}-200 transition-colors duration-200 font-medium">Destinations</a>
                            <a href="#" class="hover:text-{accent_color}-200 transition-colors duration-200 font-medium">Contact</a>
                        </div>
                        <div>
                            <button class="bg-{accent_color}-500 hover:bg-{accent_color}-400 px-4 py-2 rounded-full text-sm font-medium transition-colors duration-200">
                                Book Now
                            </button>
                        </div>
                    </div>
                </nav>

                <!-- Webpage Content -->
                <main class="max-w-6xl mx-auto p-6 grid grid-cols-1 md:grid-cols-12 gap-6">
                    <!-- Main Content -->
                    <div class="md:col-span-8 space-y-6">
    """

    # Add sections to the webpage
    for i, section in enumerate(sections):
        animation_delay = i * 0.2
        html += f"""
                        <section class="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6 transform transition-all duration-500 hover:shadow-lg hover:-translate-y-1" style="animation-delay: {animation_delay}s">
                            <h2 class="text-2xl font-bold text-gray-800 dark:text-white mb-4">{section['title']}</h2>
                            <div class="prose dark:prose-invert max-w-none">
                                <p class="text-gray-600 dark:text-gray-300">{section['content']}</p>
                            </div>
                        </section>
        """

    # Add sidebar and complete the webpage
    html += f"""
                    </div>

                    <!-- Sidebar -->
                    <div class="md:col-span-4 space-y-6">
                        <div class="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
                            <h3 class="text-xl font-bold text-gray-800 dark:text-white mb-4">About This Page</h3>
                            <p class="text-gray-600 dark:text-gray-300">This webpage was generated using Tailwind CSS with beautiful animations and a responsive design.</p>
                        </div>

                        <div class="bg-{accent_color}-50 dark:bg-{accent_color}-900/20 rounded-lg shadow-md p-6">
                            <h3 class="text-xl font-bold text-{accent_color}-800 dark:text-{accent_color}-200 mb-4">Features</h3>
                            <ul class="space-y-2 text-{accent_color}-600 dark:text-{accent_color}-300">
                                <li class="flex items-center">
                                    <svg class="w-5 h-5 mr-2" fill="currentColor" viewBox="0 0 20 20">
                                        <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"></path>
                                    </svg>
                                    Responsive Design
                                </li>
                                <li class="flex items-center">
                                    <svg class="w-5 h-5 mr-2" fill="currentColor" viewBox="0 0 20 20">
                                        <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"></path>
                                    </svg>
                                    Modern Animations
                                </li>
                                <li class="flex items-center">
                                    <svg class="w-5 h-5 mr-2" fill="currentColor" viewBox="0 0 20 20">
                                        <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"></path>
                                    </svg>
                                    Dark Mode Support
                                </li>
                                <li class="flex items-center">
                                    <svg class="w-5 h-5 mr-2" fill="currentColor" viewBox="0 0 20 20">
                                        <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"></path>
                                    </svg>
                                    Tailwind CSS
                                </li>
                            </ul>
                        </div>
                    </div>
                </main>

                <!-- Webpage Footer -->
                <footer class="bg-gray-800 text-white p-6 mt-6">
                    <div class="max-w-6xl mx-auto">
                        <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
                            <div>
                                <h3 class="text-lg font-bold mb-4">About Us</h3>
                                <p class="text-gray-400">A modern webpage created with Tailwind CSS by the Designer Agent.</p>
                            </div>
                            <div>
                                <h3 class="text-lg font-bold mb-4">Quick Links</h3>
                                <ul class="space-y-2 text-gray-400">
                                    <li><a href="#" class="hover:text-white transition-colors duration-200">Home</a></li>
                                    <li><a href="#" class="hover:text-white transition-colors duration-200">About</a></li>
                                    <li><a href="#" class="hover:text-white transition-colors duration-200">Services</a></li>
                                    <li><a href="#" class="hover:text-white transition-colors duration-200">Contact</a></li>
                                </ul>
                            </div>
                            <div>
                                <h3 class="text-lg font-bold mb-4">Connect With Us</h3>
                                <div class="flex space-x-4">
                                    <a href="#" class="text-gray-400 hover:text-white transition-colors duration-200">
                                        <svg class="w-6 h-6" fill="currentColor" viewBox="0 0 24 24">
                                            <path d="M24 4.557c-.883.392-1.832.656-2.828.775 1.017-.609 1.798-1.574 2.165-2.724-.951.564-2.005.974-3.127 1.195-.897-.957-2.178-1.555-3.594-1.555-3.179 0-5.515 2.966-4.797 6.045-4.091-.205-7.719-2.165-10.148-5.144-1.29 2.213-.669 5.108 1.523 6.574-.806-.026-1.566-.247-2.229-.616-.054 2.281 1.581 4.415 3.949 4.89-.693.188-1.452.232-2.224.084.626 1.956 2.444 3.379 4.6 3.419-2.07 1.623-4.678 2.348-7.29 2.04 2.179 1.397 4.768 2.212 7.548 2.212 9.142 0 14.307-7.721 13.995-14.646.962-.695 1.797-1.562 2.457-2.549z"></path>
                                        </svg>
                                    </a>
                                    <a href="#" class="text-gray-400 hover:text-white transition-colors duration-200">
                                        <svg class="w-6 h-6" fill="currentColor" viewBox="0 0 24 24">
                                            <path d="M12 2.163c3.204 0 3.584.012 4.85.07 3.252.148 4.771 1.691 4.919 4.919.058 1.265.069 1.645.069 4.849 0 3.205-.012 3.584-.069 4.849-.149 3.225-1.664 4.771-4.919 4.919-1.266.058-1.644.07-4.85.07-3.204 0-3.584-.012-4.849-.07-3.26-.149-4.771-1.699-4.919-4.92-.058-1.265-.07-1.644-.07-4.849 0-3.204.013-3.583.07-4.849.149-3.227 1.664-4.771 4.919-4.919 1.266-.057 1.645-.069 4.849-.069zm0-2.163c-3.259 0-3.667.014-4.947.072-4.358.2-6.78 2.618-6.98 6.98-.059 1.281-.073 1.689-.073 4.948 0 3.259.014 3.668.072 4.948.2 4.358 2.618 6.78 6.98 6.98 1.281.058 1.689.072 4.948.072 3.259 0 3.668-.014 4.948-.072 4.354-.2 6.782-2.618 6.979-6.98.059-1.28.073-1.689.073-4.948 0-3.259-.014-3.667-.072-4.947-.196-4.354-2.617-6.78-6.979-6.98-1.281-.059-1.69-.073-4.949-.073zm0 5.838c-3.403 0-6.162 2.759-6.162 6.162s2.759 6.163 6.162 6.163 6.162-2.759 6.162-6.163c0-3.403-2.759-6.162-6.162-6.162zm0 10.162c-2.209 0-4-1.79-4-4 0-2.209 1.791-4 4-4s4 1.791 4 4c0 2.21-1.791 4-4 4zm6.406-11.845c-.796 0-1.441.645-1.441 1.44s.645 1.44 1.441 1.44c.795 0 1.439-.645 1.439-1.44s-.644-1.44-1.439-1.44z"></path>
                                        </svg>
                                    </a>
                                    <a href="#" class="text-gray-400 hover:text-white transition-colors duration-200">
                                        <svg class="w-6 h-6" fill="currentColor" viewBox="0 0 24 24">
                                            <path d="M19 0h-14c-2.761 0-5 2.239-5 5v14c0 2.761 2.239 5 5 5h14c2.762 0 5-2.239 5-5v-14c0-2.761-2.238-5-5-5zm-11 19h-3v-11h3v11zm-1.5-12.268c-.966 0-1.75-.79-1.75-1.764s.784-1.764 1.75-1.764 1.75.79 1.75 1.764-.783 1.764-1.75 1.764zm13.5 12.268h-3v-5.604c0-3.368-4-3.113-4 0v5.604h-3v-11h3v1.765c1.396-2.586 7-2.777 7 2.476v6.759z"></path>
                                        </svg>
                                    </a>
                                </div>
                            </div>
                        </div>
                        <div class="mt-6 pt-6 border-t border-gray-700 text-center text-gray-400">
                            <p>© 2023 Designer Agent. All rights reserved.</p>
                        </div>
                    </div>
                </footer>
            </div>
        </div>
    </div>

    """

    # Add the JavaScript for webpage download functionality
    js_script = """
    <script>
        function downloadWebpage() {
            const content = document.querySelector('.webpage-preview').outerHTML;
            const title = document.querySelector('.text-2xl.font-bold').textContent;

            // Create HTML content with proper escaping
            const htmlContent = `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>${title}</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script>
        tailwind.config = {
            darkMode: "class",
            theme: {
                extend: {
                    animation: {
                        "pulse-slow": "pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite"
                    }
                }
            }
        }
    </script>
</head>
<body>
    ${content}
    <script>
        if(window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches) {
            document.documentElement.classList.add("dark");
        }
        document.addEventListener("DOMContentLoaded", function() {
            const sections = document.querySelectorAll("section");
            const observer = new IntersectionObserver((entries) => {
                entries.forEach(entry => {
                    if(entry.isIntersecting) {
                        entry.target.classList.add("animate-pulse-slow");
                        observer.unobserve(entry.target);
                    }
                });
            }, {threshold: 0.1});
            sections.forEach(section => {
                observer.observe(section);
            });
        });
    </script>
</body>
</html>`;

            const blob = new Blob([htmlContent], { type: 'text/html' });
            const link = document.createElement('a');
            link.href = URL.createObjectURL(blob);
            link.download = title.replace(/[^a-z0-9]/gi, '_').toLowerCase() + '.html';
            link.click();
        }
    </script>
    """

    # Append the JavaScript to the HTML
    html += js_script

    return html

@document_generator_bp.route('/api/document/analyze', methods=['POST'])
def analyze_document():
    """
    Analyze a document and provide insights.

    Returns:
        Response: JSON response with the analysis results.
    """
    try:
        data = request.get_json()
        document = data.get('document', '')

        if not document:
            return jsonify({
                'success': False,
                'error': 'No document provided'
            })

        # Analyze the document
        analysis_result = document_tools.analyze_document(document)

        return jsonify({
            'success': True,
            'analysis': analysis_result
        })
    except Exception as e:
        logger.error(f"Error analyzing document: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        })

# Extraction functions for new tools
def extract_campaign_topic(content):
    """Extract campaign topic from content."""
    content_lower = content.lower()

    # Look for explicit topic mentions
    topic_patterns = [
        r'campaign (?:about|for|on) ([^.]+)',
        r'email (?:about|for|on) ([^.]+)',
        r'marketing ([^.]+)',
        r'promote ([^.]+)',
        r'advertise ([^.]+)'
    ]

    for pattern in topic_patterns:
        match = re.search(pattern, content_lower)
        if match:
            return match.group(1).strip()

    # Extract from first few words if no explicit topic
    words = content.split()
    if len(words) > 3:
        return ' '.join(words[2:5])

    return "Product Launch"

def extract_target_audience(content):
    """Extract target audience from content."""
    content_lower = content.lower()

    audiences = {
        'millennials': ['millennials', 'young adults', '20s', '30s'],
        'business professionals': ['professionals', 'business', 'corporate', 'executives'],
        'students': ['students', 'college', 'university', 'academic'],
        'seniors': ['seniors', 'elderly', 'older adults', '60+'],
        'parents': ['parents', 'families', 'moms', 'dads'],
        'entrepreneurs': ['entrepreneurs', 'startup', 'business owners']
    }

    for audience, keywords in audiences.items():
        if any(keyword in content_lower for keyword in keywords):
            return audience

    return "general"

def extract_campaign_type(content):
    """Extract campaign type from content."""
    content_lower = content.lower()

    if any(word in content_lower for word in ['promotion', 'sale', 'discount', 'offer']):
        return "promotional"
    elif any(word in content_lower for word in ['newsletter', 'update', 'news']):
        return "newsletter"
    elif any(word in content_lower for word in ['welcome', 'onboard', 'new']):
        return "welcome"
    elif any(word in content_lower for word in ['cart', 'abandon', 'checkout']):
        return "abandoned_cart"

    return "promotional"

def extract_tone(content):
    """Extract tone from content."""
    content_lower = content.lower()

    if any(word in content_lower for word in ['casual', 'friendly', 'fun', 'relaxed']):
        return "casual"
    elif any(word in content_lower for word in ['urgent', 'immediate', 'now', 'hurry']):
        return "urgent"
    elif any(word in content_lower for word in ['professional', 'formal', 'business']):
        return "professional"

    return "professional"

def extract_keywords(content):
    """Extract keywords from content."""
    content_lower = content.lower()

    # Look for explicit keyword mentions
    keyword_match = re.search(r'keywords?:?\s*([^.]+)', content_lower)
    if keyword_match:
        keywords_text = keyword_match.group(1)
        return [kw.strip() for kw in keywords_text.split(',')]

    # Extract potential keywords from content
    words = re.findall(r'\b\w{4,}\b', content_lower)
    common_words = {'this', 'that', 'with', 'have', 'will', 'from', 'they', 'been', 'were', 'said', 'each', 'which', 'their', 'time', 'about', 'would', 'there', 'could', 'other', 'more', 'very', 'what', 'know', 'just', 'first', 'into', 'over', 'think', 'also', 'your', 'work', 'life', 'only', 'can', 'still', 'should', 'after', 'being', 'now', 'made', 'before', 'here', 'through', 'when', 'where', 'much', 'some', 'these', 'many', 'then', 'them', 'well', 'were'}

    keywords = [word for word in set(words) if word not in common_words][:5]
    return keywords if keywords else ["content", "optimization"]

def extract_content_type(content):
    """Extract content type from content."""
    content_lower = content.lower()

    if any(word in content_lower for word in ['blog', 'post', 'article']):
        return "blog_post"
    elif any(word in content_lower for word in ['product', 'item', 'buy']):
        return "product_page"
    elif any(word in content_lower for word in ['landing', 'conversion', 'signup']):
        return "landing_page"
    elif any(word in content_lower for word in ['news', 'press', 'announcement']):
        return "article"

    return "blog_post"

def extract_subject(content):
    """Extract subject from content."""
    content_lower = content.lower()

    # Look for explicit subject mentions
    subject_patterns = [
        r'learn (?:about )?([^.]+)',
        r'study ([^.]+)',
        r'course (?:on|in) ([^.]+)',
        r'training (?:on|in) ([^.]+)',
        r'master ([^.]+)',
        r'understand ([^.]+)'
    ]

    for pattern in subject_patterns:
        match = re.search(pattern, content_lower)
        if match:
            return match.group(1).strip()

    # Extract from content
    words = content.split()
    if len(words) > 2:
        return ' '.join(words[1:4])

    return "General Skills"

def extract_skill_level(content):
    """Extract skill level from content."""
    content_lower = content.lower()

    if any(word in content_lower for word in ['beginner', 'new', 'start', 'basic', 'intro']):
        return "beginner"
    elif any(word in content_lower for word in ['intermediate', 'some experience', 'familiar']):
        return "intermediate"
    elif any(word in content_lower for word in ['advanced', 'expert', 'master', 'professional']):
        return "advanced"

    return "beginner"

def extract_learning_style(content):
    """Extract learning style from content."""
    content_lower = content.lower()

    if any(word in content_lower for word in ['visual', 'see', 'watch', 'diagram']):
        return "visual"
    elif any(word in content_lower for word in ['audio', 'listen', 'hear', 'podcast']):
        return "auditory"
    elif any(word in content_lower for word in ['hands-on', 'practice', 'do', 'build']):
        return "kinesthetic"
    elif any(word in content_lower for word in ['read', 'text', 'book', 'article']):
        return "reading"

    return "mixed"

def extract_time_commitment(content):
    """Extract time commitment from content."""
    content_lower = content.lower()

    if any(word in content_lower for word in ['light', 'casual', 'part-time', 'few hours']):
        return "light"
    elif any(word in content_lower for word in ['intensive', 'full-time', 'immersive', 'bootcamp']):
        return "intensive"

    return "moderate"

def extract_goals(content):
    """Extract goals from content."""
    content_lower = content.lower()

    goals = []
    goal_patterns = [
        r'goal:?\s*([^.]+)',
        r'want to ([^.]+)',
        r'need to ([^.]+)',
        r'achieve ([^.]+)',
        r'become ([^.]+)'
    ]

    for pattern in goal_patterns:
        matches = re.findall(pattern, content_lower)
        goals.extend(matches)

    return goals[:3] if goals else ["Master the fundamentals"]

def handle_email_campaign_request(content):
    """
    Handle an email campaign generation request.

    Args:
        content: The user's prompt content

    Returns:
        Response: JSON response with the email campaign
    """
    try:
        # Log that we're handling an email campaign request
        logger.info(f"Handling email campaign request: {content[:100]}...")

        # Extract campaign parameters from content
        campaign_topic = extract_campaign_topic(content)
        target_audience = extract_target_audience(content)
        campaign_type = extract_campaign_type(content)
        tone = extract_tone(content)

        # Generate the email campaign
        campaign_result = email_tools.create_email_campaign(
            campaign_topic=campaign_topic,
            target_audience=target_audience,
            campaign_type=campaign_type,
            tone=tone,
            include_ab_testing=True
        )

        # Format the email campaign HTML
        campaign_html = format_email_campaign_html(campaign_result)

        logger.info(f"Successfully generated email campaign for: {campaign_topic}")

        return jsonify({
            'success': True,
            'document_html': campaign_html,
            'is_email_campaign': True,
            'preview': f"Email Campaign: {campaign_topic}"
        })
    except Exception as e:
        logger.error(f"Error handling email campaign request: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        })

def handle_seo_optimization_request(content):
    """
    Handle an SEO optimization request.

    Args:
        content: The user's prompt content

    Returns:
        Response: JSON response with the SEO optimization
    """
    try:
        # Log that we're handling an SEO optimization request
        logger.info(f"Handling SEO optimization request: {content[:100]}...")

        # Extract SEO parameters from content
        target_keywords = extract_keywords(content)
        content_type = extract_content_type(content)
        target_audience = extract_target_audience(content)

        # Generate the SEO optimization
        seo_result = seo_tools.optimize_seo_content(
            content=content,
            target_keywords=target_keywords,
            content_type=content_type,
            target_audience=target_audience
        )

        # Format the SEO optimization HTML
        seo_html = format_seo_optimization_html(seo_result)

        logger.info(f"Successfully generated SEO optimization")

        return jsonify({
            'success': True,
            'document_html': seo_html,
            'is_seo_optimization': True,
            'preview': f"SEO Optimization: {content_type}"
        })
    except Exception as e:
        logger.error(f"Error handling SEO optimization request: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        })

def handle_learning_path_request(content):
    """
    Handle a learning path generation request.

    Args:
        content: The user's prompt content

    Returns:
        Response: JSON response with the learning path
    """
    try:
        # Log that we're handling a learning path request
        logger.info(f"Handling learning path request: {content[:100]}...")

        # Extract learning parameters from content
        subject = extract_subject(content)
        skill_level = extract_skill_level(content)
        learning_style = extract_learning_style(content)
        time_commitment = extract_time_commitment(content)
        goals = extract_goals(content)

        # Generate the learning path
        learning_result = learning_tools.create_learning_path(
            subject=subject,
            skill_level=skill_level,
            learning_style=learning_style,
            time_commitment=time_commitment,
            goals=goals
        )

        # Format the learning path HTML
        learning_html = format_learning_path_html(learning_result)

        logger.info(f"Successfully generated learning path for: {subject}")

        return jsonify({
            'success': True,
            'document_html': learning_html,
            'is_learning_path': True,
            'preview': f"Learning Path: {subject}"
        })
    except Exception as e:
        logger.error(f"Error handling learning path request: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        })

# Formatting functions for new tools
def format_email_campaign_html(campaign_result):
    """Format email campaign result as HTML."""
    if 'error' in campaign_result:
        return f"<div class='error'>Error: {campaign_result['error']}</div>"

    html = f"""
    <div class="email-campaign-container">
        <h1>📧 Email Campaign: {campaign_result['campaign_topic']}</h1>

        <div class="campaign-overview">
            <h2>Campaign Overview</h2>
            <div class="overview-grid">
                <div class="overview-item">
                    <strong>Topic:</strong> {campaign_result['campaign_topic']}
                </div>
                <div class="overview-item">
                    <strong>Audience:</strong> {campaign_result['target_audience']}
                </div>
                <div class="overview-item">
                    <strong>Type:</strong> {campaign_result['campaign_type']}
                </div>
                <div class="overview-item">
                    <strong>Tone:</strong> {campaign_result['tone']}
                </div>
            </div>
        </div>

        <div class="subject-lines">
            <h2>📝 Subject Line Variations</h2>
            <div class="subject-grid">
    """

    for subject in campaign_result.get('subject_lines', []):
        html += f"""
                <div class="subject-card">
                    <h3>{subject['variation']}</h3>
                    <p class="subject-text">"{subject['text']}"</p>
                    <div class="subject-stats">
                        <span>Characters: {subject['character_count']}</span>
                        <span>Predicted Open Rate: {subject['predicted_open_rate']:.1f}%</span>
                        <span>Urgency: {subject['urgency_level']}</span>
                    </div>
                </div>
        """

    html += """
            </div>
        </div>

        <div class="email-content">
            <h2>✉️ Email Content</h2>
            <div class="content-tabs">
                <div class="tab-content">
                    <h3>HTML Version</h3>
                    <div class="email-preview">
    """

    html += campaign_result.get('email_body', {}).get('html_content', '')

    html += f"""
                    </div>
                </div>
            </div>
            <div class="content-stats">
                <span>Word Count: {campaign_result.get('email_body', {}).get('word_count', 0)}</span>
                <span>Read Time: {campaign_result.get('email_body', {}).get('estimated_read_time', 'N/A')}</span>
                <span>CTAs: {campaign_result.get('email_body', {}).get('cta_count', 0)}</span>
            </div>
        </div>
    """

    if campaign_result.get('ab_testing'):
        html += f"""
        <div class="ab-testing">
            <h2>🧪 A/B Testing Recommendations</h2>
            <div class="testing-grid">
                <div class="test-card">
                    <h3>Subject Line Test</h3>
                    <p><strong>Variation A:</strong> {campaign_result['ab_testing']['test_variations']['subject_lines']['variation_a']['text']}</p>
                    <p><strong>Variation B:</strong> {campaign_result['ab_testing']['test_variations']['subject_lines']['variation_b']['text']}</p>
                    <p><strong>Metric:</strong> {campaign_result['ab_testing']['test_variations']['subject_lines']['test_metric']}</p>
                </div>
            </div>
            <div class="recommendations">
                <h3>Testing Tips</h3>
                <ul>
        """

        for rec in campaign_result['ab_testing'].get('recommendations', []):
            html += f"<li>{rec}</li>"

        html += """
                </ul>
            </div>
        </div>
        """

    html += f"""
        <div class="performance-metrics">
            <h2>📊 Expected Performance</h2>
            <div class="metrics-grid">
                <div class="metric-card">
                    <h3>Open Rate</h3>
                    <p class="metric-value">{campaign_result.get('performance_metrics', {}).get('expected_performance', {}).get('open_rate', 'N/A')}</p>
                </div>
                <div class="metric-card">
                    <h3>Click Rate</h3>
                    <p class="metric-value">{campaign_result.get('performance_metrics', {}).get('expected_performance', {}).get('click_rate', 'N/A')}</p>
                </div>
                <div class="metric-card">
                    <h3>Conversion Rate</h3>
                    <p class="metric-value">{campaign_result.get('performance_metrics', {}).get('expected_performance', {}).get('conversion_rate', 'N/A')}</p>
                </div>
            </div>
        </div>

        <div class="send-times">
            <h2>⏰ Optimal Send Times</h2>
            <div class="send-time-card">
                <p><strong>Recommended:</strong> {campaign_result.get('send_times', {}).get('recommended_schedule', {}).get('primary_send_time', 'N/A')}</p>
                <p><strong>Frequency:</strong> {campaign_result.get('send_times', {}).get('recommended_schedule', {}).get('frequency', 'N/A')}</p>
            </div>
        </div>
    </div>

    <style>
    .email-campaign-container {{
        max-width: 1200px;
        margin: 0 auto;
        padding: 20px;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }}
    .overview-grid, .subject-grid, .metrics-grid {{
        display: grid;
        gap: 15px;
        margin: 15px 0;
    }}
    .overview-grid {{
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    }}
    .subject-grid {{
        grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
    }}
    .metrics-grid {{
        grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
    }}
    .subject-card, .metric-card, .test-card, .send-time-card {{
        background: #f8f9fa;
        padding: 15px;
        border-radius: 8px;
        border-left: 4px solid #007bff;
    }}
    .subject-text {{
        font-size: 16px;
        font-weight: bold;
        color: #333;
        margin: 10px 0;
    }}
    .subject-stats {{
        display: flex;
        gap: 10px;
        font-size: 12px;
        color: #666;
    }}
    .email-preview {{
        background: white;
        padding: 20px;
        border: 1px solid #ddd;
        border-radius: 5px;
        margin: 10px 0;
    }}
    .content-stats {{
        display: flex;
        gap: 20px;
        margin: 10px 0;
        font-size: 14px;
        color: #666;
    }}
    .metric-value {{
        font-size: 24px;
        font-weight: bold;
        color: #007bff;
        margin: 5px 0;
    }}
    h1 {{ color: #333; border-bottom: 2px solid #007bff; padding-bottom: 10px; }}
    h2 {{ color: #555; margin-top: 30px; }}
    h3 {{ color: #666; }}
    </style>
    """

    return html

def format_seo_optimization_html(seo_result):
    """Format SEO optimization result as HTML."""
    if 'error' in seo_result:
        return f"<div class='error'>Error: {seo_result['error']}</div>"

    html = f"""
    <div class="seo-optimization-container">
        <h1>🔍 SEO Content Optimization</h1>

        <div class="optimization-overview">
            <h2>Optimization Overview</h2>
            <div class="overview-grid">
                <div class="overview-item">
                    <strong>Content Type:</strong> {seo_result['content_type']}
                </div>
                <div class="overview-item">
                    <strong>Target Keywords:</strong> {', '.join(seo_result.get('target_keywords', []))}
                </div>
                <div class="overview-item">
                    <strong>Improvement Score:</strong> {seo_result.get('improvement_summary', {}).get('overall_score', 'N/A')}/100
                </div>
            </div>
        </div>

        <div class="content-comparison">
            <h2>📝 Content Optimization</h2>
            <div class="comparison-tabs">
                <div class="tab-content">
                    <h3>Optimized Content</h3>
                    <div class="content-preview">
                        {seo_result.get('optimized_content', '').replace(chr(10), '<br>')}
                    </div>
                </div>
            </div>
        </div>

        <div class="analysis-results">
            <h2>📊 Content Analysis</h2>
            <div class="analysis-grid">
                <div class="analysis-card">
                    <h3>Word Count</h3>
                    <p class="metric-value">{seo_result.get('optimized_analysis', {}).get('word_count', 0)}</p>
                    <p class="metric-change">+{seo_result.get('improvement_summary', {}).get('word_count_change', 0)} words</p>
                </div>
                <div class="analysis-card">
                    <h3>Readability Score</h3>
                    <p class="metric-value">{seo_result.get('optimized_analysis', {}).get('readability_score', {}).get('score', 0)}</p>
                    <p class="metric-level">{seo_result.get('optimized_analysis', {}).get('readability_score', {}).get('level', 'N/A')}</p>
                </div>
                <div class="analysis-card">
                    <h3>SEO Structure</h3>
                    <p class="metric-value">{seo_result.get('optimized_analysis', {}).get('seo_elements', {}).get('structure_score', 0)}/6</p>
                    <p class="metric-change">+{seo_result.get('improvement_summary', {}).get('seo_score_improvement', 0)} points</p>
                </div>
            </div>
        </div>
    """

    if seo_result.get('recommendations'):
        html += """
        <div class="recommendations">
            <h2>💡 SEO Recommendations</h2>
            <div class="recommendations-list">
        """

        for rec in seo_result['recommendations']:
            priority_color = {'high': '#dc3545', 'medium': '#ffc107', 'low': '#28a745'}.get(rec.get('priority', 'medium'), '#6c757d')
            html += f"""
                <div class="recommendation-card" style="border-left-color: {priority_color}">
                    <h4>{rec.get('issue', 'Issue')}</h4>
                    <p><strong>Priority:</strong> <span style="color: {priority_color}">{rec.get('priority', 'medium').upper()}</span></p>
                    <p><strong>Recommendation:</strong> {rec.get('recommendation', '')}</p>
                    <p><strong>Impact:</strong> {rec.get('impact', '')}</p>
                </div>
            """

        html += """
            </div>
        </div>
        """

    html += f"""
        <div class="meta-tags">
            <h2>🏷️ Generated Meta Tags</h2>
            <div class="meta-grid">
                <div class="meta-card">
                    <h4>Title Tag</h4>
                    <p class="meta-content">{seo_result.get('meta_tags', {}).get('title', '')}</p>
                </div>
                <div class="meta-card">
                    <h4>Meta Description</h4>
                    <p class="meta-content">{seo_result.get('meta_tags', {}).get('description', '')}</p>
                </div>
                <div class="meta-card">
                    <h4>Keywords</h4>
                    <p class="meta-content">{seo_result.get('meta_tags', {}).get('keywords', '')}</p>
                </div>
            </div>
        </div>

        <div class="technical-seo">
            <h2>⚙️ Technical SEO Suggestions</h2>
            <div class="technical-grid">
    """

    for category, details in seo_result.get('technical_seo', {}).items():
        if isinstance(details, dict) and 'recommendations' in details:
            html += f"""
                <div class="technical-card">
                    <h4>{category.replace('_', ' ').title()}</h4>
                    <ul>
            """
            for rec in details['recommendations'][:3]:  # Limit to 3 recommendations
                html += f"<li>{rec}</li>"
            html += """
                    </ul>
                </div>
            """

    html += """
            </div>
        </div>
    </div>

    <style>
    .seo-optimization-container {
        max-width: 1200px;
        margin: 0 auto;
        padding: 20px;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    .overview-grid, .analysis-grid, .meta-grid, .technical-grid {
        display: grid;
        gap: 15px;
        margin: 15px 0;
    }
    .overview-grid {
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    }
    .analysis-grid {
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    }
    .meta-grid {
        grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
    }
    .technical-grid {
        grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
    }
    .analysis-card, .meta-card, .technical-card, .recommendation-card {
        background: #f8f9fa;
        padding: 15px;
        border-radius: 8px;
        border-left: 4px solid #28a745;
    }
    .recommendation-card {
        border-left: 4px solid #ffc107;
        margin: 10px 0;
    }
    .content-preview {
        background: white;
        padding: 20px;
        border: 1px solid #ddd;
        border-radius: 5px;
        margin: 10px 0;
        max-height: 400px;
        overflow-y: auto;
    }
    .metric-value {
        font-size: 24px;
        font-weight: bold;
        color: #28a745;
        margin: 5px 0;
    }
    .metric-change {
        font-size: 14px;
        color: #007bff;
    }
    .metric-level {
        font-size: 14px;
        color: #666;
    }
    .meta-content {
        background: #e9ecef;
        padding: 10px;
        border-radius: 4px;
        font-family: monospace;
        font-size: 14px;
    }
    h1 { color: #333; border-bottom: 2px solid #28a745; padding-bottom: 10px; }
    h2 { color: #555; margin-top: 30px; }
    h3, h4 { color: #666; }
    </style>
    """

    return html

def format_learning_path_html(learning_result):
    """Format learning path result as HTML."""
    if 'error' in learning_result:
        return f"<div class='error'>Error: {learning_result['error']}</div>"

    html = f"""
    <div class="learning-path-container">
        <h1>🎓 Learning Path: {learning_result['subject']}</h1>

        <div class="path-overview">
            <h2>Learning Overview</h2>
            <div class="overview-grid">
                <div class="overview-item">
                    <strong>Subject:</strong> {learning_result['subject']}
                </div>
                <div class="overview-item">
                    <strong>Skill Level:</strong> {learning_result['skill_level']}
                </div>
                <div class="overview-item">
                    <strong>Learning Style:</strong> {learning_result['learning_style']}
                </div>
                <div class="overview-item">
                    <strong>Time Commitment:</strong> {learning_result['time_commitment']}
                </div>
                <div class="overview-item">
                    <strong>Duration:</strong> {learning_result.get('estimated_completion', {}).get('adjusted_duration_weeks', 'N/A')} weeks
                </div>
                <div class="overview-item">
                    <strong>Completion Date:</strong> {learning_result.get('estimated_completion', {}).get('estimated_completion_date', 'N/A')}
                </div>
            </div>
        </div>

        <div class="curriculum">
            <h2>📚 Curriculum</h2>
            <div class="modules-container">
    """

    for module in learning_result.get('curriculum', {}).get('modules', []):
        html += f"""
                <div class="module-card">
                    <h3>Module {module['id']}: {module['title']}</h3>
                    <p class="module-description">{module['description']}</p>
                    <div class="module-details">
                        <span class="duration">Duration: {module['duration_weeks']} weeks</span>
                        <span class="difficulty">Difficulty: {module['difficulty']}</span>
                    </div>
                    <div class="learning-objectives">
                        <h4>Learning Objectives:</h4>
                        <ul>
        """

        for objective in module.get('learning_objectives', []):
            html += f"<li>{objective}</li>"

        html += f"""
                        </ul>
                    </div>
                    <div class="key-concepts">
                        <h4>Key Concepts:</h4>
                        <div class="concepts-tags">
        """

        for concept in module.get('key_concepts', []):
            html += f'<span class="concept-tag">{concept}</span>'

        html += """
                        </div>
                    </div>
                </div>
        """

    html += """
            </div>
        </div>

        <div class="resources">
            <h2>📖 Learning Resources</h2>
            <div class="resources-grid">
    """

    resources = learning_result.get('resources', {})

    # Books section
    if resources.get('books'):
        html += """
                <div class="resource-section">
                    <h3>📚 Books</h3>
                    <div class="resource-list">
        """
        for book in resources['books'][:3]:  # Limit to 3 books
            html += f"""
                        <div class="resource-item">
                            <h4>{book['title']}</h4>
                            <p><strong>Author:</strong> {book['author']}</p>
                            <p><strong>Type:</strong> {book['type']}</p>
                            <p><strong>Rating:</strong> ⭐ {book['rating']}/5</p>
                            <p>{book['description']}</p>
                        </div>
            """
        html += """
                    </div>
                </div>
        """

    # Online courses section
    if resources.get('online_courses'):
        html += """
                <div class="resource-section">
                    <h3>💻 Online Courses</h3>
                    <div class="resource-list">
        """
        for course in resources['online_courses'][:3]:  # Limit to 3 courses
            html += f"""
                        <div class="resource-item">
                            <h4>{course['title']}</h4>
                            <p><strong>Platform:</strong> {course['platform']}</p>
                            <p><strong>Duration:</strong> {course['duration']}</p>
                            <p><strong>Price:</strong> {course['price']}</p>
                            <p><strong>Rating:</strong> ⭐ {course['rating']}/5</p>
                            <p>{course['description']}</p>
                        </div>
            """
        html += """
                    </div>
                </div>
        """

    html += """
            </div>
        </div>

        <div class="study-schedule">
            <h2>📅 Study Schedule</h2>
            <div class="schedule-overview">
    """

    schedule = learning_result.get('study_schedule', {})
    allocation = schedule.get('weekly_allocation', {})

    html += f"""
                <div class="schedule-stats">
                    <div class="stat-card">
                        <h4>Weekly Hours</h4>
                        <p class="stat-value">{allocation.get('hours_per_week', 'N/A')}</p>
                    </div>
                    <div class="stat-card">
                        <h4>Sessions per Week</h4>
                        <p class="stat-value">{allocation.get('sessions_per_week', 'N/A')}</p>
                    </div>
                    <div class="stat-card">
                        <h4>Session Length</h4>
                        <p class="stat-value">{allocation.get('session_length', 'N/A')}</p>
                    </div>
                </div>
            </div>
            <div class="study-tips">
                <h3>📝 Study Tips</h3>
                <ul>
    """

    for tip in schedule.get('daily_study_tips', [])[:5]:  # Limit to 5 tips
        html += f"<li>{tip}</li>"

    html += """
                </ul>
            </div>
        </div>

        <div class="progress-tracking">
            <h2>📊 Progress Tracking</h2>
            <div class="tracking-overview">
    """

    progress = learning_result.get('progress_tracking', {})
    metrics = progress.get('progress_metrics', {})

    html += f"""
                <div class="progress-stats">
                    <div class="progress-card">
                        <h4>Total Modules</h4>
                        <p class="progress-value">{metrics.get('total_modules', 0)}</p>
                    </div>
                    <div class="progress-card">
                        <h4>Current Progress</h4>
                        <p class="progress-value">{metrics.get('completion_percentage', 0)}%</p>
                    </div>
                    <div class="progress-card">
                        <h4>Next Milestone</h4>
                        <p class="progress-text">{metrics.get('next_milestone', 'N/A')}</p>
                    </div>
                </div>

                <div class="badges-section">
                    <h3>🏆 Available Badges</h3>
                    <div class="badges-grid">
    """

    for badge in progress.get('badges', [])[:4]:  # Limit to 4 badges
        html += f"""
                        <div class="badge-card">
                            <h4>{badge['name']}</h4>
                            <p>{badge['description']}</p>
                            <p class="badge-requirement">{badge['requirement']}</p>
                        </div>
        """

    html += """
                    </div>
                </div>
            </div>
        </div>

        <div class="learning-strategies">
            <h2>🧠 Learning Strategies</h2>
            <div class="strategies-content">
    """

    strategies = learning_result.get('learning_strategies', {})

    html += f"""
                <div class="strategy-section">
                    <h3>Primary Techniques for {strategies.get('learning_style', 'Mixed')} Learners</h3>
                    <ul>
    """

    for technique in strategies.get('primary_techniques', [])[:5]:  # Limit to 5 techniques
        html += f"<li>{technique}</li>"

    html += f"""
                    </ul>
                </div>

                <div class="strategy-section">
                    <h3>Productivity Tips</h3>
                    <ul>
    """

    for tip in strategies.get('productivity_tips', [])[:5]:  # Limit to 5 tips
        html += f"<li>{tip}</li>"

    html += """
                    </ul>
                </div>
            </div>
        </div>
    </div>

    <style>
    .learning-path-container {
        max-width: 1200px;
        margin: 0 auto;
        padding: 20px;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    .overview-grid, .resources-grid, .schedule-stats, .progress-stats, .badges-grid {
        display: grid;
        gap: 15px;
        margin: 15px 0;
    }
    .overview-grid {
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    }
    .resources-grid {
        grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
    }
    .schedule-stats, .progress-stats {
        grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
    }
    .badges-grid {
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    }
    .module-card, .resource-item, .stat-card, .progress-card, .badge-card {
        background: #f8f9fa;
        padding: 15px;
        border-radius: 8px;
        border-left: 4px solid #6f42c1;
        margin: 10px 0;
    }
    .module-details {
        display: flex;
        gap: 15px;
        margin: 10px 0;
        font-size: 14px;
        color: #666;
    }
    .concepts-tags {
        display: flex;
        flex-wrap: wrap;
        gap: 5px;
        margin: 10px 0;
    }
    .concept-tag {
        background: #e9ecef;
        padding: 4px 8px;
        border-radius: 12px;
        font-size: 12px;
        color: #495057;
    }
    .stat-value, .progress-value {
        font-size: 24px;
        font-weight: bold;
        color: #6f42c1;
        margin: 5px 0;
    }
    .progress-text {
        font-size: 14px;
        color: #666;
        margin: 5px 0;
    }
    .badge-requirement {
        font-size: 12px;
        color: #6c757d;
        font-style: italic;
    }
    h1 { color: #333; border-bottom: 2px solid #6f42c1; padding-bottom: 10px; }
    h2 { color: #555; margin-top: 30px; }
    h3, h4 { color: #666; }
    </style>
    """

    return html