# Vault 資源回收桶刪除設計

## 範圍

在 Pigo Notes App 左側檔案總管提供檔案與資料夾的右鍵刪除功能。刪除只允許在設定的 Vault 根目錄內進行。

## 安全規則

- 動作名稱為「移到資源回收桶」，不提供永久刪除。
- 右鍵後先顯示完整 Vault 相對路徑與檔案／資料夾類型，使用者須按確認。
- 拒絕 Vault 根目錄、Vault 以外路徑、空路徑與不存在目標。
- 使用 Windows 內建 `Microsoft.VisualBasic.FileIO.FileSystem` 加上 `RecycleOption.SendToRecycleBin`。
- 完成後重新整理檔案樹；若目前預覽的檔案被刪除，清空預覽。

## 驗證

- Service 測試驗證路徑限制及 PowerShell 呼叫不接受任意腳本。
- UI 測試驗證檔案與資料夾都有右鍵選單資料，並不允許根目錄作為刪除目標。
- 不在自動測試中真正刪除使用者 Vault 檔案。