import { create } from "zustand";
import type { ThemeMode } from "../theme";
import type { ChatMessage, DocumentItem, ReviewResult, RoleKey } from "../types";

function getInitialThemeMode(): ThemeMode {
  const saved = localStorage.getItem("themeMode");
  if (saved === "editorial" || saved === "precision" || saved === "night") {
    return saved;
  }
  return saved === "dark" ? "night" : "precision";
}

interface AppState {
  token: string | null;
  username: string | null;
  role: RoleKey;

  conversationId: string | null;
  messages: ChatMessage[];
  activeReview: ReviewResult | null;
  attachments: DocumentItem[];
  sending: boolean;
  themeMode: ThemeMode;
  historyVersion: number;

  setAuth: (token: string, username: string, role: RoleKey) => void;
  logout: () => void;
  setRole: (role: RoleKey) => void;

  setConversationId: (id: string | null) => void;
  setConversationMessages: (
    id: string,
    messages: ChatMessage[],
    activeReview: ReviewResult | null
  ) => void;
  addMessage: (m: ChatMessage) => void;
  updateLastAssistant: (patch: Partial<ChatMessage>) => void;
  appendToLastAssistant: (text: string) => void;
  setActiveReview: (r: ReviewResult | null) => void;
  addAttachment: (d: DocumentItem) => void;
  clearAttachments: () => void;
  setSending: (v: boolean) => void;
  setThemeMode: (mode: ThemeMode) => void;
  notifyHistoryChanged: () => void;
  newConversation: () => void;
}

export const useStore = create<AppState>((set) => ({
  token: localStorage.getItem("token"),
  username: localStorage.getItem("username"),
  role: (localStorage.getItem("role") as RoleKey) || "pm",

  conversationId: null,
  messages: [],
  activeReview: null,
  attachments: [],
  sending: false,
  themeMode: getInitialThemeMode(),
  historyVersion: 0,

  setAuth: (token, username, role) => {
    localStorage.setItem("token", token);
    localStorage.setItem("username", username);
    localStorage.setItem("role", role);
    set({ token, username, role });
  },
  logout: () => {
    localStorage.clear();
    set({ token: null, username: null, messages: [], conversationId: null, activeReview: null });
  },
  setRole: (role) => {
    localStorage.setItem("role", role);
    set({ role });
  },

  setConversationId: (id) => set({ conversationId: id }),
  setConversationMessages: (id, messages, activeReview) =>
    set({ conversationId: id, messages, activeReview, attachments: [] }),
  addMessage: (m) => set((s) => ({ messages: [...s.messages, m] })),
  updateLastAssistant: (patch) =>
    set((s) => {
      const msgs = [...s.messages];
      for (let i = msgs.length - 1; i >= 0; i--) {
        if (msgs[i].role === "assistant") {
          msgs[i] = { ...msgs[i], ...patch };
          break;
        }
      }
      return { messages: msgs };
    }),
  appendToLastAssistant: (text) =>
    set((s) => {
      const msgs = [...s.messages];
      for (let i = msgs.length - 1; i >= 0; i--) {
        if (msgs[i].role === "assistant") {
          msgs[i] = { ...msgs[i], content: msgs[i].content + text };
          break;
        }
      }
      return { messages: msgs };
    }),
  setActiveReview: (r) => set({ activeReview: r }),
  addAttachment: (d) => set((s) => ({ attachments: [...s.attachments, d] })),
  clearAttachments: () => set({ attachments: [] }),
  setSending: (v) => set({ sending: v }),
  setThemeMode: (themeMode) => {
    localStorage.setItem("themeMode", themeMode);
    set({ themeMode });
  },
  notifyHistoryChanged: () =>
    set((state) => ({ historyVersion: state.historyVersion + 1 })),
  newConversation: () =>
    set({ conversationId: null, messages: [], activeReview: null, attachments: [] }),
}));
