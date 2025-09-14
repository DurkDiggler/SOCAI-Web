"""API endpoints for SOC Agent web interface."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from .database import (
    Alert,
    get_alerts,
    get_alert_by_id,
    get_alert_statistics,
    get_db,
    get_top_event_types,
    get_top_ips,
    get_top_sources,
    update_alert_status,
)

logger = logging.getLogger(__name__)

# Create API router
api_router = APIRouter(prefix="/api/v1", tags=["alerts"])


@api_router.get("/alerts", response_model=Dict[str, Any])
async def get_alerts_endpoint(
    skip: int = Query(0, ge=0, description="Number of alerts to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of alerts to return"),
    status: Optional[str] = Query(None, description="Filter by status"),
    severity: Optional[int] = Query(None, ge=0, le=10, description="Filter by severity"),
    source: Optional[str] = Query(None, description="Filter by source"),
    category: Optional[str] = Query(None, description="Filter by category"),
    search: Optional[str] = Query(None, description="Search in message, IP, username, or event type"),
    db: Session = Depends(get_db)
):
    """Get alerts with filtering and pagination."""
    try:
        alerts = get_alerts(
            db=db,
            skip=skip,
            limit=limit,
            status=status,
            severity=severity,
            source=source,
            category=category,
            search=search
        )
        
        # Get total count for pagination
        total_count = db.query(Alert).count()
        
        return {
            "alerts": [alert.to_dict() for alert in alerts],
            "pagination": {
                "skip": skip,
                "limit": limit,
                "total": total_count,
                "has_more": skip + limit < total_count
            }
        }
    except Exception as e:
        logger.error(f"Error fetching alerts: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch alerts")


@api_router.get("/alerts/{alert_id}", response_model=Dict[str, Any])
async def get_alert_endpoint(
    alert_id: int,
    db: Session = Depends(get_db)
):
    """Get a specific alert by ID."""
    alert = get_alert_by_id(db, alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    return {"alert": alert.to_dict()}


@api_router.patch("/alerts/{alert_id}/status")
async def update_alert_status_endpoint(
    alert_id: int,
    status: str = Query(..., description="New status"),
    assigned_to: Optional[str] = Query(None, description="Assign to user"),
    notes: Optional[str] = Query(None, description="Add notes"),
    db: Session = Depends(get_db)
):
    """Update alert status."""
    valid_statuses = ["new", "acknowledged", "investigating", "resolved", "false_positive"]
    if status not in valid_statuses:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}"
        )
    
    alert = update_alert_status(db, alert_id, status, assigned_to, notes)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    return {"message": "Alert status updated successfully", "alert": alert.to_dict()}


@api_router.get("/alerts/{alert_id}/iocs")
async def get_alert_iocs_endpoint(
    alert_id: int,
    db: Session = Depends(get_db)
):
    """Get IOCs for a specific alert."""
    alert = get_alert_by_id(db, alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    return {
        "alert_id": alert_id,
        "iocs": alert.iocs,
        "intel_data": alert.intel_data
    }


@api_router.get("/statistics", response_model=Dict[str, Any])
async def get_statistics_endpoint(
    days: int = Query(7, ge=1, le=365, description="Number of days to include"),
    db: Session = Depends(get_db)
):
    """Get alert statistics for dashboard."""
    try:
        stats = get_alert_statistics(db, days)
        return {"statistics": stats}
    except Exception as e:
        logger.error(f"Error fetching statistics: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch statistics")


@api_router.get("/statistics/sources")
async def get_top_sources_endpoint(
    limit: int = Query(10, ge=1, le=100, description="Number of top sources to return"),
    db: Session = Depends(get_db)
):
    """Get top alert sources."""
    try:
        sources = get_top_sources(db, limit)
        return {"sources": sources}
    except Exception as e:
        logger.error(f"Error fetching top sources: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch top sources")


@api_router.get("/statistics/event-types")
async def get_top_event_types_endpoint(
    limit: int = Query(10, ge=1, le=100, description="Number of top event types to return"),
    db: Session = Depends(get_db)
):
    """Get top event types."""
    try:
        event_types = get_top_event_types(db, limit)
        return {"event_types": event_types}
    except Exception as e:
        logger.error(f"Error fetching top event types: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch top event types")


@api_router.get("/statistics/ips")
async def get_top_ips_endpoint(
    limit: int = Query(10, ge=1, le=100, description="Number of top IPs to return"),
    db: Session = Depends(get_db)
):
    """Get top IP addresses."""
    try:
        ips = get_top_ips(db, limit)
        return {"ips": ips}
    except Exception as e:
        logger.error(f"Error fetching top IPs: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch top IPs")


@api_router.get("/dashboard", response_model=Dict[str, Any])
async def get_dashboard_data_endpoint(
    days: int = Query(7, ge=1, le=365, description="Number of days to include"),
    db: Session = Depends(get_db)
):
    """Get comprehensive dashboard data."""
    try:
        # Get statistics
        stats = get_alert_statistics(db, days)
        
        # Get top sources
        sources = get_top_sources(db, 10)
        
        # Get top event types
        event_types = get_top_event_types(db, 10)
        
        # Get top IPs
        ips = get_top_ips(db, 10)
        
        # Get recent alerts (last 24 hours)
        recent_alerts = get_alerts(db, skip=0, limit=10)
        
        return {
            "statistics": stats,
            "top_sources": sources,
            "top_event_types": event_types,
            "top_ips": ips,
            "recent_alerts": [alert.to_dict() for alert in recent_alerts],
            "generated_at": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error fetching dashboard data: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch dashboard data")


@api_router.get("/health")
async def health_check_endpoint():
    """Health check for API."""
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}


@api_router.get("/filters")
async def get_available_filters_endpoint(db: Session = Depends(get_db)):
    """Get available filter options."""
    try:
        # Get unique values for filters
        sources = db.query(Alert.source).filter(Alert.source.isnot(None)).distinct().all()
        event_types = db.query(Alert.event_type).filter(Alert.event_type.isnot(None)).distinct().all()
        categories = db.query(Alert.category).filter(Alert.category.isnot(None)).distinct().all()
        statuses = db.query(Alert.status).distinct().all()
        
        return {
            "sources": [row[0] for row in sources],
            "event_types": [row[0] for row in event_types],
            "categories": [row[0] for row in categories],
            "statuses": [row[0] for row in statuses],
            "severity_levels": list(range(0, 11))
        }
    except Exception as e:
        logger.error(f"Error fetching filter options: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch filter options")
