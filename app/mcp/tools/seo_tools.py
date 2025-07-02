"""
SEO Content Optimizer Tools

This module provides tools for analyzing and optimizing content for search engines
with keyword suggestions and readability improvements.
"""

import logging
import re
import random
import sys
import os
from typing import Dict, List, Any, Optional
from datetime import datetime

# Import the API modules using relative imports
try:
    from ...api.gemini import GeminiAPI
    from ...api.groq import GroqAPI
except ImportError:
    # Fallback if imports fail
    GeminiAPI = None
    GroqAPI = None

logger = logging.getLogger(__name__)

class SEOTools:
    """Tools for SEO content optimization and analysis."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

        # Initialize LLM clients
        self.gemini_api = None
        self.groq_api = None
        self.llm_available = False

        try:
            if GeminiAPI:
                self.gemini_api = GeminiAPI()
                self.llm_available = True
                self.logger.info("Gemini API initialized for SEO tools")
        except Exception as e:
            self.logger.warning(f"Failed to initialize Gemini API: {e}")

        try:
            if GroqAPI and not self.llm_available:
                self.groq_api = GroqAPI()
                self.llm_available = True
                self.logger.info("Groq API initialized for SEO tools")
        except Exception as e:
            self.logger.warning(f"Failed to initialize Groq API: {e}")

        if not self.llm_available:
            self.logger.warning("No LLM APIs available - falling back to template mode")

    def _call_llm(self, prompt: str, temperature: float = 0.7) -> str:
        """Call the available LLM API with the given prompt."""
        if not self.llm_available:
            return None

        try:
            if self.gemini_api:
                return self.gemini_api.generate_text(prompt, temperature=temperature)
            elif self.groq_api:
                return self.groq_api.generate_text(prompt, temperature=temperature)
        except Exception as e:
            self.logger.error(f"LLM API call failed: {e}")

        return None

    def optimize_seo_content(
        self,
        content: str,
        target_keywords: List[str] = None,
        content_type: str = "blog_post",
        target_audience: str = "general",
        **kwargs
    ) -> Dict[str, Any]:
        """
        Analyze and optimize content for search engines with keyword suggestions and readability improvements.

        Args:
            content: The content to optimize
            target_keywords: List of target keywords to optimize for
            content_type: Type of content (blog_post, product_page, landing_page, etc.)
            target_audience: Target audience for the content

        Returns:
            Dict containing the SEO analysis and optimized content
        """
        try:
            self.logger.info(f"Optimizing SEO content for type: {content_type}")

            # Analyze current content
            current_analysis = self._analyze_current_content(content)

            # Generate keyword suggestions if not provided
            if not target_keywords:
                target_keywords = self._generate_keyword_suggestions(content, content_type)

            # Optimize content using LLM or templates
            if self.llm_available:
                optimized_content = self._optimize_content_llm(content, target_keywords, content_type)
                if not optimized_content:
                    optimized_content = self._optimize_content(content, target_keywords, content_type)
            else:
                optimized_content = self._optimize_content(content, target_keywords, content_type)

            # Analyze optimized content
            optimized_analysis = self._analyze_current_content(optimized_content)

            # Generate SEO recommendations
            recommendations = self._generate_seo_recommendations(current_analysis, target_keywords, content_type)

            # Generate meta tags
            meta_tags = self._generate_meta_tags(optimized_content, target_keywords)

            # Generate technical SEO suggestions
            technical_seo = self._generate_technical_seo_suggestions(content_type)

            result = {
                "original_content": content,
                "optimized_content": optimized_content,
                "target_keywords": target_keywords,
                "content_type": content_type,
                "current_analysis": current_analysis,
                "optimized_analysis": optimized_analysis,
                "recommendations": recommendations,
                "meta_tags": meta_tags,
                "technical_seo": technical_seo,
                "improvement_summary": self._generate_improvement_summary(current_analysis, optimized_analysis),
                "optimized_at": datetime.now().isoformat()
            }

            self.logger.info(f"Successfully optimized SEO content")
            return result

        except Exception as e:
            self.logger.error(f"Error optimizing SEO content: {str(e)}")
            return {
                "error": f"Failed to optimize SEO content: {str(e)}",
                "original_content": content
            }

    def _analyze_current_content(self, content: str) -> Dict[str, Any]:
        """Analyze the current content for SEO metrics."""

        # Basic content metrics
        word_count = len(content.split())
        char_count = len(content)
        paragraph_count = len([p for p in content.split('\n\n') if p.strip()])

        # Extract headings
        headings = {
            "h1": re.findall(r'^# (.+)$', content, re.MULTILINE),
            "h2": re.findall(r'^## (.+)$', content, re.MULTILINE),
            "h3": re.findall(r'^### (.+)$', content, re.MULTILINE)
        }

        # Calculate readability score (simplified Flesch Reading Ease)
        readability_score = self._calculate_readability_score(content)

        # Analyze keyword density
        keyword_density = self._analyze_keyword_density(content)

        # Check for SEO elements
        seo_elements = self._check_seo_elements(content)

        return {
            "word_count": word_count,
            "character_count": char_count,
            "paragraph_count": paragraph_count,
            "headings": headings,
            "readability_score": readability_score,
            "keyword_density": keyword_density,
            "seo_elements": seo_elements,
            "estimated_reading_time": f"{max(1, word_count // 200)} min"
        }

    def _calculate_readability_score(self, content: str) -> Dict[str, Any]:
        """Calculate a simplified readability score."""

        sentences = re.split(r'[.!?]+', content)
        sentences = [s.strip() for s in sentences if s.strip()]

        words = content.split()

        if not sentences or not words:
            return {"score": 0, "level": "Unknown"}

        avg_sentence_length = len(words) / len(sentences)

        # Simplified scoring (higher is better)
        if avg_sentence_length <= 15:
            score = 85
            level = "Easy"
        elif avg_sentence_length <= 20:
            score = 70
            level = "Fairly Easy"
        elif avg_sentence_length <= 25:
            score = 55
            level = "Standard"
        else:
            score = 40
            level = "Difficult"

        return {
            "score": score,
            "level": level,
            "avg_sentence_length": round(avg_sentence_length, 1),
            "total_sentences": len(sentences),
            "total_words": len(words)
        }

    def _analyze_keyword_density(self, content: str) -> Dict[str, Any]:
        """Analyze keyword density in the content."""

        words = re.findall(r'\b\w+\b', content.lower())
        total_words = len(words)

        if total_words == 0:
            return {"top_keywords": [], "total_words": 0}

        # Count word frequency
        word_freq = {}
        for word in words:
            if len(word) > 3:  # Only consider words longer than 3 characters
                word_freq[word] = word_freq.get(word, 0) + 1

        # Get top keywords
        top_keywords = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:10]

        # Calculate density percentages
        keyword_analysis = []
        for word, count in top_keywords:
            density = (count / total_words) * 100
            keyword_analysis.append({
                "keyword": word,
                "count": count,
                "density": round(density, 2)
            })

        return {
            "top_keywords": keyword_analysis,
            "total_words": total_words,
            "unique_words": len(word_freq)
        }

    def _check_seo_elements(self, content: str) -> Dict[str, Any]:
        """Check for important SEO elements in the content."""

        # Check for various SEO elements
        has_h1 = bool(re.search(r'^# ', content, re.MULTILINE))
        has_h2 = bool(re.search(r'^## ', content, re.MULTILINE))
        has_internal_links = bool(re.search(r'\[.+\]\(.+\)', content))
        has_external_links = bool(re.search(r'\[.+\]\(http.+\)', content))
        has_images = bool(re.search(r'!\[.+\]\(.+\)', content))
        has_lists = bool(re.search(r'^\s*[-*+]\s', content, re.MULTILINE))
        has_bold_text = bool(re.search(r'\*\*.+\*\*', content))

        return {
            "has_h1_heading": has_h1,
            "has_h2_headings": has_h2,
            "has_internal_links": has_internal_links,
            "has_external_links": has_external_links,
            "has_images": has_images,
            "has_lists": has_lists,
            "has_bold_text": has_bold_text,
            "structure_score": sum([has_h1, has_h2, has_internal_links, has_images, has_lists, has_bold_text])
        }

    def _generate_keyword_suggestions(self, content: str, content_type: str) -> List[str]:
        """Generate keyword suggestions based on content analysis."""

        # Extract potential keywords from content
        words = re.findall(r'\b\w+\b', content.lower())
        word_freq = {}

        for word in words:
            if len(word) > 4:  # Focus on longer words
                word_freq[word] = word_freq.get(word, 0) + 1

        # Get most frequent words as base keywords
        base_keywords = [word for word, count in sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:5]]

        # Add content-type specific keywords
        type_keywords = {
            "blog_post": ["guide", "tips", "how to", "best practices", "tutorial"],
            "product_page": ["buy", "price", "review", "features", "benefits"],
            "landing_page": ["solution", "service", "professional", "expert", "quality"],
            "article": ["information", "facts", "research", "analysis", "insights"]
        }

        suggested_keywords = base_keywords + type_keywords.get(content_type, [])

        # Remove duplicates and return top 8
        return list(dict.fromkeys(suggested_keywords))[:8]

    def _optimize_content(self, content: str, target_keywords: List[str], content_type: str) -> str:
        """Optimize the content for target keywords."""

        optimized = content

        # Ensure H1 heading exists
        if not re.search(r'^# ', optimized, re.MULTILINE):
            # Add H1 with primary keyword
            primary_keyword = target_keywords[0] if target_keywords else "Guide"
            h1_title = f"# Complete {primary_keyword.title()} Guide"
            optimized = f"{h1_title}\n\n{optimized}"

        # Add keyword-rich introduction if content is short
        if len(optimized.split()) < 50:
            intro = self._generate_keyword_rich_intro(target_keywords, content_type)
            optimized = f"{optimized}\n\n{intro}"

        # Add H2 sections if missing
        if not re.search(r'^## ', optimized, re.MULTILINE):
            sections = self._generate_h2_sections(target_keywords, content_type)
            optimized = f"{optimized}\n\n{sections}"

        # Add conclusion with keywords
        if "conclusion" not in optimized.lower():
            conclusion = self._generate_conclusion(target_keywords)
            optimized = f"{optimized}\n\n{conclusion}"

        return optimized

    def _optimize_content_llm(self, content: str, target_keywords: List[str], content_type: str) -> str:
        """Optimize content using LLM for better SEO."""

        keywords_str = ", ".join(target_keywords) if target_keywords else "relevant keywords"

        prompt = f"""Optimize this content for SEO while maintaining its original meaning and value.

