import json
from pathlib import Path
from typing import List

curFileDir = Path(__file__).parent  # 当前文件路径

with open(curFileDir / "db.text.json", "r", encoding="utf-8") as f:
    db: List[dict] = json.load(f)["data"]

db_tr = {}

for data in db:
    name_raw = data['namespace']
    name_tr = data['frontMatters']["name"]
    db_tr[name_raw] = name_tr
    for k, v in data["data"].items():
        db_tr[k] = v["name"]

with open(curFileDir / "tagDB.json", "w", encoding="utf-8") as f:
    json.dump(db_tr, f, indent=4, ensure_ascii=False)
