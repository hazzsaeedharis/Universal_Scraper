"""
Structured data extraction using AI.
Extracts specific data types (menus, business hours, contact info, etc.) into JSON schemas.
"""
import json
from typing import Dict, Any, Optional
import logging

from .groq_client import GroqClient
from ..config import get_settings

logger = logging.getLogger(__name__)


# JSON Schemas for different data types
MENU_SCHEMA = {
    "data_type": "menu",
    "restaurant": "string",
    "categories": [
        {
            "category_name": "string",
            "items": [
                {
                    "name": "string",
                    "description": "string (optional)",
                    "price": "number or string",
                    "currency": "string (e.g., EUR, USD)",
                    "annotations": ["string (e.g., vegan, GF, spicy)"],
                    "calories": "number (optional)"
                }
            ]
        }
    ],
    "notes": "string (optional)"
}

BUSINESS_HOURS_SCHEMA = {
    "data_type": "business_hours",
    "entity": "string",
    "hours": {
        "regular": [
            {"day": "string", "status": "string", "open": "string", "close": "string"}
        ],
        "kitchen": [
            {"day": "string", "status": "string", "open": "string", "close": "string"}
        ]
    },
    "timezone": "string"
}

CONTACT_INFO_SCHEMA = {
    "data_type": "contact_info",
    "entity": "string",
    "phone": "string",
    "email": "string",
    "address": {
        "street": "string",
        "city": "string",
        "postal_code": "string",
        "country": "string"
    },
    "website": "string",
    "social_media": {
        "facebook": "string",
        "instagram": "string",
        "twitter": "string"
    }
}

PRICING_SCHEMA = {
    "data_type": "pricing",
    "entity": "string",
    "items": [
        {
            "name": "string",
            "price": "number",
            "currency": "string",
            "unit": "string (e.g., per hour, per item)"
        }
    ]
}


class StructuredExtractor:
    """Extract structured data from natural language using AI."""
    
    def __init__(self):
        """Initialize the structured extractor."""
        self.groq_client = GroqClient()
        self.settings = get_settings()
        
    def _detect_data_type(self, query: str, context: str) -> str:
        """
        Detect what type of structured data is being requested.
        
        Args:
            query: User's query
            context: Retrieved context
            
        Returns:
            Data type string (menu, business_hours, contact_info, pricing, none)
        """
        query_lower = query.lower()
        context_lower = context.lower()
        
        # Menu detection
        menu_keywords = ['menu', 'food', 'drink', 'dish', 'burger', 'pizza', 'items', 'meal', 'breakfast', 'lunch', 'dinner']
        if any(kw in query_lower for kw in menu_keywords):
            return "menu"
        
        # Business hours detection
        hours_keywords = ['hours', 'open', 'close', 'opening', 'closing', 'schedule', 'when open']
        if any(kw in query_lower for kw in hours_keywords):
            return "business_hours"
        
        # Contact info detection
        contact_keywords = ['contact', 'phone', 'email', 'address', 'location', 'reach']
        if any(kw in query_lower for kw in contact_keywords):
            return "contact_info"
        
        # Pricing detection
        pricing_keywords = ['price', 'cost', 'how much', 'pricing', 'fee']
        if any(kw in query_lower for kw in pricing_keywords):
            return "pricing"
        
        return "none"
    
    def extract(self, query: str, answer: str, context: str = "") -> Dict[str, Any]:
        """
        Extract structured data from query and answer.
        
        Args:
            query: User's query
            answer: AI-generated answer
            context: Optional retrieved context
            
        Returns:
            Dictionary with structured data and metadata
        """
        # Detect data type
        data_type = self._detect_data_type(query, context or answer)
        
        if data_type == "none":
            return {
                "data_type": "none",
                "has_structured_data": False,
                "structured_data": None,
                "confidence": 0.0
            }
        
        # Get appropriate schema
        schema = self._get_schema(data_type)
        
        # Extract structured data
        try:
            structured_data = self._extract_with_schema(answer, context, data_type, schema)
            
            if structured_data:
                return {
                    "data_type": data_type,
                    "has_structured_data": True,
                    "structured_data": structured_data,
                    "confidence": 0.9
                }
        except Exception as e:
            logger.error(f"Structured extraction failed: {e}")
        
        return {
            "data_type": data_type,
            "has_structured_data": False,
            "structured_data": None,
            "confidence": 0.0
        }
    
    def _get_schema(self, data_type: str) -> Dict:
        """Get JSON schema for data type."""
        schemas = {
            "menu": MENU_SCHEMA,
            "business_hours": BUSINESS_HOURS_SCHEMA,
            "contact_info": CONTACT_INFO_SCHEMA,
            "pricing": PRICING_SCHEMA
        }
        return schemas.get(data_type, {})
    
    def _extract_with_schema(self, answer: str, context: str, data_type: str, schema: Dict) -> Optional[Dict]:
        """
        Extract structured data using Groq with schema guidance.
        
        Args:
            answer: AI-generated answer
            context: Retrieved context
            data_type: Type of data to extract
            schema: JSON schema for the data type
            
        Returns:
            Extracted structured data or None
        """
        # Create extraction prompt
        prompt = self._create_extraction_prompt(answer, context, data_type, schema)
        
        # Generate structured JSON
        try:
            json_str = self.groq_client.generate_json(
                prompt=prompt,
                system_message=f"Extract {data_type} data into valid JSON following the provided schema. Be accurate and thorough."
            )
            
            # Parse and validate
            structured_data = json.loads(json_str)
            logger.info(f"✅ Extracted {data_type} data: {len(json_str)} chars")
            return structured_data
            
        except Exception as e:
            logger.error(f"Failed to extract {data_type}: {e}")
            return None
    
    def _create_extraction_prompt(self, answer: str, context: str, data_type: str, schema: Dict) -> str:
        """Create prompt for structured extraction."""
        
        if data_type == "menu":
            return f"""Extract menu information from the following text and return as JSON.

TEXT:
{answer}

{context}

SCHEMA:
{json.dumps(schema, indent=2)}

INSTRUCTIONS:
1. Extract ALL menu items with their prices
2. Group items by category (Burgers, Sides, Drinks, Desserts, etc.)
3. Include descriptions if available
4. Note any special annotations (vegan, GF, spicy, etc.)
5. Include calories if mentioned
6. Use the currency symbol found in the text
7. Be thorough and accurate

Return ONLY valid JSON matching the schema."""

        elif data_type == "business_hours":
            return f"""Extract business hours from the following text and return as JSON.

TEXT:
{answer}

{context}

SCHEMA:
{json.dumps(schema, indent=2)}

INSTRUCTIONS:
1. Extract opening and closing times for each day
2. If kitchen hours differ from regular hours, include both
3. Use 24-hour format (HH:MM)
4. Mark closed days as "closed"
5. Include timezone if mentioned

Return ONLY valid JSON matching the schema."""

        elif data_type == "contact_info":
            return f"""Extract contact information from the following text and return as JSON.

TEXT:
{answer}

{context}

SCHEMA:
{json.dumps(schema, indent=2)}

Return ONLY valid JSON with phone, email, address, website, and social media."""

        elif data_type == "pricing":
            return f"""Extract pricing information from the following text and return as JSON.

TEXT:
{answer}

{context}

SCHEMA:
{json.dumps(schema, indent=2)}

Return ONLY valid JSON with item names, prices, currency, and units."""

        return f"Extract {data_type} data as JSON following this schema: {json.dumps(schema)}"

