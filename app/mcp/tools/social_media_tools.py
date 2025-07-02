"""
Social Media Tools for MCP Server.
These tools handle social media content generation for different platforms.
"""

import logging
import json
import random
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class SocialMediaTools:
    """
    Tools for generating optimized content for different social media platforms.
    """

    def __init__(self):
        """Initialize the social media tools."""
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

        # Initialize supported platforms
        self.platforms = {
            "twitter": {
                "max_length": 280,
                "optimal_hashtags": 2,
                "tone": "concise, engaging",
                "format": "text, links, hashtags"
            },
            "linkedin": {
                "max_length": 3000,
                "optimal_hashtags": 3,
                "tone": "professional, informative",
                "format": "text, links, hashtags, mentions"
            },
            "instagram": {
                "max_length": 2200,
                "optimal_hashtags": 10,
                "tone": "visual, inspirational",
                "format": "text, emojis, hashtags"
            },
            "facebook": {
                "max_length": 63206,
                "optimal_hashtags": 2,
                "tone": "conversational, personal",
                "format": "text, links, images, videos"
            },
            "tiktok": {
                "max_length": 2200,
                "optimal_hashtags": 5,
                "tone": "trendy, authentic",
                "format": "text, emojis, hashtags"
            }
        }

    def generate_content(self, topic: str, platforms: List[str] = None, 
                         tone: str = None, include_hashtags: bool = True,
                         include_schedule: bool = True) -> Dict[str, Any]:
        """
        Generate optimized content for different social media platforms.

        Args:
            topic: The main topic or message to create content for
            platforms: List of platforms to generate content for (defaults to all)
            tone: Optional tone override for the content
            include_hashtags: Whether to include hashtag recommendations
            include_schedule: Whether to include posting schedule recommendations

        Returns:
            Dictionary containing generated content for each platform
        """
        self.logger.info(f"Generating social media content for topic: {topic}")

        # If no platforms specified, use all supported platforms
        if not platforms:
            platforms = list(self.platforms.keys())
        else:
            # Normalize platform names
            platforms = [p.lower().strip() for p in platforms]
            # Filter out unsupported platforms
            platforms = [p for p in platforms if p in self.platforms]
            if not platforms:
                platforms = ["twitter", "linkedin", "instagram"]  # Default to these if none valid

        # Generate content using LLM
        try:
            content_by_platform = self._generate_content_with_llm(
                topic, platforms, tone, include_hashtags
            )
        except Exception as e:
            self.logger.warning(f"Failed to generate content with LLM: {str(e)}. Using fallback.")
            content_by_platform = self._generate_fallback_content(
                topic, platforms, tone, include_hashtags
            )

        # Generate posting schedule if requested
        schedule = None
        if include_schedule:
            schedule = self._generate_posting_schedule(platforms)

        # Prepare the result
        result = {
            "topic": topic,
            "content": content_by_platform,
            "schedule": schedule if include_schedule else None
        }

        return result

    def _generate_content_with_llm(self, topic: str, platforms: List[str], 
                                 tone: str = None, include_hashtags: bool = True) -> Dict[str, Any]:
        """
        Generate social media content using LLM API.

        Args:
            topic: The main topic or message
            platforms: List of platforms to generate for
            tone: Optional tone override
            include_hashtags: Whether to include hashtags

        Returns:
            Dictionary with content for each platform
        """
        if not hasattr(self, 'has_llm_api') or not self.has_llm_api:
            if not hasattr(self, 'has_groq_api') or not self.has_groq_api:
                raise Exception("No LLM API available")

        content_by_platform = {}

        for platform in platforms:
            platform_info = self.platforms.get(platform, self.platforms["twitter"])
            
            # Create a prompt for the LLM
            platform_tone = tone or platform_info["tone"]
            max_length = platform_info["max_length"]
            
            prompt = f"""
            Generate optimized social media content for {platform.capitalize()}.
            
            Topic: {topic}
            
            Requirements:
            - Maximum length: {max_length} characters
            - Tone: {platform_tone}
            - Format: {platform_info['format']}
            - Include {platform_info['optimal_hashtags']} relevant hashtags: {'Yes' if include_hashtags else 'No'}
            
            The content should be engaging, shareable, and optimized for the platform.
            Return ONLY the content, no explanations or additional text.
            """
            
            try:
                if hasattr(self, 'gemini_api') and self.has_llm_api:
                    response = self.gemini_api.generate_text(prompt)
                    content = response.strip()
                elif hasattr(self, 'groq_api') and self.has_groq_api:
                    response = self.groq_api.generate_text(prompt)
                    content = response.strip()
                else:
                    raise Exception("No LLM API available")
                
                # Extract hashtags if included
                hashtags = []
                if include_hashtags:
                    hashtags = self._extract_hashtags(content)
                
                content_by_platform[platform] = {
                    "content": content,
                    "hashtags": hashtags,
                    "character_count": len(content)
                }
            except Exception as e:
                self.logger.error(f"Error generating content for {platform}: {str(e)}")
                # Use fallback for this platform
                content_by_platform[platform] = self._generate_fallback_content_for_platform(
                    topic, platform, tone, include_hashtags
                )
        
        return content_by_platform

    def _generate_fallback_content(self, topic: str, platforms: List[str], 
                                 tone: str = None, include_hashtags: bool = True) -> Dict[str, Any]:
        """
        Generate fallback content when LLM API fails.

        Args:
            topic: The main topic or message
            platforms: List of platforms to generate for
            tone: Optional tone override
            include_hashtags: Whether to include hashtags

        Returns:
            Dictionary with fallback content for each platform
        """
        content_by_platform = {}
        
        for platform in platforms:
            content_by_platform[platform] = self._generate_fallback_content_for_platform(
                topic, platform, tone, include_hashtags
            )
            
        return content_by_platform

    def _generate_fallback_content_for_platform(self, topic: str, platform: str, 
                                              tone: str = None, include_hashtags: bool = True) -> Dict[str, Any]:
        """
        Generate fallback content for a specific platform.

        Args:
            topic: The main topic or message
            platform: The platform to generate for
            tone: Optional tone override
            include_hashtags: Whether to include hashtags

        Returns:
            Dictionary with content for the platform
        """
        platform_info = self.platforms.get(platform, self.platforms["twitter"])
        
        # Generate simple content based on platform
        if platform == "twitter":
            content = f"Check out our latest update on {topic}! #trending"
        elif platform == "linkedin":
            content = f"We're excited to share our latest insights on {topic}. This development represents a significant advancement in our field. What are your thoughts on this topic?"
        elif platform == "instagram":
            content = f"✨ New post alert! ✨\n\nExploring {topic} today and loving every moment! Double tap if you're as excited as we are!\n\n#trending #inspiration"
        elif platform == "facebook":
            content = f"We've been working on something special related to {topic} and can't wait to share it with our community! Let us know what you think in the comments below."
        elif platform == "tiktok":
            content = f"POV: When you discover {topic} for the first time 😮 #fyp #trending"
        else:
            content = f"Check out our latest update on {topic}!"
            
        # Generate hashtags if requested
        hashtags = []
        if include_hashtags:
            topic_words = topic.lower().split()
            potential_hashtags = [
                "trending", "viral", "new", "innovation", "technology", 
                "business", "marketing", "socialmedia", "digital", "growth",
                "success", "motivation", "inspiration", "creativity"
            ]
            potential_hashtags.extend([word.strip(",.!?") for word in topic_words if len(word) > 3])
            
            # Select random hashtags based on platform's optimal number
            num_hashtags = min(platform_info["optimal_hashtags"], len(potential_hashtags))
            hashtags = random.sample(potential_hashtags, num_hashtags)
            
        return {
            "content": content,
            "hashtags": hashtags,
            "character_count": len(content)
        }

    def _extract_hashtags(self, content: str) -> List[str]:
        """
        Extract hashtags from content.

        Args:
            content: The content to extract hashtags from

        Returns:
            List of hashtags
        """
        hashtags = []
        words = content.split()
        
        for word in words:
            if word.startswith("#"):
                # Remove any punctuation at the end
                hashtag = word.rstrip(",.!?:;'\"")
                if hashtag not in hashtags:
                    hashtags.append(hashtag)
                    
        return hashtags

    def _generate_posting_schedule(self, platforms: List[str]) -> Dict[str, Any]:
        """
        Generate an optimal posting schedule for the platforms.

        Args:
            platforms: List of platforms to generate schedule for

        Returns:
            Dictionary with posting schedule for each platform
        """
        schedule = {}
        
        # Best times to post by platform (simplified)
        best_times = {
            "twitter": ["8:00 AM", "12:00 PM", "5:00 PM"],
            "linkedin": ["9:00 AM", "12:00 PM", "5:30 PM"],
            "instagram": ["11:00 AM", "1:00 PM", "7:00 PM"],
            "facebook": ["9:00 AM", "1:00 PM", "3:00 PM"],
            "tiktok": ["9:00 AM", "12:00 PM", "7:00 PM"]
        }
        
        # Best days to post by platform (simplified)
        best_days = {
            "twitter": ["Monday", "Wednesday", "Friday"],
            "linkedin": ["Tuesday", "Wednesday", "Thursday"],
            "instagram": ["Wednesday", "Thursday", "Friday"],
            "facebook": ["Thursday", "Friday", "Saturday"],
            "tiktok": ["Tuesday", "Thursday", "Saturday"]
        }
        
        # Generate schedule for each platform
        today = datetime.now()
        
        for platform in platforms:
            platform_schedule = []
            
            # Get best times and days for this platform
            times = best_times.get(platform, best_times["twitter"])
            days = best_days.get(platform, best_days["twitter"])
            
            # Generate 3 posting times
            for i in range(3):
                # Get day offset (0-6 days from today)
                day_offset = i % 7
                post_date = today + timedelta(days=day_offset)
                day_name = post_date.strftime("%A")
                
                # If this isn't one of the best days, find the next best day
                if day_name not in days:
                    # Find the next best day
                    next_best_day_index = 0
                    while day_offset < 7:
                        day_offset += 1
                        post_date = today + timedelta(days=day_offset)
                        day_name = post_date.strftime("%A")
                        if day_name in days:
                            break
                
                # Get a time for this day
                time = times[i % len(times)]
                
                platform_schedule.append({
                    "day": day_name,
                    "date": post_date.strftime("%Y-%m-%d"),
                    "time": time
                })
            
            schedule[platform] = platform_schedule
            
        return schedule
