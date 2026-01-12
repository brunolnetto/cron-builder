import pytest
import warnings
from datetime import datetime
from cron_builder import CronBuilder, CronExpr, CronField, Weekday, Month


class TestImmutableMode:
    """Test immutable mode behavior."""
    
    def test_mutable_mode_mutates(self):
        b = CronBuilder(immutable=False)
        b.at_hour(9)
        assert str(b.hour) == "9"
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            b.at_hour(14)
        assert str(b.hour) == "14"
    
    def test_immutable_mode_creates_copies(self):
        b = CronBuilder(immutable=True)
        b1 = b.at_hour(9)
        b2 = b1.at_hour(14)
        
        assert str(b.hour) == "*"
        assert str(b1.hour) == "9"
        assert str(b2.hour) == "14"
    
    def test_immutable_no_warnings(self):
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            b = CronBuilder(immutable=True)
            b.at_hour(9).at_hour(14)
            # No overwrite warnings in immutable mode
            assert len([x for x in w if "overwritten" in str(x.message)]) == 0


class TestCronExpr:
    """Test structured CronExpr."""
    
    def test_any_matches_all(self):
        expr = CronExpr("any", ())
        assert expr.matches(0)
        assert expr.matches(59)
    
    def test_value_matches_exact(self):
        expr = CronExpr("value", (30,))
        assert expr.matches(30)
        assert not expr.matches(31)
    
    def test_list_matches_any_in_list(self):
        expr = CronExpr("list", (0, 15, 30, 45))
        assert expr.matches(0)
        assert expr.matches(30)
        assert not expr.matches(10)
    
    def test_range_matches_within(self):
        expr = CronExpr("range", (10, 20))
        assert expr.matches(10)
        assert expr.matches(15)
        assert expr.matches(20)
        assert not expr.matches(9)
        assert not expr.matches(21)
    
    def test_step_wildcard(self):
        expr = CronExpr("step", (-1, 15))  # */15
        assert expr.matches(0)
        assert expr.matches(15)
        assert expr.matches(30)
        assert not expr.matches(10)
    
    def test_step_from_start(self):
        expr = CronExpr("step", (5, 15))  # 5/15
        assert expr.matches(5)
        assert expr.matches(20)
        assert expr.matches(35)
        assert not expr.matches(0)
        assert not expr.matches(10)


class TestCronBuilder:
    """Test CronBuilder functionality."""
    
    def test_default_initialization(self):
        cron = CronBuilder()
        assert str(cron) == '* * * * *'
    
    def test_at(self):
        cron = CronBuilder().at(9, 30)
        assert str(cron) == '30 9 * * *'
    
    def test_every_minutes(self):
        cron = CronBuilder().every_minutes(15)
        assert str(cron) == '*/15 * * * *'
    
    def test_on_weekdays(self):
        cron = CronBuilder().on_weekdays()
        assert str(cron) == '* * * * 1-5'
    
    def test_complex_expression(self):
        cron = CronBuilder().at_minutes(0, 30).hour_range(9, 17).on_weekdays()
        assert str(cron) == '0,30 9-17 * * 1-5'


class TestConjunctionWithShouldRun:
    """Test improved conjunction API."""
    
    def test_should_run_no_conjunction(self):
        cron = CronBuilder().at(9, 0)
        assert cron.should_run() is True
    
    def test_should_run_with_and_dow_match(self):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            cron = CronBuilder().on_dom(1).and_dow(Weekday.MONDAY)
        # Jan 1, 2024 was a Monday
        assert cron.should_run(datetime(2024, 1, 1)) is True
    
    def test_should_run_with_and_dow_no_match(self):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            cron = CronBuilder().on_dom(1).and_dow(Weekday.MONDAY)
        # Jan 1, 2025 was a Wednesday
        assert cron.should_run(datetime(2025, 1, 1)) is False
    
    def test_callable_alias(self):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            cron = CronBuilder().on_dom(1).and_dow(Weekday.MONDAY)
        # __call__ is alias for should_run
        assert cron(datetime(2024, 1, 1)) is True
    
    def test_and_dom_match(self):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            cron = CronBuilder().on_dow(Weekday.MONDAY).and_dom(1)
        assert cron.should_run(datetime(2024, 1, 1)) is True
    
    def test_dom_range_with_dow(self):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            cron = CronBuilder().dom_range(1, 7).and_dow(Weekday.MONDAY)
        assert cron.should_run(datetime(2024, 1, 1)) is True  # Mon, 1st
        assert cron.should_run(datetime(2025, 1, 6)) is True  # Mon, 6th
        assert cron.should_run(datetime(2025, 1, 13)) is False  # Mon, 13th


