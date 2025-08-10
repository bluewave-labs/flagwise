# 🛡️ FlagWise

<div align="center">

**Shadow AI Detection Server - Real-time Security Monitoring for LLM Traffic**

[![Docker](https://img.shields.io/badge/Docker-Ready-blue?logo=docker)](https://www.docker.com/)
[![React](https://img.shields.io/badge/React-18+-61DAFB?logo=react)](https://reactjs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-Latest-009688?logo=fastapi)](https://fastapi.tiangolo.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15+-336791?logo=postgresql)](https://postgresql.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)


FlagWise is an open-source **Shadow AI detection server** designed to give organizations complete visibility into how Large Language Models (LLMs) are being used across their systems. It monitors LLM traffic in real time, detects unauthorized or risky usage, and provides detailed analytics so you can take action before small issues turn into serious security incidents.
</div>

## With FlagWise, you can

- **Monitor LLM traffic in real time** – Intercept and log prompts, responses, and metadata without slowing down your applications
- **Detect shadow AI usage** – Identify unauthorized models, providers, or prompt patterns that violate internal policies
- **Analyze security risks** – See which prompts contain sensitive content, potential data leaks, or compliance violations
- **Get real-time alerts** – Respond instantly when risky or unapproved activity occurs
- **Integrate easily** – Deploy with Docker, run the backend with FastAPI, the frontend with React, and store data securely in PostgreSQL


FlagWise is built for teams that care about **AI governance, security, and compliance**. 



[🚀 Quick Start](#-quick-start) • [📊 Features](#-features) • [📖 Documentation](#-documentation) • [🤝 Contributing](#-contributing)

</div>

---

## ✨ Features

### 🔍 **Real-time Threat Detection**
- **Pattern-based Detection**: Keywords, regex, and custom rules
- **Risk Scoring**: Intelligent threat assessment (0-100 scale)
- **Model Restrictions**: Control which AI models can be used
- **IP Monitoring**: Track and analyze request sources

### 📊 **Comprehensive Analytics**
- **Interactive Dashboard**: Visual insights into LLM traffic
- **Trend Analysis**: Volume, threat, and model usage trends
- **Performance Metrics**: Response times and success rates
- **Custom Reports**: Export data in multiple formats

### 👥 **User Management**
- **Role-based Access**: Admin and read-only user types
- **Secure Authentication**: JWT-based with bcrypt hashing
- **Admin Controls**: Create, edit, and manage user accounts
- **Password Management**: Self-service and admin reset capabilities

### 🚨 **Alert System**
- **Real-time Notifications**: Slack and email integration
- **Configurable Triggers**: Custom alert conditions
- **Alert Management**: Track delivery status and failures

## 🚀 Quick Start

### One-Command Installation
```bash
git clone https://github.com/bluewave-labs/flagwise.git
cd flagwise
docker-compose up -d
```

### Access Your Dashboard
- **Web Interface**: http://localhost:3000
- **Login**: `admin` / `admin123`
- **API Docs**: http://localhost:8000/docs

**⚠️ Remember to change the default password after first login!**

### Data Source Configuration
FlagWise consumes LLM traffic data from Kafka topics that are fed from network routers. Configure your Kafka connection in **Settings → Data Sources** within the FlagWise interface.

[📖 **Detailed Installation Guide →**](INSTALLATION.md)

## 🛠️ Technology Stack

| Component | Technology | Purpose |
|-----------|------------|----------|
| **Frontend** | React 18, TailwindCSS | Interactive dashboard and user interface |
| **Backend** | FastAPI, Python 3.11 | API server and business logic |
| **Database** | PostgreSQL 15 | Data persistence and analytics |
| **Security** | JWT, bcrypt | Authentication and authorization |
| **Deployment** | Docker, Docker Compose | Containerization and orchestration |

---

## 📋 Use Cases

### 🏢 **Enterprise Security**
- Monitor LLM usage across organization
- Detect data leaks and sensitive information exposure
- Enforce AI model usage policies
- Generate compliance reports

### 🔬 **Research & Development**
- Analyze AI model performance and behavior
- Track experiment metrics and outcomes  
- Monitor resource usage and costs
- A/B test different AI configurations

### 🛡️ **Security Operations**
- Real-time threat detection and response
- Integrate with SIEM and security tools
- Automated incident response workflows
- Forensic analysis of security events

## 🔧 Configuration Examples

### Detection Rules
```python
# Example: Detect sensitive data patterns
{
    "name": "Credit Card Detection",
    "rule_type": "regex",
    "pattern": r"\b(?:\d{4}[-\s]?){3}\d{4}\b",
    "severity": "critical",
    "points": 75
}
```

### Alert Configuration
```python
# Example: Slack alert for high-risk events
{
    "alert_type": "slack",
    "webhook_url": "https://hooks.slack.com/...",
    "conditions": {
        "risk_score": {"min": 70},
        "is_flagged": True
    }
}
```

---

## 🚀 Getting Started

### For Developers
1. **[📖 Installation Guide](INSTALLATION.md)** - Get up and running quickly
2. **📚 API Documentation** - Available under /docs in your installation

### For Administrators
1. **[👥 User Management](docs/USER_MANAGEMENT.md)** - Manage accounts and permissions
2. **[🔍 Detection Rules](docs/DETECTION_RULES.md)** - Configure security patterns
3. **[🚨 Alert Setup](docs/ALERTS.md)** - Set up notifications

---

## 🤝 Contributing

We welcome contributions from the community! Here's how to get started:

### Development Setup
```bash
# Clone the repository
git clone https://github.com/bluewave-labs/flagwise.git
cd flagwise

# Start development environment
docker-compose up -d

# Run tests
docker-compose exec api pytest
docker-compose exec web npm test
```

### Contribution Guidelines
- 🐛 **Bug Reports**: Use GitHub Issues with detailed reproduction steps
- ✨ **Feature Requests**: Discuss in GitHub Discussions before implementation
- 🔧 **Pull Requests**: Follow our PR template and ensure tests pass
- 📖 **Documentation**: Help improve our guides and API docs

---

## 📚 Documentation

### User Guides
- [📖 Installation Guide](INSTALLATION.md) - Complete setup instructions
- [👥 User Management](docs/USER_MANAGEMENT.md) - Account and permission management
- [🔍 Detection Rules](docs/DETECTION_RULES.md) - Security pattern configuration

### Technical Documentation
- [🗄️ Database Schema](docs/DATABASE.md) - Table structure and relationships
- [🚀 Deployment Guide](docs/DEPLOYMENT.md) - Production deployment strategies

---

## 🆘 Support

### Community Support
- 💬 **GitHub Discussions**: Ask questions and share ideas
- 🐛 **GitHub Issues**: Report bugs and request features

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- **Contributors**: Thanks to all our amazing contributors
- **Community**: Special thanks to our active community members
- **Open Source**: Built with love using amazing open source technologies

---

<div align="center">

**Made with ❤️ by the FlagWise Team**

[⭐ Star this project](https://github.com/bluewave-labs/flagwise) • [🐛 Report Bug](https://github.com/bluewave-labs/flagwise/issues) • [💡 Request Feature](https://github.com/bluewave-labs/flagwise/discussions)

</div>
