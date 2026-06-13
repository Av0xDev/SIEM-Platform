#!/bin/bash

################################################################################
# SIEM Platform - Automated Setup Script
# This script automates the installation of all dependencies for the SIEM Platform
# Supports: Node.js, Python, Java, Ruby, and PHP
################################################################################

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Counters
INSTALLED=0
FAILED=0
SKIPPED=0

################################################################################
# Helper Functions
################################################################################

print_header() {
    echo -e "${BLUE}===================================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}===================================================${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
    ((INSTALLED++))
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
    ((FAILED++))
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
    ((SKIPPED++))
}

print_info() {
    echo -e "${BLUE}ℹ $1${NC}"
}

check_command() {
    if ! command -v "$1" &> /dev/null; then
        return 1
    fi
    return 0
}

################################################################################
# Requirement Checks
################################################################################

check_requirements() {
    print_header "Checking Prerequisites"

    local missing_tools=()

    # Check Node.js
    if ! check_command node; then
        missing_tools+=("Node.js (https://nodejs.org/)")
    else
        local node_version=$(node -v)
        print_success "Node.js found: $node_version"
    fi

    # Check Python
    if ! check_command python3; then
        missing_tools+=("Python 3 (https://www.python.org/)")
    else
        local python_version=$(python3 --version)
        print_success "Python found: $python_version"
    fi

    # Check Java
    if ! check_command java; then
        missing_tools+=("Java JDK (https://www.oracle.com/java/technologies/downloads/)")
    else
        local java_version=$(java -version 2>&1 | head -n 1)
        print_success "Java found: $java_version"
    fi

    # Check Ruby
    if ! check_command ruby; then
        missing_tools+=("Ruby (https://www.ruby-lang.org/)")
    else
        local ruby_version=$(ruby -v)
        print_success "Ruby found: $ruby_version"
    fi

    # Check PHP
    if ! check_command php; then
        missing_tools+=("PHP (https://www.php.net/)")
    else
        local php_version=$(php -v | head -n 1)
        print_success "PHP found: $php_version"
    fi

    # Check npm
    if ! check_command npm; then
        missing_tools+=("npm (comes with Node.js)")
    else
        local npm_version=$(npm -v)
        print_success "npm found: v$npm_version"
    fi

    # Check pip
    if ! check_command pip3; then
        missing_tools+=("pip (comes with Python)")
    else
        local pip_version=$(pip3 --version)
        print_success "pip found: $pip_version"
    fi

    # Check Maven
    if ! check_command mvn; then
        print_warning "Maven not found. Java compilation may fail. Install from https://maven.apache.org/"
    else
        local mvn_version=$(mvn -version | head -n 1)
        print_success "Maven found: $mvn_version"
    fi

    # Check Bundler
    if ! check_command bundle; then
        print_warning "Bundler not found. Installing..."
        gem install bundler 2>/dev/null && print_success "Bundler installed" || print_error "Failed to install Bundler"
    else
        print_success "Bundler found"
    fi

    # Check Composer
    if ! check_command composer; then
        print_warning "Composer not found. PHP dependencies will be skipped."
    else
        print_success "Composer found"
    fi

    # Display summary
    echo ""
    if [ ${#missing_tools[@]} -eq 0 ]; then
        print_success "All required tools are installed!"
    else
        echo -e "${RED}Missing tools:${NC}"
        for tool in "${missing_tools[@]}"; do
            echo -e "  ${RED}• $tool${NC}"
        done
        echo ""
        print_error "Please install missing tools before running this script."
        exit 1
    fi
}

################################################################################
# Frontend Setup
################################################################################

setup_frontend() {
    print_header "Installing Frontend Dependencies"

    if [ ! -d "frontend" ]; then
        print_error "frontend directory not found"
        return 1
    fi

    cd frontend

    if [ -f "package.json" ]; then
        print_info "Installing npm dependencies..."
        if npm install 2>&1 | tail -n 5; then
            print_success "Frontend dependencies installed"
        else
            print_error "Failed to install frontend dependencies"
            cd ..
            return 1
        fi
    else
        print_error "package.json not found in frontend"
        cd ..
        return 1
    fi

    cd ..
}

################################################################################
# Python Backend Setup
################################################################################

setup_python() {
    print_header "Installing Python Backend Dependencies"

    if [ ! -d "backend-python" ]; then
        print_error "backend-python directory not found"
        return 1
    fi

    cd backend-python

    if [ -f "requirements.txt" ]; then
        print_info "Creating Python virtual environment..."
        if python3 -m venv venv 2>&1 > /dev/null; then
            print_success "Virtual environment created"

            print_info "Activating virtual environment and installing dependencies..."
            source venv/bin/activate 2>/dev/null || . venv/Scripts/activate 2>/dev/null
            
            if pip install -r requirements.txt 2>&1 | tail -n 3; then
                print_success "Python backend dependencies installed"
            else
                print_error "Failed to install Python backend dependencies"
                cd ..
                return 1
            fi
            
            deactivate 2>/dev/null || true
        else
            print_error "Failed to create Python virtual environment"
            cd ..
            return 1
        fi
    else
        print_error "requirements.txt not found in backend-python"
        cd ..
        return 1
    fi

    cd ..
}

################################################################################
# Java Backend Setup
################################################################################

setup_java() {
    print_header "Installing Java Backend Dependencies"

    if [ ! -d "backend-java" ]; then
        print_error "backend-java directory not found"
        return 1
    fi

    if ! check_command mvn; then
        print_error "Maven is not installed. Skipping Java backend setup."
        print_info "Install Maven from: https://maven.apache.org/download.cgi"
        return 1
    fi

    cd backend-java

    if [ -f "pom.xml" ]; then
        print_info "Building Java backend with Maven..."
        if mvn clean install -q 2>&1 | tail -n 3; then
            print_success "Java backend dependencies installed and project built"
        else
            print_error "Failed to build Java backend"
            cd ..
            return 1
        fi
    else
        print_error "pom.xml not found in backend-java"
        cd ..
        return 1
    fi

    cd ..
}

################################################################################
# Ruby Backend Setup
################################################################################

setup_ruby() {
    print_header "Installing Ruby Backend Dependencies"

    if [ ! -d "backend-ruby" ]; then
        print_error "backend-ruby directory not found"
        return 1
    fi

    cd backend-ruby

    if [ -f "Gemfile" ]; then
        print_info "Installing Ruby dependencies with Bundler..."
        if bundle install 2>&1 | tail -n 3; then
            print_success "Ruby backend dependencies installed"
        else
            print_error "Failed to install Ruby backend dependencies"
            cd ..
            return 1
        fi
    else
        print_error "Gemfile not found in backend-ruby"
        cd ..
        return 1
    fi

    cd ..
}

################################################################################
# PHP Backend Setup
################################################################################

setup_php() {
    print_header "Installing PHP Backend Dependencies"

    if [ ! -d "backend-php" ]; then
        print_error "backend-php directory not found"
        return 1
    fi

    if ! check_command composer; then
        print_warning "Composer not installed. Skipping PHP backend setup."
        print_info "Install Composer from: https://getcomposer.org/download/"
        return 0
    fi

    cd backend-php

    if [ -f "composer.json" ]; then
        print_info "Installing PHP dependencies with Composer..."
        if composer install 2>&1 | tail -n 3; then
            print_success "PHP backend dependencies installed"
        else
            print_error "Failed to install PHP backend dependencies"
            cd ..
            return 1
        fi
    else
        print_warning "composer.json not found in backend-php. Skipping."
        cd ..
        return 0
    fi

    cd ..
}

################################################################################
# Environment Setup
################################################################################

setup_env() {
    print_header "Setting Up Configuration"

    if [ ! -f ".env" ]; then
        if [ -f ".env.example" ]; then
            print_info "Creating .env file from .env.example..."
            cp .env.example .env
            print_success ".env file created"
        else
            print_warning ".env.example not found. Creating default .env file..."
            create_default_env
            print_success "Default .env file created"
        fi
    else
        print_info ".env file already exists"
    fi
}

create_default_env() {
    cat > .env << 'EOF'
# SIEM Platform Configuration

# Frontend Configuration
REACT_APP_API_URL=http://localhost:8080/api
VITE_API_URL=http://localhost:8080/api

# Python Backend Configuration
FLASK_ENV=development
DATABASE_URL=mongodb://localhost:27017/siem
POSTGRES_URL=******localhost:5432/siem
SECRET_KEY=change-me-in-production

# Java Backend Configuration
SERVER_PORT=8080
SPRING_DATA_MONGODB_URI=mongodb://localhost:27017/siem
SPRING_DATASOURCE_URL=jdbc:postgresql://localhost:5432/siem
SPRING_DATASOURCE_USERNAME=siem
SPRING_DATASOURCE_PASSWORD=siem_password

# Ruby Backend Configuration
RACK_ENV=development
PORT=3000

# PHP Backend Configuration
ENVIRONMENT=development
DB_HOST=localhost
DB_USER=siem
DB_PASS=siem_password
EOF
}

################################################################################
# Docker Compose Check
################################################################################

check_docker_compose() {
    print_header "Docker Setup (Optional)"

    if check_command docker && check_command docker-compose; then
        print_success "Docker and Docker Compose are installed"
        print_info "To run all services with Docker, execute: docker-compose up"
        print_info "To stop services, execute: docker-compose down"
    else
        print_warning "Docker and/or Docker Compose not found"
        print_info "Install from: https://www.docker.com/products/docker-desktop"
    fi
}

################################################################################
# Summary Report
################################################################################

print_summary() {
    print_header "Installation Summary"

    echo -e "Installation Status:"
    echo -e "  ${GREEN}✓ Completed: $INSTALLED${NC}"
    if [ $FAILED -gt 0 ]; then
        echo -e "  ${RED}✗ Failed: $FAILED${NC}"
    fi
    if [ $SKIPPED -gt 0 ]; then
        echo -e "  ${YELLOW}⚠ Skipped: $SKIPPED${NC}"
    fi

    echo ""
    echo -e "${GREEN}Next steps:${NC}"
    echo "  1. Review .env configuration file and update if needed"
    echo "  2. Ensure MongoDB and PostgreSQL are running"
    echo "  3. Start services individually or with Docker Compose:"
    echo ""
    echo "     Option A - Individual Services:"
    echo "       Terminal 1: cd frontend && npm run dev"
    echo "       Terminal 2: cd backend-python && source venv/bin/activate && python app.py"
    echo "       Terminal 3: cd backend-java && mvn spring-boot:run"
    echo "       Terminal 4: cd backend-ruby && ruby app.rb"
    echo "       Terminal 5: cd backend-php && php -S localhost:8081"
    echo ""
    echo "     Option B - Docker Compose:"
    echo "       docker-compose up"
    echo ""
    echo -e "${GREEN}Access the application:${NC}"
    echo "  • Frontend:        http://localhost:3001"
    echo "  • Python API:      http://localhost:5000"
    echo "  • Java API:        http://localhost:8080"
    echo "  • Java Swagger:    http://localhost:8080/swagger-ui.html"
    echo ""
    echo -e "${GREEN}For more information, see INSTALL.md${NC}"
}

################################################################################
# Main Execution
################################################################################

main() {
    print_header "SIEM Platform - Automated Setup"
    echo ""

    # Check system requirements
    check_requirements
    echo ""

    # Setup each component
    setup_frontend || true
    echo ""

    setup_python || true
    echo ""

    setup_java || true
    echo ""

    setup_ruby || true
    echo ""

    setup_php || true
    echo ""

    # Setup configuration
    setup_env
    echo ""

    # Check Docker
    check_docker_compose
    echo ""

    # Print summary
    print_summary
}

# Run main function
main
