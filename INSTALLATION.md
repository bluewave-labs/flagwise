# FlagWise - Installation Guide

**Shadow AI Detection Server** - A real-time security monitoring system for LLM traffic with threat detection, analytics, and user management capabilities.

## 🚀 Quick Start

### Prerequisites
- **Docker & Docker Compose** (v2.0+)
- **Git**
- **4GB+ RAM** recommended
- **Ports 3000, 8000, 5432** available

### 1. Clone & Start
```bash
git clone https://github.com/bluewave-labs/flagwise.git
cd flagwise
docker-compose up -d
```

### 2. Access the Application
- **Web Interface**: http://localhost:3000
- **API Documentation**: http://localhost:8000/docs
- **Default Login**: `admin` / `admin123`

### 3. First Login
1. Open http://localhost:3000
2. Login with `admin` / `admin123`
3. **IMPORTANT**: Change the default password immediately
   - Click user avatar → Profile → Change Password

---

## 📋 Detailed Setup

### System Requirements
- **Operating System**: Linux, macOS, or Windows with WSL2
- **Memory**: 4GB RAM minimum, 8GB recommended
- **Storage**: 10GB free space minimum
- **Network**: Internet access for Docker image downloads

### Installation Steps

#### 1. Prerequisites Installation

**Docker & Docker Compose:**
```bash
# Ubuntu/Debian
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# macOS (using Homebrew)
brew install --cask docker

# Windows
# Download Docker Desktop from https://docker.com
```

#### 2. Clone Repository
```bash
git clone https://github.com/bluewave-labs/flagwise.git
cd flagwise
```

#### 3. Environment Configuration (Optional)
Create `.env` file for custom configuration:
```bash
cp .env.example .env
# Edit .env with your preferred settings
```

**Available Environment Variables:**
```bash
# Database
POSTGRES_DB=shadow_ai
POSTGRES_USER=shadow_user
POSTGRES_PASSWORD=shadow_pass
POSTGRES_HOST=db
POSTGRES_PORT=5432

# API
API_HOST=0.0.0.0
API_PORT=8000
JWT_SECRET_KEY=your-secret-key-here
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=1440

# Web
REACT_APP_API_URL=http://localhost:8000

# Security
BCRYPT_ROUNDS=4
MAX_PAGE_SIZE=1000
```

#### 4. Start Services
```bash
# Start all services in background
docker-compose up -d

# Or start with logs visible
docker-compose up

# Check service status
docker-compose ps
```

#### 5. Verify Installation
```bash
# Check all services are running
docker-compose ps

# Expected output:
NAME            COMMAND                  SERVICE   STATUS    PORTS
shadow-ai-api   "uvicorn main:app --h…"  api       running   0.0.0.0:8000->8000/tcp
shadow-ai-db    "docker-entrypoint.s…"   db        running   5432/tcp
shadow-ai-web   "docker-entrypoint.s…"   web       running   0.0.0.0:3000->3000/tcp

# Test API health
curl http://localhost:8000/health

# Access web interface
open http://localhost:3000  # macOS
# or visit http://localhost:3000 in your browser
```

---

## 📡 Data Source Configuration

### Kafka Integration
FlagWise is designed to consume LLM traffic data from Kafka topics. This data is typically fed from network routers that intercept and forward LLM API traffic.

**To configure Kafka:**
1. Access the web interface at http://localhost:3000
2. Navigate to **Settings → Data Sources**
3. Configure your Kafka broker connection details
4. Set the topic name where your router publishes LLM traffic data
5. Test the connection and start consuming data

**Note**: Your network router must be configured to publish LLM traffic data to a Kafka topic in JSON format for FlagWise to process.

---

## 🔧 Configuration

### Default Admin Account
- **Username**: `admin`
- **Password**: `admin123`
- **Role**: Administrator (full access)

**⚠️ SECURITY NOTICE**: Change the default password immediately after first login!

### Database Initialization
The database is automatically initialized with:
- **Schema creation** (tables, indexes, functions)
- **Default detection rules** (keywords, patterns, model restrictions)
- **Sample analytics data** (for dashboard demonstration)
- **Admin user account**

### Service Ports
- **Web Interface**: http://localhost:3000
- **API Server**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Database**: localhost:5432 (internal only)

---

## 🔍 Verification & Testing

### Health Checks
```bash
# API Health
curl http://localhost:8000/health

# Database Connection
docker-compose exec api python -c "from database import DatabaseService; db = DatabaseService(); print('Database connected!')"

# Web Interface
curl -I http://localhost:3000
```

