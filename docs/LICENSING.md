# 授權範圍

此 repository 提供鯨日陪伴的原始碼；**目前沒有為本專案新增程式碼選定統一的公開授權**。公開可見不等同所有檔案都已按 MIT 或 Apache-2.0 授權。選定新增程式碼的授權後，應加入根目錄 `LICENSE` 並同步修改此文件及 README。

## 已有的第三方權利

- `desktop/vendor/rig.ts` 與 `desktop/renderer.ts` 的上游來源為 surfpet。其收到的 LICENSE 以 MIT 授權文字開頭，完整內容保存在 [surfpet-LICENSE.txt](../desktop/vendor/surfpet-LICENSE.txt)。第三方程式碼仍依其原有授權，不受本專案尚未選定授權的狀態影響。
- Electron、PixiJS、esbuild 及轉接依賴各自保留授權。原始碼包提供 lockfile，未捆綁這些套件或 Electron runtime；日後若製作可執行發行版，須保留所包含套件與 Chromium 的 notices。
- AgentAtelierR 僅作設計參考，未複製其程式碼或媒體。
- surfpet 的小肥魚分層圖片、預覽與 icon 是第三方素材。所檢查的 release 未提供可獨立確認的美術再分發授權；程式碼 MIT 聲明不能單獨證明圖片的再分發權。原始碼包因此不包含這些圖片或衍生截圖。

`tools/setup_pet_assets.py` 會從上游固定 release 還原本機素材，並驗證 SHA-256；下載工具本身不授予素材權利。若要把圖片、含圖片的 demo 截圖或可執行安裝包公開發佈，需先取得相應授權，或換成有明確授權的素材。

完整來源、revision 與修改說明見 [THIRD_PARTY_NOTICES.md](../THIRD_PARTY_NOTICES.md)。
