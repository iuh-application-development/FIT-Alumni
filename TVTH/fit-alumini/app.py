from flask import Flask, render_template, request, redirect, url_for, flash, session, send_from_directory, jsonify, abort, Response
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta, UTC
import os
import logging
from werkzeug.utils import secure_filename
from urllib.parse import urlencode
from sqlalchemy import or_, and_, func
from forms import RegistrationForm, LoginForm, JobForm
from flask_migrate import Migrate
from flask_bcrypt import Bcrypt
from flask_mail import Mail, Message
import json
from sqlalchemy import inspect
from sqlalchemy import text
import csv
import time
from models import (
    db, User, Profile, Post, Comment, Job, JobApplication, post_likes,
    Education, Experience, Skill
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants for job filters
LOCATIONS = ['Hà Nội', 'Hồ Chí Minh', 'Đà Nẵng', 'Cần Thơ', 'Khác']
JOB_TYPES = ['PHP', 'JavaScript', 'Python', 'Java', 'C#', '.NET', 'React', 'Angular', 'Vue.js']
LEVELS = ['Intern/Fresher', 'Junior', 'Middle', 'Senior', 'Team Lead', 'Manager']
WORK_TYPES = ['Full-time', 'Part-time', 'Remote', 'Hybrid']

# Get the absolute path of the current directory
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATABASE_PATH = os.path.join(BASE_DIR, 'alumni.db')

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DATABASE_PATH}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Ensure upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'resumes'), exist_ok=True)

# Ensure database directory exists
os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)

# Initialize extensions
db.init_app(app)
migrate = Migrate(app, db)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
bcrypt = Bcrypt(app)
mail = Mail(app)

def init_db():
    """Initialize the database if it doesn't exist"""
    try:
        if not os.path.exists(DATABASE_PATH):
            logger.info("Database does not exist. Please run migrations to create it.")
        else:
            logger.info("Database already exists")
    except Exception as e:
        logger.error(f"Error checking database: {str(e)}")
        raise

# Initialize database
init_db()

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

# Helper functions
def allowed_file(filename, allowed_extensions=None):
    if allowed_extensions is None:
        allowed_extensions = {
            'png', 'jpg', 'jpeg', 'gif',  # images
            'pdf', 'doc', 'docx'  # documents
        }
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions

