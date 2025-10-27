"""
Export endpoints for structured data (JSON, CSV, Markdown).
"""
from fastapi import APIRouter, HTTPException, Response
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Dict, Any, Optional
import json
import io
import csv

from ...utils.logger import setup_logger

logger = setup_logger(__name__)
router = APIRouter(prefix="/export", tags=["export"])


class ExportRequest(BaseModel):
    """Request model for data export."""
    data: Dict[str, Any]
    format: str = "json"  # json, csv, markdown
    filename: Optional[str] = None


def dict_to_csv(data: Dict[str, Any]) -> str:
    """Convert structured data to CSV format."""
    output = io.StringIO()
    
    data_type = data.get("data_type", "unknown")
    
    if data_type == "menu":
        # Menu CSV format
        writer = csv.writer(output)
        writer.writerow(["Category", "Item", "Description", "Price", "Currency", "Annotations", "Calories"])
        
        for category in data.get("categories", []):
            cat_name = category.get("category_name", "")
            for item in category.get("items", []):
                writer.writerow([
                    cat_name,
                    item.get("name", ""),
                    item.get("description", ""),
                    item.get("price", ""),
                    item.get("currency", ""),
                    ", ".join(item.get("annotations", [])),
                    item.get("calories", "")
                ])
    
    elif data_type == "business_hours":
        # Business hours CSV
        writer = csv.writer(output)
        writer.writerow(["Day", "Type", "Status", "Open", "Close"])
        
        hours = data.get("hours", {})
        for day_info in hours.get("regular", []):
            writer.writerow([
                day_info.get("day", ""),
                "Regular",
                day_info.get("status", ""),
                day_info.get("open", ""),
                day_info.get("close", "")
            ])
        
        for day_info in hours.get("kitchen", []):
            writer.writerow([
                day_info.get("day", ""),
                "Kitchen",
                day_info.get("status", ""),
                day_info.get("open", ""),
                day_info.get("close", "")
            ])
    
    elif data_type == "pricing":
        # Pricing CSV
        writer = csv.writer(output)
        writer.writerow(["Item", "Price", "Currency", "Unit"])
        
        for item in data.get("items", []):
            writer.writerow([
                item.get("name", ""),
                item.get("price", ""),
                item.get("currency", ""),
                item.get("unit", "")
            ])
    
    else:
        # Generic CSV for other types
        writer = csv.writer(output)
        writer.writerow(["Key", "Value"])
        for key, value in data.items():
            writer.writerow([key, str(value)])
    
    return output.getvalue()


def dict_to_markdown(data: Dict[str, Any]) -> str:
    """Convert structured data to Markdown format."""
    lines = []
    data_type = data.get("data_type", "unknown")
    
    if data_type == "menu":
        lines.append(f"# Menu: {data.get('restaurant', 'Unknown')}\n")
        
        for category in data.get("categories", []):
            lines.append(f"\n## {category.get('category_name', 'Items')}\n")
            
            for item in category.get("items", []):
                price_str = f"{item.get('price', '')} {item.get('currency', '')}"
                lines.append(f"### {item.get('name', '')} - {price_str}\n")
                
                if item.get('description'):
                    lines.append(f"{item['description']}\n")
                
                if item.get('annotations'):
                    lines.append(f"*{', '.join(item['annotations'])}*\n")
                
                if item.get('calories'):
                    lines.append(f"**Calories:** {item['calories']}\n")
                
                lines.append("")
        
        if data.get('notes'):
            lines.append(f"\n---\n*{data['notes']}*\n")
    
    elif data_type == "business_hours":
        lines.append(f"# Business Hours: {data.get('entity', 'Unknown')}\n")
        lines.append("\n## Regular Hours\n")
        lines.append("| Day | Status | Hours |")
        lines.append("|-----|--------|-------|")
        
        for day_info in data.get("hours", {}).get("regular", []):
            status = day_info.get("status", "")
            if status == "open":
                hours = f"{day_info.get('open', '')} - {day_info.get('close', '')}"
            else:
                hours = "Closed"
            lines.append(f"| {day_info.get('day', '')} | {status} | {hours} |")
        
        if data.get("hours", {}).get("kitchen"):
            lines.append("\n## Kitchen Hours\n")
            lines.append("| Day | Status | Hours |")
            lines.append("|-----|--------|-------|")
            
            for day_info in data["hours"]["kitchen"]:
                status = day_info.get("status", "")
                if status == "open":
                    hours = f"{day_info.get('open', '')} - {day_info.get('close', '')}"
                else:
                    hours = "Closed"
                lines.append(f"| {day_info.get('day', '')} | {status} | {hours} |")
    
    else:
        # Generic markdown
        lines.append(f"# {data_type.replace('_', ' ').title()}\n")
        lines.append(f"```json\n{json.dumps(data, indent=2)}\n```")
    
    return "\n".join(lines)


@router.post("/")
async def export_data(request: ExportRequest):
    """
    Export structured data in various formats.
    
    Args:
        request: Export request with data, format, and filename
        
    Returns:
        File download response
    """
    try:
        data = request.data
        export_format = request.format.lower()
        
        # Generate filename
        data_type = data.get("data_type", "export")
        default_filename = f"{data_type}_{data.get('entity', 'data')}"
        filename = request.filename or default_filename
        
        # Convert based on format
        if export_format == "json":
            content = json.dumps(data, indent=2, ensure_ascii=False)
            media_type = "application/json"
            filename = f"{filename}.json"
        
        elif export_format == "csv":
            content = dict_to_csv(data)
            media_type = "text/csv"
            filename = f"{filename}.csv"
        
        elif export_format == "markdown" or export_format == "md":
            content = dict_to_markdown(data)
            media_type = "text/markdown"
            filename = f"{filename}.md"
        
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported format: {export_format}")
        
        # Return as downloadable file
        return Response(
            content=content.encode('utf-8'),
            media_type=media_type,
            headers={
                'Content-Disposition': f'attachment; filename="{filename}"'
            }
        )
    
    except Exception as e:
        logger.error(f"Export error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

