# ascii-waifu

#### A Python TUI tool that fetches anime character images from [waifu.im](https://waifu.im) and converts them to ASCII art in your terminal.

<sub>i dont know why i made this, boredom gets you places.</sub>

## Prerequisites

1. **Python 3**
2. **ascii-image-converter** (External tool required for conversion)

### Installing ascii-image-converter

You need to install `ascii-image-converter` and ensure it's in your system PATH.

**Arch Linux (AUR):**
```bash
yay -S ascii-image-converter
# or
paru -S ascii-image-converter
```

**Debian/Ubuntu:**
Check the [official repo](https://github.com/TheZoraiz/ascii-image-converter) for .deb packages or install via Go.

**MacOS:**
```bash
brew install ascii-image-converter
```

**Windows:**
Use `scoop` or download the executable from the releases page.

## Installation

1. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   # venv\Scripts\activate   # Windows
   ```

2. Install dependencies:
   ```bash
   pip install requests questionary
   ```

## Usage

Run the script directly:
```bash
python main.py
```

### (Optional) Make a Terminal Alias

#### Arch Linux / Linux / macOS

You can make an alias so you can just run `ascii-waifu` from your terminal:

1. (Make sure your terminal is in the project folder)
2. Add this to your `~/.bashrc`, `~/.zshrc`, or equivalent shell config:
   ```bash
   alias ascii-waifu="/full/path/to/the/project/venv/bin/python /full/path/to/the/project/main.py"
   ```
   _(Replace `/full/path/to/the/project` with the real path)_
   
   This uses the Python interpreter from the venv, so all your installed packages will be available.

3. Reload your shell config (or open a new terminal):
   ```bash
   source ~/.bashrc      # For bash
   # or
   source ~/.zshrc       # For zsh
   ```
4. Now you can run:
   ```bash
   ascii-waifu
   ```

#### System-wide Command (Linux advanced)

Alternatively, symlink a simple shell launcher to somewhere on your PATH:
```bash
echo '/full/path/to/the/project/venv/bin/python /full/path/to/the/project/main.py "$@"' > ~/ascii-waifu
chmod +x ~/ascii-waifu
sudo mv ~/ascii-waifu /usr/local/bin/ascii-waifu
```
_(Replace `/full/path/to/the/project` with the real path)_

Then you can run `ascii-waifu` from anywhere.

_The tool will launch its TUI as soon as you run the command!_

### Features
- **Interactive TUI**: Select between Versatile (SFW (safe for work)) and NSFW modes.
- **Tag Selection**: Choose specific characters or themes.
- **Custom Height**: Adjust the size of the ASCII output.
- **Modes**: Choose between Detailed Grayscale or Original Color output.

### How Tag Selection Works

**Important**: The tag system uses **AND logic** (filter system), not OR logic. so, this means:

- **All selected tags must match** - The API searches for images that have **every** tag you select
- **More tags = more specific = fewer results** - Selecting 9 tags means you need an image with all 9 tags, which is very unlikely
- **Fewer tags = more results** - Selecting 1-3 tags gives you the best chance of finding images

So, incase no images match all your selected tags, the tool automatically tries use a **Fallback System**
- You'll see a message if it falls back to fewer tags: `"No images found with all selected tags. Using: tag1, tag2"`

## Credits
- API provided by [waifu.im](https://waifu.im)
- ASCII conversion by [ascii-image-converter](https://github.com/TheZoraiz/ascii-image-converter)