# Routes
@app.route('/')
def index():
    # Lấy 6 công việc mới nhất
    latest_jobs = Job.query.order_by(Job.created_at.desc()).limit(6).all()
    return render_template('index.html', latest_jobs=latest_jobs)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()
        
        if user and check_password_hash(user.password, password):
            login_user(user)
            next_page = request.args.get('next')
            return redirect(next_page or url_for('index'))
        flash('Email hoặc mật khẩu không đúng', 'danger')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        role = request.form.get('role', 'user')
        
        if password != confirm_password:
            flash('Mật khẩu không khớp', 'danger')
            return redirect(url_for('register'))
            
        if User.query.filter_by(email=email).first():
            flash('Email đã tồn tại', 'danger')
            return redirect(url_for('register'))
            
        user = User(
            name=name,
            email=email,
            password=generate_password_hash(password),
            role=role
        )
        db.session.add(user)
        db.session.commit()
        
        flash('Đăng ký thành công', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.args.get('user_id') and current_user.role == 'admin':
        user = User.query.get_or_404(request.args.get('user_id'))
        return redirect(url_for('admin_view_user', user_id=user.id))
    
    # Get user profile with all related data
    user_profile = Profile.query.filter_by(user_id=current_user.id).first()
    
    # Get education, experience and skills
    education = Education.query.filter_by(user_id=current_user.id).order_by(Education.start_date.desc()).all()
    experience = Experience.query.filter_by(user_id=current_user.id).order_by(Experience.start_date.desc()).all()
    skills = Skill.query.filter_by(user_id=current_user.id).all()
    
    # Calculate profile completion
    profile_completion = 0
    if user_profile:
        completion_fields = [
            user_profile.avatar,
            user_profile.phone,
            user_profile.address,
            user_profile.bio,
            user_profile.company or user_profile.position,
            education,
            experience,
            skills
        ]
        completed_fields = sum(1 for field in completion_fields if field)
        profile_completion = (completed_fields / len(completion_fields)) * 100

    return render_template('profile.html',
                         profile=user_profile,
                         education=education,
                         experience=experience,
                         skills=skills,
                         profile_completion=round(profile_completion))

@app.route('/profile/edit', methods=['GET', 'POST'])
@login_required
def edit_profile():
    profile = current_user.profile or Profile(user_id=current_user.id)
    education = Education.query.filter_by(user_id=current_user.id).all()
    experience = Experience.query.filter_by(user_id=current_user.id).all()
    skills = Skill.query.filter_by(user_id=current_user.id).all()

    if request.method == 'POST':
        try:
            # Update profile
            profile.bio = request.form.get('bio')
            profile.phone = request.form.get('phone')
            profile.address = request.form.get('address')
            profile.company = request.form.get('company')
            profile.position = request.form.get('position')
            profile.graduation_year = request.form.get('graduation_year')

            if not current_user.profile:
                db.session.add(profile)

            # Handle education entries
            schools = request.form.getlist('school[]')
            majors = request.form.getlist('major[]')
            edu_start_dates = request.form.getlist('edu_start_date[]')
            edu_end_dates = request.form.getlist('edu_end_date[]')

            # Delete all existing education entries
            Education.query.filter_by(user_id=current_user.id).delete()
            
            # Create new education entries
            for i in range(len(schools)):
                if schools[i].strip():  # Only add if school is not empty
                    education_entry = Education(
                        user_id=current_user.id,
                        school=schools[i],
                        major=majors[i] if i < len(majors) else '',
                        start_date=edu_start_dates[i] if i < len(edu_start_dates) else None,
                        end_date=edu_end_dates[i] if i < len(edu_end_dates) else None
                    )
                    db.session.add(education_entry)

            # Handle experience entries
            positions = request.form.getlist('position[]')
            companies = request.form.getlist('company[]')
            exp_start_dates = request.form.getlist('exp_start_date[]')
            exp_end_dates = request.form.getlist('exp_end_date[]')
            descriptions = request.form.getlist('description[]')

            # Delete all existing experience entries
            Experience.query.filter_by(user_id=current_user.id).delete()
            
            # Create new experience entries
            for i in range(len(positions)):
                if positions[i].strip():  # Only add if position is not empty
                    experience_entry = Experience(
                        user_id=current_user.id,
                        position=positions[i],
                        company=companies[i] if i < len(companies) else '',
                        start_date=exp_start_dates[i] if i < len(exp_start_dates) else None,
                        end_date=exp_end_dates[i] if i < len(exp_end_dates) else None,
                        description=descriptions[i] if i < len(descriptions) else ''
                    )
                    db.session.add(experience_entry)

            # Handle skills
            skills_input = request.form.get('skills', '').split(',')
            skills_list = [skill.strip() for skill in skills_input if skill.strip()]
            
            # Delete all existing skills
            Skill.query.filter_by(user_id=current_user.id).delete()
            
            # Add new skills
            for skill_name in skills_list:
                skill = Skill(user_id=current_user.id, name=skill_name)
                db.session.add(skill)

            db.session.commit()
            flash('Cập nhật thông tin thành công!', 'success')
            return redirect(url_for('profile'))

        except Exception as e:
            db.session.rollback()
            app.logger.error(f'Error in edit_profile: {str(e)}', exc_info=True)
            flash('Có lỗi xảy ra khi cập nhật thông tin!', 'error')
            return redirect(url_for('edit_profile'))

    # GET request: populate form with existing data
    return render_template('edit_profile.html', 
                         profile=profile,
                         education=education,
                         experience=experience,
                         skills=skills)

@app.route('/update_avatar', methods=['POST'])
@login_required
def update_avatar():
    if 'avatar' not in request.files:
        flash('Không có file được chọn', 'danger')
        return redirect(url_for('profile'))
    
    file = request.files['avatar']
    if file.filename == '':
        flash('Không có file được chọn', 'danger')
        return redirect(url_for('profile'))
    
    if file and allowed_file(file.filename):
        filename = secure_filename(f"{current_user.id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{file.filename}")
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        
        # Remove old avatar if exists
        if current_user.profile and current_user.profile.avatar:
            old_avatar = os.path.join(app.config['UPLOAD_FOLDER'], current_user.profile.avatar)
            if os.path.exists(old_avatar):
                os.remove(old_avatar)
        
        # Update profile
        profile = current_user.profile or Profile(user_id=current_user.id)
        profile.avatar = filename
        
        if not current_user.profile:
            db.session.add(profile)
        
        db.session.commit()
        flash('Cập nhật ảnh đại diện thành công', 'success')
    else:
        flash('File không hợp lệ. Chỉ chấp nhận file ảnh (png, jpg, jpeg, gif)', 'danger')
    
    return redirect(url_for('profile'))

@app.route('/alumni/jobs')
@login_required
def alumni_jobs():
    if current_user.role != 'alumni':
        flash('Bạn không có quyền truy cập trang này.', 'danger')
        return redirect(url_for('index'))
    
    # Lấy danh sách công việc của alumni hiện tại
    jobs = Job.query.filter_by(alumni_id=current_user.id).order_by(Job.created_at.desc()).all()
    
    # Thống kê
    total_jobs = len(jobs)
    active_jobs = sum(1 for job in jobs if job.is_confirmed and (not job.deadline or job.deadline.replace(tzinfo=None) > datetime.now().replace(tzinfo=None)))
    pending_jobs = sum(1 for job in jobs if not job.is_confirmed)
    closed_jobs = sum(1 for job in jobs if job.deadline and job.deadline.replace(tzinfo=None) <= datetime.now().replace(tzinfo=None))
    
    return render_template('alumni/jobs.html', jobs=jobs, total_jobs=total_jobs, 
                         active_jobs=active_jobs, pending_jobs=pending_jobs, 
                         closed_jobs=closed_jobs)

@app.route('/alumni/add_job', methods=['GET', 'POST'])
@login_required
def alumni_add_job():
    if current_user.role != 'alumni':
        flash('Bạn không có quyền truy cập', 'danger')
        return redirect(url_for('index'))

    form = JobForm()
    
    if request.method == 'POST':
        try:
            # Validate required fields
            required_fields = ['title', 'description', 'company_name', 'location', 'job_type']
            for field in required_fields:
                if not request.form.get(field):
                    flash(f'Vui lòng điền {field}', 'danger')
                    return render_template('alumni/add_job.html', form=form)

            # Xử lý mức lương
            salary_display = None
            if request.form.get('salary_negotiable'):
                salary_display = 'Thương lượng'
            else:
                salary_min = request.form.get('salary_min', '').replace(',', '')
                salary_max = request.form.get('salary_max', '').replace(',', '')
                currency = request.form.get('salary_currency', 'VND')
                
                if salary_min and salary_max:
                    if not salary_min.isdigit() or not salary_max.isdigit():
                        flash('Mức lương phải là số', 'danger')
                        return render_template('alumni/add_job.html', form=form)
                    if int(salary_min) > int(salary_max):
                        flash('Mức lương tối thiểu không được lớn hơn mức lương tối đa', 'danger')
                        return render_template('alumni/add_job.html', form=form)
                    salary_display = f"{int(salary_min):,} - {int(salary_max):,} {currency}"
                elif salary_min:
                    if not salary_min.isdigit():
                        flash('Mức lương phải là số', 'danger')
                        return render_template('alumni/add_job.html', form=form)
                    salary_display = f"Từ {int(salary_min):,} {currency}"
                elif salary_max:
                    if not salary_max.isdigit():
                        flash('Mức lương phải là số', 'danger')
                        return render_template('alumni/add_job.html', form=form)
                    salary_display = f"Đến {int(salary_max):,} {currency}"
            
            # Xử lý deadline
            deadline = None
            if request.form.get('deadline'):
                try:
                    deadline = datetime.strptime(request.form.get('deadline'), '%Y-%m-%d')
                    if deadline.date() < datetime.now().date():
                        flash('Deadline không được nhỏ hơn ngày hiện tại', 'danger')
                        return render_template('alumni/add_job.html', form=form)
                    deadline = deadline.replace(tzinfo=UTC)
                except ValueError:
                    flash('Định dạng ngày không hợp lệ', 'danger')
                    return render_template('alumni/add_job.html', form=form)
            
            # Create new job
            job = Job(
                title=request.form.get('title'),
                description=request.form.get('description'),
                requirements=request.form.get('requirements'),
                benefits=request.form.get('benefits'),
                salary_display=salary_display,
                location=request.form.get('location'),
                job_type=request.form.get('job_type'),
                experience=request.form.get('experience'),
                headcount=request.form.get('positions', type=int, default=1),
                deadline=deadline,
                company_name=request.form.get('company_name'),
                contact_name=request.form.get('contact_name'),
                contact_email=request.form.get('contact_email'),
                contact_phone=request.form.get('contact_phone'),
                alumni_id=current_user.id
            )
            
            # Handle company logo upload
            if 'company_logo' in request.files:
                file = request.files['company_logo']
                if file and file.filename:
                    # Check file size (max 5MB)
                    if len(file.read()) > 5 * 1024 * 1024:
                        flash('Logo công ty không được vượt quá 5MB', 'danger')
                        return render_template('alumni/add_job.html', form=form)
                    file.seek(0)  # Reset file pointer after reading
                    
                    if allowed_file(file.filename, {'png', 'jpg', 'jpeg'}):
                        filename = secure_filename(f"company_{current_user.id}_{int(time.time())}_{file.filename}")
                        file_path = os.path.join(app.config['UPLOAD_FOLDER'], 'company_logos', filename)
                        os.makedirs(os.path.dirname(file_path), exist_ok=True)
                        file.save(file_path)
                        job.company_logo = filename
                    else:
                        flash('Logo công ty không hợp lệ. Chỉ chấp nhận file PNG, JPG', 'danger')
                        return render_template('alumni/add_job.html', form=form)
            
            db.session.add(job)
            db.session.commit()
            
            flash('Đăng tin tuyển dụng thành công! Tin của bạn đang chờ duyệt.', 'success')
            return redirect(url_for('alumni_jobs'))
            
        except Exception as e:
            db.session.rollback()
            app.logger.error(f"Error creating job: {str(e)}")
            flash('Có lỗi xảy ra khi đăng tin tuyển dụng. Vui lòng thử lại sau.', 'danger')
            return render_template('alumni/add_job.html', form=form)
    
    return render_template('alumni/add_job.html', form=form)

@app.route('/alumni/delete_job/<int:job_id>', methods=['POST'])
@login_required
def delete_job(job_id):
    job = Job.query.get_or_404(job_id)
    if job.alumni_id != current_user.id and current_user.role != 'admin':
        flash('Bạn không có quyền xóa tin này', 'danger')
        return redirect(url_for('index'))
    
    db.session.delete(job)
    db.session.commit()
    flash('Đã xóa tin tuyển dụng', 'success')
    return redirect(url_for('alumni_jobs'))

@app.route('/apply/<int:job_id>', methods=['POST'])
@login_required
def apply_job(job_id):
    job = Job.query.get_or_404(job_id)
    
    # Check if user has already applied
    existing_application = Application.query.filter_by(
        job_id=job_id, 
        user_id=current_user.id
    ).first()
    
    if existing_application:
        flash('Bạn đã ứng tuyển công việc này', 'warning')
        return redirect(url_for('job_detail', job_id=job_id))
    
    # Handle resume upload
    if 'resume' not in request.files:
        flash('Vui lòng tải lên CV/Resume', 'danger')
        return redirect(url_for('job_detail', job_id=job_id))
    
    resume = request.files['resume']
    if resume.filename == '':
        flash('Vui lòng chọn file CV/Resume', 'danger')
        return redirect(url_for('job_detail', job_id=job_id))
    
    if resume and allowed_file(resume.filename, {'pdf', 'doc', 'docx'}):
        # Save resume file
        filename = secure_filename(f"{current_user.id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{resume.filename}")
        resume_path = os.path.join(app.config['UPLOAD_FOLDER'], 'resumes', filename)
        os.makedirs(os.path.dirname(resume_path), exist_ok=True)
        resume.save(resume_path)
        
        # Create application
        application = Application(
            job_id=job_id,
            user_id=current_user.id,
            cover_letter=request.form.get('cover_letter'),
            resume_path=filename,
            status='pending'
        )
        
        db.session.add(application)
        db.session.commit()
        flash('Ứng tuyển thành công', 'success')
    else:
        flash('File không hợp lệ. Chỉ chấp nhận file PDF, DOC hoặc DOCX', 'danger')

    return redirect(url_for('job_detail', job_id=job_id))

@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    if current_user.role != 'admin':
        flash('Bạn không có quyền truy cập', 'danger')
        return redirect(url_for('index'))

    total_users = User.query.count()
    total_jobs = Job.query.count()
    pending_jobs_count = Job.query.filter_by(is_confirmed=False).count()
    total_applications = Application.query.count()
    recent_jobs = Job.query.order_by(Job.created_at.desc()).limit(5).all()
    recent_users = User.query.order_by(User.created_at.desc()).limit(5).all()

    return render_template('admin/dashboard.html',
                         total_users=total_users,
                         total_jobs=total_jobs,
                         pending_jobs_count=pending_jobs_count,
                         total_applications=total_applications,
                         recent_jobs=recent_jobs,
                         recent_users=recent_users)

@app.route('/admin/jobs')
@login_required
def admin_jobs():
    """Display all jobs for admin management."""
    if current_user.role != 'admin':
        flash('Bạn không có quyền truy cập', 'danger')
        return redirect(url_for('index'))
    jobs = Job.query.order_by(Job.created_at.desc()).all()
    return render_template('admin/jobs.html', jobs=jobs)

@app.route('/admin/jobs/pending')
@login_required
def admin_pending_jobs():
    """Display pending jobs for confirmation."""
    if current_user.role != 'admin':
        flash('Bạn không có quyền truy cập', 'danger')
        return redirect(url_for('index'))
    jobs = Job.query.filter_by(is_confirmed=False).order_by(Job.created_at.desc()).all()
    # Use a different template to avoid conflicts, or add logic to jobs.html
    return render_template('admin/pending_jobs.html', jobs=jobs)

@app.route('/admin/jobs/confirm/<int:job_id>', methods=['POST'])
@login_required
def admin_confirm_job(job_id):
    if current_user.role != 'admin':
        flash('Bạn không có quyền truy cập', 'danger')
        return redirect(request.referrer or url_for('admin_dashboard'))
    job = Job.query.get_or_404(job_id)
    job.is_confirmed = True
    db.session.commit()
    flash(f'Đã duyệt công việc "{job.title}"', 'success')
    return redirect(url_for('admin_pending_jobs'))
    
@app.route('/admin/jobs/delete/<int:job_id>', methods=['POST'])
@login_required
def admin_delete_job(job_id):
    if current_user.role != 'admin':
        flash('Bạn không có quyền truy cập', 'danger')
        return redirect(request.referrer or url_for('admin_dashboard'))

    job = Job.query.get_or_404(job_id)
    job_title = job.title # Get title before deleting
    db.session.delete(job)
    db.session.commit()
    flash(f'Đã xóa tin tuyển dụng "{job_title}"', 'success')
    # Redirect back to the page the admin came from (e.g., all jobs or pending jobs)
    return redirect(request.referrer or url_for('admin_jobs'))
    
@app.route('/admin/users')
@login_required
def admin_users():
    if current_user.role != 'admin':
        flash('Bạn không có quyền truy cập', 'danger')
        return redirect(url_for('index'))
    
    # Get filter parameters
    role = request.args.get('role')
    search = request.args.get('search', '')
    
    # Build query
    query = User.query
    
    # Apply role filter
    if role:
        query = query.filter(User.role == role)
    
    # Apply search filter
    if search:
        search_term = f'%{search}%'
        query = query.filter(
            or_(
                User.name.ilike(search_term),
                User.email.ilike(search_term)
            )
        )
    
    # Get users
    users = query.order_by(User.created_at.desc()).all()
    
    return render_template('admin/users.html', users=users)

@app.route('/admin/delete_user/<int:user_id>', methods=['POST'])
@login_required
def delete_user(user_id):
    if current_user.role != 'admin':
        flash('Bạn không có quyền truy cập', 'danger')
        return redirect(url_for('index'))
    
    user = User.query.get_or_404(user_id)
    if user.role == 'admin':
        flash('Không thể xóa tài khoản quản trị viên', 'danger')
        return redirect(url_for('admin_users'))
    
    db.session.delete(user)
    db.session.commit()
    flash('Đã xóa người dùng', 'success')
    return redirect(url_for('admin_users'))

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))
    
