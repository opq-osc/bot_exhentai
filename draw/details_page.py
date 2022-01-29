from pathlib import Path

from PIL import ImageFont

curFileDir = Path(__file__).parent  # 当前文件路径


class DrawDetailsPage:
    def __init__(self, title, cover_url, tags):
        self.title = title
        self.cover_url = cover_url
        self.tags = tags
        self.font_dir = str(curFileDir.parent / "files" / "LXGWWenKaiMono-Regular.ttf")
        self.font = ImageFont.truetype(self.font_dir, 17)

    def process_text(self, texts, width=400):
        """
        处理长文本
        :param
        :param text_list: 待处理的文本
        :return: 处理完的文本
        """
        # text_list_finally = []
        for i in range(len(texts)):
            text_tmp: str = ""
            text_finally: str = ""
            # text_height_finally: int = 0
            for char in texts[i]:
                text_tmp += char
                text_width, text_height = self.font.getsize(text_tmp)
                if text_width > self.images[i].size[0]:
                    # print(text_width, pics[i].size[0])
                    text_finally += (text_tmp[:-1] if text_finally == "" else text_tmp[1:-1]) + "\n" + text_tmp[-1]
                    text_tmp = text_tmp[-1]
            if text_tmp[1:] != "":
                text_finally += text_tmp[1:]
            self.processed_texts.append(text_finally)
        # return text_list_finally
