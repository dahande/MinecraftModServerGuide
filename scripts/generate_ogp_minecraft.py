#!/usr/bin/env python3
"""
Minecraft 用 OGP / Twitter Card 画像を生成する。

出力:
  image/ogp-minecraft.png         (1200x630 — Open Graph 用)
  image/twitter-minecraft.png     (1200x628 — Twitter Card summary_large_image 用)

ピクセル風グラスブロックと和文タイトルを描画。
依存: Pillow  (pip install pillow)
"""
import random
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


REPO = Path(__file__).resolve().parent.parent

# Minecraft グラスブロック風カラー
SKY_TOP    = (135, 206, 250)
SKY_BOTTOM = (180, 220, 240)
GRASS_TOP  = (124, 179, 66)
GRASS_DARK = (90,  140, 45)
DIRT       = (139,  87,  43)
DIRT_DARK  = (110,  68,  33)
INK        = (32,  32,  32)
WHITE      = (255, 255, 255)
ACCENT     = (255, 235, 100)
RED_HOT    = (239, 68,  68)


def font(size):
    candidates = [
        "/usr/share/fonts/opentype/ipafont-gothic/ipag.ttf",
        "/usr/share/fonts/truetype/fonts-japanese-gothic.ttf",
    ]
    for p in candidates:
        try:
            return ImageFont.truetype(p, size)
        except (OSError, IOError):
            continue
    return ImageFont.load_default()


def text_with_outline(d, xy, text, font_, fill=WHITE, outline=INK, ow=4):
    x, y = xy
    for dx in range(-ow, ow + 1):
        for dy in range(-ow, ow + 1):
            if dx == 0 and dy == 0:
                continue
            d.text((x + dx, y + dy), text, font=font_, fill=outline)
    d.text(xy, text, font=font_, fill=fill)


def draw_pickaxe(d, x, y):
    """簡易ドット風ピッケル。"""
    d.rectangle([x + 8,  y + 12, x + 16, y + 30], fill=DIRT)
    d.rectangle([x + 6,  y + 10, x + 18, y + 14], outline=INK, width=2)
    d.polygon([
        (x,      y),
        (x + 28, y - 4),
        (x + 26, y + 6),
        (x + 4,  y + 12),
    ], fill=(180, 180, 195), outline=INK)


def gradient_sky(img, horizon_y):
    pixels = img.load()
    W, _ = img.size
    for y in range(horizon_y):
        t = y / horizon_y
        r = int(SKY_TOP[0] + (SKY_BOTTOM[0] - SKY_TOP[0]) * t)
        g = int(SKY_TOP[1] + (SKY_BOTTOM[1] - SKY_TOP[1]) * t)
        b = int(SKY_TOP[2] + (SKY_BOTTOM[2] - SKY_TOP[2]) * t)
        for x in range(W):
            pixels[x, y] = (r, g, b)


def draw_grass_horizon(d, W, H, horizon_y):
    grass_h = int((H - horizon_y) * 0.18)
    d.rectangle([0, horizon_y, W, horizon_y + grass_h], fill=GRASS_TOP)
    d.rectangle([0, horizon_y + grass_h, W, horizon_y + grass_h + 6], fill=GRASS_DARK)
    d.rectangle([0, horizon_y + grass_h + 6, W, H], fill=DIRT)
    rng = random.Random(7)
    dirt_top = horizon_y + grass_h + 6
    for _ in range(int(W * 0.15)):
        px = rng.randint(0, W - 8)
        py = rng.randint(dirt_top, H - 8)
        d.rectangle([px, py, px + 8, py + 8], fill=DIRT_DARK)


def draw_pixel_block(d, x, y, size):
    """グラスブロック (草の上 + 土の側面)。"""
    grass_h = int(size * 0.18)
    d.rectangle([x, y, x + size, y + grass_h], fill=GRASS_TOP)
    d.rectangle([x, y + grass_h, x + size, y + grass_h + 6], fill=GRASS_DARK)
    d.rectangle([x, y + grass_h + 6, x + size, y + size], fill=DIRT)
    rng = random.Random(42)
    for _ in range(30):
        px = rng.randint(x, x + size - 4)
        py = rng.randint(y + grass_h + 6, y + size - 4)
        d.rectangle([px, py, px + 4, py + 4], fill=DIRT_DARK)
    d.rectangle([x, y, x + size, y + size], outline=INK, width=3)


# ---------- variants ----------

