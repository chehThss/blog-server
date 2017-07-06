class RelatedDataHandlers:
    def __init__(self, models):
        self.models = models
        self.models.event.on("user-remove", self.remove_user_post)
        self.models.event.on("category-remove", self.remove_category_from_post)

    async def remove_user_post(self, data):
        uid = data['id']
        post_list = (await self.models.post.list(uid, None))
        if post_list:
            for pid in post_list:
                await self.models.post.unpublish(pid)

    async def remove_category_from_post(self, data):
        cid = data['id']
        post_list = (await self.models.post.list(None, cid))
        if post_list:
            for pid in post_list:
                old_categories = (await self.models.post.info(pid))['categories']
                old_categories.remove(cid)
                await self.models.post.update({"id": pid, "categories": old_categories})