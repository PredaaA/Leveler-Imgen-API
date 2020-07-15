import ujson
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import errors as mongoerrors

with open("/data/config/mongoconfig.json") as configdata:
    config = ujson.load(configdata)


class MongoDB:
    def __init__(self):
        self.config = config
        self.client = None
        self.db = None
        self._db_ready = False

    async def initialize(self):
        if self._db_ready:
            self._db_ready = False
        self.disconnect()
        # config = await self.config.custom("MONGODB").all()
        # log.debug(f"Leveler is connecting to a MongoDB server at: {config}")
        try:
            self.client = AsyncIOMotorClient(
                **{k: v for k, v in self.config.items() if not k == "db_name"}
            )
            await self.client.server_info()
            self.db = self.client[self.config["db_name"]]
            self._db_ready = True
        except (
            mongoerrors.ServerSelectionTimeoutError,
            mongoerrors.ConfigurationError,
            mongoerrors.OperationFailure,
        ) as error:
            # log.exception(
            #     "Can't connect to the MongoDB server.\nFollow instructions on Git/online to install MongoDB.",
            #     exc_info=error,
            # )
            self.client = None
            self.db = None
        return self.client

    def disconnect(self):
        if self.client:
            self.client.close()


mongodb = MongoDB()
