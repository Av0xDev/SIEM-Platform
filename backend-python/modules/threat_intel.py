"""
Threat intelligence enrichment module
"""

import logging

logger = logging.getLogger(__name__)

class ThreatIntelligence:
    """Integrate with threat intelligence sources"""
    
    def __init__(self):
        # Placeholder threat feeds (would integrate with real APIs)
        self.malicious_ips = set()
        self.malicious_domains = set()
        self.known_hashes = {}
    
    def enrich(self, log):
        """Enrich log with threat intelligence"""
        enriched = log.copy()
        enriched['threat_score'] = 0
        enriched['threat_indicators'] = []
        
        # Check IPs
        if 'ip_address' in log.get('raw_data', {}):
            ip = log['raw_data']['ip_address']
            if self.is_malicious_ip(ip):
                enriched['threat_score'] += 50
                enriched['threat_indicators'].append(f'Malicious IP: {ip}')
        
        # Check domains
        if 'domain' in log.get('raw_data', {}):
            domain = log['raw_data']['domain']
            if self.is_malicious_domain(domain):
                enriched['threat_score'] += 40
                enriched['threat_indicators'].append(f'Malicious Domain: {domain}')
        
        # Check message for IOCs
        message = str(log.get('message', '')).lower()
        if any(keyword in message for keyword in ['malware', 'ransomware', 'trojan']):
            enriched['threat_score'] += 30
            enriched['threat_indicators'].append('Suspicious keywords detected')
        
        enriched['threat_level'] = self.calculate_threat_level(enriched['threat_score'])
        
        return enriched
    
    def is_malicious_ip(self, ip):
        """Check if IP is malicious"""
        return ip in self.malicious_ips
    
    def is_malicious_domain(self, domain):
        """Check if domain is malicious"""
        return domain in self.malicious_domains
    
    def check_indicators(self, indicators):
        """Check batch of indicators"""
        results = {
            'ips': {},
            'domains': {},
            'hashes': {}
        }
        
        for ip in indicators.get('ips', []):
            results['ips'][ip] = {
                'malicious': self.is_malicious_ip(ip),
                'reputation': 'unknown'
            }
        
        for domain in indicators.get('domains', []):
            results['domains'][domain] = {
                'malicious': self.is_malicious_domain(domain),
                'reputation': 'unknown'
            }
        
        return results
    
    def calculate_threat_level(self, score):
        """Calculate threat level from score"""
        if score >= 80:
            return 'critical'
        elif score >= 60:
            return 'high'
        elif score >= 40:
            return 'medium'
        elif score >= 20:
            return 'low'
        else:
            return 'none'