### Login Test
```bash
# Test admin login
curl -X POST "http://localhost:8000/auth/login" \
  -d "username=admin&password=admin123"

# Expected: JWT token response
```

### Sample Data
The system includes sample detection rules and can generate demo data:
- **Detection Rules**: Pre-configured security patterns
- **Demo Data**: Optional synthetic traffic for testing
- **Analytics**: Sample metrics for dashboard visualization

---

## 🛠 Management Commands

### Service Management
```bash
# Start services
docker-compose up -d

# Stop services
docker-compose down

# Restart specific service
docker-compose restart api
docker-compose restart web
docker-compose restart db

# View logs
docker-compose logs -f api
docker-compose logs -f web
docker-compose logs -f db

# Update services (after code changes)
docker-compose build --no-cache
docker-compose up -d
```

### Database Operations
```bash
# Access database directly
docker-compose exec db psql -U shadow_user -d shadow_ai

# Backup database
docker-compose exec db pg_dump -U shadow_user shadow_ai > backup.sql

# Restore database
docker-compose exec -T db psql -U shadow_user shadow_ai < backup.sql

# Reset database (⚠️ DESTROYS ALL DATA)
docker-compose down -v
docker-compose up -d
```

### System Cleanup
```bash
# Remove all containers and volumes (⚠️ DESTROYS ALL DATA)
docker-compose down -v

# Remove old images
docker system prune -a

# Start fresh
docker-compose up -d
```

---

## 🐛 Troubleshooting

### Common Issues

#### Port Conflicts
```bash
# Check what's using the ports
netstat -tulpn | grep :3000
netstat -tulpn | grep :8000
netstat -tulpn | grep :5432

# Stop conflicting services or change ports in docker-compose.yml
```

#### Services Won't Start
```bash
# Check logs for specific service
docker-compose logs api
docker-compose logs web
docker-compose logs db

# Common fixes
docker-compose down
docker-compose up -d --force-recreate
```

#### Database Connection Issues
```bash
# Check database is running
docker-compose ps db

# Check database logs
docker-compose logs db

# Restart database
docker-compose restart db
```

#### Memory Issues
```bash
# Check available memory
free -h

# Increase Docker memory limit (Docker Desktop)
# Settings → Resources → Advanced → Memory
```

### Getting Help

#### Log Collection
```bash
# Collect all logs
docker-compose logs > system-logs.txt

# Service-specific logs
docker-compose logs api > api-logs.txt
docker-compose logs web > web-logs.txt
docker-compose logs db > db-logs.txt
```

#### System Information
```bash
# Docker version
docker --version
docker-compose --version

# System resources
docker system df
docker stats --no-stream
```

---

## 🚀 Production Deployment

### Security Hardening
1. **Change default passwords**
2. **Use strong JWT secrets**
3. **Configure HTTPS/TLS**
4. **Set up proper firewall rules**
5. **Regular security updates**

### Environment Variables
```bash
# Production .env example
JWT_SECRET_KEY=your-very-long-secure-secret-key-here
POSTGRES_PASSWORD=your-secure-database-password
BCRYPT_ROUNDS=12
API_HOST=0.0.0.0
REACT_APP_API_URL=https://your-domain.com/api
```

### Docker Compose Override
Create `docker-compose.prod.yml`:
```yaml
version: '3.8'
services:
  api:
    environment:
      - ENVIRONMENT=production
    restart: unless-stopped
  
  web:
    environment:
      - NODE_ENV=production
    restart: unless-stopped
  
  db:
    restart: unless-stopped
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./backups:/backups
```

Deploy with:
```bash
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

---

## 📚 Next Steps

After successful installation:

1. **📋 User Management**: Create additional user accounts
2. **🔍 Detection Rules**: Configure custom security patterns
3. **📊 Analytics**: Explore the monitoring dashboard
4. **🚨 Alerts**: Set up notifications (Slack, email)
5. **🔌 Integration**: Connect to your LLM traffic sources
6. **📖 Documentation**: Read the full user guide

For detailed feature documentation, visit: [User Guide](USER_GUIDE.md)

---

## 💡 Support

- **Issues**: [GitHub Issues](https://github.com/yourusername/shadow-ai/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/shadow-ai/discussions)
- **Documentation**: [Wiki](https://github.com/yourusername/shadow-ai/wiki)

---

**🎉 Congratulations! Your FlagWise detection server is now running.**

Access the web interface at http://localhost:3000 and start monitoring your LLM traffic!