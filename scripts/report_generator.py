"""
Report Generator - Creates comprehensive reports and statistics
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

class ReportGenerator:
    """Generate comprehensive reports and statistics."""
    
    def __init__(self, config):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.reports_dir = Path("reports")
        self.reports_dir.mkdir(exist_ok=True)
    
    def generate_markdown_report(self, stats: Dict, health_results: Dict = None) -> str:
        """Generate a detailed Markdown report."""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        report_lines = [
            "# IPTV Playlist Generation Report",
            f"**Generated:** {timestamp}\n",
            "## Summary Statistics",
            f"- **Total channels processed:** {stats.get('total_channels', 0)}",
            f"- **Valid channels:** {stats.get('valid_channels', 0)}",
            f"- **Duplicates removed:** {stats.get('duplicates_removed', 0)}",
            f"- **New channels imported:** {stats.get('imported_channels', 0)}",
            f"- **Countries detected:** {stats.get('countries_detected', 0)}",
            ""
        ]
        
        # Health check section
        if health_results:
            healthy_count = sum(1 for is_healthy, _ in health_results.values() if is_healthy)
            total_checked = len(health_results)
            success_rate = (healthy_count / total_checked * 100) if total_checked > 0 else 0
            
            report_lines.extend([
                "## Health Check Results",
                f"- **Channels checked:** {total_checked}",
                f"- **Healthy channels:** {healthy_count}",
                f"- **Success rate:** {success_rate:.1f}%",
                ""
            ])
            
            # Failed channels
            failed_channels = [name for name, (is_healthy, status) in health_results.items() if not is_healthy]
            if failed_channels:
                report_lines.extend([
                    "### Failed Channels",
                    *[f"- {channel}" for channel in failed_channels[:10]],  # Limit to first 10
                    ""
                ])
        
        # Country distribution
        if 'country_distribution' in stats and stats['country_distribution']:
            sorted_countries = sorted(
                stats['country_distribution'].items(), 
                key=lambda x: x[1], 
                reverse=True
            )
            
            report_lines.extend([
                "## Channel Distribution by Country",
                *[f"- **{country}:** {count} channels" for country, count in sorted_countries],
                ""
            ])
        
        # Configuration summary
        report_lines.extend([
            "## Configuration",
            f"- **Remove duplicates:** {self.config.settings.get('remove_duplicates', 'Unknown')}",
            f"- **Auto country detection:** {self.config.settings.get('auto_detect_country', 'Unknown')}",
            f"- **Quality detection:** {self.config.settings.get('detect_quality', 'Unknown')}",
            f"- **Adult content filtering:** {self.config.settings.get('skip_adult_content', 'Unknown')}",
            f"- **Health check enabled:** {self.config.settings.get('enable_health_check', 'Unknown')}",
            ""
        ])
        
        return "\n".join(report_lines)
    
    def save_report(self, stats: Dict, health_results: Dict = None) -> Optional[Path]:
        """Save the report to a file."""
        try:
            report_content = self.generate_markdown_report(stats, health_results)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            report_path = self.reports_dir / f"playlist_report_{timestamp}.md"
            
            with open(report_path, 'w', encoding='utf-8') as f:
                f.write(report_content)
            
            self.logger.info(f"Report saved: {report_path}")
            
            # Cleanup old reports (keep last 10)
            self._cleanup_old_reports()
            
            return report_path
            
        except Exception as e:
            self.logger.error(f"Failed to save report: {e}")
            return None
    
    def _cleanup_old_reports(self):
        """Remove old reports, keeping only the most recent ones."""
        try:
            report_files = sorted(
                [f for f in self.reports_dir.glob("playlist_report_*.md") if f.is_file()],
                key=lambda x: x.stat().st_mtime,
                reverse=True
            )
            
            # Keep last 10 reports
            for old_report in report_files[10:]:
                old_report.unlink()
                self.logger.debug(f"Removed old report: {old_report}")
                
        except Exception as e:
            self.logger.warning(f"Could not cleanup old reports: {e}")
    
    def log_summary_stats(self, stats: Dict):
        """Log a quick summary to console/log."""
        self.logger.info("=" * 50)
        self.logger.info("PLAYLIST GENERATION SUMMARY")
        self.logger.info("=" * 50)
        self.logger.info(f"Total channels: {stats.get('total_channels', 0)}")
        self.logger.info(f"Valid channels: {stats.get('valid_channels', 0)}")
        self.logger.info(f"Duplicates removed: {stats.get('duplicates_removed', 0)}")
        self.logger.info(f"New imports: {stats.get('imported_channels', 0)}")
        self.logger.info(f"Countries: {stats.get('countries_detected', 0)}")
        self.logger.info("=" * 50)