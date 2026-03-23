FROM ruby:3.2-alpine

WORKDIR /app

# Install system dependencies
RUN apk add --no-cache \
    build-base \
    curl

# Copy Gemfile
COPY Gemfile Gemfile.lock* ./

# Install gems
RUN bundle install --jobs 4 --retry 3

# Copy application
COPY . .

# Health check
HEALTHCHECK --interval=10s --timeout=5s --retries=5 \
    CMD curl -f http://localhost:3000/health || exit 1

EXPOSE 3000

CMD ["bundle", "exec", "ruby", "app.rb"]