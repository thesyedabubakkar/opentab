import asyncio
from pathlib import Path
from PIL import Image, ImageDraw
import sys

# Ensure project root in sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

from tools.nano_banana_engine import nano_banana_engine
from tools.github_inswapper import github_inswapper

async def test_nano_banana_face_replacement(tmp_path: Path):
    # Create a synthetic target image with a face-like area
    target_img = tmp_path / "target_car_scene.jpg"
    base = Image.new("RGB", (600, 800), color=(180, 140, 100)) # desert-like background
    draw = ImageDraw.Draw(base)
    # Draw a simulated car body
    draw.rectangle([50, 450, 550, 750], fill=(20, 20, 20))
    # Draw a simulated head
    draw.ellipse([250, 100, 370, 250], fill=(210, 170, 130))
    base.save(target_img, "JPEG")

    # Run Nano Banana inpainting / character replacement
    out_img = tmp_path / "result.jpg"
    res = await nano_banana_engine.inpaint_character(
        target_image_path=target_img,
        character_desc="handsome stylish young man, dark wavy hair, groomed full beard, aviator sunglasses",
        user_id="test_user_42",
        output_path=out_img
    )

    assert res.exists(), "Output image was not created!"
    assert res.stat().st_size > 0, "Output image is empty!"
    with Image.open(res) as out_im:
        assert out_im.size == (600, 800), f"Expected size (600, 800), got {out_im.size}"
    print("PASS: test_nano_banana_face_replacement")

async def test_github_inswapper_direct(tmp_path: Path):
    target = tmp_path / "target.jpg"
    source = tmp_path / "source.jpg"
    Image.new("RGB", (400, 600), (100, 150, 200)).save(target)
    Image.new("RGB", (200, 200), (220, 180, 140)).save(source)

    out = tmp_path / "swapped.jpg"
    res = github_inswapper.swap_face(target, source, out)
    assert res.exists(), "Swapped image does not exist!"
    assert res.stat().st_size > 100, "Swapped image is too small!"
    print("PASS: test_github_inswapper_direct")

if __name__ == "__main__":
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        p = Path(td)
        asyncio.run(test_github_inswapper_direct(p))
        asyncio.run(test_nano_banana_face_replacement(p))
    print("ALL TESTS PASSED SUCCESSFULLY!")
