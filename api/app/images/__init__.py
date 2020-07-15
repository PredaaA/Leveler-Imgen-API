from app.images.profile import Profile
from app.images.rank import Rank
from app.images.levelup import LevelUp


images_types = {"profile": Profile, "rank": Rank, "levelup": LevelUp}


async def draw_image(image_type: str, data):
    _class = images_types[image_type](data)
    data = await _class.draw()
    return data
