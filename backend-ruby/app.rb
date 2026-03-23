# frozen_string_literal: true

# SIEM Platform - Ruby Automation Engine
#
# Sinatra service that executes security playbooks, schedules correlation
# tasks, and orchestrates responses across the SIEM microservices.
#
# Port: 3000

require 'sinatra'
require 'sinatra/json'
require 'sinatra/reloader' if development?
require 'rack/cors'
require 'dotenv/load'
require 'logger'
require 'json'
require 'securerandom'
require 'time'

require_relative 'lib/playbooks'
require_relative 'lib/scheduler'

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

LOGGER = Logger.new($stdout).tap do |l|
  l.progname  = 'automation-engine'
  l.level     = ENV.fetch('LOG_LEVEL', 'INFO').upcase
  l.formatter = proc do |sev, time, prog, msg|
    "#{time.utc.iso8601(3)} [#{sev}] #{prog} - #{msg}\n"
  end
end

# ---------------------------------------------------------------------------
# In-memory job store (use Redis / DB in production)
# ---------------------------------------------------------------------------

JOBS_MUTEX = Mutex.new
JOBS_STORE = {}   # job_id => Hash

def store_job(job)
  JOBS_MUTEX.synchronize { JOBS_STORE[job[:job_id]] = job }
end

def find_job(job_id)
  JOBS_MUTEX.synchronize { JOBS_STORE[job_id] }
end

def all_jobs
  JOBS_MUTEX.synchronize { JOBS_STORE.values.sort_by { |j| j[:started_at] }.reverse }
end

# ---------------------------------------------------------------------------
# Sinatra configuration
# ---------------------------------------------------------------------------

configure do
  set :port,         ENV.fetch('PORT', 3000).to_i
  set :bind,         '0.0.0.0'
  set :environment,  ENV.fetch('APP_ENV', 'production').to_sym
  set :show_exceptions, false
  set :raise_errors,    false
  disable :logging  # Use custom LOGGER instead
end

use Rack::Cors do
  allow do
    origins ENV.fetch('ALLOWED_ORIGINS', '*')
    resource '*',
      headers: :any,
      methods: %i[get post put delete options]
  end
end

# ---------------------------------------------------------------------------
# Before filter — parse JSON body, set response content type
# ---------------------------------------------------------------------------

before do
  content_type :json
  if request.post? || request.put?
    body = request.body.read
    unless body.empty?
      begin
        @parsed_body = JSON.parse(body, symbolize_names: true)
      rescue JSON::ParserError => e
        halt 400, { error: 'invalid_json', message: e.message }.to_json
      end
    end
    @parsed_body ||= {}
  end
end

# ---------------------------------------------------------------------------
# Error handling
# ---------------------------------------------------------------------------

error do
  err = env['sinatra.error']
  LOGGER.error "Unhandled exception: #{err.class}: #{err.message}\n#{err.backtrace.first(5).join("\n")}"
  status 500
  { error: 'internal_server_error', message: 'An unexpected error occurred.' }.to_json
end

not_found do
  status 404
  {
    error:   'not_found',
    message: "No route matches #{request.request_method} #{request.path_info}",
    available_routes: [
      'GET  /health',
      'GET  /automation/playbooks',
      'POST /automation/playbooks/execute',
      'GET  /automation/jobs',
      'POST /automation/schedule'
    ]
  }.to_json
end

# ---------------------------------------------------------------------------
# GET /health
# ---------------------------------------------------------------------------

get '/health' do
  status 200
  {
    status:    'healthy',
    service:   'ruby-automation-engine',
    version:   '1.0.0',
    timestamp: Time.now.utc.iso8601,
    scheduler: SIEMScheduler.running? ? 'running' : 'stopped',
    jobs_in_memory: all_jobs.size
  }.to_json
end

# ---------------------------------------------------------------------------
# GET /automation/playbooks
# ---------------------------------------------------------------------------

get '/automation/playbooks' do
  books = PlaybookRegistry.all.map do |name, pb|
    {
      name:        name,
      description: pb[:description],
      trigger:     pb[:trigger],
      actions:     pb[:actions].map { |a| a[:name] }
    }
  end
  { playbooks: books, count: books.size }.to_json
end

