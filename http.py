import aiohttp
from typing import Optional, Tuple


class HttpUtils:
    def __init__(self):
        pass

    @staticmethod
    async def get(url: str) -> Tuple[Optional[bytes], Optional[str]]:
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url) as response:
                    if response.status == 200:
                        content = await response.read()
                        content_type = response.headers.get('Content-Type')
                        return content, content_type
                    return None, None
            except Exception:
                return None, None
        return None
