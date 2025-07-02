"""
Email Campaign Manager Tools

This module provides tools for creating email campaigns with subject lines,
body content, and A/B testing suggestions.
"""

import logging
import json
import random
import sys
import os
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta

# Import the API modules using relative imports
try:
    from ...api.gemini import GeminiAPI
    from ...api.groq import GroqAPI
except ImportError:
    # Fallback if imports fail
    GeminiAPI = None
    GroqAPI = None

logger = logging.getLogger(__name__)

class EmailTools:
    """Tools for email campaign management and creation."""

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
                self.logger.info("Gemini API initialized for email tools")
        except Exception as e:
            self.logger.warning(f"Failed to initialize Gemini API: {e}")

        try:
            if GroqAPI and not self.llm_available:
                self.groq_api = GroqAPI()
                self.llm_available = True
                self.logger.info("Groq API initialized for email tools")
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

    def create_email_campaign(
        self,
        campaign_topic: str,
        target_audience: str = "general",
        campaign_type: str = "promotional",
        tone: str = "professional",
        include_ab_testing: bool = True,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Create a complete email campaign with subject lines, body content, and A/B testing suggestions.

        Args:
            campaign_topic: The main topic or purpose of the email campaign
            target_audience: The target audience (e.g., "millennials", "business professionals", "customers")
            campaign_type: Type of campaign (promotional, newsletter, welcome, abandoned_cart, etc.)
            tone: Tone of the email (professional, casual, friendly, urgent, etc.)
            include_ab_testing: Whether to include A/B testing suggestions

        Returns:
            Dict containing the complete email campaign
        """
        try:
            self.logger.info(f"Creating email campaign for topic: {campaign_topic}")

            # Generate subject lines
            subject_lines = self._generate_subject_lines(campaign_topic, campaign_type, tone)

            # Generate email body content
            email_body = self._generate_email_body(campaign_topic, target_audience, campaign_type, tone)

            # Generate A/B testing suggestions if requested
            ab_testing = None
            if include_ab_testing:
                ab_testing = self._generate_ab_testing_suggestions(subject_lines, campaign_type)

            # Generate performance metrics and recommendations
            metrics = self._generate_performance_metrics(campaign_type, target_audience)

            # Generate send time recommendations
            send_times = self._generate_send_time_recommendations(target_audience, campaign_type)

            campaign = {
                "campaign_topic": campaign_topic,
                "target_audience": target_audience,
                "campaign_type": campaign_type,
                "tone": tone,
                "subject_lines": subject_lines,
                "email_body": email_body,
                "ab_testing": ab_testing,
                "performance_metrics": metrics,
                "send_times": send_times,
                "created_at": datetime.now().isoformat()
            }

            self.logger.info(f"Successfully created email campaign: {campaign_topic}")
            return campaign

        except Exception as e:
            self.logger.error(f"Error creating email campaign: {str(e)}")
            return {
                "error": f"Failed to create email campaign: {str(e)}",
                "campaign_topic": campaign_topic
            }

    def _generate_subject_lines(self, topic: str, campaign_type: str, tone: str) -> List[Dict[str, Any]]:
        """Generate multiple subject line variations using LLM or templates."""

        # Try LLM first
        if self.llm_available:
            return self._generate_subject_lines_llm(topic, campaign_type, tone)

        # Fallback to templates
        return self._generate_subject_lines_template(topic, campaign_type, tone)

    def _generate_subject_lines_llm(self, topic: str, campaign_type: str, tone: str) -> List[Dict[str, Any]]:
        """Generate subject lines using LLM."""

        prompt = f"""Create 5 compelling email subject lines for a {campaign_type} email campaign about "{topic}".

Campaign Details:
- Topic: {topic}
- Campaign Type: {campaign_type}
- Tone: {tone}

Requirements:
- Each subject line should be unique and engaging
- Keep them under 60 characters for mobile optimization
- Match the {tone} tone
- Optimize for {campaign_type} campaign goals
- Include variety in approach (urgency, curiosity, benefit-focused, etc.)

Return the response as a JSON array with this format:
[
  {{
    "text": "Subject line text",
    "character_count": 45,
    "predicted_open_rate": 28.5,
    "tone": "{tone}",
    "urgency_level": "medium",
    "approach": "benefit-focused"
  }}
]

Generate exactly 5 subject lines:"""

        try:
            response = self._call_llm(prompt, temperature=0.8)
            if response:
                # Try to parse JSON response
                import json
                subject_lines_data = json.loads(response)

                # Add variation labels
                for i, subject_line in enumerate(subject_lines_data):
                    subject_line["variation"] = f"Version {chr(65 + i)}"  # A, B, C, etc.

                return subject_lines_data
        except Exception as e:
            self.logger.warning(f"LLM subject line generation failed: {e}")

        # Fallback to template method
        return self._generate_subject_lines_template(topic, campaign_type, tone)

    def _generate_subject_lines_template(self, topic: str, campaign_type: str, tone: str) -> List[Dict[str, Any]]:
        """Generate subject lines using templates (fallback method)."""

        # Subject line templates based on campaign type and tone
        templates = {
            "promotional": {
                "professional": [
                    f"Exclusive Offer: {topic}",
                    f"Limited Time: {topic} - Don't Miss Out",
                    f"Special Savings on {topic}",
                    f"Your {topic} Discount Awaits",
                    f"Act Now: {topic} Sale Ends Soon"
                ],
                "casual": [
                    f"🎉 Amazing {topic} Deal Inside!",
                    f"Hey! Your {topic} discount is here",
                    f"Don't sleep on this {topic} offer",
                    f"Last chance for {topic} savings!",
                    f"You'll love this {topic} deal"
                ],
                "urgent": [
                    f"URGENT: {topic} Sale Ends Tonight!",
                    f"Final Hours: {topic} Discount",
                    f"⏰ Last Call for {topic}",
                    f"ENDING SOON: {topic} Offer",
                    f"Don't Miss Out: {topic} - 24hrs Left"
                ]
            },
            "newsletter": {
                "professional": [
                    f"Weekly Update: {topic}",
                    f"This Week in {topic}",
                    f"Your {topic} Newsletter",
                    f"Latest {topic} Insights",
                    f"{topic} Roundup - Week of {datetime.now().strftime('%B %d')}"
                ],
                "casual": [
                    f"What's new in {topic}? 📰",
                    f"Your weekly {topic} fix is here!",
                    f"Catching up on {topic}",
                    f"The {topic} scoop you've been waiting for",
                    f"Fresh {topic} content just for you"
                ]
            },
            "welcome": {
                "professional": [
                    f"Welcome to {topic}",
                    f"Getting Started with {topic}",
                    f"Your {topic} Journey Begins",
                    f"Thank You for Joining {topic}",
                    f"Welcome Aboard - {topic} Awaits"
                ],
                "friendly": [
                    f"Welcome to the {topic} family! 👋",
                    f"So excited you joined {topic}!",
                    f"Your {topic} adventure starts now",
                    f"Hey there! Welcome to {topic}",
                    f"You're in! Let's explore {topic} together"
                ]
            }
        }

        # Get appropriate templates
        campaign_templates = templates.get(campaign_type, templates["promotional"])
        tone_templates = campaign_templates.get(tone, campaign_templates.get("professional", []))

        # Generate subject lines with metadata
        subject_lines = []
        for i, template in enumerate(tone_templates[:5]):  # Limit to 5 variations
            subject_lines.append({
                "text": template,
                "variation": f"Version {chr(65 + i)}",  # A, B, C, etc.
                "character_count": len(template),
                "predicted_open_rate": random.uniform(15, 35),  # Simulated prediction
                "tone": tone,
                "urgency_level": "high" if "urgent" in tone or any(word in template.lower() for word in ["urgent", "last", "final", "ending"]) else "medium"
            })

        return subject_lines

    def _generate_email_body(self, topic: str, audience: str, campaign_type: str, tone: str) -> Dict[str, Any]:
        """Generate email body content using LLM or templates."""

        # Try LLM first
        if self.llm_available:
            body = self._generate_email_body_llm(topic, audience, campaign_type, tone)
            if body:
                return {
                    "html_content": body["html"],
                    "text_content": body["text"],
                    "word_count": len(body["text"].split()),
                    "estimated_read_time": f"{max(1, len(body['text'].split()) // 200)} min",
                    "cta_count": body["cta_count"],
                    "personalization_tags": body["personalization_tags"]
                }

        # Fallback to templates
        if campaign_type == "promotional":
            body = self._generate_promotional_email(topic, audience, tone)
        elif campaign_type == "newsletter":
            body = self._generate_newsletter_email(topic, audience, tone)
        elif campaign_type == "welcome":
            body = self._generate_welcome_email(topic, audience, tone)
        else:
            body = self._generate_general_email(topic, audience, tone)

        return {
            "html_content": body["html"],
            "text_content": body["text"],
            "word_count": len(body["text"].split()),
            "estimated_read_time": f"{max(1, len(body['text'].split()) // 200)} min",
            "cta_count": body["cta_count"],
            "personalization_tags": body["personalization_tags"]
        }

    def _generate_email_body_llm(self, topic: str, audience: str, campaign_type: str, tone: str) -> Dict[str, Any]:
        """Generate email body content using LLM."""

        prompt = f"""Create a compelling {campaign_type} email about "{topic}" for {audience}.

Campaign Details:
- Topic: {topic}
- Target Audience: {audience}
- Campaign Type: {campaign_type}
- Tone: {tone}

Requirements:
- Create both HTML and plain text versions
- Include appropriate greeting and closing
- Add relevant call-to-action buttons/links
- Make it engaging and {tone} in tone
- Optimize for {campaign_type} campaign goals
- Include personalization placeholders like {{{{first_name}}}}
- Keep it concise but informative (200-400 words)

Return the response as JSON with this exact format:
{{
  "html": "Complete HTML email content with inline styles",
  "text": "Plain text version of the email",
  "cta_count": 2,
  "personalization_tags": ["{{{{first_name}}}}", "{{{{company}}}}"]
}}

Generate the email content:"""

        try:
            response = self._call_llm(prompt, temperature=0.7)
            if response:
                import json
                # Try to extract JSON from response
                if "```json" in response:
                    json_start = response.find("```json") + 7
                    json_end = response.find("```", json_start)
                    response = response[json_start:json_end].strip()
                elif "{" in response and "}" in response:
                    # Extract JSON from response
                    json_start = response.find("{")
                    json_end = response.rfind("}") + 1
                    response = response[json_start:json_end]

                email_data = json.loads(response)
                return email_data
        except Exception as e:
            self.logger.warning(f"LLM email body generation failed: {e}")

        return None

    def _generate_promotional_email(self, topic: str, audience: str, tone: str) -> Dict[str, Any]:
        """Generate promotional email content."""

        greeting = "Hi there!" if tone == "casual" else "Dear Valued Customer,"

        html_content = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <h1 style="color: #333; text-align: center;">Special Offer: {topic}</h1>

            <p>{greeting}</p>

            <p>We're excited to share an exclusive offer on {topic} just for you!</p>

            <div style="background: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0;">
                <h2 style="color: #007bff; margin-top: 0;">🎉 Limited Time Offer</h2>
                <p><strong>Save 25% on {topic}</strong></p>
                <p>Use code: <strong>SAVE25</strong></p>
            </div>

            <p>This offer is perfect for {audience} who want to get the most out of {topic}.</p>

            <div style="text-align: center; margin: 30px 0;">
                <a href="#" style="background: #007bff; color: white; padding: 15px 30px; text-decoration: none; border-radius: 5px; display: inline-block;">
                    Shop Now
                </a>
            </div>

            <p><em>Offer expires in 48 hours. Don't miss out!</em></p>

            <p>Best regards,<br>The {topic} Team</p>
        </div>
        """

        text_content = f"""
        Special Offer: {topic}

        {greeting}

        We're excited to share an exclusive offer on {topic} just for you!

        LIMITED TIME OFFER
        Save 25% on {topic}
        Use code: SAVE25

        This offer is perfect for {audience} who want to get the most out of {topic}.

        [Shop Now - Link]

        Offer expires in 48 hours. Don't miss out!

        Best regards,
        The {topic} Team
        """

        return {
            "html": html_content,
            "text": text_content,
            "cta_count": 1,
            "personalization_tags": ["{{first_name}}", "{{audience_type}}"]
        }

    def _generate_newsletter_email(self, topic: str, audience: str, tone: str) -> Dict[str, Any]:
        """Generate newsletter email content."""

        greeting = "Hey there!" if tone == "casual" else "Hello,"

        html_content = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <h1 style="color: #333; text-align: center;">Your {topic} Update</h1>

            <p>{greeting}</p>

            <p>Here's what's happening in the world of {topic} this week:</p>

            <div style="border-left: 4px solid #007bff; padding-left: 20px; margin: 20px 0;">
                <h3>📈 Trending Now</h3>
                <p>Latest developments in {topic} that {audience} should know about.</p>
            </div>

            <div style="border-left: 4px solid #28a745; padding-left: 20px; margin: 20px 0;">
                <h3>💡 Pro Tip</h3>
                <p>Expert advice on maximizing your {topic} experience.</p>
            </div>

            <div style="border-left: 4px solid #ffc107; padding-left: 20px; margin: 20px 0;">
                <h3>🎯 Featured Resource</h3>
                <p>Check out our latest guide on {topic} best practices.</p>
                <a href="#" style="color: #007bff;">Read More →</a>
            </div>

            <p>That's all for this week! Stay tuned for more {topic} insights.</p>

            <p>Best,<br>The {topic} Team</p>
        </div>
        """

        text_content = f"""
        Your {topic} Update

        {greeting}

        Here's what's happening in the world of {topic} this week:

        TRENDING NOW
        Latest developments in {topic} that {audience} should know about.

        PRO TIP
        Expert advice on maximizing your {topic} experience.

        FEATURED RESOURCE
        Check out our latest guide on {topic} best practices.
        [Read More - Link]

        That's all for this week! Stay tuned for more {topic} insights.

        Best,
        The {topic} Team
        """

        return {
            "html": html_content,
            "text": text_content,
            "cta_count": 1,
            "personalization_tags": ["{{first_name}}", "{{week_date}}"]
        }

    def _generate_welcome_email(self, topic: str, audience: str, tone: str) -> Dict[str, Any]:
        """Generate welcome email content."""

        greeting = "Welcome aboard!" if tone == "casual" else "Welcome!"

        html_content = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <h1 style="color: #333; text-align: center;">🎉 {greeting}</h1>

            <p>We're thrilled to have you join our {topic} community!</p>

            <p>As a new member, here's what you can expect:</p>

            <ul style="line-height: 1.6;">
                <li>Exclusive access to {topic} resources</li>
                <li>Regular updates and insights</li>
                <li>Special offers just for {audience}</li>
                <li>Expert tips and best practices</li>
            </ul>

            <div style="background: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0; text-align: center;">
                <h3 style="margin-top: 0;">🚀 Get Started</h3>
                <p>Ready to dive into {topic}? Here's your first step:</p>
                <a href="#" style="background: #28a745; color: white; padding: 15px 30px; text-decoration: none; border-radius: 5px; display: inline-block;">
                    Explore Now
                </a>
            </div>

            <p>If you have any questions, don't hesitate to reach out. We're here to help!</p>

            <p>Welcome to the family,<br>The {topic} Team</p>
        </div>
        """

        text_content = f"""
        {greeting}

        We're thrilled to have you join our {topic} community!

        As a new member, here's what you can expect:

        • Exclusive access to {topic} resources
        • Regular updates and insights
        • Special offers just for {audience}
        • Expert tips and best practices

        GET STARTED
        Ready to dive into {topic}? Here's your first step:
        [Explore Now - Link]

        If you have any questions, don't hesitate to reach out. We're here to help!

        Welcome to the family,
        The {topic} Team
        """

        return {
            "html": html_content,
            "text": text_content,
            "cta_count": 1,
            "personalization_tags": ["{{first_name}}", "{{signup_date}}"]
        }

    def _generate_general_email(self, topic: str, audience: str, tone: str) -> Dict[str, Any]:
        """Generate general email content."""

        greeting = "Hi!" if tone == "casual" else "Hello,"

        html_content = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <h1 style="color: #333; text-align: center;">About {topic}</h1>

            <p>{greeting}</p>

            <p>We wanted to share some important information about {topic} with you.</p>

            <p>This is particularly relevant for {audience} who are interested in staying updated.</p>

            <div style="background: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0;">
                <h3 style="margin-top: 0;">Key Points:</h3>
                <ul>
                    <li>Important updates about {topic}</li>
                    <li>How this affects {audience}</li>
                    <li>Next steps and recommendations</li>
                </ul>
            </div>

            <div style="text-align: center; margin: 30px 0;">
                <a href="#" style="background: #007bff; color: white; padding: 15px 30px; text-decoration: none; border-radius: 5px; display: inline-block;">
                    Learn More
                </a>
            </div>

            <p>Thank you for your attention to this matter.</p>

            <p>Best regards,<br>The Team</p>
        </div>
        """

        text_content = f"""
        About {topic}

        {greeting}

        We wanted to share some important information about {topic} with you.

        This is particularly relevant for {audience} who are interested in staying updated.

        Key Points:
        • Important updates about {topic}
        • How this affects {audience}
        • Next steps and recommendations

        [Learn More - Link]

        Thank you for your attention to this matter.

        Best regards,
        The Team
        """

        return {
            "html": html_content,
            "text": text_content,
            "cta_count": 1,
            "personalization_tags": ["{{first_name}}"]
        }

    def _generate_ab_testing_suggestions(self, subject_lines: List[Dict], campaign_type: str) -> Dict[str, Any]:
        """Generate A/B testing suggestions."""

        return {
            "test_variations": {
                "subject_lines": {
                    "variation_a": subject_lines[0] if subject_lines else {"text": "Default Subject"},
                    "variation_b": subject_lines[1] if len(subject_lines) > 1 else {"text": "Alternative Subject"},
                    "test_metric": "open_rate",
                    "sample_size": "50% each variation",
                    "duration": "24 hours"
                },
                "send_times": {
                    "variation_a": "9:00 AM",
                    "variation_b": "2:00 PM",
                    "test_metric": "click_through_rate",
                    "sample_size": "50% each variation",
                    "duration": "1 week"
                },
                "content": {
                    "variation_a": "Short, concise content",
                    "variation_b": "Detailed, comprehensive content",
                    "test_metric": "conversion_rate",
                    "sample_size": "50% each variation",
                    "duration": "2 weeks"
                }
            },
            "recommendations": [
                "Test subject lines first as they have the biggest impact on open rates",
                "Ensure statistical significance with at least 1000 recipients per variation",
                "Run tests for at least 24 hours to account for different time zones",
                "Only test one element at a time for clear results",
                f"For {campaign_type} campaigns, focus on testing call-to-action placement"
            ],
            "success_metrics": {
                "open_rate": {"good": ">25%", "excellent": ">35%"},
                "click_rate": {"good": ">3%", "excellent": ">5%"},
                "conversion_rate": {"good": ">2%", "excellent": ">5%"},
                "unsubscribe_rate": {"good": "<0.5%", "excellent": "<0.2%"}
            }
        }

    def _generate_performance_metrics(self, campaign_type: str, audience: str) -> Dict[str, Any]:
        """Generate expected performance metrics and benchmarks."""

        # Industry benchmarks (simulated realistic ranges)
        benchmarks = {
            "promotional": {
                "open_rate": {"min": 18, "max": 28, "average": 23},
                "click_rate": {"min": 2, "max": 5, "average": 3.5},
                "conversion_rate": {"min": 1, "max": 4, "average": 2.5}
            },
            "newsletter": {
                "open_rate": {"min": 20, "max": 35, "average": 27},
                "click_rate": {"min": 3, "max": 7, "average": 5},
                "conversion_rate": {"min": 0.5, "max": 2, "average": 1.2}
            },
            "welcome": {
                "open_rate": {"min": 40, "max": 60, "average": 50},
                "click_rate": {"min": 8, "max": 15, "average": 12},
                "conversion_rate": {"min": 3, "max": 8, "average": 5.5}
            }
        }

        campaign_benchmarks = benchmarks.get(campaign_type, benchmarks["promotional"])

        return {
            "expected_performance": {
                "open_rate": f"{campaign_benchmarks['open_rate']['average']}%",
                "click_rate": f"{campaign_benchmarks['click_rate']['average']}%",
                "conversion_rate": f"{campaign_benchmarks['conversion_rate']['average']}%",
                "bounce_rate": "<2%",
                "unsubscribe_rate": "<0.5%"
            },
            "industry_benchmarks": {
                "open_rate_range": f"{campaign_benchmarks['open_rate']['min']}-{campaign_benchmarks['open_rate']['max']}%",
                "click_rate_range": f"{campaign_benchmarks['click_rate']['min']}-{campaign_benchmarks['click_rate']['max']}%",
                "conversion_rate_range": f"{campaign_benchmarks['conversion_rate']['min']}-{campaign_benchmarks['conversion_rate']['max']}%"
            },
            "optimization_tips": [
                "Personalize subject lines to increase open rates by 26%",
                "Segment your audience for 14% higher click rates",
                "Use clear, action-oriented CTAs",
                "Optimize for mobile (60% of emails are opened on mobile)",
                "Test send times for your specific audience"
            ],
            "kpis_to_track": [
                "Open Rate", "Click-Through Rate", "Conversion Rate",
                "Revenue per Email", "List Growth Rate", "Unsubscribe Rate"
            ]
        }

    def _generate_send_time_recommendations(self, audience: str, campaign_type: str) -> Dict[str, Any]:
        """Generate optimal send time recommendations."""

        # Audience-based recommendations
        audience_times = {
            "business professionals": {
                "best_days": ["Tuesday", "Wednesday", "Thursday"],
                "best_times": ["9:00 AM", "1:00 PM", "3:00 PM"],
                "avoid": ["Monday mornings", "Friday afternoons", "Weekends"]
            },
            "millennials": {
                "best_days": ["Tuesday", "Wednesday", "Saturday"],
                "best_times": ["10:00 AM", "2:00 PM", "7:00 PM"],
                "avoid": ["Monday mornings", "Friday evenings"]
            },
            "general": {
                "best_days": ["Tuesday", "Wednesday", "Thursday"],
                "best_times": ["10:00 AM", "2:00 PM", "8:00 PM"],
                "avoid": ["Monday mornings", "Friday afternoons"]
            }
        }

        # Campaign type adjustments
        campaign_adjustments = {
            "promotional": "Send during business hours for B2B, evenings for B2C",
            "newsletter": "Consistent weekly schedule works best",
            "welcome": "Send immediately after signup for best engagement"
        }

        audience_key = audience.lower() if audience.lower() in audience_times else "general"
        audience_data = audience_times[audience_key]

        return {
            "recommended_schedule": {
                "primary_send_time": f"{random.choice(audience_data['best_days'])} at {random.choice(audience_data['best_times'])}",
                "alternative_times": [
                    f"{day} at {time}"
                    for day in audience_data['best_days'][:2]
                    for time in audience_data['best_times'][:2]
                ],
                "frequency": self._get_frequency_recommendation(campaign_type)
            },
            "audience_insights": {
                "target_audience": audience,
                "best_days": audience_data['best_days'],
                "best_times": audience_data['best_times'],
                "times_to_avoid": audience_data['avoid']
            },
            "campaign_specific": {
                "type": campaign_type,
                "recommendation": campaign_adjustments.get(campaign_type, "Follow general best practices")
            },
            "timezone_considerations": [
                "Consider your audience's primary timezone",
                "For global audiences, segment by region",
                "Test different times for international campaigns",
                "Use recipient's local time when possible"
            ]
        }

    def _get_frequency_recommendation(self, campaign_type: str) -> str:
        """Get frequency recommendation based on campaign type."""

        frequencies = {
            "promotional": "1-2 times per week maximum",
            "newsletter": "Weekly or bi-weekly",
            "welcome": "One-time, then follow-up sequence",
            "abandoned_cart": "3-email sequence over 1 week",
            "re_engagement": "Monthly for inactive subscribers"
        }

        return frequencies.get(campaign_type, "Weekly or bi-weekly")
