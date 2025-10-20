"""
Background task for monitoring CUPS print jobs
"""
import os
import sqlite3
import time
import threading
from datetime import datetime
from config import Config
from utils.print_utils import check_print_job_status

# Global flag to control background task
cups_monitor_running = False
monitor_thread = None


def monitor_cups_jobs(socketio, app):
    """Background task to monitor CUPS job status and broadcast updates via WebSocket"""
    global cups_monitor_running
    
    # Import here to avoid circular dependency
    from websocket.events import broadcast_job_update
    from models.database import update_job_status
    
    print("\n" + "="*60)
    print("🔄 CUPS Monitor Background Task Started")
    print("="*60)
    print("📊 Checking print jobs every 30 seconds...")
    print("="*60 + "\n")
    
    while cups_monitor_running:
        try:
            # Get all jobs currently marked as 'printing'
            con = sqlite3.connect(Config.DB_PATH)
            con.row_factory = sqlite3.Row
            cur = con.cursor()
            
            # Check if print_job_id column exists
            cur.execute("PRAGMA table_info(jobs)")
            columns = [col[1] for col in cur.fetchall()]
            
            if 'print_job_id' not in columns:
                con.close()
                # Sleep in smaller intervals to be responsive to shutdown
                for _ in range(30):
                    if not cups_monitor_running:
                        break
                    time.sleep(1)
                continue
            
            cur.execute('''SELECT id, print_job_id, status, filename FROM jobs 
                           WHERE status = 'printing' AND print_job_id IS NOT NULL''')
            printing_jobs = cur.fetchall()
            con.close()
            
            if len(printing_jobs) > 0:
                print(f"\n{'='*60}")
                print(f"🔍 CUPS Monitor Check - {datetime.now().strftime('%H:%M:%S')}")
                print(f"{'='*60}")
                print(f"📋 Found {len(printing_jobs)} job(s) in 'printing' status")
            
            # Check each printing job
            for job in printing_jobs:
                if not cups_monitor_running:
                    break
                    
                job_id = job['id']
                print_job_id = job['print_job_id']
                old_status = job['status']
                filename = job['filename']
                
                print(f"\n📄 Checking: {filename} (Job ID: {job_id[:8]}...)")
                print(f"   CUPS Job: {print_job_id}")
                print(f"   DB Status: {old_status}")
                
                # Check actual status from CUPS
                actual_status = check_print_job_status(print_job_id)
                
                print(f"   CUPS Status: {actual_status}")
                
                # If status changed, update database and broadcast
                if actual_status != old_status and actual_status != 'unknown':
                    print(f"\n✅ Status Changed: {old_status} → {actual_status}")
                    
                    # Update database within app context
                    with app.app_context():
                        con = sqlite3.connect(Config.DB_PATH)
                        cur = con.cursor()
                        cur.execute('UPDATE jobs SET status = ? WHERE id = ?', (actual_status, job_id))
                        con.commit()
                        con.close()
                        
                        # Broadcast update
                        print(f"📡 Broadcasting update to all connected clients...")
                        broadcast_job_update(socketio, job_id, actual_status, f'status_changed_to_{actual_status}')
                elif actual_status == old_status:
                    print(f"   ℹ️  No change (still {actual_status})")
            
            if len(printing_jobs) > 0:
                print(f"{'='*60}\n")
            
        except Exception as e:
            print(f"\n❌ Error in CUPS monitor: {e}")
        
        # Wait 30 seconds before next check, but check shutdown flag every second
        for _ in range(30):
            if not cups_monitor_running:
                break
            time.sleep(1)
    
    print("\n🛑 CUPS Monitor Background Task Stopped\n")


def start_cups_monitor(socketio, app):
    """Start the CUPS monitoring background task"""
    global cups_monitor_running, monitor_thread
    
    if not cups_monitor_running:
        cups_monitor_running = True
        monitor_thread = threading.Thread(target=monitor_cups_jobs, args=(socketio, app), daemon=True)
        monitor_thread.start()
        print("✅ CUPS monitoring thread started")


def stop_cups_monitor():
    """Stop the CUPS monitoring background task"""
    global cups_monitor_running
    cups_monitor_running = False
    print("🛑 CUPS monitoring thread stopping...")
