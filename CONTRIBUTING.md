# Contributing to Universal Scraper

Thank you for your interest in contributing! This document provides guidelines for contributing to the project.

## Getting Started

1. Fork the repository
2. Clone your fork
3. Create a new branch: `git checkout -b feature/your-feature-name`
4. Follow the setup instructions in [SETUP.md](SETUP.md)

## Development Setup

### Backend Development

```bash
# Activate virtual environment
source venv/bin/activate

# Install development dependencies
pip install -r requirements.txt

# Run tests
pytest

# Format code
black backend/
```

### Frontend Development

```bash
cd frontend

# Install dependencies
npm install

# Run development server
npm run dev

# Lint code
npm run lint

# Build for production
npm run build
```

## Code Style

### Python (Backend)

- Follow PEP 8 style guidelines
- Use Black for code formatting: `black backend/`
- Add type hints where possible
- Write docstrings for all public functions and classes
- Keep functions focused and under 50 lines when possible

### JavaScript/React (Frontend)

- Use functional components with hooks
- Follow React best practices
- Use ESLint for linting: `npm run lint`
- Keep components small and reusable
- Use meaningful variable names

## Project Structure

```
backend/
├── ai/          # AI agents (Groq, search, site selection)
├── api/         # FastAPI routes and schemas
├── rag/         # RAG pipeline components
├── scraper/     # Web scraping logic
├── storage/     # Database and file storage
├── utils/       # Utility functions
└── main.py      # Application entry point

frontend/
├── src/
│   ├── components/  # React components
│   ├── lib/         # Utilities and API client
│   └── App.jsx      # Main app component
└── package.json
```

## Making Changes

### Adding a New Feature

1. **Plan**: Discuss major changes by opening an issue first
2. **Code**: Implement your feature following the code style
3. **Test**: Add tests for new functionality
4. **Document**: Update README.md and docstrings
5. **Commit**: Write clear, descriptive commit messages

### Commit Message Format

```
type(scope): subject

body

footer
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Build process or auxiliary tool changes

Examples:
```
feat(scraper): add support for JavaScript-rendered pages

Integrated Playwright for dynamic content scraping.
Allows scraping of SPA websites.

Closes #123
```

```
fix(api): resolve WebSocket connection timeout

Fixed issue where WebSocket connections would timeout
after 30 seconds of inactivity.
```

## Testing

### Backend Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_scraper.py

# Run with coverage
pytest --cov=backend

# Run specific test
pytest tests/test_scraper.py::test_fetch_url
```

### Frontend Tests

```bash
cd frontend
npm test
```

## Pull Request Process

1. **Update Documentation**: Ensure README.md reflects any changes
2. **Add Tests**: Include tests for new features
3. **Update CHANGELOG**: Add your changes to CHANGELOG.md
4. **Clean Commits**: Squash commits if needed
5. **Submit PR**: Open a pull request with a clear description

### PR Checklist

- [ ] Code follows the project's style guidelines
- [ ] Self-review completed
- [ ] Comments added for complex code
- [ ] Documentation updated
- [ ] Tests added/updated and passing
- [ ] No new warnings generated
- [ ] Dependent changes merged

## Feature Requests

Have an idea? Open an issue with:

1. **Use Case**: Describe the problem you're trying to solve
2. **Proposed Solution**: Your suggested approach
3. **Alternatives**: Other solutions you've considered
4. **Additional Context**: Screenshots, examples, etc.

## Bug Reports

Found a bug? Open an issue with:

1. **Description**: Clear description of the bug
2. **Steps to Reproduce**: Detailed steps to reproduce the issue
3. **Expected Behavior**: What should happen
4. **Actual Behavior**: What actually happens
5. **Environment**: OS, Python version, Node version
6. **Logs**: Relevant error messages or logs
7. **Screenshots**: If applicable

## Code Review Process

- All submissions require review
- Maintainers will provide feedback within 1 week
- Address review comments
- Once approved, maintainers will merge

## Areas for Contribution

### High Priority

- [ ] Search API integration for Smart Scraping
- [ ] Comprehensive test coverage
- [ ] Docker containerization
- [ ] Performance optimizations
- [ ] Better error handling

### Features

- [ ] PDF scraping support
- [ ] Export functionality (JSON, CSV, Markdown)
- [ ] Scheduled scraping jobs
- [ ] User authentication
- [ ] Advanced search filters
- [ ] Mobile responsive improvements

### Documentation

- [ ] Video tutorials
- [ ] More code examples
- [ ] Deployment guides (AWS, GCP, Azure)
- [ ] API usage examples
- [ ] Architecture diagrams

### Bug Fixes

- Check the [issues page](../../issues) for bugs labeled `good first issue`

## Community

- Be respectful and inclusive
- Help others in issues and discussions
- Share your use cases and experiences
- Contribute to documentation

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

## Questions?

Open an issue with the `question` label or reach out to the maintainers.

---

Thank you for contributing! 🙏


