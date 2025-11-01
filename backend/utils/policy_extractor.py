"""
backend/utils/policy_extractor.py
----------------------------------
Extract information from travel documents (itinerary, ticket, policy) for quote summaries.
"""

import json
import os
import re
from typing import Dict, Any, Optional
from dotenv import load_dotenv

from langchain_groq import ChatGroq

load_dotenv()


def init_llm():
    """Initialize Groq LLM for extraction."""
    return ChatGroq(
        model="llama-3.3-70b-versatile",
        temperature=0.2,
        groq_api_key=os.getenv("GROQ_API_KEY"),
    )


def extract_itinerary_info(llm, pdf_text: str) -> Dict[str, Any]:
    """
    Extract comprehensive travel itinerary information from document.
    
    Returns:
        Dict with all flight and itinerary details
    """
    prompt = f"""You are an expert travel document analyzer. Extract ALL relevant information from this travel itinerary/booking document.

REQUIRED INFORMATION (extract all of these):
1. Traveler Name(s) - ALL passenger names listed
2. Destination - city AND country (e.g., "Tokyo, Japan")
3. Travel Dates - departure date and return date (format: "YYYY-MM-DD to YYYY-MM-DD")
4. Ticket Cost - total booking amount including flight (as a number only, no currency)
5. Duration - trip duration in days
6. Flight Information - airline name and flight number(s)
7. Location(s) - specific locations or cities to visit
8. Activities - planned activities, tours, or experiences
9. Timeline - day-by-day schedule or itinerary highlights
10. Trip Purpose - business, leisure, family, honeymoon, etc.

DOCUMENT TEXT:
{pdf_text[:15000]}

CRITICAL EXTRACTION RULES:
- Extract EVERY field - if information is not found, use "None"
- For multiple travelers: list ALL names separated by commas
- For destination: ALWAYS include city AND country
- For dates: MUST have departure AND return dates
- For cost: extract the total booking amount as a number (look for "Total", "Amount", "Price")
- For duration: calculate days from departure to return
- Be thorough - parse tables, headers, footers, booking confirmations

Return ONLY valid JSON with these EXACT keys:
{{
  "traveler_name": "string or None",
  "destination": "string or None",
  "dates": "string (YYYY-MM-DD to YYYY-MM-DD) or None",
  "trip_cost": number or 0,
  "duration": number or 0,
  "flight_info": "string or None",
  "location": "string or None",
  "activities": "string or None",
  "timeline": "string or None",
  "trip_purpose": "string or None"
}}

Return ONLY the JSON object, no markdown, no explanations."""

    try:
        response = llm.invoke(prompt)
        text = response.content.strip() if hasattr(response, 'content') else str(response).strip()
        text = re.sub(r'```json|```|json\n', '', text).strip()
        result = json.loads(text)
        # Normalize None values
        for key, value in result.items():
            if value in [None, "", "None", "none"]:
                result[key] = None
        return result
    except Exception as e:
        print(f"Error extracting itinerary info: {e}")
        return {
            "traveler_name": None,
            "destination": None,
            "dates": None,
            "trip_cost": 0,
            "duration": None,
            "flight_info": None,
            "location": None,
            "activities": None,
            "timeline": None,
            "trip_purpose": None
        }


def extract_ticket_info(llm, pdf_text: str) -> Dict[str, Any]:
    """
    Extract comprehensive ticket information focusing on personal details.
    
    Returns:
        Dict with passenger_count, passenger_details, special_requirements, dates, duration
    """
    prompt = f"""You are analyzing a travel ticket/booking document. Extract ALL passenger and travel information precisely.

REQUIRED INFORMATION (extract all):
1. Number of Passengers - total count of all travelers
2. Passenger Details - composition as "X adults, Y children, Z infants" 
3. Special Requirements - wheelchair, medical needs, dietary restrictions, special assistance, etc.
4. Traveler Names - ALL passenger names listed
5. Travel Dates - departure date and return date (format: "YYYY-MM-DD to YYYY-MM-DD")
6. Trip Duration - duration in days (calculate from dates)

DOCUMENT TEXT:
{pdf_text[:15000]}

EXTRACTION GUIDELINES:
- Count EVERY passenger listed (including infants as "infant")
- Look for adult/child/infant classifications, ages, or passenger type codes
- Extract ANY special service requests, medical notes, or accessibility needs
- List ALL passenger names if available
- Find departure AND return dates if mentioned in the document
- Calculate duration in days from the dates
- Be thorough - check booking details, passenger manifest, special requests, flight dates

Return ONLY valid JSON with these exact keys:
{{
  "passenger_count": number,
  "passenger_details": "string or None",
  "special_requirements": "string or None",
  "traveler_names": "string or None",
  "dates": "string (YYYY-MM-DD to YYYY-MM-DD) or None",
  "duration": number or 0
}}

Return only the JSON object, no markdown, no explanations."""

    try:
        response = llm.invoke(prompt)
        text = response.content.strip() if hasattr(response, 'content') else str(response).strip()
        text = re.sub(r'```json|```|json\n', '', text).strip()
        result = json.loads(text)
        # Normalize None values
        for key, value in result.items():
            if value in [None, "", "None", "none"]:
                result[key] = None
        return result
    except Exception as e:
        print(f"Error extracting ticket info: {e}")
        return {
            "passenger_count": 1,
            "passenger_details": None,
            "special_requirements": None,
            "traveler_names": None,
            "dates": None,
            "duration": 0
        }


