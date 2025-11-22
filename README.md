# ascii-waifu

#### A Python TUI tool that fetches anime character images from [waifu.im](https://waifu.im) and converts them to ASCII art in your terminal.

<sub>i dont know why i made this, boredom gets you places.</sub>

## Showcase

<video src="./readme-assets/showcase.mp4" controls width="45%"></video>

## Prerequisites

- ![Python](https://img.shields.io/badge/python-3.8+-blue.svg?style=for-the-badge&logo=python&logoColor=white)
- [![ascii-image-converter](https://img.shields.io/badge/ascii--image--converter-blueviolet?style=for-the-badge)](https://github.com/TheZoraiz/ascii-image-converter) (External tool required for conversion)

### Installing ascii-image-converter

First, make sure you have `ascii-image-converter` installed and that its accessible from your terminal.

**Arch Linux (AUR):**
```bash
yay -S ascii-image-converter
# or
paru -S ascii-image-converter
```

**Debian/Ubuntu:**
Check the [official repo](https://github.com/TheZoraiz/ascii-image-converter) for .deb packages or install via Go.

## Installation

1. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

Run the script directly:
```bash
python main.py
```

### (Optional) Make it a Terminal Alias

You can make an alias so you can just run `ascii-waifu` from your terminal:

1. Add this to your `~/.bashrc`, `~/.zshrc`, or equivalent shell config:
   ```bash
   alias ascii-waifu="/full/path/to/the/project/venv/bin/python /full/path/to/the/project/main.py"
   ```
   _(Replace `/full/path/to/the/project` with the real path)_
   
   This uses the Python interpreter from the venv, so all the installed/needed packages will be available.

2. Reload your shell config (or open a new terminal):
   ```bash
   source ~/.bashrc      # For bash
   # or
   source ~/.zshrc       # For zsh
   ```
3. Now you can run:
   ```bash
   ascii-waifu
   ```

### How the tag selection works

Tags use **AND logic**: the image must have **all** the tags you pick.

- Choosing more tags = harder to find a match
- Fewer tags = more results

So, incase no images match all your selected tags, the tool automatically tries use a **Fallback System**
- You'll see a message if it falls back to fewer tags: `"No images found with all selected tags. Using: tag1, tag2"`

## Credits
- API provided by [waifu.im](https://waifu.im)
- ASCII conversion by [ascii-image-converter](https://github.com/TheZoraiz/ascii-image-converter)
