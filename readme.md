# 再新洗車資料庫 (new_again_db)

給洗車場使用的離線客戶紀錄程式，專為不熟悉電腦的長輩設計：大字、大按鈕、全中文，畫面簡單乾淨。

- 不需要安裝、不需要網路 — 一個 `再新洗車資料庫.exe` 點兩下就能用
- **客戶資料**：車牌（前半—後半）、電話、備註、品牌（可不選）、VIP；用車牌或電話查詢，邊打邊找
- **記錄消費**：選洗車類型、輸入金額，一次完成；打錯可以在「客戶資訊」刪除
- **客戶資訊**：累計消費、來店次數、上次來店、平均消費、每一筆消費紀錄
- **營收報表**：今日 / 本週 / 本月 / 今年，可以往前、往後看；總營收、筆數、來店車輛、明細
- **備份 / 還原**：一鍵備份成一個檔案（隨身碟、雲端硬碟）；舊版的 .db、.sql 備份檔也能還原
- 每天開啟時自動備份到 `再新洗車資料\自動備份\`（保留 30 天）
- 字體與畫面會依視窗大小自動縮放，「設定」可再調大小

## 使用方式

1. 把 `再新洗車資料庫.exe` 放在一個資料夾裡，點兩下開啟。
2. 第一次開啟會在旁邊建立 `再新洗車資料` 資料夾，所有資料都在這裡。
3. **從舊版升級**：直接用新的 exe 取代舊的 exe。旁邊原本的 `database.db` 會自動搬進
   `再新洗車資料\洗車資料.db`，資料全部保留。
4. 換新電腦：複製 exe → 開啟 →「備份 / 還原」→「選擇備份檔並還原」。

## 開發 (Development)

```bash
pip install -r requirements.txt
NEWAGAIN_DATA_DIR=/tmp/cw python start.py      # run with test data
python -m pytest -q -p no:cacheprovider tests  # data layer, old schemas, old backups
build_exe.bat                                  # Windows: -> dist\再新洗車資料庫.exe
```

Maintainers (human or AI): start with
[`.claude/skills/new-again-dev/SKILL.md`](.claude/skills/new-again-dev/SKILL.md).

## License

MIT License — Copyright (c) 2025 Sukio Lin. See [LICENSE](LICENSE).
