# FIT Alumni Portal

Cổng thông tin dành cho cựu sinh viên FIT.

## Yêu cầu hệ thống

- Python 3.8 hoặc cao hơn
- pip (Python package installer)

## Cài đặt

1. Clone repository này về máy local:
```bash
git clone <repository-url>
cd fit-alumini
```

2. Tạo và kích hoạt môi trường ảo (virtual environment):
```bash
python -m venv venv
# Windows
.\venv\Scripts\activate
# Linux/Mac
source venv/bin/activate
```

3. Cài đặt các thư viện cần thiết:
```bash
pip install -r requirements.txt
```

## Chạy ứng dụng

1. Đảm bảo bạn đang ở trong môi trường ảo (venv)

2. Chạy ứng dụng:
```bash
python app.py
```

3. Mở trình duyệt web và truy cập:
```
http://localhost:5000
```

## Cấu trúc thư mục

- `app.py`: File chính chứa mã nguồn ứng dụng Flask
- `forms.py`: Chứa các form được sử dụng trong ứng dụng
- `requirements.txt`: Danh sách các thư viện Python cần thiết
- `static/`: Thư mục chứa các file tĩnh (CSS, JavaScript, hình ảnh)
- `templates/`: Thư mục chứa các template HTML
- `migrations/`: Thư mục chứa các file migration của database
- `alumni.db`: Database SQLite chứa dữ liệu ứng dụng

## Đóng góp

Nếu bạn muốn đóng góp cho dự án, vui lòng tạo pull request hoặc báo cáo issues. 