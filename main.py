import requests, questionary, subprocess, tempfile, os, sys, random, time, re
from dataclasses import dataclass
from typing import List, Optional, Tuple, Union
from PIL import Image, ImageEnhance

try:
    from rich.console import Console
    from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, DownloadColumn, TransferSpeedColumn
    from rich.panel import Panel
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False
    class Console:
        def print(self, text="", **kwargs): print(re.sub(r'\[.*?\]', '', text))
        def status(self, text): return type('Status', (), {'__enter__': lambda s: s, '__exit__': lambda s, *a: None})()
    class Progress:
        def __init__(self, *args, **kwargs): pass
        def __enter__(self): return self
        def __exit__(self, *args): pass
        def add_task(self, *args, **kwargs): return 0
        def update(self, *args, **kwargs): pass
    class Panel:
        @staticmethod
        def fit(text, **kwargs): return text
    SpinnerColumn = TextColumn = BarColumn = DownloadColumn = TransferSpeedColumn = None

API_URL = 'https://api.waifu.im/search'
API_TIMEOUT, DOWNLOAD_TIMEOUT = 10, 30
MAX_RETRIES, RETRY_DELAY_BASE = 3, 1.0
CONTRAST_FACTOR, SHARPNESS_FACTOR, IMAGE_QUALITY, CHUNK_SIZE = 1.1, 1.2, 95, 8192
BRAILLE_ASPECT_RATIO, MIN_WIDTH_MULTIPLIER = 2.5, 1.7
MAX_ASCII_HEIGHT, MAX_ASCII_WIDTH = 60, 120
DEFAULT_ASCII_HEIGHT, MIN_ASCII_HEIGHT, MAX_ASCII_HEIGHT_INPUT = 50, 10, 200
TAG_FALLBACK_THRESHOLD = 3
VERSATILE_TAGS = ['waifu', 'maid', 'marin-kitagawa', 'mori-calliope', 'raiden-shogun', 'oppai', 'selfies', 'uniform', 'kamisato-ayaka']
NSFW_TAGS = ['ero', 'ass', 'hentai', 'milf', 'oral', 'paizuri', 'ecchi']

console = Console()
_session = requests.Session()

@dataclass
class TagSelection:
    tags: List[str]
    is_nsfw: bool

@dataclass
class ImageConfig:
    height: int
    is_color: bool

def select_tags() -> Optional[TagSelection]:
    mode = questionary.select("Select content type:", choices=["Versatile (Safe/Mixed)", "NSFW (18+)"]).ask()
    if not mode: return None
    tags = questionary.checkbox("Select tags:", choices=NSFW_TAGS if mode == "NSFW (18+)" else VERSATILE_TAGS).ask()
    return TagSelection(tags=tags, is_nsfw=mode == "NSFW (18+)") if tags else None

def select_height() -> Optional[int]:
    validate = lambda t: True if t.isdigit() and MIN_ASCII_HEIGHT <= int(t) <= MAX_ASCII_HEIGHT_INPUT else f"Enter a number between {MIN_ASCII_HEIGHT} and {MAX_ASCII_HEIGHT_INPUT}"
    return int(h) if (h := questionary.text(f"Enter ASCII height (default: {DEFAULT_ASCII_HEIGHT}, higher = more detail):", default=str(DEFAULT_ASCII_HEIGHT), validate=validate).ask()) else None

def select_color_mode() -> Optional[bool]:
    return (c == "Color (Original Colors)") if (c := questionary.select("Select output mode:", choices=["Grayscale (Detailed B&W)", "Color (Original Colors)"], default="Grayscale (Detailed B&W)").ask()) else None

def build_tag_fallback_sets(tags: List[str]) -> List[List[str]]:
    return [tags] + ([tags[:TAG_FALLBACK_THRESHOLD]] if len(tags) > TAG_FALLBACK_THRESHOLD else []) + ([[random.choice(tags)]] if len(tags) > 1 else [])

def fetch_waifu_with_retry(tags: List[str], is_nsfw: bool) -> Optional[str]:
    for attempt_tags in build_tag_fallback_sets(tags):
        params = {'is_nsfw': 'true' if is_nsfw else None, 'included_tags': attempt_tags}
        params = {k: v for k, v in params.items() if v}
        for attempt in range(MAX_RETRIES):
            try:
                response = _session.get(API_URL, params=params, timeout=API_TIMEOUT)
                if response.status_code == 404: break
                response.raise_for_status()
                if images := response.json().get('images'):
                    if attempt_tags != tags:
                        console.print(f"[yellow]No images found with all selected tags. Using: {', '.join(attempt_tags)}[/yellow]")
                    return images[0]['url']
            except (requests.HTTPError, requests.RequestException) as e:
                if isinstance(e, requests.HTTPError) and e.response and e.response.status_code == 404: break
                if attempt < MAX_RETRIES - 1:
                    time.sleep(RETRY_DELAY_BASE * (2 ** attempt))
                    continue
                console.print(f"[red]API request failed: {e}[/red]")
                return None
    console.print("[red]No images found matching any of the selected tags.[/red]")
    return None

