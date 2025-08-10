# Contributing to FlagWise

Thank you for your interest in contributing to FlagWise! This document provides guidelines and instructions for contributing to the project.

## 🎯 Getting Started

### Prerequisites
- **Docker & Docker Compose** (v2.0+)
- **Git**
- **Node.js** (v18+) for frontend development
- **Python** (v3.11+) for backend development

### Development Setup
```bash
# 1. Fork and clone the repository
git clone https://github.com/bluewave-labs/flagwise.git
cd flagwise

# 2. Copy environment configuration
cp .env.example .env

# 3. Start development environment
docker-compose up -d

# 4. Verify services are running
docker-compose ps
```

## 🛠️ Development Workflow

### Code Organization
```
shadow-ai/
├── services/
│   ├── api/          # FastAPI backend
│   ├── web/          # React frontend
│   └── consumer/     # Kafka consumer (if applicable)
├── database/         # PostgreSQL initialization
├── docs/             # Documentation
└── tests/            # Test suites
```

### Making Changes
1. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes** following our coding standards

3. **Test your changes** thoroughly
   ```bash
   # Run backend tests
   docker-compose exec api pytest
   
   # Run frontend tests
   docker-compose exec web npm test
   
   # Run linting
   docker-compose exec api flake8 .
   docker-compose exec web npm run lint
   ```

4. **Commit with clear messages**
   ```bash
   git commit -m "feat: add user password reset functionality"
   ```

5. **Push and create a pull request**
   ```bash
   git push origin feature/your-feature-name
   ```

## 📋 Contribution Types

