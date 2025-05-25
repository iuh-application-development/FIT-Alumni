import os
import shutil
import sqlite3

def check_and_fix_static_paths():
    """
    Kiểm tra và đảm bảo thư mục static/uploads có đầy đủ cấu trúc và quyền truy cập
    """
    base_dir = os.getcwd()
    static_dir = os.path.join(base_dir, 'static')
    uploads_dir = os.path.join(static_dir, 'uploads')
    posts_dir = os.path.join(uploads_dir, 'posts')
    
    print(f"Đang kiểm tra cấu trúc thư mục static trong {base_dir}")
    
    # Kiểm tra thư mục static
    if not os.path.exists(static_dir):
        print(f"Thư mục static không tồn tại. Tạo mới...")
        os.makedirs(static_dir)
    
    # Kiểm tra thư mục uploads
    if not os.path.exists(uploads_dir):
        print(f"Thư mục uploads không tồn tại. Tạo mới...")
        os.makedirs(uploads_dir)
    
    # Kiểm tra các thư mục con của uploads
    for subfolder in ['posts', 'avatars', 'events', 'resumes', 'company_logos']:
        subfolder_path = os.path.join(uploads_dir, subfolder)
        if not os.path.exists(subfolder_path):
            print(f"Thư mục {subfolder_path} không tồn tại. Tạo mới...")
            os.makedirs(subfolder_path)
    
    print("Đã kiểm tra và tạo đầy đủ cấu trúc thư mục")
    
    # Kiểm tra quyền truy cập
    try:
        # Tạo file test để kiểm tra quyền ghi
        test_file = os.path.join(posts_dir, "test_write_access.txt")
        with open(test_file, 'w') as f:
            f.write("Test write access")
        
        # Xóa file test
        os.remove(test_file)
        print("Quyền ghi vào thư mục static/uploads/posts OK")
    except Exception as e:
        print(f"CẢNH BÁO: Không thể ghi vào thư mục: {str(e)}")
        print("Vui lòng kiểm tra quyền truy cập vào thư mục static/uploads")

def check_database_image_paths():
    """
    Kiểm tra các đường dẫn hình ảnh trong cơ sở dữ liệu
    """
    try:
        conn = sqlite3.connect('alumni.db')
        cursor = conn.cursor()
        
        # Kiểm tra các đường dẫn trong posts
        cursor.execute("SELECT id, image_url FROM post WHERE image_url IS NOT NULL AND image_url NOT LIKE 'http%'")
        posts = cursor.fetchall()
        
        print(f"Tìm thấy {len(posts)} bài viết có hình ảnh cục bộ")
        
        # Kiểm tra từng đường dẫn
        for post_id, image_url in posts:
            if not image_url.startswith('uploads/'):
                print(f"Bài viết ID={post_id}: Đường dẫn không đúng định dạng: {image_url}")
            else:
                # Kiểm tra xem file có tồn tại không
                file_path = os.path.join('static', image_url)
                if not os.path.exists(file_path):
                    print(f"Bài viết ID={post_id}: File không tồn tại: {file_path}")
        
        conn.close()
    except Exception as e:
        print(f"Lỗi khi kiểm tra cơ sở dữ liệu: {str(e)}")

if __name__ == "__main__":
    print("=== Bắt đầu kiểm tra và sửa thư mục static ===")
    check_and_fix_static_paths()
    check_database_image_paths()
    print("=== Hoàn thành kiểm tra thư mục static ===") 