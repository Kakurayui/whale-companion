# 開發與疑難排解

所有指令以 repository 根目錄為起點；Python 只需要標準函式庫。主要入口是 `python -m backend.server`，預設角色為 `feiyu`。

## 設定

建議透過介面的「模型設定」輸入 DeepSeek key。也可將根目錄 `.env.example` 複製為 `.env` 後編輯；不要將 `.env` 提交。

| 變數 | 用途 |
|---|---|
| `COMPANION_PROVIDER` | `deepseek` 或 `ollama` |
| `DEEPSEEK_API_KEY` | DeepSeek key，僅由 Python 後端使用 |
| `DEEPSEEK_MODEL` | 預設 `deepseek-flash` |
| `OLLAMA_MODEL` | 預設 `qwen3:4b` |
| `COMPANION_PORT` | 手動啟動後端的預設 port；Windows 啟動器請用 `-Port` |

Windows 啟動器會依序嘗試 `COMPANION_PYTHON` 環境變數、`.venv/Scripts/python.exe`、PATH 中的 Python、`py -3`，最後讀取可選的本機 `.work/python-path.txt`。至少需要 Python 3.11；公開程式碼不依賴開發者電腦上的絕對路徑。

```powershell
# 指定其他 port，同時傳給後端及 Electron
.\Start-Whale.cmd -Port 8766

# 只啟動後端，然後自行開啟 http://127.0.0.1:8765/
.\Start-Whale.cmd -NoDesktop
```

`-NoDesktop` 仍會在缺少素材時還原網頁預覽。若要完全不下載角色素材，可先用 `python -m backend.server` 查看聊天介面；此時小肥魚預覽圖片會缺失。

## 程式分工

- `backend/companion.py`：模型適配、提示組裝、BM25、規則式記憶、SQLite 交易。
- `backend/server.py`：HTTP 路由、訪客身分、靜態檔案白名單與模型設定。
- `web/feiyu/`：中文 UI；`web/mira/`：早期英文 UI。兩者沿用相同 API。
- `desktop/main.cjs`：原生視窗與 IPC；preload 只暴露桌寵所需方法。
- `desktop/renderer.ts`：角色互動；`desktop/vendor/rig.ts`：保留的上游 rig。
- `content/<角色>/`：人格與世界；`evaluation/scenarios/<角色>.json`：對應情境。

修改 renderer 後執行 `npm run build`（在 `desktop/`）。啟動器只在缺少 bundle 時建置，不會每次重新編譯。修改 Python 後重啟後端；修改角色內容或網頁後重新載入對應服務 / 頁面。

## 測試與評估

```powershell
python -m unittest discover -s tests -v
python -m tools.evaluate --dry-run
python -m tools.evaluate --character mira --dry-run
```

評估用獨立臨時 SQLite，不改動平日聊天資料庫；原始結果寫入 `evaluation/results/`。真實模型測試需要已連接 provider。比較規則見 [RUBRIC](../evaluation/RUBRIC.md)。

## 常見問題

| 情況 | 處理 |
|---|---|
| 找不到 Python | 安裝 Python 3.11+ 並加入 PATH，或在 PowerShell 設定 `$env:COMPANION_PYTHON = '你的 python.exe 完整路徑'` 再啟動 |
| 模型顯示尚未連接 | 在設定頁輸入 key，確認 API 額度與帳戶可用模型；key 不要貼進聊天 |
| `Electron 0x80000003` / sandbox 無法讀取執行檔 | 使用 Windows 啟動器安裝；它只為 `desktop/node_modules/electron/dist` 增加 `ALL APPLICATION PACKAGES` 的讀取及執行權限，不停用 sandbox |
| 找不到桌寵 | 系統匣右鍵 → 找回小肥魚；位置在 `.runtime/whale-desktop/settings.json` |
| Port 被佔用 | 使用 `-Port 8766` 或另一個未使用的 port；不要終止不明服務 |
| 下載校驗失敗 | 先確認上游 release 與 [checksum](../THIRD_PARTY_NOTICES.md)；確認是損壞下載後，移走 `.work/reference/surfpet/pet-pack.zip` 再重試，不略過校驗 |
| 動畫修改沒有反映 | 在 `desktop/` 重新 `npm run build`，退出桌寵後重新啟動 |

診斷記錄在 `.work/server-errors.log` 與 `.runtime/whale-desktop/desktop.log`。它們不應提交至 repository。

退出桌寵不會停止 Python 後端。開發時建議在終端直接執行 `python -m backend.server`，以 `Ctrl+C` 停止；啟動器啟動的背景程序 PID 記錄在 `.work/server.pid`，舊 Mira 使用 `.work/mira-server.pid`。僅在確認 PID 與此專案相符後才終止該程序。

## 可選 Ollama

DeepSeek 不需本機模型。若要嘗試本機生成，可自行安裝 [Ollama](https://github.com/ollama/ollama)，啟動 `127.0.0.1:11434` 並準備 `qwen3:4b`。另有 `python -m tools.setup_local` 可下載固定版本的 Windows runtime 及模型；會佔用數 GB 空間。

在 `.env` 設定 `COMPANION_PROVIDER=ollama`、`OLLAMA_MODEL=qwen3:4b`，然後重啟後端。啟動器不會自動啟動 Ollama。此路徑與 DeepSeek 是不同實驗條件，不能混合結果；完整相容性及模型品質仍待實測。模型與 runtime 各有自己的授權，均不包含於原始碼包。
