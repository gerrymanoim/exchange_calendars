---
  name: writing-tests
  description: Instructions and guidance on writing tests
---
## Location
- tests are in `tests/`.
- doctests can be used instead of unit tests if the doctest fully covers the function/method's functionality.
- fixtures shared by the whole suite are located in `tests/conftest.py`; fixtures shared by the tests of one package are located in the `conftest.py` of that package's test directory.

## Framework
- tests should assume use of the `pytest` framework.
- use appropriate features of the `pytest` framework, to include fixtures and mocking.
- a fixture that returns a class is named in CapWords, as a class is; every other fixture is named in snake_case.

## Creating Test Datasets
- datasets should be assigned to global constants in order to facilitate external access. Tests should not access these constants directly but rather use them via fixtures which should in turn return a COPY of the constants. Note that this rule does not apply to small datasets of less than 10 rows which can be reasonably interpreted from inspection of the raw data.
- datasets shared by more than one test module are defined in a dedicated module of the test directory and exposed via fixtures in that directory's `conftest.py`. A test module must NEVER import from another test module.
- define test data to include values at the limits of where the output of tested functions/methods changes.

## Writing tests
- tests should be written to test the INTENDED implementation with a focus on finding bugs.
- NEVER assume that the implementation is correct and that a test should pass.
- always test on and either side of limits where output changes.
- always seek to identify and test edge cases.

## Documentation
- if including a docstring for a test then docstring should start with an imperative, for example 'Verify' or 'Test'.
