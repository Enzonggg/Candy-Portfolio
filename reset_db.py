from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash
from datetime import datetime
import os
import sys
import sqlite3

print("=" * 60)
print("PORTFOLIO SYSTEM DATABASE RESET TOOL")
print("=" * 60)
print("This tool will reset your database and recreate it with proper schema")
print("WARNING: All existing data will be lost!")
print()

# Define and create Flask app (minimal version for DB operations)
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///portfolio.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize database
db = SQLAlchemy(app)

# Define the location of the database file
db_file = 'instance/portfolio.db'

# Models definition needs to match app.py exactly
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    projects = db.relationship('Project', backref='author', lazy=True)
    about_me = db.Column(db.Text, nullable=True)
    tech_stack = db.Column(db.Text, nullable=True)
    # Personal information fields
    birthdate = db.Column(db.String(20), nullable=True)
    location = db.Column(db.String(100), nullable=True)
    occupation = db.Column(db.String(100), nullable=True)
    social_media = db.Column(db.Text, nullable=True)
    contact_info = db.Column(db.Text, nullable=True)
    # Additional personal fields
    full_name = db.Column(db.String(100), nullable=True)
    age = db.Column(db.String(20), nullable=True)
    gender = db.Column(db.String(50), nullable=True)
    address = db.Column(db.Text, nullable=True)
    student_id = db.Column(db.String(50), nullable=True)
    section = db.Column(db.String(50), nullable=True)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    date_posted = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    image_filename = db.Column(db.String(100), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

# Main execution
try:
    print("\nChecking for database file...")
    if os.path.exists(db_file):
        print(f"Database file found at {os.path.abspath(db_file)}")
    else:
        print(f"Database file does not exist at {os.path.abspath(db_file)}. It will be created.")
    
    print("\nInitiating full database reset...")
    
    with app.app_context():
        print("\nStep 1: Dropping all existing tables...")
        db.drop_all()
        print("All tables dropped successfully")
        
        print("\nStep 2: Creating tables with complete schema...")
        db.create_all()
        print("Database tables created with full schema")
        
        print("\nStep 3: Creating sample users...")
        # Create admin user with all fields
        admin = User(
            username="admin", 
            email="admin@example.com", 
            about_me="I manage this sweet portfolio system!",
            tech_stack="HTML, CSS, JavaScript, Python, Flask",
            birthdate="2000-01-01",
            location="Main Campus",
            occupation="Student",
            social_media="twitter: @admin, instagram: @admin",
            contact_info="admin@example.com",
            full_name="Admin User",
            age="21",
            gender="Unspecified",
            address="123 Campus Drive",
            student_id="ADMIN-001",
            section="Administrator Section"
        )
        admin.set_password("admin123")
        db.session.add(admin)
        
        # Create demo user too
        demo_user = User(
            username="demo", 
            email="demo@example.com",
            about_me="I'm a demo user for the portfolio system.",
            tech_stack="HTML, CSS, JavaScript, Python",
            birthdate="2000-01-01",
            location="Demo Campus",
            occupation="Student",
            social_media="twitter: @demo, instagram: @demouser",
            contact_info="demo@example.com",
            full_name="Demo User",
            age="20",
            gender="Unspecified",
            address="456 Demo Street",
            student_id="DEMO-123",
            section="Demo Section"
        )
        demo_user.set_password("demo123")
        db.session.add(demo_user)
        
        # Create a sample project for demo user
        sample_project = Project(
            title="Sample Project",
            description="This is a sample project to demonstrate the portfolio system.",
            user_id=2  # This should be the demo user's ID
        )
        db.session.add(sample_project)
        
        # Commit changes
        db.session.commit()
        print("Default users and sample project created!")
        print("\nAccount details:")
        print("- Admin username: admin")
        print("- Admin password: admin123")
        print("- Demo username: demo")
        print("- Demo password: demo123")
        
        # Verify database
        print("\nStep 4: Verifying database structure...")
        admin = User.query.filter_by(username="admin").first()
        demo = User.query.filter_by(username="demo").first()
        
        if admin and demo:
            print("Database verification complete! All users created successfully.")
        else:
            print("WARNING: User verification failed!")
    
    print("\n" + "=" * 60)
    print("DATABASE RESET COMPLETE!")
    print("=" * 60)
    print("\nYou can now run the Flask application with 'python app.py'")
    print("IMPORTANT: Login with admin/admin123 or demo/demo123")
    
except Exception as e:
    print(f"\nERROR: {str(e)}")
    print("\nThe database reset failed. This might be because:")
    print("1. The Flask application is still running - please stop it first")
    print("2. Another process has the database file open")
    print("3. You don't have permission to modify the database file")
    print("\nTroubleshooting steps:")
    print("1. Stop all Flask applications")
    print("2. Try deleting the database file manually at:", os.path.abspath(db_file))
    print("3. Then run this script again")
    
    sys.exit(1)