@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/job/<int:job_id>')
def job_detail(job_id):
    job = Job.query.get_or_404(job_id)
    return render_template('job_detail.html', job=job)

@app.route('/search')
def search():
    return redirect(url_for('jobs'))

@app.route('/jobs')
def jobs():
    # Get search parameters
    keyword = request.args.get('keyword', '').strip()
    location = request.args.get('location', '')
    level = request.args.get('level', '')
    job_type = request.args.get('job_type', '')
    work_type = request.args.get('work_type', '')
    sort = request.args.get('sort', 'newest')
    
    # Base query
    query = Job.query.filter_by(is_confirmed=True)
    
    # Apply filters
    if keyword:
        search_term = f"%{keyword}%"
        query = query.filter(or_(
            Job.title.ilike(search_term),
            Job.description.ilike(search_term),
            Job.requirements.ilike(search_term)
        ))
    
    if location:
        query = query.filter(Job.location == location)
    
    if level:
        query = query.filter(Job.level == level)
    
    if job_type:
        query = query.filter(Job.job_type == job_type)
    
    if work_type:
        query = query.filter(Job.work_type == work_type)
    
    # Apply sorting
    if sort == 'newest':
        query = query.order_by(Job.created_at.desc())
    
    # Execute query
    jobs = query.all()
    
    return render_template('jobs.html',
                         jobs=jobs,
                         locations=LOCATIONS,
                         job_types=JOB_TYPES,
                         levels=LEVELS,
                         work_types=WORK_TYPES,
                         sort=sort)

