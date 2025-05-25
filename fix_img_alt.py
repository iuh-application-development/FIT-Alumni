import os
import re
from bs4 import BeautifulSoup

def fix_image_tag_in_templates():
    """
    Sửa lại tất cả các thẻ img có alt="Post image" để hiển thị hình ảnh đúng
    """
    # Danh sách các file template cần kiểm tra
    template_files = [
        'templates/social/feed.html',
        'templates/social/user_posts.html',
        'templates/social/edit_post.html'
    ]
    
    for template_file in template_files:
        file_path = os.path.join(template_file)
        if not os.path.exists(file_path):
            print(f"File {file_path} không tồn tại")
            continue
            
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Tìm và sửa các thẻ img
            soup = BeautifulSoup(content, 'html.parser')
            img_tags = soup.find_all('img', alt="Post image")
            
            total_tags = len(img_tags)
            if total_tags > 0:
                print(f"Tìm thấy {total_tags} thẻ img có alt='Post image' trong {template_file}")
                
                # Sửa lại nội dung file bằng regex để giữ nguyên cấu trúc
                # Thay thế img alt="Post image" bằng đoạn code Jinja2 chính xác
                # Đoạn mẫu cần thay thế
                pattern = r'<img\s+[^>]*\salt="Post\s+image"[^>]*>'
                
                # Kiểm tra xem file có chứa mẫu hiển thị hình ảnh đúng không
                correct_pattern = r'{%\s*if\s+post\.image_url\s*%}.*?{%\s*endif\s*%}'
                has_correct_pattern = bool(re.search(correct_pattern, content, re.DOTALL))
                
                if not has_correct_pattern:
                    # Đoạn mã Jinja2 đúng để hiển thị hình ảnh
                    replacement = """
                        {% if post.image_url %}
                            {% if post.image_url.startswith('http') %}
                            <!-- External image URL -->
                            <img src="{{ post.image_url }}" class="img-fluid post-image rounded" alt="Post image">
                            {% else %}
                            <!-- Local uploaded image -->
                            <img src="{{ url_for('static', filename=post.image_url) }}" class="img-fluid post-image rounded" alt="Post image">
                            {% endif %}
                        {% endif %}
                    """
                    
                    # Thay thế mẫu cũ bằng mẫu mới
                    new_content = re.sub(pattern, replacement, content)
                    
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(new_content)
                        
                    print(f"Đã sửa thành công file {template_file}")
                else:
                    print(f"File {template_file} đã có mẫu hiển thị hình ảnh đúng")
            else:
                print(f"Không tìm thấy thẻ img có alt='Post image' trong {template_file}")
                
        except Exception as e:
            print(f"Lỗi khi xử lý file {template_file}: {str(e)}")

def fix_create_post_function():
    """
    Kiểm tra và sửa lỗi trong hàm create_post và edit_post
    """
    app_file = 'app.py'
    
    try:
        with open(app_file, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Kiểm tra xử lý hình ảnh trong create_post
        create_post_pattern = r'@app\.route\(\'/social/posts/create\',\s*methods=\[\'POST\'\]\)(.*?)def\s+create_post\(\):(.*?)return\s+redirect\(.*?\)'
        create_post_match = re.search(create_post_pattern, content, re.DOTALL)
        
        if create_post_match:
            create_post_code = create_post_match.group(0)
            
            # Kiểm tra xử lý image đúng cách
            if 'post.image_url = f"uploads/posts/{filename}"' in create_post_code:
                print("Hàm create_post có xử lý image đúng")
            else:
                print("Cần kiểm tra và sửa hàm create_post")
                
        # Kiểm tra xử lý hình ảnh trong edit_post
        edit_post_pattern = r'@app\.route\(\'/social/posts/<int:post_id>/edit\',\s*methods=\[\'GET\',\s*\'POST\'\]\)(.*?)def\s+edit_post\(post_id\):(.*?)return\s+render_template\(\'social/edit_post\.html\',\s*post=post\)'
        edit_post_match = re.search(edit_post_pattern, content, re.DOTALL)
        
        if edit_post_match:
            edit_post_code = edit_post_match.group(0)
            
            # Kiểm tra xử lý image đúng cách
            if 'post.image_url = f"uploads/posts/{filename}"' in edit_post_code:
                print("Hàm edit_post có xử lý image đúng")
            else:
                print("Cần kiểm tra và sửa hàm edit_post")
                
    except Exception as e:
        print(f"Lỗi khi kiểm tra hàm xử lý bài viết: {str(e)}")

if __name__ == "__main__":
    # Đảm bảo chạy từ thư mục gốc của dự án
    current_dir = os.getcwd()
    if os.path.basename(current_dir) != "FIT-Alumni new":
        print(f"Chuyển đến thư mục dự án FIT-Alumni new")
        os.chdir("FIT-Alumni new")
        
    # Kiểm tra xem thư mục static/uploads/posts có tồn tại không
    if not os.path.exists('static/uploads/posts'):
        print("Thư mục static/uploads/posts không tồn tại, tạo thư mục")
        os.makedirs('static/uploads/posts', exist_ok=True)
        
    print("Bắt đầu sửa lỗi hiển thị hình ảnh trong bài viết")
    fix_image_tag_in_templates()
    fix_create_post_function()
    print("Hoàn thành kiểm tra và sửa lỗi") 