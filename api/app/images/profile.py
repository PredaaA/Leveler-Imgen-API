from app.images.image import ImageGeneration

import string
import asyncio
import operator
import platform
import textwrap
from pathlib import Path
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont, ImageOps

working_path = Path(__file__).resolve().parent


class Profile(ImageGeneration):
    async def _badge_convert_dict(self, userinfo):
        if "badges" not in userinfo or not isinstance(userinfo["badges"], dict):
            await self.db.users.update_one(
                {"user_id": userinfo["user_id"]}, {"$set": {"badges": {}}}
            )
        return await self.db.users.find_one({"user_id": userinfo["user_id"]})

    async def _valid_image_url(self, url):
        try:
            async with self.session.get(url) as r:
                image = await r.content.read()
            with open(working_path + f"data/tmp/test.png", "wb") as f:
                f.write(image)
            Image.open(working_path + f"data/tmp/test.png").convert("RGBA")
            os.remove(working_path + f"data/tmp/test.png")
            return True
        except:
            return False

    async def draw(self):
        if not self._db_ready:
            return None

        font_bold_file = f"{working_path}/data/fonts/font_bold.ttf"
        font_unicode_file = f"{working_path}/data/fonts/unicode.ttf"
        # name_fnt = ImageFont.truetype(font_bold_file, 22, encoding="utf-8")
        header_u_fnt = ImageFont.truetype(font_unicode_file, 18, encoding="utf-8")
        # title_fnt = ImageFont.truetype(font_file, 18, encoding="utf-8")
        sub_header_fnt = ImageFont.truetype(font_bold_file, 14, encoding="utf-8")
        # badge_fnt = ImageFont.truetype(font_bold_file, 10, encoding="utf-8")
        exp_fnt = ImageFont.truetype(font_bold_file, 14, encoding="utf-8")
        # large_fnt = ImageFont.truetype(font_bold_file, 33, encoding="utf-8")
        level_label_fnt = ImageFont.truetype(font_bold_file, 22, encoding="utf-8")
        general_info_fnt = ImageFont.truetype(font_bold_file, 15, encoding="utf-8")
        general_info_u_fnt = ImageFont.truetype(font_unicode_file, 12, encoding="utf-8")
        rep_fnt = ImageFont.truetype(font_bold_file, 26, encoding="utf-8")
        text_fnt = ImageFont.truetype(font_bold_file, 12, encoding="utf-8")
        text_u_fnt = ImageFont.truetype(font_unicode_file, 8, encoding="utf-8")
        # credit_fnt = ImageFont.truetype(font_bold_file, 10, encoding="utf-8")

        def _write_unicode(text, init_x, y, font, unicode_font, fill):
            write_pos = init_x

            for char in text:
                if char.isalnum() or char in string.punctuation or char in string.whitespace:
                    draw.text((write_pos, y), "{}".format(char), font=font, fill=fill)
                    write_pos += font.getsize(char)[0]
                else:
                    draw.text((write_pos, y), "{}".format(char), font=unicode_font, fill=fill)
                    write_pos += unicode_font.getsize(char)[0]

        # get urls
        userinfo = await self.db.users.find_one({"user_id": str(self.user_data["id"])})
        await self._badge_convert_dict(userinfo)
        bg_url = userinfo["profile_background"]

        async with self.session.get(bg_url) as r:
            profile_background = BytesIO(await r.read())

        async with self.session.get(self.user_data["avatar"]) as r:
            profile_avatar = BytesIO(await r.read())

        bg_image = Image.open(profile_background).convert("RGBA")
        profile_image = Image.open(profile_avatar).convert("RGBA")

        # set canvas
        bg_color = (255, 255, 255, 0)
        result = Image.new("RGBA", (290, 290), bg_color)
        process = Image.new("RGBA", (290, 290), bg_color)

        # draw
        draw = ImageDraw.Draw(process)

        # puts in background
        bg_image = bg_image.resize((290, 290), Image.ANTIALIAS)
        bg_image = bg_image.crop((0, 0, 290, 290))
        result.paste(bg_image, (0, 0))

        # draw filter
        draw.rectangle([(0, 0), (290, 290)], fill=(0, 0, 0, 10))

        # draw transparent overlay
        vert_pos = 110
        left_pos = 70
        right_pos = 285
        title_height = 22
        # gap = 3

        # determines rep section color
        if "rep_color" not in userinfo.keys() or not userinfo["rep_color"]:
            rep_fill = (92, 130, 203, 230)
        else:
            rep_fill = tuple(userinfo["rep_color"])
        # determines badge section color, should be behind the titlebar
        if "badge_col_color" not in userinfo.keys() or not userinfo["badge_col_color"]:
            badge_fill = (128, 151, 165, 230)
        else:
            badge_fill = tuple(userinfo["badge_col_color"])

        if "profile_info_color" in userinfo.keys():
            info_color = tuple(userinfo["profile_info_color"])
        else:
            info_color = (30, 30, 30, 220)

        draw.rectangle(
            [(left_pos - 20, vert_pos + title_height), (right_pos, 156)], fill=info_color
        )  # title box
        draw.rectangle([(100, 159), (285, 212)], fill=info_color)  # general content
        draw.rectangle([(100, 215), (285, 285)], fill=info_color)  # info content

        # stick in credits if needed
        # if bg_url in bg_credits.keys():
        # credit_text = "  ".join("Background by {}".format(bg_credits[bg_url]))
        # credit_init = 290 - credit_fnt.getsize(credit_text)[0]
        # draw.text((credit_init, 0), credit_text,  font=credit_fnt, fill=(0,0,0,100))
        draw.rectangle(
            [(5, vert_pos), (right_pos, vert_pos + title_height)], fill=(230, 230, 230, 230)
        )  # name box in front

        # draw level circle
        multiplier = 8
        lvl_circle_dia = 104
        circle_left = 1
        circle_top = 42
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

        # level outline
        lvl_circle = Image.new("RGBA", (raw_length, raw_length))
        draw_lvl_circle = ImageDraw.Draw(lvl_circle)
        draw_lvl_circle.ellipse(
            [0, 0, raw_length, raw_length],
            fill=(badge_fill[0], badge_fill[1], badge_fill[2], 180),
            outline=(255, 255, 255, 250),
        )
        # determines exp bar color
        if "profile_exp_color" not in userinfo.keys() or not userinfo["profile_exp_color"]:
            exp_fill = (255, 255, 255, 230)
        else:
            exp_fill = tuple(userinfo["profile_exp_color"])
        draw_lvl_circle.pieslice(
            [0, 0, raw_length, raw_length],
            start_angle,
            angle,
            fill=exp_fill,
            outline=(255, 255, 255, 255),
        )
        # put on level bar circle
        lvl_circle = lvl_circle.resize((lvl_circle_dia, lvl_circle_dia), Image.ANTIALIAS)
        lvl_bar_mask = mask.resize((lvl_circle_dia, lvl_circle_dia), Image.ANTIALIAS)
        process.paste(lvl_circle, (circle_left, circle_top), lvl_bar_mask)

        # draws boxes
        draw.rectangle([(5, 133), (100, 285)], fill=badge_fill)  # badges
        draw.rectangle([(10, 138), (95, 168)], fill=rep_fill)  # reps

        total_gap = 10
        # border = int(total_gap / 2)
        profile_size = lvl_circle_dia - total_gap
        # raw_length = profile_size * multiplier
        # put in profile picture
        total_gap = 6
        border = int(total_gap / 2)
        profile_size = lvl_circle_dia - total_gap
        mask = mask.resize((profile_size, profile_size), Image.ANTIALIAS)
        profile_image = profile_image.resize((profile_size, profile_size), Image.ANTIALIAS)
        process.paste(profile_image, (circle_left + border, circle_top + border), mask)

        # write label text
        white_color = (240, 240, 240, 255)
        light_color = (160, 160, 160, 255)

        head_align = 105
        _write_unicode(
            self.user_data["truncate_name"],
            head_align,
            vert_pos + 3,
            level_label_fnt,
            header_u_fnt,
            (110, 110, 110, 255),
        )  # NAME
        _write_unicode(
            userinfo["title"], head_align, 136, level_label_fnt, header_u_fnt, white_color
        )

        # draw level box
        level_right = 290
        level_left = level_right - 78
        draw.rectangle(
            [(level_left, 0), (level_right, 21)],
            fill=(badge_fill[0], badge_fill[1], badge_fill[2], 160),
        )  # box
        lvl_text = "LEVEL {}".format(userinfo["servers"][str(self.server_data["id"])]["level"])
        if badge_fill == (128, 151, 165, 230):
            lvl_color = white_color
        else:
            lvl_color = self._contrast(badge_fill, rep_fill, exp_fill)
        draw.text(
            (self._center(level_left + 2, level_right, lvl_text, level_label_fnt), 2),
            lvl_text,
            font=level_label_fnt,
            fill=(lvl_color[0], lvl_color[1], lvl_color[2], 255),
        )  # Level #

        rep_text = "{} REP".format(userinfo["rep"])
        draw.text(
            (self._center(7, 100, rep_text, rep_fnt), 144),
            rep_text,
            font=rep_fnt,
            fill=white_color,
        )

        exp_text = "{}/{}".format(
            userinfo["servers"][str(self.server_data["id"])]["current_exp"],
            self._required_exp(userinfo["servers"][str(self.server_data["id"])]["level"]),
        )  # Exp
        exp_color = exp_fill
        draw.text(
            (105, 99), exp_text, font=exp_fnt, fill=(exp_color[0], exp_color[1], exp_color[2], 255)
        )  # Exp Text

        # determine info text color
        dark_text = (35, 35, 35, 230)
        info_text_color = self._contrast(info_color, light_color, dark_text)

        # lvl_left = 100
        label_align = 105
        _write_unicode(
            "Rank:", label_align, 165, general_info_fnt, general_info_u_fnt, info_text_color
        )
        draw.text((label_align, 180), "Exp:", font=general_info_fnt, fill=info_text_color)  # Exp
        draw.text(
            (label_align, 195), "Credits:", font=general_info_fnt, fill=info_text_color
        )  # Credits

        # local stats
        num_local_align = 172
        # local_symbol = "\U0001F3E0 "
        if "linux" in platform.system().lower():
            local_symbol = "\U0001F3E0 "
        else:
            local_symbol = "S "

        s_rank_txt = local_symbol + self._truncate_text(f"#{self.server_data['rank']}", 8)
        _write_unicode(
            s_rank_txt,
            num_local_align - general_info_u_fnt.getsize(local_symbol)[0],
            165,
            general_info_fnt,
            general_info_u_fnt,
            info_text_color,
        )  # Rank

        s_exp_txt = self._truncate_text(str(self.server_data["exp"]), 8)
        _write_unicode(
            s_exp_txt, num_local_align, 180, general_info_fnt, general_info_u_fnt, info_text_color
        )  # Exp
        draw.text(
            (num_local_align, 195),
            self._truncate_text(f"${self.user_data['bank_balance']}", 18),
            font=general_info_fnt,
            fill=info_text_color,
        )  # Credits

        # global stats
        num_align = 230
        if "linux" in platform.system().lower():
            global_symbol = "\U0001F30E "
            fine_adjust = 1
        else:
            global_symbol = "G "
            fine_adjust = 0

        global_rank = self.user_data["global_rank"]
        rank_number = global_rank if global_rank else "1000+"
        rank_txt = global_symbol + self._truncate_text(f"#{rank_number}", 8)
        exp_txt = self._truncate_text(f"{userinfo['total_exp']}", 8)
        _write_unicode(
            rank_txt,
            num_align - general_info_u_fnt.getsize(global_symbol)[0] + fine_adjust,
            165,
            general_info_fnt,
            general_info_u_fnt,
            info_text_color,
        )  # Rank
        _write_unicode(
            exp_txt, num_align, 180, general_info_fnt, general_info_u_fnt, info_text_color
        )  # Exp

        draw.text((105, 220), "Info Box", font=sub_header_fnt, fill=white_color)  # Info Box
        margin = 105
        offset = 238
        for line in textwrap.wrap(userinfo["info"], width=42):
            await asyncio.sleep(0)
            # draw.text((margin, offset), line, font=text_fnt, fill=(70,70,70,255))
            _write_unicode(line, margin, offset, text_fnt, text_u_fnt, info_text_color)
            offset += text_fnt.getsize(line)[1] + 2

        # sort badges
        priority_badges = []

        for badgename in userinfo["badges"].keys():
            await asyncio.sleep(0)
            badge = userinfo["badges"][badgename]
            priority_num = badge["priority_num"]
            if priority_num != 0 and priority_num != -1:
                priority_badges.append((badge, priority_num))
        sorted_badges = sorted(priority_badges, key=operator.itemgetter(1), reverse=True)

        # TODO: simplify this. it shouldn't be this complicated... sacrifices conciseness for customizability
        badge_type = self.config_data["badge_type"]
        if badge_type == "circles":
            # circles require antialiasing
            vert_pos = 171
            right_shift = 0
            left = 9 + right_shift
            # right = 52 + right_shift
            size = 27
            total_gap = 4  # /2
            hor_gap = 3
            vert_gap = 2
            border_width = int(total_gap / 2)
            mult = [
                (0, 0),
                (1, 0),
                (2, 0),
                (0, 1),
                (1, 1),
                (2, 1),
                (0, 2),
                (1, 2),
                (2, 2),
                (0, 3),
                (1, 3),
                (2, 3),
            ]
            i = 0
            for pair in sorted_badges[:12]:
                try:
                    coord = (
                        left + int(mult[i][0]) * int(hor_gap + size),
                        vert_pos + int(mult[i][1]) * int(vert_gap + size),
                    )
                    badge = pair[0]
                    bg_color = badge["bg_img"]
                    border_color = badge["border_color"]
                    multiplier = 6  # for antialiasing
                    raw_length = size * multiplier

                    # draw mask circle
                    mask = Image.new("L", (raw_length, raw_length), 0)
                    draw_thumb = ImageDraw.Draw(mask)
                    draw_thumb.ellipse((0, 0) + (raw_length, raw_length), fill=255, outline=0)

                    # determine image or color for badge bg
                    if await self._valid_image_url(bg_color):
                        # get image
                        async with self.session.get(bg_color) as r:
                            image = await r.content.read()
                        with open(
                            f"{working_path}/data/tmp/{self.user_data['id']}_temp_badge.png", "wb"
                        ) as f:
                            f.write(image)
                        badge_image = Image.open(
                            f"{working_path}/data/tmp/{self.user_data['id']}_temp_badge.png"
                        ).convert("RGBA")
                        badge_image = badge_image.resize((raw_length, raw_length), Image.ANTIALIAS)

                        # structured like this because if border = 0, still leaves outline.
                        if border_color:
                            square = Image.new("RGBA", (raw_length, raw_length), border_color)
                            # put border on ellipse/circle
                            output = ImageOps.fit(
                                square, (raw_length, raw_length), centering=(0.5, 0.5)
                            )
                            output = output.resize((size, size), Image.ANTIALIAS)
                            outer_mask = mask.resize((size, size), Image.ANTIALIAS)
                            process.paste(output, coord, outer_mask)

                            # put on ellipse/circle
                            output = ImageOps.fit(
                                badge_image, (raw_length, raw_length), centering=(0.5, 0.5)
                            )
                            output = output.resize(
                                (size - total_gap, size - total_gap), Image.ANTIALIAS
                            )
                            inner_mask = mask.resize(
                                (size - total_gap, size - total_gap), Image.ANTIALIAS
                            )
                            process.paste(
                                output,
                                (coord[0] + border_width, coord[1] + border_width),
                                inner_mask,
                            )
                        else:
                            # put on ellipse/circle
                            output = ImageOps.fit(
                                badge_image, (raw_length, raw_length), centering=(0.5, 0.5)
                            )
                            output = output.resize((size, size), Image.ANTIALIAS)
                            outer_mask = mask.resize((size, size), Image.ANTIALIAS)
                            process.paste(output, coord, outer_mask)
                except:
                    pass
                i += 1
        elif badge_type == "bars":
            vert_pos = 187
            i = 0
            for pair in sorted_badges[:5]:
                badge = pair[0]
                bg_color = badge["bg_img"]
                border_color = badge["border_color"]
                left_pos = 10
                right_pos = 95
                total_gap = 4
                border_width = int(total_gap / 2)
                bar_size = (85, 15)

                # determine image or color for badge bg
                if await self._valid_image_url(bg_color):
                    async with self.session.get(bg_color) as r:
                        image = await r.content.read()
                    badge_image = Image.open(image).convert("RGBA")

                    if border_color is not None:
                        draw.rectangle(
                            [(left_pos, vert_pos + i * 17), (right_pos, vert_pos + 15 + i * 17)],
                            fill=border_color,
                            outline=border_color,
                        )  # border
                        badge_image = badge_image.resize(
                            (bar_size[0] - total_gap + 1, bar_size[1] - total_gap + 1),
                            Image.ANTIALIAS,
                        )
                        process.paste(
                            badge_image,
                            (left_pos + border_width, vert_pos + border_width + i * 17),
                        )
                    else:
                        badge_image = badge_image.resize(bar_size, Image.ANTIALIAS)
                        process.paste(badge_image, (left_pos, vert_pos + i * 17))

                vert_pos += 3  # spacing
                i += 1

        image_object = BytesIO()
        result = Image.alpha_composite(result, process)
        result.save(image_object, format="PNG")
        image_object.seek(0)
        return image_object
