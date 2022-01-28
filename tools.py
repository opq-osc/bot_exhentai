from pathlib import Path
from typing import Union
import httpx
import pyzipper
from botoy.contrib import get_cache_dir
from tenacity import AsyncRetrying, RetryError, stop_after_attempt
from tenacity import retry, stop_after_attempt, wait_random
from botoy.pool import WorkerPool
from botoy import logger, Action, GroupMsg, FriendMsg, jconfig
import threading
from .files.config import config
from ._proxies import transport, proxies

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
    def __init__(self, groupid, url, filename: str):
        threading.Thread.__init__(self)
        self._daemonic = False
        self.groupid = groupid
        self.url = url
        self.filename = filename
        self.filePath = curFileDir / "download" / self.filename
        self.pic_cache_dir = get_cache_dir(filename).absolute()
        self.zip_cache_dir = get_cache_dir("zip").absolute()
        self.action = Action(jconfig.bot, host=jconfig.host, port=jconfig.port)

    def encryption_zip_aes(self):
        if not pyzipper.is_zipfile(self.filePath):
            self.action.sendGroupText(self.groupid, "解压出错")
            return
        with pyzipper.ZipFile(self.filePath, 'r') as f:
            f.extractall(self.pic_cache_dir)
        files = [_ for _ in self.pic_cache_dir.iterdir()]
        print(files)
        with pyzipper.AESZipFile(self.zip_cache_dir / self.filename, "w", compression=pyzipper.ZIP_BZIP2,
                                 compresslevel=9) as zf:
            zf.setpassword(self.filename.encode())
            zf.setencryption(pyzipper.WZ_AES, nbits=128)
            for file in files:
                zf.write(filename=file, arcname=file.name)

    def send(self):
        self.encryption_zip_aes()
        self.action.sendGroupText(self.groupid,
                                  f"{self.filename}\r\n大小:{round(Path(self.zip_cache_dir / self.filename).stat().st_size / 1024 / 1024, 2)}MB\r\n解压密码为压缩包文件名")
        logger.warning("开始上传群文件")
        # self.action.uploadGroupFile(self.groupid, filePath="/root/health_sign/testfile.txt")
        self.action.uploadGroupFile(self.groupid, filePath=str(self.zip_cache_dir / self.filename))

    @retry(stop=stop_after_attempt(3), retry_error_callback=lambda
            retry_state: print("下载error"))
    def downlaod(self):
        self.action.sendGroupText(self.groupid, "开始下载,请耐心等待~")
        logger.warning(f"开始下载{self.filename}")
        with httpx.Client( headers=headers, cookies=cookies, proxies=proxies, transport=transport) as client:
            res = client.get(self.url).content
            with open(self.filePath, 'wb') as f:
                f.write(res)
        logger.warning(f"{self.filename}下载完成")

    def run(self):
        self.downlaod()
        self.send()
