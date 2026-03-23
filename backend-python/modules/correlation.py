"""
Alert correlation engine for detecting patterns
"""

from datetime import datetime, timedelta
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)

class CorrelationEngine:
    """Detect correlations between logs and alerts"""
    
    def __init__(self):
        self.window_size = timedelta(minutes=5)  # 5-minute correlation window
        self.threshold = 3  # Minimum events to trigger correlation
    
    def check_correlations(self, logs):
        """Check for correlations in batch of logs"""
        correlations = []
        
        # Group by source IP
        by_source = defaultdict(list)
        for log in logs:
            source_ip = log.get('raw_data', {}).get('ip_address') or log.get('source', '')
            by_source[source_ip].append(log)
        
        # Check patterns
        for source, source_logs in by_source.items():
            if len(source_logs) >= self.threshold:
                # Check for repeated failures
                corr = self.detect_brute_force(source_logs)
                if corr:
                    correlations.append(corr)
                
                # Check for port scanning
                corr = self.detect_port_scan(source_logs)
                if corr:
                    correlations.append(corr)
                
                # Check for data exfiltration
                corr = self.detect_data_exfiltration(source_logs)
                if corr:
                    correlations.append(corr)
        
        return correlations
    
    def detect_brute_force(self, logs):
        """Detect brute force attack pattern"""
        failure_count = sum(1 for log in logs if 'fail' in str(log.get('message', '')).lower())
        
        if failure_count >= self.threshold:
            return {
                'type': 'brute_force',
                'severity': 'high' if failure_count > 10 else 'medium',
                'source': logs[0].get('source'),
                'count': failure_count,
                'timestamp': datetime.utcnow(),
                'affected_logs': len(logs)
            }
        
        return None
    
    def detect_port_scan(self, logs):
        """Detect port scanning pattern"""
        ports = set()
        for log in logs:
            port = log.get('raw_data', {}).get('dest_port')
            if port:
                ports.add(port)
        
        if len(ports) >= self.threshold:
            return {
                'type': 'port_scan',
                'severity': 'high',
                'source': logs[0].get('source'),
                'ports_scanned': len(ports),
                'timestamp': datetime.utcnow(),
                'affected_logs': len(logs)
            }
        
        return None
    
    def detect_data_exfiltration(self, logs):
        """Detect potential data exfiltration"""
        large_transfers = []
        for log in logs:
            size = log.get('raw_data', {}).get('bytes_out', 0)
            if size and size > 1000000:  # > 1MB
                large_transfers.append(size)
        
        if len(large_transfers) >= 2:
            return {
                'type': 'data_exfiltration',
                'severity': 'critical',
                'source': logs[0].get('source'),
                'transfers': len(large_transfers),
                'total_bytes': sum(large_transfers),
                'timestamp': datetime.utcnow(),
                'affected_logs': len(logs)
            }
        
        return None