# ---------------------------------------------------------------------------
# POST /automation/playbooks/execute
# ---------------------------------------------------------------------------

post '/automation/playbooks/execute' do
  playbook_name = @parsed_body[:playbook_name]&.to_s
  event_data    = @parsed_body[:event_data] || {}
  context       = @parsed_body[:context]    || {}

  unless playbook_name && !playbook_name.empty?
    halt 400, { error: 'validation_error', message: '`playbook_name` is required.' }.to_json
  end

  unless PlaybookRegistry.exists?(playbook_name)
    halt 404, {
      error:              'playbook_not_found',
      message:            "Playbook '#{playbook_name}' does not exist.",
      available_playbooks: PlaybookRegistry.names
    }.to_json
  end

  job_id = SecureRandom.uuid
  job = {
    job_id:        job_id,
    playbook_name: playbook_name,
    status:        'running',
    started_at:    Time.now.utc.iso8601(3),
    completed_at:  nil,
    event_data:    event_data,
    context:       context,
    actions_taken: [],
    errors:        []
  }
  store_job(job)

  LOGGER.info "Executing playbook '#{playbook_name}' [job=#{job_id}]"

  executor = PlaybookExecutor.new(job_id: job_id, logger: LOGGER)
  result   = executor.execute(playbook_name, event_data: event_data, context: context)

  job.merge!(
    status:        result[:success] ? 'completed' : 'failed',
    completed_at:  Time.now.utc.iso8601(3),
    actions_taken: result[:actions_taken],
    errors:        result[:errors]
  )
  store_job(job)

  http_status = result[:success] ? 200 : 207
  status http_status

  {
    job_id:        job_id,
    playbook_name: playbook_name,
    status:        job[:status],
    started_at:    job[:started_at],
    completed_at:  job[:completed_at],
    actions_taken: result[:actions_taken],
    errors:        result[:errors],
    summary:       result[:summary]
  }.to_json
end

# ---------------------------------------------------------------------------
# GET /automation/jobs
# ---------------------------------------------------------------------------

get '/automation/jobs' do
  page     = [params[:page].to_i,     1].max
  per_page = [params[:per_page].to_i, 20].max
  per_page = [per_page, 100].min

  jobs = all_jobs
  jobs = jobs.select { |j| j[:status] == params[:status] } if params[:status]
  jobs = jobs.select { |j| j[:playbook_name] == params[:playbook] } if params[:playbook]

  total  = jobs.size
  paged  = jobs.slice((page - 1) * per_page, per_page) || []

  {
    jobs:       paged,
    pagination: { total: total, page: page, per_page: per_page, pages: (total.to_f / per_page).ceil }
  }.to_json
end

# ---------------------------------------------------------------------------
# POST /automation/schedule
# ---------------------------------------------------------------------------

post '/automation/schedule' do
  playbook_name = @parsed_body[:playbook_name]&.to_s
  cron_expr     = @parsed_body[:cron]&.to_s
  interval_sec  = @parsed_body[:interval_seconds]&.to_i
  event_data    = @parsed_body[:event_data] || {}

  unless playbook_name && !playbook_name.empty?
    halt 400, { error: 'validation_error', message: '`playbook_name` is required.' }.to_json
  end

  unless PlaybookRegistry.exists?(playbook_name)
    halt 404, { error: 'playbook_not_found', message: "Playbook '#{playbook_name}' not found." }.to_json
  end

  unless cron_expr || interval_sec&.positive?
    halt 400, { error: 'validation_error', message: 'Provide either `cron` or `interval_seconds`.' }.to_json
  end

  schedule_id = SIEMScheduler.schedule_playbook(
    playbook_name: playbook_name,
    cron:          cron_expr,
    interval:      interval_sec,
    event_data:    event_data,
    logger:        LOGGER
  )

  status 201
  {
    schedule_id:   schedule_id,
    playbook_name: playbook_name,
    cron:          cron_expr,
    interval_seconds: interval_sec,
    status:        'scheduled',
    message:       "Playbook '#{playbook_name}' has been scheduled."
  }.to_json
end

# ---------------------------------------------------------------------------
# Start background scheduler
# ---------------------------------------------------------------------------

SIEMScheduler.start(logger: LOGGER)
LOGGER.info 'Automation engine started'
