# FIT-Alumni: Hệ Thống Kết Nối Cựu Sinh Viên Khoa CNTT

## Giới thiệu tổng quan

**FIT-Alumni** là một hệ thống phần mềm được phát triển với mục tiêu xây dựng cầu nối vững chắc giữa cựu sinh viên và nhà trường. Thông qua nền tảng này, người dùng có thể cập nhật hồ sơ cá nhân, theo dõi vị trí việc làm sau tốt nghiệp, giao lưu và hỗ trợ lẫn nhau trong quá trình phát triển sự nghiệp.

Hệ thống không chỉ hỗ trợ việc quản lý dữ liệu cựu sinh viên mà còn cung cấp các chức năng thống kê, phân loại theo lĩnh vực công tác, đơn vị công tác, đồng thời tạo ra một diễn đàn mở để trao đổi học thuật, chia sẻ kinh nghiệm làm việc và đăng tin tuyển dụng.

## Thành viên thực hiện dự án

| Họ và tên             | Mã số sinh viên  | Vai trò chính                                                | Mức độ hoàn thành  |
|-----------------------|------------------|--------------------------------------------------------------|--------------------|
| Nguyễn Phước Điền     | 21002595         | Phát triển chức năng: Trang chủ, đăng bài, việc làm, profile | 100%               |
| Lê Thị Thúy Kiều      | 22733091         | Giao diện và chức năng quản lý của Admin, auth, báo cáo      | 100%               |
| Nguyễn Thị Mỹ Duyên   | 22640511         | Thiết kế giao diện, chỉnh sửa HTML/CSS, báo cáo              | 100%               |
| Lê Hữu Trọng          | 22652671         | Lên ý tưởng thiết kế Slide trình bày và video demo           | 100%               |

## Cấu trúc dự án

```
FIT-ALUMNI NEW/
├── __pycache__/
├── .venv/
├── instance/
├── migrations/
├── static/
│   ├── css/
│   ├── images/
│   ├── img/
│   ├── js/
│   └── uploads/
├── templates/
│   ├── admin/
│   ├── alumni/
│   ├── social/
│   ├── student/
│   ├── user/
│   ├── _messages.html
│   ├── base.html
│   ├── edit_profile.html
│   ├── events.html
│   ├── index.html
│   ├── job_detail.html
│   ├── jobs.html
│   ├── login.html
│   ├── profile.html
│   ├── register.html
│   └── test_image.html
├── venv/
├── .gitignore
├── alumni.db
├── app.py
├── forms.py
├── models.py
├── README.md
└── requirements.txt
```

## Vai trò người dùng

- **Admin**:
  - Quản lý tài khoản người dùng và cựu sinh viên.
  - Duyệt các bài đăng tuyển dụng và hồ sơ ứng tuyển.
  - Đăng bài, bình luận trên bảng tin nội bộ.

- **Cựu sinh viên**:
  - Đăng ký/đăng nhập hệ thống.
  - Đăng bài viết, đăng tin tuyển dụng.
  - Duyệt các hồ sơ ứng tuyển và hỗ trợ sinh viên hiện đang theo học.

- **Sinh viên hiện tại**:
  - Đăng bài viết, bình luận, giao lưu trong cộng đồng.
  - Tìm kiếm, ứng tuyển các vị trí việc làm phù hợp.

## Công nghệ sử dụng

- **Ngôn ngữ backend**: Python (Flask Framework)
- **Cơ sở dữ liệu**: SQLite
- **Frontend**: HTML5, CSS3, JavaScript
- **Giao diện tĩnh**: Thư mục static và templates theo kiến trúc MVC

## Hướng dẫn triển khai hệ thống

### Bước 1: Sao chép mã nguồn về máy local
```bash
git clone https://github.com/iuh-application-development/FIT-Alumni.git
```

### Bước 2: Tạo môi trường ảo và kích hoạt
```bash
python -m venv venv

# Đối với Windows
.\venv\Scripts\activate

# Đối với Mac/Linux
source venv/bin/activate
```

### Bước 3: Cài đặt thư viện phụ thuộc
```bash
pip install -r requirements.txt
```

### Bước 4: Khởi chạy ứng dụng
```bash
python app.py
```
Sau đó, mở trình duyệt và truy cập địa chỉ:
```
http://localhost:5000
```

## Tài liệu và nguồn tham khảo

1. Phạm Minh Tâm, Lê Thanh Hòa (2021). *Ứng dụng CNTT trong việc kết nối mạng lưới cựu sinh viên* - Hội thảo ICT 2021.
2. Tran, H.T. & Nguyen, M.H. (2019). *Developing an Alumni Information System Using PHP and MySQL* - IJCA.
3. Dahri, A.S. et al. (2017). *Design and Development of Alumni Information System* - IJCA.
4. Roy, S. & Saha, S. (2016). *Web-Based Alumni Information System* - IEEE CSE.
5. Ngô Văn Tùng (2020). *Ứng dụng hệ thống alumni trong nâng cao chất lượng đào tạo* - Tạp chí Giáo dục.

## Tài nguyên bổ sung

- Video demo, báo cáo chi tiết và bản trình chiếu có thể được truy cập tại:  
🔗 [Google Drive - FIT Alumni Project](https://drive.google.com/drive/folders/1bITDdpy7vZUikldcUwcj6JTNOun3UaFu?usp=drive_link)

---

> *FIT-Alumni không chỉ là một bài tập học thuật, mà còn là nền tảng thực tiễn cho việc áp dụng kỹ năng phát triển phần mềm, tổ chức nhóm và phục vụ cộng đồng sinh viên đại học một cách có trách nhiệm và hiệu quả.*
