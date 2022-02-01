import base64
import time
from functools import partial
from io import BytesIO
from pathlib import Path
from typing import List

import httpx
from PIL import Image, ImageDraw, ImageFont
from botoy import logger
from botoy.pool import WorkerPool

from .._proxies import transport, proxies
from ..files.config import config
from ..tools import download_to_bytes

curFileDir = Path(__file__).parent  # 当前文件路径

headers = config.headers
cookies = config.cookies


class DrawIndexPage:
    def __init__(self, image_urls, texts):
        self.ONE_LINE_MAX = 3
        self.GAP_X = 15
        self.pic_with_text_gap = 8  # 图片与文本的间隔
        self.font_dir = str(curFileDir.parent / "files" / "LXGWWenKaiMono-Regular.ttf")
        self.font = ImageFont.truetype(self.font_dir, 17)
        self.pool = WorkerPool(12)
        # ---------------------------
        self.image_urls: List[str] = image_urls
        self.texts: List[str] = texts
        # ---------------------------
        self.counts = 0
        self.images: List[Image.Image] = []  # 封面
        self.processed_texts: List[str] = []  # 处理后的标题
        self.text_sizes: List[tuple] = []  # 处理后的文本的长宽
        self.pic_coordinates: List[tuple] = []  # 每张图的对应坐标
        self.text_coordinates: List[tuple] = []  # 每张图下方的文字的对应坐标

    def download_all_pic(self) -> bool:
        """
        下载所有封面
        :return:
        """
        with httpx.Client(headers=headers, cookies=cookies, proxies=proxies, transport=transport) as client:
            for pic_bytes in self.pool.map(partial(download_to_bytes, client=client), self.image_urls):
                if type(pic_bytes) != str:
                    self.images.append(Image.open(BytesIO(pic_bytes)).convert('RGB'))
                else:
                    self.images.append(Image.open(pic_bytes))

        # print(len(self.images))
        if len(self.images) == self.counts:
            return True
        return False

    def build_coordinate(self) -> (List[tuple], List[tuple]):
        """
        生成瀑布流坐标
        :param pics: 图片列表
        :param self.text_sizes: 文本的实际占用大小
        :return: 图片坐标列表,文本坐标列表
        """
        # pic_coordinates: List[tuple] = []  
        # text_coordinates: List[tuple] = [] 
        # print(len(self.images))
        for i in range(self.counts):
            if i < self.ONE_LINE_MAX:  # 第一行
                coordinate_x = self.GAP_X + \
                               (self.pic_coordinates[i - 1][0] + self.images[i - 1].size[0] if i != 0 else 0)
                # 固定偏移+左边图片的坐标+左边图片的宽度
                coordinate_y = 20
            elif i != 0 and i % self.ONE_LINE_MAX == 0:  # 换行
                # print("换行")
                coordinate_x = self.GAP_X
                coordinate_y = self.text_sizes[i - self.ONE_LINE_MAX][1] + 2 * self.pic_with_text_gap + \
                               self.pic_coordinates[i - self.ONE_LINE_MAX][1] + \
                               self.images[i - self.ONE_LINE_MAX].size[1]
                # 向下的固定偏移+上方图片的Y坐标+上方图片的长度
            else:
                coordinate_x = self.pic_coordinates[i - self.ONE_LINE_MAX][0]  # 和上方图片的X坐标保持一致
                coordinate_y = self.text_sizes[i - self.ONE_LINE_MAX][1] + 2 * self.pic_with_text_gap + \
                               self.pic_coordinates[i - self.ONE_LINE_MAX][1] + \
                               self.images[i - self.ONE_LINE_MAX].size[1]
                # 向下的固定偏移+上方图片的Y坐标+上方图片的长度
            # print(f"NOW :{i}")
            self.pic_coordinates.append((coordinate_x, coordinate_y))
            self.text_coordinates.append((coordinate_x, coordinate_y + self.pic_with_text_gap + self.images[i].size[1]))
        # return pic_coordinates, text_coordinates

    def process_text(self):
        """
        处理长文本
        :param pics: 文本对应上方的图片列表
        :param text_list: 待处理的文本
        :return: 处理完的文本
        """
        # text_list_finally = []
        for i in range(self.counts):
            text_tmp: str = ""
            text_finally: str = ""
            # text_height_finally: int = 0
            for char in self.texts[i]:
                # print(char)
                text_tmp += char
                text_width, text_height = self.font.getsize(text_tmp)
                if text_width > self.images[i].size[0]:
                    # print(text_width, pics[i].size[0])
                    text_finally += (text_tmp[:-1] if text_finally == "" else text_tmp[1:-1]) + "\n" + text_tmp[-1]
                    text_tmp = text_tmp[-1]
            if text_tmp[1:] != "" and text_finally == "":
                text_finally += text_tmp
            elif text_tmp[1:] != "" and text_finally != "":
                text_finally += text_tmp[1:]
            self.processed_texts.append(text_finally)
        # return text_list_finally

    def get_text_sizes(self):
        """
        获取渲染后的文本实际大小
        :param texts: 文本
        :return: 渲染后文本的实际size
        """
        # text_size = []
        for text in self.processed_texts:
            img = Image.new("RGB", (1, 1))
            draw = ImageDraw.Draw(img)
            size = draw.textsize(text, self.font)
            self.text_sizes.append(size)
        # print(self.text_sizes)
        # return text_size

    def get_background_size(self):
        # X_MAX = (self.ONE_LINE_MAX + 1) * self.GAP_X + self.ONE_LINE_MAX * 250  # 250是固定图片宽度
        X_MAX = 0
        Y_MAX = 0
        for i in range(0, self.counts, self.ONE_LINE_MAX):
            imgs = self.images[i:i + self.ONE_LINE_MAX]
            X_tmp = sum([img.size[0] for img in imgs]) + (len(imgs) + 1) * self.GAP_X
            if X_tmp > X_MAX:
                X_MAX = X_tmp
        for line in range(self.ONE_LINE_MAX):
            y_tmp = 20
            for i in range(line, self.counts, 3):
                y_tmp += (self.images[i].size[1] + self.text_sizes[i][1] + self.pic_with_text_gap * 2)
            if y_tmp > Y_MAX:
                Y_MAX = y_tmp
        return X_MAX, Y_MAX

    def draw_index_number(self):
        """
        给图片左上角画上序号
        :return:
        """
        for i in range(self.counts):
            cover = self.images[i]
            draw = ImageDraw.Draw(cover)
            font = ImageFont.truetype(self.font_dir, 70)
            draw.text((0, 0), str(i + 1), font=font, fill="#00ff00")

    def main(self):
        if len(self.image_urls) == len(self.texts):
            self.counts = len(self.texts)
        else:
            logger.error("图片和文字数量不匹配")
            return
        if not self.download_all_pic():
            return
        start_time = time.time()
        self.process_text()
        self.get_text_sizes()
        bg_x, bg_y = self.get_background_size()
        background = Image.new('RGB', (bg_x, bg_y), (255, 255, 255))
        self.build_coordinate()
        self.draw_index_number()
        for i in range(self.counts):
            background.paste(self.images[i], (self.pic_coordinates[i][0], self.pic_coordinates[i][1]))
        draw = ImageDraw.Draw(background)
        for i in range(self.counts):
            # print(self.processed_texts[i])
            draw.multiline_text(self.text_coordinates[i], text=self.processed_texts[i], font=self.font, fill='black')
        logger.info(f"画图用时: {time.time() - start_time}")
        # background.show()
        with BytesIO() as bf:
            background.save(bf, format="JPEG", quality=80)
            return base64.b64encode(bf.getvalue()).decode()
        # background.save("res.jpg")


