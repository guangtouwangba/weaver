"""
Elasticsearch Configuration
"""
import os
from typing import List, Optional

class ElasticsearchConfig:
    """Elasticsearch configuration manager"""
    
    def __init__(self):
        self.hosts = self._get_hosts()
        self.username = self._get_username()
        self.password = self._get_password()
        self.index_prefix = self._get_index_prefix()
        self.enabled = self._is_enabled()
    
    def _get_hosts(self) -> List[str]:
        """Get Elasticsearch hosts from environment"""
        hosts_str = os.getenv('ELASTICSEARCH_HOSTS', 'http://localhost:9200')
        return [host.strip() for host in hosts_str.split(',')]
    
    def _get_username(self) -> Optional[str]:
        """Get Elasticsearch username from environment"""
        return os.getenv('ELASTICSEARCH_USERNAME')
    
    def _get_password(self) -> Optional[str]:
        """Get Elasticsearch password from environment"""
        return os.getenv('ELASTICSEARCH_PASSWORD')
    
    def _get_index_prefix(self) -> str:
        """Get index prefix from environment"""
        return os.getenv('ELASTICSEARCH_INDEX_PREFIX', 'job-logs')
    
    def _is_enabled(self) -> bool:
        """Check if Elasticsearch is enabled"""
        return os.getenv('ELASTICSEARCH_ENABLED', 'true').lower() == 'true'
    
    def get_config_dict(self) -> dict:
        """Get configuration as dictionary"""
        return {
            'hosts': self.hosts,
            'username': self.username,
            'password': self.password,
            'index_prefix': self.index_prefix,
            'enabled': self.enabled
        }
    
    def is_configured(self) -> bool:
        """Check if Elasticsearch is properly configured"""
        return self.enabled and len(self.hosts) > 0

# Global configuration instance
elasticsearch_config = ElasticsearchConfig() 