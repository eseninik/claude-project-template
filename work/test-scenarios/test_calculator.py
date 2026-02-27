"""Tests for calculator module."""
from calculator import add, subtract, multiply, divide, fibonacci


def test_add():
    assert add(2, 3) == 5
    assert add(-1, 1) == 0
    assert add(0, 0) == 0


def test_subtract():
    assert subtract(5, 3) == 2
    assert subtract(0, 5) == -5


def test_multiply():
    assert multiply(3, 4) == 12
    assert multiply(0, 100) == 0


def test_divide():
    assert divide(10, 2) == 5.0
    assert divide(7, 2) == 3.5


def test_divide_by_zero():
    """Should raise ValueError, not ZeroDivisionError."""
    try:
        divide(1, 0)
        assert False, "Should have raised ValueError"
    except ValueError:
        pass
    except ZeroDivisionError:
        assert False, "Got ZeroDivisionError instead of ValueError"


def test_fibonacci():
    assert fibonacci(0) == 0
    assert fibonacci(1) == 1
    assert fibonacci(2) == 1
    assert fibonacci(5) == 5
    assert fibonacci(10) == 55
