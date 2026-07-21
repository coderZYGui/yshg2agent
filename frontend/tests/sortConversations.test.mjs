import assert from "node:assert/strict";
import test from "node:test";

import { sortConversations } from "../src/utils/sortConversations.ts";

const conversation = (id, updatedAt, pinned = false) => ({
  id,
  title: id,
  role: "pm",
  created_at: updatedAt,
  updated_at: updatedAt,
  pinned,
});

test("置顶会话排在普通会话之前，同组内按更新时间倒序", () => {
  const sorted = sortConversations([
    conversation("normal-new", "2026-07-21T12:00:00.000Z"),
    conversation("pinned-old", "2026-07-20T12:00:00.000Z", true),
    conversation("normal-old", "2026-07-19T12:00:00.000Z"),
    conversation("pinned-new", "2026-07-21T11:00:00.000Z", true),
  ]);

  assert.deepEqual(
    sorted.map((item) => item.id),
    ["pinned-new", "pinned-old", "normal-new", "normal-old"],
  );
});

test("排序不修改原数组", () => {
  const conversations = [
    conversation("normal", "2026-07-21T12:00:00.000Z"),
    conversation("pinned", "2026-07-20T12:00:00.000Z", true),
  ];

  sortConversations(conversations);

  assert.deepEqual(
    conversations.map((item) => item.id),
    ["normal", "pinned"],
  );
});
