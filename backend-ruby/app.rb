# SIEM Platform - Ruby Automation Service
require 'sinatra'
require 'json'
require 'net/http'
require 'logger'

set :port, 3000
set :bind, '0.0.0.0'
set :environment, :production

logger = Logger.new(STDOUT)
logger.level = Logger::INFO

# Middleware
use Rack::Logger

class AutomationEngine
  attr_reader :logger

  def initialize(logger)
    @logger = logger
    @java_service = ENV['JAVA_SERVICE_URL'] || 'http://localhost:8080'
    @python_service = ENV['PYTHON_SERVICE_URL'] || 'http://localhost:5000'
  end

  def execute_playbook(playbook_id, incident_id, params)
    logger.info "Executing playbook #{playbook_id} for incident #{incident_id}"

    case playbook_id
    when 'isolate_host'
      isolate_host(params[:host_ip])
    when 'block_ip'
      block_ip(params[:source_ip])
    when 'disable_user'
      disable_user(params[:user_id])
    when 'escalate_incident'
      escalate_incident(incident_id, params[:escalation_level])
    when 'notify_soc'
      notify_soc(incident_id)
    else
      { status: 'error', message: 'Unknown playbook' }
    end
  end

  private

  def isolate_host(host_ip)
    logger.info "Isolating host: #{host_ip}"
    { status: 'success', action: 'isolate_host', target: host_ip }
  end

  def block_ip(source_ip)
    logger.info "Blocking IP: #{source_ip}"
    { status: 'success', action: 'block_ip', target: source_ip }
  end

  def disable_user(user_id)
    logger.info "Disabling user: #{user_id}"
    { status: 'success', action: 'disable_user', target: user_id }
  end

  def escalate_incident(incident_id, level)
    logger.info "Escalating incident #{incident_id} to level #{level}"
    {
      status: 'success',
      action: 'escalate',
      incident_id: incident_id,
      escalation_level: level
    }
  end

  def notify_soc(incident_id)
    logger.info "Notifying SOC team for incident #{incident_id}"
    { status: 'success', action: 'notify_soc', incident_id: incident_id }
  end
end

engine = AutomationEngine.new(logger)

# Health check endpoint
get '/health' do
  content_type :json
  {
    status: 'healthy',
    timestamp: Time.now.iso8601,
    service: 'Ruby Automation Service'
  }.to_json
end

# Get available playbooks
get '/api/playbooks' do
  content_type :json
  {
    playbooks: [
      { id: 'isolate_host', name: 'Isolate Host', description: 'Isolate infected host from network' },
      { id: 'block_ip', name: 'Block IP', description: 'Block malicious IP address' },
      { id: 'disable_user', name: 'Disable User', description: 'Disable compromised user account' },
      { id: 'escalate_incident', name: 'Escalate Incident', description: 'Escalate incident severity' },
      { id: 'notify_soc', name: 'Notify SOC', description: 'Send alert to SOC team' }
    ]
  }.to_json
end

# Execute playbook
post '/api/playbooks/:id/execute' do
  content_type :json
  begin
    data = JSON.parse(request.body.read)
    incident_id = params[:incident_id]
    playbook_id = params[:id]

    result = engine.execute_playbook(playbook_id, incident_id, data)

    status 200
    {
      status: 'success',
      result: result,
      timestamp: Time.now.iso8601
    }.to_json
  rescue => e
    logger.error "Error executing playbook: #{e.message}"
    status 500
    { error: e.message }.to_json
  end
end

# Schedule recurring tasks
get '/api/tasks' do
  content_type :json
  {
    tasks: [
      { id: 1, name: 'Threat Intelligence Update', interval: '6h', status: 'scheduled' },
      { id: 2, name: 'Correlation Analysis', interval: '1h', status: 'running' },
      { id: 3, name: 'Report Generation', interval: '24h', status: 'scheduled' }
    ]
  }.to_json
end

# Error handling
error 404 do
  content_type :json
  { error: 'Endpoint not found' }.to_json
end

error 500 do
  content_type :json
  { error: 'Internal server error' }.to_json
end