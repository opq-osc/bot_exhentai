import re
import time
from functools import lru_cache

import httpx

from ._proxies import transport, proxies
from .files.config import config

# curFileDir = Path(__file__).parent  # 当前文件路径

headers = config.headers
cookies = config.cookies


class ExApi:
    def __init__(self):
        self.client = httpx.Client(headers=headers, cookies=cookies, proxies=proxies, transport=transport)

    def ex_search(self,keywords: str, page: int = 0) -> tuple:
        """
        ex搜索
        :param page: 翻页的页码
        :param keywords:关键字
        :return: 返回html里的画廊信息(标题,封面,画廊链接)
        """
        params = {
            "f_search": keywords
        }
        if page != 0:
            params['page'] = page
        html = self.client.get("https://exhentai.org", params=params, headers=headers, cookies=cookies).text
        res = re.findall(
            r'<tr.*?><td class=\"gl1c glcat\">.*?title=\"(.*?)\".*?\".*?(https://exhentai\.org/t/.*?)\".*?(https://exhentai\.org/g/.*?)\".*?</tr>',
            html)
        if info := re.search(r"Jump to page: \(\d+-(\d+)\)", html):
            max_page = int(info[1])
        else:
            max_page = 0
        return res, max_page

    @lru_cache(maxsize=16)
    def get_archive_html(self, url):
        return self.client.get(url, headers=headers, cookies=cookies).text

    def get_download_page_url(self, archive_url: str) -> str:
        """
        提取下载界面的链接
        :param archive_url:画廊url
        :return: 选择下载画质的页面url
        """
        archive_text = self.get_archive_html(archive_url)
        download_choose_page_url = re.search(r"\('(https://exhentai\.org/archiver\.php.*?)'.*?\)\">Archive Download",
                                             archive_text).group(1).replace("amp;", "").replace("--", "-")  # 选择下载画质的页面
        print(download_choose_page_url)
        time.sleep(2)
        self.client.get(download_choose_page_url, headers=headers, cookies=cookies)  # 正常走一下网页的流程,没有用
        return download_choose_page_url

    def get_download_zipfile_url(self,download_page_url: str, original: bool = False):
        """
        返回zip压缩包的下载链接
        :param download_page_url: 选择画质的下载页面链接
        :param original: 是否下载原画
        :return:
        """
        download_url_data_last = self.client.post(download_page_url,
                                            data={
                                                "dltype": "org",
                                                "dlcheck": "Download Original Archive"
                                            } if original else {
                                                "dltype": "res",
                                                "dlcheck": "Download Resample Archive"
                                            },
                                            headers=headers,
                                            cookies=cookies).text  # 最终的下载页面
        download_url = re.search(r'\"Please wait\.\.\.\";.*?document\.location = \"(.*?)\";', download_url_data_last,
                                 flags=re.S).group(1)  # 提取下载链接
        print(download_url)
        filename_info = self.client.get(download_url, headers=headers, cookies=cookies).text
        filename = re.search(r'<strong>(.*?)</strong>', filename_info).group(1)
        return download_url + "?start=1", filename

    def get_archive_tags(self,url: str):
        print(url)
        html = self.get_archive_html(url)
        tags = re.findall(r"toggle_tagmenu\('(.*?)',this\)", html, flags=re.S)  # 提取tag
        return tags


if __name__ == '__main__':
    archives = ex_search('ntr')
    # archives_tag = get_archive_tags([tagshtml[3] for tagshtml in archives])
    time.sleep(3)
    print(archives)
    durl = get_download_page_url(archives[0][0][2])
    print(get_download_zipfile_url(durl, ))
