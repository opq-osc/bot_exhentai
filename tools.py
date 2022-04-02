import shutil
import threading
from pathlib import Path

import httpx
import pyzipper
from botoy import jconfig
from botoy import logger, Action
from botoy.contrib import get_cache_dir
from botoy.session.globals import _ctx
from tenacity import retry, stop_after_attempt

from ._proxies import transport, proxies

# curFileDir = Path(__file__).parent  # 当前文件路径

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36 Edg/96.0.1054.62",
    "Referer": "https://exhentai.org/",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6"
}
cookies = jconfig['exhentai.cookies']

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
        # self._daemonic = False
        self.groupid = groupid
        self.ctx = _ctx.get()
        self.url = url
        self.filename = filename
        # self.filePath = curFileDir / "download" / self.filename
        self.pic_cache_dir = get_cache_dir(filename).absolute()
        self.zip_cache_dir = (get_cache_dir("zip") / self.filename).absolute()  # 按群号独立出来
        self.action = Action(jconfig.bot, host=jconfig.host, port=jconfig.port)

    def encryption_zip_aes(self):
        if not pyzipper.is_zipfile(self.zip_cache_dir):
            self.action.sendGroupText(self.groupid, "解压出错")
            return
        with pyzipper.ZipFile(self.zip_cache_dir, 'r') as f:
            f.extractall(self.pic_cache_dir)
        files = [_ for _ in self.pic_cache_dir.iterdir()]
        # print(files)
        self.zip_cache_dir.unlink()  # 删除无密码的压缩包
        with pyzipper.AESZipFile(self.zip_cache_dir, "w", compression=pyzipper.ZIP_DEFLATED,
                                 compresslevel=6) as zf:
            zf.setpassword(str(self.ctx.CurrentQQ).encode())
            zf.setencryption(pyzipper.WZ_AES, nbits=128)
            for file in files:
                zf.write(filename=file, arcname=file.name)

        shutil.rmtree(self.pic_cache_dir)  # 删除解压出来的图片

    def send(self):
        self.encryption_zip_aes()
        self.action.sendGroupText(
            self.groupid,
            f"{self.filename}\r\n大小:{round(self.zip_cache_dir.stat().st_size / 1024 / 1024, 2)}MB\r\n解压密码为Bot的QQ号"
        )
        logger.warning("开始上传群文件")
        res = self.action.uploadGroupFile(self.groupid, filePath=str(self.zip_cache_dir))
        logger.warning(res)
        # self.action.uploadGroupFile(self.groupid, filePath="/root/health_sign/testfile.txt")
        self.action.sendGroupText(self.groupid, "上传ing~")

    @retry(stop=stop_after_attempt(3), retry_error_callback=lambda
            retry_state: print("下载error"))
    def downlaod(self):
        self.action.sendGroupText(self.groupid, "开始下载,请耐心等待~")
        logger.warning(f"开始下载{self.filename}")
        with httpx.Client(headers=headers, cookies=cookies, proxies=proxies, transport=transport) as client:
            res = client.get(self.url).content
            with open(self.zip_cache_dir, 'wb') as f:
                f.write(res)
        logger.warning(f"{self.filename}下载完成")

    def run(self):
        self.downlaod()
        self.send()
