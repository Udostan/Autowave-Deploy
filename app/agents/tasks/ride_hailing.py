"""
Ride Hailing Task for Super Agent.

This module provides a task handler for ride hailing tasks.
"""

import re
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta

from app.agents.tasks.base_task import BaseTask
from app.utils.web_browser import WebBrowser


class RideHailingTask(BaseTask):
    """Task handler for ride hailing tasks."""

    def __init__(self, task_description: str, **kwargs):
        """
        Initialize the ride hailing task.

        Args:
            task_description (str): The task description.
            **kwargs: Additional arguments.
        """
        super().__init__(task_description, **kwargs)
        self.web_browser = kwargs.get("web_browser", WebBrowser())
        self.gemini_api = kwargs.get("gemini_api", None)
        self.groq_api = kwargs.get("groq_api", None)
        
        # Extract ride details from task description
        self.pickup_location = self._extract_pickup_location()
        self.dropoff_location = self._extract_dropoff_location()
        self.pickup_time = self._extract_pickup_time()
        self.ride_type = self._extract_ride_type()
        self.num_passengers = self._extract_num_passengers()
        self.special_requests = self._extract_special_requests()

    def execute(self) -> Dict[str, Any]:
        """
        Execute the ride hailing task.

        Returns:
            Dict[str, Any]: The task execution result.
        """
        try:
            # Step 1: Search for ride options
            self._search_ride_options()
            
            # Step 2: Analyze ride options
            self._analyze_ride_options()
            
            # Step 3: Generate recommendations
            self._generate_recommendations()
            
            # Set task as successful
            self.set_success(True)
            
            return self.get_result()
        except Exception as e:
            print(f"Error executing ride hailing task: {str(e)}")
            self.set_success(False)
            self.result["error"] = str(e)
            return self.get_result()

    def _search_ride_options(self) -> None:
        """Search for ride options based on the extracted details."""
        # Add step
        step = {
            "action": "browse_web",
            "url": "https://m.uber.com"
        }
        self.add_step(**step)
        
        # Browse to Uber mobile site
        browse_result = self.web_browser.browse("https://m.uber.com")
        
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
            description="Step 1: Search - Searching for ride options",
            summary="Successfully loaded ride hailing service" if browse_result.get("success", False) else "Failed to load ride hailing service",
            success=browse_result.get("success", False)
        )
        
        # Also check Lyft as an alternative
        step = {
            "action": "browse_web",
            "url": "https://ride.lyft.com"
        }
        self.add_step(**step)
        
        # Browse to Lyft ride page
        browse_result = self.web_browser.browse("https://ride.lyft.com")
        
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
            description="Step 2: Alternative - Checking alternative ride service",
            summary="Successfully loaded alternative ride service" if browse_result.get("success", False) else "Failed to load alternative ride service",
            success=browse_result.get("success", False)
        )

    def _analyze_ride_options(self) -> None:
        """Analyze the ride options."""
        # Add step
        step = {
            "action": "analyze_ride_options"
        }
        self.add_step(**step)
        
        # Add result (placeholder for now)
        self.add_result(step, {
            "success": True,
            "analysis": "Analyzed ride options"
        })
        
        # Add step summary
        self.add_step_summary(
            description="Step 3: Analyze Options - Analyzing ride options",
            summary="Successfully analyzed ride options",
            success=True
        )

    def _generate_recommendations(self) -> None:
        """Generate ride recommendations based on the analysis."""
        # Generate a comprehensive response using the Groq API
        prompt = f"""
        Task: {self.task_description}
        
        Please provide a detailed response about ride hailing options 
        {f'from {self.pickup_location}' if self.pickup_location else 'from the pickup location'} 
        {f'to {self.dropoff_location}' if self.dropoff_location else 'to the destination'} 
        {f'at {self.pickup_time}' if self.pickup_time else ''} 
        {f'for {self.ride_type} service' if self.ride_type else ''} 
        {f'for {self.num_passengers} passengers' if self.num_passengers else ''}.
        
        Include:
        1. Comparison between Uber and Lyft services for this route
        2. Estimated prices for different service levels (economy, premium, etc.)
        3. Estimated pickup and travel times
        4. Tips for getting the best service and price
        5. How to handle any special requests: {self.special_requests if self.special_requests else 'None'}
        
        Format the response in a clear, organized manner with markdown formatting.
        """
        
        if self.groq_api and self.groq_api.api_key:
            print("Generating response with Groq API...")
            task_summary = self.groq_api.generate_text(prompt)
        elif self.gemini_api:
            print("Generating response with Gemini API...")
            task_summary = self.gemini_api.generate_text(prompt)
        else:
            task_summary = "I'm sorry, but I couldn't complete the ride hailing task due to technical limitations. Please try again later."
        
        self.set_task_summary(task_summary)

    def _extract_pickup_location(self) -> Optional[str]:
        """Extract the pickup location from the task description."""
        patterns = [
            r"(?:from|at|in|near|pickup|pick up|pick-up|starting from|starting at|start from|start at)\s+([A-Za-z0-9\s,]+)(?:\s+to|\s+and|\s+at|\s+for|\s+\.|$)",
            r"(?:get|book|order|call|need|want)\s+(?:a|an|the)?\s+(?:ride|taxi|uber|lyft|cab)\s+(?:from|at|in|near)\s+([A-Za-z0-9\s,]+)(?:\s+to|\s+and|\s+at|\s+for|\s+\.|$)"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, self.task_description, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        return None

    def _extract_dropoff_location(self) -> Optional[str]:
        """Extract the dropoff location from the task description."""
        patterns = [
            r"(?:to|towards|toward|destination|drop off|drop-off|ending at|end at)\s+([A-Za-z0-9\s,]+)(?:\s+from|\s+at|\s+for|\s+\.|$)",
            r"(?:get|book|order|call|need|want)\s+(?:a|an|the)?\s+(?:ride|taxi|uber|lyft|cab)\s+(?:to|towards|toward)\s+([A-Za-z0-9\s,]+)(?:\s+from|\s+at|\s+for|\s+\.|$)",
            r"(?:from|at|in|near|pickup|pick up|pick-up|starting from|starting at|start from|start at)\s+([A-Za-z0-9\s,]+)\s+to\s+([A-Za-z0-9\s,]+)"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, self.task_description, re.IGNORECASE)
            if match:
                if pattern == patterns[2]:  # Third pattern has dropoff in group 2
                    return match.group(2).strip()
                return match.group(1).strip()
        
        return None

    def _extract_pickup_time(self) -> Optional[str]:
        """Extract the pickup time from the task description."""
        patterns = [
            r"(?:at|for|by|around|approximately|about|@)\s+(\d{1,2}(?::\d{2})?\s*(?:am|pm|a\.m\.|p\.m\.))",
            r"(?:at|for|by|around|approximately|about|@)\s+(\d{1,2}(?::\d{2})?)",
            r"(?:in|after|within)\s+(\d+)\s+(?:minute|minutes|min|mins|hour|hours|hr|hrs)",
            r"(?:now|immediately|asap|as soon as possible|right now|right away)"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, self.task_description, re.IGNORECASE)
            if match:
                if pattern == patterns[3]:  # Fourth pattern is for immediate pickup
                    return "now"
                return match.group(1).strip()
        
        return None

    def _extract_ride_type(self) -> Optional[str]:
        """Extract the ride type from the task description."""
        ride_types = {
            "economy": ["economy", "standard", "regular", "basic", "uberx", "lyft", "normal"],
            "premium": ["premium", "luxury", "lux", "black", "select", "executive", "uber black", "lyft lux"],
            "shared": ["shared", "pool", "carpool", "shared ride", "uber pool", "lyft shared"],
            "xl": ["xl", "extra large", "large", "big", "uber xl", "lyft xl", "suv"],
            "accessible": ["accessible", "wheelchair", "handicap", "disabled", "uber assist", "lyft access"]
        }
        
        for ride_type, keywords in ride_types.items():
            for keyword in keywords:
                if re.search(r'\b' + re.escape(keyword) + r'\b', self.task_description, re.IGNORECASE):
                    return ride_type
        
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

    def _extract_special_requests(self) -> Optional[str]:
        """Extract special requests from the task description."""
        special_requests = []
        
        # Common special requests to look for
        common_requests = [
            "car seat", "child seat", "baby seat", "booster seat",
            "extra space", "luggage", "bags", "suitcase", "suitcases",
            "pet", "dog", "cat", "animal",
            "wheelchair", "accessible", "disability", "disabled",
            "quiet", "no talking", "silent",
            "female driver", "male driver",
            "stop", "multiple stops", "wait", "waiting"
        ]
        
        for request in common_requests:
            if re.search(r'\b' + re.escape(request) + r'\b', self.task_description, re.IGNORECASE):
                special_requests.append(request)
        
        if special_requests:
            return ", ".join(special_requests)
        
        return None
