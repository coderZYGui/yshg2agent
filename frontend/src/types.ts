export type RoleKey = "pm" | "qa" | "legal";

export interface Citation {
  document: string;
  snippet: string;
  score: number;
}

export interface RiskItem {
  risk_level: "high" | "medium" | "low" | "compliant";
  location: string;
  verdict: string;
  suggestion: string;
  citations: Citation[];
}

export interface ReviewResult {
  summary: string;
  items: RiskItem[];
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  review?: ReviewResult;
  streaming?: boolean;
}

export interface Conversation {
  id: number;
  title: string;
  role: string;
  created_at: string;
}

export interface DocumentItem {
  id: number;
  filename: string;
  mime: string;
  kind: string;
  parse_status: string;
  summary: string;
  created_at: string;
}
