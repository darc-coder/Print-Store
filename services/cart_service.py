"""
Shopping cart service for managing user sessions
"""
import sqlite3
from flask import session
from models.database import get_job
from config import Config


def get_cart_jobs():
    """Get all job IDs from the current session cart"""
    return session.get('cart', [])


def add_to_cart(job_id):
    """Add a job ID to the session cart"""
    cart = session.get('cart', [])
    if job_id not in cart:
        cart.append(job_id)
        session['cart'] = cart


def remove_from_cart(job_id):
    """Remove a job ID from the session cart"""
    cart = session.get('cart', [])
    if job_id in cart:
        cart.remove(job_id)
        session['cart'] = cart


def clear_cart():
    """Clear all items from the cart"""
    session['cart'] = []


def get_cart_summary():
    """Get summary of all jobs in cart"""
    cart_job_ids = get_cart_jobs()
    jobs = []
    total_pages = 0
    total_cost = 0
    
    for job_id in cart_job_ids:
        job = get_job(job_id)
        if job:
            jobs.append(job)
            copies = job.get('copies', 1)
            total_pages += job['pages'] * copies
            # job['cost'] already includes copies, so don't multiply again
            total_cost += job['cost']
    
    return {
        'jobs': jobs,
        'total_pages': total_pages,
        'total_cost': total_cost,
        'count': len(jobs)
    }