@app.route('/alumni/edit_job/<int:job_id>', methods=['GET', 'POST'])
@login_required
def edit_job(job_id):
    if current_user.role != 'alumni':
        flash('Bạn không có quyền truy cập', 'danger')
        return redirect(url_for('index'))
    
    job = Job.query.get_or_404(job_id)
    if job.alumni_id != current_user.id:
        flash('Bạn không có quyền chỉnh sửa tin này', 'danger')
        return redirect(url_for('alumni_jobs'))
    
    form = JobForm(obj=job)

    if form.validate_on_submit():
        try:
            # Xử lý mức lương
            salary_display = None
            if form.salary_negotiable.data:
                salary_display = 'Thương lượng'
            else:
                salary_min = form.salary_min.data.replace(',', '') if form.salary_min.data else ''
                salary_max = form.salary_max.data.replace(',', '') if form.salary_max.data else ''
                currency = form.salary_currency.data
                
                if salary_min and salary_max:
                    salary_display = f"{int(salary_min):,} - {int(salary_max):,} {currency}"
                elif salary_min:
                    salary_display = f"Từ {int(salary_min):,} {currency}"
                elif salary_max:
                    salary_display = f"Đến {int(salary_max):,} {currency}"
            
            # Cập nhật thông tin job
            form.populate_obj(job)
            job.salary_display = salary_display
            
            # Xử lý deadline
            if form.deadline.data:
                job.deadline = form.deadline.data.replace(tzinfo=UTC)
            
            # Xử lý logo công ty
            if form.company_logo.data:
                file = form.company_logo.data
                if file and file.filename and allowed_file(file.filename, {'png', 'jpg', 'jpeg'}):
                    # Xóa logo cũ nếu có
                    if job.company_logo:
                        old_logo_path = os.path.join(app.config['UPLOAD_FOLDER'], 'company_logos', job.company_logo)
                        if os.path.exists(old_logo_path):
                            os.remove(old_logo_path)
                    
                    filename = secure_filename(f"company_{current_user.id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{file.filename}")
                    file_path = os.path.join(app.config['UPLOAD_FOLDER'], 'company_logos', filename)
                    os.makedirs(os.path.dirname(file_path), exist_ok=True)
                    file.save(file_path)
                    job.company_logo = filename
                elif file and file.filename:
                    flash('Logo công ty không hợp lệ. Chỉ chấp nhận file PNG, JPG', 'danger')
                    return render_template('alumni/edit_job.html', form=form, job=job)
            
            db.session.commit()
            flash('Cập nhật tin tuyển dụng thành công', 'success')
            return redirect(url_for('alumni_jobs'))
            
        except Exception as e:
            db.session.rollback()
            app.logger.error(f"Error updating job {job_id}: {str(e)}")
            flash(f'Đã xảy ra lỗi khi cập nhật tin: {str(e)}', 'danger')
            return render_template('alumni/edit_job.html', form=form, job=job)
    
    return render_template('alumni/edit_job.html', form=form, job=job)

