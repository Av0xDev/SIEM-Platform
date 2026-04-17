"""
Log parsing module supporting multiple formats
"""

import re
import json
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class LogParser:
    """Parse logs in multiple formats (syslog, JSON, CEF, LEEF)"""
    
    def __init__(self):
        # Syslog pattern
        self.syslog_pattern = re.compile(
            r'(\w+ \d+ \d+:\d+:\d+)\s+(\S+)\s+(\S+):\s*(.*)'
        )
        
        # CEF pattern
        self.cef_pattern = re.compile(
            r'CEF:(\d+)\|([^|]*)\|([^|]*)\|([^|]*)\|([^|]*)\|([^|]*)\|([^|]*)\|(.*)'
        )
        
        # LEEF pattern
        self.leef_pattern = re.compile(
            r'LEEF:(\d+.\d+)\|([^|]*)\|([^|]*)\|([^|]*)\|(.*)'
        )
    
    def parse(self, log_entry):
        """Parse log entry in any supported format"""
        if isinstance(log_entry, str):
            log_entry = log_entry.strip()
            
            # Try JSON first
            try:
                parsed = json.loads(log_entry)
                parsed['format'] = 'json'
                return self.normalize(parsed)
            except json.JSONDecodeError:
                pass
            
            # Try CEF
            if log_entry.startswith('CEF:'):
                return self.parse_cef(log_entry)
            
            # Try LEEF
            if log_entry.startswith('LEEF:'):
                return self.parse_leef(log_entry)
            
            # Default to syslog
            return self.parse_syslog(log_entry)
        
        # Already structured
        return self.normalize(log_entry)
    
    def parse_syslog(self, log_entry):
        """Parse syslog format"""
        match = self.syslog_pattern.match(log_entry)
        
        if match:
            timestamp, hostname, service, message = match.groups()
            return self.normalize({
                'timestamp': timestamp,
                'hostname': hostname,
                'service': service,
                'message': message,
                'format': 'syslog'
            })
        
        # Fallback for raw messages
        return self.normalize({
            'message': log_entry,
            'format': 'raw'
        })
    
    def parse_cef(self, log_entry):
        """Parse Common Event Format (CEF)"""
        match = self.cef_pattern.match(log_entry)
        
        if match:
            version, device_vendor, device_product, device_version, \
                signal_id, signal_name, severity, extensions = match.groups()
            
            # Parse extensions
            ext_dict = self.parse_key_value(extensions)
            
            return self.normalize({
                'cef_version': version,
                'device_vendor': device_vendor,
                'device_product': device_product,
                'device_version': device_version,
                'signal_id': signal_id,
                'signal_name': signal_name,
                'severity': severity,
                'extensions': ext_dict,
                'format': 'cef'
            })
        
        return self.normalize({'message': log_entry, 'format': 'cef'})
    
    def parse_leef(self, log_entry):
        """Parse Log Event Extended Format (LEEF)"""
        match = self.leef_pattern.match(log_entry)
        
        if match:
            version, vendor, product, version_str, attributes = match.groups()
            
            # Parse attributes
            attr_dict = self.parse_key_value(attributes)
            
            return self.normalize({
                'leef_version': version,
                'vendor': vendor,
                'product': product,
                'product_version': version_str,
                'attributes': attr_dict,
                'format': 'leef'
            })
        
        return self.normalize({'message': log_entry, 'format': 'leef'})
    
    def parse_key_value(self, kv_string):
        """Parse key=value pairs"""
        result = {}
        # Simple key=value parser
        pairs = re.findall(r'(\w+)=([^\s]+)', kv_string)
        for key, value in pairs:
            result[key] = value
        return result
    
    def normalize(self, parsed_log):
        """Normalize parsed log to standard schema"""
        normalized = {
            'timestamp': self.parse_timestamp(parsed_log.get('timestamp')),
            'source': parsed_log.get('hostname') or parsed_log.get('source') or 'unknown',
            'message': parsed_log.get('message') or str(parsed_log),
            'level': self.extract_level(parsed_log),
            'format': parsed_log.get('format', 'unknown'),
            'raw_data': parsed_log
        }
        
        # Extract common fields
        if 'ip_address' in parsed_log:
            normalized['ip_address'] = parsed_log['ip_address']
        if 'user' in parsed_log:
            normalized['user'] = parsed_log['user']
        if 'action' in parsed_log:
            normalized['action'] = parsed_log['action']
        
        return normalized
    
    def parse_timestamp(self, ts):
        """Parse various timestamp formats"""
        if not ts:
            return datetime.utcnow()
        
        if isinstance(ts, datetime):
            return ts
        
        # Try common formats
        formats = [
            '%Y-%m-%dT%H:%M:%S.%fZ',
            '%Y-%m-%d %H:%M:%S',
            '%b %d %H:%M:%S',
            '%d/%b/%Y:%H:%M:%S',
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(str(ts), fmt)
            except ValueError:
                continue
        
        return datetime.utcnow()
    
    def extract_level(self, parsed_log):
        """Extract log level/severity"""
        message = str(parsed_log.get('message', '')).lower()
        severity = parsed_log.get('severity', 'info').lower()
        
        # Check message for level indicators
        for level in ['critical', 'emergency', 'alert', 'error', 'warning', 'notice', 'info', 'debug']:
            if level in message or level in severity:
                return level
        
        return 'info'