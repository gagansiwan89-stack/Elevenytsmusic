import os
import asyncio
import aiohttp
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont

from Elevenyts import config
from Elevenyts.helpers import Track

WIDTH, HEIGHT = 1280, 720

THUMB_W, THUMB_H = 420, 420
THUMB_X, THUMB_Y = 80, 150

TITLE_X = 550
TITLE_Y = 200

SUBTITLE_Y = TITLE_Y + 60

BAR_X = 550
BAR_Y = SUBTITLE_Y + 80
BAR_TOTAL = 450
BAR_PROGRESS = 220


class Thumbnail:
    def __init__(self):
        try:
            self.title_font = ImageFont.truetype(
                "Elevenyts/helpers/Raleway-Bold.ttf", 48)
            self.regular_font = ImageFont.truetype(
                "Elevenyts/helpers/Inter-Light.ttf", 24)
        except:
            self.title_font = self.regular_font = ImageFont.load_default()

    async def save_thumb(self, path, url):
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as r:
                with open(path, "wb") as f:
                    f.write(await r.read())
        return path

    async def generate(self, song: Track):
        try:
            temp = f"cache/{song.id}.jpg"
            output = f"cache/{song.id}_final.png"

            if os.path.exists(output):
                return output

            await self.save_thumb(temp, song.thumbnail)

            return await asyncio.get_event_loop().run_in_executor(
                None, self._draw, temp, output, song
            )
        except:
            return config.DEFAULT_THUMB

    def _draw(self, temp, output, song):
        try:
            base = Image.open(temp).resize((WIDTH, HEIGHT)).convert("RGBA")

            # 🔥 Background blur
            bg = base.filter(ImageFilter.GaussianBlur(30))
            bg = ImageEnhance.Brightness(bg).enhance(0.5)

            draw = ImageDraw.Draw(bg)

            # 🎧 Album thumbnail (rounded)
            thumb = base.resize((THUMB_W, THUMB_H))
            mask = Image.new("L", (THUMB_W, THUMB_H), 0)
            ImageDraw.Draw(mask).rounded_rectangle(
                (0, 0, THUMB_W, THUMB_H), 40, fill=255)
            bg.paste(thumb, (THUMB_X, THUMB_Y), mask)

            # ✨ Glow
            glow = Image.new("RGBA", (THUMB_W+40, THUMB_H+40), (0,0,0,0))
            gdraw = ImageDraw.Draw(glow)
            gdraw.rounded_rectangle(
                (0,0,THUMB_W+40,THUMB_H+40),
                50,
                fill=(0,150,255,60)
            )
            bg.paste(glow, (THUMB_X-20, THUMB_Y-20), glow)

            # 🎵 TITLE (clean + trimmed)
            title = song.title.strip()
            if len(title) > 32:
                title = title[:32] + "..."

            draw.text(
                (TITLE_X, TITLE_Y),
                title,
                fill="white",
                font=self.title_font
            )

            # ⚡ SUBTITLE (branding instead of artist/views)
            draw.text(
                (TITLE_X, SUBTITLE_Y),
                "Adam Music Bot",
                fill="#CCCCCC",
                font=self.regular_font
            )

            # 🔊 Progress bar
            draw.line(
                [(BAR_X, BAR_Y), (BAR_X + BAR_TOTAL, BAR_Y)],
                fill=(80, 80, 80),
                width=6
            )

            draw.line(
                [(BAR_X, BAR_Y), (BAR_X + BAR_PROGRESS, BAR_Y)],
                fill=(0, 200, 255),
                width=6
            )

            # ⏱ Time
            draw.text(
                (BAR_X, BAR_Y + 15),
                "00:00",
                fill="#AAAAAA",
                font=self.regular_font
            )

            draw.text(
                (BAR_X + BAR_TOTAL - 80, BAR_Y + 15),
                song.duration,
                fill="#AAAAAA",
                font=self.regular_font
            )

            # 💎 CLEAN BRANDING (no box, no spam)
            draw.text(
                (TITLE_X, BAR_Y + 70),
                "ADAM MUSIC BOT",
                fill="#00CCFF",
                font=self.regular_font
            )

            bg.save(output, "PNG", quality=95)

            try:
                os.remove(temp)
            except:
                pass

            return output

        except Exception as e:
            print("Thumbnail Error:", e)
            return config.DEFAULT_THUMB
