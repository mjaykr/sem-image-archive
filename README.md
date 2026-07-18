# SEM Image Archive

Convert RGB TIFF files that are visually grayscale into true 8-bit grayscale TIFFs, then store the converted images in a maximum-compression 7-Zip archive.

Original images are never modified or deleted.

## Requirements

- Python 3.9 or newer
- [7-Zip](https://www.7-zip.org/) available as `7z`, `7zz`, or `7za` on `PATH`

The Python dependency is Pillow. ImageMagick is not required.

## Installation

### Recommended: isolated command with pipx

```powershell
py -m pip install --user pipx
py -m pipx ensurepath
pipx install git+https://github.com/<your-user>/sem-image-archive.git
```

Restart PowerShell after `ensurepath`, then verify:

```powershell
sem-archive --help
```

### From a local clone

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e .
```

For development and tests:

```powershell
python -m pip install -r requirements-dev.txt
pytest
```

### PowerShell profile helper

After cloning, the optional installer adds a `sem-archive` function to the current user's PowerShell profile:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\install.ps1
```

Open a new PowerShell session after installation. The command accepts an explicit folder, so it works from any drive.

## Usage

Process the current folder:

```powershell
sem-archive
```

Process another folder:

```powershell
sem-archive -i "G:\Shared drives\Mirtunjay Data\SEM Images\Zr doped"
```

Specify output and archive paths:

```powershell
sem-archive `
  -i "G:\SEM\Zr doped" `
  -o "G:\SEM\Zr doped\grayscale_8bit" `
  -a "G:\SEM\Zr doped\Zr-doped.7z"
```

By default, the program:

1. Reads `.tif` and `.tiff` files directly inside the input folder.
2. Writes 8-bit grayscale TIFFs into `<input>\grayscale_8bit`.
3. Creates `<input>\<folder-name>_grayscale_8bit.7z`.
4. Tests the completed archive with 7-Zip.

Existing outputs are protected. Use `--overwrite` only when replacement is intentional.

To delete the original TIFFs after the converted files have been archived and
the archive has passed its integrity test, add `--del`:

```powershell
sem-archive --del -i "G:\SEM\Zr doped"
```

Without `--del`, source files are always retained. If conversion or archive
verification fails, source files are never deleted.

## Image handling

RGB images with identical channels are converted directly to grayscale. If an RGB image has unequal channels, Pillow's luminance conversion is used and a warning is printed. To stop instead of converting such an image, use:

```powershell
sem-archive --reject-color
```

The output TIFFs use 8-bit `L` mode and Deflate compression. The archive uses solid LZMA2 compression with maximum settings (`-mx=9`).

## Options

| Option | Description |
| --- | --- |
| `-i`, `--input-folder` | Source folder; defaults to the current folder |
| `-o`, `--output-folder` | Converted TIFF folder |
| `-a`, `--archive` | Output `.7z` path |
| `--reject-color` | Stop on unequal RGB channels |
| `--overwrite` | Replace existing converted TIFFs and archive |
| `--del` | Delete source TIFFs after successful archive verification |
| `-h`, `--help` | Show command help |

## Development

```powershell
git clone https://github.com/<your-user>/sem-image-archive.git
cd sem-image-archive
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements-dev.txt
pytest
python -m sem_image_archive.cli --help
```

## License

MIT. See [LICENSE](LICENSE).
