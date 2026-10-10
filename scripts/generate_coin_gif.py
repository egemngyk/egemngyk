
from pathlib import Path
import math

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "source.png"
OUTPUT_DIR = ROOT / "assets"
CIRCLE_OUTPUT = OUTPUT_DIR / "circle.png"
GIF_OUTPUT = OUTPUT_DIR / "coin-spin.gif"

SIZE = 512
FRAMES = 72
FRAME_DURATION = 60
ROTATION_STEPS = FRAMES // 2


def create_circle(source: Image.Image) -> Image.Image:
    width, height = source.size
    side = min(width, height)
    left = (width - side) // 2
    top = (height - side) // 2

    image = source.crop(
        (left, top, left + side, top + side)
    ).resize((SIZE, SIZE), Image.Resampling.LANCZOS)

    mask = Image.new("L", (SIZE, SIZE), 0)
    ImageDraw.Draw(mask).ellipse(
        (0, 0, SIZE - 1, SIZE - 1), fill=255
    )
    image.putalpha(mask)
    return image


def create_coin_frame(
    front: Image.Image,
    angle: float,
) -> Image.Image:
    # Perspektif etkisi: yatay eksende daralıp genişler.
    scale_x = abs(math.cos(angle))
    width = max(1, round(SIZE * scale_x))

    # Arka yüzü, yarım dönüşten sonra aynalayarak göster.
    face = front
    if math.cos(angle) < 0:
        face = front.transpose(Image.Transpose.FLIP_LEFT_RIGHT)

    face = face.resize(
        (width, SIZE), Image.Resampling.LANCZOS
    )

    frame = Image.new("RGBA", (SIZE, SIZE), color=(0, 0, 0, 0))
    x = (SIZE - width) // 2
    frame.alpha_composite(face, (x, 0))

    return frame


def main():
    if not SOURCE.is_file():
        raise FileNotFoundError(
            f"Kaynak görsel bulunamadı: {SOURCE}"
        )

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    source = Image.open(SOURCE).convert("RGBA")
    circle = create_circle(source)
    circle.save(CIRCLE_OUTPUT)

    frames = []
    for index in range(FRAMES):
        angle = 2 * math.pi * index / FRAMES
        frames.append(create_coin_frame(circle, angle))

    # GIF'in şeffaflığını koru.
    gif_frames = []
    for frame in frames:
        rgba = frame.convert("RGBA")
        palette = Image.new("P", rgba.size)
        palette.putpalette(
            [0, 0, 0, 255, 255, 255] + [0, 0, 0] * 254
        )

        # RGBA -> paletli GIF; şeffaf pikselleri ayrı indeksle.
        alpha = rgba.getchannel("A")
        rgb = rgba.convert("RGB")
        quantized = rgb.quantize(colors=255)
        quantized = quantized.convert("P")

        palette_data = quantized.getpalette()
        if palette_data is None:
            palette_data = [0] * 768

        quantized.putpalette(palette_data[:768])
        quantized.info["transparency"] = 255

        alpha_mask = alpha.point(lambda value: 255 if value < 128 else 0)
        quantized.paste(255, mask=alpha_mask)
        gif_frames.append(quantized)

    gif_frames[0].save(
        GIF_OUTPUT,
        save_all=True,
        append_images=gif_frames[1:],
        duration=FRAME_DURATION,
        loop=0,
        disposal=2,
        transparency=255,
        optimize=False,
    )

    print(f"PNG oluşturuldu: {CIRCLE_OUTPUT.relative_to(ROOT)}")
    print(f"GIF oluşturuldu: {GIF_OUTPUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
