from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, PasswordField, SelectField, IntegerField, DateField, FileField, BooleanField, EmailField, DateTimeField
from wtforms.validators import DataRequired, Email, Length, Optional, NumberRange, ValidationError
from datetime import datetime
import email_validator

class RegistrationForm(FlaskForm):
    name = StringField('Họ và tên', validators=[DataRequired(), Length(min=2, max=100)])
    email = StringField('Email', validators=[DataRequired(), Email(message='Email không hợp lệ')])
    password = PasswordField('Mật khẩu', validators=[DataRequired(), Length(min=6)])

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email(message='Email không hợp lệ')])
    password = PasswordField('Mật khẩu', validators=[DataRequired()])

class JobForm(FlaskForm):
    title = StringField('Tiêu đề', validators=[DataRequired()])
    company_name = StringField('Tên công ty', validators=[DataRequired()])
    company_logo = FileField('Logo công ty')
    location = StringField('Địa điểm', validators=[DataRequired()])
    
    job_type = SelectField('Loại công việc', choices=[
        ('', 'Chọn loại công việc'),
        ('full_time', 'Toàn thời gian'),
        ('part_time', 'Bán thời gian'),
        ('contract', 'Hợp đồng'),
        ('internship', 'Thực tập'),
        ('remote', 'Từ xa')
    ])
    
    experience = SelectField('Kinh nghiệm', choices=[
        ('', 'Chọn yêu cầu kinh nghiệm'),
        ('fresh', 'Mới tốt nghiệp'),
        ('1_year', '1 năm'),
        ('2_years', '2 năm'),
        ('3_5_years', '3-5 năm'),
        ('5_plus_years', 'Trên 5 năm')
    ])
    
    work_type = SelectField('Hình thức làm việc', choices=[
        ('', 'Chọn hình thức làm việc'),
        ('Full-time', 'Toàn thời gian'),
        ('Part-time', 'Bán thời gian'),
        ('Remote', 'Làm từ xa'),
        ('Hybrid', 'Kết hợp')
    ])
    
    salary_min = StringField('Lương tối thiểu')
    salary_max = StringField('Lương tối đa')
    salary_currency = SelectField('Đơn vị', choices=[
        ('VND', 'VND'),
        ('USD', 'USD')
    ])
    salary_negotiable = BooleanField('Thương lượng')
    salary_display = StringField('Mức lương hiển thị')
    
    positions = IntegerField('Số lượng cần tuyển', default=1)
    deadline = DateField('Hạn nộp hồ sơ', format='%Y-%m-%d')
    
    description = TextAreaField('Mô tả công việc', validators=[DataRequired()])
    requirements = TextAreaField('Yêu cầu ứng viên', validators=[DataRequired()])
    benefits = TextAreaField('Quyền lợi')
    
    contact_name = StringField('Người liên hệ')
    contact_email = EmailField('Email liên hệ', validators=[DataRequired(), Email()])
    contact_phone = StringField('Số điện thoại')

    def validate_deadline(self, field):
        if field.data and field.data < datetime.now().date():
            raise ValidationError('Hạn nộp hồ sơ phải lớn hơn ngày hiện tại')

class EventForm(FlaskForm):
    title = StringField('Tên sự kiện', validators=[DataRequired(), Length(min=5, max=200)])
    description = TextAreaField('Mô tả sự kiện', validators=[DataRequired(), Length(min=10)])
    start_time = DateTimeField('Thời gian bắt đầu', validators=[DataRequired()], format='%Y-%m-%dT%H:%M')
    end_time = DateTimeField('Thời gian kết thúc', validators=[Optional()], format='%Y-%m-%dT%H:%M')
    location = StringField('Địa điểm', validators=[DataRequired(), Length(min=5, max=200)])
    capacity = IntegerField('Sức chứa', validators=[Optional(), NumberRange(min=1)])
    requirements = TextAreaField('Yêu cầu tham gia', validators=[Optional()])
    contact_info = TextAreaField('Thông tin liên hệ', validators=[Optional()])
    image = FileField('Ảnh sự kiện', validators=[Optional()])

    def validate_start_time(self, field):
        if field.data and field.data < datetime.now():
            raise ValidationError('Thời gian bắt đầu phải lớn hơn thời gian hiện tại')
    
    def validate_end_time(self, field):
        if field.data and self.start_time.data and field.data <= self.start_time.data:
            raise ValidationError('Thời gian kết thúc phải lớn hơn thời gian bắt đầu') 