def extract_policy_summary(llm, pdf_text: str) -> Dict[str, Any]:
    """
    Extract key policy information from insurance policy PDF.
    
    Returns:
        Dict with plan_name, medical_coverage, trip_cancellation, price
    """
    prompt = f"""Extract the following information from this travel insurance policy document:

1. Plan/Product Name
2. Medical Coverage Amount (overseas medical expenses coverage)
3. Trip Cancellation Coverage Amount
4. Approximate Price/Premium (if available)

Policy Document:
{pdf_text[:8000]}

Return ONLY a JSON object with these exact keys:
{{
  "plan_name": "string",
  "medical_coverage": "string (e.g., $100,000)",
  "trip_cancellation": "string (e.g., $5,000)",
  "price": "string (e.g., $42.50 or estimate if not found)"
}}

If information is not found, use reasonable defaults based on typical travel insurance standards.
Return only valid JSON, no markdown or extra text."""

    try:
        response = llm.invoke(prompt)
        text = response.content.strip() if hasattr(response, 'content') else str(response).strip()
        text = re.sub(r'```json|```', '', text).strip()
        result = json.loads(text)
        return result
    except Exception as e:
        print(f"Error extracting policy info: {e}")
        return {
            "plan_name": "Travel Insurance Plan",
            "medical_coverage": "$50,000",
            "trip_cancellation": "$2,000",
            "price": "$35.00"
        }


def calculate_dynamic_price(product_name: str, duration_days: int = 7) -> float:
    """
    Calculate dynamic insurance price based on trip duration.
    
    Pricing logic based on typical travel insurance per-day rates:
    - TravelEasy: ~$4.25/day (base) + age/destination factors
    - TravelEasy Pre-Ex: ~$7.13/day (higher for pre-existing conditions)
    - Scootsurance: ~$5.43/day (budget option)
    
    For simplicity, using average daily rates.
    """
    base_rates_per_day = {
        "TravelEasy Policy QTD032212": 4.25,
        "TravelEasy Pre-Ex Policy QTD032212-PX": 7.13,
        "Scootsurance QSR022206_updated": 5.43,
    }
    
    daily_rate = base_rates_per_day.get(product_name, 5.0)
    
    # Minimum 1 week, then pro-rated
    # Typical travel insurance: 1-7 days = same rate, then additional days
    if duration_days <= 7:
        return daily_rate * 7
    elif duration_days <= 30:
        return daily_rate * duration_days
    else:
        # Monthly cap + additional days
        monthly_rate = daily_rate * 30
        additional_days = duration_days - 30
        return monthly_rate + (daily_rate * additional_days * 0.7)


def get_recommended_plan(quotes: list, trip_cost: float = 0) -> str:
    """
    Recommend the best plan based on simple logic.
    
    Logic: Choose based on trip cost and coverage adequacy.
    """
    if not quotes:
        return ""
    
    # For now, use simple logic: cheapest with adequate coverage
    # Later can be enhanced with LLM-based recommendation
    
    # Sort by price (extract numeric value)
    def extract_price(price_str: str) -> float:
        try:
            return float(price_str.replace("$", "").replace(",", ""))
        except:
            return 999999
    
    sorted_quotes = sorted(quotes, key=lambda x: extract_price(x.get("price", "$999")))
    
    # Simple heuristic: if trip cost > $3000, prefer better coverage
    if trip_cost > 3000:
        # Find plan with good medical coverage
        for quote in quotes:
            med_str = quote.get("medical", "$0")
            try:
                med_val = float(med_str.replace("$", "").replace(",", ""))
                if med_val >= 80000:
                    return quote.get("plan", "")
            except:
                pass
    
    # Default: return cheapest
    return sorted_quotes[0].get("plan", "") if sorted_quotes else quotes[0].get("plan", "")

