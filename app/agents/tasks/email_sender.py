"""
Email Sender Task for Super Agent.

This module provides a task handler for email sending tasks.
"""

import re
from typing import Dict, Any, Optional, List

from app.agents.tasks.base_task import BaseTask
from app.utils.web_browser import WebBrowser


class EmailSenderTask(BaseTask):
    """Task handler for email sending tasks."""

    def __init__(self, task_description: str, **kwargs):
        """
        Initialize the email sender task.

        Args:
            task_description (str): The task description.
            **kwargs: Additional arguments.
        """
        super().__init__(task_description, **kwargs)
        self.web_browser = kwargs.get("web_browser", WebBrowser())
        self.gemini_api = kwargs.get("gemini_api", None)
        self.groq_api = kwargs.get("groq_api", None)
        
        # Extract email details from task description
        self.recipient = self._extract_recipient()
        self.subject = self._extract_subject()
        self.content_type = self._extract_content_type()
        self.tone = self._extract_tone()
        self.purpose = self._extract_purpose()
        self.key_points = self._extract_key_points()

    def execute(self) -> Dict[str, Any]:
        """
        Execute the email sending task.

        Returns:
            Dict[str, Any]: The task execution result.
        """
        try:
            # Step 1: Generate email content
            self._generate_email_content()
            
            # Step 2: Prepare email draft
            self._prepare_email_draft()
            
            # Set task as successful
            self.set_success(True)
            
            return self.get_result()
        except Exception as e:
            print(f"Error executing email sender task: {str(e)}")
            self.set_success(False)
            self.result["error"] = str(e)
            return self.get_result()

    def _generate_email_content(self) -> None:
        """Generate email content based on the task description."""
        # Add step
        step = {
            "action": "generate_email_content"
        }
        self.add_step(**step)
        
        # Generate email content using Groq API or Gemini API
        prompt = f"""
        Task: {self.task_description}
        
        Please write a professional email with the following details:
        
        Recipient: {self.recipient or 'Not specified'}
        Subject: {self.subject or 'Not specified'}
        Content Type: {self.content_type or 'General'}
        Tone: {self.tone or 'Professional'}
        Purpose: {self.purpose or 'Not specified'}
        Key Points: {', '.join(self.key_points) if self.key_points else 'Not specified'}
        
        The email should be well-structured with:
        1. A proper greeting
        2. Clear and concise body paragraphs
        3. A professional closing
        4. Your name/signature
        
        Please format the email in a way that it can be directly copied and pasted into an email client.
        """
        
        if self.groq_api and self.groq_api.api_key:
            print("Generating email content with Groq API...")
            email_content = self.groq_api.generate_text(prompt)
        elif self.gemini_api:
            print("Generating email content with Gemini API...")
            email_content = self.gemini_api.generate_text(prompt)
        else:
            email_content = "I'm sorry, but I couldn't generate the email content due to technical limitations. Please try again later."
        
        # Add result
        self.add_result(step, {
            "success": True,
            "email_content": email_content
        })
        
        # Store the email content for later use
        self.result["email_content"] = email_content
        
        # Add step summary
        self.add_step_summary(
            description="Step 1: Generate Email - Creating email content",
            summary="Successfully generated email content",
            success=True
        )

    def _prepare_email_draft(self) -> None:
        """Prepare an email draft using a webmail service."""
        # Add step
        step = {
            "action": "prepare_email_draft"
        }
        self.add_step(**step)
        
        # Generate instructions for manually sending the email
        instructions = f"""
        ## Email Draft Ready

        I've prepared an email draft based on your request. Here's how you can send it:

        1. Copy the email content below
        2. Open your preferred email client (Gmail, Outlook, etc.)
        3. Create a new email
        4. Set the recipient to: {self.recipient or 'Your intended recipient'}
        5. Set the subject to: {self.subject or 'Your subject line'}
        6. Paste the email content into the body
        7. Review the email for any final adjustments
        8. Send the email

        ### Email Content:

        ```
        {self.result.get('email_content', 'Email content not available')}
        ```

        Would you like me to make any changes to this email draft?
        """
        
        # Add result
        self.add_result(step, {
            "success": True,
            "instructions": instructions
        })
        
        # Set task summary
        self.set_task_summary(instructions)
        
        # Add step summary
        self.add_step_summary(
            description="Step 2: Prepare Draft - Creating email draft",
            summary="Successfully prepared email draft with instructions",
            success=True
        )

    def _extract_recipient(self) -> Optional[str]:
        """Extract the recipient from the task description."""
        patterns = [
            r"(?:to|for|with)\s+([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})",
            r"email\s+(?:to|for)\s+([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})",
            r"email\s+([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})",
            r"([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, self.task_description, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        # Check for names without email addresses
        patterns = [
            r"(?:to|for)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)",
            r"email\s+(?:to|for)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, self.task_description, re.IGNORECASE)
            if match:
                # Make sure we're not matching common words
                recipient = match.group(1).strip()
                common_words = ["me", "you", "him", "her", "them", "someone", "anybody", "everyone"]
                if recipient.lower() not in common_words:
                    return recipient
        
        return None

    def _extract_subject(self) -> Optional[str]:
        """Extract the subject from the task description."""
        patterns = [
            r"subject[:\s]+\"([^\"]+)\"",
            r"subject[:\s]+\'([^\']+)\'",
            r"subject[:\s]+([^,.]+)",
            r"about\s+\"([^\"]+)\"",
            r"about\s+\'([^\']+)\'",
            r"about\s+([^,.]+)",
            r"regarding\s+\"([^\"]+)\"",
            r"regarding\s+\'([^\']+)\'",
            r"regarding\s+([^,.]+)"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, self.task_description, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        return None

    def _extract_content_type(self) -> Optional[str]:
        """Extract the content type from the task description."""
        content_types = {
            "formal": ["formal", "official", "business", "professional"],
            "informal": ["informal", "casual", "friendly", "personal"],
            "thank you": ["thank you", "thanks", "appreciation", "grateful"],
            "request": ["request", "asking for", "inquiry", "enquiry", "question"],
            "invitation": ["invitation", "invite", "inviting", "attend", "join"],
            "follow-up": ["follow-up", "follow up", "following up", "checking in"],
            "complaint": ["complaint", "complain", "issue", "problem", "concern"],
            "application": ["application", "apply", "applying", "job application", "position"],
            "resignation": ["resignation", "resign", "resigning", "notice", "leaving"],
            "introduction": ["introduction", "introduce", "introducing", "new", "meet"]
        }
        
        for content_type, keywords in content_types.items():
            for keyword in keywords:
                if re.search(r'\b' + re.escape(keyword) + r'\b', self.task_description, re.IGNORECASE):
                    return content_type
        
        return None

    def _extract_tone(self) -> Optional[str]:
        """Extract the tone from the task description."""
        tones = {
            "professional": ["professional", "business", "formal", "official"],
            "friendly": ["friendly", "casual", "informal", "personal", "warm"],
            "urgent": ["urgent", "immediate", "asap", "as soon as possible", "quickly"],
            "apologetic": ["apologetic", "apology", "sorry", "regret", "apologize"],
            "enthusiastic": ["enthusiastic", "excited", "enthusiastic", "passionate", "eager"],
            "grateful": ["grateful", "thankful", "appreciative", "thanks", "thank you"],
            "assertive": ["assertive", "firm", "strong", "direct", "straightforward"],
            "persuasive": ["persuasive", "convincing", "compelling", "persuade", "convince"],
            "sympathetic": ["sympathetic", "empathetic", "understanding", "compassionate", "caring"]
        }
        
        for tone, keywords in tones.items():
            for keyword in keywords:
                if re.search(r'\b' + re.escape(keyword) + r'\b', self.task_description, re.IGNORECASE):
                    return tone
        
        return None

    def _extract_purpose(self) -> Optional[str]:
        """Extract the purpose from the task description."""
        # Look for phrases that might indicate the purpose
        patterns = [
            r"(?:to|for)\s+(?:the\s+)?(?:purpose\s+of\s+)?([^,.]+)",
            r"(?:in\s+order\s+to|so\s+that|so\s+as\s+to)\s+([^,.]+)",
            r"(?:asking|requesting|inquiring|enquiring)\s+(?:about|for)\s+([^,.]+)",
            r"(?:informing|notifying|telling)\s+(?:about|of)\s+([^,.]+)",
            r"(?:thanking|expressing\s+gratitude)\s+(?:for)\s+([^,.]+)"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, self.task_description, re.IGNORECASE)
            if match:
                purpose = match.group(1).strip()
                # Filter out common phrases that aren't actually purposes
                common_phrases = ["me", "you", "him", "her", "them", "someone", "anybody", "everyone"]
                if purpose.lower() not in common_phrases and len(purpose.split()) > 1:
                    return purpose
        
        return None

    def _extract_key_points(self) -> List[str]:
        """Extract key points from the task description."""
        key_points = []
        
        # Look for bullet points or numbered lists
        patterns = [
            r"(?:points|details|information|include|mention|discuss)(?:[:\s]+)([^.]+)",
            r"(?:•|\*|\-|\d+\.)\s+([^.]+)"
        ]
        
        for pattern in patterns:
            matches = re.finditer(pattern, self.task_description, re.IGNORECASE)
            for match in matches:
                key_points.append(match.group(1).strip())
        
        # If no structured points found, try to extract sentences that might be key points
        if not key_points:
            sentences = re.split(r'[.!?]', self.task_description)
            for sentence in sentences:
                sentence = sentence.strip()
                if 5 < len(sentence.split()) < 15 and sentence not in ["", "I", "me", "you", "he", "she", "they"]:
                    key_points.append(sentence)
        
        return key_points[:5]  # Limit to 5 key points
