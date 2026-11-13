# 參考專案與採用範圍

來源檢查日期：2026-11-06；目錄與說明更新：2026-11-13。這是原始碼與文件分析，不是對參考專案的完整建置或模型效果測試。

## surfpet：實際沿用

[Repository](https://github.com/Mieksido/surfpet/tree/d825d236a2afb760c15b9332eee3a8ccad1958a4) · revision `d825d236a2afb760c15b9332eee3a8ccad1958a4`

目前展示方向採用 surfpet 的 PixiJS 分層角色 rig、滑鼠互動邏輯，以及 v0.2.3 的小肥魚全身版與 Q 版素材作本機原型。Electron 殼層與本專案 Python / DeepSeek 後端整合，沒有接入 upstream SurfCore。

- 未修改的 rig：`desktop/vendor/rig.ts`。
- 經修改的 renderer：`desktop/renderer.ts`。
- 本機素材下載及 checksum：`tools/setup_pet_assets.py`。
- 程式授權、美術範圍與實際來源連結：[THIRD_PARTY_NOTICES.md](../THIRD_PARTY_NOTICES.md)。

上游美術不納入公開原始碼包；保留下載工具不等同已取得圖片再分發授權。

## AgentAtelierR：設計參考

[Repository](https://github.com/onion-aqua/AgentAtelierR/tree/e44eb267171168da23d982ac4d3c80bf954336a8) · revision `e44eb267171168da23d982ac4d3c80bf954336a8`

沒有複製此專案的程式碼或素材。以下設計用來比較可能的方向，而非本專案已實作的功能清單。

| 觀察 | 對本專案的啟發 | 本專案現況 |
|---|---|---|
| Flutter UI 整合角色對話、動畫、場景及設定 | 保持角色體驗連貫 | Electron 桌寵與中文聊天；未移植 Flutter / Spine |
| Chat Completions API client 可配置 endpoint / key / model | 以明確的模型適配層隔開 UI 與 provider | Python 的 DeepSeek / Ollama adapter；未實作串流 |
| 記憶 ledger 保留事實來源及人工修正 | 記憶應可追溯、可編輯 | 三種可編輯事實；尚無完整事件 ledger 或來源追蹤 |
| BM25 與可選多語語意向量檢索 | 比較字面匹配與語意召回 | 目前只用 BM25；沒有 embedding model |
| 區分對話證據、確認事實、權威現況 | 生成文字不應直接改變遊戲狀態 | 世界設定與使用者記憶分開；未實作物品、任務或關係狀態 |
| 分開評估檢索候選與最終回答 | 檢索命中不等於回答正確 | 記錄 retrieval hit，回答品質由人工 rubric 評分 |

### 採用前需要知道的限制

1. 檢查的 tree 中，`pubspec.yaml` 所需的本機 `packages/spine_flutter` 不在公開 tree；README 亦說明角色圖片、Spine、地圖與音訊等未完整公開。單純 clone 不能保證重現其展示體驗。
2. 文件涵蓋不同開發階段：較早 `memory_framework.md` 著重字面召回；較新 `rag_memory_prototype.md` 與實作加入可選本機語意編碼器及 lexical fallback。其文件中的模型大小與延遲數字屬於對方設計／測量，不是本專案的實測結果。
3. 根目錄有 Apache-2.0 LICENSE；媒體及部分依賴另有限制。不能把根目錄程式碼授權套用到所有角色美術。由於此處只引用設計，沒有把其授權當作本專案授權。

### 後續可以驗證的方向

先完成真實模型的設定一致性與跨對話記憶比較。若失敗例顯示字面檢索不足，再比較向量或混合檢索；若記憶修正需要更多脈絡，再加入來源與時間資訊。串流及語音是後續體驗工作，尚未完成。

### 原始來源

- [README](https://github.com/onion-aqua/AgentAtelierR/blob/e44eb267171168da23d982ac4d3c80bf954336a8/README.md)
- [API client](https://github.com/onion-aqua/AgentAtelierR/blob/e44eb267171168da23d982ac4d3c80bf954336a8/lib/src/ai_services.dart)
- [Memory framework](https://github.com/onion-aqua/AgentAtelierR/blob/e44eb267171168da23d982ac4d3c80bf954336a8/docs/memory_framework.md)
- [Local hybrid RAG design](https://github.com/onion-aqua/AgentAtelierR/blob/e44eb267171168da23d982ac4d3c80bf954336a8/docs/rag_memory_prototype.md)
- [Retrieval implementation](https://github.com/onion-aqua/AgentAtelierR/blob/e44eb267171168da23d982ac4d3c80bf954336a8/lib/src/rag_memory_retriever.dart)
- [Character prompt integration](https://github.com/onion-aqua/AgentAtelierR/blob/e44eb267171168da23d982ac4d3c80bf954336a8/lib/src/app_controller.dart)
- [Protected character assets](https://github.com/onion-aqua/AgentAtelierR/blob/e44eb267171168da23d982ac4d3c80bf954336a8/docs/PROTECTED_CHARACTER_ASSETS.md)
- [Dependency declaration](https://github.com/onion-aqua/AgentAtelierR/blob/e44eb267171168da23d982ac4d3c80bf954336a8/pubspec.yaml)
- [Root license](https://github.com/onion-aqua/AgentAtelierR/blob/e44eb267171168da23d982ac4d3c80bf954336a8/LICENSE)