class TestRealWorldScenarios:
    """Test real-world cron scenarios."""
    
    def test_daily_backup(self):
        cron = CronBuilder().daily(2, 0)
        assert str(cron) == '0 2 * * *'
    
    def test_business_hours(self):
        cron = CronBuilder().at_minutes(0, 30).hour_range(9, 17).on_weekdays()
        assert str(cron) == '0,30 9-17 * * 1-5'
    
    def test_first_monday_of_month(self):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            cron = CronBuilder().at(9, 0).dom_range(1, 7).and_dow(Weekday.MONDAY)
        assert str(cron) == '0 9 1-7 * *'
        assert cron.should_run(datetime(2024, 1, 1))  # First Monday


class TestValidationErrors:
    """Test validation and error handling."""
    
    def test_minute_out_of_range(self):
        with pytest.raises(ValueError, match="minute must be between 0 and 59"):
            CronBuilder().at_minute(60)
    
    def test_hour_out_of_range(self):
        with pytest.raises(ValueError, match="hour must be between 0 and 23"):
            CronBuilder().at_hour(24)
    
    def test_dom_out_of_range(self):
        with pytest.raises(ValueError, match="day_of_month must be between 1 and 31"):
            CronBuilder().on_dom(32)
    
    def test_month_out_of_range(self):
        with pytest.raises(ValueError, match="month must be between 1 and 12"):
            CronBuilder().in_month(13)
    
    def test_dow_out_of_range(self):
        with pytest.raises(ValueError, match="day_of_week must be between 0 and 6"):
            CronBuilder().on_dow(7)
    
    def test_range_validation_start_greater_than_end(self):
        with pytest.raises(ValueError, match="Range start .* must be <= end"):
            CronBuilder().minute_range(30, 15)
    
    def test_interval_validation_zero(self):
        with pytest.raises(ValueError, match="Interval must be positive"):
            CronBuilder().every_minutes(0)
    
    def test_interval_validation_negative(self):
        with pytest.raises(ValueError, match="Interval must be positive"):
            CronBuilder().every_minutes(-5)
    
    def test_interval_with_invalid_start(self):
        field = CronField(0, 59, "test")
        with pytest.raises(ValueError):
            field.set_interval(15, start=100)
    
    def test_and_dow_without_dom(self):
        with pytest.raises(ValueError, match="Must set day_of_month before calling and_dow"):
            CronBuilder().and_dow(Weekday.MONDAY)
    
    def test_and_dom_without_dow(self):
        with pytest.raises(ValueError, match="Must set day_of_week before calling and_dom"):
            CronBuilder().and_dom(1)


class TestCronExprEdgeCases:
    """Test CronExpr edge cases and fallback."""
    
    def test_to_cron_str_fallback(self):
        # Invalid kind should return "*" as fallback
        expr = CronExpr("invalid", ())
        assert expr.to_cron_str() == "*"
    
    def test_step_with_explicit_start(self):
        expr = CronExpr("step", (10, 15))
        assert expr.to_cron_str() == "10/15"
    
    def test_matches_invalid_kind(self):
        expr = CronExpr("invalid", ())
        assert expr.matches(10) is False


