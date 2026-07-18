from pathlib import Path

from PIL import Image

from sem_image_archive.cli import convert_image, image_is_grayscale


def test_equal_rgb_channels_are_grayscale(tmp_path: Path):
    source = tmp_path / "source.tif"
    output = tmp_path / "output.tif"
    image = Image.new("RGB", (12, 8), (123, 123, 123))
    image.save(source)

    was_grayscale, size = convert_image(source, output)

    assert was_grayscale is True
    assert size == (12, 8)
    with Image.open(output) as converted:
        assert converted.mode == "L"
        assert converted.size == (12, 8)
        assert converted.getpixel((0, 0)) == 123


def test_unequal_rgb_channels_are_detected(tmp_path: Path):
    image = Image.new("RGB", (2, 2), (255, 0, 0))
    assert image_is_grayscale(image) is False
