import pytest

from django_event_sourcing.conditions import Condition


class Condition30(Condition):
    def has_condition(self, value):
        return value < 30


class Condition40(Condition):
    def has_condition(self, value):
        return value < 40


class Condition50(Condition):
    def has_condition(self, value):
        return value < 50


class TestConditions:
    def test_and(self):
        condition_class = Condition30 & Condition40
        assert condition_class().has_condition(24)

    def test_triple_and(self):
        condition_class = Condition30 & Condition40 & Condition50
        assert condition_class().has_condition(24)

    def test_or(self):
        condition_class = Condition30 | Condition40
        assert condition_class().has_condition(35)

    def test_failing_and(self):
        condition_class = Condition30 & Condition40
        assert not condition_class().has_condition(35)

    def test_not(self):
        condition_class = ~Condition30
        assert condition_class().has_condition(31)

    def test_must_instance_permission(self):
        with pytest.raises(AttributeError):
            condition_class = Condition30 | Condition40
            assert condition_class.has_condition(35)

    def test_xor(self):
        condition_class = Condition30 ^ Condition40
        assert condition_class().has_condition(35)
        assert not condition_class().has_condition(25)
