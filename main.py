import requests
import questionary
import subprocess
import tempfile
import os
import sys
import random
from typing import List, Optional, Tuple
from PIL import Image, ImageEnhance

# Constants
API_URL = 'https://api.waifu.im/search'

# Reuse session for connection pooling
_session = requests.Session()

VERSATILE_TAGS = [
    'waifu', 'maid', 'marin-kitagawa', 'mori-calliope', 
    'raiden-shogun', 'oppai', 'selfies', 'uniform', 'kamisato-ayaka'
]

NSFW_TAGS = [
    'ero', 'ass', 'hentai', 'milf', 'oral', 'paizuri', 'ecchi'
]

def select_tags() -> dict:
    """Interactive tag selection."""
    mode = questionary.select(
        "Select content type:",
        choices=["Versatile (Safe/Mixed)", "NSFW (18+)"]
    ).ask()
    
    is_nsfw = mode == "NSFW (18+)"
    available_tags = NSFW_TAGS if is_nsfw else VERSATILE_TAGS
    
    tags = questionary.checkbox(
        "Select tags:",
        choices=available_tags
    ).ask()
    
    return {
        "tags": tags,
        "is_nsfw": is_nsfw
    }

def select_height() -> int:
    """Ask for ASCII output height."""
    height = questionary.text(
        "Enter ASCII height (default: 40, higher = more detail):",
        default="40",
        validate=lambda text: text.isdigit() or "Please enter a valid integer"
    ).ask()
    return int(height)

def fetch_waifu(tags: List[str], is_nsfw: bool) -> Optional[str]:
    """Fetch waifu image URL from API."""
    # API requires ALL tags to match, so too many tags = no results (womp womp), pre-build tag sets to try to get a result
    tag_count = len(tags)
    if tag_count == 0:
        return None
    
    tag_sets_to_try = [tags]
    if tag_count > 3:
        tag_sets_to_try.append(tags[:3])
    if tag_count > 1:
        tag_sets_to_try.append([random.choice(tags)])
    
    # Pre-build base params (is_nsfw doesn't change)
    base_params = {}
    if is_nsfw:
        base_params['is_nsfw'] = 'true'
    
    for attempt_tags in tag_sets_to_try:
        params = {**base_params, 'included_tags': attempt_tags}
        
        try:
            response = _session.get(API_URL, params=params, timeout=10)
            
            if response.status_code == 404:
                continue
                
            response.raise_for_status()
            data = response.json()
            
            images = data.get('images')
            if images:
                if attempt_tags != tags:
                    print(f"No images found with all selected tags. Using: {', '.join(attempt_tags)}")
                return images[0]['url']
                
        except requests.HTTPError as e:
            if e.response.status_code != 404:
                print(f"API Request failed: {e}")
                return None
        except requests.RequestException as e:
            print(f"API Request failed: {e}")
            return None
    
    print("No images found matching any of the selected tags.")
    return None

def select_color_mode() -> bool:
    """Ask user for color preference."""
    choice = questionary.select(
        "Select output mode:",
        choices=["Grayscale (Detailed B&W)", "Color (Original Colors)"],
        default="Grayscale (Detailed B&W)"
    ).ask()
    return choice == "Color (Original Colors)"

def get_image_dimensions(image_path: str) -> Tuple[int, int]:
    """Get image width and height."""
    try:
        with Image.open(image_path) as img:
            return img.size
    except Exception:
        return (1, 1)

def convert_to_ascii(image_url: str, height: int, is_color: bool):
    """Download image and convert to Braille ASCII using external tool."""
    ext = os.path.splitext(image_url)[1] or '.jpg'
    temp_path = None
    
    try:
        with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as temp_img:
            temp_path = temp_img.name
            response = _session.get(image_url, stream=True, timeout=30)
            response.raise_for_status()
            
            for chunk in response.iter_content(chunk_size=8192):
                temp_img.write(chunk)
        
        # Preprocess image for better ASCII detail: contrast + sharpening
        with Image.open(temp_path) as img:
            # Enhance contrast for better feature distinction
            contrast_enhancer = ImageEnhance.Contrast(img)
            img = contrast_enhancer.enhance(1.1)
            
            # Sharpen edges for better character definition
            sharpness_enhancer = ImageEnhance.Sharpness(img)
            img = sharpness_enhancer.enhance(1.2)
            
            img.save(temp_path, quality=95)
        
        img_width, img_height = get_image_dimensions(temp_path)
        aspect_ratio = img_width / img_height if img_height > 0 else 1.0
        
        # some math to get the width of the ASCII output, braille chars are actually ~2:1 (width:height)
        width = int(height * aspect_ratio * 2.5)
        width = max(width, int(height * 1.7))
        
        max_height = 60
        max_width = 120
        height = min(height, max_height)
        width = min(width, max_width)
        
        cmd = [
            'ascii-image-converter', temp_path,
            '--dimensions', f'{width},{height}',
            '--braille', '--dither'
        ]
        cmd.append('--color' if is_color else '--grayscale')
        
        subprocess.run(cmd, check=True)
        
    except FileNotFoundError:
        print("Error: 'ascii-image-converter' not found. Please install it first.")
    except subprocess.CalledProcessError as e:
        print(f"Conversion failed: {e}")
    except requests.RequestException as e:
        print(f"Failed to download image: {e}")
    except ImportError:
        print("Error: 'Pillow' not found. Install it with: pip install Pillow")
    finally:
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)

def main():
    print("ascii-waifu, turning anime images into ascii art")
    
    # 1. Get Preferences
    selection = select_tags()
    if not selection['tags']:
        print("No tags selected. Exiting.")
        return

    ascii_height = select_height()
    is_color = select_color_mode()

    # 2. Fetch Image
    print("Fetching waifu...")
    image_url = fetch_waifu(selection['tags'], selection['is_nsfw'])
    
    if image_url:
        print(f"Found image: {image_url}")
        # 3. Convert
        convert_to_ascii(image_url, ascii_height, is_color)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nCya, exiting...")
        sys.exit(0)
