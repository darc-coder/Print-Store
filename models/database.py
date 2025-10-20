"""
Database initialization and helper functions
"""
import sqlite3
from pathlib import Path
from flask import url_for
from config import Config


def init_db():
    """Initialize the database with the jobs table"""
    con = sqlite3.connect(Config.DB_PATH)
    cur = con.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS jobs (
            id TEXT PRIMARY KEY,
            filename TEXT,
            stored_path TEXT,
            pages INTEGER,
            cost REAL,
            status TEXT,
            copies INTEGER DEFAULT 1,
            orientation TEXT DEFAULT 'portrait',
            print_color TEXT DEFAULT 'bw',
            payment_screenshot TEXT,
            submitted_at TEXT,
            approved_at TEXT,
            approved_by TEXT,
            print_job_id TEXT,
            refunded_at TEXT,
            refunded_by TEXT
        )
    ''')
    con.commit()
    con.close()


def save_job(job_id, filename, stored_path, pages, cost, status='pending', copies=1, orientation='portrait', print_color='bw'):
    """Save a new job to the database"""
    con = sqlite3.connect(Config.DB_PATH)
    cur = con.cursor()
    cur.execute('''INSERT INTO jobs 
                   (id, filename, stored_path, pages, cost, status, copies, orientation, print_color) 
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                (job_id, filename, stored_path, pages, cost, status, copies, orientation, print_color))
    con.commit()
    con.close()


def get_job(job_id):
    """Get a job by ID"""
    con = sqlite3.connect(Config.DB_PATH)
    cur = con.cursor()
    
    # Check if print_job_id, payment_screenshot, and print_color columns exist
    cur.execute("PRAGMA table_info(jobs)")
    columns = [col[1] for col in cur.fetchall()]
    
    # Build SELECT query based on available columns
    base_fields = 'id, filename, stored_path, pages, cost, status, copies, orientation'
    has_print_job_id = 'print_job_id' in columns
    has_payment_screenshot = 'payment_screenshot' in columns
    has_print_color = 'print_color' in columns
    
    # Build the query dynamically
    select_fields = base_fields
    if has_print_job_id:
        select_fields += ', print_job_id'
    if has_payment_screenshot:
        select_fields += ', payment_screenshot'
    if has_print_color:
        select_fields += ', print_color'
    
    cur.execute(f'''SELECT {select_fields} FROM jobs WHERE id = ?''', (job_id,))
    row = cur.fetchone()
    
    con.close()
    if not row:
        return None
    
    # Parse row based on what columns exist
    base_idx = 8
    print_job_id = None
    payment_screenshot = None
    print_color = 'bw'  # default
    
    if has_print_job_id:
        print_job_id = row[base_idx] if len(row) > base_idx else None
        base_idx += 1
    if has_payment_screenshot:
        payment_screenshot = row[base_idx] if len(row) > base_idx else None
        base_idx += 1
    if has_print_color:
        print_color = row[base_idx] if len(row) > base_idx else 'bw'
    
    # Generate preview_url from stored_path
    filename = Path(row[2]).name if row[2] else None
    preview_url = url_for('user.serve_upload', filename=filename) if filename else None
    
    return dict(
        id=row[0], 
        filename=row[1], 
        stored_path=row[2], 
        pages=row[3], 
        cost=row[4], 
        status=row[5],
        copies=row[6] or 1,
        orientation=row[7] or 'portrait',
        print_color=print_color,
        print_job_id=print_job_id,
        payment_screenshot=payment_screenshot,
        preview_url=preview_url,
        file_number=1
    )


def update_job_status(job_id, status):
    """Update job status"""
    con = sqlite3.connect(Config.DB_PATH)
    cur = con.cursor()
    cur.execute('UPDATE jobs SET status = ? WHERE id = ?', (status, job_id))
    con.commit()
    con.close()


def update_job_settings(job_id, copies, orientation, print_color='bw'):
    """Update job copies, orientation, and color settings"""
    con = sqlite3.connect(Config.DB_PATH)
    cur = con.cursor()
    cur.execute('UPDATE jobs SET copies = ?, orientation = ?, print_color = ? WHERE id = ?', 
               (copies, orientation, print_color, job_id))
    con.commit()
    con.close()


def update_job_print_id(job_id, print_job_id):
    """Store the CUPS print job ID for status tracking"""
    con = sqlite3.connect(Config.DB_PATH)
    cur = con.cursor()
    # Check if column exists, if not add it
    cur.execute("PRAGMA table_info(jobs)")
    columns = [col[1] for col in cur.fetchall()]
    if 'print_job_id' not in columns:
        cur.execute('ALTER TABLE jobs ADD COLUMN print_job_id TEXT')
    cur.execute('UPDATE jobs SET print_job_id = ? WHERE id = ?', (print_job_id, job_id))
    con.commit()
    con.close()
