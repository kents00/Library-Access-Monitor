import os

def ensure_upload_directories(app):
    """Ensure that necessary upload directories exist."""
    uploads_dir = os.path.join(app.static_folder, 'uploads')
    if not os.path.exists(uploads_dir):
        os.makedirs(uploads_dir)
        app.logger.info(f"Created uploads directory at {uploads_dir}")

    # Create a default image if it doesn't exist
    default_img = os.path.join(uploads_dir, 'default_image.jpg')
    if not os.path.exists(default_img):
        # Try to create an empty placeholder image or copy from assets
        try:
            from PIL import Image
            img = Image.new('RGB', (200, 200), color='gray')
            img.save(default_img)
            app.logger.info(f"Created default image at {default_img}")
        except ImportError:
            app.logger.warning("PIL not available. Default image not created.")
            # Create an empty file as fallback
            with open(default_img, 'w') as f:
                f.write('')
