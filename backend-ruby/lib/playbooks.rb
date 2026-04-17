# frozen_string_literal: true

# SIEM Platform - Playbook Definitions and Executor
#
# Defines built-in security-response playbooks and the engine that executes
# their action steps, coordinating with external services via HTTP.

require 'httparty'
require 'json'
require 'time'
require 'logger'

# ---------------------------------------------------------------------------
# Service HTTP client helpers
# ---------------------------------------------------------------------------

module ServiceClient
  PYTHON_URL = ENV.fetch('PYTHON_SERVICE_URL', 'http://python-service:5000')
  JAVA_URL   = ENV.fetch('JAVA_SERVICE_URL',   'http://java-service:8080')
  TIMEOUT    = 5

  def self.post(url, path, body)
    response = HTTParty.post(
      "#{url}#{path}",
      headers: {
        'Content-Type'  => 'application/json',
        'X-Service-Key' => ENV.fetch('INTERNAL_SERVICE_KEY', 'internal-key'),
        'X-Source'      => 'ruby-automation'
      },
      body:    body.to_json,
      timeout: TIMEOUT
    )
    { success: response.success?, status: response.code, body: response.parsed_response }
  rescue StandardError => e
    { success: false, status: 0, body: nil, error: e.message }
  end

  def self.get(url, path)
    response = HTTParty.get(
      "#{url}#{path}",
      headers: {
        'Accept'        => 'application/json',
        'X-Service-Key' => ENV.fetch('INTERNAL_SERVICE_KEY', 'internal-key'),
        'X-Source'      => 'ruby-automation'
      },
      timeout: TIMEOUT
    )
    { success: response.success?, status: response.code, body: response.parsed_response }
  rescue StandardError => e
    { success: false, status: 0, body: nil, error: e.message }
  end
end

# ---------------------------------------------------------------------------
# Playbook Registry
# ---------------------------------------------------------------------------

