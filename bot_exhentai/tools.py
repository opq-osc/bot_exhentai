from pathlib import Path

import httpx
from tenacity import AsyncRetrying, RetryError, stop_after_attempt
from tenacity import retry, stop_after_attempt, wait_random
from botoy.pool import WorkerPool
from botoy import logger

curFileDir = Path(__file__).parent  # 当前文件路径



@retry(stop=stop_after_attempt(3), retry_error_callback=lambda
        retry_state: str(curFileDir / "files" / "error.jpg"))
def download_to_bytes(url, client: httpx.Client) -> bytes:
    res = client.get(url)
    if res.status_code != 200:
        logger.warning("download_cover: res.status_code != 200")
        raise Exception("download: res.status_code != 200")
    return res.content
