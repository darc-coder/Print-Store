#!/usr/bin/env python3
"""
Cleanup old files from RpiPrint
Removes old uploads and screenshots to save disk space
"""
import os
import sys
import time
from pathlib import Path
from datetime import datetime, timedelta
import sqlite3

# Configuration
DAYS_TO_KEEP_COMPLETED = int(os.getenv('CLEANUP_DAYS_COMPLETED', '14'))  # Keep completed jobs for 14 days
DAYS_TO_KEEP_REJECTED = int(os.getenv('CLEANUP_DAYS_REJECTED', '7'))    # Keep rejected jobs for 7 days
DAYS_TO_KEEP_ORPHANED = int(os.getenv('CLEANUP_DAYS_ORPHANED', '3'))    # Keep orphaned files for 3 days
DRY_RUN = '--dry-run' in sys.argv or '-n' in sys.argv

# Paths
BASE_DIR = Path(__file__).parent.absolute()
UPLOADS_DIR = BASE_DIR / 'uploads'
SCREENSHOTS_DIR = BASE_DIR / 'screenshots'
DB_PATH = BASE_DIR / 'jobs.db'

def get_old_jobs(cursor, status, days):
    """Get jobs older than specified days with given status"""
    cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
    cursor.execute("""
        SELECT id, filename, stored_path, payment_screenshot, status
        FROM jobs 
        WHERE status = ? AND submitted_at < ?
    """, (status, cutoff_date))
    return cursor.fetchall()

def get_all_job_files(cursor):
    """Get set of all files referenced in database"""
    cursor.execute("SELECT stored_path, payment_screenshot FROM jobs")
    files = set()
    for row in cursor.fetchall():
        if row[0]:  # stored_path
            files.add(Path(row[0]).name)
        if row[1]:  # payment_screenshot
            files.add(Path(row[1]).name)
    return files

