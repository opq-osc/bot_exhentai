import json
from pathlib import Path

from botoy import logger
from pydantic import BaseModel


class Config(BaseModel):
    cookies: dict
    headers: dict
    ONE_LINE_MAX: int


curFileDir = Path(__file__).parent  # 当前文件路径

try:
    with open(curFileDir / "config.json", "r", encoding="utf-8") as f:
        config = Config(**json.load(f))
except:
    logger.error("配置文件错误")
    exit(0)
