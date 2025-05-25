import os
import sys

print("Testing application imports...")

try:
    # Import main app module
    from app import app, db
    print("✓ Successfully imported app module")
    
    # Test database model imports
    from models import User, Post, Comment, Event, EventRegistration
    print("✓ Successfully imported database models")
    
    # Test form imports
    from forms import EventForm, JobForm
    print("✓ Successfully imported forms")
    
    print("\nAll imports successful! The application seems to be set up correctly.")
    print(f"Python version: {sys.version}")
    
    # Check if database file exists
    db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'alumni.db'))
    if os.path.exists(db_path):
        print(f"✓ Database file found at {db_path}")
    else:
        print(f"⚠ Database file not found at {db_path}")
    
except Exception as e:
    print(f"Error during imports: {str(e)}")
    import traceback
    traceback.print_exc() 