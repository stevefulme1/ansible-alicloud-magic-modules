# Contributing to ansible-alicloud-magic-modules

Thank you for your interest in contributing to **ansible-alicloud-magic-modules**!

## How to Contribute

### Reporting Issues

- Check existing issues before creating a new one
- Use the issue templates if available
- Include steps to reproduce, expected behavior, and actual behavior

### Submitting Changes

1. Fork the repository
2. Create a feature branch from `main`: `git checkout -b feat/my-feature`
3. Make your changes following the project conventions
4. Write or update tests as needed
5. Ensure all CI checks pass
6. Submit a pull request with a clear description

### Pull Request Guidelines

- Keep PRs focused on a single change
- Write meaningful commit messages
- Update documentation if your change affects user-facing behavior
- Update CHANGELOG.md with a summary of your changes
- Ensure CI passes before requesting review

### Adding a New Resource Definition

1. Create a new YAML file in `definitions/` following the schema in `definitions/_schema.yaml`
2. Run `nox -s generate` to produce the modules
3. Run `nox -s tests` to verify all definitions parse correctly
4. Run `nox -s lint` and `nox -s sanity` to check generated output
5. Submit a PR with the new definition file

### Code Style

- Follow existing patterns in the codebase
- Use consistent naming conventions
- Add comments only when the "why" is non-obvious

### Development Setup

```bash
git clone https://github.com/stevefulme1/ansible-alicloud-magic-modules.git
cd ansible-alicloud-magic-modules
pip install -r requirements-dev.txt
nox -s tests
```

See README.md for additional setup instructions.

## License

By contributing, you agree that your contributions will be licensed under
the same license as the project (see LICENSE file).
