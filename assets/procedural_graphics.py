"""
BEYOND UNKNOWN - Premium Procedural Graphics and Layout Engine
Generates:
- Topic-adaptive 1080x1920 cinematic backgrounds (archaeological, telemetry, nature, space)
- Pixel-perfect documentary fact panels, stat cards, and info boxes
- Safe-area compliant layouts adhering to mobile vertical boundaries
- Blurred vertical backdrop compositing for landscape imagery
- Channel watermark and branding elements
Strictly adheres to brand color palette:
- Midnight Black: #10151E
- Deep Navy: #182638
- Antique Gold: #D6B56D
- Warm White: #F5F1E8
"""

import math
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from config import settings

WIDTH = 1080
HEIGHT = 1920

# Safe zone boundaries
SAFE_TOP = 240
SAFE_BOTTOM = 1920 - 380
SAFE_LEFT = 80
SAFE_RIGHT = 1080 - 140
CONTENT_WIDTH = SAFE_RIGHT - SAFE_LEFT

# Brand Color Palette
COLOR_BLACK = (16, 21, 30)         # #10151E
COLOR_NAVY = (24, 38, 56)          # #182638
COLOR_GOLD = (214, 181, 109)       # #D6B56D
COLOR_WHITE = (245, 241, 232)      # #F5F1E8
COLOR_GOLD_MUTED = (160, 135, 80)
COLOR_CARD_BG = (24, 38, 56, 220)  # 86% alpha
COLOR_BORDER_GOLD = (214, 181, 109, 140)