def format_size(bytes):
    """Format bytes to human readable size"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes < 1024.0:
            return f"{bytes:.2f} {unit}"
        bytes /= 1024.0
    return f"{bytes:.2f} TB"

def delete_file(filepath, dry_run=False):
    """Delete file and return size"""
    try:
        if filepath.exists():
            size = filepath.stat().st_size
            if not dry_run:
                filepath.unlink()
            return size
        return 0
    except Exception as e:
        print(f"  ⚠️  Error deleting {filepath.name}: {e}")
        return 0

def delete_job_files(job, dry_run=False):
    """Delete all files associated with a job"""
    deleted_size = 0
    job_id, filename, stored_path, screenshot, status = job
    
    # Delete uploaded file
    if stored_path:
        file_path = BASE_DIR / stored_path
        size = delete_file(file_path, dry_run)
        if size > 0:
            deleted_size += size
            action = "Would delete" if dry_run else "Deleted"
            print(f"  {action}: {file_path.name} ({format_size(size)})")
    
    # Delete screenshot
    if screenshot:
        screenshot_path = BASE_DIR / screenshot
        size = delete_file(screenshot_path, dry_run)
        if size > 0:
            deleted_size += size
            action = "Would delete" if dry_run else "Deleted"
            print(f"  {action}: {screenshot_path.name} ({format_size(size)})")
    
    return deleted_size

def delete_job_from_db(cursor, job_id, dry_run=False):
    """Delete job record from database"""
    if not dry_run:
        cursor.execute("DELETE FROM jobs WHERE id = ?", (job_id,))

def cleanup_old_jobs():
    """Clean up old completed and rejected jobs"""
    print("=" * 70)
    print("🧹 RpiPrint File Cleanup")
    print("=" * 70)
    
    if DRY_RUN:
        print("🔍 DRY RUN MODE - No files will be deleted")
        print()
    
    print(f"Configuration:")
    print(f"  - Completed jobs: Keep {DAYS_TO_KEEP_COMPLETED} days")
    print(f"  - Rejected jobs: Keep {DAYS_TO_KEEP_REJECTED} days")
    print(f"  - Orphaned files: Keep {DAYS_TO_KEEP_ORPHANED} days")
    print()
    
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        total_deleted = 0
        total_jobs = 0
        
        # Clean up completed jobs
        print("🔍 Checking completed jobs...")
        completed_jobs = get_old_jobs(cursor, 'completed', DAYS_TO_KEEP_COMPLETED)
        if completed_jobs:
            print(f"   Found {len(completed_jobs)} old completed job(s)")
            for job in completed_jobs:
                job_id, filename = job[0], job[1]
                print(f"\n   Job: {job_id[:8]}... - {filename}")
                deleted = delete_job_files(job, DRY_RUN)
                delete_job_from_db(cursor, job_id, DRY_RUN)
                total_deleted += deleted
                total_jobs += 1
        else:
            print("   ✓ No old completed jobs to clean")
        
        # Clean up rejected jobs
        print("\n🔍 Checking rejected jobs...")
        rejected_jobs = get_old_jobs(cursor, 'rejected', DAYS_TO_KEEP_REJECTED)
        if rejected_jobs:
            print(f"   Found {len(rejected_jobs)} old rejected job(s)")
            for job in rejected_jobs:
                job_id, filename = job[0], job[1]
                print(f"\n   Job: {job_id[:8]}... - {filename}")
                deleted = delete_job_files(job, DRY_RUN)
                delete_job_from_db(cursor, job_id, DRY_RUN)
                total_deleted += deleted
                total_jobs += 1
        else:
            print("   ✓ No old rejected jobs to clean")
        
        # Clean up refunded jobs (older than completed)
        print("\n🔍 Checking refunded jobs...")
        refunded_jobs = get_old_jobs(cursor, 'refunded', DAYS_TO_KEEP_COMPLETED)
        if refunded_jobs:
            print(f"   Found {len(refunded_jobs)} old refunded job(s)")
            for job in refunded_jobs:
                job_id, filename = job[0], job[1]
                print(f"\n   Job: {job_id[:8]}... - {filename}")
                deleted = delete_job_files(job, DRY_RUN)
                delete_job_from_db(cursor, job_id, DRY_RUN)
                total_deleted += deleted
                total_jobs += 1
        else:
            print("   ✓ No old refunded jobs to clean")
        
        if not DRY_RUN:
            conn.commit()
        conn.close()
        
        print("\n" + "=" * 70)
        print(f"📊 Job Cleanup Summary:")
        print(f"   - Jobs processed: {total_jobs}")
        print(f"   - Space freed: {format_size(total_deleted)}")
        print("=" * 70)
        
    except Exception as e:
        print(f"\n❌ Error during job cleanup: {e}")
        return 1
    
    return 0

def cleanup_orphaned_files():
    """Clean up files not referenced in database"""
    print("\n🔍 Checking for orphaned files...")
    
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Get all files referenced in database
        db_files = get_all_job_files(cursor)
        conn.close()
        
        total_deleted = 0
        total_files = 0
        cutoff_time = time.time() - (DAYS_TO_KEEP_ORPHANED * 24 * 60 * 60)
        
        # Check uploads directory
        if UPLOADS_DIR.exists():
            for file in UPLOADS_DIR.iterdir():
                if file.is_file() and file.name not in db_files:
                    # Check if file is old enough
                    if file.stat().st_mtime < cutoff_time:
                        size = delete_file(file, DRY_RUN)
                        if size > 0:
                            total_deleted += size
                            total_files += 1
                            action = "Would delete" if DRY_RUN else "Deleted"
                            print(f"   {action} orphaned upload: {file.name} ({format_size(size)})")
        
        # Check screenshots directory
        if SCREENSHOTS_DIR.exists():
            for file in SCREENSHOTS_DIR.iterdir():
                if file.is_file() and file.name not in db_files:
                    # Check if file is old enough
                    if file.stat().st_mtime < cutoff_time:
                        size = delete_file(file, DRY_RUN)
                        if size > 0:
                            total_deleted += size
                            total_files += 1
                            action = "Would delete" if DRY_RUN else "Deleted"
                            print(f"   {action} orphaned screenshot: {file.name} ({format_size(size)})")
        
        if total_files == 0:
            print("   ✓ No orphaned files found")
        else:
            print(f"\n📊 Orphaned Files Summary:")
            print(f"   - Files removed: {total_files}")
            print(f"   - Space freed: {format_size(total_deleted)}")
        
    except Exception as e:
        print(f"\n❌ Error during orphaned file cleanup: {e}")
        return 1
    
    return 0

def main():
    """Main cleanup function"""
    print(f"\n⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Check if database exists
    if not DB_PATH.exists():
        print(f"❌ Database not found: {DB_PATH}")
        return 1
    
    # Run cleanup
    result1 = cleanup_old_jobs()
    result2 = cleanup_orphaned_files()
    
    print("\n" + "=" * 70)
    if DRY_RUN:
        print("✅ Dry run completed - No files were deleted")
        print("   Run without --dry-run to actually delete files")
    else:
        print("✅ Cleanup completed successfully")
    print(f"⏰ Finished at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    print()
    
    return result1 or result2

if __name__ == '__main__':
    sys.exit(main())