Original Content:
{content}

SEO Requirements:
- Target Keywords: {keywords_str}
- Content Type: {content_type}
- Optimize for search engines while keeping it natural and readable
- Add proper heading structure (H1, H2, H3)
- Include target keywords naturally throughout the content
- Improve readability and flow
- Add a compelling introduction and conclusion
- Ensure content is comprehensive and valuable

Instructions:
1. Keep the core message and value of the original content
2. Add proper markdown headings (# for H1, ## for H2, ### for H3)
3. Naturally incorporate the target keywords without keyword stuffing
4. Improve sentence structure and readability
5. Add relevant sections if the content is too short
6. Include a strong introduction and conclusion
7. Make it engaging and informative

Return only the optimized content in markdown format:"""

        try:
            response = self._call_llm(prompt, temperature=0.7)
            if response and len(response.strip()) > len(content) * 0.5:  # Ensure we got substantial content
                return response.strip()
        except Exception as e:
            self.logger.warning(f"LLM content optimization failed: {e}")

        return None

    def _generate_keyword_rich_intro(self, keywords: List[str], content_type: str) -> str:
        """Generate a keyword-rich introduction."""

        primary_keyword = keywords[0] if keywords else "topic"

        intros = {
            "blog_post": f"In this comprehensive guide, we'll explore everything you need to know about {primary_keyword}. Whether you're a beginner or looking to improve your {primary_keyword} skills, this article covers the essential aspects.",
            "product_page": f"Discover the best {primary_keyword} solutions available today. Our {primary_keyword} products are designed to meet your specific needs and deliver exceptional results.",
            "landing_page": f"Looking for professional {primary_keyword} services? You've come to the right place. Our expert team specializes in {primary_keyword} and delivers outstanding results.",
            "article": f"Understanding {primary_keyword} is crucial in today's landscape. This article provides in-depth analysis and insights into {primary_keyword} trends and best practices."
        }

        return intros.get(content_type, intros["blog_post"])

    def _generate_h2_sections(self, keywords: List[str], content_type: str) -> str:
        """Generate H2 sections with keywords."""

        primary_keyword = keywords[0] if keywords else "topic"
        secondary_keywords = keywords[1:4] if len(keywords) > 1 else ["benefits", "tips", "guide"]

        sections = []

        if content_type == "blog_post":
            sections = [
                f"## What is {primary_keyword.title()}?",
                f"## Benefits of {primary_keyword.title()}",
                f"## How to Get Started with {primary_keyword.title()}",
                f"## Best Practices for {primary_keyword.title()}"
            ]
        elif content_type == "product_page":
            sections = [
                f"## {primary_keyword.title()} Features",
                f"## Why Choose Our {primary_keyword.title()}",
                f"## {primary_keyword.title()} Specifications",
                f"## Customer Reviews"
            ]
        else:
            sections = [
                f"## Understanding {primary_keyword.title()}",
                f"## Key {primary_keyword.title()} Strategies",
                f"## {primary_keyword.title()} Implementation"
            ]

        return "\n\n".join(sections[:3])  # Limit to 3 sections

    def _generate_conclusion(self, keywords: List[str]) -> str:
        """Generate a conclusion with keywords."""

        primary_keyword = keywords[0] if keywords else "topic"

        return f"## Conclusion\n\nIn conclusion, {primary_keyword} plays a vital role in achieving your goals. By implementing the strategies and best practices outlined in this guide, you'll be well-equipped to succeed with {primary_keyword}. Remember to stay updated with the latest {primary_keyword} trends and continuously improve your approach."

    def _generate_seo_recommendations(self, analysis: Dict, keywords: List[str], content_type: str) -> List[Dict[str, Any]]:
        """Generate SEO recommendations based on content analysis."""

        recommendations = []

        # Word count recommendations
        if analysis["word_count"] < 300:
            recommendations.append({
                "type": "content_length",
                "priority": "high",
                "issue": "Content too short",
                "recommendation": "Expand content to at least 300-500 words for better SEO performance",
                "impact": "Low word count may hurt search rankings"
            })
        elif analysis["word_count"] > 2000:
            recommendations.append({
                "type": "content_length",
                "priority": "medium",
                "issue": "Content very long",
                "recommendation": "Consider breaking into multiple pages or adding table of contents",
                "impact": "Very long content may have lower engagement"
            })

        # Heading structure recommendations
        if not analysis["seo_elements"]["has_h1_heading"]:
            recommendations.append({
                "type": "heading_structure",
                "priority": "high",
                "issue": "Missing H1 heading",
                "recommendation": "Add a clear H1 heading with your primary keyword",
                "impact": "H1 tags are crucial for SEO and user experience"
            })

        if not analysis["seo_elements"]["has_h2_headings"]:
            recommendations.append({
                "type": "heading_structure",
                "priority": "medium",
                "issue": "Missing H2 headings",
                "recommendation": "Add H2 headings to structure your content and include keywords",
                "impact": "Proper heading structure improves readability and SEO"
            })

        # Readability recommendations
        if analysis["readability_score"]["score"] < 60:
            recommendations.append({
                "type": "readability",
                "priority": "medium",
                "issue": "Content difficult to read",
                "recommendation": "Use shorter sentences and simpler words to improve readability",
                "impact": "Better readability improves user engagement and SEO"
            })

        # Keyword density recommendations
        top_keywords = analysis["keyword_density"]["top_keywords"]
        if top_keywords:
            max_density = max([kw["density"] for kw in top_keywords])
            if max_density > 5:
                recommendations.append({
                    "type": "keyword_density",
                    "priority": "medium",
                    "issue": "Keyword over-optimization",
                    "recommendation": "Reduce keyword density to 2-3% to avoid keyword stuffing",
                    "impact": "Keyword stuffing can hurt search rankings"
                })

        # Link recommendations
        if not analysis["seo_elements"]["has_internal_links"]:
            recommendations.append({
                "type": "internal_linking",
                "priority": "medium",
                "issue": "No internal links",
                "recommendation": "Add 2-3 internal links to related content",
                "impact": "Internal links help with site navigation and SEO"
            })

        # Image recommendations
        if not analysis["seo_elements"]["has_images"]:
            recommendations.append({
                "type": "images",
                "priority": "low",
                "issue": "No images found",
                "recommendation": "Add relevant images with descriptive alt text",
                "impact": "Images improve user engagement and provide SEO opportunities"
            })

        return recommendations

    def _generate_meta_tags(self, content: str, keywords: List[str]) -> Dict[str, str]:
        """Generate meta tags for the content."""

        # Extract title from H1 or generate one
        h1_match = re.search(r'^# (.+)$', content, re.MULTILINE)
        title = h1_match.group(1) if h1_match else f"{keywords[0].title()} Guide" if keywords else "Complete Guide"

        # Generate meta description from first paragraph
        paragraphs = [p.strip() for p in content.split('\n\n') if p.strip() and not p.startswith('#')]
        first_paragraph = paragraphs[0] if paragraphs else ""

        # Clean and truncate description
        description = re.sub(r'[#*\[\]()]', '', first_paragraph)
        description = description[:155] + "..." if len(description) > 155 else description

        # Generate keywords string
        keywords_string = ", ".join(keywords[:5]) if keywords else ""

        return {
            "title": title,
            "description": description,
            "keywords": keywords_string,
            "og_title": title,
            "og_description": description,
            "twitter_title": title,
            "twitter_description": description
        }

    def _generate_technical_seo_suggestions(self, content_type: str) -> Dict[str, Any]:
        """Generate technical SEO suggestions."""

        return {
            "page_speed": {
                "recommendations": [
                    "Optimize images for web (WebP format, proper sizing)",
                    "Minimize CSS and JavaScript files",
                    "Enable browser caching",
                    "Use a Content Delivery Network (CDN)",
                    "Compress text files with Gzip"
                ],
                "target_score": "90+ on Google PageSpeed Insights"
            },
            "mobile_optimization": {
                "recommendations": [
                    "Ensure responsive design works on all devices",
                    "Use mobile-friendly font sizes (16px minimum)",
                    "Optimize touch targets (44px minimum)",
                    "Test on various mobile devices",
                    "Implement Accelerated Mobile Pages (AMP) if applicable"
                ],
                "importance": "60%+ of searches are on mobile"
            },
            "schema_markup": {
                "recommendations": [
                    "Add Article schema for blog posts",
                    "Implement Organization schema for business pages",
                    "Use Product schema for product pages",
                    "Add FAQ schema for question-based content",
                    "Implement Breadcrumb schema for navigation"
                ],
                "benefit": "Rich snippets in search results"
            },
            "url_structure": {
                "recommendations": [
                    "Use descriptive, keyword-rich URLs",
                    "Keep URLs short and readable",
                    "Use hyphens to separate words",
                    "Avoid special characters and numbers",
                    "Implement proper URL hierarchy"
                ],
                "example": f"/blog/{content_type.replace('_', '-')}-guide"
            },
            "security": {
                "recommendations": [
                    "Implement HTTPS (SSL certificate)",
                    "Keep software and plugins updated",
                    "Use strong passwords and 2FA",
                    "Regular security audits",
                    "Implement proper backup procedures"
                ],
                "importance": "HTTPS is a ranking factor"
            }
        }

    def _generate_improvement_summary(self, current: Dict, optimized: Dict) -> Dict[str, Any]:
        """Generate a summary of improvements made."""

        improvements = []

        # Word count improvement
        word_diff = optimized["word_count"] - current["word_count"]
        if word_diff > 0:
            improvements.append(f"Added {word_diff} words for better content depth")

        # Heading improvements
        current_headings = len(current["headings"]["h1"]) + len(current["headings"]["h2"])
        optimized_headings = len(optimized["headings"]["h1"]) + len(optimized["headings"]["h2"])
        heading_diff = optimized_headings - current_headings
        if heading_diff > 0:
            improvements.append(f"Added {heading_diff} headings for better structure")

        # Readability improvement
        readability_diff = optimized["readability_score"]["score"] - current["readability_score"]["score"]
        if readability_diff > 0:
            improvements.append(f"Improved readability score by {readability_diff} points")

        # SEO elements improvement
        current_seo_score = current["seo_elements"]["structure_score"]
        optimized_seo_score = optimized["seo_elements"]["structure_score"]
        seo_diff = optimized_seo_score - current_seo_score
        if seo_diff > 0:
            improvements.append(f"Enhanced SEO structure score by {seo_diff} points")

        return {
            "improvements_made": improvements,
            "word_count_change": word_diff,
            "readability_improvement": readability_diff,
            "seo_score_improvement": seo_diff,
            "overall_score": min(100, max(0, 60 + (word_diff // 10) + readability_diff + (seo_diff * 5)))
        }
