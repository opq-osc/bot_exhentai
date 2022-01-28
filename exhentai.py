import httpx

from .api import ex_search, get_archive_tags, get_download_page_url, get_download_zipfile_url
from .draw import DrawIndexPage
from .tools import DownloadArchive
from pathlib import Path
import json
from typing import List
import time

curFileDir = Path(__file__).parent  # 当前文件路径

with open(curFileDir / "files" / "tagDB.json", "r", encoding="utf-8") as f:
    tag_db: dict = json.load(f)

exitFlag = 0


class Exhentai:
    def __init__(self):
        self.search_keyword = None
        self.archives = []
        self.archive_cover_urls = []
        self.archive_urls = []
        self.archive_titles = []
        self.now_page = 0
        self.max_page = 0

    def _update_info(self, archives, now_page, max_page):
        self.archives = archives
        self.now_page = now_page
        self.max_page = max_page
        self.archive_cover_urls = [cover_url[1] for cover_url in archives]
        self.archive_urls = [url[2] for url in archives]
        self.archive_titles = [title[0] for title in archives]

    def _conversion_tags(self, tags):
        tags_finish = []
        for tag in tags:
            tag_split = tag.split(":")
            tags_finish.append(f"{tag_db.get(tag_split[0]) or tag_split[0]}:{tag_db.get(tag_split[1]) or tag_split[1]}")
        return tags_finish

    def search(self, keyword, page=0):
        self.search_keyword = keyword
        res = ex_search(keyword, page)
        self._update_info(res[0], page, res[1] - 1)
        if self.archives == []:
            return False
        if pic := DrawIndexPage(self.archive_cover_urls, self.archive_titles).main():
            return pic

    def previous_page(self):
        print("上一页")
        if self.now_page - 1 < 0:
            return False
        self.now_page -= 1
        return self.search(self.search_keyword, self.now_page)

    def next_page(self):
        print("下一页")
        if self.now_page + 1 > self.max_page:
            return False
        self.now_page += 1
        return self.search(self.search_keyword, self.now_page)

    def jump_page(self, page):
        if page < 0 or page > self.max_page:
            return False
        self.now_page = page
        return self.search(self.search_keyword, self.now_page)

    def get_more_info(self, index):
        if index < 0 or index > len(self.archives):
            return False
        tags = get_archive_tags(url=self.archive_urls[index])
        print(self._conversion_tags(tags))

    def add_download_job(self,ctx, index: int, file_type: str = "zip"):
        if index < 0 or index > len(self.archives):
            return False
        download_page_url = get_download_page_url(self.archive_urls[index])
        download_url, filename = get_download_zipfile_url(download_page_url)
        DownloadArchive(ctx,download_url, filename).start()
