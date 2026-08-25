# pixa

Convert any image into a dot-style wallpaper.

## Install

```bash
pip install .
```

Or run directly:

```bash
python pixa.py input.jpg
```

## Usage

```bash
# Basic usage (output = input resolution, black background)
pixa image.jpg -o wallpaper.png

# Custom resolution
pixa image.jpg -o wallpaper.png -w 1920 -ht 1080

# Color mode (keep original colors)
pixa image.jpg -o wallpaper.png --color

# Auto-remove background
pixa image.jpg -o wallpaper.png --no-background

# Custom colors
pixa image.jpg -o wallpaper.png --bg "#131313" --text-color "#f5c2e7"
```

## Options

| Option | Default | Description |
|--------|---------|-------------|
| `-o, --output` | `output.png` | Output file |
| `-w, --width` | input width | Output width in px |
| `-ht, --height` | input height | Output height in px |
| `-d, --dot-size` | `7` | Spacing between dots |
| `-r, --radius` | `3.2` | Max dot radius |
| `-th, --threshold` | `25` | Min brightness to render |
| `--bg` | `#000000` | Background color |
| `--text-color` | `#ffffff` | Dot color (white mode) |
| `--color` | off | Use original image colors |
| `--no-background` | off | Auto-detect and remove background |

## Examples

```bash
# White dots on black, 1920x1080
pixa photo.jpg -o wall.png -w 1920 -ht 1080

# Colored dots with background removal
pixa anime.jpg -o wall.png --color --no-background

# Pink dots on dark background
pixa photo.jpg -o wall.png --text-color "#f5c2e7" --bg "#131313"
```

## License

MIT
