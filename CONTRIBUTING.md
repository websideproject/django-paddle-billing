# How to contribute

## Dependencies

We use `hatch` to manage the dependencies.
If you dont have `hatch`, you should install with `pip install hatch`.

## Environment

To create a virtual environment, check out [`hatch`](https://hatch.pypa.io/latest/environment/) documentation.
Alternatively, you can use `make` commands in your activated environment:

```bash
make install
```

To prepare [`pre-commit`](https://pre-commit.com/) hooks you would need to run `pre-commit-install` command:

```bash
make pre-commit-install
```

## Codestyle

After installation you may execute code formatting.

```bash
make codestyle
```

### Checks

Many checks are configured for this project. Command `make check-codestyle` will check black, isort and darglint.
The `make check-safety` command will look at the security of your code.

Comand `make lint` applies all checks.

### Before submitting

Before submitting your code please do the following steps:

1. Add any changes you want
1. Add tests for the new changes
1. Edit documentation if you have changed something significant
1. Run `make codestyle` to format your changes.
1. Run `make lint` to ensure that types, security and docstrings are okay.

## Other help

You can contribute by spreading a word about this library.
It would also be a huge contribution to write
a short article on how you are using this project.
You can also share your best practices with us.
