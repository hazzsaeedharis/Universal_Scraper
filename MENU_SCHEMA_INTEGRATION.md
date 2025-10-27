# Menu Schema Integration Guide

## Overview

This document explains how to integrate the PDF Menu OCR feature with the AI Structured Export feature when merging both branches.

## Flexible Menu Schema

The menu schema should be **flexible** like the business hours schema, allowing AI to add fields dynamically based on what's in the PDF.

### Base Schema (Required Fields)

```python
"menu": {
    "data_type": "menu",
    "restaurant": "string",
    "currency": "EUR",  # or USD, GBP, etc.
    "categories": [
        {
            "name": "Category Name",
            "items": [
                {
                    "name": "Item Name",
                    "price": 12.50,
                    # ... additional fields added dynamically
                }
            ]
        }
    ]
}
```

### Dynamic Fields (AI-Added)

The AI can add these fields if present in the menu:

**Common Fields:**
- `description` - Item description
- `portion` - Portion size (e.g., "250g", "500ml")
- `dietary` - Array of dietary labels ["vegan", "vegetarian", "gluten-free"]
- `allergens` - Array of allergens ["nuts", "dairy", "gluten"]
- `spice_level` - Spiciness (e.g., "mild", "medium", "hot", or 1-5)

**Nutritional Fields (if available):**
- `calories` - Calorie count
- `protein_g` - Protein in grams
- `carbs_g` - Carbohydrates in grams
- `fat_g` - Fat in grams
- `sugar_g` - Sugar in grams

**Additional Fields:**
- `ingredients` - List of ingredients
- `preparation_time` - Prep time (e.g., "15 min")
- `image_url` - URL to item image (if extractable from PDF)
- `popularity` - If menu indicates popular items
- `seasonal` - If marked as seasonal
- `chef_recommended` - Boolean

### Implementation in structured_extractor.py

Update the `SCHEMA_TEMPLATES` dictionary:

```python
"menu": {
    "data_type": "menu",
    "restaurant": "string - name of restaurant",
    "currency": "string - EUR, USD, etc.",
    "categories": [
        {
            "name": "string - category name (Appetizers, Mains, Desserts, Drinks, etc.)",
            "items": [
                {
                    # REQUIRED
                    "name": "string - item name",
                    "price": "number",
                    
                    # OPTIONAL - Add if present in menu
                    "description": "string",
                    "portion": "string - size/weight",
                    "dietary": ["array of dietary labels"],
                    "allergens": ["array of allergens"],
                    "spice_level": "string or number",
                    "calories": "number",
                    "protein_g": "number",
                    "carbs_g": "number",
                    "fat_g": "number",
                    "ingredients": ["array of ingredients"],
                    "seasonal": "boolean",
                    "chef_recommended": "boolean"
                    # AI can add more fields if it finds other structured data
                }
            ]
        }
    ],
    "last_updated": "date - current date",
    "source": "PDF" 
}
```

### AI Prompt for Flexible Extraction

```python
system_prompt = """You are a menu extraction expert. Extract menu information precisely.

CRITICAL RULES:
1. Return ONLY valid JSON
2. Include ALL required fields: name, price, category
3. Add optional fields ONLY if explicitly stated in the text
4. For dietary info, use standard labels: vegetarian, vegan, gluten-free, dairy-free, nut-free
5. Extract ALL available nutritional info (calories, protein, carbs, fat, etc.)
6. If you find additional structured data (e.g., preparation time, spice level), include it
7. Use null for missing optional fields

The schema is flexible - add fields that are present in the menu data."""

user_prompt = f"""Extract the complete menu from this text.

Menu Text:
{text}

Extract into JSON following this base schema, but ADD any additional fields you find:
{{
    "data_type": "menu",
    "restaurant": "name",
    "currency": "EUR/USD/etc",
    "categories": [
        {{
            "name": "category",
            "items": [
                {{
                    "name": "required",
                    "price": "required",
                    "description": "if available",
                    "calories": "if available",
                    "dietary": ["if available"],
                    "allergens": ["if available"],
                    ...additional fields as needed
                }}
            ]
        }}
    ]
}}

Return ONLY the JSON, no other text."""
```

### Frontend Rendering (StructuredDataViewer.jsx)

Add menu-specific rendering:

```javascript
// In renderTableView() method:
if (dataType === 'menu' && data.categories) {
  return (
    <div className="space-y-6">
      {data.restaurant && (
        <h3 className="text-lg font-semibold">{data.restaurant}</h3>
      )}
      
      {data.categories.map((category, catIdx) => (
        <div key={catIdx} className="space-y-3">
          <h4 className="text-md font-semibold text-primary">
            {category.name} ({category.items.length} items)
          </h4>
          
          <div className="border rounded-lg overflow-hidden">
            <table className="w-full text-sm">
              <thead className="bg-muted">
                <tr>
                  <th className="px-4 py-2 text-left">Item</th>
                  <th className="px-4 py-2 text-left">Price</th>
                  {/* Dynamically add columns if data exists */}
                  {category.items[0]?.calories && <th className="px-4 py-2">Calories</th>}
                  {category.items[0]?.dietary && <th className="px-4 py-2">Dietary</th>}
                  {category.items[0]?.description && <th className="px-4 py-2 text-left">Description</th>}
                </tr>
              </thead>
              <tbody>
                {category.items.map((item, idx) => (
                  <tr key={idx} className="border-t hover:bg-accent/30">
                    <td className="px-4 py-2 font-medium">{item.name}</td>
                    <td className="px-4 py-2">{data.currency} {item.price}</td>
                    
                    {/* Dynamic columns */}
                    {item.calories && (
                      <td className="px-4 py-2 text-center">{item.calories}</td>
                    )}
                    {item.dietary && (
                      <td className="px-4 py-2">
                        {item.dietary.map((d, i) => (
                          <Badge key={i} variant="outline" className="mr-1">
                            {d}
                          </Badge>
                        ))}
                      </td>
                    )}
                    {item.description && (
                      <td className="px-4 py-2 text-muted-foreground text-xs">
                        {item.description}
                      </td>
                    )}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      ))}
    </div>
  )
}
```

## Integration Steps

1. Merge `pdf-menu-ocr` branch into main (PDF extraction working)
2. Merge `ai-structured-export` branch into main (structured extraction working)
3. Update `structured_extractor.py` with flexible menu schema (as shown above)
4. Update `StructuredDataViewer.jsx` with menu rendering (as shown above)
5. Test with real restaurant PDF menus

## Testing

Test with various menu types:
- Simple text menu (prices only)
- Detailed menu (with descriptions)
- Health-conscious menu (with calories, allergens)
- International menu (multiple languages)
- Multi-page menu (categories spread across pages)

## Benefits of Flexible Schema

- **Adaptable**: Works with minimal menus and detailed menus
- **Future-proof**: AI can extract new field types without code changes
- **Accurate**: Only includes data actually present in the menu
- **Export-friendly**: Any structure can be exported to JSON/CSV

