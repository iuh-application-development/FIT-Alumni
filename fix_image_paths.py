import os
import shutil
import sqlite3

def merge_uploads_folders():
    """
    Merge the two uploads folders - copy any missing files from the external 
    static/uploads to FIT-Alumni new/static/uploads
    """
    base_dir = os.path.dirname(os.getcwd())  # Get the parent directory
    external_uploads = os.path.join(base_dir, 'static', 'uploads')
    project_uploads = os.path.join('static', 'uploads')
    
    print(f"Merging uploads folders:")
    print(f"- External folder: {external_uploads}")
    print(f"- Project folder: {project_uploads}")
    
    # Check if external uploads folder exists
    if not os.path.exists(external_uploads):
        print("External uploads folder not found.")
        return
    
    # Create project uploads folder if it doesn't exist
    if not os.path.exists(project_uploads):
        os.makedirs(project_uploads)
        print(f"Created project uploads folder: {project_uploads}")
    
    # Copy files from external to project uploads
    copied_count = 0
    for root, dirs, files in os.walk(external_uploads):
        # Get the relative path from external_uploads
        rel_path = os.path.relpath(root, external_uploads)
        if rel_path == '.':  # Root directory
            rel_path = ''
        
        # Create corresponding directory in project_uploads if needed
        dest_dir = os.path.join(project_uploads, rel_path)
        if not os.path.exists(dest_dir):
            os.makedirs(dest_dir)
            print(f"Created directory: {dest_dir}")
        
        # Copy files that don't exist in project_uploads
        for file in files:
            src_file = os.path.join(root, file)
            dest_file = os.path.join(dest_dir, file)
            
            if not os.path.exists(dest_file):
                shutil.copy2(src_file, dest_file)
                print(f"Copied: {src_file} -> {dest_file}")
                copied_count += 1
    
    print(f"Copied {copied_count} files from external to project uploads.")

def fix_database_image_paths():
    """
    Fix image paths in the database to ensure they all use the format 'uploads/posts/filename'
    """
    try:
        conn = sqlite3.connect('alumni.db')
        cursor = conn.cursor()
        
        # Get all posts with image URLs
        cursor.execute("SELECT id, image_url FROM post WHERE image_url IS NOT NULL AND image_url NOT LIKE 'http%'")
        posts = cursor.fetchall()
        
        print(f"\nFixing image paths in database for {len(posts)} posts:")
        
        fixed_count = 0
        for post_id, image_url in posts:
            original_url = image_url
            
            # Fix paths that don't start with "uploads/"
            if not image_url.startswith('uploads/'):
                # If it's just a filename, add the uploads/posts/ prefix
                if '/' not in image_url:
                    image_url = f"uploads/posts/{image_url}"
                # If it starts with static/uploads, remove the static/ prefix
                elif image_url.startswith('static/uploads/'):
                    image_url = image_url[7:]  # Remove "static/"
            
            # Save the updated path if it changed
            if original_url != image_url:
                cursor.execute("UPDATE post SET image_url = ? WHERE id = ?", (image_url, post_id))
                fixed_count += 1
                print(f"Post ID={post_id}: Changed path from '{original_url}' to '{image_url}'")
            
            # Check if the file exists at the new location
            file_path = os.path.join('static', image_url)
            if not os.path.exists(file_path):
                print(f"WARNING: Post ID={post_id}: File still not found at: {file_path}")
        
        conn.commit()
        conn.close()
        print(f"Fixed {fixed_count} database records.")
    
    except Exception as e:
        print(f"Error fixing database paths: {str(e)}")

if __name__ == "__main__":
    print("=== Starting uploads folder merge and database path fixes ===")
    merge_uploads_folders()
    fix_database_image_paths()
    print("=== Completed uploads folder merge and database path fixes ===") 