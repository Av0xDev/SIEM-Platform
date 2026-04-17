# ============================================================
# SIEM Platform - Java Backend Multi-Stage Dockerfile
# ============================================================

# Stage 1: Build
FROM maven:3.9.6-eclipse-temurin-17 AS builder

WORKDIR /app

# Copy only POM first for layer caching of dependencies
COPY pom.xml .
RUN mvn dependency:go-offline -B

# Copy source and build
COPY src ./src
RUN mvn package -DskipTests -B

# ============================================================
# Stage 2: Runtime
FROM eclipse-temurin:17-jre-jammy AS runtime

LABEL maintainer="SIEM Platform Team <siem-support@example.com>"
LABEL description="SIEM Platform Java Spring Boot Backend"
LABEL version="1.0.0"

# Create non-root user for security
RUN groupadd --gid 1001 siem && \
    useradd --uid 1001 --gid siem --shell /bin/bash --create-home siem

WORKDIR /app

# Copy the fat JAR from builder
COPY --from=builder /app/target/*.jar app.jar

# Set ownership
RUN chown -R siem:siem /app

USER siem

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8080/actuator/health || exit 1

EXPOSE 8080

ENTRYPOINT ["java", \
    "-XX:+UseContainerSupport", \
    "-XX:MaxRAMPercentage=75.0", \
    "-XX:+UseG1GC", \
    "-Djava.security.egd=file:/dev/./urandom", \
    "-jar", "app.jar"]
