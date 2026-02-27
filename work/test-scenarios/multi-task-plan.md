# Plan: Add Logging and Validation to Calculator

## Tasks

### Task 1: Add input validation to all functions
- File: calculator.py
- Add type checking for all function parameters
- Raise TypeError for non-numeric inputs
- Raise ValueError for divide(x, 0)

### Task 2: Add logging module
- File: logger.py (NEW)
- Create a simple logger that writes to calculator.log
- Functions: log_operation(func_name, args, result), log_error(func_name, error)

### Task 3: Add power function
- File: calculator.py
- Add power(base, exponent) function
- Handle negative exponents (return float)
- Add tests in test_calculator.py

### Task 4: Add statistics functions
- File: stats.py (NEW)
- Functions: mean(numbers), median(numbers), mode(numbers)
- Each should validate input (non-empty list of numbers)

### Task 5: Add integration tests
- File: test_integration.py (NEW)
- Test calculator + logger working together
- Test calculator + stats working together

### Task 6: Update README
- File: README.md (NEW)
- Document all functions, usage examples
