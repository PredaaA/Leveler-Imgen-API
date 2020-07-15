import aiohttp
import asyncio
import operator
from pydantic import BaseModel

from app.images.db.mongodb import mongodb


async def create_session():
    return aiohttp.ClientSession()


session = asyncio.get_event_loop().run_until_complete(create_session())


class ImageGeneration:
    def __init__(self, data: BaseModel):
        self.user_data = data.user
        self.server_data = data.server
        self.config_data = data.config

        self._mongo_db = mongodb
        self.db = self._mongo_db.db
        self._db_ready = self._mongo_db._db_ready
        self.session = session

    async def draw(self):
        raise NotImplementedError()

    @staticmethod
    def _required_exp(level: int):
        if level < 0:
            return 0
        return 139 * level + 65

    @staticmethod
    def _truncate_text(text, max_length):
        if len(text) > max_length:
            if text.strip("$").isdigit():
                text = int(text.strip("$"))
                return "${:.2E}".format(text)
            return text[: max_length - 3] + "..."
        return text

    @staticmethod
    def _luminance(color):
        # convert to greyscale
        luminance = float((0.2126 * color[0]) + (0.7152 * color[1]) + (0.0722 * color[2]))
        return luminance

    def _contrast_ratio(self, bgcolor, foreground):
        f_lum = float(self._luminance(foreground) + 0.05)
        bg_lum = float(self._luminance(bgcolor) + 0.05)

        if bg_lum > f_lum:
            return bg_lum / f_lum
        else:
            return f_lum / bg_lum

    def _contrast(self, bg_color, color1, color2):
        color1_ratio = self._contrast_ratio(bg_color, color1)
        color2_ratio = self._contrast_ratio(bg_color, color2)
        if color1_ratio >= color2_ratio:
            return color1
        else:
            return color2

    @staticmethod
    def _center(start, end, text, font):
        dist = end - start
        width = font.getsize(text)[0]
        start_pos = start + ((dist - width) / 2)
        return int(start_pos)

    @staticmethod
    def _required_exp(level: int):
        if level < 0:
            return 0
        return 139 * level + 65