if __name__ == '__main__':
    urls = [
        'https://exhentai.org/t/69/fb/69fb6d072e74f5d86b566a028fed07a5259d64fb-2683152-4400-3500-jpg_250.jpg',
        'https://exhentai.org/t/c0/9b/c09b8c2fce0938ff0e2ca5917fcb4e9d58bfb536-215016-828-1280-jpg_250.jpg',
        'https://exhentai.org/t/e8/3f/e83f75ed0e835b5f504eacf5e614e00432418c75-494024-872-1088-jpg_250.jpg',
        'https://exhentai.org/t/c3/a5/c3a525882e5fa6b5ada3ba4a595d4f4c5c418f21-367626-898-784-jpg_250.jpg',
        'https://exhentai.org/t/12/91/1291faa5d37f92be38cca6082f83ab55ba9f7563-1546320-1359-1920-jpg_250.jpg',
        'https://exhentai.org/t/97/c8/97c8e1719c92aa46768f44f7e28512456a3382b6-1184155-1063-1500-jpg_250.jpg',
        'https://exhentai.org/t/51/c8/51c84ef796e1ac91a2f13c8d1e8b7e6a1d96475a-553270-1200-675-jpg_250.jpg',
        'https://exhentai.org/t/17/d9/17d9977eac6cd3717c750051b7e955ee9410b19e-394252-1200-675-jpg_250.jpg',
        'https://exhentai.org/t/89/59/8959ece7934f525dba6fa2fc99bb54c383b7826e-313170-1200-675-jpg_250.jpg',
        'https://exhentai.org/t/83/dc/83dcb40fa317f6aaa8be36c1162e3a3c3dedf00a-319202-1200-675-jpg_250.jpg',
        'https://exhentai.org/t/77/23/7723048a985fa419d07d89d605eae9000ca04eb4-334997-1200-675-jpg_250.jpg',
        'https://exhentai.org/t/9d/6c/9d6c5f825d44bae12303da239a7c5e6c79ce4428-459684-1200-675-jpg_250.jpg',
        'https://exhentai.org/t/f4/66/f46618de2c1a1db184a84db8544180dc09ca1163-346335-1200-675-jpg_250.jpg',
        'https://exhentai.org/t/5e/47/5e477c56f5476ce770cc2bdebdd911817cb11c3b-541571-1200-675-jpg_250.jpg',
        'https://exhentai.org/t/ad/9c/ad9c1518a8f772f758cfd8c4f82c3cabf78384ca-386148-1200-675-jpg_250.jpg',
        'https://exhentai.org/t/57/e3/57e3a18edee853e8e7896869acbc017857c3c78b-337336-1200-675-jpg_250.jpg',
        'https://exhentai.org/t/85/88/85884214c4e2da1fe535aba2f7ceb0a9099b2cf0-426860-1200-675-jpg_250.jpg',
        'https://exhentai.org/t/77/1a/771a4c3d41aa4c402ce1bbb05a2b8bb2b2c76104-494156-1200-675-jpg_250.jpg',
        'https://exhentai.org/t/41/ab/41ab7891073e8fb07ab6fe73a3e8430d228ad025-556780-1200-675-jpg_250.jpg',
        'https://exhentai.org/t/1a/12/1a12bfc5c1270c3ec05e52d7dd168817057a2100-295172-1200-675-jpg_250.jpg',
        'https://exhentai.org/t/4b/4a/4b4ab01305648fcbcde875a60e210a3278f2a85e-4401307-4961-7016-jpg_250.jpg',
        'https://exhentai.org/t/c5/06/c5063a6d896a56fc7eb7ba33e10d0f722883546e-2834338-1308-1864-png_250.jpg',
        'https://exhentai.org/t/08/a7/08a79fc3aa9702f7d1b8029547b94f6b2724a521-383247-800-1159-jpg_250.jpg',
        'https://exhentai.org/t/f4/63/f46387049afcecb47375278afcb69571b0f73e17-214700-800-1252-jpg_250.jpg',
        'https://exhentai.org/t/a8/36/a8365d1cf7b13d3d96636b6774cb9424b9ef28a8-287840-729-980-jpg_250.jpg']

    txts = ['[FANBOX] dangonesan [2021-12-24]', '[phrannd] Overstay(ongoing) [Chinese] [lostecho个人汉化]',
            '[tokunocin (Tokuno Yuika)] Mousou Shoujo Kikuri-chan  | 想治治妹妹这个臭丫头的样子！（妄想少女篇） [Chinese] [无糖·漫画组]',
            '[Shimahara] Uchi no Neko ga Onnanoko de Kawaii | 我家的猫猫是可爱的女孩子! [Chinese] [无糖·漫画组][绿茶汉化组]',
            '[Aomushi] Petted Girl  || 被饲养的女孩 (COMIC Shitsurakuten 2021-08)  [夜空下的萝莉x真不可视汉化组]',
            '[Aomushi] Pet Girl || 饲养女孩 (COMIC Shitsurakuten 2021-07) [夜空下的萝莉x真不可视汉化组]', 'Spirit sacrificeⅠ—— EP22',
            'Spirit sacrificeⅠ—— EP21', 'Spirit sacrificeⅠ—— EP20', 'Spirit sacrificeⅠ—— EP19',
            'Spirit sacrificeⅠ—— EP18',
            'Spirit sacrificeⅠ—— EP17', 'Spirit sacrificeⅠ—— EP16',
            'Evil Metropolis Ⅳ ——  Return to  Golden City 6',
            'Evil Metropolis Ⅳ ——  Return to  Golden City 5', 'Evil Metropolis Ⅳ ——  Return to  Golden City 4',
            'Evil Metropolis Ⅳ ——  Return to  Golden City 3', 'Evil Metropolis Ⅳ ——  Return to  Golden City 2',
            'Evil Metropolis Ⅲ  —— Penalty Golden City 12', 'Evil Metropolis Ⅳ ——  Return to  Golden City 1',
            '[安堂流] お母さんいただきます。2 連載 P1-35 [空気系☆漢化]',
            '[Unmei no Ikasumi (Harusame)] Suwarete Dame nara Suttemiro! (Touhou Project) [Chinese] [現場目睹全過程的古明地戀個人漢化] [Digital]',
            'Chinese 神契 幻奇谭（刘冲L.Dart）02', 'Chinese 神契 幻奇谭（刘冲L.Dart）01',
            '[Pixiv] ebiblue (379606) [Chinese] [白杨汉化组]']

    test = DrawIndexPage(urls, txts)
    pic_bytes = test.main()
