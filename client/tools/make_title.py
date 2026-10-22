#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""breakout 打砖块标题图 —— 程序化霓虹标题生成器。

用法（在仓根下）：
    python client/tools/make_title.py

产出 `client/assets/title.png`（1152x384 RGBA，透明底），尺寸与被替换的
素材完全一致，可直接覆盖。

为什么重做：
    旧标题图是图像模型（gpt-image-2）生成的，模型的中文字形不可靠——图上的
    「打砖块」三个字是形近的伪汉字，发布出去是明显的错字。图像模型解决不了
    这类问题：它的强项是画面，不是字形。
    改为本地程序化排版：字形用系统中文字体渲染（真字），霓虹外发光用
    多次高斯模糊叠出来，产出确定、可复现、不依赖任何出图服务。

设计口径：
  * 画布 1152x384，与旧图一致，避免下游尺寸假设被打破。
  * 字色取菜单页 `<h1>` 的 `#ffedbe`（上浅下暖），外辉光取按钮描边的
    `#4fd595`，深色描边取 `#0d1b12`——与 `client/assets/scenes/menu.html`
    的配色同源。
  * 底部一排砖用**游戏实砖调色板**（`src/BkGame.zan` 的 PalR/PalG/PalB
    六色循环），呼应玩法而不是随手配色。

字体：脚本按候选列表挑一个可用的中文粗体；都不在时可以用环境变量
`ZAN_TITLE_FONT` 指定一个 .ttf/.ttc 路径。生成结果已入库，脚本只为可复现。

