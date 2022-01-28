import re
from pathlib import Path

import httpx
from aiofile import async_open
from botoy import AsyncAction
from botoy import GroupMsg, logger
from botoy import async_decorators as deco
from botoy.collection import MsgTypes
from botoy.session import SessionHandler, ctx, session
from botoy.parser import group as gp
from tenacity import AsyncRetrying, RetryError, stop_after_attempt
from tenacity import retry, stop_after_attempt, wait_random
from botoy.decorators import ignore_botself, startswith, from_these_groups
from .exhentai import Exhentai

__doc__ = "ExHentai的一些功能"

handler_ex = SessionHandler(
    ignore_botself, startswith("exfunc"), expiration=300
).receive_group_msg().receive_friend_msg()


@handler_ex.receive
def receive():
    if not session.get("flag", wait=False):
        print("not_flag")
        return
    ex: Exhentai = session.get("class")
    if ctx.Content in ["up", "上一页", "上页"]:
        if res := ex.previous_page():
            session.send_pic(base64=res)
        else:
            session.send_text(f"当前页数{ex.now_page},无法翻页")
    elif ctx.Content in ["down", "下一页", "下页"]:
        if res := ex.next_page():
            session.send_pic(base64=res)
        else:
            session.send_text(f"当前页数{ex.now_page},无法翻页")
    elif info := re.match(r"搜索 ?(.*)", ctx.Content):
        if res := ex.search(info[1]):
            session.send_pic(base64=res)
        else:
            session.send_text("无结果")
    elif info := re.match(r"翻页 ?(\d+)", ctx.Content):
        if res := ex.jump_page(int(info[1])):
            session.send_pic(base64=res)
        else:
            session.send_text(f"当前页数{ex.now_page},无法翻页")
    elif info := re.match(r"详细信息 ?(\d+)", ctx.Content):
        ex.get_more_info(int(info[1]) + 1)
    elif info := re.match(r"下载 ?(\d+)", ctx.Content):
        ex.add_download_job(ctx.FromGroupId, int(info[1])-1)


@handler_ex.handle
def main():
    ex = Exhentai()
    session.set("class", ex)
    keyword = ctx.Content[6:].strip()
    if not keyword:
        keyword = session.want(
            "ex_tag", "请发送本子关键字", timeout=20, default="退出"
        )
        if not keyword or keyword == "退出":
            handler_ex.finish("已退出")
            return
        if res := ex.search(keyword):
            session.send_pic(base64=res)
        else:
            session.send_text("无结果")
    session.set("flag", True)
    while True:
        word = session.pop("word", wait=True)
        if word == "退出":
            handler_ex.finish("已退出")