module PlaybookRegistry
  # Each playbook is a Hash with keys:
  #   :description  - human-readable summary
  #   :trigger      - event_type that typically triggers this playbook
  #   :actions      - ordered Array of action Hashes
  #
  # Each action Hash has:
  #   :name         - action identifier
  #   :description  - human-readable description
  #   :handler      - Symbol matching a method on PlaybookExecutor (prefixed with `action_`)
  #   :params       - static params merged with runtime event_data at execution time

  REGISTRY = {
    'brute_force_response' => {
      description: 'Respond to a detected brute-force attack by blocking the source IP, ' \
                   'disabling the targeted account, and creating an incident.',
      trigger: 'brute_force_detected',
      actions: [
        {
          name:        'log_detection',
          description: 'Log the brute-force detection event',
          handler:     :log_detection,
          params:      { severity: 'high', category: 'authentication' }
        },
        {
          name:        'block_source_ip',
          description: 'Add source IP to firewall block-list via Java service',
          handler:     :block_ip,
          params:      {}
        },
        {
          name:        'disable_account',
          description: 'Temporarily disable the targeted user account',
          handler:     :disable_account,
          params:      { reason: 'brute_force_detected', duration_minutes: 30 }
        },
        {
          name:        'create_incident',
          description: 'Create a security incident in the SIEM',
          handler:     :create_incident,
          params:      { severity: 'high', type: 'brute_force' }
        },
        {
          name:        'send_notification',
          description: 'Notify the SOC team',
          handler:     :send_notification,
          params:      { channel: 'soc-alerts', priority: 'high' }
        }
      ]
    },

    'malware_response' => {
      description: 'Contain and remediate a malware detection: isolate host, kill processes, ' \
                   'collect forensics, and create a critical incident.',
      trigger: 'malware_detected',
      actions: [
        {
          name:        'log_detection',
          description: 'Log the malware detection event',
          handler:     :log_detection,
          params:      { severity: 'critical', category: 'malware' }
        },
        {
          name:        'isolate_host',
          description: 'Network-isolate the affected host via Java service',
          handler:     :isolate_host,
          params:      {}
        },
        {
          name:        'kill_malicious_processes',
          description: 'Terminate identified malicious processes',
          handler:     :kill_processes,
          params:      {}
        },
        {
          name:        'collect_forensics',
          description: 'Collect memory dump and artefacts for analysis',
          handler:     :collect_forensics,
          params:      { artefact_types: %w[memory_dump process_list network_connections] }
        },
        {
          name:        'create_incident',
          description: 'Create a critical security incident',
          handler:     :create_incident,
          params:      { severity: 'critical', type: 'malware' }
        },
        {
          name:        'send_notification',
          description: 'Page the on-call security engineer',
          handler:     :send_notification,
          params:      { channel: 'soc-critical', priority: 'critical' }
        }
      ]
    },

    'data_exfiltration_response' => {
      description: 'Respond to suspected data exfiltration: block egress, revoke tokens, ' \
                   'audit accessed data, and escalate.',
      trigger: 'data_exfiltration_detected',
      actions: [
        {
          name:        'log_detection',
          description: 'Log the data exfiltration event',
          handler:     :log_detection,
          params:      { severity: 'critical', category: 'data_loss' }
        },
        {
          name:        'block_egress',
          description: 'Block outbound traffic to the destination IP',
          handler:     :block_ip,
          params:      { direction: 'egress' }
        },
        {
          name:        'revoke_tokens',
          description: 'Revoke all active sessions and API tokens for the user',
          handler:     :revoke_tokens,
          params:      {}
        },
        {
          name:        'audit_data_access',
          description: 'Retrieve recent data-access logs for the user/host',
          handler:     :audit_data_access,
          params:      { look_back_hours: 24 }
        },
        {
          name:        'create_incident',
          description: 'Create a critical DLP incident',
          handler:     :create_incident,
          params:      { severity: 'critical', type: 'data_exfiltration' }
        },
        {
          name:        'send_notification',
          description: 'Notify SOC and management',
          handler:     :send_notification,
          params:      { channel: 'soc-critical', priority: 'critical', escalate_to_management: true }
        }
      ]
    },

    'unauthorized_access_response' => {
      description: 'Respond to unauthorised access: revoke session, enforce MFA, alert.',
      trigger: 'unauthorized_access',
      actions: [
        {
          name:        'log_detection',
          description: 'Log the unauthorised access event',
          handler:     :log_detection,
          params:      { severity: 'high', category: 'access_control' }
        },
        {
          name:        'revoke_tokens',
          description: 'Revoke active sessions for the compromised account',
          handler:     :revoke_tokens,
          params:      {}
        },
        {
          name:        'enforce_mfa',
          description: 'Force MFA challenge on next login',
          handler:     :enforce_mfa,
          params:      {}
        },
        {
          name:        'create_incident',
          description: 'Create a security incident',
          handler:     :create_incident,
          params:      { severity: 'high', type: 'unauthorized_access' }
        },
        {
          name:        'send_notification',
          description: 'Notify the SOC team',
          handler:     :send_notification,
          params:      { channel: 'soc-alerts', priority: 'high' }
        }
      ]
    }
  }.freeze

  def self.all = REGISTRY

  def self.names = REGISTRY.keys

  def self.exists?(name) = REGISTRY.key?(name)

  def self.[](name) = REGISTRY[name]
end

# ---------------------------------------------------------------------------
# Playbook Executor
# ---------------------------------------------------------------------------

