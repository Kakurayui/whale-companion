# Lantern & Leaf · Mira（早期原型）

Mira 是本專案早期的英文煉金術師角色，用來建立檢索、記憶與比較流程。目前主要展示方向為 [鯨日陪伴 · 小肥魚](../README.md)，Mira 保留供比較與測試。

## 啟動

從 repository 根目錄執行：

```powershell
python -m backend.server --character mira --port 8766
```

然後開啟 [http://127.0.0.1:8766/](http://127.0.0.1:8766/)。Windows 也可執行 `scripts/Start-Mira.cmd`；預設 port 8766，方便與小肥魚分開。

模型設定共用根目錄 `.env`。角色內容、網頁及 SQLite 各自獨立：

| 內容 | 位置 |
|---|---|
| Mira 人格與世界 | `content/mira/character.json`、`content/mira/world.json` |
| 英文介面及本專案 SVG 示意圖 | `web/mira/` |
| 對話與記憶（不提交） | `data/companion.sqlite` |
| 20 個英文評估情境 | `evaluation/scenarios/mira.json` |

在 Enhanced 模式說 `My name is Alex. I prefer jasmine tea.`，成功回覆後開始新對話，詢問名字。Baseline 不讀取或自動更新長期記憶。兩個角色共用相同後端實作；Mira 不是獨立 Electron 桌寵。

## 評估

```powershell
python -m tools.evaluate --character mira --dry-run
python -m tools.evaluate --character mira --scenario M01 --repeats 1
python -m tools.evaluate --character mira --repeats 3
```

完整 Mira 評估為 120 個受評回覆、共 150 次請求；M01 單次共 4 次。這與小肥魚的 162 次不同。評分與證據限制見 [RUBRIC](../evaluation/RUBRIC.md)，來源分析見 [REFERENCES](REFERENCES.md)。
