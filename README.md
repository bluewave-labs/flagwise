<h1 align="center">🛡️ FlagWise</h1>

<div align="center">

**Shadow AI Detection Server - Real-time Security Monitoring for LLM Traffic**

[![Docker](https://img.shields.io/badge/Docker-Ready-blue?logo=docker)](https://www.docker.com/)
[![React](https://img.shields.io/badge/React-18+-61DAFB?logo=react)](https://reactjs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-Latest-009688?logo=fastapi)](https://fastapi.tiangolo.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15+-336791?logo=postgresql)](https://postgresql.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

<img width="1341" height="859" alt="SCR-20250810-frva" src="https://github.com/user-attachments/assets/9259c19f-4e05-4925-ae8a-45cf7e037549" />


</div>

FlagWise is an open-source **Shadow AI detection server** designed to give organizations complete visibility into how Large Language Models (LLMs) are being used across their systems. It monitors LLM traffic in real time, detects unauthorized or risky usage, and provides detailed analytics so you can take action before small issues turn into serious security incidents.

With FlagWise, you can:

- **Monitor LLM traffic in real time** – Log prompts, responses, and metadata.
- **Detect shadow AI usage** – Identify unauthorized models, providers, or prompt patterns that violate policies.
- **Analyze security risks** – See which prompts contain sensitive content, potential data leaks or compliance violations.
- **Get real-time alerts** – Respond instantly when risky or unapproved activity occurs.
- **Integrate easily** – Deploy with Docker, run the backend with FastAPI, the frontend with React and store data securely in PostgreSQL

<img width="1046" height="533" alt="SCR-20250810-etjk" src="https://github.com/user-attachments/assets/be79487c-cf9a-4a01-83ce-be14a1f4aa09" />


[🚀 Quick Start](#-quick-start) • [📊 Features](#-features) • [📖 Documentation](#-documentation) • [🤝 Contributing](#-contributing)

</div>

---

## ✨ Features

### 🔍 **Real-time Threat Detection**
- **Pattern-based Detection**: Keywords, regex, and custom rules
- **Risk Scoring**: Intelligent threat assessment (0-100 scale)
- **Model Restrictions**: Control which AI models can be used
- **IP Monitoring**: Track and analyze request sources
- **Interactive Dashboard**: Visual insights into LLM traffic
- **Trend Analysis**: Volume, threat, and model usage trends
- **Performance Metrics**: Response times and success rates
- **Role-based Access**: Admin and read-only user types
- **Configurable Triggers**: Custom alert conditions

Email integration and Slack coming soon
 
## 🚀 Quick Start

### One-Command Installation
```bash
git clone https://github.com/bluewave-labs/flagwise.git
cd flagwise
docker-compose up -d
```

### Access Your Dashboard
- **Web Interface**: http://localhost:3000
- **Login**: `admin` / `admin123` (please change this once you login)
- **API Docs**: http://localhost:8000/docs

### Data Source Configuration
FlagWise consumes LLM traffic data from Kafka topics that are fed from network routers. Configure your Kafka connection in **Settings → Data Sources** within the FlagWise interface. In the future we'll add more data sources.

![SCR-20250810-dtaq](https://github.com/user-attachments/assets/7a09d058-8f10-447d-90fb-af7e29b6f8f7)

[📖 **Installation Guide →**](INSTALLATION.md)

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

In enterprise security, the system enables organizations to track LLM usage across the company, detect and prevent data leaks or sensitive information exposure, enforce approved AI model usage policies, and generate audit-ready compliance reports.

For research and development, it allows teams to analyze AI model performance and behavior, track experiment metrics and outcomes, monitor resource consumption and related costs, and run A/B tests to compare different AI configurations.

Within security operations, it provides real-time threat detection and response capabilities, integrates seamlessly with SIEM platforms and other security tools, automates incident response workflows, and supports forensic analysis of security events.


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

## 🆘 Support & License

Please ask your questions or submit an issue in Github issues section.

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

<div align="center">

**Made with ❤️ by the FlagWise Team**

[⭐ Star this project](https://github.com/bluewave-labs/flagwise) • [🐛 Report Bug](https://github.com/bluewave-labs/flagwise/issues) • [💡 Request Feature](https://github.com/bluewave-labs/flagwise/discussions)

</div>
