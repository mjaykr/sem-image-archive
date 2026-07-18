from pathlib import Path

from PIL import Image

from sem_image_archive import cli
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


def test_del_removes_sources_only_after_archive_success(tmp_path: Path, monkeypatch):
    source = tmp_path / "source.tif"
    output_dir = tmp_path / "output"
    archive = tmp_path / "images.7z"
    Image.new("RGB", (2, 2), (7, 7, 7)).save(source)

    def fake_archive(_output_dir, archive_path):
        archive_path.write_bytes(b"verified archive")
        return "7z"

    monkeypatch.setattr(cli, "create_archive", fake_archive)

    result = cli.main(
        ["-i", str(tmp_path), "-o", str(output_dir), "-a", str(archive), "--del"]
    )

    assert result == 0
    assert not source.exists()
    assert (output_dir / "source.tif").exists()
    assert archive.exists()


def test_del_keeps_sources_when_archive_fails(tmp_path: Path, monkeypatch):
    source = tmp_path / "source.tif"
    output_dir = tmp_path / "output"
    archive = tmp_path / "images.7z"
    Image.new("RGB", (2, 2), (7, 7, 7)).save(source)

    def failed_archive(_output_dir, _archive_path):
        raise RuntimeError("archive failed")

    monkeypatch.setattr(cli, "create_archive", failed_archive)

    result = cli.main(
        ["-i", str(tmp_path), "-o", str(output_dir), "-a", str(archive), "--del"]
    )

    assert result == 1
    assert source.exists()


def test_7z_only_leaves_only_archive(tmp_path: Path, monkeypatch):
    source = tmp_path / "source.tif"
    output_dir = tmp_path / "output"
    archive = tmp_path / "images.7z"
    Image.new("RGB", (2, 2), (7, 7, 7)).save(source)

    def fake_archive(_output_dir, archive_path):
        archive_path.write_bytes(b"verified archive")
        return "7z"

    monkeypatch.setattr(cli, "create_archive", fake_archive)

    result = cli.main(
        ["-i", str(tmp_path), "-o", str(output_dir), "-a", str(archive), "--7z-only"]
    )

    assert result == 0
    assert archive.exists()
    assert not source.exists()
    assert not output_dir.exists()


def test_7z_only_rejects_archive_inside_output(tmp_path: Path):
    source = tmp_path / "source.tif"
    output_dir = tmp_path / "output"
    Image.new("RGB", (2, 2), (7, 7, 7)).save(source)

    result = cli.main(
        [
            "-i",
            str(tmp_path),
            "-o",
            str(output_dir),
            "-a",
            str(output_dir / "images.7z"),
            "--7z-only",
        ]
    )

    assert result == 2
    assert source.exists()
