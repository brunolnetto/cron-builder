from typing import Union, Literal, Optional
from enum import IntEnum
from datetime import datetime
from dataclasses import dataclass
import warnings


class Weekday(IntEnum):
    """Enum for weekday values in cron expressions."""
    SUNDAY = 0
    MONDAY = 1
    TUESDAY = 2
    WEDNESDAY = 3
    THURSDAY = 4
    FRIDAY = 5
    SATURDAY = 6
    
    SUN = 0
    MON = 1
    TUE = 2
    WED = 3
    THU = 4
    FRI = 5
    SAT = 6


class Month(IntEnum):
    """Enum for month values in cron expressions."""
    JANUARY = 1
    FEBRUARY = 2
    MARCH = 3
    APRIL = 4
    MAY = 5
    JUNE = 6
    JULY = 7
    AUGUST = 8
    SEPTEMBER = 9
    OCTOBER = 10
    NOVEMBER = 11
    DECEMBER = 12
    
    JAN = 1
    FEB = 2
    MAR = 3
    APR = 4
    JUN = 6
    JUL = 7
    AUG = 8
    SEP = 9
    OCT = 10
    NOV = 11
    DEC = 12


@dataclass(frozen=True)
class CronExpr:
    """Structured representation of a cron field value."""
    kind: Literal["any", "value", "list", "range", "step"]
    values: tuple[int, ...]
    
    def matches(self, actual: int) -> bool:
        """Check if a value matches this expression."""
        if self.kind == "any":
            return True
        elif self.kind == "value":
            return actual == self.values[0]
        elif self.kind == "list":
            return actual in self.values
        elif self.kind == "range":
            return self.values[0] <= actual <= self.values[1]
        elif self.kind == "step":
            start, step = self.values
            if start == -1:
                return actual % step == 0
            return actual >= start and (actual - start) % step == 0
        return False
    
    def to_cron_str(self) -> str:
        """Convert to cron syntax string."""
        if self.kind == "any":
            return "*"
        elif self.kind == "value":
            return str(self.values[0])
        elif self.kind == "list":
            return ",".join(map(str, self.values))
        elif self.kind == "range":
            return f"{self.values[0]}-{self.values[1]}"
        elif self.kind == "step":
            start, step = self.values
            if start == -1:
                return f"*/{step}"
            return f"{start}/{step}"
        return "*"


class CronField:
    """Represents a single cron field with validation."""
    
    def __init__(self, min_val: int, max_val: int, name: str, immutable: bool = False):
        self.min_val = min_val
        self.max_val = max_val
        self.name = name
        self.immutable = immutable
        self.expr = CronExpr("any", ())
    
    def _validate_value(self, val: int) -> None:
        """Validate a single value is within range."""
        if not self.min_val <= val <= self.max_val:
            raise ValueError(
                f"{self.name} must be between {self.min_val} and {self.max_val}, got {val}"
            )
    
    def _warn_overwrite(self, new_expr: CronExpr) -> None:
        """Warn if overwriting non-wildcard value."""
        if self.expr.kind != "any":
            warnings.warn(
                f"{self.name} field overwritten: '{self.expr.to_cron_str()}' -> '{new_expr.to_cron_str()}'",
                UserWarning,
                stacklevel=4
            )
    
    def _apply(self, expr: CronExpr) -> 'CronField':
        """Apply expression, returning new field if immutable."""
        if self.immutable:
            new_field = CronField(self.min_val, self.max_val, self.name, self.immutable)
            new_field.expr = expr
            return new_field
        else:
            self._warn_overwrite(expr)
            self.expr = expr
            return self
    
    def set_value(self, val: int) -> 'CronField':
        """Set a specific value."""
        self._validate_value(val)
        return self._apply(CronExpr("value", (val,)))
    
    def set_values(self, *values: int) -> 'CronField':
        """Set multiple specific values (comma-separated)."""
        for val in values:
            self._validate_value(val)
        return self._apply(CronExpr("list", tuple(values)))
    
    def set_range(self, start: int, end: int) -> 'CronField':
        """Set a range of values."""
        self._validate_value(start)
        self._validate_value(end)
        if start > end:
            raise ValueError(f"Range start ({start}) must be <= end ({end})")
        return self._apply(CronExpr("range", (start, end)))
    
    def set_interval(self, interval: int, start: int = -1) -> 'CronField':
        """Set an interval (step value). start=-1 means wildcard."""
        if interval <= 0:
            raise ValueError(f"Interval must be positive, got {interval}")
        if start != -1:
            self._validate_value(start)
        return self._apply(CronExpr("step", (start, interval)))
    
    def set_any(self) -> 'CronField':
        """Set to any value (*)."""
        return self._apply(CronExpr("any", ()))
    
    def matches(self, actual: int) -> bool:
        """Check if a value matches this field's expression."""
        return self.expr.matches(actual)
    
    def __str__(self) -> str:
        return self.expr.to_cron_str()