### 🐛 Bug Reports
**Before submitting a bug report:**
- Check if the issue already exists in [GitHub Issues](https://github.com/bluewave-labs/flagwise/issues)
- Try to reproduce the issue with the latest version
- Collect relevant logs and system information

**Bug report should include:**
- Clear description of the problem
- Steps to reproduce
- Expected vs actual behavior
- Environment details (OS, Docker version, etc.)
- Relevant logs or screenshots

### ✨ Feature Requests
**Before submitting a feature request:**
- Check [GitHub Discussions](https://github.com/bluewave-labs/flagwise/discussions) for similar ideas
- Consider if the feature fits the project's scope and vision
- Think about implementation complexity and maintenance impact

**Feature request should include:**
- Clear description of the feature
- Use case and business value
- Proposed implementation approach
- Consider backward compatibility

### 🔧 Code Contributions
We welcome pull requests for:
- Bug fixes
- Feature implementations
- Performance improvements
- Documentation updates
- Test coverage improvements

## 📐 Coding Standards

### Backend (Python/FastAPI)
- **Style**: Follow PEP 8 guidelines
- **Formatting**: Use `black` for code formatting
- **Linting**: Use `flake8` for linting
- **Type Hints**: Use type annotations where possible
- **Documentation**: Include docstrings for all functions and classes

```python
# Example function with proper documentation
def calculate_risk_score(request_data: dict, rules: List[DetectionRule]) -> int:
    """Calculate risk score for an LLM request.
    
    Args:
        request_data: The request data containing prompt and metadata
        rules: List of detection rules to apply
        
    Returns:
        Risk score between 0-100
        
    Raises:
        ValueError: If request_data is invalid
    """
    pass
```

### Frontend (React/JavaScript)
- **Style**: Use Prettier for code formatting
- **Linting**: Use ESLint with our configuration
- **Components**: Use functional components with hooks
- **State Management**: Use React Context for global state
- **Styling**: Use TailwindCSS for styling

```javascript
// Example component structure
const UserManagement = () => {
  const [users, setUsers] = useState([]);
  const { toast } = useToast();
  
  useEffect(() => {
    loadUsers();
  }, []);
  
  const loadUsers = async () => {
    // Implementation
  };
  
  return (
    <div className="space-y-6">
      {/* Component JSX */}
    </div>
  );
};
```

### Database
- **Migrations**: Use SQL migration scripts in `database/`
- **Indexing**: Add appropriate indexes for performance
- **Security**: Use parameterized queries, never string concatenation
- **Documentation**: Comment complex queries and schemas

## 🧪 Testing Guidelines

### Backend Testing
```bash
# Run all tests
docker-compose exec api pytest

# Run specific test file
docker-compose exec api pytest tests/test_auth.py

# Run with coverage
docker-compose exec api pytest --cov=.
```

**Test Categories:**
- **Unit Tests**: Test individual functions and classes
- **Integration Tests**: Test API endpoints and database interactions
- **Security Tests**: Test authentication and authorization

### Frontend Testing
```bash
# Run all tests
docker-compose exec web npm test

# Run tests in watch mode
docker-compose exec web npm test -- --watch

# Run tests with coverage
docker-compose exec web npm test -- --coverage
```

**Test Categories:**
- **Component Tests**: Test React components
- **Integration Tests**: Test user interactions and API calls
- **E2E Tests**: Test complete user workflows

### Writing Good Tests
- **Descriptive names**: Test names should describe what they test
- **Arrange-Act-Assert**: Structure tests clearly
- **Mock external dependencies**: Don't depend on external services
- **Test edge cases**: Include boundary conditions and error scenarios

## 📖 Documentation

### Code Documentation
- **Comments**: Explain complex logic, not obvious code
- **API Documentation**: Update OpenAPI specs for API changes
- **README Updates**: Keep setup instructions current
- **Changelog**: Add entries for user-facing changes

### User Documentation
- **Installation Guide**: Update setup instructions
- **User Guides**: Create guides for new features
- **Configuration**: Document all configuration options
- **Troubleshooting**: Add common issues and solutions

## 🔒 Security Considerations

### Security Guidelines
- **Never commit secrets**: Use environment variables
- **Input validation**: Validate all user inputs
- **Authentication**: Implement proper access controls
- **Encryption**: Encrypt sensitive data at rest and in transit
- **Dependencies**: Keep dependencies up to date

### Reporting Security Issues
**Do NOT create public issues for security vulnerabilities.**

Instead:
1. Email security@yourdomain.com with details
2. Include steps to reproduce
3. Wait for response before public disclosure
4. We'll coordinate responsible disclosure

## 🚀 Release Process

### Versioning
We use [Semantic Versioning](https://semver.org/):
- **MAJOR**: Breaking changes
- **MINOR**: New features (backward compatible)
- **PATCH**: Bug fixes (backward compatible)

### Release Checklist
- [ ] All tests passing
- [ ] Documentation updated
- [ ] Changelog updated
- [ ] Version numbers bumped
- [ ] Security review completed
- [ ] Performance benchmarks run

## 📞 Communication

### Channels
- **GitHub Issues**: Bug reports and feature requests
- **GitHub Discussions**: Questions, ideas, and general discussion
- **Pull Request Reviews**: Code review discussions
- **Discord/Slack**: Real-time community chat (if available)

### Code Review Process
1. **Automated Checks**: CI/CD must pass
2. **Peer Review**: At least one maintainer review required
3. **Testing**: Manual testing for UI changes
4. **Documentation**: Ensure docs are updated
5. **Security Review**: For security-sensitive changes

## 🏆 Recognition

### Contributors
- All contributors are recognized in our README
- Significant contributors may be invited as maintainers
- We follow the [All Contributors](https://allcontributors.org/) specification

### Maintainer Guidelines
**For project maintainers:**
- Be welcoming and helpful to new contributors
- Provide constructive feedback in reviews
- Maintain high code quality standards
- Keep the project roadmap updated
- Handle security issues responsibly

## 📜 Code of Conduct

We are committed to providing a welcoming and inclusive environment for all contributors.

### Our Standards
- **Be respectful**: Treat everyone with respect and professionalism
- **Be inclusive**: Welcome people of all backgrounds and skill levels
- **Be constructive**: Provide helpful feedback and suggestions
- **Be patient**: Help newcomers learn and contribute

### Unacceptable Behavior
- Harassment, discrimination, or hostile behavior
- Personal attacks or inflammatory language
- Publishing private information without consent
- Any conduct that would be inappropriate in a professional setting

### Enforcement
Violations may result in:
1. Warning from maintainers
2. Temporary suspension from project
3. Permanent ban from project

Report issues to: conduct@yourdomain.com

## 📚 Additional Resources

### Learning Resources
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [React Documentation](https://reactjs.org/docs)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [Docker Documentation](https://docs.docker.com/)

### Project Resources
- [Architecture Overview](docs/ARCHITECTURE.md)
- [API Reference](http://localhost:8000/docs)
- [Database Schema](docs/DATABASE.md)
- [Deployment Guide](docs/DEPLOYMENT.md)

## 🎉 Thank You!

Thank you for contributing to FlagWise! Your contributions help make LLM security monitoring better for everyone.

---

**Questions?** Feel free to ask in [GitHub Discussions](https://github.com/bluewave-labs/flagwise/discussions) or create an issue.