class ProceduralGraphics:
    def __init__(self):
        self.fonts_dir = settings.FONTS_DIR
        self.font_cinzel = self._load_font("Cinzel.ttf", 46)
        self.font_cinzel_large = self._load_font("Cinzel.ttf", 56)
        self.font_montserrat = self._load_font("Montserrat.ttf", 32)
        self.font_montserrat_bold = self._load_font("Montserrat.ttf", 36)
        self.font_devanagari = self._load_font("NotoSansDevanagari.ttf", 38)
        self.font_badge = self._load_font("Montserrat.ttf", 22)

    def _load_font(self, font_name: str, size: int) -> ImageFont.FreeTypeFont:
        font_path = self.fonts_dir / font_name
        if font_path.exists():
            try:
                return ImageFont.truetype(str(font_path), size)
            except Exception:
                pass
        return ImageFont.load_default()

    def generate_adaptive_background(self, layout_style: str, seed: int = 1) -> Image.Image:
        """
        Creates a high-resolution 1080x1920 dark cinematic textured backdrop
        adapted to the topic style:
        - 'archaeological_card': dark basalt / granite stone texture with ancient subtle gold grid
        - 'telemetry_hud': cosmic navy starfield with coordinates and orbital reticle
        - 'stat_card': sleek geometric documentary gradient with angular accents
        - 'clean_documentary': rich vignette gradient from Midnight Black to Deep Navy
        """
        img = Image.new("RGB", (WIDTH, HEIGHT), COLOR_BLACK)
        draw = ImageDraw.Draw(img)

        # 1. Base vertical subtle gradient
        for y in range(HEIGHT):
            ratio = y / HEIGHT
            r = int(COLOR_BLACK[0] + (COLOR_NAVY[0] - COLOR_BLACK[0]) * math.sin(ratio * math.pi))
            g = int(COLOR_BLACK[1] + (COLOR_NAVY[1] - COLOR_BLACK[1]) * math.sin(ratio * math.pi))
            b = int(COLOR_BLACK[2] + (COLOR_NAVY[2] - COLOR_BLACK[2]) * math.sin(ratio * math.pi))
            draw.line([(0, y), (WIDTH, y)], fill=(r, g, b))

        # 2. Topic-adaptive accents
        if layout_style == "telemetry_hud":
            # Space & Science Telemetry Grid
            grid_step = 90
            for x in range(SAFE_LEFT, SAFE_RIGHT, grid_step):
                draw.line([(x, SAFE_TOP - 80), (x, SAFE_BOTTOM + 80)], fill=(35, 52, 75), width=1)
            for y in range(SAFE_TOP - 80, SAFE_BOTTOM + 80, grid_step):
                draw.line([(SAFE_LEFT, y), (SAFE_RIGHT, y)], fill=(35, 52, 75), width=1)

            # Circular orbital reticle at center
            cx, cy = WIDTH // 2, HEIGHT // 2 - 100
            for r in [180, 320]:
                draw.ellipse([(cx - r, cy - r), (cx + r, cy + r)], outline=(COLOR_GOLD[0], COLOR_GOLD[1], COLOR_GOLD[2]), width=1)
            draw.text((SAFE_LEFT + 10, SAFE_TOP - 70), "SYS // TELEMETRY: ACTIVE", font=self.font_badge, fill=COLOR_GOLD)
            draw.text((SAFE_RIGHT - 240, SAFE_TOP - 70), "COORDS: 44.3° N / 12.8° E", font=self.font_badge, fill=COLOR_GOLD_MUTED)

        elif layout_style == "archaeological_card":
            # Ancient archaeological frame with gold corner brackets
            bracket_len = 40
            # Top-left bracket
            draw.line([(SAFE_LEFT - 20, SAFE_TOP - 20), (SAFE_LEFT - 20 + bracket_len, SAFE_TOP - 20)], fill=COLOR_GOLD, width=3)
            draw.line([(SAFE_LEFT - 20, SAFE_TOP - 20), (SAFE_LEFT - 20, SAFE_TOP - 20 + bracket_len)], fill=COLOR_GOLD, width=3)
            # Top-right bracket
            draw.line([(SAFE_RIGHT + 20, SAFE_TOP - 20), (SAFE_RIGHT + 20 - bracket_len, SAFE_TOP - 20)], fill=COLOR_GOLD, width=3)
            draw.line([(SAFE_RIGHT + 20, SAFE_TOP - 20), (SAFE_RIGHT + 20, SAFE_TOP - 20 + bracket_len)], fill=COLOR_GOLD, width=3)
            # Bottom-left bracket
            draw.line([(SAFE_LEFT - 20, SAFE_BOTTOM + 20), (SAFE_LEFT - 20 + bracket_len, SAFE_BOTTOM + 20)], fill=COLOR_GOLD, width=3)
            draw.line([(SAFE_LEFT - 20, SAFE_BOTTOM + 20), (SAFE_LEFT - 20, SAFE_BOTTOM + 20 - bracket_len)], fill=COLOR_GOLD, width=3)
            # Bottom-right bracket
            draw.line([(SAFE_RIGHT + 20, SAFE_BOTTOM + 20), (SAFE_RIGHT + 20 - bracket_len, SAFE_BOTTOM + 20)], fill=COLOR_GOLD, width=3)
            draw.line([(SAFE_RIGHT + 20, SAFE_BOTTOM + 20), (SAFE_RIGHT + 20, SAFE_BOTTOM + 20 - bracket_len)], fill=COLOR_GOLD, width=3)

        elif layout_style == "stat_card":
            # Modern high-contrast documentary framing
            draw.rectangle([(SAFE_LEFT, SAFE_TOP - 40), (SAFE_RIGHT, SAFE_TOP - 36)], fill=COLOR_GOLD)
            draw.rectangle([(SAFE_LEFT, SAFE_BOTTOM + 36), (SAFE_RIGHT, SAFE_BOTTOM + 40)], fill=COLOR_GOLD)

        return img

    def compose_scene_image(
        self,
        base_media_path: Optional[str],
        topic_title: str,
        category: str,
        scene_on_screen_text: str,
        highlight_words: List[str],
        layout_style: str,
        output_image_path: Path
    ) -> Path:
        """
        Composites base footage/photo with the premium documentary fact card,
        safe-area alignment, channel branding watermark, and antique gold highlights.
        """
        output_image_path.parent.mkdir(parents=True, exist_ok=True)

        # 1. Base Layer: Either blur-expand downloaded media or generate procedural backdrop
        if base_media_path and Path(base_media_path).exists() and not base_media_path.endswith(".mp4"):
            try:
                raw_img = Image.open(base_media_path).convert("RGBA")
                canvas = self._expand_and_blur_to_916(raw_img)
            except Exception:
                canvas = self.generate_adaptive_background(layout_style).convert("RGBA")
        else:
            canvas = self.generate_adaptive_background(layout_style).convert("RGBA")

        # 2. Add cinematic top & bottom dark vignette
        vignette = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
        v_draw = ImageDraw.Draw(vignette)
        # Top vignette
        for y in range(400):
            alpha = int(180 * (1.0 - y / 400))
            v_draw.line([(0, y), (WIDTH, y)], fill=(16, 21, 30, alpha))
        # Bottom vignette
        for y in range(HEIGHT - 500, HEIGHT):
            alpha = int(220 * ((y - (HEIGHT - 500)) / 500))
            v_draw.line([(0, y), (WIDTH, y)], fill=(16, 21, 30, alpha))

        canvas = Image.alpha_composite(canvas, vignette)

        # 3. Add Channel Watermark Pill (Top safe zone: Y=120)
        canvas = self._draw_channel_badge(canvas)

        # 4. Add Custom Documentary Fact Card (Y: 260 to 480)
        canvas = self._draw_fact_card(
            canvas,
            category=category.upper(),
            fact_text=scene_on_screen_text,
            highlight_words=highlight_words,
            layout_style=layout_style
        )

        # Convert to RGB and save
        final_rgb = canvas.convert("RGB")
        final_rgb.save(output_image_path, "JPEG", quality=95)
        return output_image_path

    def _expand_and_blur_to_916(self, raw_img: Image.Image) -> Image.Image:
        """
        Expands any landscape or square image to vertical 9:16 (1080x1920)
        by applying Gaussian blur to background and sharply centering the subject.
        """
        canvas = Image.new("RGBA", (WIDTH, HEIGHT), COLOR_BLACK + (255,))

        # Create heavily blurred background fill
        bg = raw_img.copy().resize((WIDTH, HEIGHT), Image.Resampling.LANCZOS)
        bg = bg.filter(ImageFilter.GaussianBlur(radius=28))
        canvas.paste(bg, (0, 0))

        # Overlay a dark tint on the blurred background for contrast
        tint = Image.new("RGBA", (WIDTH, HEIGHT), (16, 21, 30, 160))
        canvas = Image.alpha_composite(canvas, tint)

        # Fit sharp image into center safe area
        max_w = WIDTH - 60
        max_h = 960  # center block
        img_w, img_h = raw_img.size
        scale = min(max_w / img_w, max_h / img_h)
        new_w = int(img_w * scale)
        new_h = int(img_h * scale)

        sharp_center = raw_img.resize((new_w, new_h), Image.Resampling.LANCZOS)
        pos_x = (WIDTH - new_w) // 2
        pos_y = 560 + (max_h - new_h) // 2

        # Draw a subtle antique gold border around sharp center photo
        b_draw = ImageDraw.Draw(canvas)
        b_draw.rectangle([(pos_x - 4, pos_y - 4), (pos_x + new_w + 3, pos_y + new_h + 3)], outline=COLOR_BORDER_GOLD, width=3)
        canvas.paste(sharp_center, (pos_x, pos_y), mask=sharp_center if sharp_center.mode == "RGBA" else None)

        return canvas

    def _draw_channel_badge(self, canvas: Image.Image) -> Image.Image:
        """Draws top minimal channel watermark."""
        overlay = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)

        badge_w, badge_h = 320, 48
        bx = (WIDTH - badge_w) // 2
        by = 130

        # Background pill
        draw.rounded_rectangle([(bx, by), (bx + badge_w, by + badge_h)], radius=12, fill=(24, 38, 56, 190), outline=COLOR_BORDER_GOLD, width=1)
        # Text
        badge_text = "BEYOND UNKNOWN"
        draw.text((bx + 35, by + 12), badge_text, font=self.font_badge, fill=COLOR_GOLD)
        return Image.alpha_composite(canvas, overlay)

    def _draw_fact_card(
        self,
        canvas: Image.Image,
        category: str,
        fact_text: str,
        highlight_words: List[str],
        layout_style: str
    ) -> Image.Image:
        """
        Draws the central information card inside mobile safe bounds.
        """
        overlay = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)

        card_x0 = SAFE_LEFT
        card_y0 = SAFE_TOP
        card_x1 = SAFE_RIGHT
        card_h = 240
        card_y1 = card_y0 + card_h

        # 1. Card backdrop with rounded corners
        draw.rounded_rectangle([(card_x0, card_y0), (card_x1, card_y1)], radius=18, fill=COLOR_CARD_BG, outline=COLOR_BORDER_GOLD, width=2)

        # 2. Category badge inside card
        cat_badge_w = min(360, len(category) * 14 + 40)
        draw.rounded_rectangle([(card_x0 + 24, card_y0 + 20), (card_x0 + 24 + cat_badge_w, card_y0 + 56)], radius=8, fill=(16, 21, 30, 220), outline=COLOR_BORDER_GOLD, width=1)
        draw.text((card_x0 + 38, card_y0 + 26), f"• {category}", font=self.font_badge, fill=COLOR_GOLD)

        # 3. Main fact text rendering with Antique Gold keyword highlight
        text_y = card_y0 + 80
        words = fact_text.upper().split()
        curr_x = card_x0 + 28
        max_x = card_x1 - 28

        # Line wrap logic
        line = []
        for word in words:
            line.append(word)
            test_line = " ".join(line)
            # Use font_cinzel
            bbox = draw.textbbox((0, 0), test_line, font=self.font_cinzel)
            if (bbox[2] - bbox[0]) > (max_x - curr_x) and len(line) > 1:
                line.pop()
                # Render line
                self._render_line_with_highlights(draw, line, curr_x, text_y, highlight_words)
                text_y += 56
                line = [word]

        if line:
            self._render_line_with_highlights(draw, line, curr_x, text_y, highlight_words)

        return Image.alpha_composite(canvas, overlay)

    def _render_line_with_highlights(
        self,
        draw: ImageDraw.ImageDraw,
        words: List[str],
        start_x: int,
        start_y: int,
        highlight_words: List[str]
    ):
        """Renders words horizontally, coloring highlighted tokens in Antique Gold."""
        norm_highlights = [h.strip().upper() for h in highlight_words]
        cx = start_x

        for w in words:
            clean_w = w.strip(",.!?\":;'")
            is_hl = any(clean_w == nh or nh in clean_w for nh in norm_highlights)
            color = COLOR_GOLD if is_hl else COLOR_WHITE

            # Drop shadow
            draw.text((cx + 2, start_y + 2), w + " ", font=self.font_cinzel, fill=(0, 0, 0, 180))
            # Main text
            draw.text((cx, start_y), w + " ", font=self.font_cinzel, fill=color)

            bbox = draw.textbbox((0, 0), w + " ", font=self.font_cinzel)
            cx += (bbox[2] - bbox[0])