依赖：pip install pillow
"""

import os
import sys

from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

W, H = 1152, 384
TEXT = "打砖块"
TRACKING = 20          # 字距
TEXT_W = 760           # 文字组目标宽
TEXT_TOP = 30          # 文字组顶边 y

# 配色（与 client/assets/scenes/menu.html 同源）
FILL_TOP = (255, 246, 214)
FILL_BOTTOM = (255, 219, 150)
GLOW = (79, 213, 149)           # 霓虹绿（按钮描边色）
CONTOUR = (13, 27, 18)          # 深色描边

# 游戏实砖调色板：src/BkGame.zan 的 PalR/PalG/PalB 六色循环
BRICK_PALETTE = [
    (255, 110, 140),   # hue 0
    (255, 205, 90),    # hue 1
    (120, 235, 140),   # hue 2
    (90, 160, 255),    # hue 3
    (190, 120, 255),   # hue 4
    (255, 235, 120),   # hue 5
]

FONT_CANDIDATES = [
    os.environ.get("ZAN_TITLE_FONT", ""),
    r"C:\Windows\Fonts\msyhbd.ttc",     # 微软雅黑 Bold
    r"C:\Windows\Fonts\simhei.ttf",     # 黑体
    r"C:\Windows\Fonts\Dengb.ttf",      # 等线 Bold
    r"C:\Windows\Fonts\msyh.ttc",       # 微软雅黑
    r"C:\Windows\Fonts\STZHONGS.TTF",   # 华文中宋
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
    "/usr/share/fonts/truetype/noto/NotoSansCJK-Bold.ttc",
    "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
    "/System/Library/Fonts/PingFang.ttc",
    "/System/Library/Fonts/STHeiti Medium.ttc",
]


def pick_font(size):
    """挑一个能渲染这三个字的中文粗体；找不到就报错退出。"""
    tried = []
    for path in FONT_CANDIDATES:
        if not path or not os.path.isfile(path):
            continue
        tried.append(path)
        for index in (0, 1):
            try:
                font = ImageFont.truetype(path, size, index=index)
            except Exception:
                continue
            # 字体缺字会退化成豆腐块，用掩膜确认「砖」真的画出来了
            try:
                if font.getmask("砖").getbbox() is None:
                    continue
            except Exception:
                pass
            return font, path
    raise SystemExit(
        "找不到可用的中文字体。已尝试：\n  " + "\n  ".join(tried or ["(候选列表为空)"]) +
        "\n请安装一个中文粗体，或用环境变量 ZAN_TITLE_FONT 指向一个 .ttf/.ttc 路径。"
    )


def layout(size):
    """给定字号，算出逐字的 x 位置与文字组尺寸。"""
    font, path = pick_font(size)
    boxes = [font.getbbox(ch) for ch in TEXT]
    widths = [b[2] - b[0] for b in boxes]
    total = sum(widths) + TRACKING * (len(TEXT) - 1)
    ascent, descent = font.getmetrics()
    height = ascent + descent
    # 逐字的绘制起点：PIL 的 anchor="lt" 以字符的 ascender 顶边为基准
    xs = []
    x = 0
    for w in widths:
        xs.append(x)
        x += w + TRACKING
    return font, path, xs, widths, total, height


def fit_font():
    """按目标宽度反推字号（等比收敛，步数上限防死循环）。"""
    size = 240
    font = path = None
    xs = widths = None
    total = height = 0
    for _ in range(24):
        font, path, xs, widths, total, height = layout(size)
        if abs(total - TEXT_W) <= 6:
            break
        nxt = max(60, min(360, int(size * (TEXT_W / float(total)))))
        if nxt == size:
            break
        size = nxt
    return font, path, xs, widths, total, height


def draw_chars(target, font, xs, fill, stroke_width=0, stroke_fill=None):
    """按同一套字位逐字绘制——描边层与字面层共用它，保证严格对齐。"""
    d = ImageDraw.Draw(target)
    for ch, x in zip(TEXT, xs):
        if stroke_width:
            d.text((x, TEXT_TOP), ch, font=font, fill=fill,
                   stroke_width=stroke_width, stroke_fill=stroke_fill, anchor="lt")
        else:
            d.text((x, TEXT_TOP), ch, font=font, fill=fill, anchor="lt")


def build():
    font, path, xs, widths, tw, th = fit_font()
    x0 = (W - tw) // 2
    print("  字体：%s  文字组：%dx%d  起点 x=%d" % (path, tw, th, x0))

    # 字位平移到画布坐标
    xs = [x + x0 for x in xs]

    # --- 辉光：先用同一套字位画一张整幅 alpha 掩膜，再多档模糊 ---
    # 辉光要「亮核 + 软晕」，不是一坨实色：模糊后的掩膜先做 gamma 整形，
    # 把低亮度区压下去，剩下贴着字形的一圈才是霓虹。
    mask = Image.new("L", (W, H), 0)
    draw_chars(mask, font, xs, 255)
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    for radius, gamma, amp in ((34, 2.9, 190), (16, 2.1, 120), (6, 1.6, 70)):
        blurred = mask.filter(ImageFilter.GaussianBlur(radius))
        shaped = blurred.point(lambda v, g=gamma: int(255.0 * (v / 255.0) ** g))
        layer = Image.new("RGBA", (W, H), GLOW + (0,))
        layer.putalpha(shaped.point(lambda v, a=amp: v * a // 255))
        glow = Image.alpha_composite(glow, layer)

    # --- 描边层：深色，比字面大一圈 ---
    contour = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw_chars(contour, font, xs, CONTOUR + (255,), stroke_width=9,
               stroke_fill=CONTOUR + (255,))

    # --- 字面层：cream，垂直方向由浅到暖（渐变只作用在字面自身） ---
    face_mask = Image.new("L", (W, H), 0)
    draw_chars(face_mask, font, xs, 255)
    bbox = face_mask.getbbox()
    face = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    if bbox:
        gw, gh = bbox[2] - bbox[0], bbox[3] - bbox[1]
        grad = Image.new("L", (1, gh))
        gp = grad.load()
        for y in range(gh):
            gp[0, y] = 255 - int(255 * y / float(max(1, gh - 1)))
        grad = grad.resize((gw, gh))
        top = Image.new("RGBA", (gw, gh), FILL_TOP + (255,))
        bottom = Image.new("RGBA", (gw, gh), FILL_BOTTOM + (255,))
        ramp = Image.composite(top, bottom, grad)
        # 只保留字形内部的像素
        cut = face_mask.crop(bbox)
        ramp.putalpha(cut)
        face.paste(ramp, (bbox[0], bbox[1]), ramp)

    out = Image.alpha_composite(glow, contour)
    out = Image.alpha_composite(out, face)
    return out


def brick_row(base, y, count=8):
    """底部一排实砖，用游戏调色板，与正文同一套光。"""
    layer = Image.new("RGBA", base.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    gap = 16
    margin = 150
    bw = (W - 2 * margin - gap * (count - 1)) // count
    bh = 28
    x0 = (W - (bw * count + gap * (count - 1))) // 2
    for i in range(count):
        c = BRICK_PALETTE[i % len(BRICK_PALETTE)]
        x = x0 + i * (bw + gap)
        d.rounded_rectangle([x, y, x + bw, y + bh], radius=3, fill=c + (255,))
        # 砖顶一道高光，下沿一道压暗，做出体积感
        d.rounded_rectangle([x + 3, y + 3, x + bw - 3, y + 8], radius=2,
                            fill=(255, 255, 255, 60))
        d.rounded_rectangle([x, y + bh - 5, x + bw, y + bh], radius=2,
                            fill=(0, 0, 0, 70))
    # 辉光同样走 gamma 整形，只留贴着砖的一圈
    halo = layer.filter(ImageFilter.GaussianBlur(7))
    halo = halo.point(lambda v: int(255.0 * (v / 255.0) ** 2.6))
    halo = Image.alpha_composite(halo, layer)
    return Image.alpha_composite(base, halo)


def main():
    out_dir = os.path.join(ROOT, "client", "assets")
    os.makedirs(out_dir, exist_ok=True)
    img = build()
    img = brick_row(img, H - 84)
    path = os.path.join(out_dir, "title.png")
    img.save(path, optimize=True)
    print("  %5.1f KB  title.png  (%dx%d)" % (os.path.getsize(path) / 1024.0, W, H))
    print("DONE")
    return 0


if __name__ == "__main__":
    sys.exit(main())
