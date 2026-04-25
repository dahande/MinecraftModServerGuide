#!/usr/bin/env python3
"""
Minecraft 用 OGP 画像 (1200x630 PNG) を生成する。

ピクセル風グラスブロックと和文タイトルを描画。出力先:
  image/ogp-minecraft.png

依存: Pillow
  pip install pillow
"""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


REPO = Path(__file__).resolve().parent.parent
OUT  = REPO / "image" / "ogp-minecraft.png"

W, H = 1200, 630

# Minecraft グラスブロック風カラー
SKY_TOP    = (135, 206, 250)   # ライトスカイブルー
SKY_BOTTOM = (180, 220, 240)   # 雲色
GRASS_TOP  = (124, 179, 66)    # 新緑
GRASS_DARK = (90,  140, 45)
DIRT       = (139,  87,  43)
DIRT_DARK  = (110,  68,  33)
INK        = (32,  32,  32)
WHITE      = (255, 255, 255)
ACCENT     = (255, 235, 100)   # トーチ風イエロー


def font(size, bold=False):
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


def draw_pixel_block(d, x, y, size, top_color, side_color, dark_color):
    """Minecraft 風の立体ブロックを描く (アイソメトリックではなく簡易正面 + 側面)。"""
    # トップ
    d.rectangle([x, y, x + size, y + size // 4], fill=top_color)
    # 側面
    d.rectangle([x, y + size // 4, x + size, y + size], fill=side_color)
    # ピクセルノイズ (グラデっぽさ)
    import random
    rng = random.Random(42)
    for _ in range(30):
        px = rng.randint(x, x + size - 4)
        py = rng.randint(y + size // 4, y + size - 4)
        d.rectangle([px, py, px + 4, py + 4], fill=dark_color)
    # 縁取り
    d.rectangle([x, y, x + size, y + size], outline=INK, width=3)


def draw_grass_horizon(d, y, height):
    """地平線の草ブロック層 + 土層を横一列に。"""
    # 草層 (上から数ピクセル)
    grass_h = int(height * 0.18)
    d.rectangle([0, y, W, y + grass_h], fill=GRASS_TOP)
    # 草の下のダーク帯
    d.rectangle([0, y + grass_h, W, y + grass_h + 6], fill=GRASS_DARK)
    # 土層
    d.rectangle([0, y + grass_h + 6, W, H], fill=DIRT)
    # 土の暗いピクセルでテクスチャ
    import random
    rng = random.Random(7)
    dirt_top = y + grass_h + 6
    for _ in range(180):
        px = rng.randint(0, W - 8)
        py = rng.randint(dirt_top, H - 8)
        d.rectangle([px, py, px + 8, py + 8], fill=DIRT_DARK)


def gradient_sky(img):
    """空のグラデーションを縦方向に。"""
    pixels = img.load()
    horizon_y = int(H * 0.55)
    for y in range(horizon_y):
        t = y / horizon_y
        r = int(SKY_TOP[0] + (SKY_BOTTOM[0] - SKY_TOP[0]) * t)
        g = int(SKY_TOP[1] + (SKY_BOTTOM[1] - SKY_TOP[1]) * t)
        b = int(SKY_TOP[2] + (SKY_BOTTOM[2] - SKY_TOP[2]) * t)
        for x in range(W):
            pixels[x, y] = (r, g, b)


def text_with_outline(d, xy, text, font_, fill=WHITE, outline=INK, ow=4):
    """縁取り付きテキスト (Minecraft っぽさ)。"""
    x, y = xy
    for dx in range(-ow, ow + 1):
        for dy in range(-ow, ow + 1):
            if dx == 0 and dy == 0:
                continue
            d.text((x + dx, y + dy), text, font=font_, fill=outline)
    d.text(xy, text, font=font_, fill=fill)


def main():
    img = Image.new("RGB", (W, H), SKY_TOP)
    d = ImageDraw.Draw(img)

    # 1. 空のグラデーション
    gradient_sky(img)

    # 2. 地平線 (草 → 土)
    horizon_y = int(H * 0.55)
    draw_grass_horizon(d, horizon_y, H - horizon_y)

    # 3. 雲 (テキストとは重ならない位置)
    cloud_color = (255, 255, 255)
    # 左上の雲 (eyebrow テキストより上)
    d.rectangle([130, 35, 320, 65], fill=cloud_color)
    d.rectangle([150, 25, 300, 55], fill=cloud_color)
    # 右上の雲
    d.rectangle([720, 60, 880, 90], fill=cloud_color)
    d.rectangle([740, 50, 860, 80], fill=cloud_color)

    # 4. 大きな草ブロック (右側)
    block_size = 220
    block_x = W - block_size - 80
    block_y = horizon_y - block_size + 30
    draw_pixel_block(d, block_x, block_y, block_size, GRASS_TOP, DIRT, DIRT_DARK)
    # ブロックの草の縁
    d.rectangle([block_x, block_y, block_x + block_size, block_y + 14], fill=GRASS_DARK)
    d.rectangle([block_x, block_y, block_x + block_size, block_y + 8], fill=GRASS_TOP)

    # 5. テキスト
    f_eyebrow = font(28)
    f_title   = font(96)
    f_subtitle = font(40)
    f_meta    = font(28)
    f_brand   = font(26)

    # eyebrow (上部) — 絵文字はフォントにないので簡易ピッケルを矩形で描く
    pickaxe_x, pickaxe_y = 80, 105
    # 柄
    d.rectangle([pickaxe_x + 8,  pickaxe_y + 12, pickaxe_x + 16, pickaxe_y + 30], fill=DIRT)
    d.rectangle([pickaxe_x + 6,  pickaxe_y + 10, pickaxe_x + 18, pickaxe_y + 14], outline=INK, width=2)
    # 刃
    d.polygon([
        (pickaxe_x,      pickaxe_y),
        (pickaxe_x + 28, pickaxe_y - 4),
        (pickaxe_x + 26, pickaxe_y + 6),
        (pickaxe_x + 4,  pickaxe_y + 12),
    ], fill=(180, 180, 195), outline=INK)
    text_with_outline(d, (130, 100), "MINECRAFT JAVA EDITION", f_eyebrow, fill=ACCENT, ow=3)

    # メインタイトル (2行)
    text_with_outline(d, (80, 165), "のんびり",         f_title, fill=WHITE, ow=5)
    text_with_outline(d, (80, 280), "サバイバル鯖",     f_title, fill=WHITE, ow=5)

    # サブタイトル
    text_with_outline(d, (80, 410), "バニラ運用 / ホワイトリスト制",
                      f_subtitle, fill=WHITE, ow=4)

    # IP (草の上に配置)
    text_with_outline(d, (80, 478), "IP: 162.43.44.103",
                      f_meta, fill=ACCENT, ow=3)

    # ブランド (右下、土の中)
    text_with_outline(d, (W - 360, H - 50), "dahande.github.io",
                      f_brand, fill=(220, 220, 220), ow=2)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    img.save(OUT, "PNG", optimize=True)
    print(f"wrote: {OUT}  ({OUT.stat().st_size / 1024:.1f} KB)")


if __name__ == "__main__":
    main()
