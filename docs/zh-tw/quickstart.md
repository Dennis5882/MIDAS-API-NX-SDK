# midas-nx 新手指南（沒有程式設計經驗也沒關係）

本指南適合每天使用 MIDAS Gen NX/Civil NX，但從未寫過 Python 程式的結構工程師。
內容從安裝 Python 開始，一路帶到執行第一支腳本為止，依序照做即可一次完成。

> 如果您已經會寫程式，[README.md](https://github.com/Dennis5882/MIDAS-API-NX-SDK/blob/main/README.md) 的 Quick Start 章節會更快。
> 本指南是給「還不太確定 Python 是什麼」的讀者準備的前置步驟。

> 本專案由 MIDAS IT 員工依據實際產品與 API 驗證經驗開發維護，屬於**員工自主的開源
> 專案**，並非 MIDAS IT 官方發布或提供技術支援的產品。因此本指南與 SDK 的相關問題
> 請至 [GitHub Issues](https://github.com/Dennis5882/MIDAS-API-NX-SDK/issues) 回報，
> 官方產品技術支援並不涵蓋本專案。

## 開始之前需要準備

- Windows 電腦（本指南以 Windows 為準說明）
- 已安裝 MIDAS Gen NX 或 Civil NX，且授權有效
- 網路連線（此 SDK 會透過 MIDAS 雲端中繼伺服器通訊）

## 第 1 步：安裝 Python

1. 前往 https://www.python.org/downloads/ 。
2. 點選「Download Python 3.x.x」下載安裝檔。
3. 執行安裝檔。**安裝畫面最下方的「Add python.exe to PATH」核取方塊務必勾選**，
   再點「Install Now」。若漏勾這個選項，之後命令提示字元會無法辨識 `python`
   指令。
4. 安裝完成後進行確認。在開始功能表搜尋「cmd」開啟命令提示字元，輸入：

   ```
   python --version
   ```

   若顯示類似 `Python 3.x.x` 的結果即代表安裝成功。若出現
   `'python' 不是內部或外部命令` 之類的錯誤，代表第 3 步漏勾了 PATH 選項，
   請重新安裝一次 Python 並勾選該選項。

## 第 2 步：安裝 midas-nx

在同一個命令提示字元視窗輸入：

```
pip install midas-nx
```

出現 `Successfully installed midas-nx-...` 訊息即代表安裝完成。

## 第 3 步：取得 MAPI 金鑰

`MAPI-Key` 是此 SDK 與 MIDAS Gen NX/Civil NX 通訊時使用的驗證金鑰，並非在
Python 中取得，而是**直接在 MIDAS Gen NX（或 Civil NX）程式內**發行。

1. 執行 MIDAS Gen NX（或 Civil NX）。
2. 在上方選單找到 **Open API** 相關選單（依版本不同，可能顯示為「Open API」
   或位於「Apps」選單底下）。
3. 選擇 **API Key 發行**（或類似字樣），畫面會顯示一長串英數字組成的金鑰，
   請複製下來備用。

> 此金鑰為暫時性金鑰，僅在程式執行期間有效。隨時都能從同一個選單重新發行，
> 遺失也不必擔心。

> ⚠️ **金鑰有效期間請視同密碼處理。** 以下腳本為求方便，直接把金鑰貼在
> 程式碼中——若只是自己電腦上的一次性檔案沒問題，但請不要把這個檔案提交
> 到 Git、貼到公開聊天室或 Issue，也不要分享含有金鑰的截圖。若懷疑金鑰
> 外洩，直接到同一個選單重新發行即可——舊金鑰在關閉程式後本來就會失效。

## 第 4 步：撰寫並執行第一支腳本（唯讀）

開啟記事本（或 VS Code 等任何文字編輯器），原封不動貼上以下內容，只需將
`"請貼上第3步複製的金鑰"` 換成您實際複製的金鑰。

```python
from midas_nx import MidasClient, Product
from midas_nx.db.node_element import Node

# 若使用 Civil NX，請將此處改為 product=Product.CIVIL
client = MidasClient(mapi_key="請貼上第3步複製的金鑰", product=Product.GEN)

print(client.verify_connection())

nodes = Node.items(client=client)
print(f"連線成功。目前模型中找到 {len(nodes)} 個節點。")
```

檔名存為 `first_script.py`（存在桌面或任何資料夾都可以）。

在命令提示字元切換到儲存的資料夾後執行。例如存在桌面的話：

```
cd Desktop
python first_script.py
```

畫面會出現類似以下的結果：

```
{'status': 'connected', 'keyVerified': True}
連線成功。目前模型中找到 3 個節點。
```

（節點數量取決於目前開啟的模型 —— 若是空白專案，出現 `0` 也是正常的。）

**這支腳本只會讀取資料。** 不論對哪個專案執行，都不會建立、變更或刪除
模型中的任何內容 —— 即使拿實際的專案來執行也很安全。

## 遇到問題時

- **出現 `MidasConnectionError`**：請確認 Gen NX/Civil NX 是否正在執行、
  Open API 是否已連線。此 SDK 的錯誤訊息結尾會附上 `(Hint: ...)`，
  告訴您該檢查什麼。
- **出現 `MidasAuthError`**：請確認貼上的金鑰與第 3 步複製的完全一致。
  重新啟動程式後金鑰可能會改變，若發生此情況請重新發行並貼上新的金鑰。
- **身處公司防火牆環境**：請參考 [README.md](https://github.com/Dennis5882/MIDAS-API-NX-SDK/blob/main/README.md) 的
  「Troubleshooting」章節，內含可交給 IT 團隊的連接埠/位址資訊。

## 第 5 步：試著變更模型（選用 —— 會變更您的模型）

上面的腳本用來確認連線是否正常。若您想看看 `midas-nx` 實際建立東西的過程，
以下準備了 MIDAS-API 手冊使用的相同範例 —— 但請先閱讀下方警告。

> ⚠️ **這支腳本會呼叫 `doc.new_project()`，這會捨棄目前 Gen NX/Civil NX
> 中已開啟文件的所有未儲存工作** —— 即使與這支腳本無關的工作也一樣。
> 請只在空白專案，或不介意遺失未儲存變更的專案中執行。若您開啟的是實際
> 模型，請先儲存（或關閉後開新的空白專案）再執行。

```python
from midas_nx import MidasClient, Product, doc
from midas_nx.db.node_element import Element, Node
from midas_nx.db.project import Unit
from midas_nx.db.properties.material import Material
from midas_nx.db.properties.section import Section

# 若使用 Civil NX，請將此處改為 product=Product.CIVIL
client = MidasClient(mapi_key="請貼上第3步複製的金鑰", product=Product.GEN)

doc.new_project(client=client)
Unit.update({1: {"DIST": "M", "FORCE": "KN"}}, client=client)

Material.create(
    {1: {"TYPE": "CONC", "NAME": "C24",
         "PARAM": [{"P_TYPE": 1, "STANDARD": "KS01(RC)", "DB": "C24"}]}},
    client=client,
)
Section.create(
    {1: {"SECTTYPE": "DBUSER", "SECT_NAME": "Column",
         "SECT_BEFORE": {"USE_SHEAR_DEFORM": True, "SHAPE": "SB", "DATATYPE": 2,
                          "SECT_I": {"vSIZE": [0.6, 0.6]}}}},
    client=client,
)
Node.create({1: {"X": 0, "Y": 0, "Z": 0}, 2: {"X": 0, "Y": 0, "Z": 3.2}}, client=client)
Element.create({1: {"TYPE": "BEAM", "MATL": 1, "SECT": 1, "NODE": [1, 2]}}, client=client)
doc.save(client=client)

print("成功！請切換到 Gen NX 畫面確認柱子是否已建立。")
```

執行方式與第 4 步相同（存成 `.py` 檔後用 `python` 執行）。畫面出現
`成功！請切換到 Gen NX 畫面...` 後，切換到 Gen NX 視窗即可看到新建立的
0.6m × 0.6m、高 3.2m 的混凝土柱。

> 以上範例使用的材料/斷面組合（`C24`/`KS01(RC)`）已於 2026-07-22 在實際 Gen NX
> 與 Civil NX 連線環境中完成即時驗證（詳見
> [docs/live_verification_notes.md](../live_verification_notes.md)）——
> 使用的是已確認可行的數值，而非未經測試的隨意範例。

## 下一步

- **搭配 AI 程式設計工具繼續延伸**：熟悉上面的模式之後，不需要自己背下或手寫
  每一行程式碼。把這支腳本拿給 Claude Code、ChatGPT、GitHub Copilot 等工具，
  用一般語言描述需求即可，例如「改成 20 公尺長的梁而不是柱子」、「幫我加一個
  載重組合」，AI 就會幫您轉換成實際的 `midas-nx` 程式碼。這套 SDK 本身就是為了
  方便這樣搭配使用而設計的（型別提示、清楚的錯誤訊息等）。執行 AI 產生的程式碼前，
  請先參考
  [AI 輔助程式設計安全指南](../ai-coding/safe-start.md)，
  取得要給 AI 的 context pack 以及執行前的檢查清單。
- 更貼近實務的範例：GitHub 上的
  [`examples/python/`](https://github.com/Dennis5882/MIDAS-API-NX-SDK/tree/main/examples/python/) 資料夾（梁載重組合、
  風載重、施工階段等）——也可以直接拿給 AI 說「照這個範例幫我做」。
- 已實作功能完整清單：[ROADMAP.md](https://github.com/Dennis5882/MIDAS-API-NX-SDK/blob/main/ROADMAP.md)
- 更詳細的使用方式與設計說明：[README.md](https://github.com/Dennis5882/MIDAS-API-NX-SDK/blob/main/README.md)

若您在跟著本指南操作時卡關，歡迎到 GitHub Issues 告訴我們——
這能幫助我們為下一位使用者改善這份指南。
