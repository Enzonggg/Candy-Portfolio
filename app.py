from flask import Flask, render_template, request, redirect, url_for, flash, session 
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os
from datetime import datetime

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'  # Change this to a random secret key
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///portfolio.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max-limit

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Initialize database
db = SQLAlchemy(app)

# Add a context processor to make request available in all templates
@app.context_processor
def inject_request():
    return {'request': request}

# Add custom jinja2 filters
@app.template_filter('nl2br')
def nl2br_filter(text):
    if text:
        return text.replace('\n', '<br>')
    return ''

# Models
class User(db.Model): # Represents a user in the system
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
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Project(db.Model): # Represents a project in the system
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    date_posted = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    image_filename = db.Column(db.String(100), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

# Initialize database tables - ensure this happens with the app context
with app.app_context():
    db.create_all()
    print("Database tables created (if they didn't exist already)")

# Routes
@app.route('/') 
def home():
    projects = Project.query.order_by(Project.date_posted.desc()).all()
    return render_template('home.html', projects=projects)

# User Authentication Routes
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        
        # Check if username or email already exists
        user_exists = User.query.filter_by(username=username).first()
        email_exists = User.query.filter_by(email=email).first()
        
        if user_exists:
            flash('Username already exists!')
            return redirect(url_for('register'))
        
        if email_exists:
            flash('Email already registered!')
            return redirect(url_for('register'))
        
        # Create new user
        new_user = User(username=username, email=email)
        new_user.set_password(password)
        
        db.session.add(new_user)
        db.session.commit()
        
        flash('Registration successful! Please log in.')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST']) # User login route
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user = User.query.filter_by(username=username).first()
        
        if not user:
            flash(f'Username "{username}" not found')
            return redirect(url_for('login'))
            
        if user and user.check_password(password):
            session['user_id'] = user.id
            flash(f'Login successful! Welcome {user.username}')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid password')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash('You have been logged out')
    return redirect(url_for('home'))

# User Dashboard
@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        flash('Please log in first')
        return redirect(url_for('login'))
    
    user = User.query.get(session['user_id'])
    
    # Handle case where user doesn't exist despite having a session
    if not user:
        session.clear()  # Clear invalid session
        flash('User not found. Please log in again.')
        return redirect(url_for('login'))
    
    projects = Project.query.filter_by(user_id=user.id).all()
    all_users = User.query.all()  # Get all users for the dashboard
    
    return render_template('dashboard.html', user=user, projects=projects, all_users=all_users)

@app.route('/user/<int:user_id>/sanctuary')
def user_sanctuary(user_id):
    viewed_user = User.query.get_or_404(user_id)
    projects = Project.query.filter_by(user_id=viewed_user.id).all()
    return render_template('user_sanctuary.html', user=viewed_user, projects=projects)

# Profile Routes
@app.route('/profile')
def view_profile():
    if 'user_id' not in session:
        flash('Please log in first')
        return redirect(url_for('login'))
    
    user = User.query.get(session['user_id'])
    
    # Handle case where user doesn't exist despite having a session
    if not user:
        session.clear()  # Clear invalid session
        flash('User not found. Please log in again.')
        return redirect(url_for('login'))
    
    return render_template('profile.html', user=user)

@app.route('/profile/edit', methods=['GET', 'POST']) # Edit user profile route
def edit_profile():
    if 'user_id' not in session:
        flash('Please log in first')
        return redirect(url_for('login'))
    
    user = User.query.get(session['user_id']) 
    
    # Handle case where user doesn't exist despite having a session
    if not user:
        session.clear()  # Clear invalid session
        flash('User not found. Please log in again.')
        return redirect(url_for('login'))
    
    if request.method == 'POST': # Update user profile
        user.about_me = request.form['about_me']
        user.tech_stack = request.form['tech_stack']
        user.birthdate = request.form['birthdate']
        user.location = request.form['location']
        user.occupation = request.form['occupation']
        user.social_media = request.form['social_media']
        user.contact_info = request.form['contact_info']
        
        # Additional fields
        user.full_name = request.form['full_name']
        user.age = request.form['age']
        user.gender = request.form['gender']
        user.address = request.form['address']
        user.student_id = request.form['student_id']
        user.section = request.form['section']
        
        db.session.commit()
        flash('Your dark essence has been transformed!')
        return redirect(url_for('view_profile'))
    
    return render_template('edit_profile.html', user=user)

@app.route('/user/<int:user_id>/profile') # View another user's profile route
def user_profile(user_id):
    user = User.query.get_or_404(user_id)
    return render_template('user_profile.html', user=user)

# Project Routes
@app.route('/project/new', methods=['GET', 'POST']) # Create new project route
def new_project():
    if 'user_id' not in session:
        flash('Please log in first')
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        
        # Handle file upload
        image_filename = None
        if 'image' in request.files:
            file = request.files['image']
            if file.filename != '':
                filename = secure_filename(file.filename)
                image_filename = f"{session['user_id']}_{datetime.now().strftime('%Y%m%d%H%M%S')}_{filename}" # Unique filename
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], image_filename))
        
        # Create new project
        new_project = Project(
            title=title,
            description=description,
            image_filename=image_filename,
            user_id=session['user_id']
        )
        
        db.session.add(new_project)
        db.session.commit() 
        
        flash('Project posted successfully!')
        return redirect(url_for('dashboard'))
    
    return render_template('new_project.html')