def render_ogp(W=1200, H=630):
    """OGP (Open Graph) 用 1200x630。"""
    img = Image.new("RGB", (W, H), SKY_TOP)
    d = ImageDraw.Draw(img)
    horizon_y = int(H * 0.55)

    gradient_sky(img, horizon_y)
    draw_grass_horizon(d, W, H, horizon_y)

    # 雲
    cloud = (255, 255, 255)
    d.rectangle([130, 35, 320, 65], fill=cloud)
    d.rectangle([150, 25, 300, 55], fill=cloud)
    d.rectangle([720, 60, 880, 90], fill=cloud)
    d.rectangle([740, 50, 860, 80], fill=cloud)

    # 草ブロック (右側)
    block_size = 220
    block_x = W - block_size - 80
    block_y = horizon_y - block_size + 30
    draw_pixel_block(d, block_x, block_y, block_size)

    # フォント
    f_eyebrow  = font(28)
    f_title    = font(96)
    f_subtitle = font(40)
    f_meta     = font(28)
    f_brand    = font(26)

    # ピッケル + eyebrow
    draw_pickaxe(d, 80, 105)
    text_with_outline(d, (130, 100), "MINECRAFT JAVA EDITION", f_eyebrow, fill=ACCENT, ow=3)

    # タイトル 2 行
    text_with_outline(d, (80, 165), "のんびり",     f_title, fill=WHITE, ow=5)
    text_with_outline(d, (80, 280), "サバイバル鯖", f_title, fill=WHITE, ow=5)

    # サブタイトル
    text_with_outline(d, (80, 410), "バニラ運用 / ホワイトリスト制", f_subtitle, fill=WHITE, ow=4)

    # IP
    text_with_outline(d, (80, 478), "IP: 162.43.44.103", f_meta, fill=ACCENT, ow=3)

    # ブランド
    text_with_outline(d, (W - 360, H - 50), "dahande.github.io", f_brand, fill=(220, 220, 220), ow=2)

    return img


def render_twitter(W=1200, H=628):
    """Twitter Card (summary_large_image) 用 1200x628 — フィード訴求重視。"""
    img = Image.new("RGB", (W, H), SKY_TOP)
    d = ImageDraw.Draw(img)
    horizon_y = int(H * 0.62)   # 地平線をやや低めに → タイトル領域を広く

    gradient_sky(img, horizon_y)
    draw_grass_horizon(d, W, H, horizon_y)

    # 雲 (3つ)
    cloud = (255, 255, 255)
    d.rectangle([60, 35, 250, 65], fill=cloud)
    d.rectangle([80, 25, 230, 55], fill=cloud)
    d.rectangle([520, 70, 700, 100], fill=cloud)
    d.rectangle([540, 60, 680, 90], fill=cloud)
    d.rectangle([880, 30, 1060, 60], fill=cloud)
    d.rectangle([900, 20, 1040, 50], fill=cloud)

    # 草ブロック × 2 (フィードでも目立つように)
    bs = 180
    draw_pixel_block(d, W - bs - 70,        horizon_y - bs + 28, bs)
    draw_pixel_block(d, W - bs * 2 - 110,   horizon_y - bs + 50, bs - 30)

    # フォント
    f_eyebrow = font(30)
    f_badge   = font(34)
    f_title   = font(92)
    f_sub     = font(40)
    f_meta    = font(30)
    f_brand   = font(26)

    # eyebrow
    draw_pickaxe(d, 70, 75)
    text_with_outline(d, (122, 70), "MINECRAFT JAVA EDITION", f_eyebrow, fill=ACCENT, ow=3)

    # 稼働告知バッジ (赤背景)
    badge_text = "本日 21:00 START"
    badge_w, badge_h = 380, 56
    badge_x, badge_y = 70, 130
    d.rectangle([badge_x, badge_y, badge_x + badge_w, badge_y + badge_h], fill=RED_HOT, outline=INK, width=3)
    # テキストの中央寄せ
    bbox = d.textbbox((0, 0), badge_text, font=f_badge)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    d.text((badge_x + (badge_w - tw) // 2 - bbox[0],
            badge_y + (badge_h - th) // 2 - bbox[1]),
           badge_text, font=f_badge, fill=WHITE)

    # タイトル
    text_with_outline(d, (70, 220), "のんびり",     f_title, fill=WHITE, ow=5)
    text_with_outline(d, (70, 320), "サバイバル鯖", f_title, fill=WHITE, ow=5)

    # サブ + IP
    text_with_outline(d, (70, 432), "バニラ / ホワイトリスト制",     f_sub, fill=WHITE, ow=4)
    text_with_outline(d, (70, 488), "IP: 162.43.44.103",            f_meta, fill=ACCENT, ow=3)

    # ブランド (土の中)
    text_with_outline(d, (W - 360, H - 48), "dahande.github.io",    f_brand, fill=(220, 220, 220), ow=2)

    return img


def main():
    out_dir = REPO / "image"
    out_dir.mkdir(parents=True, exist_ok=True)

    targets = [
        (out_dir / "ogp-minecraft.png",     render_ogp),
        (out_dir / "twitter-minecraft.png", render_twitter),
    ]
    for path, fn in targets:
        img = fn()
        img.save(path, "PNG", optimize=True)
        print(f"wrote: {path.relative_to(REPO)}  ({path.stat().st_size / 1024:.1f} KB)")


if __name__ == "__main__":
    main()

