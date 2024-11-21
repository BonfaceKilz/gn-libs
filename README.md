# gn-libs: GeneNetwork Libraries

This is a collection of tools/utilities that find use in more than one
GeneNetwork project.

## Installing

* TODO: Document this

## Developing

### Code Checks: Linting and Typing

Run linter
```sh
pylint $(find gn_libs -name '*.py')
```

Run mypy
```sh
mypy --show-error-codes .
```

### Running Tests

Use the following command to run unit tests.

```sh
pytest -k unit_test
```
