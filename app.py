from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'  # Change this to a secure secret key
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///alumni.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Database Models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    is_admin = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    profile = db.relationship('Profile', backref='user', uselist=False)
    posts = db.relationship('Post', backref='author', lazy=True)
    sent_messages = db.relationship('Message', backref='sender', foreign_keys='Message.sender_id')
    received_messages = db.relationship('Message', backref='recipient', foreign_keys='Message.recipient_id')
    created_events = db.relationship('Event', backref='creator', lazy=True)
    registered_events = db.relationship('EventRegistration', backref='user', lazy=True)
    job_posts = db.relationship('Job', backref='posted_by', lazy=True)
    connections = db.relationship('Connection', backref='user', foreign_keys='Connection.user_id')
    connection_requests = db.relationship('ConnectionRequest', backref='sender', foreign_keys='ConnectionRequest.sender_id')

class Profile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    full_name = db.Column(db.String(100))
    bio = db.Column(db.Text)
    current_job = db.Column(db.String(100))
    location = db.Column(db.String(100))
    avatar = db.Column(db.String(200))

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    comments = db.relationship('Comment', backref='post', lazy=True)

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    recipient_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    is_read = db.Column(db.Boolean, default=False)

class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    date = db.Column(db.Date, nullable=False)
    time = db.Column(db.Time, nullable=False)
    location = db.Column(db.String(200), nullable=False)
    type = db.Column(db.String(50), nullable=False)
    max_participants = db.Column(db.Integer, nullable=False)
    registration_deadline = db.Column(db.Date, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    creator_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    registrations = db.relationship('EventRegistration', backref='event', lazy=True)

class EventRegistration(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey('event.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    registered_at = db.Column(db.DateTime, default=datetime.utcnow)

class Job(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    company = db.Column(db.String(200), nullable=False)
    location = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    requirements = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(50), nullable=False)
    type = db.Column(db.String(50), nullable=False)
    experience_level = db.Column(db.String(50), nullable=False)
    contact_email = db.Column(db.String(120), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    posted_by_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

class Connection(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    connected_user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class ConnectionRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    recipient_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, accepted, rejected
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class SystemSettings(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    site_name = db.Column(db.String(100), default='Alumni Network')
    site_description = db.Column(db.Text)
    maintenance_mode = db.Column(db.Boolean, default=False)

class ActivityLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    description = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Routes
@app.route('/')
def index():
    posts = Post.query.order_by(Post.created_at.desc()).all()
    return render_template('index.html', posts=posts)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            return redirect(url_for('index'))
        flash('Invalid username or password')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        
        if User.query.filter_by(username=username).first():
            flash('Username already exists')
            return redirect(url_for('register'))
            
        if User.query.filter_by(email=email).first():
            flash('Email already registered')
            return redirect(url_for('register'))
            
        user = User(
            username=username,
            email=email,
            password_hash=generate_password_hash(password)
        )
        db.session.add(user)
        db.session.commit()
        
        login_user(user)
        return redirect(url_for('index'))
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/profile')
@login_required
def profile():
    return render_template('profile.html')

@app.route('/update_profile', methods=['POST'])
@login_required
def update_profile():
    if not current_user.profile:
        current_user.profile = Profile(user_id=current_user.id)
    
    current_user.profile.full_name = request.form.get('full_name')
    current_user.profile.current_job = request.form.get('current_job')
    current_user.profile.location = request.form.get('location')
    current_user.profile.bio = request.form.get('bio')
    
    db.session.commit()
    flash('Profile updated successfully')
    return redirect(url_for('profile'))

@app.route('/update_avatar', methods=['POST'])
@login_required
def update_avatar():
    if 'avatar' not in request.files:
        flash('No file uploaded')
        return redirect(url_for('profile'))
    
    file = request.files['avatar']
    if file.filename == '':
        flash('No file selected')
        return redirect(url_for('profile'))
    
    if file:
        filename = f"{current_user.id}_{file.filename}"
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        
        if not current_user.profile:
            current_user.profile = Profile(user_id=current_user.id)
        
        current_user.profile.avatar = f"uploads/{filename}"
        db.session.commit()
        flash('Avatar updated successfully')
    
    return redirect(url_for('profile'))

@app.route('/update_password', methods=['POST'])
@login_required
def update_password():
    current_password = request.form.get('current_password')
    new_password = request.form.get('new_password')
    confirm_password = request.form.get('confirm_password')
    
    if not check_password_hash(current_user.password_hash, current_password):
        flash('Current password is incorrect')
        return redirect(url_for('profile'))
    
    if new_password != confirm_password:
        flash('New passwords do not match')
        return redirect(url_for('profile'))
    
    current_user.password_hash = generate_password_hash(new_password)
    db.session.commit()
    flash('Password updated successfully')
    return redirect(url_for('profile'))

@app.route('/delete_account', methods=['POST'])
@login_required
def delete_account():
    db.session.delete(current_user)
    db.session.commit()
    logout_user()
    flash('Account deleted successfully')
    return redirect(url_for('index'))

@app.route('/connections')
@login_required
def connections():
    users = User.query.filter(User.id != current_user.id).all()
    connection_requests = ConnectionRequest.query.filter_by(
        recipient_id=current_user.id,
        status='pending'
    ).all()
    return render_template('connections.html', users=users, connection_requests=connection_requests)

@app.route('/send_connection_request/<int:user_id>', methods=['POST'])
@login_required
def send_connection_request(user_id):
    if ConnectionRequest.query.filter_by(
        sender_id=current_user.id,
        recipient_id=user_id,
        status='pending'
    ).first():
        flash('Connection request already sent')
        return redirect(url_for('connections'))
    
    request = ConnectionRequest(
        sender_id=current_user.id,
        recipient_id=user_id
    )
    db.session.add(request)
    db.session.commit()
    flash('Connection request sent')
    return redirect(url_for('connections'))

@app.route('/accept_connection_request/<int:request_id>', methods=['POST'])
@login_required
def accept_connection_request(request_id):
    connection_request = ConnectionRequest.query.get_or_404(request_id)
    if connection_request.recipient_id != current_user.id:
        flash('Unauthorized')
        return redirect(url_for('connections'))
    
    connection_request.status = 'accepted'
    
    connection1 = Connection(
        user_id=current_user.id,
        connected_user_id=connection_request.sender_id
    )
    connection2 = Connection(
        user_id=connection_request.sender_id,
        connected_user_id=current_user.id
    )
    
    db.session.add(connection1)
    db.session.add(connection2)
    db.session.commit()
    flash('Connection request accepted')
    return redirect(url_for('connections'))

@app.route('/reject_connection_request/<int:request_id>', methods=['POST'])
@login_required
def reject_connection_request(request_id):
    connection_request = ConnectionRequest.query.get_or_404(request_id)
    if connection_request.recipient_id != current_user.id:
        flash('Unauthorized')
        return redirect(url_for('connections'))
    
    connection_request.status = 'rejected'
    db.session.commit()
    flash('Connection request rejected')
    return redirect(url_for('connections'))

@app.route('/jobs')
@login_required
def jobs():
    search = request.args.get('search', '')
    category = request.args.get('category', '')
    location = request.args.get('location', '')
    
    query = Job.query
    
    if search:
        query = query.filter(
            (Job.title.ilike(f'%{search}%')) |
            (Job.company.ilike(f'%{search}%')) |
            (Job.description.ilike(f'%{search}%'))
        )
    
    if category:
        query = query.filter_by(category=category)
    
    if location:
        query = query.filter_by(location=location)
    
    jobs = query.order_by(Job.created_at.desc()).all()
    my_jobs = Job.query.filter_by(posted_by_id=current_user.id).all()
    
    category_counts = {
        'technology': Job.query.filter_by(category='technology').count(),
        'business': Job.query.filter_by(category='business').count(),
        'education': Job.query.filter_by(category='education').count(),
        'healthcare': Job.query.filter_by(category='healthcare').count()
    }
    
    return render_template('jobs.html', jobs=jobs, my_jobs=my_jobs, category_counts=category_counts)

@app.route('/post_job', methods=['POST'])
@login_required
def post_job():
    job = Job(
        title=request.form.get('title'),
        company=request.form.get('company'),
        location=request.form.get('location'),
        description=request.form.get('description'),
        requirements=request.form.get('requirements'),
        category=request.form.get('category'),
        type=request.form.get('type'),
        experience_level=request.form.get('experience_level'),
        contact_email=request.form.get('contact_email'),
        posted_by_id=current_user.id
    )
    db.session.add(job)
    db.session.commit()
    flash('Job posted successfully')
    return redirect(url_for('jobs'))

@app.route('/events')
@login_required
def events():
    search = request.args.get('search', '')
    event_type = request.args.get('type', '')
    status = request.args.get('status', '')
    
    query = Event.query
    
    if search:
        query = query.filter(
            (Event.title.ilike(f'%{search}%')) |
            (Event.description.ilike(f'%{search}%'))
        )
    
    if event_type:
        query = query.filter_by(type=event_type)
    
    if status:
        if status == 'upcoming':
            query = query.filter(Event.date >= datetime.now().date())
        elif status == 'ongoing':
            query = query.filter(Event.date == datetime.now().date())
        elif status == 'past':
            query = query.filter(Event.date < datetime.now().date())
    
    events = query.order_by(Event.date).all()
    
    my_events = {
        'created_count': Event.query.filter_by(creator_id=current_user.id).count(),
        'registered_count': EventRegistration.query.filter_by(user_id=current_user.id).count(),
        'past_count': EventRegistration.query.join(Event).filter(
            EventRegistration.user_id == current_user.id,
            Event.date < datetime.now().date()
        ).count()
    }
    
    type_counts = {
        'networking': Event.query.filter_by(type='networking').count(),
        'workshop': Event.query.filter_by(type='workshop').count(),
        'reunion': Event.query.filter_by(type='reunion').count(),
        'career': Event.query.filter_by(type='career').count()
    }
    
    return render_template('events.html', events=events, my_events=my_events, type_counts=type_counts)

@app.route('/create_event', methods=['POST'])
@login_required
def create_event():
    event = Event(
        title=request.form.get('title'),
        type=request.form.get('type'),
        description=request.form.get('description'),
        date=datetime.strptime(request.form.get('date'), '%Y-%m-%d').date(),
        time=datetime.strptime(request.form.get('time'), '%H:%M').time(),
        location=request.form.get('location'),
        max_participants=request.form.get('max_participants'),
        registration_deadline=datetime.strptime(request.form.get('registration_deadline'), '%Y-%m-%d').date(),
        creator_id=current_user.id
    )
    db.session.add(event)
    db.session.commit()
    flash('Event created successfully')
    return redirect(url_for('events'))

@app.route('/register_event/<int:event_id>', methods=['POST'])
@login_required
def register_event(event_id):
    event = Event.query.get_or_404(event_id)
    
    if EventRegistration.query.filter_by(event_id=event_id, user_id=current_user.id).first():
        flash('You are already registered for this event')
        return redirect(url_for('events'))
    
    if len(event.registrations) >= event.max_participants:
        flash('Event is full')
        return redirect(url_for('events'))
    
    registration = EventRegistration(event_id=event_id, user_id=current_user.id)
    db.session.add(registration)
    db.session.commit()
    flash('Successfully registered for the event')
    return redirect(url_for('events'))

@app.route('/messages')
@login_required
def messages():
    user_id = request.args.get('user_id', type=int)
    
    conversations = []
    for user in User.query.filter(User.id != current_user.id).all():
        last_message = Message.query.filter(
            ((Message.sender_id == current_user.id) & (Message.recipient_id == user.id)) |
            ((Message.sender_id == user.id) & (Message.recipient_id == current_user.id))
        ).order_by(Message.created_at.desc()).first()
        
        unread_count = Message.query.filter_by(
            recipient_id=current_user.id,
            sender_id=user.id,
            is_read=False
        ).count()
        
        conversations.append({
            'user': user,
            'last_message': last_message,
            'unread_count': unread_count
        })
    
    current_chat_user = User.query.get(user_id) if user_id else None
    messages = []
    if current_chat_user:
        messages = Message.query.filter(
            ((Message.sender_id == current_user.id) & (Message.recipient_id == current_chat_user.id)) |
            ((Message.sender_id == current_chat_user.id) & (Message.recipient_id == current_user.id))
        ).order_by(Message.created_at).all()
        
        # Mark messages as read
        Message.query.filter_by(
            recipient_id=current_user.id,
            sender_id=current_chat_user.id,
            is_read=False
        ).update({'is_read': True})
        db.session.commit()
    
    return render_template('messages.html', conversations=conversations, current_chat_user=current_chat_user, messages=messages)

@app.route('/send_message/<int:user_id>', methods=['POST'])
@login_required
def send_message(user_id):
    recipient = User.query.get_or_404(user_id)
    content = request.form.get('content')
    
    message = Message(
        content=content,
        sender_id=current_user.id,
        recipient_id=recipient.id
    )
    db.session.add(message)
    db.session.commit()
    
    return redirect(url_for('messages', user_id=user_id))

@app.route('/admin')
@login_required
def admin():
    if not current_user.is_admin:
        return redirect(url_for('index'))
    
    users = User.query.all()
    stats = {
        'total_users': User.query.count(),
        'active_users': User.query.filter_by(is_active=True).count(),
        'total_posts': Post.query.count(),
        'total_events': Event.query.count()
    }
    
    recent_activity = ActivityLog.query.order_by(ActivityLog.created_at.desc()).limit(10).all()
    settings = SystemSettings.query.first()
    
    return render_template('admin.html', users=users, stats=stats, recent_activity=recent_activity, settings=settings)

@app.route('/toggle_user_status/<int:user_id>', methods=['POST'])
@login_required
def toggle_user_status(user_id):
    if not current_user.is_admin:
        return redirect(url_for('index'))
    
    user = User.query.get_or_404(user_id)
    user.is_active = not user.is_active
    db.session.commit()
    
    activity = ActivityLog(
        user_id=current_user.id,
        description=f"{'Activated' if user.is_active else 'Deactivated'} user {user.username}"
    )
    db.session.add(activity)
    db.session.commit()
    
    flash(f"User {user.username} has been {'activated' if user.is_active else 'deactivated'}")
    return redirect(url_for('admin'))

@app.route('/edit_user/<int:user_id>', methods=['POST'])
@login_required
def edit_user(user_id):
    if not current_user.is_admin:
        return redirect(url_for('index'))
    
    user = User.query.get_or_404(user_id)
    user.username = request.form.get('username')
    user.email = request.form.get('email')
    user.is_admin = request.form.get('role') == 'admin'
    
    db.session.commit()
    
    activity = ActivityLog(
        user_id=current_user.id,
        description=f"Updated user {user.username}"
    )
    db.session.add(activity)
    db.session.commit()
    
    flash('User updated successfully')
    return redirect(url_for('admin'))

@app.route('/delete_user/<int:user_id>', methods=['POST'])
@login_required
def delete_user(user_id):
    if not current_user.is_admin:
        return redirect(url_for('index'))
    
    user = User.query.get_or_404(user_id)
    username = user.username
    db.session.delete(user)
    db.session.commit()
    
    activity = ActivityLog(
        user_id=current_user.id,
        description=f"Deleted user {username}"
    )
    db.session.add(activity)
    db.session.commit()
    
    flash(f"User {username} has been deleted")
    return redirect(url_for('admin'))

@app.route('/update_system_settings', methods=['POST'])
@login_required
def update_system_settings():
    if not current_user.is_admin:
        return redirect(url_for('index'))
    
    settings = SystemSettings.query.first()
    if not settings:
        settings = SystemSettings()
        db.session.add(settings)
    
    settings.site_name = request.form.get('site_name')
    settings.site_description = request.form.get('site_description')
    settings.maintenance_mode = request.form.get('maintenance_mode') == '1'
    
    db.session.commit()
    
    activity = ActivityLog(
        user_id=current_user.id,
        description="Updated system settings"
    )
    db.session.add(activity)
    db.session.commit()
    
    flash('System settings updated successfully')
    return redirect(url_for('admin'))

@app.route('/confirm_logout')
@login_required
def confirm_logout():
    return render_template('confirm_logout.html')

@app.route('/resetpass', methods=['GET', 'POST'])
def resetpass():
    if request.method == 'POST':
        email = request.form.get('email')
        user = User.query.filter_by(email=email).first()
        if user:
            # Here you would typically send a password reset email
            flash('Password reset instructions have been sent to your email.')
            return redirect(url_for('login'))
        flash('Email not found.')
    return render_template('resetpass.html')

@app.route('/create_post', methods=['POST'])
@login_required
def create_post():
    title = request.form.get('title')
    content = request.form.get('content')
    
    post = Post(
        title=title,
        content=content,
        user_id=current_user.id
    )
    db.session.add(post)
    db.session.commit()
    
    flash('Post created successfully')
    return redirect(url_for('index'))

@app.route('/settings')
@login_required
def settings():
    return render_template('settings.html')

@app.route('/update_settings', methods=['POST'])
@login_required
def update_settings():
    # Here you would typically update user settings in the database
    # For now, we'll just flash a success message
    flash('Settings updated successfully', 'success')
    return redirect(url_for('settings'))

if __name__ == '__main__':
    with app.app_context():
        # Drop all tables
        db.drop_all()
        # Create all tables
        db.create_all()
    app.run(debug=True) 