@app.route('/student/dashboard')
@login_required
def student_dashboard():
    if current_user.role != 'user':
        flash('Bạn không có quyền truy cập', 'danger')
        return redirect(url_for('index'))
    
    # Get statistics
    total_jobs = Job.query.filter_by(is_confirmed=True).count()
    total_companies = db.session.query(Profile.company).filter(Profile.company.isnot(None)).distinct().count()
    total_alumni = User.query.filter_by(role='alumni').count()
    success_rate = 85  # Example value, you can calculate this based on your metrics
    
    # Get featured jobs
    featured_jobs = Job.query.filter_by(is_confirmed=True).order_by(Job.created_at.desc()).limit(6).all()
    
    # Get recent applications
    recent_applications = Application.query.filter_by(user_id=current_user.id)\
        .order_by(Application.created_at.desc())\
        .limit(5).all()
    
    # Calculate profile completion
    profile_completion = 0
    if current_user.profile:
        fields = ['avatar', 'bio', 'phone', 'address', 'graduation_year']
        completed_fields = sum(1 for field in fields if getattr(current_user.profile, field))
        profile_completion = (completed_fields / len(fields)) * 100
    
    return render_template('student/dashboard.html',
                         total_jobs=total_jobs,
                         total_companies=total_companies,
                         total_alumni=total_alumni,
                         success_rate=success_rate,
                         featured_jobs=featured_jobs,
                         recent_applications=recent_applications,
                         profile_completion=round(profile_completion),
                         locations=LOCATIONS,
                         job_types=JOB_TYPES)

@app.route('/profile/education/add', methods=['POST'])
@login_required
def add_education():
    data = request.get_json()
    education = Education(
        user_id=current_user.id,
        school=data.get('school'),
        major=data.get('major'),
        start_date=data.get('start_date'),
        end_date=data.get('end_date')
    )
    db.session.add(education)
    db.session.commit()
    return jsonify({'success': True, 'id': education.id})
    
@app.route('/profile/education/<int:id>', methods=['DELETE'])
@login_required
def delete_education(id):
    education = Education.query.get_or_404(id)
    if education.user_id != current_user.id:
        abort(403)
    db.session.delete(education)
    db.session.commit()
    return jsonify({'success': True})

@app.route('/profile/experience/add', methods=['POST'])
@login_required
def add_experience():
    data = request.get_json()
    experience = Experience(
        user_id=current_user.id,
        position=data.get('position'),
        company=data.get('company'),
        start_date=data.get('start_date'),
        end_date=data.get('end_date'),
        description=data.get('description')
    )
    db.session.add(experience)
    db.session.commit()
    return jsonify({'success': True, 'id': experience.id})
    
@app.route('/profile/experience/<int:id>', methods=['DELETE'])
@login_required
def delete_experience(id):
    experience = Experience.query.get_or_404(id)
    if experience.user_id != current_user.id:
        abort(403)
    db.session.delete(experience)
    db.session.commit()
    return jsonify({'success': True})

@app.route('/profile/skill/add', methods=['POST'])
@login_required
def add_skill():
    data = request.get_json()
    skill = Skill(
        user_id=current_user.id,
        name=data.get('name')
    )
    db.session.add(skill)
    db.session.commit()
    return jsonify({'success': True, 'id': skill.id})

