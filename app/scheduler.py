"""Scheduler for video uploads."""
from datetime import datetime, timedelta
from enum import Enum
from typing import Optional
from app.logging_config import log_manager

logger = log_manager.get_logger(__name__)


class ScheduleType(str, Enum):
    """Schedule type enumeration."""
    NOW = "now"
    FIXED_DELAY = "fixed_delay"
    RANDOM_DELAY = "random_delay"
    SPECIFIC_TIME = "specific_time"
    DAILY = "daily"
    WEEKLY = "weekly"


class Scheduler:
    """Manages upload scheduling."""

    def __init__(self, default_timezone: str = "Asia/Kolkata"):
        """Initialize scheduler.
        
        Args:
            default_timezone: Default timezone for scheduling
        """
        self.default_timezone = default_timezone
        self.schedules = {}

    def schedule_now(self) -> datetime:
        """Schedule for immediate upload.
        
        Returns:
            Scheduled time (current time)
        """
        return datetime.utcnow()

    def schedule_fixed_delay(self, delay_minutes: int) -> datetime:
        """Schedule with fixed delay.
        
        Args:
            delay_minutes: Delay in minutes
            
        Returns:
            Scheduled time
        """
        return datetime.utcnow() + timedelta(minutes=delay_minutes)

    def schedule_random_delay(self, min_minutes: int = 20, 
                             max_minutes: int = 45) -> datetime:
        """Schedule with random delay.
        
        Args:
            min_minutes: Minimum delay in minutes
            max_minutes: Maximum delay in minutes
            
        Returns:
            Scheduled time
        """
        import random
        delay = random.randint(min_minutes, max_minutes)
        return datetime.utcnow() + timedelta(minutes=delay)

    def schedule_specific_time(self, scheduled_time: datetime) -> datetime:
        """Schedule for specific time.
        
        Args:
            scheduled_time: Target time for upload
            
        Returns:
            Scheduled time
        """
        if scheduled_time < datetime.utcnow():
            logger.warning("Scheduled time is in the past, using current time")
            return datetime.utcnow()
        return scheduled_time

    def schedule_daily(self, hour: int, minute: int = 0) -> datetime:
        """Schedule for daily upload.
        
        Args:
            hour: Hour of day (0-23)
            minute: Minute of hour (0-59)
            
        Returns:
            Scheduled time for next occurrence
        """
        now = datetime.utcnow()
        scheduled = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        
        if scheduled <= now:
            scheduled += timedelta(days=1)
        
        return scheduled

    def schedule_weekly(self, day_of_week: int, hour: int, minute: int = 0) -> datetime:
        """Schedule for weekly upload.
        
        Args:
            day_of_week: Day of week (0=Monday, 6=Sunday)
            hour: Hour of day (0-23)
            minute: Minute of hour (0-59)
            
        Returns:
            Scheduled time for next occurrence
        """
        now = datetime.utcnow()
        scheduled = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        
        days_ahead = day_of_week - now.weekday()
        if days_ahead <= 0:
            days_ahead += 7
        
        scheduled += timedelta(days=days_ahead)
        return scheduled

    def is_scheduled_time(self, scheduled_at: datetime) -> bool:
        """Check if scheduled time has arrived.
        
        Args:
            scheduled_at: Scheduled datetime
            
        Returns:
            True if current time >= scheduled time
        """
        return datetime.utcnow() >= scheduled_at

    def time_until_scheduled(self, scheduled_at: datetime) -> int:
        """Get time until scheduled upload.
        
        Args:
            scheduled_at: Scheduled datetime
            
        Returns:
            Seconds until scheduled time
        """
        diff = scheduled_at - datetime.utcnow()
        return max(0, int(diff.total_seconds()))
