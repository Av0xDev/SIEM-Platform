# frozen_string_literal: true

# SIEM Platform - Ruby Automation Engine RSpec Tests
#
# Run with: bundle exec rspec spec/ --format documentation

require 'rack/test'
require 'json'
require 'rspec'

ENV['APP_ENV']             = 'test'
ENV['PYTHON_SERVICE_URL']  = 'http://python-service:5000'
ENV['JAVA_SERVICE_URL']    = 'http://java-service:8080'
ENV['INTERNAL_SERVICE_KEY'] = 'test-internal-key'

require_relative '../lib/playbooks'
require_relative '../lib/scheduler'
require_relative '../app'

RSpec.configure do |config|
  config.include Rack::Test::Methods

  config.before(:suite) do
    # Stop scheduler so it does not fire during tests
    SIEMScheduler.stop if SIEMScheduler.running?
  end
end

def app
  Sinatra::Application
end

# ---------------------------------------------------------------------------
# Shared stubs for external HTTP calls
# ---------------------------------------------------------------------------

def stub_external_calls_success
  allow(HTTParty).to receive(:post).and_return(
    double('response', success?: true, code: 200, parsed_response: { 'status' => 'ok' })
  )
  allow(HTTParty).to receive(:get).and_return(
    double('response', success?: true, code: 200, parsed_response: { 'data' => [] })
  )
end

def stub_external_calls_failure
  allow(HTTParty).to receive(:post).and_raise(StandardError, 'Connection refused')
  allow(HTTParty).to receive(:get).and_raise(StandardError, 'Connection refused')
end

# ---------------------------------------------------------------------------
# GET /health
# ---------------------------------------------------------------------------

RSpec.describe 'GET /health' do
  it 'returns 200 with healthy status' do
    get '/health'
    expect(last_response.status).to eq(200)
    body = JSON.parse(last_response.body)
    expect(body['status']).to eq('healthy')
    expect(body['service']).to eq('ruby-automation-engine')
    expect(body).to have_key('version')
    expect(body).to have_key('timestamp')
  end

  it 'returns valid JSON' do
    get '/health'
    expect { JSON.parse(last_response.body) }.not_to raise_error
  end
end

# ---------------------------------------------------------------------------
# GET /automation/playbooks
# ---------------------------------------------------------------------------

RSpec.describe 'GET /automation/playbooks' do
  it 'returns 200 with a list of playbooks' do
    get '/automation/playbooks'
    expect(last_response.status).to eq(200)
    body = JSON.parse(last_response.body)
    expect(body).to have_key('playbooks')
    expect(body['playbooks']).to be_an(Array)
    expect(body['count']).to eq(body['playbooks'].size)
  end

  it 'includes all four built-in playbooks' do
    get '/automation/playbooks'
    names = JSON.parse(last_response.body)['playbooks'].map { |p| p['name'] }
    expect(names).to include(
      'brute_force_response',
      'malware_response',
      'data_exfiltration_response',
      'unauthorized_access_response'
    )
  end

  it 'includes description, trigger and actions for each playbook' do
    get '/automation/playbooks'
    playbooks = JSON.parse(last_response.body)['playbooks']
    playbooks.each do |pb|
      expect(pb).to have_key('description')
      expect(pb).to have_key('trigger')
      expect(pb['actions']).to be_an(Array)
      expect(pb['actions']).not_to be_empty
    end
  end
end

# ---------------------------------------------------------------------------
# POST /automation/playbooks/execute
# ---------------------------------------------------------------------------

