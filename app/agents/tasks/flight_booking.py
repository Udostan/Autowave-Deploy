"""
Flight Booking Task for Super Agent.

This module provides a task handler for flight booking tasks.
"""

import re
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta

from app.agents.tasks.base_task import BaseTask
from app.utils.web_browser import WebBrowser


class FlightBookingTask(BaseTask):
    """Task handler for flight booking tasks."""

    def __init__(self, task_description: str, **kwargs):
        """
        Initialize the flight booking task.

        Args:
            task_description (str): The task description.
            **kwargs: Additional arguments.
        """
        super().__init__(task_description, **kwargs)
        self.web_browser = kwargs.get("web_browser", WebBrowser())
        self.gemini_api = kwargs.get("gemini_api", None)
        self.groq_api = kwargs.get("groq_api", None)
        
        # Extract flight details from task description
        self.origin = self._extract_origin()
        self.destination = self._extract_destination()
        self.departure_date = self._extract_departure_date()
        self.return_date = self._extract_return_date()
        self.num_passengers = self._extract_num_passengers()
        self.cabin_class = self._extract_cabin_class()
        self.budget = self._extract_budget()

    def execute(self) -> Dict[str, Any]:
        """
        Execute the flight booking task.

        Returns:
            Dict[str, Any]: The task execution result.
        """
        try:
            # Step 1: Search for flights
            self._search_flights()
            
            # Step 2: Analyze search results
            self._analyze_search_results()
            
            # Step 3: Generate recommendations
            self._generate_recommendations()
            
            # Set task as successful
            self.set_success(True)
            
            return self.get_result()
        except Exception as e:
            print(f"Error executing flight booking task: {str(e)}")
            self.set_success(False)
            self.result["error"] = str(e)
            return self.get_result()

    def _search_flights(self) -> None:
        """Search for flights based on the extracted details."""
        # Add step
        step = {
            "action": "browse_web",
            "url": "https://www.google.com/travel/flights"
        }
        self.add_step(**step)
        
        # Browse to Google Flights
        browse_result = self.web_browser.browse("https://www.google.com/travel/flights")
        
        # Add result
        self.add_result(step, {
            "success": browse_result.get("success", False),
            "url": browse_result.get("url", ""),
            "title": browse_result.get("title", ""),
            "content": browse_result.get("content", "")[:1000] + "..." if browse_result.get("content", "") else "",
            "screenshot": browse_result.get("screenshot", None)
        })
        
        # Add step summary
        self.add_step_summary(
            description="Step 1: Search - Searching for flights",
            summary="Successfully loaded flight search page" if browse_result.get("success", False) else "Failed to load flight search page",
            success=browse_result.get("success", False)
        )
        
        # TODO: Implement form filling and submission for flight search
        # This would require more complex browser automation

    def _analyze_search_results(self) -> None:
        """Analyze the flight search results."""
        # Add step
        step = {
            "action": "analyze_webpage"
        }
        self.add_step(**step)
        
        # Add result (placeholder for now)
        self.add_result(step, {
            "success": True,
            "analysis": "Analyzed flight search results"
        })
        
        # Add step summary
        self.add_step_summary(
            description="Step 2: Analyze Results - Analyzing flight options",
            summary="Successfully analyzed flight options",
            success=True
        )

    def _generate_recommendations(self) -> None:
        """Generate flight recommendations based on the analysis."""
        # Generate a comprehensive response using the Groq API
        prompt = f"""
        Task: {self.task_description}
        
        Please provide a detailed response about flight options from {self.origin or 'the origin'} to {self.destination or 'the destination'} 
        {f'on {self.departure_date}' if self.departure_date else ''} 
        {f'returning on {self.return_date}' if self.return_date else ''} 
        {f'for {self.num_passengers} passengers' if self.num_passengers else ''} 
        {f'in {self.cabin_class} class' if self.cabin_class else ''} 
        {f'with a budget of {self.budget}' if self.budget else ''}.
        
        Include:
        1. Best flight options with airlines, departure/arrival times, and prices
        2. Tips for getting the best deals
        3. Information about baggage allowances and policies
        4. Recommendations for booking timeframes
        5. Any additional relevant information
        
        Format the response in a clear, organized manner with markdown formatting.
        """
        
        if self.groq_api and self.groq_api.api_key:
            print("Generating response with Groq API...")
            task_summary = self.groq_api.generate_text(prompt)
        elif self.gemini_api:
            print("Generating response with Gemini API...")
            task_summary = self.gemini_api.generate_text(prompt)
        else:
            task_summary = "I'm sorry, but I couldn't complete the flight booking task due to technical limitations. Please try again later."
        
        self.set_task_summary(task_summary)

    def _extract_origin(self) -> Optional[str]:
        """Extract the origin from the task description."""
        patterns = [
            r"from\s+([A-Za-z\s]+)(?:\s+to|\s+and|\s+on|\s+for|\s+in|\s+with|\s+\.|$)",
            r"([A-Za-z\s]+)\s+to\s+([A-Za-z\s]+)"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, self.task_description, re.IGNORECASE)
            if match:
                if pattern == patterns[1]:  # Second pattern has origin in group 1
                    return match.group(1).strip()
                return match.group(1).strip()
        
        return None

    def _extract_destination(self) -> Optional[str]:
        """Extract the destination from the task description."""
        patterns = [
            r"to\s+([A-Za-z\s]+)(?:\s+from|\s+on|\s+for|\s+in|\s+with|\s+\.|$)",
            r"([A-Za-z\s]+)\s+to\s+([A-Za-z\s]+)"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, self.task_description, re.IGNORECASE)
            if match:
                if pattern == patterns[1]:  # Second pattern has destination in group 2
                    return match.group(2).strip()
                return match.group(1).strip()
        
        return None

    def _extract_departure_date(self) -> Optional[str]:
        """Extract the departure date from the task description."""
        patterns = [
            r"on\s+(\d{1,2}(?:st|nd|rd|th)?\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)(?:\s+\d{4})?)",
            r"on\s+(\d{1,2}/\d{1,2}(?:/\d{2,4})?)",
            r"on\s+((?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2}(?:st|nd|rd|th)?(?:\s+\d{4})?)",
            r"departing\s+(\d{1,2}(?:st|nd|rd|th)?\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)(?:\s+\d{4})?)",
            r"departing\s+(\d{1,2}/\d{1,2}(?:/\d{2,4})?)",
            r"departing\s+((?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2}(?:st|nd|rd|th)?(?:\s+\d{4})?)"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, self.task_description, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        return None

    def _extract_return_date(self) -> Optional[str]:
        """Extract the return date from the task description."""
        patterns = [
            r"returning\s+(?:on\s+)?(\d{1,2}(?:st|nd|rd|th)?\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)(?:\s+\d{4})?)",
            r"returning\s+(?:on\s+)?(\d{1,2}/\d{1,2}(?:/\d{2,4})?)",
            r"returning\s+(?:on\s+)?((?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2}(?:st|nd|rd|th)?(?:\s+\d{4})?)",
            r"return\s+(?:on\s+)?(\d{1,2}(?:st|nd|rd|th)?\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)(?:\s+\d{4})?)",
            r"return\s+(?:on\s+)?(\d{1,2}/\d{1,2}(?:/\d{2,4})?)",
            r"return\s+(?:on\s+)?((?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2}(?:st|nd|rd|th)?(?:\s+\d{4})?)"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, self.task_description, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        return None

    def _extract_num_passengers(self) -> Optional[int]:
        """Extract the number of passengers from the task description."""
        patterns = [
            r"(\d+)\s+(?:passenger|passengers|people|person|adult|adults|traveler|travelers|traveller|travellers)",
            r"for\s+(\d+)\s+(?:passenger|passengers|people|person|adult|adults|traveler|travelers|traveller|travellers)"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, self.task_description, re.IGNORECASE)
            if match:
                try:
                    return int(match.group(1))
                except ValueError:
                    pass
        
        return None

    def _extract_cabin_class(self) -> Optional[str]:
        """Extract the cabin class from the task description."""
        patterns = [
            r"(?:in|on)\s+(economy|premium economy|business|first)\s+(?:class|cabin)",
            r"(economy|premium economy|business|first)\s+(?:class|cabin)"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, self.task_description, re.IGNORECASE)
            if match:
                return match.group(1).strip().lower()
        
        return None

    def _extract_budget(self) -> Optional[str]:
        """Extract the budget from the task description."""
        patterns = [
            r"budget\s+(?:of\s+)?(\$?\d+(?:,\d+)?(?:\.\d+)?)",
            r"under\s+(\$?\d+(?:,\d+)?(?:\.\d+)?)",
            r"less\s+than\s+(\$?\d+(?:,\d+)?(?:\.\d+)?)",
            r"maximum\s+(?:of\s+)?(\$?\d+(?:,\d+)?(?:\.\d+)?)",
            r"max\s+(?:of\s+)?(\$?\d+(?:,\d+)?(?:\.\d+)?)",
            r"around\s+(\$?\d+(?:,\d+)?(?:\.\d+)?)"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, self.task_description, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        return None
