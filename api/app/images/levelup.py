from app.images.image import ImageGeneration

from io import BytesIO
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageOps


class LevelUp(ImageGeneration):
    async def draw(self):
        if not self._db_ready:
            return None

        font_bold_file = f"{Path(__file__).resolve().parent}/data/fonts/font_bold.ttf"
        userinfo = await self.db.users.find_one({"user_id": str(self.user_data["id"])})
        # get urls
        bg_url = userinfo["levelup_background"]
        # profile_url = user.avatar_url

        # create image objects
        # bg_image = Image
        # profile_image = Image

        async with self.session.get(bg_url) as r:
            level_background = BytesIO(await r.read())

        async with self.session.get(self.user_data["avatar"]) as r:
            level_avatar = BytesIO(await r.read())

        bg_image = Image.open(level_background).convert("RGBA")
        profile_image = Image.open(level_avatar).convert("RGBA")

        # set canvas
        width = 175
        height = 65
        bg_color = (255, 255, 255, 0)
        result = Image.new("RGBA", (width, height), bg_color)
        process = Image.new("RGBA", (width, height), bg_color)

        # draw
        draw = ImageDraw.Draw(process)

        # puts in background
        bg_image = bg_image.resize((width, height), Image.ANTIALIAS)
        bg_image = bg_image.crop((0, 0, width, height))
        result.paste(bg_image, (0, 0))

        # draw transparent overlay
        if "levelup_info_color" in userinfo.keys():
            info_color = tuple(userinfo["levelup_info_color"])
            info_color = (
                info_color[0],
                info_color[1],
                info_color[2],
                150,
            )  # increase transparency
        else:
            info_color = (30, 30, 30, 150)
        draw.rectangle([(38, 5), (170, 60)], fill=info_color)  # info portion

        # draw level circle
        multiplier = 6
        lvl_circle_dia = 60
        circle_left = 4
        circle_top = int((height - lvl_circle_dia) / 2)
        raw_length = lvl_circle_dia * multiplier

        # create mask
        mask = Image.new("L", (raw_length, raw_length), 0)
        draw_thumb = ImageDraw.Draw(mask)
        draw_thumb.ellipse((0, 0) + (raw_length, raw_length), fill=255, outline=0)

        # drawing level bar calculate angle
        # start_angle = -90  # from top instead of 3oclock

        lvl_circle = Image.new("RGBA", (raw_length, raw_length))
        draw_lvl_circle = ImageDraw.Draw(lvl_circle)
        draw_lvl_circle.ellipse(
            [0, 0, raw_length, raw_length], fill=(255, 255, 255, 220), outline=(255, 255, 255, 220)
        )

        # put on level bar circle
        lvl_circle = lvl_circle.resize((lvl_circle_dia, lvl_circle_dia), Image.ANTIALIAS)
        lvl_bar_mask = mask.resize((lvl_circle_dia, lvl_circle_dia), Image.ANTIALIAS)
        process.paste(lvl_circle, (circle_left, circle_top), lvl_bar_mask)

        # draws mask
        total_gap = 6
        border = int(total_gap / 2)
        profile_size = lvl_circle_dia - total_gap
        raw_length = profile_size * multiplier
        # put in profile picture
        # output = ImageOps.fit(profile_image, (raw_length, raw_length), centering=(0.5, 0.5))
        ImageOps.fit(profile_image, (raw_length, raw_length), centering=(0.5, 0.5))
        # output = output.resize((profile_size, profile_size), Image.ANTIALIAS)
        mask = mask.resize((profile_size, profile_size), Image.ANTIALIAS)
        profile_image = profile_image.resize((profile_size, profile_size), Image.ANTIALIAS)
        process.paste(profile_image, (circle_left + border, circle_top + border), mask)

        # fonts
        # level_fnt2 = ImageFont.truetype(font_bold_file, 19)
        level_fnt = ImageFont.truetype(font_bold_file, 26)

        # write label text
        white_text = (240, 240, 240, 255)
        dark_text = (35, 35, 35, 230)
        level_up_text = self._contrast(info_color, white_text, dark_text)
        lvl_text = "LEVEL {}".format(userinfo["servers"][str(self.server_data["id"])]["level"])
        draw.text(
            (self._center(50, 170, lvl_text, level_fnt), 22),
            lvl_text,
            font=level_fnt,
            fill=level_up_text,
        )  # Level Number

        image_object = BytesIO()
        result = Image.alpha_composite(result, process)
        result.save(image_object, format="PNG")
        image_object.seek(0)
        return image_object