RSpec.describe 'POST /automation/playbooks/execute' do
  context 'with a valid playbook' do
    before { stub_external_calls_success }

    let(:payload) do
      {
        playbook_name: 'brute_force_response',
        event_data:    { source_ip: '10.0.0.1', user: 'jdoe', host: 'ws-01' }
      }.to_json
    end

    it 'returns 200 on full success' do
      post '/automation/playbooks/execute', payload, 'CONTENT_TYPE' => 'application/json'
      expect(last_response.status).to eq(200)
    end

    it 'returns a job_id and status' do
      post '/automation/playbooks/execute', payload, 'CONTENT_TYPE' => 'application/json'
      body = JSON.parse(last_response.body)
      expect(body['job_id']).to match(/\A[0-9a-f-]{36}\z/)
      expect(body['status']).to eq('completed')
    end

    it 'returns actions_taken array' do
      post '/automation/playbooks/execute', payload, 'CONTENT_TYPE' => 'application/json'
      body = JSON.parse(last_response.body)
      expect(body['actions_taken']).to be_an(Array)
      expect(body['actions_taken']).not_to be_empty
    end

    it 'returns a summary string' do
      post '/automation/playbooks/execute', payload, 'CONTENT_TYPE' => 'application/json'
      body = JSON.parse(last_response.body)
      expect(body['summary']).to be_a(String)
      expect(body['summary']).not_to be_empty
    end
  end

  context 'when external services fail' do
    before { stub_external_calls_failure }

    let(:payload) do
      {
        playbook_name: 'malware_response',
        event_data:    { host: 'infected-host', user: 'alice' }
      }.to_json
    end

    it 'returns 207 Multi-Status on partial failure' do
      post '/automation/playbooks/execute', payload, 'CONTENT_TYPE' => 'application/json'
      expect(last_response.status).to eq(207)
    end

    it 'reports errors in the response body' do
      post '/automation/playbooks/execute', payload, 'CONTENT_TYPE' => 'application/json'
      body = JSON.parse(last_response.body)
      expect(body['errors']).to be_an(Array)
      expect(body['errors']).not_to be_empty
    end

    it 'still returns actions_taken for attempted actions' do
      post '/automation/playbooks/execute', payload, 'CONTENT_TYPE' => 'application/json'
      body = JSON.parse(last_response.body)
      expect(body['actions_taken']).to be_an(Array)
    end
  end

  context 'with missing playbook_name' do
    it 'returns 400' do
      post '/automation/playbooks/execute', '{"event_data":{}}', 'CONTENT_TYPE' => 'application/json'
      expect(last_response.status).to eq(400)
      body = JSON.parse(last_response.body)
      expect(body['error']).to eq('validation_error')
    end
  end

  context 'with unknown playbook' do
    it 'returns 404' do
      payload = { playbook_name: 'nonexistent_playbook' }.to_json
      post '/automation/playbooks/execute', payload, 'CONTENT_TYPE' => 'application/json'
      expect(last_response.status).to eq(404)
      body = JSON.parse(last_response.body)
      expect(body['error']).to eq('playbook_not_found')
    end
  end

  context 'with invalid JSON body' do
    it 'returns 400' do
      post '/automation/playbooks/execute', 'not-json', 'CONTENT_TYPE' => 'application/json'
      expect(last_response.status).to eq(400)
      body = JSON.parse(last_response.body)
      expect(body['error']).to eq('invalid_json')
    end
  end
end

# ---------------------------------------------------------------------------
# GET /automation/jobs
# ---------------------------------------------------------------------------

RSpec.describe 'GET /automation/jobs' do
  before do
    stub_external_calls_success
    payload = { playbook_name: 'unauthorized_access_response', event_data: { user: 'bob' } }.to_json
    post '/automation/playbooks/execute', payload, 'CONTENT_TYPE' => 'application/json'
  end

  it 'returns 200' do
    get '/automation/jobs'
    expect(last_response.status).to eq(200)
  end

  it 'returns jobs array and pagination info' do
    get '/automation/jobs'
    body = JSON.parse(last_response.body)
    expect(body).to have_key('jobs')
    expect(body).to have_key('pagination')
    expect(body['jobs']).to be_an(Array)
  end

  it 'supports status filter' do
    get '/automation/jobs?status=completed'
    body = JSON.parse(last_response.body)
    body['jobs'].each do |job|
      expect(job['status']).to eq('completed')
    end
  end

  it 'supports playbook filter' do
    get '/automation/jobs?playbook=unauthorized_access_response'
    body = JSON.parse(last_response.body)
    body['jobs'].each do |job|
      expect(job['playbook_name']).to eq('unauthorized_access_response')
    end
  end
end

# ---------------------------------------------------------------------------
# POST /automation/schedule
# ---------------------------------------------------------------------------