@app.route('/profile/skill/<int:id>', methods=['DELETE'])
@login_required
def delete_skill(id):
    skill = Skill.query.get_or_404(id)
    if skill.user_id != current_user.id:
        abort(403)
    db.session.delete(skill)
    db.session.commit()
    return jsonify({'success': True})

@app.route('/admin/users/<int:user_id>')
@login_required
def admin_view_user(user_id):
    if current_user.role != 'admin':
        flash('Bạn không có quyền truy cập trang này', 'danger')
        return redirect(url_for('index'))
    
    user = User.query.get_or_404(user_id)
    education = Education.query.filter_by(user_id=user.id).order_by(Education.start_date.desc()).all()
    experience = Experience.query.filter_by(user_id=user.id).order_by(Experience.start_date.desc()).all()
    skills = Skill.query.filter_by(user_id=user.id).all()
    
    return render_template('admin/profile.html',
                         user=user,
                         education=education,
                         experience=experience,
                         skills=skills)

@app.route('/admin/analytics')
@login_required
def admin_analytics():
    if current_user.role != 'admin':
        flash('Bạn không có quyền truy cập trang này', 'danger')
        return redirect(url_for('index'))

    # Calculate basic statistics
    total_users = User.query.count()
    total_jobs = Job.query.count()
    active_jobs = Job.query.filter_by(is_confirmed=True).count()
    total_applications = Application.query.count()

    # Calculate user distribution
    student_count = User.query.filter_by(role='user').count()
    alumni_count = User.query.filter_by(role='alumni').count()
    admin_count = User.query.filter_by(role='admin').count()

    # Calculate monthly statistics
    now = datetime.utcnow()
    last_month = now.replace(day=1) - timedelta(days=1)
    this_month_start = now.replace(day=1)
    last_month_start = last_month.replace(day=1)

    last_month_users = User.query.filter(
        User.created_at >= last_month_start,
        User.created_at < this_month_start
    ).count()

    this_month_applications = Application.query.filter(
        Application.created_at >= this_month_start
    ).count()

    # Calculate user growth
    user_growth = 0
    if last_month_users > 0:
        current_month_users = User.query.filter(
            User.created_at >= this_month_start
        ).count()
        user_growth = round(((current_month_users - last_month_users) / last_month_users) * 100)

    # Calculate success rate (example: based on application status)
    successful_applications = Application.query.filter_by(status='accepted').count()
    success_rate = round((successful_applications / total_applications * 100) if total_applications > 0 else 0)

    # Get job categories data
    job_categories = JOB_TYPES
    job_category_counts = [Job.query.filter_by(job_type=cat).count() for cat in job_categories]

    # Get monthly activity data for the last 6 months
    monthly_labels = []
    monthly_jobs = []
    monthly_applications = []
    
    for i in range(5, -1, -1):
        month_start = (now - timedelta(days=30*i)).replace(day=1)
        month_end = (month_start.replace(month=month_start.month+1) if month_start.month < 12 
                    else month_start.replace(year=month_start.year+1, month=1))
        
        monthly_labels.append(month_start.strftime('%m/%Y'))
        monthly_jobs.append(Job.query.filter(
            Job.created_at >= month_start,
            Job.created_at < month_end
        ).count())
        monthly_applications.append(Application.query.filter(
            Application.created_at >= month_start,
            Application.created_at < month_end
        ).count())

    # Get recent activities (example: job postings and applications)
    recent_activities = []
    recent_jobs = Job.query.order_by(Job.created_at.desc()).limit(5).all()
    recent_applications = Application.query.order_by(Application.created_at.desc()).limit(5).all()

    for job in recent_jobs:
        recent_activities.append({
            'timestamp': job.created_at,
            'action': 'Tin tuyển dụng mới',
            'details': f'{job.title} - {job.company_name}'
        })

    for app in recent_applications:
        recent_activities.append({
            'timestamp': app.created_at,
            'action': 'Đơn ứng tuyển mới',
            'details': f'{app.applicant.name} - {app.job.title}'
        })

    # Sort activities by timestamp
    recent_activities.sort(key=lambda x: x['timestamp'], reverse=True)
    recent_activities = recent_activities[:10]  # Keep only 10 most recent

    # Get top employers
    top_employers = []
    company_stats = {}
    
    for job in Job.query.all():
        if job.company_name not in company_stats:
            company_stats[job.company_name] = {
                'company_name': job.company_name,
                'job_count': 0,
                'application_count': 0
            }
        company_stats[job.company_name]['job_count'] += 1
        company_stats[job.company_name]['application_count'] += len(job.applications)

    top_employers = sorted(
        company_stats.values(),
        key=lambda x: (x['job_count'], x['application_count']),
        reverse=True
    )[:5]  # Top 5 employers

    stats = {
        'total_users': total_users,
        'total_jobs': total_jobs,
        'active_jobs': active_jobs,
        'total_applications': total_applications,
        'last_month_users': last_month_users,
        'this_month_applications': this_month_applications,
        'user_growth': user_growth,
        'success_rate': success_rate,
        'student_count': student_count,
        'alumni_count': alumni_count,
        'admin_count': admin_count
    }

    return render_template('admin/analytics.html',
                         stats=stats,
                         job_categories=job_categories,
                         job_category_counts=job_category_counts,
                         monthly_labels=monthly_labels,
                         monthly_jobs=monthly_jobs,
                         monthly_applications=monthly_applications,
                         recent_activities=recent_activities,
                         top_employers=top_employers,
                         now=now)  # Add now variable to template context

@app.route('/posts')
def posts():
    """Display all public posts."""
    posts = Post.query.filter_by(is_published=True).order_by(Post.created_at.desc()).all()
    return render_template('posts.html', posts=posts)

