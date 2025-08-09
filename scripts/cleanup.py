#!/usr/bin/env python3
"""
Quick Repository Cleanup Tool
Simple script to clean and organize the IPTV repository
"""

import os
import shutil
import glob
from pathlib import Path
from datetime import datetime

def main():
    """Run quick repository cleanup."""
    print("🧹 IPTV Repository Quick Cleanup")
    print("=" * 40)
    
    root_path = Path.cwd()
    cleaned_items = []
    
    # 1. Remove Python cache
    print("1. Cleaning Python cache...")
    pycache_dirs = list(root_path.rglob('__pycache__'))
    pyc_files = list(root_path.rglob('*.pyc')) + list(root_path.rglob('*.pyo'))
    
    for cache_dir in pycache_dirs:
        try:
            shutil.rmtree(cache_dir)
            cleaned_items.append(f"   Removed: {cache_dir.relative_to(root_path)}")
        except Exception as e:
            print(f"   Warning: Could not remove {cache_dir}: {e}")
    
    for pyc_file in pyc_files:
        try:
            pyc_file.unlink()
            cleaned_items.append(f"   Removed: {pyc_file.relative_to(root_path)}")
        except Exception as e:
            print(f"   Warning: Could not remove {pyc_file}: {e}")
    
    # 2. Remove temporary files
    print("2. Cleaning temporary files...")
    temp_patterns = ['*_temp*', '*.tmp', '*~', '*.swp', '*.swo']
    
    for pattern in temp_patterns:
        for temp_file in root_path.rglob(pattern):
            if temp_file.is_file() and '.git' not in str(temp_file):
                try:
                    temp_file.unlink()
                    cleaned_items.append(f"   Removed: {temp_file.relative_to(root_path)}")
                except Exception as e:
                    print(f"   Warning: Could not remove {temp_file}: {e}")
    
    # 3. Organize log files
    print("3. Organizing log files...")
    logs_dir = root_path / 'reports' / 'logs'
    logs_dir.mkdir(parents=True, exist_ok=True)
    
    for log_file in root_path.glob('*.log'):
        try:
            new_location = logs_dir / log_file.name
            shutil.move(str(log_file), str(new_location))
            cleaned_items.append(f"   Moved: {log_file.name} → reports/logs/")
        except Exception as e:
            print(f"   Warning: Could not move {log_file}: {e}")
    
    # 4. Compress old backups
    print("4. Compressing old backups...")
    backup_dir = root_path / 'backups'
    if backup_dir.exists():
        import gzip
        from datetime import timedelta
        
        cutoff_date = datetime.now() - timedelta(days=7)
        
        for backup_file in backup_dir.glob('*.txt'):
            file_date = datetime.fromtimestamp(backup_file.stat().st_mtime)
            if file_date < cutoff_date:
                try:
                    # Compress with gzip
                    with open(backup_file, 'rb') as f_in:
                        with gzip.open(f"{backup_file}.gz", 'wb') as f_out:
                            shutil.copyfileobj(f_in, f_out)
                    backup_file.unlink()
                    cleaned_items.append(f"   Compressed: {backup_file.name}")
                except Exception as e:
                    print(f"   Warning: Could not compress {backup_file}: {e}")
    
    # 5. Ensure proper directory structure
    print("5. Ensuring directory structure...")
    directories = [
        'config',
        'backups',
        'reports/logs',
        'reports/archive',
        'templates'
    ]
    
    for directory in directories:
        dir_path = root_path / directory
        dir_path.mkdir(parents=True, exist_ok=True)
    
    # 6. Clean bulk_import.m3u if it has content
    print("6. Cleaning import file...")
    import_file = root_path / 'bulk_import.m3u'
    if import_file.exists():
        try:
            with open(import_file, 'r', encoding='utf-8') as f:
                content = f.read().strip()
            
            # If it has more than just the M3U header
            lines = content.split('\n')
            if len(lines) > 2 or any('#EXTINF' in line for line in lines):
                with open(import_file, 'w', encoding='utf-8') as f:
                    f.write('#EXTM3U\n')
                cleaned_items.append("   Cleared: bulk_import.m3u (ready for next import)")
        except Exception as e:
            print(f"   Warning: Could not clean import file: {e}")
    
    # 7. Create/update .gitignore if needed
    print("7. Checking .gitignore...")
    gitignore_path = root_path / '.gitignore'
    
    essential_ignores = [
        '__pycache__/',
        '*.pyc',
        '*.pyo',
        '*.log',
        '*.tmp',
        '*_temp*',
        '*~',
        '.DS_Store',
        'Thumbs.db'
    ]
    
    if gitignore_path.exists():
        with open(gitignore_path, 'r', encoding='utf-8') as f:
            existing_content = f.read()
        
        missing_ignores = [ignore for ignore in essential_ignores if ignore not in existing_content]
        
        if missing_ignores:
            with open(gitignore_path, 'a', encoding='utf-8') as f:
                f.write('\n# Added by cleanup script\n')
                for ignore in missing_ignores:
                    f.write(f'{ignore}\n')
            cleaned_items.append("   Updated: .gitignore with missing patterns")
    else:
        with open(gitignore_path, 'w', encoding='utf-8') as f:
            f.write('# IPTV Playlist Generator - Essential ignores\n')
            for ignore in essential_ignores:
                f.write(f'{ignore}\n')
        cleaned_items.append("   Created: .gitignore")
    
    # Summary
    print("\n" + "=" * 40)
    print("✅ Cleanup completed!")
    print(f"📊 {len(cleaned_items)} items processed")
    
    if cleaned_items:
        print("\n🔧 Changes made:")
        for item in cleaned_items[:10]:  # Show first 10
            print(item)
        if len(cleaned_items) > 10:
            print(f"   ... and {len(cleaned_items) - 10} more items")
    else:
        print("\n✨ Repository was already clean!")
    
    # Show current status
    try:
        total_files = len(list(root_path.rglob('*')))
        repo_size = sum(f.stat().st_size for f in root_path.rglob('*') if f.is_file() and '.git' not in str(f))
        repo_size_mb = repo_size / (1024 * 1024)
        
        print(f"\n📈 Current repository status:")
        print(f"   - Total files: {total_files}")
        print(f"   - Repository size: {repo_size_mb:.1f} MB")
        
        if (root_path / 'playlist.m3u').exists():
            try:
                with open(root_path / 'playlist.m3u', 'r', encoding='utf-8') as f:
                    channel_count = len([line for line in f if line.startswith('#EXTINF')])
                print(f"   - Channels in playlist: {channel_count}")
            except:
                pass
    except Exception as e:
        print(f"   Could not calculate stats: {e}")
    
    print("\n🚀 Repository is now clean and organized!")

if __name__ == "__main__":
    main()
