from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os
from werkzeug.utils import secure_filename

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
    alumni_info = db.relationship('Alumni', backref='user', uselist=False)

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
    user = db.relationship('User', backref='activities')

class Alumni(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    graduation_year = db.Column(db.Integer, nullable=False)
    major = db.Column(db.String(100), nullable=False)
    current_position = db.Column(db.String(200))
    company = db.Column(db.String(200))
    achievements = db.Column(db.Text)
    contributions = db.Column(db.Text)
    is_featured = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Scholarship(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    amount = db.Column(db.String(100))
    deadline = db.Column(db.Date)
    requirements = db.Column(db.Text)
    contact_email = db.Column(db.String(120))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Internship(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    company = db.Column(db.String(200), nullable=False)
    position = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    requirements = db.Column(db.Text)
    duration = db.Column(db.String(100))
    location = db.Column(db.String(200))
    contact_email = db.Column(db.String(120))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class MentorProgram(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    mentor_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    max_mentees = db.Column(db.Integer)
    start_date = db.Column(db.Date)
    end_date = db.Column(db.Date)
    status = db.Column(db.String(50), default='active')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    mentor = db.relationship('User', backref='mentor_programs')

class AlumniEvent(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    event_type = db.Column(db.String(50))  # reunion, workshop, networking, etc.
    date = db.Column(db.DateTime, nullable=False)
    location = db.Column(db.String(200))
    image = db.Column(db.String(200))
    organizer_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    participants = db.relationship('EventParticipant', backref='event', lazy=True)

class EventParticipant(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey('alumni_event.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    status = db.Column(db.String(20), default='registered')  # registered, attended, cancelled
    registration_date = db.Column(db.DateTime, default=datetime.utcnow)

class AlumniJob(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    company = db.Column(db.String(200), nullable=False)
    location = db.Column(db.String(200))
    job_type = db.Column(db.String(50))  # full-time, part-time, internship
    description = db.Column(db.Text)
    requirements = db.Column(db.Text)
    benefits = db.Column(db.Text)
    posted_by_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    deadline = db.Column(db.DateTime)
    status = db.Column(db.String(20), default='active')  # active, closed, draft

class AlumniProject(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    project_type = db.Column(db.String(50))  # research, community, business
    start_date = db.Column(db.DateTime)
    end_date = db.Column(db.DateTime)
    status = db.Column(db.String(20), default='active')
    leader_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    members = db.relationship('ProjectMember', backref='project', lazy=True)

class ProjectMember(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('alumni_project.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    role = db.Column(db.String(50))
    join_date = db.Column(db.DateTime, default=datetime.utcnow)

class AlumniGroup(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    group_type = db.Column(db.String(50))  # academic, professional, hobby
    created_by_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    members = db.relationship('GroupMember', backref='group', lazy=True)

class GroupMember(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(db.Integer, db.ForeignKey('alumni_group.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    role = db.Column(db.String(20), default='member')  # admin, moderator, member
    join_date = db.Column(db.DateTime, default=datetime.utcnow)

class AlumniMentorship(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    mentor_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    mentee_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    status = db.Column(db.String(20), default='pending')  # pending, active, completed
    start_date = db.Column(db.DateTime)
    end_date = db.Column(db.DateTime)
    goals = db.Column(db.Text)
    feedback = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Routes
@app.route('/')
def index():
    # Get recent posts for homepage
    recent_posts = [
        {
            'id': 1,
            'title': 'Fashion show IUH – Chung kết "Nét đẹp sinh viên SFA 2025"',
            'content': 'Với mục đích góp phần xây dựng nên bản sắc của sinh viên thời đại mới, tôn vinh vẻ đẹp hình thể và vẻ đẹp tri thức, Viện Tài chính - Kế toán, Đại học Công nghiệp TP. HCM (SFA-IUH) đã tổ chức cuộc thi "Nét đẹp sinh viên SFA 2025" vào ngày 31-3. Đây là một hoạt động ngoại khóa của Viện Tài chính - Kế toán, giúp tìm kiếm hình mẫu sinh viên phát triển toàn diện bản thân...',
            'image': 'fashion-show-iuh.jpg',
            'created_at': datetime.now(),
            'author': {'username': 'Admin IUH'},
            'url': 'https://iuh.edu.vn/vi/sinh-vien-fi23/fashion-show-iuh-chung-ket-net-dep-sinh-vien-sfa-2025-a2446.html'
        },
        {
            'id': 2,
            'title': 'Tuần cuối trước kỳ thi ĐGNL: Checklist quan trọng thí sinh không thể bỏ lỡ!',
            'content': 'Chuẩn bị cho kỳ thi Đánh giá năng lực sắp tới, các thí sinh cần lưu ý những điểm quan trọng...',
            'image': 'dgnl-checklist.jpg',
            'created_at': datetime.now(),
            'author': {'username': 'Admin IUH'}
        },
        {
            'id': 3,
            'title': 'IUH tăng cường trao đổi, hợp tác các doanh nghiệp trong kỷ nguyên AI',
            'content': 'Nhằm tăng cường mối quan hệ hợp tác giữa nhà trường và doanh nghiệp trong lĩnh vực AI...',
            'image': 'iuh-ai-cooperation.jpg',
            'created_at': datetime.now(),
            'author': {'username': 'Admin IUH'}
        }
    ]
    
    # Get upcoming events
    upcoming_events = Event.query.filter(Event.date >= datetime.utcnow()).order_by(Event.date).limit(3).all()
    
    # Get featured alumni
    featured_alumni = Alumni.query.filter_by(is_featured=True).limit(3).all()
    
    # Get statistics
    stats = {
        'total_alumni': Alumni.query.count(),
        'featured_alumni': Alumni.query.filter_by(is_featured=True).count(),
        'events_this_month': Event.query.filter(
            Event.date >= datetime.utcnow(),
            Event.date <= datetime.utcnow().replace(day=1).replace(month=datetime.utcnow().month + 1)
        ).count()
    }
    
    return render_template('index.html', 
                         posts=recent_posts,
                         upcoming_events=upcoming_events,
                         featured_alumni=featured_alumni,
                         stats=stats)

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
            
        # Check if trying to register as admin
        if username.lower() == 'admin' or email.lower() == 'admin@alumni.com':
            flash('Cannot register with admin username or email')
            return redirect(url_for('register'))
            
        user = User(
            username=username,
            email=email,
            password_hash=generate_password_hash(password),
            is_admin=False  # Ensure new users are not admins
        )
        db.session.add(user)
        db.session.commit()
        
        login_user(user)
        return redirect(url_for('index'))
    return render_template('register.html')

@app.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    # Log the logout activity before clearing session
    activity = ActivityLog(
        user_id=current_user.id,
        description=f"User logged out"
    )
    db.session.add(activity)
    db.session.commit()
    
    # Clear session data
    session.clear()
    
    # Perform logout
    logout_user()
    
    # Flash success message
    flash('You have been successfully logged out', 'success')
    
    # Redirect to home page
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
    new_role = request.form.get('role') == 'admin'
    
    # Check if trying to make another user admin when admin already exists
    if new_role and user.id != current_user.id:
        existing_admin = User.query.filter_by(is_admin=True).first()
        if existing_admin and existing_admin.id != user.id:
            flash('Cannot have multiple admin accounts')
            return redirect(url_for('admin'))
    
    user.username = request.form.get('username')
    user.email = request.form.get('email')
    user.is_admin = new_role
    
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
    
    # Prevent deleting the last admin account
    if user.is_admin:
        admin_count = User.query.filter_by(is_admin=True).count()
        if admin_count <= 1:
            flash('Cannot delete the last admin account')
            return redirect(url_for('admin'))
    
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

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')

@app.route('/contact', methods=['POST'])
def submit_contact():
    name = request.form.get('name')
    email = request.form.get('email')
    message = request.form.get('message')
    
    # Here you would typically send an email or save to database
    flash('Cảm ơn bạn đã liên hệ. Chúng tôi sẽ phản hồi sớm nhất có thể.')
    return redirect(url_for('contact'))

@app.route('/documents')
def documents():
    # This replaces the previous events route for the "Văn bản" menu item
    documents = {
        'regulations': [
            {'title': 'Quy chế tổ chức', 'file': 'org_regulations.pdf'},
            {'title': 'Quy định hoạt động', 'file': 'operations.pdf'},
        ],
        'forms': [
            {'title': 'Mẫu đăng ký cựu sinh viên', 'file': 'alumni_registration.pdf'},
            {'title': 'Mẫu cập nhật thông tin', 'file': 'info_update.pdf'},
        ],
        'reports': [
            {'title': 'Báo cáo hoạt động 2023', 'file': 'report_2023.pdf'},
            {'title': 'Kế hoạch 2024', 'file': 'plan_2024.pdf'},
        ]
    }
    return render_template('documents.html', documents=documents)

@app.route('/student-support')
def student_support():
    # This replaces the previous jobs route for the "Hỗ trợ sinh viên" menu item
    support_categories = {
        'scholarships': Scholarship.query.all(),
        'internships': Internship.query.all(),
        'mentoring': MentorProgram.query.all()
    }
    return render_template('student_support.html', categories=support_categories)

@app.route('/alumni')
def alumni():
    # Get featured and recent alumni
    featured_alumni = Alumni.query.filter_by(is_featured=True).order_by(Alumni.created_at.desc()).all()
    recent_alumni = Alumni.query.order_by(Alumni.created_at.desc()).limit(10).all()
    
    # Get statistics
    stats = {
        'total_alumni': Alumni.query.count(),
        'featured_alumni': Alumni.query.filter_by(is_featured=True).count(),
        'by_year': db.session.query(Alumni.graduation_year, db.func.count(Alumni.id)).group_by(Alumni.graduation_year).all(),
        'by_major': db.session.query(Alumni.major, db.func.count(Alumni.id)).group_by(Alumni.major).all()
    }
    
    # Get recent activities
    recent_activities = ActivityLog.query.order_by(ActivityLog.created_at.desc()).limit(5).all()
    
    return render_template('alumni.html', 
                         featured_alumni=featured_alumni,
                         recent_alumni=recent_alumni,
                         stats=stats,
                         recent_activities=recent_activities)

@app.route('/alumni/<int:alumni_id>')
def alumni_profile(alumni_id):
    alumni = Alumni.query.get_or_404(alumni_id)
    return render_template('alumni_profile.html', alumni=alumni)

@app.route('/update_alumni_info', methods=['POST'])
@login_required
def update_alumni_info():
    if not current_user.alumni_info:
        current_user.alumni_info = Alumni(user_id=current_user.id)
    
    current_user.alumni_info.graduation_year = request.form.get('graduation_year')
    current_user.alumni_info.major = request.form.get('major')
    current_user.alumni_info.current_position = request.form.get('current_position')
    current_user.alumni_info.company = request.form.get('company')
    current_user.alumni_info.achievements = request.form.get('achievements')
    current_user.alumni_info.contributions = request.form.get('contributions')
    
    db.session.commit()
    flash('Alumni information updated successfully')
    return redirect(url_for('alumni_profile', alumni_id=current_user.alumni_info.id))

@app.route('/admin/toggle_featured_alumni/<int:alumni_id>', methods=['POST'])
@login_required
def toggle_featured_alumni(alumni_id):
    if not current_user.is_admin:
        return redirect(url_for('index'))
    
    alumni = Alumni.query.get_or_404(alumni_id)
    alumni.is_featured = not alumni.is_featured
    db.session.commit()
    
    activity = ActivityLog(
        user_id=current_user.id,
        description=f"{'Featured' if alumni.is_featured else 'Unfeatured'} alumni {alumni.user.username}"
    )
    db.session.add(activity)
    db.session.commit()
    
    flash(f"Alumni {alumni.user.username} has been {'featured' if alumni.is_featured else 'unfeatured'}")
    return redirect(url_for('admin'))

@app.route('/api/alumni/stats')
def get_alumni_stats():
    stats = {
        'by_year': db.session.query(Alumni.graduation_year, db.func.count(Alumni.id)).group_by(Alumni.graduation_year).all(),
        'by_major': db.session.query(Alumni.major, db.func.count(Alumni.id)).group_by(Alumni.major).all()
    }
    return jsonify(stats)

@app.route('/post/<int:post_id>')
def post_detail(post_id):
    # Tìm bài viết theo ID trong danh sách tin tức
    posts = [
        {
            'id': 1,
            'title': 'Fashion show IUH – Chung kết "Nét đẹp sinh viên SFA 2025"',
            'content': '''Với mục đích góp phần xây dựng nên bản sắc của sinh viên thời đại mới, tôn vinh vẻ đẹp hình thể và vẻ đẹp tri thức, Viện Tài chính - Kế toán, Đại học Công nghiệp TP. HCM (SFA-IUH) đã tổ chức cuộc thi "Nét đẹp sinh viên SFA 2025" vào ngày 31-3.

Đây là một hoạt động ngoại khóa của Viện Tài chính - Kế toán, giúp tìm kiếm hình mẫu sinh viên phát triển toàn diện bản thân, vừa có chuyên môn tốt, có tính sáng tạo, vừa tự tin trong giao tiếp, toả sáng trước đám đông và lan tỏa được tinh thần phục vụ cộng đồng đầy ý nghĩa.

Kết quả chung cuộc:
- Danh hiệu Nam vương: Phùng Đình Quang Minh
- Danh hiệu Á vương: Đỗ Văn Hiền
- Danh hiệu Hoa khôi: Nguyễn Thị Như Quỳnh
- Danh hiệu Á khôi: Trần Thị Diệu Hương''',
            'image': 'fashion-show-iuh.jpg',
            'created_at': datetime.now(),
            'author': {'username': 'Admin IUH'},
            'url': 'https://iuh.edu.vn/vi/sinh-vien-fi23/fashion-show-iuh-chung-ket-net-dep-sinh-vien-sfa-2025-a2446.html'
        }
    ]
    
    post = next((p for p in posts if p['id'] == post_id), None)
    if post is None:
        flash('Không tìm thấy bài viết', 'error')
        return redirect(url_for('index'))
        
    return render_template('post_detail.html', post=post)

@app.route('/alumni/events')
@login_required
def alumni_events():
    events = AlumniEvent.query.order_by(AlumniEvent.date.desc()).all()
    return render_template('alumni/events.html', events=events)

@app.route('/alumni/events/create', methods=['GET', 'POST'])
@login_required
def create_alumni_event():
    if request.method == 'POST':
        event = AlumniEvent(
            title=request.form.get('title'),
            description=request.form.get('description'),
            event_type=request.form.get('event_type'),
            date=datetime.strptime(request.form.get('date'), '%Y-%m-%dT%H:%M'),
            location=request.form.get('location'),
            organizer_id=current_user.id
        )
        if 'image' in request.files:
            file = request.files['image']
            if file:
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], 'events', filename))
                event.image = f'events/{filename}'
        
        db.session.add(event)
        db.session.commit()
        flash('Sự kiện đã được tạo thành công')
        return redirect(url_for('alumni_events'))
    return render_template('alumni/create_event.html')

@app.route('/alumni/jobs')
@login_required
def alumni_jobs():
    jobs = AlumniJob.query.filter_by(status='active').order_by(AlumniJob.created_at.desc()).all()
    return render_template('alumni/jobs.html', jobs=jobs)

@app.route('/alumni/jobs/post', methods=['GET', 'POST'])
@login_required
def post_alumni_job():
    if request.method == 'POST':
        job = AlumniJob(
            title=request.form.get('title'),
            company=request.form.get('company'),
            location=request.form.get('location'),
            job_type=request.form.get('job_type'),
            description=request.form.get('description'),
            requirements=request.form.get('requirements'),
            benefits=request.form.get('benefits'),
            posted_by_id=current_user.id,
            deadline=datetime.strptime(request.form.get('deadline'), '%Y-%m-%d')
        )
        db.session.add(job)
        db.session.commit()
        flash('Tin tuyển dụng đã được đăng thành công')
        return redirect(url_for('alumni_jobs'))
    return render_template('alumni/post_job.html')

@app.route('/alumni/projects')
@login_required
def alumni_projects():
    projects = AlumniProject.query.filter_by(status='active').order_by(AlumniProject.created_at.desc()).all()
    return render_template('alumni/projects.html', projects=projects)

@app.route('/alumni/projects/create', methods=['GET', 'POST'])
@login_required
def create_alumni_project():
    if request.method == 'POST':
        project = AlumniProject(
            title=request.form.get('title'),
            description=request.form.get('description'),
            project_type=request.form.get('project_type'),
            start_date=datetime.strptime(request.form.get('start_date'), '%Y-%m-%d'),
            end_date=datetime.strptime(request.form.get('end_date'), '%Y-%m-%d'),
            leader_id=current_user.id
        )
        db.session.add(project)
        db.session.commit()
        flash('Dự án đã được tạo thành công')
        return redirect(url_for('alumni_projects'))
    return render_template('alumni/create_project.html')

@app.route('/alumni/groups')
@login_required
def alumni_groups():
    groups = AlumniGroup.query.order_by(AlumniGroup.created_at.desc()).all()
    return render_template('alumni/groups.html', groups=groups)

@app.route('/alumni/groups/create', methods=['GET', 'POST'])
@login_required
def create_alumni_group():
    if request.method == 'POST':
        group = AlumniGroup(
            name=request.form.get('name'),
            description=request.form.get('description'),
            group_type=request.form.get('group_type'),
            created_by_id=current_user.id
        )
        db.session.add(group)
        db.session.commit()
        
        # Add creator as group admin
        member = GroupMember(
            group_id=group.id,
            user_id=current_user.id,
            role='admin'
        )
        db.session.add(member)
        db.session.commit()
        
        flash('Nhóm đã được tạo thành công')
        return redirect(url_for('alumni_groups'))
    return render_template('alumni/create_group.html')

@app.route('/alumni/mentorship')
@login_required
def mentorship():
    mentorships = AlumniMentorship.query.filter(
        (AlumniMentorship.mentor_id == current_user.id) |
        (AlumniMentorship.mentee_id == current_user.id)
    ).all()
    return render_template('alumni/mentorship.html', mentorships=mentorships)

@app.route('/alumni/mentorship/request', methods=['GET', 'POST'])
@login_required
def request_mentorship():
    if request.method == 'POST':
        mentorship = AlumniMentorship(
            mentor_id=request.form.get('mentor_id'),
            mentee_id=current_user.id,
            goals=request.form.get('goals')
        )
        db.session.add(mentorship)
        db.session.commit()
        flash('Yêu cầu mentorship đã được gửi')
        return redirect(url_for('mentorship'))
    mentors = User.query.join(Alumni).filter(Alumni.is_featured == True).all()
    return render_template('alumni/request_mentorship.html', mentors=mentors)

if __name__ == '__main__':
    with app.app_context():
        # Drop all tables
        db.drop_all()
        # Create all tables
        db.create_all()
        
        # Create default admin account if it doesn't exist
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            admin = User(
                username='admin',
                email='admin@alumni.com',
                password_hash=generate_password_hash('admin123'),
                is_admin=True,
                is_active=True
            )
            db.session.add(admin)
            db.session.commit()
            print('Default admin account created successfully!')
            print('Username: admin')
            print('Password: admin123')
            
    app.run(debug=True) 