def calculate_ascii_dimensions(image_path: str, target_height: int) -> Tuple[int, int]:
    try:
        with Image.open(image_path) as img:
            aspect_ratio = img.width / img.height if img.height > 0 else 1.0
    except Exception:
        aspect_ratio = 1.0
    width = max(int(target_height * aspect_ratio * BRAILLE_ASPECT_RATIO), int(target_height * MIN_WIDTH_MULTIPLIER))
    return min(width, MAX_ASCII_WIDTH), min(target_height, MAX_ASCII_HEIGHT)

def preprocess_image(image_path: str) -> None:
    try:
        with Image.open(image_path) as img:
            img = ImageEnhance.Sharpness(ImageEnhance.Contrast(img).enhance(CONTRAST_FACTOR)).enhance(SHARPNESS_FACTOR)
            if img.format == 'PNG':
                img.save(image_path, format='PNG', optimize=True)
            else:
                (img if img.mode == 'RGB' else img.convert('RGB')).save(image_path, format='JPEG', quality=IMAGE_QUALITY, optimize=True)
    except Exception as e:
        console.print(f"[yellow]Warning: Image preprocessing failed: {e}[/yellow]")

def download_image(image_url: str, temp_path: str) -> None:
    try:
        response = _session.get(image_url, stream=True, timeout=DOWNLOAD_TIMEOUT)
        response.raise_for_status()
        if RICH_AVAILABLE and SpinnerColumn:
            with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), BarColumn(), DownloadColumn(), TransferSpeedColumn(), console=console) as progress:
                task = progress.add_task("[cyan]Downloading...", total=int(response.headers.get('content-length', 0)))
                with open(temp_path, 'wb') as f:
                    [f.write(chunk) or progress.update(task, advance=len(chunk)) for chunk in response.iter_content(chunk_size=CHUNK_SIZE) if chunk]
        else:
            console.print("Downloading image...")
            with open(temp_path, 'wb') as f:
                f.write(response.content)
    except requests.RequestException as e:
        raise RuntimeError(f"Failed to download image: {e}") from e

def convert_to_ascii(image_url: str, config: ImageConfig) -> None:
    ext = os.path.splitext(image_url)[1] or '.jpg'
    temp_path = None
    try:
        with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as temp_img:
            temp_path = temp_img.name
        download_image(image_url, temp_path)
        with console.status("[cyan]Processing image..."):
            preprocess_image(temp_path)
        width, height = calculate_ascii_dimensions(temp_path, config.height)
        console.print("[cyan]Converting to ASCII...[/cyan]")
        subprocess.run(['ascii-image-converter', temp_path, '--dimensions', f'{width},{height}', '--braille', '--dither', '--color' if config.is_color else '--grayscale'], check=True)
    except FileNotFoundError:
        console.print("[red]Error: 'ascii-image-converter' not found. Install it first.[/red]\n[yellow]See README.md for installation instructions.[/yellow]")
    except subprocess.CalledProcessError as e:
        console.print(f"[red]Conversion failed: {e}[/red]")
    except (RuntimeError, ImportError) as e:
        console.print(f"[red]{e}[/red]")
    finally:
        if temp_path and os.path.exists(temp_path):
            try: os.remove(temp_path)
            except OSError: pass

def main() -> None:
    console.print(Panel.fit("[bold cyan]ascii-waifu[/bold cyan] - turning anime images into ascii art", border_style="cyan"))
    if not (selection := select_tags()) or not selection.tags:
        console.print("[yellow]No tags selected. Exiting.[/yellow]")
        return
    if not (ascii_height := select_height()) or (is_color := select_color_mode()) is None:
        console.print("[yellow]Invalid input. Exiting.[/yellow]")
        return
    with console.status("[cyan]Fetching waifu..."):
        image_url = fetch_waifu_with_retry(selection.tags, selection.is_nsfw)
    if image_url:
        console.print(f"[green]Found image:[/green] {image_url}")
        convert_to_ascii(image_url, ImageConfig(height=ascii_height, is_color=is_color))
    else:
        console.print("[red]Failed to fetch image.[/red]")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        console.print("\n[yellow]Cya, exiting...[/yellow]")
        sys.exit(0)
