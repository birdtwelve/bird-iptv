#!/usr/bin/env python3
"""
IPTV Repository Monthly Maintenance
Run automatically by workflow
"""

import os
import shutil
import gzip
from pathlib import Path
from datetime import datetime, timedelta

def monthly_maintenance():
    """Run monthly maintenance tasks."""
    print("🧹 IPTV Repository Monthly Maintenance")
    print("=" * 40)
    
    root_path = Path.cwd()
    actions = []
    
    # 1. Compress old backups
    print("1. Compressing old backups...")
    backups_dir = root_path / 'backups'
    cutoff_date = datetime.now() - timedelta(days=7)
    
    if backups_dir.exists():
        for backup_file in backups_dir.glob('*.txt'):
            try:
                file_date = datetime.fromtimestamp(backup_file.stat().st_mtime)
                if file_date < cutoff_date:
                    compressed_path = backup_file.with_suffix('.txt.gz')
                    if not compressed_path.exists():
                        with open(backup_file, 'rb') as f_in:
                            with gzip.open(compressed_path, 'wb') as f_out:
                                shutil.copyfileobj(f_in, f_out)
                        backup_file.unlink()
                        actions.append(f"Compressed: {backup_file.name}")
            except Exception as e:
                print(f"   Warning: {e}")
    
    # 2. Archive old reports
    print("2. Archiving old reports...")
    reports_dir = root_path / 'reports' / 'daily'
    archive_dir = root_path / 'reports' / 'archive'
    
    cutoff_date = datetime.now() - timedelta(days=30)
    
    if reports_dir.exists():
        for report_file in reports_dir.glob('*.md'):
            try:
                file_date = datetime.fromtimestamp(report_file.stat().st_mtime)
                if file_date < cutoff_date:
                    month_folder = archive_dir / file_date.strftime('%Y-%m')
                    month_folder.mkdir(parents=True, exist_ok=True)
                    
                    new_path = month_folder / report_file.name
                    shutil.move(str(report_file), str(new_path))
                    actions.append(f"Archived: {report_file.name}")
            except Exception as e:
                print(f"   Warning: {e}")
    
    # 3. Clean temporary files
    print("3. Cleaning temporary files...")
    patterns = ['*_temp*', '*.tmp', '*~', '*.swp']
    
    for pattern in patterns:
        for temp_file in root_path.rglob(pattern):
            if temp_file.is_file() and '.git' not in str(temp_file):
                try:
                    temp_file.unlink()
                    actions.append(f"Removed: {temp_file.relative_to(root_path)}")
                except Exception as e:
                    print(f"   Warning: {e}")
    
    print(f"\n✅ Monthly maintenance complete! {len(actions)} actions taken")
    if actions:
        for action in actions[:5]:
            print(f"   ✅ {action}")
        if len(actions) > 5:
            print(f"   ... and {len(actions) - 5} more")

if __name__ == "__main__":
    monthly_maintenance()