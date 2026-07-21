import type { Conversation } from "../types";

export function sortConversations(conversations: Conversation[]): Conversation[] {
  return [...conversations].sort((a, b) => {
    const pinnedDifference = Number(Boolean(b.pinned)) - Number(Boolean(a.pinned));
    return pinnedDifference || b.updated_at.localeCompare(a.updated_at);
  });
}
