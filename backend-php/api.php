<?php
/**
 * SIEM Platform - PHP Webhook Service
 * Receives webhook events and forwards to processing pipeline
 */

header('Content-Type: application/json');
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: POST, GET, OPTIONS');
header('Access-Control-Allow-Headers: Content-Type, Authorization');

if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    http_response_code(200);
    exit();
}

require_once 'config.php';

class WebhookHandler {
    private $python_service_url;
    private $java_service_url;

    public function __construct($python_url, $java_url) {
        $this->python_service_url = $python_url;
        $this->java_service_url = $java_url;
    }

    public function handle() {
        $method = $_SERVER['REQUEST_METHOD'];
        $path = parse_url($_SERVER['REQUEST_URI'], PHP_URL_PATH);

        if ($method === 'GET' && strpos($path, '/health') !== false) {
            return $this->healthCheck();
        }

        if ($method === 'POST' && strpos($path, '/webhooks') !== false) {
            return $this->handleWebhook();
        }

        http_response_code(404);
        echo json_encode(['error' => 'Endpoint not found']);
    }

    private function healthCheck() {
        http_response_code(200);
        echo json_encode([
            'status' => 'healthy',
            'timestamp' => date('c'),
            'service' => 'PHP Webhook Service'
        ]);
    }

    private function handleWebhook() {
        $input = json_decode(file_get_contents('php://input'), true);

        if (!$input) {
            http_response_code(400);
            echo json_encode(['error' => 'Invalid JSON payload']);
            return;
        }

        // Validate webhook signature if provided
        if (!$this->validateSignature($input)) {
            http_response_code(401);
            echo json_encode(['error' => 'Invalid signature']);
            return;
        }

        // Forward to Python service for processing
        $result = $this->forwardToPython($input);

        if ($result) {
            http_response_code(200);
            echo json_encode([
                'status' => 'accepted',
                'message' => 'Webhook processed successfully',
                'timestamp' => date('c')
            ]);
        } else {
            http_response_code(500);
            echo json_encode(['error' => 'Failed to process webhook']);
        }
    }

    private function validateSignature($data) {
        // Placeholder for signature validation
        // In production, validate against webhook secret
        return true;
    }

    private function forwardToPython($data) {
        $url = $this->python_service_url . '/api/logs/ingest';

        $payload = json_encode(['logs' => [$data]]);
        $ch = curl_init($url);
        curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
        curl_setopt($ch, CURLOPT_POST, true);
        curl_setopt($ch, CURLOPT_HTTPHEADER, ['Content-Type: application/json']);
        curl_setopt($ch, CURLOPT_POSTFIELDS, $payload);
        curl_setopt($ch, CURLOPT_TIMEOUT, 5);

        $response = curl_exec($ch);
        $httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
        curl_close($ch);

        return $httpCode === 200;
    }
}

// Route and handle requests
$handler = new WebhookHandler(
    getenv('PYTHON_SERVICE_URL') ?: 'http://python:5000',
    getenv('JAVA_SERVICE_URL') ?: 'http://java:8080'
);

$handler->handle();
?>