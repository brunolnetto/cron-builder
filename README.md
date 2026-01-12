# Cron Builder

[![Python 3.13+](https://img.shields.io/badge/python-3.13+-blue.svg)](https://www.python.org/downloads/)
[![Coverage](https://img.shields.io/badge/coverage-100%25-brightgreen.svg)](htmlcov/index.html)
[![Tests](https://img.shields.io/badge/tests-75%20passed-brightgreen.svg)](cron-builder/cron_builder.py)

A fluent, type-safe Python library for building and validating cron expressions with an intuitive API.

## Features

✨ **Fluent API** - Chain methods for readable cron expressions  
🔒 **Type-Safe** - Full type hints and IDE autocomplete support  
✅ **Validated** - Automatic range checking and validation  
🎯 **Expressive** - Use enums for months and weekdays  
⚡ **Immutable Mode** - Optional immutability for functional programming  
🔍 **Smart Matching** - Built-in `should_run()` for schedule validation  
📝 **Well-Tested** - 100% test coverage with 75 tests

## Installation

```bash
pip install cron-builder
```

Or with uv:
```bash
uv add cron-builder
```

## Quick Start

```python
from cron_builder import CronBuilder, Weekday, Month

# Every day at 9:30 AM
cron = CronBuilder().at(9, 30)
print(cron)  # 30 9 * * *

# Every 15 minutes
cron = CronBuilder().every_minutes(15)
print(cron)  # */15 * * * *

# Weekdays at 2:30 PM
cron = CronBuilder().at(14, 30).on_weekdays()
print(cron)  # 30 14 * * 1-5

# First day of every month at midnight
cron = CronBuilder().monthly()
print(cron)  # 0 0 1 * *
```

## Usage Guide

### Basic Time Settings

```python
from cron_builder import CronBuilder

# Set specific minute (0-59)
CronBuilder().at_minute(30)  # 30 * * * *

# Set multiple minutes
CronBuilder().at_minutes(0, 15, 30, 45)  # 0,15,30,45 * * * *

# Every N minutes
CronBuilder().every_minutes(10)  # */10 * * * *

# Minute range
CronBuilder().minute_range(0, 30)  # 0-30 * * * *

# Set hour (0-23)
CronBuilder().at_hour(14)  # * 14 * * *

# Multiple hours
CronBuilder().at_hours(9, 12, 15, 18)  # * 9,12,15,18 * * *

# Every N hours
CronBuilder().every_hours(6)  # * */6 * * *

# Combine hour and minute
CronBuilder().at(9, 30)  # 30 9 * * *
```

### Day of Month

```python
# Specific day
CronBuilder().on_dom(15)  # * * 15 * *

# Multiple days
CronBuilder().on_doms(1, 15, 30)  # * * 1,15,30 * *

# Day range
CronBuilder().dom_range(1, 7)  # * * 1-7 * *

# Aliases available
CronBuilder().on_day_of_month(15)
CronBuilder().on_days_of_month(1, 15)
CronBuilder().day_of_month_range(10, 20)
```

### Day of Week

```python
from cron_builder import Weekday

# Specific day
CronBuilder().on_dow(Weekday.MONDAY)  # * * * * 1

# Multiple days
CronBuilder().on_dows(Weekday.MON, Weekday.WED, Weekday.FRI)  # * * * * 1,3,5

# Weekdays (Monday-Friday)
CronBuilder().on_weekdays()  # * * * * 1-5

# Weekends (Saturday-Sunday)
CronBuilder().on_weekends()  # * * * * 0,6

# Day range
CronBuilder().dow_range(Weekday.MON, Weekday.FRI)  # * * * * 1-5

# Aliases available
CronBuilder().on_day(Weekday.TUESDAY)
CronBuilder().on_days(Weekday.MON, Weekday.FRI)
```

### Months

```python
from cron_builder import Month

# Specific month
CronBuilder().in_month(Month.JUNE)  # * * * 6 *
CronBuilder().in_month(6)  # Same as above

# Multiple months
CronBuilder().in_months(Month.JAN, Month.JUL, Month.DEC)  # * * * 1,7,12 *

# Month range
CronBuilder().month_range(Month.MARCH, Month.MAY)  # * * * 3-5 *
```

### Convenience Presets

```python
from cron_builder import CronBuilder, Weekday, Month

# Hourly (at minute 0 by default)
CronBuilder().hourly()  # 0 * * * *
CronBuilder().hourly(30)  # 30 * * * *

# Daily (at midnight by default)
CronBuilder().daily()  # 0 0 * * *
CronBuilder().daily(14, 30)  # 30 14 * * *

# Weekly (Monday at midnight by default)
CronBuilder().weekly()  # 0 0 * * 1
CronBuilder().weekly(Weekday.FRIDAY, 18, 0)  # 0 18 * * 5

# Monthly (1st at midnight by default)
CronBuilder().monthly()  # 0 0 1 * *
CronBuilder().monthly(15, 9, 30)  # 30 9 15 * *

# Yearly (Jan 1st at midnight by default)
CronBuilder().yearly()  # 0 0 1 1 *
CronBuilder().yearly(Month.JULY, 4, 12, 0)  # 0 12 4 7 *
```

### Advanced: Conjunctions

Handle complex schedules that require both day-of-month AND day-of-week conditions:

```python
from cron_builder import CronBuilder, Weekday
from datetime import datetime

# First Monday of every month
cron = CronBuilder().at(9, 0).dom_range(1, 7).and_dow(Weekday.MONDAY)
print(cron)  # 0 9 1-7 * *

# Check if it should run
if cron.should_run(datetime(2024, 1, 1)):  # Jan 1, 2024 is a Monday
    print("Task runs!")

# Or use callable syntax
if cron():  # Checks current time
    run_task()
```

⚠️ **Note:** Standard cron uses OR logic for day fields, but this library provides `should_run()` to validate AND conditions.

### Immutable Mode

For functional programming or when you want to avoid mutations:

```python
# Mutable mode (default) - modifies in place
builder = CronBuilder()
builder.at_hour(9)
builder.at_hour(14)  # Overwrites previous value (shows warning)
print(builder)  # * 14 * * *

# Immutable mode - returns new instances
builder = CronBuilder(immutable=True)
morning = builder.at_hour(9)
afternoon = builder.at_hour(14)

print(builder)    # * * * * * (unchanged)
print(morning)    # * 9 * * *
print(afternoon)  # * 14 * * *
```

## Real-World Examples

```python
from cron_builder import CronBuilder, Weekday, Month

# Daily backup at 2 AM
backup_cron = CronBuilder().daily(2, 0)
# 0 2 * * *

# Business hours notifications (9 AM - 5 PM, every 30 minutes, weekdays)
notifications = CronBuilder().at_minutes(0, 30).hour_range(9, 17).on_weekdays()
# 0,30 9-17 * * 1-5

# Quarterly reports (first day of Jan, Apr, Jul, Oct at 8 AM)
reports = CronBuilder().at(8, 0).on_dom(1).in_months(Month.JAN, Month.APR, Month.JUL, Month.OCT)
# 0 8 1 1,4,7,10 *

# Weekly deployment window (Sunday 2 AM)
deployment = CronBuilder().weekly(Weekday.SUNDAY, 2, 0)
# 0 2 * * 0

# Holiday reminder (Christmas morning)
holiday = CronBuilder().yearly(Month.DECEMBER, 25, 8, 0)
# 0 8 25 12 *
```

## API Reference

### Enums

#### Weekday
```python
class Weekday(IntEnum):
    SUNDAY = 0
    MONDAY = 1
    TUESDAY = 2
    WEDNESDAY = 3
    THURSDAY = 4
    FRIDAY = 5
    SATURDAY = 6
    # Aliases: SUN, MON, TUE, WED, THU, FRI, SAT
```

#### Month
```python
class Month(IntEnum):
    JANUARY = 1
    FEBRUARY = 2
    # ... through DECEMBER = 12
    # Aliases: JAN, FEB, MAR, APR, JUN, JUL, AUG, SEP, OCT, NOV, DEC
```

### CronBuilder Methods

| Method | Description | Example |
|--------|-------------|---------|
| `at(hour, minute)` | Set specific time | `at(9, 30)` → `30 9 * * *` |
| `at_minute(min)` | Set minute | `at_minute(30)` → `30 * * * *` |
| `at_minutes(*mins)` | Set multiple minutes | `at_minutes(0, 30)` → `0,30 * * * *` |
| `every_minutes(n)` | Every N minutes | `every_minutes(15)` → `*/15 * * * *` |
| `minute_range(start, end)` | Minute range | `minute_range(0, 30)` → `0-30 * * * *` |
| `at_hour(hour)` | Set hour | `at_hour(14)` → `* 14 * * *` |
| `at_hours(*hours)` | Set multiple hours | `at_hours(9, 17)` → `* 9,17 * * *` |
| `every_hours(n)` | Every N hours | `every_hours(6)` → `* */6 * * *` |
| `hour_range(start, end)` | Hour range | `hour_range(9, 17)` → `* 9-17 * * *` |
| `on_dom(day)` | Day of month | `on_dom(15)` → `* * 15 * *` |
| `on_doms(*days)` | Multiple days of month | `on_doms(1, 15)` → `* * 1,15 * *` |
| `dom_range(start, end)` | Day of month range | `dom_range(1, 7)` → `* * 1-7 * *` |
| `on_dow(day)` | Day of week | `on_dow(Weekday.MON)` → `* * * * 1` |
| `on_dows(*days)` | Multiple days of week | `on_dows(1, 3, 5)` → `* * * * 1,3,5` |
| `on_weekdays()` | Monday-Friday | `on_weekdays()` → `* * * * 1-5` |
| `on_weekends()` | Saturday-Sunday | `on_weekends()` → `* * * * 0,6` |
| `dow_range(start, end)` | Day of week range | `dow_range(1, 5)` → `* * * * 1-5` |
| `in_month(month)` | Specific month | `in_month(Month.JUN)` → `* * * 6 *` |
| `in_months(*months)` | Multiple months | `in_months(1, 6, 12)` → `* * * 1,6,12 *` |
| `month_range(start, end)` | Month range | `month_range(3, 5)` → `* * * 3-5 *` |
| `hourly(minute=0)` | Every hour | `hourly(30)` → `30 * * * *` |
| `daily(hour=0, minute=0)` | Every day | `daily(14, 30)` → `30 14 * * *` |
| `weekly(day=MON, h=0, m=0)` | Every week | `weekly(Weekday.FRI)` → `0 0 * * 5` |
| `monthly(day=1, h=0, m=0)` | Every month | `monthly(15)` → `0 0 15 * *` |
| `yearly(month=JAN, day=1, h=0, m=0)` | Every year | `yearly(Month.JUL, 4)` → `0 0 4 7 *` |
| `and_dow(day)` | Add DOW conjunction | `on_dom(1).and_dow(Weekday.MON)` |
| `and_dom(day)` | Add DOM conjunction | `on_dow(Weekday.MON).and_dom(1)` |
| `should_run(dt=None)` | Check if should run | Returns `bool` |

## Validation

All methods automatically validate input ranges:

```python
# These will raise ValueError with helpful messages
CronBuilder().at_minute(60)    # minute must be between 0 and 59
CronBuilder().at_hour(24)      # hour must be between 0 and 23
CronBuilder().on_dom(32)       # day_of_month must be between 1 and 31
CronBuilder().in_month(13)     # month must be between 1 and 12
CronBuilder().on_dow(7)        # day_of_week must be between 0 and 6
CronBuilder().every_minutes(0) # Interval must be positive
```

## Development

### Setup

```bash
# Clone the repository
git clone https://github.com/yourusername/cron-builder.git
cd cron-builder

# Install dependencies with uv
uv sync
```

### Running Tests

```bash
# Run all tests
pytest cron-builder/cron_builder.py -v

# Run with coverage
pytest cron-builder/cron_builder.py --cov=cron-builder --cov-report=html

# Open coverage report
open htmlcov/index.html
```

### Test Coverage

This project maintains **100% test coverage** with 75 comprehensive tests covering:

- ✅ All cron expression types (value, list, range, step, any)
- ✅ Validation and error handling
- ✅ Convenience methods and presets
- ✅ Immutable and mutable modes
- ✅ Conjunction logic
- ✅ Method aliases
- ✅ Edge cases and fallbacks

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

MIT License - see LICENSE file for details

## Credits

Built with ❤️ for developers who want type-safe, validated cron expressions in Python.
