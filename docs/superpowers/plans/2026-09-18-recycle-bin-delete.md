# Recycle Bin Delete Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在 Vault 檔案總管中加入經二次確認、只移至 Windows 資源回收桶的安全刪除功能。

**Architecture:** `RecycleBinService` 負責解析及限制 Vault 相對路徑，並以固定的 PowerShell 腳本呼叫 Windows 內建回收桶 API。`MainWindow` 為檔案與資料夾節點附加類型資料，在右鍵選單確認後呼叫 service 並重新整理檔案樹。

**Tech Stack:** Python 3.13、PySide6、pytest、Windows PowerShell、Microsoft.VisualBasic.FileIO。

---

### Task 1: 服務層失敗測試

**Files:**
- Create: `tests/services/test_recycle_bin_service.py`
- Create: `src/pigo_notes/services/recycle_bin_service.py`

- [ ] **Step 1: 寫入測試**

```python
service = RecycleBinService(vault_root)
assert service.target_for(Path("Notes/Readme.md")) == vault_root / "Notes/Readme.md"
with pytest.raises(ValueError): service.target_for(Path("../outside.md"))
with pytest.raises(ValueError): service.target_for(Path("."))
```

以 monkeypatch 攔截 `subprocess.run`，驗證固定腳本包含 `SendToRecycleBin`，而目標路徑以獨立引數傳入。

- [ ] **Step 2: 執行並確認失敗**

Run: `python -m pytest tests/services/test_recycle_bin_service.py -v`
Expected: FAIL，因為 service 尚未存在。

- [ ] **Step 3: 實作最小 service**

提供 `target_for(relative_path)` 與 `move_to_recycle_bin(relative_path, is_directory)`；只允許現存、在 Vault 內且非根目錄目標。

- [ ] **Step 4: 驗證通過**

Run: `python -m pytest tests/services/test_recycle_bin_service.py -v`
Expected: PASS。

### Task 2: 檔案總管右鍵刪除

**Files:**
- Modify: `src/pigo_notes/ui/main_window.py`
- Modify: `tests/ui/test_main_window.py`

- [ ] **Step 1: 寫入失敗測試**

建立資料夾與檔案後驗證節點分別標記為 `folder` 與 `file`，使右鍵刪除只處理具有效目標的節點。

- [ ] **Step 2: 實作資料與選單**

使用 `Qt.CustomContextMenu`；右鍵選單只加入「移到資源回收桶」。確認對話顯示相對路徑；成功後重新整理樹與清理被刪檔案的預覽。

- [ ] **Step 3: 驗證 UI 測試**

Run: `python -m pytest tests/ui/test_main_window.py -v`
Expected: PASS。

### Task 3: 完整驗證與提交

- [ ] **Step 1:** Run `python -m pytest -v --basetemp .tmp_pytest` and `python -m compileall src`.
- [ ] **Step 2:** 更新 README 的安全刪除說明。
- [ ] **Step 3:** 提交 `feat: add recycle bin delete action`。