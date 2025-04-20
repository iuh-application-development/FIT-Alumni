from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from sqlalchemy.sql import func

db = SQLAlchemy()

# Association table for post likes
post_likes = db.Table('post_likes',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('post_id', db.Integer, db.ForeignKey('post.id'), primary_key=True)
)

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='user')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    profile = db.relationship('Profile', backref='user', uselist=False)
    posts = db.relationship('Post', backref='author', lazy=True)
    comments = db.relationship('Comment', backref='author', lazy=True)
    liked_posts = db.relationship('Post', secondary=post_likes, backref=db.backref('likers', lazy='dynamic'))
    education = db.relationship('Education', backref='user', lazy=True)
    experience = db.relationship('Experience', backref='user', lazy=True)
    skills = db.relationship('Skill', backref='user', lazy=True)
    jobs_posted = db.relationship('Job', backref='alumni', lazy=True, foreign_keys='Job.alumni_id')

class Profile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    avatar = db.Column(db.String(200))
    bio = db.Column(db.Text)
    phone = db.Column(db.String(20))
    address = db.Column(db.String(200))
    company = db.Column(db.String(100))
    position = db.Column(db.String(100))
    graduation_year = db.Column(db.Integer)

class Education(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    school = db.Column(db.String(200), nullable=False)
    major = db.Column(db.String(200))
    degree = db.Column(db.String(100))
    start_date = db.Column(db.DateTime)
    end_date = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Experience(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    position = db.Column(db.String(200), nullable=False)
    company = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    start_date = db.Column(db.DateTime)
    end_date = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Skill(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    image_url = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    comments = db.relationship('Comment', backref='post', lazy=True, cascade='all, delete-orphan')

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)

class Job(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    requirements = db.Column(db.Text)
    benefits = db.Column(db.Text)
    salary_display = db.Column(db.String(100))
    location = db.Column(db.String(200), nullable=False)
    job_type = db.Column(db.String(50))
    experience = db.Column(db.String(50))
    headcount = db.Column(db.Integer, default=1)
    deadline = db.Column(db.DateTime(timezone=True))
    company_logo = db.Column(db.String(200))
    company_name = db.Column(db.String(200), nullable=False)
    contact_name = db.Column(db.String(100))
    contact_email = db.Column(db.String(120))
    contact_phone = db.Column(db.String(20))
    alumni_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    is_confirmed = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime(timezone=True), server_default=func.now())
    applications = db.relationship('JobApplication', backref='job', lazy=True, cascade='all, delete-orphan')

    @property
    def salary_range(self):
        if not self.salary_display:
            return "Thương lượng"
        return self.salary_display

class JobApplication(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    job_id = db.Column(db.Integer, db.ForeignKey('job.id'), nullable=False)
    status = db.Column(db.String(20), default='pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user = db.relationship('User', backref=db.backref('job_applications', lazy=True)) 