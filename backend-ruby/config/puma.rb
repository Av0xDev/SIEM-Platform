# frozen_string_literal: true

# Puma configuration for SIEM Ruby Automation Engine

port        ENV.fetch('PORT', 3000)
bind        "tcp://0.0.0.0:#{ENV.fetch('PORT', 3000)}"
environment ENV.fetch('APP_ENV', 'production')

workers     ENV.fetch('WEB_CONCURRENCY', 2).to_i
threads     ENV.fetch('MIN_THREADS', 2).to_i, ENV.fetch('MAX_THREADS', 8).to_i

preload_app!

on_worker_boot do
  # Re-establish any connections that are not fork-safe here.
end

pidfile     ENV.fetch('PIDFILE', '/tmp/puma.pid')
state_path  ENV.fetch('STATE', '/tmp/puma.state')
