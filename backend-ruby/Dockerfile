FROM ruby:3.2-slim

# System dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        libpq-dev \
        curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install gems first for layer caching
COPY Gemfile Gemfile.lock* ./
RUN bundle install --without test --jobs 4 --retry 3

# Copy application source
COPY . .

# Non-root user for security
RUN useradd -m -u 1001 appuser \
    && chown -R appuser:appuser /app
USER appuser

EXPOSE 3000

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD curl -fs http://localhost:3000/health || exit 1

CMD ["bundle", "exec", "puma", "-C", "config/puma.rb"]
