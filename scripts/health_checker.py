#!/usr/bin/env python3
"""
Health Checker - Simple health checking without external dependencies
"""

import logging
import urllib.request
import urllib.error
import socket
import time
import concurrent.futures
from typing import Dict, List, Optional

class HealthChecker:
    """Simple health checker using only standard library."""
    
    def __init__(self, config):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.timeout = config.settings.get('health_check_timeout', 5)
        self.max_workers = config.settings.get('max_workers', 4)
        
        # Set default socket timeout
        socket.setdefaulttimeout(self.timeout)
        
    def check_single_url(self, url: str) -> Dict:
        """Check a single URL for accessibility using urllib."""
        start_time = time.time()
        
        try:
            # Create request with proper headers
            req = urllib.request.Request(
                url,
                headers={'User-Agent': 'IPTV-Health-Checker/1.0'}
            )
            
            # Try to open the URL
            with urllib.request.urlopen(req, timeout=self.timeout) as response:
                response_time = time.time() - start_time
                status_code = response.getcode()
                
                return {
                    'url': url,
                    'status': 'healthy' if status_code < 400 else 'unhealthy',
                    'status_code': status_code,
                    'response_time': round(response_time, 2),
                    'error': None
                }
                
        except urllib.error.HTTPError as e:
            return {
                'url': url,
                'status': 'unhealthy',
                'status_code': e.code,
                'response_time': time.time() - start_time,
                'error': f'HTTP {e.code}: {e.reason}'
            }
            
        except urllib.error.URLError as e:
            return {
                'url': url,
                'status': 'unreachable',
                'status_code': None,
                'response_time': time.time() - start_time,
                'error': f'URL Error: {e.reason}'
            }
            
        except socket.timeout:
            return {
                'url': url,
                'status': 'timeout',
                'status_code': None,
                'response_time': self.timeout,
                'error': 'Request timeout'
            }
            
        except Exception as e:
            return {
                'url': url,
                'status': 'error',
                'status_code': None,
                'response_time': time.time() - start_time,
                'error': str(e)
            }
    
    def check_channel_health(self, channel: Dict) -> Dict:
        """Check health of a single channel."""
        url = channel.get('Stream URL', '')
        
        if not url:
            return {
                'channel_name': channel.get('Stream name', 'Unknown'),
                'url': '',
                'status': 'no_url',
                'status_code': None,
                'response_time': 0,
                'error': 'No URL provided'
            }
        
        result = self.check_single_url(url)
        result['channel_name'] = channel.get('Stream name', 'Unknown')
        
        return result
    
    def batch_health_check(self, channels: List[Dict]) -> Dict:
        """Perform batch health check on multiple channels."""
        if not self.config.settings.get('enable_health_check', False):
            self.logger.info("Health checking is disabled")
            return {
                'enabled': False,
                'results': [],
                'summary': {
                    'total': len(channels),
                    'healthy': 0,
                    'health_percentage': 0,
                    'total_check_time': 0
                }
            }
        
        self.logger.info(f"Starting health check for {len(channels)} channels...")
        
        start_time = time.time()
        results = []
        
        # Limit concurrent checks to avoid overwhelming servers
        max_workers = min(self.max_workers, len(channels))
        
        if max_workers > 1:
            # Use ThreadPoolExecutor for concurrent checks
            try:
                with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
                    # Submit all health check tasks
                    future_to_channel = {
                        executor.submit(self.check_channel_health, channel): channel 
                        for channel in channels
                    }
                    
                    # Collect results as they complete
                    for future in concurrent.futures.as_completed(future_to_channel, timeout=60):
                        try:
                            result = future.result(timeout=10)
                            results.append(result)
                        except Exception as e:
                            channel = future_to_channel[future]
                            self.logger.warning(f"Health check failed for {channel.get('Stream name', 'Unknown')}: {e}")
                            results.append({
                                'channel_name': channel.get('Stream name', 'Unknown'),
                                'url': channel.get('Stream URL', ''),
                                'status': 'error',
                                'status_code': None,
                                'response_time': 0,
                                'error': str(e)
                            })
            except Exception as e:
                self.logger.error(f"Concurrent health check failed: {e}")
                # Fall back to sequential processing
                for channel in channels:
                    try:
                        result = self.check_channel_health(channel)
                        results.append(result)
                    except Exception as channel_error:
                        self.logger.warning(f"Channel check failed: {channel_error}")
        else:
            # Sequential processing for single worker
            for channel in channels:
                try:
                    result = self.check_channel_health(channel)
                    results.append(result)
                except Exception as e:
                    self.logger.warning(f"Health check failed for {channel.get('Stream name', 'Unknown')}: {e}")
                    results.append({
                        'channel_name': channel.get('Stream name', 'Unknown'),
                        'url': channel.get('Stream URL', ''),
                        'status': 'error',
                        'status_code': None,
                        'response_time': 0,
                        'error': str(e)
                    })
        
        total_time = time.time() - start_time
        
        # Generate summary statistics
        summary = self._generate_health_summary(results, total_time)
        
        self.logger.info(f"Health check completed in {total_time:.1f}s: "
                        f"{summary['healthy']}/{summary['total']} channels healthy")
        
        return {
            'enabled': True,
            'results': results,
            'summary': summary,
            'total_time': total_time
        }
    
    def _generate_health_summary(self, results: List[Dict], total_time: float) -> Dict:
        """Generate summary statistics from health check results."""
        total = len(results)
        healthy = sum(1 for r in results if r['status'] == 'healthy')
        unhealthy = sum(1 for r in results if r['status'] == 'unhealthy')
        timeout = sum(1 for r in results if r['status'] == 'timeout')
        unreachable = sum(1 for r in results if r['status'] == 'unreachable')
        errors = sum(1 for r in results if r['status'] == 'error')
        no_url = sum(1 for r in results if r['status'] == 'no_url')
        
        # Calculate average response time for successful checks
        successful_times = [r['response_time'] for r in results if r['status'] == 'healthy']
        avg_response_time = sum(successful_times) / len(successful_times) if successful_times else 0
        
        return {
            'total': total,
            'healthy': healthy,
            'unhealthy': unhealthy,
            'timeout': timeout,
            'unreachable': unreachable,
            'errors': errors,
            'no_url': no_url,
            'health_percentage': round((healthy / total * 100) if total > 0 else 0, 1),
            'avg_response_time': round(avg_response_time, 2),
            'total_check_time': round(total_time, 1)
        }
    
    def get_unhealthy_channels(self, health_results: Dict) -> List[Dict]:
        """Get list of unhealthy channels for reporting."""
        if not health_results.get('enabled', False):
            return []
        
        unhealthy = []
        for result in health_results.get('results', []):
            if result['status'] != 'healthy':
                unhealthy.append({
                    'name': result['channel_name'],
                    'url': result['url'],
                    'status': result['status'],
                    'error': result.get('error', 'Unknown error')
                })
        
        return unhealthy
    
    def save_health_report(self, health_results: Dict, filename: str = None) -> Optional[str]:
        """Save health check results to a file."""
        if not health_results.get('enabled', False):
            return None
        
        import json
        from datetime import datetime
        from pathlib import Path
        
        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'health_check_{timestamp}.json'
        
        reports_dir = Path('reports')
        reports_dir.mkdir(exist_ok=True)
        
        report_path = reports_dir / filename
        
        try:
            # Prepare report data
            report_data = {
                'timestamp': datetime.now().isoformat(),
                'summary': health_results['summary'],
                'unhealthy_channels': self.get_unhealthy_channels(health_results),
                'total_time': health_results['total_time']
            }
            
            with open(report_path, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, indent=2)
            
            self.logger.info(f"Health report saved to: {report_path}")
            return str(report_path)
            
        except Exception as e:
            self.logger.error(f"Could not save health report: {e}")
            return None