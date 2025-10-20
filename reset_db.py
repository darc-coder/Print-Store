#!/usr/bin/env python3
"""
Database Reset Script for RpiPrint
Deletes the existing database and recreates it with the correct schema
"""
import os
import sys
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

from models.database import init_db

def main():
    """Reset the database"""
    print("=" * 60)
    print("🗄️  RpiPrint Database Reset")
    print("=" * 60)
    print()
    
    db_path = Path(__file__).parent / 'jobs.db'
    
    # Check if database exists
    if db_path.exists():
        print(f"⚠️  WARNING: This will delete the existing database!")
        print(f"   Location: {db_path}")
        print(f"   Size: {db_path.stat().st_size / 1024:.2f} KB")
        print()
        print("   All jobs, uploads, and payment data will be LOST!")
        print()
        
        # Confirm deletion
        response = input("Type 'yes' to continue: ").strip().lower()
        
        if response != 'yes':
            print()
            print("❌ Reset cancelled. Database was not modified.")
            return
        
        # Delete the database
        print()
        print("Deleting database...")
        db_path.unlink()
        print("✅ Database deleted")
    else:
        print("ℹ️  No existing database found")
    
    # Recreate the database
    print()
    print("Creating new database with correct schema...")
    init_db()
    print("✅ Database created successfully")
    
    print()
    print("=" * 60)
    print("🎉 Database Reset Complete!")
    print("=" * 60)
    print()
    print("The database is now ready with the latest schema.")
    print("All tables have been created with correct columns.")
    print()
    print("Next steps:")
    print("  1. Start the server: python3 app.py")
    print("  2. Or for production: python3 app_production.py")
    print()

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print()
        print()
        print("❌ Reset interrupted by user")
        sys.exit(1)
    except Exception as e:
        print()
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
