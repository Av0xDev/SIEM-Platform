# frozen_string_literal: true

# SIEM Platform - Background Scheduler
#
# Wraps rufus-scheduler to run recurring correlation and housekeeping tasks.
# Playbooks can also be scheduled dynamically via the /automation/schedule API.

require 'rufus-scheduler'
require 'securerandom'
require 'logger'
require 'time'

module SIEMScheduler
  MUTEX = Mutex.new

  @scheduler    = nil
  @schedule_map = {}   # schedule_id => rufus job id

  module_function

  # Start the background scheduler and register built-in recurring tasks.
  def start(logger: Logger.new($stdout))
    MUTEX.synchronize do
      return if @scheduler&.running?

      @scheduler = Rufus::Scheduler.new
      @logger    = logger

      register_built_in_tasks
      @logger.info '[Scheduler] Started'
    end
  end

  # Schedule a playbook for periodic execution.
  # Returns a unique schedule_id.
  def schedule_playbook(playbook_name:, cron: nil, interval: nil, event_data: {}, logger: @logger)
    schedule_id = SecureRandom.uuid

    MUTEX.synchronize do
      unless @scheduler&.running?
        raise 'Scheduler is not running. Call SIEMScheduler.start first.'
      end

      job = if cron
              @scheduler.cron(cron, overlap: false, tag: schedule_id) do
                run_playbook_job(playbook_name, event_data, logger)
              end
            else
              @scheduler.every("#{interval}s", overlap: false, tag: schedule_id) do
                run_playbook_job(playbook_name, event_data, logger)
              end
            end

      @schedule_map[schedule_id] = job.id
    end

    logger&.info "[Scheduler] Playbook '#{playbook_name}' scheduled [schedule=#{schedule_id}]"
    schedule_id
  end

  # Unschedule a previously scheduled playbook.
  def unschedule(schedule_id)
    MUTEX.synchronize do
      job_id = @schedule_map.delete(schedule_id)
      @scheduler.unschedule(job_id) if job_id && @scheduler
    end
  end

  def running?
    @scheduler&.running? || false
  end

  def stop
    MUTEX.synchronize do
      @scheduler&.stop
      @scheduler = nil
      @logger&.info '[Scheduler] Stopped'
    end
  end

  private

  module_function

  # Run a playbook and store the resulting job.
  def run_playbook_job(playbook_name, event_data, logger)
    require_relative 'playbooks'

    job_id   = SecureRandom.uuid
    executor = PlaybookExecutor.new(job_id: job_id, logger: logger)
    logger&.info "[Scheduler] Executing playbook '#{playbook_name}' [job=#{job_id}]"

    result = executor.execute(playbook_name, event_data: event_data)
    logger&.info "[Scheduler] Playbook '#{playbook_name}' finished: #{result[:summary]}"
  rescue StandardError => e
    logger&.error "[Scheduler] Error running playbook '#{playbook_name}': #{e.message}"
  end

  # Built-in recurring tasks that run independently of user-triggered playbooks.
  def register_built_in_tasks
    # Correlation check — every 60 seconds
    @scheduler.every('60s', overlap: false, tag: 'correlation_check') do
      run_correlation_check
    end

    # Threat-intel feed refresh — every 10 minutes
    @scheduler.every('600s', overlap: false, tag: 'threat_intel_refresh') do
      run_threat_intel_refresh
    end

    # Stale incident cleanup — daily at 02:00 UTC
    @scheduler.cron('0 2 * * *', overlap: false, tag: 'incident_cleanup') do
      run_incident_cleanup
    end

    @logger.info '[Scheduler] Built-in tasks registered: correlation_check, threat_intel_refresh, incident_cleanup'
  end

  def run_correlation_check
    require 'httparty'

    @logger&.debug '[Scheduler] Running correlation check'
    response = HTTParty.post(
      "#{ENV.fetch('PYTHON_SERVICE_URL', 'http://python-service:5000')}/api/correlation/run",
      headers: {
        'Content-Type'  => 'application/json',
        'X-Service-Key' => ENV.fetch('INTERNAL_SERVICE_KEY', 'internal-key'),
        'X-Source'      => 'ruby-scheduler'
      },
      body:    { triggered_by: 'scheduler', timestamp: Time.now.utc.iso8601 }.to_json,
      timeout: 10
    )
    @logger&.info "[Scheduler] Correlation check completed (HTTP #{response.code})"
  rescue StandardError => e
    @logger&.error "[Scheduler] Correlation check failed: #{e.message}"
  end

  def run_threat_intel_refresh
    require 'httparty'

    @logger&.debug '[Scheduler] Refreshing threat intelligence feeds'
    response = HTTParty.post(
      "#{ENV.fetch('PYTHON_SERVICE_URL', 'http://python-service:5000')}/api/threat-intel/refresh",
      headers: {
        'Content-Type'  => 'application/json',
        'X-Service-Key' => ENV.fetch('INTERNAL_SERVICE_KEY', 'internal-key'),
        'X-Source'      => 'ruby-scheduler'
      },
      body:    { triggered_by: 'scheduler', timestamp: Time.now.utc.iso8601 }.to_json,
      timeout: 15
    )
    @logger&.info "[Scheduler] Threat intel refresh completed (HTTP #{response.code})"
  rescue StandardError => e
    @logger&.error "[Scheduler] Threat intel refresh failed: #{e.message}"
  end

  def run_incident_cleanup
    require 'httparty'

    @logger&.info '[Scheduler] Running stale incident cleanup'
    response = HTTParty.post(
      "#{ENV.fetch('PYTHON_SERVICE_URL', 'http://python-service:5000')}/api/incidents/cleanup",
      headers: {
        'Content-Type'  => 'application/json',
        'X-Service-Key' => ENV.fetch('INTERNAL_SERVICE_KEY', 'internal-key'),
        'X-Source'      => 'ruby-scheduler'
      },
      body:    {
        triggered_by:    'scheduler',
        max_age_days:    ENV.fetch('INCIDENT_MAX_AGE_DAYS', '90').to_i,
        timestamp:       Time.now.utc.iso8601
      }.to_json,
      timeout: 30
    )
    @logger&.info "[Scheduler] Incident cleanup completed (HTTP #{response.code})"
  rescue StandardError => e
    @logger&.error "[Scheduler] Incident cleanup failed: #{e.message}"
  end
end
