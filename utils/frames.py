from PIL import Image, ImageDraw
from io import BytesIO
from textwrap import wrap
from urllib.request import urlopen
import base64


def generate_frame_for_queue_item(qi):
    cover_img = qi["image"]

    cover_img = Image.open(urlopen(cover_img)).convert("RGBA")
    img = Image.new("RGBA", cover_img.size, (0, 0, 0, 255))

    content = wrap(qi["name"], 25)
    line_count = len(content)
    content = "\n".join(content)

    draw = ImageDraw.Draw(img)
    draw.rectangle(((0, 0), cover_img.size), fill=(0, 0, 0, 0))
    draw.rectangle(
        ((0, cover_img.size[0] - 50 - 24 - 48 * line_count - 30), cover_img.size),
        fill=(0, 0, 0, int(0.9 * 255)),
    )
    draw.multiline_text(
        (50, cover_img.size[0] - 50 - 24 - 48 * line_count - 12), content, font_size=48
    )
    draw.multiline_text((50, cover_img.size[0] - 50 - 12), qi["artists"], font_size=24)

    img = Image.alpha_composite(cover_img, img).convert("RGB")
    # img.save("tmp/frame.jpeg", format="JPEG", optimize=True)

    buffer = BytesIO()
    img.save(buffer, format="JPEG", optimize=True)
    img_buffer = buffer.getvalue()

    return "data:image/jpeg;base64," + base64.b64encode(img_buffer).decode()
