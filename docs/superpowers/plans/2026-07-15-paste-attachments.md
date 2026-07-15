# 粘贴附件 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 让评审输入框在粘贴图片或文件时将其加入现有附件上传流程，同时不影响纯文本粘贴。

**Architecture:** 新增一个纯函数，从浏览器剪贴板项中提取可用的 `File`。`ChatPanel` 的输入框仅在该函数返回文件时阻止默认粘贴，并逐个调用现有 `handleAttach`；上传、附件展示与错误反馈继续由既有逻辑负责。

**Tech Stack:** React 18、TypeScript、Ant Design、Node 26 内置断言。

## Global Constraints

- 仅监听评审输入框；不新增全页面粘贴监听、拖拽上传或后端接口。
- 有文件时阻止默认粘贴；无文件时保持浏览器文本粘贴。
- 复用 `handleAttach(file)`，不复制上传请求或提示逻辑。
- 测试命令使用 `node --experimental-strip-types`。

---

### Task 1: 提取并上传粘贴的文件

**Files:**
- Create: `frontend/src/utils/getPastedFiles.ts`
- Create: `frontend/tests/getPastedFiles.test.mjs`
- Modify: `frontend/src/components/ChatPanel.tsx:9-15,106-115,183-195`

**Interfaces:**
- Consumes: `DataTransferItemList` 及现有 `handleAttach(file: File): Promise<false>`。
- Produces: `getPastedFiles(items: Iterable<Pick<DataTransferItem, "kind" | "getAsFile">>): File[]`，供输入框粘贴事件调用。

- [x] **Step 1: 写入失败测试**

```js
import assert from "node:assert/strict";
import { getPastedFiles } from "../src/utils/getPastedFiles.ts";

const image = { name: "paste.png" };
const document = { name: "review.pdf" };
const files = getPastedFiles([
  { kind: "string", getAsFile: () => null },
  { kind: "file", getAsFile: () => image },
  { kind: "file", getAsFile: () => document },
]);

assert.deepEqual(files, [image, document]);
```

- [x] **Step 2: 运行测试并确认失败**

Run: `node --experimental-strip-types frontend/tests/getPastedFiles.test.mjs`

Expected: 失败，提示无法解析 `frontend/src/utils/getPastedFiles.ts`。

- [x] **Step 3: 实现最小文件提取函数**

```ts
type ClipboardItem = Pick<DataTransferItem, "kind" | "getAsFile">;

export function getPastedFiles(items: Iterable<ClipboardItem>): File[] {
  const files: File[] = [];
  for (const item of items) {
    if (item.kind !== "file") continue;
    const file = item.getAsFile();
    if (file) files.push(file);
  }
  return files;
}
```

- [x] **Step 4: 接入输入框粘贴事件**

```tsx
import type { ClipboardEvent } from "react";
import { getPastedFiles } from "../utils/getPastedFiles";

const handlePaste = async (event: ClipboardEvent<HTMLTextAreaElement>) => {
  const files = getPastedFiles(event.clipboardData.items);
  if (!files.length) return;
  event.preventDefault();
  for (const file of files) {
    await handleAttach(file);
  }
};

<Input.TextArea onPaste={handlePaste} />
```

- [x] **Step 5: 运行验证**

Run: `node --experimental-strip-types frontend/tests/getPastedFiles.test.mjs && npm run typecheck --prefix frontend && npm run build --prefix frontend`

Expected: 文件项提取测试、类型检查和生产构建均成功。

- [x] **Step 6: 提交**

```bash
git add frontend/src/utils/getPastedFiles.ts frontend/tests/getPastedFiles.test.mjs frontend/src/components/ChatPanel.tsx
git commit -m "feat: support pasted chat attachments"
```
