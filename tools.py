from pathlib import Path
from typing import Union
import httpx
from tenacity import AsyncRetrying, RetryError, stop_after_attempt
from tenacity import retry, stop_after_attempt, wait_random
from botoy.pool import WorkerPool
from botoy import logger, Action, GroupMsg, FriendMsg, jconfig
import threading
from .files.config import config

# curFileDir = Path(__file__).parent  # 当前文件路径

headers = config.headers
cookies = config.cookies

curFileDir = Path(__file__).parent  # 当前文件路径


@retry(stop=stop_after_attempt(3), retry_error_callback=lambda
        retry_state: str(curFileDir / "files" / "error.jpg"))
def download_to_bytes(url, client: httpx.Client) -> bytes:
    res = client.get(url)
    if res.status_code != 200:
        logger.warning("download_cover: res.status_code != 200")
        raise Exception("download: res.status_code != 200")
    return res.content


class DownloadArchive(threading.Thread):
    def __init__(self, groupid, url, filename):
        threading.Thread.__init__(self)
        self._daemonic = False
        self.groupid = groupid
        self.url = url
        self.filename = filename
        self.filePath = curFileDir / "download" / self.filename

    def send(self):
        action = Action(jconfig.bot, host=jconfig.host, port=jconfig.port)
        logger.warning("开始上传群文件")
        # action.uploadGroupFile(self.groupid, filePath="/root/health_sign/testfile.txt")
        action.uploadGroupFile(self.groupid, filePath=str(self.filePath))

    @retry(stop=stop_after_attempt(3), retry_error_callback=lambda
            retry_state: print("下载error"))
    def downlaod(self):
        logger.warning(f"开始下载{self.filename}")
        res = httpx.get(self.url, headers=headers, cookies=cookies).content
        with open(self.filePath, 'wb') as f:
            f.write(res)
        logger.warning(f"{self.filename}下载完成")

    def run(self):
        self.downlaod()
        self.send()
