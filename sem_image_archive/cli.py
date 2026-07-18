"""Command-line interface for SEM image archiving."""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageChops


SUPPORTED_EXTENSIONS = {".tif", ".tiff"}


def find_images(input_dir: Path) -> list[Path]:
    """Return source TIFFs, excluding generated output directories."""
    return sorted(
        path
        for path in input_dir.iterdir()
        if path.is_file()
        and path.suffix.lower() in SUPPORTED_EXTENSIONS
        and not path.name.startswith(".")
    )


def image_is_grayscale(image: Image.Image) -> bool:
    """Return whether all RGB channels contain identical pixel values."""
    if image.mode in {"1", "L", "I", "F", "I;16", "I;16B", "I;16L"}:
        return True
    if image.mode not in {"RGB", "RGBA"}:
        return False

    rgb = image.convert("RGB")
    red, green, blue = rgb.split()
    return ImageChops.difference(red, green).getbbox() is None and ImageChops.difference(
        red, blue
    ).getbbox() is None


def convert_image(source: Path, destination: Path) -> tuple[bool, tuple[int, int]]:
    """Convert one image to an 8-bit grayscale TIFF.

    Returns whether the source was already channel-equivalent grayscale and the
    output dimensions.
    """
    with Image.open(source) as image:
        was_grayscale = image_is_grayscale(image)
        grayscale = image.convert("L")
        save_options = {"format": "TIFF", "compression": "tiff_adobe_deflate"}
        if "icc_profile" in image.info:
            save_options["icc_profile"] = image.info["icc_profile"]
        grayscale.save(destination, **save_options)
        return was_grayscale, grayscale.size


def find_7z() -> str:
    """Find a 7-Zip executable on PATH."""
    for name in ("7z", "7zz", "7za"):
        executable = shutil.which(name)
        if executable:
            return executable
    raise RuntimeError("7-Zip was not found. Install 7-Zip and add it to PATH.")


def create_archive(output_dir: Path, archive_path: Path) -> str:
    """Create and test a solid maximum-compression 7z archive."""
    executable = find_7z()
    archive_path.parent.mkdir(parents=True, exist_ok=True)
    files = sorted(output_dir.glob("*.tif")) + sorted(output_dir.glob("*.tiff"))
    if not files:
        raise RuntimeError(f"No converted TIFF files found in {output_dir}")

    command = [
        executable,
        "a",
        "-y",
        "-t7z",
        "-mx=9",
        "-m0=lzma2",
        "-mmt=on",
        "-ms=on",
        "-mfb=273",
        "-md=64m",
        str(archive_path),
        "*.tif",
        "*.tiff",
    ]
    result = subprocess.run(command, cwd=output_dir, text=True, capture_output=True)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip() or "7-Zip failed")

    test = subprocess.run(
        [executable, "t", "-y", str(archive_path)],
        text=True,
        capture_output=True,
    )
    if test.returncode != 0:
        raise RuntimeError(test.stderr.strip() or test.stdout.strip() or "Archive test failed")
    return executable


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Convert SEM TIFFs to true 8-bit grayscale TIFFs and archive them."
    )
    parser.add_argument(
        "-i",
        "--input-folder",
        type=Path,
        default=Path.cwd(),
        help="Folder containing source TIFFs (default: current folder).",
    )
    parser.add_argument(
        "-o",
        "--output-folder",
        type=Path,
        default=None,
        help="Output folder (default: <input>/grayscale_8bit).",
    )
    parser.add_argument(
        "-a",
        "--archive",
        type=Path,
        default=None,
        help="Archive path (default: beside input folder).",
    )
    parser.add_argument(
        "--reject-color",
        action="store_true",
        help="Stop if any input has unequal RGB channels instead of converting luminance.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Allow replacing existing converted TIFFs and archives.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    input_dir = args.input_folder.expanduser().resolve()
    if not input_dir.is_dir():
        print(f"Error: input folder does not exist: {input_dir}", file=sys.stderr)
        return 2

    output_dir = (args.output_folder or input_dir / "grayscale_8bit").expanduser().resolve()
    archive_path = (
        args.archive
        or input_dir / f"{input_dir.name}_grayscale_8bit.7z"
    ).expanduser().resolve()
    images = find_images(input_dir)
    if not images:
        print(f"Error: no TIFF files found in {input_dir}", file=sys.stderr)
        return 2
    if archive_path.exists() and not args.overwrite:
        print(f"Error: archive already exists; use --overwrite: {archive_path}", file=sys.stderr)
        return 2

    output_dir.mkdir(parents=True, exist_ok=True)
    converted = 0
    luminance_converted = 0
    try:
        for source in images:
            destination = output_dir / source.name
            if destination.exists() and not args.overwrite:
                print(f"Error: output already exists; use --overwrite: {destination}", file=sys.stderr)
                return 2
            with Image.open(source) as image:
                source_is_grayscale = image_is_grayscale(image)
            if args.reject_color and not source_is_grayscale:
                print(f"Error: non-grayscale RGB image: {source.name}", file=sys.stderr)
                return 2
            was_grayscale, size = convert_image(source, destination)
            converted += 1
            if not was_grayscale:
                luminance_converted += 1
            print(f"Converted {source.name} -> {destination.name} ({size[0]}x{size[1]})")

        executable = create_archive(output_dir, archive_path)
    except (OSError, RuntimeError, ValueError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1

    input_bytes = sum(path.stat().st_size for path in images)
    archive_bytes = archive_path.stat().st_size
    ratio = archive_bytes / input_bytes if input_bytes else 0
    print(f"\nConverted: {converted} TIFFs")
    if luminance_converted:
        print(f"Warning: luminance-converted non-equivalent RGB images: {luminance_converted}")
    print(f"Output:    {output_dir}")
    print(f"Archive:   {archive_path}")
    print(f"7-Zip:     {executable}")
    print(f"Archive/input size: {ratio:.1%}")
    print("Archive test: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
