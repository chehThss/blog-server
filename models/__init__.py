from motor import motor_asyncio
from .user import User
from .post import Post
from .event import Event
from .file import Repo
from .settings import Settings
from .post_categories import PostCategories
from .related_data_handlers import RelatedDataHandlers


class Models:
    def __init__(self, config):
        self.config = config
        self.client = motor_asyncio.AsyncIOMotorClient(self.config['db'])
        self.db = self.client.get_default_database()
        self.event = Event()
        self.user = User(self)
        self.file = Repo(self)
        self.post = Post(self)
        self.settings = Settings(self)
        self.post_categories = PostCategories(self)
        self.related_data_handlers = RelatedDataHandlers(self)

    async def startup(self):
        await self.user.startup()
        await self.post.startup()
        await self.settings.startup()
        await self.post_categories.startup()

    async def shutdown(self):
        self.client.close()
