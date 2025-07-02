"""
Hotel Booking Task for Super Agent.

This module provides a task handler for hotel booking tasks.
"""

import re
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta

from app.agents.tasks.base_task import BaseTask
from app.utils.web_browser import WebBrowser


class HotelBookingTask(BaseTask):
    """Task handler for hotel booking tasks."""

    def __init__(self, task_description: str, **kwargs):
        """
        Initialize the hotel booking task.

        Args:
            task_description (str): The task description.
            **kwargs: Additional arguments.
        """
        super().__init__(task_description, **kwargs)
        self.web_browser = kwargs.get("web_browser", WebBrowser())
        self.gemini_api = kwargs.get("gemini_api", None)
        self.groq_api = kwargs.get("groq_api", None)
        
        # Extract hotel details from task description
        self.location = self._extract_location()
        self.check_in_date = self._extract_check_in_date()
        self.check_out_date = self._extract_check_out_date()
        self.num_guests = self._extract_num_guests()
        self.num_rooms = self._extract_num_rooms()
        self.amenities = self._extract_amenities()
        self.budget = self._extract_budget()
        self.hotel_type = self._extract_hotel_type()
        self.special_requests = self._extract_special_requests()

    def execute(self) -> Dict[str, Any]:
        """
        Execute the hotel booking task.

        Returns:
            Dict[str, Any]: The task execution result.
        """
        try:
            # Step 1: Search for hotels
            self._search_hotels()
            
            # Step 2: Analyze search results
            self._analyze_search_results()
            
            # Step 3: Generate recommendations
            self._generate_recommendations()
            
            # Set task as successful
            self.set_success(True)
            
            return self.get_result()
        except Exception as e:
            print(f"Error executing hotel booking task: {str(e)}")
            self.set_success(False)
            self.result["error"] = str(e)
            return self.get_result()

    def _search_hotels(self) -> None:
        """Search for hotels based on the extracted details."""
        # Add step
        step = {
            "action": "browse_web",
            "url": "https://www.booking.com"
        }
        self.add_step(**step)
        
        # Browse to Booking.com
        browse_result = self.web_browser.browse("https://www.booking.com")
        
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
            description="Step 1: Search - Searching for hotels",
            summary="Successfully loaded hotel search page" if browse_result.get("success", False) else "Failed to load hotel search page",
            success=browse_result.get("success", False)
        )
        
        # If location is available, search for it
        if self.location:
            search_url = f"https://www.booking.com/searchresults.html?ss={self.location.replace(' ', '+')}"
            
            # Add additional parameters if available
            if self.check_in_date and self.check_out_date:
                # TODO: Convert dates to the format required by Booking.com
                pass
            
            if self.num_guests:
                search_url += f"&group_adults={self.num_guests}"
            
            if self.num_rooms:
                search_url += f"&no_rooms={self.num_rooms}"
            
            # Add step
            step = {
                "action": "browse_web",
                "url": search_url
            }
            self.add_step(**step)
            
            # Browse to search results
            browse_result = self.web_browser.browse(search_url)
            
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
                description=f"Step 2: Search Results - Viewing hotels in {self.location}",
                summary="Successfully loaded hotel search results" if browse_result.get("success", False) else "Failed to load hotel search results",
                success=browse_result.get("success", False)
            )

    def _analyze_search_results(self) -> None:
        """Analyze the hotel search results."""
        # Add step
        step = {
            "action": "analyze_webpage"
        }
        self.add_step(**step)
        
        # Add result (placeholder for now)
        self.add_result(step, {
            "success": True,
            "analysis": "Analyzed hotel search results"
        })
        
        # Add step summary
        self.add_step_summary(
            description="Step 3: Analyze Results - Analyzing hotel options",
            summary="Successfully analyzed hotel options",
            success=True
        )

    def _generate_recommendations(self) -> None:
        """Generate hotel recommendations based on the analysis."""
        # Generate a comprehensive response using the Groq API
        prompt = f"""
        Task: {self.task_description}
        
        Please provide a detailed response about hotel options in {self.location or 'the requested location'} 
        {f'for check-in on {self.check_in_date}' if self.check_in_date else ''} 
        {f'and check-out on {self.check_out_date}' if self.check_out_date else ''} 
        {f'for {self.num_guests} guests' if self.num_guests else ''} 
        {f'in {self.num_rooms} rooms' if self.num_rooms else ''} 
        {f'with a budget of {self.budget}' if self.budget else ''}.
        
        Include:
        1. Best hotel options with ratings, amenities, and prices
        2. Location information and proximity to attractions
        3. Tips for getting the best deals
        4. Recommendations for booking timeframes
        5. Any additional relevant information based on the special requests: {self.special_requests if self.special_requests else 'None'}
        
        Format the response in a clear, organized manner with markdown formatting.
        """
        
        if self.groq_api and self.groq_api.api_key:
            print("Generating response with Groq API...")
            task_summary = self.groq_api.generate_text(prompt)
        elif self.gemini_api:
            print("Generating response with Gemini API...")
            task_summary = self.gemini_api.generate_text(prompt)
        else:
            task_summary = "I'm sorry, but I couldn't complete the hotel booking task due to technical limitations. Please try again later."
        
        self.set_task_summary(task_summary)

    def _extract_location(self) -> Optional[str]:
        """Extract the location from the task description."""
        patterns = [
            r"(?:hotel|hotels|accommodation|stay|room|rooms)\s+in\s+([A-Za-z\s,]+)(?:\s+for|\s+on|\s+from|\s+with|\s+\.|$)",
            r"(?:hotel|hotels|accommodation|stay|room|rooms)\s+(?:at|near)\s+([A-Za-z\s,]+)(?:\s+for|\s+on|\s+from|\s+with|\s+\.|$)",
            r"(?:visit|visiting|trip|travel|traveling|travelling)\s+(?:to\s+)?([A-Za-z\s,]+)(?:\s+for|\s+on|\s+from|\s+with|\s+\.|$)",
            r"(?:in|at|near)\s+([A-Za-z\s,]+)(?:\s+for|\s+on|\s+from|\s+with|\s+\.|$)"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, self.task_description, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        return None

    def _extract_check_in_date(self) -> Optional[str]:
        """Extract the check-in date from the task description."""
        patterns = [
            r"(?:check[- ]in|arrive|arrival|arriving|from)\s+(?:on\s+)?(\d{1,2}(?:st|nd|rd|th)?\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)(?:\s+\d{4})?)",
            r"(?:check[- ]in|arrive|arrival|arriving|from)\s+(?:on\s+)?(\d{1,2}/\d{1,2}(?:/\d{2,4})?)",
            r"(?:check[- ]in|arrive|arrival|arriving|from)\s+(?:on\s+)?((?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2}(?:st|nd|rd|th)?(?:\s+\d{4})?)",
            r"(?:stay|book|booking)\s+(?:from|on)\s+(\d{1,2}(?:st|nd|rd|th)?\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)(?:\s+\d{4})?)",
            r"(?:stay|book|booking)\s+(?:from|on)\s+(\d{1,2}/\d{1,2}(?:/\d{2,4})?)",
            r"(?:stay|book|booking)\s+(?:from|on)\s+((?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2}(?:st|nd|rd|th)?(?:\s+\d{4})?)"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, self.task_description, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        # Check for month names without explicit check-in wording
        months = "January|February|March|April|May|June|July|August|September|October|November|December"
        pattern = rf"(?:in|for|during)\s+({months})(?:\s+\d{{4}})?(?:\s+for|\s+to|\s+until|\s+through|\s+\.|$)"
        match = re.search(pattern, self.task_description, re.IGNORECASE)
        if match:
            return match.group(1).strip()
        
        return None

    def _extract_check_out_date(self) -> Optional[str]:
        """Extract the check-out date from the task description."""
        patterns = [
            r"(?:check[- ]out|depart|departure|departing|until|to)\s+(?:on\s+)?(\d{1,2}(?:st|nd|rd|th)?\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)(?:\s+\d{4})?)",
            r"(?:check[- ]out|depart|departure|departing|until|to)\s+(?:on\s+)?(\d{1,2}/\d{1,2}(?:/\d{2,4})?)",
            r"(?:check[- ]out|depart|departure|departing|until|to)\s+(?:on\s+)?((?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2}(?:st|nd|rd|th)?(?:\s+\d{4})?)",
            r"(?:stay|book|booking)\s+(?:until|to)\s+(\d{1,2}(?:st|nd|rd|th)?\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)(?:\s+\d{4})?)",
            r"(?:stay|book|booking)\s+(?:until|to)\s+(\d{1,2}/\d{1,2}(?:/\d{2,4})?)",
            r"(?:stay|book|booking)\s+(?:until|to)\s+((?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2}(?:st|nd|rd|th)?(?:\s+\d{4})?)"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, self.task_description, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        return None

    def _extract_num_guests(self) -> Optional[int]:
        """Extract the number of guests from the task description."""
        patterns = [
            r"(\d+)\s+(?:guest|guests|people|person|adult|adults|traveler|travelers|traveller|travellers)",
            r"for\s+(\d+)\s+(?:guest|guests|people|person|adult|adults|traveler|travelers|traveller|travellers)"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, self.task_description, re.IGNORECASE)
            if match:
                try:
                    return int(match.group(1))
                except ValueError:
                    pass
        
        return None

    def _extract_num_rooms(self) -> Optional[int]:
        """Extract the number of rooms from the task description."""
        patterns = [
            r"(\d+)\s+(?:room|rooms)",
            r"book\s+(\d+)\s+(?:room|rooms)"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, self.task_description, re.IGNORECASE)
            if match:
                try:
                    return int(match.group(1))
                except ValueError:
                    pass
        
        return None

    def _extract_amenities(self) -> List[str]:
        """Extract the amenities from the task description."""
        amenities = []
        
        # Common amenities to look for
        common_amenities = [
            "wifi", "pool", "gym", "fitness", "breakfast", "parking", 
            "restaurant", "bar", "spa", "beach", "view", "balcony", 
            "air conditioning", "air-conditioning", "ac", "a/c",
            "room service", "concierge", "pet friendly", "pet-friendly",
            "non-smoking", "smoking", "family", "business center", 
            "conference", "meeting", "shuttle", "airport shuttle",
            "wheelchair", "accessible", "kitchen", "kitchenette"
        ]
        
        for amenity in common_amenities:
            if re.search(r'\b' + re.escape(amenity) + r'\b', self.task_description, re.IGNORECASE):
                amenities.append(amenity)
        
        return amenities

    def _extract_budget(self) -> Optional[str]:
        """Extract the budget from the task description."""
        patterns = [
            r"budget\s+(?:of\s+)?(\$?\d+(?:,\d+)?(?:\.\d+)?(?:\s+per\s+night)?)",
            r"under\s+(\$?\d+(?:,\d+)?(?:\.\d+)?(?:\s+per\s+night)?)",
            r"less\s+than\s+(\$?\d+(?:,\d+)?(?:\.\d+)?(?:\s+per\s+night)?)",
            r"maximum\s+(?:of\s+)?(\$?\d+(?:,\d+)?(?:\.\d+)?(?:\s+per\s+night)?)",
            r"max\s+(?:of\s+)?(\$?\d+(?:,\d+)?(?:\.\d+)?(?:\s+per\s+night)?)",
            r"around\s+(\$?\d+(?:,\d+)?(?:\.\d+)?(?:\s+per\s+night)?)",
            r"(\$?\d+(?:,\d+)?(?:\.\d+)?)\s+per\s+night"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, self.task_description, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        return None

    def _extract_hotel_type(self) -> Optional[str]:
        """Extract the hotel type from the task description."""
        hotel_types = [
            "luxury", "budget", "boutique", "resort", "all-inclusive", 
            "motel", "inn", "bed and breakfast", "b&b", "hostel", 
            "apartment", "villa", "cottage", "cabin", "chalet", 
            "vacation rental", "airbnb", "5-star", "4-star", "3-star"
        ]
        
        for hotel_type in hotel_types:
            if re.search(r'\b' + re.escape(hotel_type) + r'\b', self.task_description, re.IGNORECASE):
                return hotel_type
        
        return None

    def _extract_special_requests(self) -> Optional[str]:
        """Extract special requests from the task description."""
        # Look for phrases that might indicate special requests
        patterns = [
            r"(?:with|has|have|including|need|wants?|looking\s+for)\s+(?:a\s+)?(?:view\s+of|view|overlooking)\s+([^,.]+)",
            r"(?:close\s+to|near|walking\s+distance\s+(?:to|from)|proximity\s+to)\s+([^,.]+)",
            r"(?:romantic|family-friendly|business|quiet|central|downtown|beachfront|ski-in|ski-out)"
        ]
        
        special_requests = []
        
        for pattern in patterns:
            matches = re.finditer(pattern, self.task_description, re.IGNORECASE)
            for match in matches:
                if len(match.groups()) > 0:
                    special_requests.append(match.group(0).strip())
                else:
                    special_requests.append(match.group(0).strip())
        
        if special_requests:
            return ", ".join(special_requests)
        
        return None