class PlaybookExecutor
  attr_reader :job_id, :logger

  def initialize(job_id:, logger: Logger.new($stdout))
    @job_id = job_id
    @logger = logger
  end

  # Execute a named playbook and return a result hash.
  def execute(playbook_name, event_data: {}, context: {})
    playbook       = PlaybookRegistry[playbook_name]
    actions_taken  = []
    errors         = []

    playbook[:actions].each do |action|
      merged_params = action[:params].merge(
        event_data:    event_data,
        context:       context,
        job_id:        job_id,
        playbook_name: playbook_name
      )

      logger.info "[job=#{job_id}] Running action '#{action[:name]}'"
      result = dispatch(action[:handler], merged_params)

      entry = {
        name:        action[:name],
        description: action[:description],
        status:      result[:success] ? 'success' : 'failed',
        executed_at: Time.now.utc.iso8601(3),
        detail:      result[:detail]
      }
      actions_taken << entry

      unless result[:success]
        errors << { action: action[:name], error: result[:error] || result[:detail] }
        logger.warn "[job=#{job_id}] Action '#{action[:name]}' failed: #{result[:error]}"
        # Continue executing remaining actions (best-effort response).
      end
    end

    success = errors.empty?
    {
      success:       success,
      actions_taken: actions_taken,
      errors:        errors,
      summary:       build_summary(playbook_name, actions_taken, errors)
    }
  end

  private

  # Dispatch to the matching action_ method.
  def dispatch(handler, params)
    method_name = :"action_#{handler}"
    if respond_to?(method_name, true)
      send(method_name, params)
    else
      { success: false, error: "Unknown handler '#{handler}'" }
    end
  rescue StandardError => e
    logger.error "[job=#{job_id}] Exception in handler '#{handler}': #{e.message}"
    { success: false, error: e.message }
  end

  # -------------------------------------------------------------------------
  # Action handlers
  # -------------------------------------------------------------------------

  def action_log_detection(params)
    event = {
      event_type:    'playbook_action',
      action:        'log_detection',
      job_id:        params[:job_id],
      playbook_name: params[:playbook_name],
      severity:      params[:severity] || 'medium',
      category:      params[:category] || 'general',
      event_data:    params[:event_data],
      timestamp:     Time.now.utc.iso8601(3)
    }
    result = ServiceClient.post(ServiceClient::PYTHON_URL, '/api/logs/ingest', event)
    {
      success: result[:success],
      detail:  "Logged detection event (HTTP #{result[:status]})",
      error:   result[:error]
    }
  end

  def action_block_ip(params)
    ip        = params.dig(:event_data, :source_ip) || params.dig(:event_data, 'source_ip')
    direction = params[:direction] || 'ingress'

    unless ip
      return { success: false, error: 'source_ip not present in event_data' }
    end

    result = ServiceClient.post(ServiceClient::JAVA_URL, '/api/response/block-ip', {
      ip:        ip,
      direction: direction,
      job_id:    params[:job_id],
      reason:    "Automated response by playbook '#{params[:playbook_name]}'"
    })
    {
      success: result[:success],
      detail:  "Block IP #{ip} #{direction} (HTTP #{result[:status]})",
      error:   result[:error]
    }
  end

  def action_disable_account(params)
    user = params.dig(:event_data, :user) || params.dig(:event_data, 'user')
    unless user
      return { success: false, error: 'user not present in event_data' }
    end

    result = ServiceClient.post(ServiceClient::JAVA_URL, '/api/response/disable-account', {
      username:         user,
      reason:           params[:reason] || 'security_policy',
      duration_minutes: params[:duration_minutes] || 30,
      job_id:           params[:job_id]
    })
    {
      success: result[:success],
      detail:  "Disabled account '#{user}' for #{params[:duration_minutes] || 30} minutes (HTTP #{result[:status]})",
      error:   result[:error]
    }
  end

  def action_isolate_host(params)
    host = params.dig(:event_data, :host) || params.dig(:event_data, 'host')
    unless host
      return { success: false, error: 'host not present in event_data' }
    end

    result = ServiceClient.post(ServiceClient::JAVA_URL, '/api/response/isolate-host', {
      host:   host,
      job_id: params[:job_id],
      reason: "Malware containment by playbook '#{params[:playbook_name]}'"
    })
    {
      success: result[:success],
      detail:  "Isolated host '#{host}' (HTTP #{result[:status]})",
      error:   result[:error]
    }
  end

  def action_kill_processes(params)
    host      = params.dig(:event_data, :host)      || params.dig(:event_data, 'host')
    processes = params.dig(:event_data, :processes) || params.dig(:event_data, 'processes') || []

    result = ServiceClient.post(ServiceClient::JAVA_URL, '/api/response/kill-processes', {
      host:      host,
      processes: processes,
      job_id:    params[:job_id]
    })
    {
      success: result[:success],
      detail:  "Kill-process command sent (HTTP #{result[:status]})",
      error:   result[:error]
    }
  end

  def action_collect_forensics(params)
    host = params.dig(:event_data, :host) || params.dig(:event_data, 'host')
    result = ServiceClient.post(ServiceClient::JAVA_URL, '/api/response/collect-forensics', {
      host:           host,
      artefact_types: params[:artefact_types] || [],
      job_id:         params[:job_id]
    })
    {
      success: result[:success],
      detail:  "Forensic collection initiated (HTTP #{result[:status]})",
      error:   result[:error]
    }
  end

  def action_create_incident(params)
    result = ServiceClient.post(ServiceClient::PYTHON_URL, '/api/incidents', {
      title:    "Auto-created by playbook '#{params[:playbook_name]}'",
      severity: params[:severity] || 'medium',
      type:     params[:type]     || 'generic',
      job_id:   params[:job_id],
      source:   'ruby-automation',
      event_data: params[:event_data],
      created_at: Time.now.utc.iso8601(3)
    })
    {
      success: result[:success],
      detail:  "Incident created (HTTP #{result[:status]})",
      error:   result[:error]
    }
  end

  def action_send_notification(params)
    result = ServiceClient.post(ServiceClient::PYTHON_URL, '/api/notifications', {
      channel:               params[:channel]  || 'soc-alerts',
      priority:              params[:priority] || 'medium',
      escalate_to_management: params[:escalate_to_management] || false,
      message:               "Playbook '#{params[:playbook_name]}' executed for job #{params[:job_id]}",
      job_id:                params[:job_id],
      event_data:            params[:event_data],
      timestamp:             Time.now.utc.iso8601(3)
    })
    {
      success: result[:success],
      detail:  "Notification sent to #{params[:channel]} (HTTP #{result[:status]})",
      error:   result[:error]
    }
  end

  def action_revoke_tokens(params)
    user = params.dig(:event_data, :user) || params.dig(:event_data, 'user')
    unless user
      return { success: false, error: 'user not present in event_data' }
    end

    result = ServiceClient.post(ServiceClient::JAVA_URL, '/api/response/revoke-tokens', {
      username: user,
      job_id:   params[:job_id],
      reason:   "Security playbook '#{params[:playbook_name]}'"
    })
    {
      success: result[:success],
      detail:  "Revoked tokens for user '#{user}' (HTTP #{result[:status]})",
      error:   result[:error]
    }
  end

  def action_audit_data_access(params)
    user = params.dig(:event_data, :user) || params.dig(:event_data, 'user')
    result = ServiceClient.get(
      ServiceClient::PYTHON_URL,
      "/api/audit/data-access?user=#{user}&hours=#{params[:look_back_hours] || 24}"
    )
    {
      success: result[:success],
      detail:  "Data-access audit retrieved (HTTP #{result[:status]})",
      error:   result[:error]
    }
  end

  def action_enforce_mfa(params)
    user = params.dig(:event_data, :user) || params.dig(:event_data, 'user')
    unless user
      return { success: false, error: 'user not present in event_data' }
    end

    result = ServiceClient.post(ServiceClient::JAVA_URL, '/api/response/enforce-mfa', {
      username: user,
      job_id:   params[:job_id]
    })
    {
      success: result[:success],
      detail:  "MFA enforced for user '#{user}' (HTTP #{result[:status]})",
      error:   result[:error]
    }
  end

  # -------------------------------------------------------------------------
  # Summary builder
  # -------------------------------------------------------------------------

  def build_summary(playbook_name, actions_taken, errors)
    total    = actions_taken.size
    success  = actions_taken.count { |a| a[:status] == 'success' }
    "Playbook '#{playbook_name}': #{success}/#{total} actions succeeded" \
      "#{errors.empty? ? '' : ", #{errors.size} failed"}."
  end
end