@app.route('/admin/posts')
@login_required
def admin_posts():
    """Display all posts for admin management."""
    if current_user.role != 'admin':
        flash('Bạn không có quyền truy cập', 'danger')
        return redirect(url_for('index'))
    posts = Post.query.order_by(Post.created_at.desc()).all()
    return render_template('admin/posts.html', posts=posts)

@app.route('/admin/posts/confirm/<int:post_id>', methods=['POST'])
@login_required
def admin_confirm_post(post_id):
    if current_user.role != 'admin':
        flash('Bạn không có quyền truy cập', 'danger')
        return redirect(url_for('index'))
    
    post = Post.query.get_or_404(post_id)
    post.is_published = True
    db.session.commit()
    
    flash('Đã duyệt tin tức thành công', 'success')
    return redirect(url_for('admin_posts'))

@app.route('/admin/posts/delete/<int:post_id>', methods=['POST'])
@login_required
def admin_delete_post(post_id):
    if current_user.role != 'admin':
        flash('Bạn không có quyền truy cập', 'danger')
        return redirect(url_for('index'))
    
    post = Post.query.get_or_404(post_id)
    db.session.delete(post)
    db.session.commit()
    
    flash('Đã xóa tin tức thành công', 'success')
    return redirect(url_for('admin_posts'))

@app.route('/job/<int:job_id>/applications')
@login_required
def job_applications(job_id):
    job = Job.query.get_or_404(job_id)
    if current_user.role != 'alumni' or job.alumni_id != current_user.id:
        flash('Bạn không có quyền truy cập trang này.', 'danger')
        return redirect(url_for('index'))
    
    # Get filter parameters
    search = request.args.get('search', '')
    status = request.args.get('status', '')
    sort = request.args.get('sort', 'newest')
    viewed = request.args.get('viewed', '')
    
    # Base query
    applications = Application.query.filter_by(job_id=job_id)
    
    # Apply filters
    if search:
        applications = applications.join(User).filter(
            or_(
                User.name.ilike(f'%{search}%'),
                User.email.ilike(f'%{search}%')
            )
        )
    if status:
        applications = applications.filter_by(status=status)
    if viewed == 'true':
        applications = applications.filter_by(is_viewed=True)
    elif viewed == 'false':
        applications = applications.filter_by(is_viewed=False)
    
    # Apply sorting
    if sort == 'newest':
        applications = applications.order_by(Application.created_at.desc())
    elif sort == 'oldest':
        applications = applications.order_by(Application.created_at.asc())
    elif sort == 'name':
        applications = applications.join(User).order_by(User.name.asc())
    
    applications = applications.all()
    
    return render_template('alumni/job_applications.html', 
                         job=job, 
                         applications=applications)

@app.route('/application/<int:application_id>/details')
@login_required
def view_application_details(application_id):
    application = Application.query.get_or_404(application_id)
    if current_user.role != 'alumni' or application.job.alumni_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    # Mark application as viewed
    if not application.is_viewed:
        application.is_viewed = True
        db.session.commit()
    
    return jsonify({
        'applicant': {
            'name': application.applicant.name,
            'email': application.applicant.email,
            'profile': {
                'phone': application.applicant.profile.phone if application.applicant.profile else None,
                'location': application.applicant.profile.location if application.applicant.profile else None,
                'avatar': application.applicant.profile.avatar if application.applicant.profile else None,
                'education': [{
                    'school': edu.school,
                    'degree': edu.degree,
                    'major': edu.major,
                    'start_year': edu.start_year,
                    'end_year': edu.end_year
                } for edu in application.applicant.profile.education] if application.applicant.profile else [],
                'experience': [{
                    'position': exp.position,
                    'company': exp.company,
                    'description': exp.description,
                    'start_date': exp.start_date.strftime('%d/%m/%Y'),
                    'end_date': exp.end_date.strftime('%d/%m/%Y') if exp.end_date else None
                } for exp in application.applicant.profile.experience] if application.applicant.profile else [],
                'skills': [{'name': skill.name} for skill in application.applicant.profile.skills] if application.applicant.profile else []
            }
        },
        'status': application.status,
        'is_viewed': application.is_viewed
    })

@app.route('/application/<int:application_id>/status', methods=['POST'])
@login_required
def update_application_status(application_id):
    application = Application.query.get_or_404(application_id)
    if current_user.role != 'alumni' or application.job.alumni_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    data = request.get_json()
    new_status = data.get('status')
    
    if new_status not in ['pending', 'accepted', 'rejected']:
        return jsonify({'error': 'Invalid status'}), 400
    
    application.status = new_status
    db.session.commit()
    
    return jsonify({'success': True})

@app.route('/post/<int:post_id>/toggle_publish', methods=['POST'])
@login_required
def toggle_publish_post(post_id):
    post = Post.query.get_or_404(post_id)
    if post.author_id != current_user.id and current_user.role != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    
    post.is_published = not post.is_published
    db.session.commit()
    return jsonify({'success': True})

@app.route('/post/<int:post_id>/delete', methods=['POST'])
@login_required
def delete_post(post_id):
    post = Post.query.get_or_404(post_id)
    if post.author_id != current_user.id and current_user.role != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    
    db.session.delete(post)
    db.session.commit()
    return jsonify({'success': True})

@app.route('/posts/export')
@login_required
def export_posts():
    if current_user.role != 'alumni':
        return jsonify({'error': 'Unauthorized'}), 403
    
    posts = Post.query.filter_by(author_id=current_user.id).all()
    posts_data = [{
        'title': post.title,
        'content': post.content,
        'image': post.image,
        'is_published': post.is_published,
        'created_at': post.created_at.isoformat()
    } for post in posts]
    
    return jsonify(posts_data)

