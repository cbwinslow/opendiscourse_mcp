# Contributing to OpenDiscourse MCP Servers

## Welcome!

Thank you for your interest in contributing to the OpenDiscourse MCP Servers project! We welcome contributions from everyone, regardless of experience level.

## Code of Conduct

This project adheres to a [Code of Conduct](CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code.

## How to Contribute

### Reporting Issues

1. **Search existing issues** to avoid duplicates
2. **Use clear titles** that describe the problem
3. **Provide detailed information**:
   - Steps to reproduce
   - Expected vs actual behavior
   - Environment details (OS, Python/Node version, etc.)
   - Screenshots or logs if applicable

### Suggesting Features

1. **Check the roadmap** in [project_summary.md](project_summary.md)
2. **Open a feature request** with:
   - Clear description of the feature
   - Use cases and benefits
   - Potential implementation approaches

### Submitting Code Changes

1. **Fork the repository** and create your branch
2. **Follow our development rules** in [rules.md](rules.md)
3. **Write tests** for your changes
4. **Update documentation** as needed
5. **Submit a pull request** with:
   - Clear description of changes
   - Reference to related issues
   - Screenshots if UI changes

## Development Setup

### Prerequisites

- Python 3.8+
- Node.js 14+ (for TypeScript version)
- Docker (for containerized development)
- Git

### Python Development

```bash
# Clone the repository
git clone https://github.com/opendiscourse/opendiscourse-mcp.git
cd opendiscourse-mcp

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/macOS
# venv\Scripts\activate   # Windows

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Run tests
pytest
```

### TypeScript Development

```bash
# Install Node.js dependencies
npm install

# Build TypeScript
npm run build

# Run tests
npm test
```

## Pull Request Process

1. **Create a branch** with descriptive name:
   - `feature/your-feature-name`
   - `bugfix/issue-description`
   - `docs/documentation-update`

2. **Make your changes** following our guidelines

3. **Run tests** to ensure nothing breaks:
   ```bash
   pytest --cov=src --cov-report=term
   ```

4. **Update documentation** if applicable

5. **Commit your changes** with clear messages:
   ```
   git commit -m "feat(congress): add bill tracking functionality"
   ```

6. **Push to your fork**:
   ```bash
   git push origin your-branch-name
   ```

7. **Create a pull request** to our `develop` branch

## Code Review Process

1. **Automated checks** will run (CI pipeline)
2. **Maintainers will review** your code
3. **Address feedback** and make requested changes
4. **Once approved**, your code will be merged

## Style Guidelines

### Python

- Follow [PEP 8](https://peps.python.org/pep-0008/)
- Use type hints
- Write comprehensive docstrings
- Use `black` for formatting
- Use `flake8` for linting

### TypeScript

- Follow [Google TypeScript Style Guide](https://google.github.io/styleguide/tsguide.html)
- Use strict typing
- Write JSDoc comments
- Use `eslint` for linting
- Use `prettier` for formatting

## Testing

- **Unit tests**: Test individual functions
- **Integration tests**: Test component interactions
- **End-to-end tests**: Test complete workflows
- **Performance tests**: Test under load

## Documentation

- **Update existing docs** when making changes
- **Add new docs** for new features
- **Use clear examples** in documentation
- **Keep docs up-to-date**

## Community

- **Join discussions** on GitHub
- **Ask questions** in issues
- **Help others** with their contributions
- **Share your use cases**

## Recognition

All contributors will be recognized in:
- **Contributors list** in documentation
- **Release notes** for significant contributions
- **GitHub contributors** section

## License

By contributing, you agree that your contributions will be licensed under the project's [MIT License](LICENSE).

## Questions?

If you have any questions about contributing, please open an issue with the "question" label.

Thank you for contributing to OpenDiscourse MCP Servers! 🚀