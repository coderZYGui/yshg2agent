import axios from "axios";
import type { DocumentItem, ReviewResult } from "../types";

const api = axios.create({ baseURL: "/api" });

api.interceptors.request.use((config) => {
  const token = localStorage.getItem("token");
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

export async function login(username: string, password: string) {
  const form = new URLSearchParams();
  form.set("username", username);
  form.set("password", password);
  const { data } = await api.post("/auth/login", form);
  return data as { access_token: string; role: string; username: string };
}

export async function register(username: string, password: string, role: string) {
  const { data } = await api.post("/auth/register", { username, password, role });
  return data;
}

export async function listKnowledge() {
  const { data } = await api.get("/knowledge");
  return data as DocumentItem[];
}

export async function uploadKnowledge(file: File) {
  const form = new FormData();
  form.append("file", file);
  const { data } = await api.post("/knowledge", form);
  return data as DocumentItem;
}

export async function deleteKnowledge(id: number) {
  await api.delete(`/knowledge/${id}`);
}

export async function uploadDocument(file: File, kind = "review") {
  const form = new FormData();
  form.append("file", file);
  form.append("kind", kind);
  const { data } = await api.post("/documents/upload", form);
  return data as DocumentItem;
}

export interface StreamHandlers {
  onMeta?: (m: { attachments?: number; images?: number }) => void;
  onToken?: (t: string) => void;
  onReview?: (r: ReviewResult) => void;
  onDone?: () => void;
  onError?: (e: unknown) => void;
}

export async function chatStream(
  body: {
    role: string;
    message: string;
    document_ids: number[];
  },
  handlers: StreamHandlers
) {
  const token = localStorage.getItem("token");
  const resp = await fetch("/api/chat/stream", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: JSON.stringify(body),
  });

  if (!resp.ok || !resp.body) {
    handlers.onError?.(new Error(`HTTP ${resp.status}`));
    return;
  }

  const reader = resp.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });

    const blocks = buffer.split("\n\n");
    buffer = blocks.pop() ?? "";
    for (const block of blocks) {
      const eventLine = block.split("\n").find((l) => l.startsWith("event:"));
      const dataLine = block.split("\n").find((l) => l.startsWith("data:"));
      if (!eventLine || !dataLine) continue;
      const event = eventLine.slice("event:".length).trim();
      const dataStr = dataLine.slice("data:".length).trim();
      let data: any;
      try {
        data = JSON.parse(dataStr);
      } catch {
        data = dataStr;
      }
      if (event === "meta") handlers.onMeta?.(data);
      else if (event === "token") handlers.onToken?.(data.t ?? "");
      else if (event === "review") handlers.onReview?.(data);
      else if (event === "done") handlers.onDone?.();
      else if (event === "error") {
        handlers.onError?.(new Error(data.message ?? "附件处理失败"));
      }
    }
  }
}

export default api;