@app.route('/posts/stats/export')
@login_required
def export_posts_stats():
    if current_user.role != 'alumni':
        return jsonify({'error': 'Unauthorized'}), 403
    
    posts = Post.query.filter_by(author_id=current_user.id).all()
    stats = {
        'total_posts': len(posts),
        'published_posts': len([p for p in posts if p.is_published]),
        'unpublished_posts': len([p for p in posts if not p.is_published]),
        'total_applications': sum(len(p.applications) for p in posts),
        'average_applications': sum(len(p.applications) for p in posts) / len(posts) if posts else 0,
        'categories': {}
    }
    
    for post in posts:
        if post.job_type:
            stats['categories'][post.job_type] = stats['categories'].get(post.job_type, 0) + 1
    
    # Convert to CSV format
    csv_data = "Metric,Value\n"
    csv_data += f"Total Posts,{stats['total_posts']}\n"
    csv_data += f"Published Posts,{stats['published_posts']}\n"
    csv_data += f"Unpublished Posts,{stats['unpublished_posts']}\n"
    csv_data += f"Total Applications,{stats['total_applications']}\n"
    csv_data += f"Average Applications,{stats['average_applications']:.2f}\n\n"
    csv_data += "Category,Count\n"
    for category, count in stats['categories'].items():
        csv_data += f"{category},{count}\n"
    
    return Response(
        csv_data,
        mimetype="text/csv",
        headers={"Content-disposition": "attachment; filename=posts_stats.csv"}
    )

@app.route('/posts/import', methods=['POST'])
@login_required
def import_posts():
    if current_user.role != 'alumni':
        return jsonify({'error': 'Unauthorized'}), 403
    
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    save_as_published = request.form.get('save_as_published', 'true').lower() == 'true'
    
    try:
        if file.filename.endswith('.json'):
            data = json.loads(file.read())
        elif file.filename.endswith('.csv'):
            data = []
            csv_data = file.read().decode('utf-8').splitlines()
            reader = csv.DictReader(csv_data)
            for row in reader:
                data.append(row)
        else:
            return jsonify({'error': 'Unsupported file format'}), 400
        
        count = 0
        for post_data in data:
            post = Post(
                title=post_data.get('title', 'Untitled'),
                content=post_data.get('content', ''),
                image=post_data.get('image', ''),
                author_id=current_user.id,
                is_published=save_as_published
            )
            db.session.add(post)
            count += 1
        
        db.session.commit()
        return jsonify({'success': True, 'count': count})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# Social Media Routes
@app.route('/social/feed')
@login_required
def social_feed():
    posts = Post.query.order_by(Post.created_at.desc()).all()
    return render_template('social/feed.html', posts=posts)

@app.route('/social/posts/create', methods=['POST'])
@login_required
def create_post():
    content = request.form.get('content')
    image = request.files.get('image')
    
    if not content:
        flash('Nội dung bài đăng không được để trống', 'danger')
        return redirect(url_for('social_feed'))
    
    post = Post(content=content, user_id=current_user.id)
    
    if image:
        filename = secure_filename(image.filename)
        image_path = os.path.join(app.config['UPLOAD_FOLDER'], 'posts', filename)
        image.save(image_path)
        post.image_url = filename
    
    db.session.add(post)
    db.session.commit()
    
    flash('Đăng bài thành công', 'success')
    return redirect(url_for('social_feed'))

@app.route('/social/posts/<int:post_id>/comments', methods=['POST'])
@login_required
def create_comment(post_id):
    data = request.get_json()
    content = data.get('content')
    
    if not content:
        return jsonify({'success': False, 'message': 'Nội dung bình luận không được để trống'})
    
    comment = Comment(content=content, user_id=current_user.id, post_id=post_id)
    db.session.add(comment)
    db.session.commit()
    
    return jsonify({'success': True})

@app.route('/social/posts/<int:post_id>/toggle_like', methods=['POST'])
@login_required
def toggle_like(post_id):
    post = Post.query.get_or_404(post_id)
    if current_user in post.likers:
        post.likers.remove(current_user)
    else:
        post.likers.append(current_user)
    db.session.commit()
    return jsonify({
        'success': True,
        'likes_count': post.likers.count()
    })

@app.template_global()
def update_url(args, **kwargs):
    """Make update_url function available in templates"""
    params = args.copy()
    for key, value in kwargs.items():
        params[key] = value
    return '?' + urlencode(params)

@app.route('/init-admin')
def init_admin():
    admin_email = "admin@fit.edu.vn"
    admin_password = "admin123"  # In production, use a secure password
    admin_name = "Admin"
    
    # Check if admin user already exists
    admin = User.query.filter_by(email=admin_email).first()
    if not admin:
        admin = User(
            name=admin_name,
            email=admin_email,
            password=generate_password_hash(admin_password),
            role='admin'
        )
        db.session.add(admin)
        db.session.commit()
        return "Admin user created successfully!"
    return "Admin user already exists!"

if __name__ == '__main__':
    with app.app_context():
        # Create tables if they don't exist
        db.create_all()
        
        # Add new columns to Job table if they don't exist
        with db.engine.connect() as conn:
            # Check if columns exist
            inspector = inspect(db.engine)
            existing_columns = [col['name'] for col in inspector.get_columns('job')]
            
            # Add contact_name column if not exists
            if 'contact_name' not in existing_columns:
                conn.execute(text('ALTER TABLE job ADD COLUMN contact_name VARCHAR(100)'))
            
            # Add contact_email column if not exists
            if 'contact_email' not in existing_columns:
                conn.execute(text('ALTER TABLE job ADD COLUMN contact_email VARCHAR(120)'))
            
            # Add contact_phone column if not exists
            if 'contact_phone' not in existing_columns:
                conn.execute(text('ALTER TABLE job ADD COLUMN contact_phone VARCHAR(20)'))
            
            conn.commit()
            
    app.run(debug=True) 