@app.route('/project/<int:project_id>') # View project route
def view_project(project_id):
    project = Project.query.get_or_404(project_id) 
    return render_template('view_project.html', project=project)

@app.route('/project/<int:project_id>/edit', methods=['GET', 'POST'])
def edit_project(project_id):
    if 'user_id' not in session:
        flash('Please log in first')
        return redirect(url_for('login'))
    
    project = Project.query.get_or_404(project_id)
    
    # Check if user is the author
    if project.user_id != session['user_id']:
        flash('You do not have permission to edit this project')
        return redirect(url_for('home'))
    
    if request.method == 'POST':
        project.title = request.form['title']
        project.description = request.form['description']
        
        # Handle file upload if a new image is provided
        if 'image' in request.files:
            file = request.files['image']
            if file.filename != '':
                # Delete old image if it exists
                if project.image_filename:
                    old_image_path = os.path.join(app.config['UPLOAD_FOLDER'], project.image_filename) 
                    if os.path.exists(old_image_path):
                        os.remove(old_image_path)
                
                # Save new image
                filename = secure_filename(file.filename)
                project.image_filename = f"{session['user_id']}_{datetime.now().strftime('%Y%m%d%H%M%S')}_{filename}" 
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], project.image_filename))
        
        db.session.commit()
        flash('Project updated successfully!')
        return redirect(url_for('view_project', project_id=project.id))
    
    return render_template('edit_project.html', project=project)

@app.route('/project/<int:project_id>/delete', methods=['POST'])
def delete_project(project_id):
    if 'user_id' not in session:
        flash('Please log in first')
        return redirect(url_for('login'))
    
    project = Project.query.get_or_404(project_id)
    
    # Check if user is the author
    if project.user_id != session['user_id']:
        flash('You do not have permission to delete this project')
        return redirect(url_for('home'))
    
    # Delete the associated image file if it exists
    if project.image_filename:
        image_path = os.path.join(app.config['UPLOAD_FOLDER'], project.image_filename)
        if os.path.exists(image_path):
            os.remove(image_path)
    
    db.session.delete(project)
    db.session.commit()
    
    flash('Project deleted successfully!')
    return redirect(url_for('dashboard'))

# Add User Route
@app.route('/add_user', methods=['GET', 'POST'])
def add_user():
    if 'user_id' not in session:
        flash('Please log in first')
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        about_me = request.form['about_me']
        tech_stack = request.form['tech_stack']
        
        # Check if username or email already exists
        user_exists = User.query.filter_by(username=username).first()
        email_exists = User.query.filter_by(email=email).first()
        
        if user_exists:
            flash('Username already exists!')
            return redirect(url_for('add_user'))
        
        if email_exists:
            flash('Email already registered!')
            return redirect(url_for('add_user'))
        
        # Create new user
        new_user = User(
            username=username, 
            email=email,
            about_me=about_me,
            tech_stack=tech_stack
        )
        new_user.set_password(password)
        
        db.session.add(new_user)
        db.session.commit()
        
        flash(f'New soul "{username}" has been summoned to the netherworld!')
        return redirect(url_for('dashboard'))
    
    return render_template('add_user.html')

# User Impersonation Route
@app.route('/impersonate/<int:user_id>', methods=['POST'])
def impersonate_user(user_id):
    if 'user_id' not in session:
        flash('Please log in first')
        return redirect(url_for('login'))
    
    # Store original user ID for potential "switch back" feature
    if 'original_user_id' not in session:
        session['original_user_id'] = session['user_id']
    
    # Switch to the target user
    target_user = User.query.get_or_404(user_id)
    session['user_id'] = target_user.id
    
    flash(f'You are now possessing the soul of {target_user.username}')
    return redirect(url_for('dashboard'))

# Return to Original User
@app.route('/return_to_self', methods=['POST']) 
def return_to_self():
    if 'original_user_id' in session:
        original_user = User.query.get(session['original_user_id'])
        if original_user:
            session['user_id'] = session['original_user_id']
            flash(f'You have returned to your own form, {original_user.username}')
        session.pop('original_user_id', None)
    
    return redirect(url_for('dashboard'))

# Run the application
if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Create database tables
    app.run(debug=True)
