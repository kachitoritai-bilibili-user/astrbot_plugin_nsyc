from astrbot.api.event import filter, AstrMessageEvent, MessageEventResult
from astrbot.api.star import Context, Star, register
import astrbot.api.message_components as Comp
from astrbot.api import logger
import os
import json
import random
import aiohttp


@register("nsyimages", "kachitoritai", "女声优图片管理插件", "1.0")
class NSYImagesPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)
        self.images_path = r"/AstrBot/nsy"
        self.nickname_file = os.path.join(self.images_path, "nicknames.json")
        self.names = []
        self.nicknames = dict()
        # self.upload = dict()

    async def initialize(self):
        """初始化插件"""
        if not os.path.exists(self.images_path):
            os.makedirs(self.images_path)
        self._update_names()
        if os.path.exists(self.nickname_file):
            try:
                with open(self.nickname_file, "r", encoding="utf-8") as f:
                    self.nicknames = json.load(f)
                logger.info(f"✅ 已加载 {len(self.nicknames)} 条黑称映射")
            except Exception as e:
                logger.warning(f"加载黑称文件失败: {e}")
                self.nicknames = {}
        else:
            self.nicknames = {}
        for name in self.names:
            self.nicknames[name] = name
        logger.info("✅ nsyimages 插件初始化完成")

    def _update_names(self):
        self.names = [d for d in os.listdir(self.images_path)
                      if os.path.isdir(os.path.join(self.images_path, d))]

    def _save_nicknames(self):
        """将黑称映射保存到 JSON 文件"""
        try:
            with open(self.nickname_file, "w", encoding="utf-8") as f:
                json.dump(self.nicknames, f, ensure_ascii=False, indent=2)
            logger.info("✅ 黑称映射已保存")
        except Exception as e:
            logger.warning(f"保存黑称失败: {e}")

    def _random_image(self, name: str):
        """从某个声优文件夹中随机挑选一张图片"""
        imgdir = os.path.join(self.images_path, name)
        files = os.listdir(imgdir)
        if not files:
            return None
        random_img = random.choice(files)
        img_path = os.path.join(imgdir, random_img)
        return img_path, random_img

    # --------------------------------------------
    # ✅ nsy列表 指令
    # --------------------------------------------
    @filter.command("list")
    async def nsy_list(self, event: AstrMessageEvent):
        """查看可查询的声优列表"""
        self._update_names()
        if not self.names:
            yield event.plain_result("当前还没有任何声优图片，请使用 /add 添加~")
            return
        yield event.plain_result("支持查询的声优有：" + "，".join(self.names))

    # --------------------------------------------
    # ✅ nsy 指令
    # --------------------------------------------
    @filter.command("nsy")
    async def nsy(self, event: AstrMessageEvent):
        """nsy + 名字 → 获取图片"""
        name = event.message_str.strip().split(' ')[-1]
        name = self.nicknames[name]
        self._update_names()
        if not name:
            yield event.plain_result("请发送 /nsy + 声优名字")
            return
        if name not in self.names:
            yield event.plain_result("不包含您所查询的声优哦，您可以自行添加~")
            return

        img_info = self._random_image(name)
        if not img_info:
            yield event.plain_result("这个声优暂时没有图片哦~")
            return

        img_path, filename = img_info
        yield event.image_result(img_path)
        yield event.plain_result(f"{filename}，若与人物不符或您不喜欢这张图片，请联系bot主删除ww")

    # --------------------------------------------
    # ✅ 看nsy 指令
    # --------------------------------------------
    @filter.command("今日nsy")
    async def nsy_random(self, event: AstrMessageEvent):
        """随机声优图片"""
        self._update_names()
        if not self.names:
            yield event.plain_result("当前还没有声优图片，请先添加哦~")
            return

        name = random.choice(self.names)
        img_info = self._random_image(name)
        if not img_info:
            yield event.plain_result(f"{name} 暂无图片~")
            return

        img_path, filename = img_info
        yield event.image_result(img_path)
        yield event.plain_result(f"{filename}（来自 {name})")

    # --------------------------------------------
    # ✅ 添加nsy 指令
    # --------------------------------------------
    @filter.command("add")
    async def add_nsy(self, event: AstrMessageEvent):
        """添加新的声优目录"""
        name = event.message_str.strip().split(' ')[-1]
        if not name:
            yield event.plain_result("请发送 /add 声优名字")
            return
        self._update_names()
        path = os.path.join(self.images_path, name)
        if name in self.names or name in self.nicknames:
            yield event.plain_result("该声优已经存在了喵")
        else:
            os.mkdir(path)
            self.names.append(name)
            self.nicknames[name] = name
            self._save_nicknames()
            yield event.plain_result(f"已成功添加声优 {name}")

    # --------------------------------------------
    # ✅ 上传nsy 指令
    # --------------------------------------------
    # @filter.command("upload")
    # async def upload_nsy(self, event: AstrMessageEvent):
    #     """
    #     上传声优图片。
    #     用户应先发送：/upload 声优名
    #     然后发送一条或多条图片消息。
    #     """
    #     name = event.message_str.strip().split(' ')[-1]
    #     name = self.nicknames[name]
    #     self._update_names()
    #     if not name:
    #         yield event.plain_result("请发送 /upload 声优名字")
    #         return
    #     if name not in self.names:
    #         yield event.plain_result("未找到该声优，请先使用 /add 添加目录~")
    #         return

    #     yield event.plain_result("请直接发送图片")
    #     self.upload["upload_target"] = name

    @filter.command("upload")
    async def upload_by_reply(self, event: AstrMessageEvent):
        """
        用户通过回复图片消息并输入 /upload 名字 上传图片。
        """
        name = event.message_str.strip().split(' ')[-1]
        self._update_names()

        if not name:
            yield event.plain_result("请发送 /upload 声优名字")
            return
        if name not in self.names:
            yield event.plain_result("未找到该声优，请先使用 /add 添加目录~")
            return

        # 检查是否是回复图片消息
        logger.info(f'{event.message_obj.message}')
        reply_comp = None
        for comp in event.message_obj.message:
            comp_type = getattr(comp, "type", None)
            if comp_type and ("Reply" in str(comp_type)):
                reply_comp = comp
                break
        if not reply_comp:
            yield event.plain_result("请回复一条图片消息再使用 /upload 声优名字")
            return

        replied_chain = getattr(reply_comp, "chain", None)
        if not replied_chain:
            yield event.plain_result("未能获取被回复的消息内容，请确认你回复的是图片消息~")
            return

        # 查找被回复消息中的图片
        for msg in replied_chain:
            logger.info(f'msg.type.name: {msg.type.name}')
            msg_type = getattr(msg, "type", None)
            if msg_type and ("Image" in str(msg_type)):
                url = msg.url
                if not url:
                    continue
                upload_dir = os.path.join(self.images_path, name)
                filename = f"{len(os.listdir(upload_dir)) + 501}.jpg"
                await self._download_image(url, os.path.join(upload_dir, filename))
                yield event.plain_result(f"✅ 已成功为 {name} 上传图片！")
                return

        yield event.plain_result("未在被回复消息中找到图片，请确认回复的是一张图片~")

    @filter.event_message_type(filter.EventMessageType.ALL)
    async def direct_name_call(self, event: AstrMessageEvent):
        """处理上传图片的消息"""
        logger.info(f'{event.message_obj.message}')
        msg_chain = event.message_obj.message
        # 不在上传流程中 判断是否为nsy指令的变体
        for msg in msg_chain:
            msg_type_str = str(msg.type)
            if 'Plain' in msg_type_str and '/' not in msg.text and ' ' not in msg.text and len(msg.text) <= 7:
                name = msg.text
                if name not in self.nicknames:
                    return
                name = self.nicknames[name]
                if not name:
                    yield event.plain_result("很奇怪但是我也不知道发生了什么喵")
                    return
                if name not in self.names:
                    return
                img_info = self._random_image(name)
                if not img_info:
                    yield event.plain_result("这个声优暂时没有图片哦~")
                    return

                img_path, filename = img_info
                yield event.image_result(img_path)
                yield event.plain_result(f"{filename}，若与人物不符或您不喜欢这张图片，请联系bot主删除ww")   
                return

    async def _download_image(self, url, path):
        """异步下载图片"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, ssl=False) as resp:
                    content = await resp.read()
                    with open(path, "wb") as f:
                        f.write(content)
        except Exception as e:
            logger.warning(f"下载图片失败: {e}")

    # --------------------------------------------
    # ✅ 添加nsy黑称 指令
    # --------------------------------------------
    @filter.command("nickname")
    async def add_nickname(self, event: AstrMessageEvent):
        """添加新的声优目录"""
        msg_split = event.message_str.strip().split(' ')
        if len(msg_split) is not 3:
            yield event.plain_result("请发送 /nickname nickname name")
            return
        nickname = msg_split[1]
        name = msg_split[2]
        if not name or not nickname:
            yield event.plain_result("请发送 /nickname nickname name")
            return
        if name not in self.names:
            yield event.plain_result("没有找到对应的nsy喵")
        elif nickname in self.nicknames:
            if name != self.nicknames[nickname]:
                yield event.plain_result("黑称对应的nsy和存储的不一样喵，联系管理员~")
        else:
            #TODO 使用SQLite持久化存储黑称
            #TODO 支持表情类型的黑称
            self.nicknames[nickname] = name
            self._save_nicknames()
            yield event.plain_result(f"已成功添加声优 {name} 的黑称 {nickname}")

    # --------------------------------------------
    # ✅ 帮助指令
    # --------------------------------------------
    @filter.command("nsyhelp")
    async def nsy_help(self, event: AstrMessageEvent):
        """帮助信息"""
        help_text = """🎀 NSYImages 插件使用说明：
名字 → 获取对应声优图片
/今日nsy → 随机获取一张声优图片
/list → 查看当前支持的声优
/add 名字 → 添加一个新的声优目录
/upload 名字 → 上传该声优图片
/nickname 黑称 名字 → 为声优添加黑称
/nsyhelp → 查看帮助信息
"""
        yield event.plain_result(help_text)

