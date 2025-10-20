"""
CUPS printing utilities
"""
import os
import subprocess


def print_file(file_path, printer="G3000-series", copies=1, orientation="portrait", color_mode="bw"):
    """Send file to printer and return job ID if successful"""
    print(f"\n{'='*60}")
    print(f"🖨️  PRINT_FILE FUNCTION CALLED")
    print(f"{'='*60}")
    print(f"📄 File: {file_path}")
    print(f"🖨️  Printer: {printer}")
    print(f"📋 Copies: {copies}")
    print(f"📐 Orientation: {orientation}")
    print(f"🎨 Color Mode: {color_mode}")
    
    # Check if file exists
    if not os.path.exists(file_path):
        print(f"❌ ERROR: File does not exist!")
        print(f"{'='*60}\n")
        return {'success': False, 'job_id': None, 'error': 'File not found'}
    
    print(f"✅ File exists, size: {os.path.getsize(file_path)} bytes")
    
    # Send the file to CUPS using lp with options
    cmd = ['lp', '-d', printer, '-n', str(copies)]
    
    # Add orientation option
    if orientation == 'landscape':
        cmd.extend(['-o', 'landscape'])
    else:
        cmd.extend(['-o', 'portrait'])
    
    # Add color mode option (Canon-specific options)
    if color_mode == 'bw':
        # Use Canon's Grayscale option for B&W printing
        cmd.extend(['-o', 'CNIJGrayScale=1'])
    else:
        # Use default color mode (CNIJGrayScale=0)
        cmd.extend(['-o', 'CNIJGrayScale=0'])
    
    cmd.append(file_path)
    
    print(f"💻 Executing command: {' '.join(cmd)}")
    
    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    
    print(f"📊 Return code: {proc.returncode}")
    
    if proc.returncode == 0:
        # Extract job ID from output: "request id is Canon_G3000_W-123 (1 file(s))"
        output = proc.stdout.strip()
        print(f"✅ SUCCESS!")
        print(f"📤 STDOUT: {output}")
        
        if 'request id is' in output:
            try:
                job_id = output.split('request id is ')[1].split(' ')[0]
                print(f"🎫 CUPS Job ID: {job_id}")
                print(f"{'='*60}\n")
                return {'success': True, 'job_id': job_id}
            except Exception as e:
                print(f"⚠️  Could not extract job ID: {e}")
                print(f"{'='*60}\n")
                return {'success': True, 'job_id': None}
        print(f"⚠️  No job ID in output")
        print(f"{'='*60}\n")
        return {'success': True, 'job_id': None}
    else:
        error = proc.stderr.strip()
        print(f"❌ PRINT FAILED!")
        print(f"📥 STDERR: {error}")
        print(f"{'='*60}\n")
        return {'success': False, 'job_id': None, 'error': error}


def check_print_job_status(job_id):
    """Check the status of a CUPS print job
    
    Returns one of: 'printing', 'pending', 'completed', 'canceled', 'aborted', 'error', 'unknown'
    """
    print(f"\n🔍 Checking CUPS status for job: {job_id}")
    
    if not job_id:
        print(f"❌ No job ID provided")
        return 'unknown'
    
    # First, check if job is in the ACTIVE queue (printing/pending)
    cmd_active = ['lpstat', '-o']
    print(f"💻 Running: {' '.join(cmd_active)}")
    
    proc_active = subprocess.run(cmd_active, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    
    if proc_active.returncode != 0:
        print(f"❌ lpstat failed with return code {proc_active.returncode}")
        print(f"STDERR: {proc_active.stderr}")
        return 'unknown'
    
    active_output = proc_active.stdout
    print(f"📊 Active jobs output: {len(active_output)} chars")
    
    # Check if job is in active queue
    if job_id in active_output:
        print(f"✅ Job {job_id} found in ACTIVE queue")
        
        # Get detailed status with lpstat -l
        cmd_detail = ['lpstat', '-l', '-o', job_id]
        proc_detail = subprocess.run(cmd_detail, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        detail_output = proc_detail.stdout.lower()
        
        print(f"📋 Job details:\n{proc_detail.stdout}")
        
        # Check for specific status keywords
        if 'processing' in detail_output or 'printing' in detail_output:
            print(f"📋 Status: printing (actively processing)")
            return 'printing'
        elif 'pending' in detail_output or 'held' in detail_output or 'waiting' in detail_output:
            print(f"📋 Status: pending (waiting in queue)")
            return 'pending'
        else:
            # Job is in active queue but no specific status - assume printing
            print(f"📋 Status: printing (in active queue)")
            return 'printing'
    
    # Job not in active queue - check for completed/canceled/aborted
    print(f"❌ Job {job_id} NOT in active queue")
    
    # Check completed jobs with detailed output
    cmd_completed = ['lpstat', '-W', 'completed', '-l']
    print(f"💻 Running: {' '.join(cmd_completed)}")
    
    proc_completed = subprocess.run(cmd_completed, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    
    if proc_completed.returncode == 0:
        completed_output = proc_completed.stdout
        
        # Check if this specific job is in the output
        if job_id in completed_output:
            print(f"✅ Job {job_id} found in COMPLETED history")
            
            # Parse the output to find this job's details
            lines = completed_output.split('\n')
            job_section = []
            in_job = False
            
            for line in lines:
                if job_id in line:
                    in_job = True
                    job_section.append(line)
                elif in_job:
                    # Continue collecting lines until next job or empty line
                    if line and not line[0].isspace() and '-' in line:
                        # Start of next job
                        break
                    job_section.append(line)
            
            job_details = '\n'.join(job_section).lower()
            print(f"📋 Job section:\n{job_details}")
            
            # Analyze the job state
            if 'canceled' in job_details or 'cancelled' in job_details:
                print(f"📋 Status: canceled")
                return 'canceled'
            elif 'aborted' in job_details:
                print(f"📋 Status: aborted")
                return 'aborted'
            elif 'error' in job_details or 'failed' in job_details:
                print(f"📋 Status: error")
                return 'error'
            elif 'completed' in job_details or 'finished' in job_details:
                print(f"📋 Status: completed")
                return 'completed'
            else:
                # Found in completed queue but no clear status - assume completed
                print(f"📋 Status: completed (found in history, no errors)")
                return 'completed'
        else:
            print(f"ℹ️  Job {job_id} not found in completed history")
    
    # Job not found anywhere - might be very old or already purged
    # Check if it's still pending somewhere
    print(f"ℹ️  Job {job_id} not found in any queue (might be purged)")
    print(f"📋 Status: unknown (job not found)")
    return 'unknown'
