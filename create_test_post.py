import os
import sqlite3
from datetime import datetime
import shutil

def create_test_post():
    """
    Create a test post with an image to verify that images are displayed correctly
    """
    # Connect to the database
    conn = sqlite3.connect('alumni.db')
    cursor = conn.cursor()
    
    # Create a test post
    content = "This is a test post with an image to verify image display functionality"
    user_id = 1  # Assuming admin user has ID 1
    created_at = datetime.now().isoformat()
    
    # Test image filename
    test_img_filename = "test_image_" + datetime.now().strftime("%Y%m%d%H%M%S") + ".jpg"
    image_url = f"uploads/posts/{test_img_filename}"
    
    # Insert the post
    cursor.execute(
        "INSERT INTO post (content, user_id, created_at, image_url) VALUES (?, ?, ?, ?)",
        (content, user_id, created_at, image_url)
    )
    post_id = cursor.lastrowid
    
    # Copy a sample image to the posts folder
    sample_image = "static/uploads/posts/20250522190038_0021410471.JPG"  # Use the existing image
    target_path = f"static/uploads/posts/{test_img_filename}"
    
    if os.path.exists(sample_image):
        shutil.copy2(sample_image, target_path)
        print(f"Created test post with ID {post_id} and copied image to {target_path}")
    else:
        print(f"WARNING: Could not find sample image at {sample_image}")
        
    # Commit changes and close connection
    conn.commit()
    conn.close()
    
    print(f"Test post created with ID: {post_id}")
    print(f"Image URL: {image_url}")

if __name__ == "__main__":
    print("Creating test post with image...")
    create_test_post()
    print("Done! Please check the feed page to see if the image is displayed correctly.") 