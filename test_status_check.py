#!/usr/bin/env python3
"""
Test script to verify CUPS status checking logic
"""
import subprocess

def check_print_job_status(job_id):
    """Check the status of a CUPS print job - FIXED VERSION"""
    print(f"\n{'='*60}")
    print(f"🔍 Testing Status Check for: {job_id}")
    print(f"{'='*60}")
    
    if not job_id:
        print(f"❌ No job ID provided")
        return 'unknown'
    
    # First, check if job is in the ACTIVE queue (not completed)
    cmd_active = ['lpstat', '-o']
    print(f"💻 Checking active queue: {' '.join(cmd_active)}")
    
    proc_active = subprocess.run(cmd_active, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    
    if proc_active.returncode != 0:
        print(f"❌ lpstat failed with return code {proc_active.returncode}")
        return 'unknown'
    
    active_output = proc_active.stdout
    print(f"📊 Active jobs count: {len(active_output.strip().split(chr(10))) if active_output.strip() else 0}")
    
    # Check if job is in active queue
    if job_id in active_output:
        print(f"✅ Job {job_id} IS in ACTIVE queue")
        print(f"📋 Status: printing")
        return 'printing'
    else:
        print(f"❌ Job {job_id} NOT in active queue")
        
        # Job not in active queue - check completed jobs
        cmd_completed = ['lpstat', '-W', 'completed', '-o']
        print(f"💻 Checking completed queue: {' '.join(cmd_completed)}")
        
        proc_completed = subprocess.run(cmd_completed, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        completed_output = proc_completed.stdout
        
        print(f"📊 Completed jobs count: {len(completed_output.strip().split(chr(10))) if completed_output.strip() else 0}")
        
        if proc_completed.returncode == 0 and job_id in completed_output:
            print(f"✅ Job {job_id} IS in COMPLETED queue")
            print(f"📋 Status: completed")
            return 'completed'
        else:
            print(f"❌ Job {job_id} NOT in completed queue either")
            print(f"📋 Status: completed (assumed)")
            return 'completed'


if __name__ == '__main__':
    # Test with a known completed job
    test_job_id = 'Canon_G3000_W-13'
    
    print(f"\n{'#'*60}")
    print(f"# CUPS STATUS CHECK TEST")
    print(f"{'#'*60}")
    
    status = check_print_job_status(test_job_id)
    
    print(f"\n{'='*60}")
    print(f"✅ FINAL RESULT: {status}")
    print(f"{'='*60}\n")
    
    # Show the difference between old and new approach
    print(f"\n{'#'*60}")
    print(f"# COMPARISON: Old vs New Approach")
    print(f"{'#'*60}\n")
    
    print("❌ OLD APPROACH (BROKEN):")
    print("   lpstat -W all -o  → Shows ALL jobs (active + completed)")
    print("   Problem: Job found in output → Thinks it's still printing!")
    print()
    
    print("✅ NEW APPROACH (FIXED):")
    print("   lpstat -o  → Shows ONLY active jobs")
    print("   lpstat -W completed -o  → Shows ONLY completed jobs")
    print("   If in active queue → printing")
    print("   If in completed queue → completed")
    print("   If nowhere → completed (assumed)")