RSpec.describe 'POST /automation/schedule' do
  before { SIEMScheduler.start(logger: Logger.new('/dev/null')) }
  after  { SIEMScheduler.stop }

  context 'with interval_seconds' do
    let(:payload) do
      { playbook_name: 'brute_force_response', interval_seconds: 300 }.to_json
    end

    it 'returns 201' do
      post '/automation/schedule', payload, 'CONTENT_TYPE' => 'application/json'
      expect(last_response.status).to eq(201)
    end

    it 'returns a schedule_id' do
      post '/automation/schedule', payload, 'CONTENT_TYPE' => 'application/json'
      body = JSON.parse(last_response.body)
      expect(body['schedule_id']).to match(/\A[0-9a-f-]{36}\z/)
      expect(body['status']).to eq('scheduled')
    end
  end

  context 'with missing schedule parameters' do
    let(:payload) { { playbook_name: 'brute_force_response' }.to_json }

    it 'returns 400' do
      post '/automation/schedule', payload, 'CONTENT_TYPE' => 'application/json'
      expect(last_response.status).to eq(400)
    end
  end

  context 'with unknown playbook' do
    let(:payload) { { playbook_name: 'unknown', interval_seconds: 60 }.to_json }

    it 'returns 404' do
      post '/automation/schedule', payload, 'CONTENT_TYPE' => 'application/json'
      expect(last_response.status).to eq(404)
    end
  end
end

# ---------------------------------------------------------------------------
# 404 fallback
# ---------------------------------------------------------------------------

RSpec.describe 'Unknown routes' do
  it 'returns 404 with error body' do
    get '/nonexistent'
    expect(last_response.status).to eq(404)
    body = JSON.parse(last_response.body)
    expect(body['error']).to eq('not_found')
    expect(body).to have_key('available_routes')
  end
end

# ---------------------------------------------------------------------------
# PlaybookRegistry unit tests
# ---------------------------------------------------------------------------

RSpec.describe PlaybookRegistry do
  describe '.names' do
    it 'returns all built-in playbook names' do
      expect(PlaybookRegistry.names).to include(
        'brute_force_response',
        'malware_response',
        'data_exfiltration_response',
        'unauthorized_access_response'
      )
    end
  end

  describe '.exists?' do
    it 'returns true for known playbooks' do
      expect(PlaybookRegistry.exists?('malware_response')).to be true
    end

    it 'returns false for unknown playbooks' do
      expect(PlaybookRegistry.exists?('does_not_exist')).to be false
    end
  end

  describe '.[]' do
    it 'returns playbook definition with required keys' do
      pb = PlaybookRegistry['brute_force_response']
      expect(pb).to have_key(:description)
      expect(pb).to have_key(:trigger)
      expect(pb).to have_key(:actions)
    end
  end
end

# ---------------------------------------------------------------------------
# PlaybookExecutor unit tests
# ---------------------------------------------------------------------------

RSpec.describe PlaybookExecutor do
  let(:logger)   { Logger.new('/dev/null') }
  let(:executor) { PlaybookExecutor.new(job_id: 'test-job-id', logger: logger) }

  describe '#execute with stubbed HTTP' do
    before { stub_external_calls_success }

    it 'returns success: true when all actions succeed' do
      result = executor.execute('unauthorized_access_response',
                                event_data: { user: 'testuser', host: 'test-host' })
      expect(result[:success]).to be true
      expect(result[:errors]).to be_empty
    end

    it 'returns actions_taken for every defined action' do
      pb_actions = PlaybookRegistry['unauthorized_access_response'][:actions].size
      result     = executor.execute('unauthorized_access_response',
                                    event_data: { user: 'u', host: 'h' })
      expect(result[:actions_taken].size).to eq(pb_actions)
    end

    it 'returns a non-empty summary string' do
      result = executor.execute('brute_force_response',
                                event_data: { source_ip: '1.2.3.4', user: 'u' })
      expect(result[:summary]).to be_a(String)
      expect(result[:summary]).not_to be_empty
    end
  end

  describe '#execute when HTTP calls fail' do
    before { stub_external_calls_failure }

    it 'returns success: false when actions fail' do
      result = executor.execute('brute_force_response',
                                event_data: { source_ip: '1.2.3.4', user: 'u' })
      expect(result[:success]).to be false
    end

    it 'still executes all actions (best-effort)' do
      pb_actions = PlaybookRegistry['brute_force_response'][:actions].size
      result     = executor.execute('brute_force_response',
                                    event_data: { source_ip: '1.2.3.4', user: 'u' })
      expect(result[:actions_taken].size).to eq(pb_actions)
    end
  end
end
