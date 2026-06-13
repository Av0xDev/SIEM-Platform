# Quick Start Guide for SIEM Platform

This guide will get you up and running with the SIEM Platform in minutes.

## 🚀 Fastest Way to Get Started

### Option 1: Automated Setup (Recommended for First-Time Users)

```bash
# 1. Make the setup script executable
chmod +x setup.sh

# 2. Run the automated setup
./setup.sh

# 3. The script will:
#    - Check for required tools (Node.js, Python, Java, Ruby, PHP)
#    - Install frontend dependencies
#    - Install backend dependencies
#    - Create configuration files
#    - Display next steps
```

### Option 2: Docker Compose (Best for Isolated Environment)

**Prerequisites:** Docker and Docker Compose installed

```bash
# 1. Copy environment configuration
cp .env.example .env

# 2. Start all services
docker-compose up --build

# 3. Access the application
# - Frontend: http://localhost:3001
# - Java API: http://localhost:8080
# - Python API: http://localhost:5000
```

### Option 3: Manual Installation with npm

```bash
# 1. Install all dependencies at once
npm run install:all

# 2. In one terminal, start the frontend
npm run dev

# 3. In another terminal, start the Python backend
cd backend-python
source venv/bin/activate
python app.py

# 4. In a third terminal, start the Java backend
cd backend-java
mvn spring-boot:run
```

## ✅ Verify Installation

After running any of the above options, verify that everything is working:

```bash
# Check frontend
curl http://localhost:3001

# Check Python backend
curl http://localhost:5000/health

# Check Java backend
curl http://localhost:8080/swagger-ui.html
```

## 📋 System Requirements

Before you start, ensure you have:

- **Node.js** 18+ - [Download](https://nodejs.org/)
- **Python** 3.9+ - [Download](https://www.python.org/)
- **Java JDK** 17+ - [Download](https://www.oracle.com/java/)
- **Ruby** 2.7+ (Optional) - [Download](https://www.ruby-lang.org/)
- **PHP** 8.0+ (Optional) - [Download](https://www.php.net/)

## 🔧 Configuration

The platform requires MongoDB and PostgreSQL. With Docker Compose, these are automatically set up. Otherwise:

**MongoDB:**
```bash
# Using Docker
docker run -d -p 27017:27017 --name mongodb mongo:latest

# Or install from https://www.mongodb.com/try/download/community
```

**PostgreSQL:**
```bash
# Using Docker
docker run -d -p 5432:5432 \
  -e POSTGRES_USER=siem \
  -e POSTGRES_PASSWORD=siem_password \
  -e POSTGRES_DB=siem \
  --name postgres \
  postgres:latest

# Or install from https://www.postgresql.org/download/
```

## 📝 Environment Variables

The setup script creates a `.env` file. You can customize it:

```bash
# Edit configuration
nano .env

# Key variables to customize:
# - FLASK_ENV: development or production
# - DATABASE_URL: MongoDB connection
# - POSTGRES_URL: PostgreSQL connection
# - JWT_SECRET: Change for production!
```

## 🚨 Troubleshooting

### Port Already in Use
```bash
# Find process using port (e.g., 5000)
lsof -i :5000

# Kill the process
kill -9 <PID>
```

### Python Virtual Environment Issues
```bash
# Reset virtual environment
rm -rf backend-python/venv
python3 -m venv backend-python/venv
source backend-python/venv/bin/activate
pip install -r backend-python/requirements.txt
```

### Node Dependencies Issues
```bash
# Clean reinstall
rm -rf frontend/node_modules
cd frontend
npm install
```

### MongoDB Connection Issues
```bash
# Test MongoDB connection
mongosh --eval "db.adminCommand('ping')"
```

## 📚 Next Steps

1. Read the [INSTALL.md](INSTALL.md) for detailed setup instructions
2. Check the [docs/](docs/) folder for architecture and API documentation
3. Review [README.md](README.md) for full feature list
4. Start developing or integrating with your security infrastructure

## 🆘 Need Help?

- Review [INSTALL.md](INSTALL.md) for detailed troubleshooting
- Check GitHub issues for solutions
- See [docs/](docs/) for comprehensive documentation

## 🎯 Default Ports

- **Frontend**: http://localhost:3001
- **Java API**: http://localhost:8080
- **Python Service**: http://localhost:5000
- **Ruby Service**: http://localhost:3000
- **PHP Service**: http://localhost:8081
- **MongoDB**: localhost:27017
- **PostgreSQL**: localhost:5432

## 💡 Pro Tips

1. **Use npm scripts**: Available commands in root `package.json`
   ```bash
   npm run install:all    # Install all components
   npm run build:all      # Build all components
   npm run test:all       # Test all components
   npm run docker:up      # Start with Docker
   ```

2. **Keep services separate**: Run each service in its own terminal for easier debugging

3. **Monitor logs**: Use `docker-compose logs -f` for real-time logs

4. **Development mode**: Always use the setup script's results and follow INSTALL.md for manual configuration

5. **Production deployment**: See [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) for production setup

---

**Ready to go?** Run `./setup.sh` or `docker-compose up --build` now!
