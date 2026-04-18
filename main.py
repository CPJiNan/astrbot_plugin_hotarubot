import random
import time
from pathlib import Path

from astrbot.api import logger
from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star, register
from astrbot.core.message.components import Plain, Image, Record

from .http import HttpUtils
from .storage import UserStorage, ImageStorage


@register(
    "astrbot_plugin_hotarubot",
    "季楠",
    "HotaruBot",
    "1.0.0"
)
class HotaruBotPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)
        self.user_storage = None
        self.image_storage = None
        self.images_dir = None
        self.record_dir = None

    async def initialize(self):
        logger.info("插件加载成功。")
        storage_path = Path.cwd() / "data" / "plugin_data" / self.name
        self.user_storage = UserStorage(storage_path)
        self.image_storage = ImageStorage(storage_path)
        self.images_dir = storage_path / "images"
        self.images_dir.mkdir(parents=True, exist_ok=True)
        self.record_dir = storage_path / "records"
        self.record_dir.mkdir(parents=True, exist_ok=True)

    async def terminate(self):
        logger.info("插件卸载成功。")

    @filter.command("命令帮助", alias={"help"})
    async def help(self, event: AstrMessageEvent):
        """命令帮助"""
        message = event.message_str
        try:
            if " " in message:
                current_page = int(message.split(" ")[1].strip())
            else:
                current_page = 1
        except ValueError:
            current_page = 1

        if current_page == 1:
            help_text = "萤宝BOT 命令帮助：" + \
                        "\n" + \
                        "\n /会萤吗 - 随机数生成器" + \
                        "\n" + \
                        "\n /最新萤图 - 最新汐见萤图片" + \
                        "\n /随机萤图 - 随机汐见萤图片" + \
                        "\n /萤图ID <图片ID> - 根据 ID 搜索图片" + \
                        "\n /萤图描述 <图片描述> - 根据描述搜索图片" + \
                        "\n" + \
                        "\n /收萤 - 收录回复的消息中所有的图片" + \
                        "\n /设置描述 <图片ID> <图片描述> - 设置图片描述" + \
                        "\n" + \
                        "\n /新增收萤员 <QQ号> - 为用户新增图片收录权限" + \
                        "\n /移除收萤员 <QQ号> - 移除用户的图片收录权限" + \
                        "\n" + \
                        "\n 第 1 页 / 共 3 页"
        elif current_page == 2:
            help_text = "萤宝BOT 命令帮助：" + \
                        "\n" + \
                        "\n /用户管理 用户信息 [QQ号] - 查看用户信息" + \
                        "\n /用户管理 新增用户 <QQ号> - 新增用户数据" + \
                        "\n /用户管理 移除用户 <QQ号> - 移除用户数据" + \
                        "\n" + \
                        "\n /权限管理 查看用户权限 <QQ号> - 查看用户的权限" + \
                        "\n /权限管理 新增用户权限 <QQ号> <权限> - 为用户新增权限" + \
                        "\n /权限管理 移除用户权限 <QQ号> <权限> - 移除用户的权限" + \
                        "\n" + \
                        "\n 第 2 页 / 共 3 页"
        elif current_page == 3:
            help_text = "萤宝BOT 命令帮助：" + \
                        "\n" + \
                        "\n 反馈邮箱：ShiomiHotaru@126.com" + \
                        "\n" + \
                        "\n 第 3 页 / 共 3 页"
        else:
            help_text = "未找到指定页面哦。"

        yield event.plain_result(help_text)

    @filter.command_group("用户管理")
    def user(self):
        """用户管理"""
        pass

    @user.command("用户信息")
    async def user_info(self, event: AstrMessageEvent, user_id: int = None):
        """查看用户信息"""
        if user_id is None:
            user_id = int(event.get_sender_id())

        yield event.plain_result(f"用户 ID： {user_id}")

    @user.command("新增用户")
    async def add_user(self, event: AstrMessageEvent, user_id: int):
        """新增用户"""
        sender_id = int(event.get_sender_id())
        if not self.user_storage.has_permission(sender_id, "admin"):
            yield event.plain_result("你没有使用新增用户命令的权限哦。")
            return
        self.user_storage.add_user(user_id)
        yield event.plain_result(f"已新增用户 {user_id}。")

    @user.command("移除用户")
    async def remove_user(self, event: AstrMessageEvent, user_id: int):
        """移除用户"""
        sender_id = int(event.get_sender_id())
        if not self.user_storage.has_permission(sender_id, "admin"):
            yield event.plain_result("你没有使用移除用户命令的权限哦。")
            return
        self.user_storage.remove_user(user_id)
        yield event.plain_result(f"已移除用户 {user_id}。")

    @filter.command_group("权限管理")
    def permission(self):
        """权限管理"""
        pass

    @permission.command("查看用户权限")
    async def get_permissions(self, event: AstrMessageEvent, user_id: int):
        """查看用户权限"""
        sender_id = int(event.get_sender_id())
        if not self.user_storage.has_permission(sender_id, "admin") and not self.user_storage.has_permission(sender_id,
                                                                                                             "permission.get"):
            yield event.plain_result("你没有使用查看用户权限命令的权限哦。")
            return
        permissions = self.user_storage.get_permissions(user_id)
        if permissions:
            perm_text = "\n+".join(permissions)
            yield event.plain_result(f"用户 {user_id} 有以下权限：\n+{perm_text}")
        else:
            yield event.plain_result(f"用户 {user_id} 没有任何权限。")

    @permission.command("新增用户权限")
    async def add_permission(self, event: AstrMessageEvent, user_id: int, permission: str):
        """新增用户权限"""
        sender_id = int(event.get_sender_id())
        if not self.user_storage.has_permission(sender_id, "admin") and not self.user_storage.has_permission(sender_id,
                                                                                                             "permission.add"):
            yield event.plain_result("你没有使用新增用户权限命令的权限哦。")
            return
        self.user_storage.add_permission(user_id, permission)
        yield event.plain_result(f"已为用户 {user_id} 新增 {permission} 权限。")

    @permission.command("移除用户权限")
    async def remove_permission(self, event: AstrMessageEvent, user_id: int, permission: str):
        """移除用户权限"""
        sender_id = int(event.get_sender_id())
        if not self.user_storage.has_permission(sender_id, "admin") and not self.user_storage.has_permission(sender_id,
                                                                                                             "permission.remove"):
            yield event.plain_result("你没有使用移除用户权限命令的权限哦。")
            return
        self.user_storage.remove_permission(user_id, permission)
        yield event.plain_result(f"已移除用户 {user_id} 的 {permission} 权限。")

    @filter.command("会萤吗")
    async def roll(self, event: AstrMessageEvent):
        """随机数生成器"""
        value = random.randint(0, 100)

        if 0 <= value <= 19:
            type_ = "小小萤"
        elif 20 <= value <= 39:
            type_ = "小萤"
        elif 40 <= value <= 59:
            type_ = "中萤"
        elif 60 <= value <= 79:
            type_ = "大萤"
        elif 80 <= value <= 100:
            type_ = "大萤特萤"
        else:
            type_ = ""

        message = f"本次萤度为「{value}」，评价为{type_}。"
        yield event.plain_result(message)

    @filter.command("萤图ID")
    async def get_image_by_id(self, event: AstrMessageEvent, image_id: int):
        """根据 ID 搜索图片"""
        image = self.image_storage.get_image_by_id(image_id)
        if not image:
            yield event.plain_result("未找到指定图片哦。")
            return

        import time
        upload_time = time.strftime("%Y/%m/%d %H:%M:%S", time.localtime(image["uploadTime"] / 1000))
        desc = f"\n图片描述：{image['description']}" if image['description'] else ""
        uploader = f"\n图片上传者：{image['uploader']}" if image['uploader'] != -1 else ""
        message = f"图片 ID：「{image['id']}」{desc}{uploader}\n图片上传时间：{upload_time}"

        image_path = self.images_dir / image['file']
        if image_path.exists():
            chain = [
                Image.fromFileSystem(str(image_path)),
                Plain(message)
            ]
            yield event.chain_result(chain)
        else:
            yield event.plain_result(message)

    @filter.command("萤图描述")
    async def get_image_by_description(self, event: AstrMessageEvent, description: str):
        """根据描述搜索图片"""
        images = self.image_storage.get_images_by_description(description)
        if not images:
            yield event.plain_result("未找到指定图片哦。")
            return

        image = images[0]
        import time
        upload_time = time.strftime("%Y/%m/%d %H:%M:%S", time.localtime(image["uploadTime"] / 1000))
        desc = f"\n图片描述：{image['description']}" if image['description'] else ""
        uploader = f"\n图片上传者：{image['uploader']}" if image['uploader'] != -1 else ""
        related_ids = f"\n所有相关图片 ID：" + "、".join([f"「{img['id']}」" for img in images]) if len(images) > 1 else ""
        message = f"图片 ID：「{image['id']}」{desc}{uploader}\n图片上传时间：{upload_time}{related_ids}"

        image_path = self.images_dir / image['file']
        if image_path.exists():
            chain = [
                Image.fromFileSystem(str(image_path)),
                Plain(message)
            ]
            yield event.chain_result(chain)
        else:
            yield event.plain_result(message)

    @filter.command("随机萤图")
    async def get_random_image(self, event: AstrMessageEvent):
        """随机汐见萤图片"""
        image = self.image_storage.get_random_image()
        if not image:
            yield event.plain_result("图库中暂无图片哦。")
            return

        upload_time = time.strftime("%Y/%m/%d %H:%M:%S", time.localtime(image["uploadTime"] / 1000))
        desc = f"\n图片描述：{image['description']}" if image['description'] else ""
        uploader = f"\n图片上传者：{image['uploader']}" if image['uploader'] != -1 else ""
        message = f"图片 ID：「{image['id']}」{desc}{uploader}\n图片上传时间：{upload_time}"

        image_path = self.images_dir / image['file']
        if image_path.exists():
            chain = [
                Image.fromFileSystem(str(image_path)),
                Plain(message + "\n")
            ]
            yield event.chain_result(chain)
        else:
            yield event.plain_result(message)

    @filter.command("最新萤图")
    async def get_latest_image(self, event: AstrMessageEvent):
        """最新汐见萤图片"""
        image = self.image_storage.get_latest_image()
        if not image:
            yield event.plain_result("未找到指定图片哦。")
            return

        import time
        upload_time = time.strftime("%Y/%m/%d %H:%M:%S", time.localtime(image["uploadTime"] / 1000))
        desc = f"\n图片描述：{image['description']}" if image['description'] else ""
        uploader = f"\n图片上传者：{image['uploader']}" if image['uploader'] != -1 else ""
        message = f"图片 ID：「{image['id']}」{desc}{uploader}\n图片上传时间：{upload_time}"

        image_path = self.images_dir / image['file']
        if image_path.exists():
            chain = [
                Image.fromFileSystem(str(image_path)),
                Plain(message)
            ]
            yield event.chain_result(chain)
        else:
            yield event.plain_result(message)

    @filter.command("收萤")
    async def upload_image(self, event: AstrMessageEvent):
        """收录回复的消息中所有的图片"""
        user_id = int(event.get_sender_id())
        if not self.user_storage.has_permission(user_id, "admin") and not self.user_storage.has_permission(user_id,
                                                                                                           "image.upload"):
            yield event.plain_result("你没有使用收萤命令的权限哦。")
            return

        messages = event.get_messages()
        reply_message = None
        for message in messages:
            if hasattr(message, 'type') and message.type == 'Reply':
                reply_message = message
                break

        if not reply_message:
            return

        image_urls = []
        if hasattr(reply_message, 'chain'):
            for message in reply_message.chain:
                if hasattr(message, 'type') and message.type == 'Image':
                    if hasattr(message, 'url') and message.url:
                        image_urls.append(message.url)

        if not image_urls:
            yield event.plain_result("未在该消息中找到图片哦。")
            return

        images = []

        for image_url in image_urls:
            try:
                content, _ = await HttpUtils.get(image_url)
                if not content:
                    continue

                image_bytes = content
                format = None

                if len(image_bytes) >= 8 and image_bytes[0] == 0x89 and image_bytes[1] == 0x50 and image_bytes[
                    2] == 0x4E and image_bytes[3] == 0x47:
                    format = "png"
                elif len(image_bytes) >= 2 and image_bytes[0] == 0xFF and image_bytes[1] == 0xD8:
                    format = "jpg"
                elif len(image_bytes) >= 6 and image_bytes[0] == 0x47 and image_bytes[1] == 0x49 and image_bytes[
                    2] == 0x46:
                    format = "gif"
                elif len(image_bytes) >= 2 and image_bytes[0] == 0x42 and image_bytes[1] == 0x4D:
                    format = "bmp"
                elif len(image_bytes) >= 4 and image_bytes[0] == 0x52 and image_bytes[1] == 0x49 and image_bytes[
                    2] == 0x46 and image_bytes[3] == 0x46:
                    format = "webp"

                if format is None:
                    yield event.plain_result("是未知的图片格式呢。")
                    continue

                image_id = self.image_storage.next_id()
                image = self.image_storage.upload_image(
                    id=image_id,
                    file=f"{image_id}.{format}",
                    description="",
                    uploader=int(reply_message.sender_id) if hasattr(reply_message, 'sender_id') else -1
                )
                file_path = self.images_dir / image['file']
                with open(file_path, 'wb') as f:
                    f.write(image_bytes)
                images.append(image)
            except Exception:
                return
        if images:
            image_info = ""
            for index, image in enumerate(images):
                image_info += f"\n第 {index + 1} 张图片的 ID 为「{image['id']}」。"
            yield event.plain_result(f"成功收萤 {len(images)} 张图片。{image_info}")

    @filter.command("设置描述")
    async def set_image_description(self, event: AstrMessageEvent, image_id: int, description: str):
        """设置图片描述"""
        user_id = int(event.get_sender_id())
        if not self.user_storage.has_permission(user_id, "admin") and not self.user_storage.has_permission(user_id,
                                                                                                           "image.description"):
            yield event.plain_result("你没有使用设置图片描述命令的权限哦。")
            return

        image = self.image_storage.set_image_description(image_id, description)
        if not image:
            yield event.plain_result("未找到指定图片哦。")
            return

        yield event.plain_result(f"已设置「{image_id}」的图片描述为：{description}")

    @filter.command("新增收萤员")
    async def add_uploader(self, event: AstrMessageEvent, user_id: int):
        """为用户新增图片收录权限"""
        sender_id = int(event.get_sender_id())
        if not self.user_storage.has_permission(sender_id, "admin") and not self.user_storage.has_permission(sender_id,
                                                                                                             "uploader.add"):
            yield event.plain_result("你没有使用新增收萤员命令的权限哦。")
            return

        self.user_storage.add_permission(user_id, "image.upload")
        self.user_storage.add_permission(user_id, "image.description")
        yield event.plain_result(f"已为用户 {user_id} 新增收萤员权限。")

    @filter.command("移除收萤员")
    async def remove_uploader(self, event: AstrMessageEvent, user_id: int):
        """移除用户的图片收录权限"""
        sender_id = int(event.get_sender_id())
        if not self.user_storage.has_permission(sender_id, "admin") and not self.user_storage.has_permission(sender_id,
                                                                                                             "uploader.remove"):
            yield event.plain_result("你没有使用移除收萤员命令的权限哦。")
            return

        self.user_storage.remove_permission(user_id, "image.upload")
        self.user_storage.remove_permission(user_id, "image.description")
        yield event.plain_result(f"已移除用户 {user_id} 的收萤员权限。")

    @filter.on_decorating_result()
    async def on_decorating_result(self, event: AstrMessageEvent):
        result = event.get_result()
        if not result:
            return

        tag = "%record:起死开战%"
        has_tag = False
        components = []

        for component in result.chain:
            if isinstance(component, Plain):
                if tag in component.text:
                    has_tag = True
                    text = component.text.replace(tag, "").strip()
                    if text:
                        components.append(Plain(text))
                else:
                    components.append(component)
            else:
                components.append(component)

        if has_tag:
            index = random.randint(1, 7)
            path = str(self.record_dir / f"起死開戦_{index}.wav")
            components.append(Record(file=path, url=path))
            result.chain = components