class CronBuilder:
    """A fluent builder for cron expressions with validation."""
    
    def __init__(self, immutable: bool = False):
        """Create a CronBuilder."""
        self.immutable = immutable
        self.minute = CronField(0, 59, "minute", immutable)
        self.hour = CronField(0, 23, "hour", immutable)
        self.day_of_month = CronField(1, 31, "day_of_month", immutable)
        self.month = CronField(1, 12, "month", immutable)
        self.day_of_week = CronField(0, 6, "day_of_week", immutable)
        self._conjunction: Optional[tuple[str, int]] = None
    
    def _copy_with(self, **fields) -> 'CronBuilder':
        """Create a copy with updated fields (for immutable mode)."""
        if not self.immutable:
            for name, field in fields.items():
                setattr(self, name, field)
            return self
        
        new = CronBuilder(immutable=True)
        new.minute = fields.get('minute', self.minute)
        new.hour = fields.get('hour', self.hour)
        new.day_of_month = fields.get('day_of_month', self.day_of_month)
        new.month = fields.get('month', self.month)
        new.day_of_week = fields.get('day_of_week', self.day_of_week)
        new._conjunction = fields.get('_conjunction', self._conjunction)
        return new
    
    def at_minute(self, minute: int) -> 'CronBuilder':
        return self._copy_with(minute=self.minute.set_value(minute))
    
    def at_minutes(self, *minutes: int) -> 'CronBuilder':
        return self._copy_with(minute=self.minute.set_values(*minutes))
    
    def every_minutes(self, interval: int) -> 'CronBuilder':
        return self._copy_with(minute=self.minute.set_interval(interval))
    
    def minute_range(self, start: int, end: int) -> 'CronBuilder':
        return self._copy_with(minute=self.minute.set_range(start, end))
    
    def at_hour(self, hour: int) -> 'CronBuilder':
        return self._copy_with(hour=self.hour.set_value(hour))
    
    def at_hours(self, *hours: int) -> 'CronBuilder':
        return self._copy_with(hour=self.hour.set_values(*hours))
    
    def every_hours(self, interval: int) -> 'CronBuilder':
        return self._copy_with(hour=self.hour.set_interval(interval))
    
    def hour_range(self, start: int, end: int) -> 'CronBuilder':
        return self._copy_with(hour=self.hour.set_range(start, end))
    
    def at(self, hour: int, minute: int = 0) -> 'CronBuilder':
        result = self.at_hour(hour)
        return result.at_minute(minute)
    
    def on_dom(self, day: int) -> 'CronBuilder':
        return self._copy_with(day_of_month=self.day_of_month.set_value(day))
    
    def on_doms(self, *days: int) -> 'CronBuilder':
        return self._copy_with(day_of_month=self.day_of_month.set_values(*days))
    
    def dom_range(self, start: int, end: int) -> 'CronBuilder':
        return self._copy_with(day_of_month=self.day_of_month.set_range(start, end))
    
    on_day_of_month = on_dom
    on_days_of_month = on_doms
    day_of_month_range = dom_range
    
    def in_month(self, month: Union[int, Month]) -> 'CronBuilder':
        month_val = month.value if isinstance(month, Month) else month
        return self._copy_with(month=self.month.set_value(month_val))
    
    def in_months(self, *months: Union[int, Month]) -> 'CronBuilder':
        month_values = [m.value if isinstance(m, Month) else m for m in months]
        return self._copy_with(month=self.month.set_values(*month_values))
    
    def month_range(self, start: Union[int, Month], end: Union[int, Month]) -> 'CronBuilder':
        start_val = start.value if isinstance(start, Month) else start
        end_val = end.value if isinstance(end, Month) else end
        return self._copy_with(month=self.month.set_range(start_val, end_val))
    
    def on_dow(self, day: Union[int, Weekday]) -> 'CronBuilder':
        day_val = day.value if isinstance(day, Weekday) else day
        return self._copy_with(day_of_week=self.day_of_week.set_value(day_val))
    
    def on_dows(self, *days: Union[int, Weekday]) -> 'CronBuilder':
        day_values = [d.value if isinstance(d, Weekday) else d for d in days]
        return self._copy_with(day_of_week=self.day_of_week.set_values(*day_values))
    
    def on_weekdays(self) -> 'CronBuilder':
        return self._copy_with(day_of_week=self.day_of_week.set_range(1, 5))
    
    def on_weekends(self) -> 'CronBuilder':
        return self._copy_with(day_of_week=self.day_of_week.set_values(0, 6))
    
    def dow_range(self, start: Union[int, Weekday], end: Union[int, Weekday]) -> 'CronBuilder':
        start_val = start.value if isinstance(start, Weekday) else start
        end_val = end.value if isinstance(end, Weekday) else end
        return self._copy_with(day_of_week=self.day_of_week.set_range(start_val, end_val))
    
    on_day = on_dow
    on_days = on_dows
    day_of_week_range = dow_range
    
    def hourly(self, minute: int = 0) -> 'CronBuilder':
        return self.at_minute(minute)
    
    def daily(self, hour: int = 0, minute: int = 0) -> 'CronBuilder':
        return self.at(hour, minute)
    
    def weekly(self, day: Union[int, Weekday] = Weekday.MONDAY, hour: int = 0, minute: int = 0) -> 'CronBuilder':
        return self.at(hour, minute).on_dow(day)
    
    def monthly(self, day: int = 1, hour: int = 0, minute: int = 0) -> 'CronBuilder':
        return self.at(hour, minute).on_dom(day)
    
    def yearly(self, month: Union[int, Month] = Month.JANUARY, day: int = 1, hour: int = 0, minute: int = 0) -> 'CronBuilder':
        return self.at(hour, minute).on_dom(day).in_month(month)
    
    def and_dow(self, day: Union[int, Weekday]) -> 'CronBuilder':
        if self.day_of_month.expr.kind == "any":
            raise ValueError("Must set day_of_month before calling and_dow()")
        
        day_val = day.value if isinstance(day, Weekday) else day
        
        warnings.warn(
            f"Conjunction created: DOM AND DOW={day_val}. "
            f"Cron runs on DOM, use should_run() to validate both conditions.",
            UserWarning,
            stacklevel=2
        )
        
        return self._copy_with(_conjunction=("dow", day_val))
    
    def and_dom(self, day: int) -> 'CronBuilder':
        if self.day_of_week.expr.kind == "any":
            raise ValueError("Must set day_of_week before calling and_dom()")
        
        warnings.warn(
            f"Conjunction created: DOW AND DOM={day}. "
            f"Cron runs on DOW, use should_run() to validate both conditions.",
            UserWarning,
            stacklevel=2
        )
        
        return self._copy_with(_conjunction=("dom", day))
    
    and_day = and_dow
    and_day_of_month = and_dom
    
    def should_run(self, check_time: Optional[datetime] = None) -> bool:
        if self._conjunction is None:
            return True
        
        dt = check_time or datetime.now()
        conj_type, conj_value = self._conjunction
        
        dt_weekday = (dt.weekday() + 1) % 7
        
        if conj_type == "dow":
            if not self.day_of_month.matches(dt.day):
                return False
            return dt_weekday == conj_value
        else:
            if not self.day_of_week.matches(dt_weekday):
                return False
            return dt.day == conj_value
    
    def __call__(self, check_time: Optional[datetime] = None) -> bool:
        return self.should_run(check_time)
    
    def __str__(self) -> str:
        return f"{self.minute} {self.hour} {self.day_of_month} {self.month} {self.day_of_week}"
    
    def __repr__(self) -> str:
        return f"CronBuilder('{str(self)}')"


__all__ = ["CronBuilder", "CronExpr", "CronField", "Weekday", "Month"]
