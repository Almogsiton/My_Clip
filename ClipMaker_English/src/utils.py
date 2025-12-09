import os
import tempfile
from PIL import Image, ImageOps, ImageDraw, ImageFont
import numpy as np
from src.constants import SCREEN_SIZE

def resize_and_pad_image(image, target_size=SCREEN_SIZE, background_color=(0, 0, 0)):
    """
    Resizes an image to fit within target_size while maintaining aspect ratio.
    Pads with background_color to fill the target_size.
    """
    img = ImageOps.exif_transpose(image)
    target_width, target_height = target_size
    target_ratio = target_width / target_height
    img_ratio = img.width / img.height
    
    if img_ratio > target_ratio:
        # Image is wider than target
        new_width = target_width
        new_height = int(target_width / img_ratio)
    else:
        # Image is taller than target
        new_height = target_height
        new_width = int(target_height * img_ratio)
        
    img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
    
    # Create background
    background = Image.new('RGB', target_size, background_color)
    
    # Paste in center
    paste_x = (target_width - new_width) // 2
    paste_y = (target_height - new_height) // 2
    background.paste(img, (paste_x, paste_y))
    
    return background

def create_slide_image(slide_data):
    """
    Creates a numpy array image for a given slide data dictionary.
    """
    # Create base image
    if slide_data['type'] == 'image':
        # Reset file pointer if it's a file-like object (UploadedFile)
        if hasattr(slide_data['content'], 'seek'):
            slide_data['content'].seek(0)
            
        img = Image.open(slide_data['content'])
        # Use helper function
        img = resize_and_pad_image(img)
    else:
        # Solid color
        color = slide_data['color']
        img = Image.new('RGB', SCREEN_SIZE, color)
    
    # Add Text Overlay
    if slide_data.get('text'):
        draw = ImageDraw.Draw(img)
        try:
            # Try to use a better default font if available, else default
            font = ImageFont.truetype("arial.ttf", 80)
        except:
            font = ImageFont.load_default()
            
        text = slide_data['text']
        text_color = slide_data.get('text_color', '#ffffff')
        
        # Simple centering
        # In newer Pillow versions, textbbox is preferred but keeping simple for compatibility
        w = SCREEN_SIZE[0]
        h = SCREEN_SIZE[1]
        draw.text((w/2, h/2), text, font=font, fill=text_color, anchor="mm")
        
    return np.array(img)

def save_uploaded_file(uploaded_file):
    """
    Saves an uploaded file to a temporary file and returns the path.
    """
    if uploaded_file is None:
        return None
        
    try:
        suffix = f".{uploaded_file.name.split('.')[-1]}"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tfile:
            tfile.write(uploaded_file.read())
            return tfile.name
    except Exception as e:
        print(f"Error saving file: {e}")
        return None

def safe_remove(path):
    """Safely removes a file if it exists."""
    if path and os.path.exists(path):
        try:
            os.remove(path)
        except Exception:
            pass