class TestAllMethods:
    """Test all methods for complete coverage."""
    
    def test_at_hours(self):
        cron = CronBuilder().at_hours(9, 12, 15)
        assert str(cron.hour) == "9,12,15"
    
    def test_every_hours(self):
        cron = CronBuilder().every_hours(3)
        assert str(cron.hour) == "*/3"
    
    def test_minute_range(self):
        cron = CronBuilder().minute_range(0, 30)
        assert str(cron.minute) == "0-30"
    
    def test_on_doms(self):
        cron = CronBuilder().on_doms(1, 15, 30)
        assert str(cron.day_of_month) == "1,15,30"
    
    def test_in_month_with_enum(self):
        cron = CronBuilder().in_month(Month.JUNE)
        assert str(cron.month) == "6"
    
    def test_in_month_with_int(self):
        cron = CronBuilder().in_month(7)
        assert str(cron.month) == "7"
    
    def test_in_months_mixed(self):
        cron = CronBuilder().in_months(Month.JANUARY, 6, Month.DECEMBER)
        assert str(cron.month) == "1,6,12"
    
    def test_month_range_with_enums(self):
        cron = CronBuilder().month_range(Month.MARCH, Month.MAY)
        assert str(cron.month) == "3-5"
    
    def test_month_range_with_ints(self):
        cron = CronBuilder().month_range(6, 8)
        assert str(cron.month) == "6-8"
    
    def test_on_dows_with_enums(self):
        cron = CronBuilder().on_dows(Weekday.MONDAY, Weekday.WEDNESDAY, Weekday.FRIDAY)
        assert str(cron.day_of_week) == "1,3,5"
    
    def test_on_dows_with_ints(self):
        cron = CronBuilder().on_dows(1, 3, 5)
        assert str(cron.day_of_week) == "1,3,5"
    
    def test_on_weekends(self):
        cron = CronBuilder().on_weekends()
        assert str(cron.day_of_week) == "0,6"
    
    def test_dow_range_with_enums(self):
        cron = CronBuilder().dow_range(Weekday.MONDAY, Weekday.FRIDAY)
        assert str(cron.day_of_week) == "1-5"
    
    def test_dow_range_with_ints(self):
        cron = CronBuilder().dow_range(1, 5)
        assert str(cron.day_of_week) == "1-5"
    
    def test_hourly_default(self):
        cron = CronBuilder().hourly()
        assert str(cron) == "0 * * * *"
    
    def test_hourly_with_minute(self):
        cron = CronBuilder().hourly(30)
        assert str(cron) == "30 * * * *"
    
    def test_daily_default(self):
        cron = CronBuilder().daily()
        assert str(cron) == "0 0 * * *"
    
    def test_daily_with_time(self):
        cron = CronBuilder().daily(14, 30)
        assert str(cron) == "30 14 * * *"
    
    def test_weekly_default(self):
        cron = CronBuilder().weekly()
        assert str(cron) == "0 0 * * 1"
    
    def test_weekly_with_day(self):
        cron = CronBuilder().weekly(Weekday.FRIDAY)
        assert str(cron) == "0 0 * * 5"
    
    def test_weekly_with_time(self):
        cron = CronBuilder().weekly(Weekday.SATURDAY, 10, 30)
        assert str(cron) == "30 10 * * 6"
    
    def test_monthly_default(self):
        cron = CronBuilder().monthly()
        assert str(cron) == "0 0 1 * *"
    
    def test_monthly_with_day(self):
        cron = CronBuilder().monthly(15)
        assert str(cron) == "0 0 15 * *"
    
    def test_monthly_with_time(self):
        cron = CronBuilder().monthly(20, 9, 30)
        assert str(cron) == "30 9 20 * *"
    
    def test_yearly_default(self):
        cron = CronBuilder().yearly()
        assert str(cron) == "0 0 1 1 *"
    
    def test_yearly_with_month(self):
        cron = CronBuilder().yearly(Month.JUNE)
        assert str(cron) == "0 0 1 6 *"
    
    def test_yearly_full(self):
        cron = CronBuilder().yearly(Month.DECEMBER, 25, 8, 0)
        assert str(cron) == "0 8 25 12 *"
    
    def test_set_any(self):
        field = CronField(0, 59, "test")
        field.set_value(10)
        field.set_any()
        assert str(field) == "*"
    
    def test_aliases_on_day_of_month(self):
        cron = CronBuilder().on_day_of_month(15)
        assert str(cron.day_of_month) == "15"
    
    def test_aliases_on_days_of_month(self):
        cron = CronBuilder().on_days_of_month(1, 15)
        assert str(cron.day_of_month) == "1,15"
    
    def test_aliases_day_of_month_range(self):
        cron = CronBuilder().day_of_month_range(10, 20)
        assert str(cron.day_of_month) == "10-20"
    
    def test_aliases_on_day(self):
        cron = CronBuilder().on_day(Weekday.TUESDAY)
        assert str(cron.day_of_week) == "2"
    
    def test_aliases_on_days(self):
        cron = CronBuilder().on_days(Weekday.MONDAY, Weekday.FRIDAY)
        assert str(cron.day_of_week) == "1,5"
    
    def test_aliases_day_of_week_range(self):
        cron = CronBuilder().day_of_week_range(Weekday.MONDAY, Weekday.FRIDAY)
        assert str(cron.day_of_week) == "1-5"
    
    def test_aliases_and_day(self):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            cron = CronBuilder().on_dom(1).and_day(Weekday.MONDAY)
        assert cron._conjunction == ("dow", 1)
    
    def test_aliases_and_day_of_month(self):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            cron = CronBuilder().on_dow(Weekday.MONDAY).and_day_of_month(1)
        assert cron._conjunction == ("dom", 1)


class TestConjunctionEdgeCases:
    """Test conjunction edge cases."""
    
    def test_and_dom_with_int_dow(self):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            cron = CronBuilder().on_dow(1).and_dom(15)
        # Test the DOM check path
        assert cron.should_run(datetime(2024, 1, 15)) is True  # Monday Jan 15
        assert cron.should_run(datetime(2024, 1, 8)) is False  # Monday but not 15th
    
    def test_should_run_dow_mismatch_in_and_dom(self):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            cron = CronBuilder().on_dow(Weekday.MONDAY).and_dom(15)
        # Tuesday Jan 15, 2024 - DOM matches but DOW doesn't
        assert cron.should_run(datetime(2024, 1, 16)) is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
