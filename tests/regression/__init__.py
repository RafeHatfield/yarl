"""Regression tests package.

This package contains tests specifically designed to prevent regression
of bugs that have been fixed. Each test module should focus on a specific
component or system and clearly document the bugs it prevents.

Guidelines for regression tests:
1. Each test should have a clear docstring explaining the bug it prevents
2. Tests should use real classes when possible, not just mocks
3. Include the original error message or symptom in the test name/docstring
4. Test both the specific bug and the general interface contract
5. Include integration tests that would have caught the bug originally
"""
