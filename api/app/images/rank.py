from app.images.image import ImageGeneration

import string
import aiohttp
from pathlib import Path
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont, ImageOps

working_path = Path(__file__).resolve().parent


class Rank(ImageGeneration):
    @staticmethod
    def _add_corners(im, rad, multiplier=6):
        raw_length = rad * 2 * multiplier
        circle = Image.new("L", (raw_length, raw_length), 0)
        draw = ImageDraw.Draw(circle)
        draw.ellipse((0, 0, raw_length, raw_length), fill=255)
        circle = circle.resize((rad * 2, rad * 2), Image.ANTIALIAS)

        alpha = Image.new("L", im.size, 255)
        w, h = im.size
        alpha.paste(circle.crop((0, 0, rad, rad)), (0, 0))
        alpha.paste(circle.crop((0, rad, rad, rad * 2)), (0, h - rad))
        alpha.paste(circle.crop((rad, 0, rad * 2, rad)), (w - rad, 0))
        alpha.paste(circle.crop((rad, rad, rad * 2, rad * 2)), (w - rad, h - rad))
        im.putalpha(alpha)
        return im

    async def draw(self):
        if not self._db_ready:
            return None

        # fonts
        # font_file = f"{bundled_data_path(self)}/font.ttf"
        font_bold_file = f"{working_path}/data/fonts/font_bold.ttf"
        font_unicode_file = f"{working_path}/data/fonts/unicode.ttf"
        name_fnt = ImageFont.truetype(font_bold_file, 22)
        header_u_fnt = ImageFont.truetype(font_unicode_file, 18)
        # sub_header_fnt = ImageFont.truetype(font_bold_file, 14)
        # badge_fnt = ImageFont.truetype(font_bold_file, 12)
        # large_fnt = ImageFont.truetype(font_bold_file, 33)
        level_label_fnt = ImageFont.truetype(font_bold_file, 22)
        general_info_fnt = ImageFont.truetype(font_bold_file, 15)
        # general_info_u_fnt = ImageFont.truetype(font_unicode_file, 11)
        # credit_fnt = ImageFont.truetype(font_bold_file, 10)

        def _write_unicode(text, init_x, y, font, unicode_font, fill):
            write_pos = init_x

            for char in text:
                if char.isalnum() or char in string.punctuation or char in string.whitespace:
                    draw.text((write_pos, y), char, font=font, fill=fill)
                    write_pos += font.getsize(char)[0]
                else:
                    draw.text((write_pos, y), "{}".format(char), font=unicode_font, fill=fill)
                    write_pos += unicode_font.getsize(char)[0]

        userinfo = await self.db.users.find_one({"user_id": str(self.user_data["id"])})
        # get urls
        bg_url = userinfo["rank_background"]

        try:
            async with self.session.get(self.server_data["icon"]) as r:
                server_icon = BytesIO(await r.read())
        except aiohttp.ClientConnectionError:
            server_icon = f"{working_path}/data/images/defaultguildicon.png"

        # rank bg image
        async with self.session.get(bg_url) as r:
            image = await r.content.read()
        rank_background = BytesIO(image)

        # user icon image
        async with self.session.get(self.user_data["avatar"]) as r:
            rank_avatar = BytesIO(await r.read())

        # set all to RGBA
        bg_image = Image.open(rank_background).convert("RGBA")
        profile_image = Image.open(rank_avatar).convert("RGBA")
        server_icon_image = Image.open(server_icon).convert("RGBA")

        # set canvas
        width = 360
        height = 100
        bg_color = (255, 255, 255, 0)
        result = Image.new("RGBA", (width, height), bg_color)
        process = Image.new("RGBA", (width, height), bg_color)

        # puts in background
        bg_image = bg_image.resize((width, height), Image.ANTIALIAS)
        bg_image = bg_image.crop((0, 0, width, height))
        result.paste(bg_image, (0, 0))

        # draw
        draw = ImageDraw.Draw(process)

        # draw transparent overlay
        vert_pos = 5
        left_pos = 70
        right_pos = width - vert_pos
        title_height = 22
        gap = 3

        draw.rectangle(
            [(left_pos - 20, vert_pos), (right_pos, vert_pos + title_height)],
            fill=(230, 230, 230, 230),
        )  # title box
        content_top = vert_pos + title_height + gap
        content_bottom = 100 - vert_pos

        if "rank_info_color" in userinfo.keys():
            info_color = tuple(userinfo["rank_info_color"])
            info_color = (
                info_color[0],
                info_color[1],
                info_color[2],
                160,
            )  # increase transparency
        else:
            info_color = (30, 30, 30, 160)
        draw.rectangle(
            [(left_pos - 20, content_top), (right_pos, content_bottom)],
            fill=info_color,
            outline=(180, 180, 180, 180),
        )  # content box

        # stick in credits if needed
        # if bg_url in bg_credits.keys():
        # credit_text = " ".join("{}".format(bg_credits[bg_url]))
        # draw.text((2, 92), credit_text,  font=credit_fnt, fill=(0,0,0,190))

        # draw level circle
        multiplier = 6
        lvl_circle_dia = 94
        circle_left = 15
        circle_top = int((height - lvl_circle_dia) / 2)
        raw_length = lvl_circle_dia * multiplier

        # create mask
        mask = Image.new("L", (raw_length, raw_length), 0)
        draw_thumb = ImageDraw.Draw(mask)
        draw_thumb.ellipse((0, 0) + (raw_length, raw_length), fill=255, outline=0)

        # drawing level bar calculate angle
        start_angle = -90  # from top instead of 3oclock
        angle = (
            int(
                360
                * (
                    userinfo["servers"][str(self.server_data["id"])]["current_exp"]
                    / self._required_exp(userinfo["servers"][str(self.server_data["id"])]["level"])
                )
            )
            + start_angle
        )

        lvl_circle = Image.new("RGBA", (raw_length, raw_length))
        draw_lvl_circle = ImageDraw.Draw(lvl_circle)
        draw_lvl_circle.ellipse(
            [0, 0, raw_length, raw_length], fill=(180, 180, 180, 180), outline=(255, 255, 255, 220)
        )
        # determines exp bar color
        if "rank_exp_color" not in userinfo.keys() or not userinfo["rank_exp_color"]:
            exp_fill = (255, 255, 255, 230)
        else:
            exp_fill = tuple(userinfo["rank_exp_color"])
        draw_lvl_circle.pieslice(
            [0, 0, raw_length, raw_length],
            start_angle,
            angle,
            fill=exp_fill,
            outline=(255, 255, 255, 230),
        )
        # put on level bar circle
        lvl_circle = lvl_circle.resize((lvl_circle_dia, lvl_circle_dia), Image.ANTIALIAS)
        lvl_bar_mask = mask.resize((lvl_circle_dia, lvl_circle_dia), Image.ANTIALIAS)
        process.paste(lvl_circle, (circle_left, circle_top), lvl_bar_mask)

        # draws mask
        total_gap = 10
        border = int(total_gap / 2)
        profile_size = lvl_circle_dia - total_gap
        raw_length = profile_size * multiplier
        # put in profile picture
        output = ImageOps.fit(profile_image, (raw_length, raw_length), centering=(0.5, 0.5))
        output.resize((profile_size, profile_size), Image.ANTIALIAS)
        mask = mask.resize((profile_size, profile_size), Image.ANTIALIAS)
        profile_image = profile_image.resize((profile_size, profile_size), Image.ANTIALIAS)
        process.paste(profile_image, (circle_left + border, circle_top + border), mask)

        # draw level box
        level_left = 274
        level_right = right_pos
        draw.rectangle(
            [(level_left, vert_pos), (level_right, vert_pos + title_height)], fill="#AAA"
        )  # box
        lvl_text = "LEVEL {}".format(userinfo["servers"][str(self.server_data["id"])]["level"])
        draw.text(
            (self._center(level_left, level_right, lvl_text, level_label_fnt), vert_pos + 3),
            lvl_text,
            font=level_label_fnt,
            fill=(110, 110, 110, 255),
        )  # Level #

        # labels text colors
        white_text = (240, 240, 240, 255)
        dark_text = (35, 35, 35, 230)
        label_text_color = self._contrast(info_color, white_text, dark_text)

        # draw text
        grey_color = (110, 110, 110, 255)
        # white_color = (230, 230, 230, 255)

        # put in server picture
        server_size = content_bottom - content_top - 10
        server_border_size = server_size + 4
        radius = 20
        light_border = (150, 150, 150, 180)
        dark_border = (90, 90, 90, 180)
        border_color = self._contrast(info_color, light_border, dark_border)

        draw_server_border = Image.new(
            "RGBA",
            (server_border_size * multiplier, server_border_size * multiplier),
            border_color,
        )
        draw_server_border = self._add_corners(draw_server_border, int(radius * multiplier / 2))
        draw_server_border = draw_server_border.resize(
            (server_border_size, server_border_size), Image.ANTIALIAS
        )
        server_icon_image = server_icon_image.resize(
            (server_size * multiplier, server_size * multiplier), Image.ANTIALIAS
        )
        server_icon_image = self._add_corners(server_icon_image, int(radius * multiplier / 2) - 10)
        server_icon_image = server_icon_image.resize((server_size, server_size), Image.ANTIALIAS)
        process.paste(
            draw_server_border,
            (circle_left + profile_size + 2 * border + 8, content_top + 3),
            draw_server_border,
        )
        process.paste(
            server_icon_image,
            (circle_left + profile_size + 2 * border + 10, content_top + 5),
            server_icon_image,
        )

        # name
        left_text_align = 130
        _write_unicode(
            self.user_data["truncate_name"],
            left_text_align - 12,
            vert_pos + 3,
            name_fnt,
            header_u_fnt,
            grey_color,
        )  # Name

        # divider bar
        draw.rectangle([(187, 45), (188, 85)], fill=(160, 160, 160, 220))

        # labels
        label_align = 200
        draw.text(
            (label_align, 38), "Server Rank:", font=general_info_fnt, fill=label_text_color
        )  # Server Rank
        draw.text(
            (label_align, 58), "Server Exp:", font=general_info_fnt, fill=label_text_color
        )  # Server Exp
        draw.text(
            (label_align, 78), "Credits:", font=general_info_fnt, fill=label_text_color
        )  # Credit
        # info
        right_text_align = 290
        draw.text(
            (right_text_align, 38),
            self._truncate_text(str(self.server_data['rank']), 12),
            font=general_info_fnt,
            fill=label_text_color,
        )  # Rank
        draw.text(
            (right_text_align, 58),
            self._truncate_text(str(self.server_data["exp"]), 12),
            font=general_info_fnt,
            fill=label_text_color,
        )  # Exp
        draw.text(
            (right_text_align, 78),
            self._truncate_text(f"${self.user_data['bank_balance']}", 12),
            font=general_info_fnt,
            fill=label_text_color,
        )  # Credits

        image_object = BytesIO()
        result = Image.alpha_composite(result, process)
        result.save(image_object, format="PNG")
        image_object.seek(0)
        return image_object
