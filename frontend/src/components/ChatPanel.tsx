import {
  CloseOutlined,
  PaperClipOutlined,
  RobotOutlined,
  SendOutlined,
  UserOutlined,
} from "@ant-design/icons";
import { Button, Input, Tag, Upload, message as antdMessage } from "antd";
import { useEffect, useRef, useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { chatStream, uploadDocument } from "../api/client";
import { useStore } from "../store/useStore";
import { colors } from "../theme";
import type { ChatMessage, ReviewResult } from "../types";
import { stripReferenceTags } from "../utils/stripReferences";

const roleTitle: Record<string, string> = {
  pm: "产品经理 · 隐私风险评审",
  qa: "测试开发工程师 · 合规实现评审",
  legal: "法务 · 政策条款评审",
};

const riskLabel: Record<string, string> = {
  high: "高危",
  medium: "中危",
  low: "低危",
  compliant: "合规",
};

function formatReviewMarkdown(review: ReviewResult) {
  if (!review.items.length) return review.summary;

  const parts = ["【隐私合规审核报告】", "", review.summary];
  review.items.forEach((item, index) => {
    parts.push(
      "",
      `## ${index + 1}. ${item.location || "评审项"}（${riskLabel[item.risk_level] || item.risk_level}）`,
      "",
      `**合规判定：** ${item.verdict || "-"}`,
      "",
      `**整改建议：** ${item.suggestion || "-"}`
    );

    if (item.citations?.length) {
      parts.push("", "**引用来源：**");
      item.citations.forEach((citation) => {
        parts.push(
          `- ${citation.document}（相关度 ${citation.score ?? 0}）：${citation.snippet}`
        );
      });
    }
  });
  return parts.join("\n");
}

function Bubble({ msg }: { msg: ChatMessage }) {
  const isUser = msg.role === "user";
  return (
    <div className={`msg-row ${isUser ? "user" : "assistant"}`}>
      <div className={`avatar ${isUser ? "user" : "assistant"}`}>
        {isUser ? <UserOutlined /> : <RobotOutlined />}
      </div>
      <div className={`bubble ${isUser ? "user" : "assistant"}`}>
        {msg.content ? (
          <>
            <ReactMarkdown remarkPlugins={[remarkGfm]}>
              {stripReferenceTags(msg.content)}
            </ReactMarkdown>
            {msg.streaming && (
              <span style={{ color: colors.accent, marginLeft: 3 }} aria-hidden="true">
                ▍
              </span>
            )}
          </>
        ) : msg.streaming ? (
          <span style={{ color: colors.textSecondary }}>正在检索知识库并评审…</span>
        ) : null}
      </div>
    </div>
  );
}

export default function ChatPanel() {
  const {
    role,
    messages,
    conversationId,
    attachments,
    sending,
    addMessage,
    appendToLastAssistant,
    updateLastAssistant,
    setActiveReview,
    setConversationId,
    addAttachment,
    clearAttachments,
    setSending,
  } = useStore();
  const [text, setText] = useState("");
  const bodyRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bodyRef.current?.scrollTo({ top: bodyRef.current.scrollHeight, behavior: "smooth" });
  }, [messages]);

  const handleAttach = async (file: File) => {
    try {
      const doc = await uploadDocument(file, "review");
      addAttachment(doc);
      antdMessage.success(`已上传 ${file.name}`);
    } catch {
      antdMessage.error("上传失败");
    }
    return false;
  };

  const send = async () => {
    if (!text.trim() || sending) return;
    const userText = text.trim();
    setText("");
    addMessage({ id: crypto.randomUUID(), role: "user", content: userText });
    addMessage({ id: crypto.randomUUID(), role: "assistant", content: "", streaming: true });
    setSending(true);
    setActiveReview(null);

    const docIds = attachments.map((a) => a.id);

    await chatStream(
      { conversation_id: conversationId, role, message: userText, document_ids: docIds },
      {
        onMeta: (m) => setConversationId(m.conversation_id),
        onToken: (token) => {
          appendToLastAssistant(token);
        },
        onReview: (r) => {
          setActiveReview(r);
          const contentPatch = r.items.length ? { content: formatReviewMarkdown(r) } : {};
          updateLastAssistant({ ...contentPatch, review: r, streaming: false });
        },
        onDone: () => setSending(false),
        onError: () => {
          updateLastAssistant({ content: "评审失败，请稍后重试。", streaming: false });
          setSending(false);
        },
      }
    );
    clearAttachments();
  };

  return (
    <div className="chat-col">
      <div className="chat-header">
        <Tag color="blue" style={{ borderRadius: 8 }}>
          {roleTitle[role]}
        </Tag>
      </div>

      <div className="chat-body" ref={bodyRef}>
        {messages.length === 0 ? (
          <div className="empty-hero">
            <h1>
              今天要评审<span className="accent">什么</span>？
            </h1>
            <p>
              上传 PRD / 政策 / 架构文档或直接提问，AI 将比对隐私合规知识库并给出结构化评审。
            </p>
          </div>
        ) : (
          messages.map((m) => <Bubble key={m.id} msg={m} />)
        )}
      </div>

      <div className="chat-input">
        <div className="input-shell">
          {attachments.length > 0 && (
            <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
              {attachments.map((a) => (
                <span className="attach-chip" key={a.id}>
                  <PaperClipOutlined />
                  {a.filename}
                </span>
              ))}
            </div>
          )}
          <Input.TextArea
            variant="borderless"
            autoSize={{ minRows: 1, maxRows: 6 }}
            placeholder="描述你的评审诉求，或上传文档后提问…（Enter 发送）"
            value={text}
            onChange={(e) => setText(e.target.value)}
            onPressEnter={(e) => {
              if (!e.shiftKey) {
                e.preventDefault();
                send();
              }
            }}
          />
          <div className="input-toolbar">
            <Upload
              beforeUpload={(f) => handleAttach(f as File)}
              showUploadList={false}
              multiple
            >
              <Button type="text" size="small" icon={<PaperClipOutlined />}>
                附件
              </Button>
            </Upload>
            {attachments.length > 0 && (
              <Button
                type="text"
                size="small"
                icon={<CloseOutlined />}
                onClick={clearAttachments}
              >
                清除
              </Button>
            )}
            <div style={{ flex: 1 }} />
            <Button
              type="primary"
              icon={<SendOutlined />}
              loading={sending}
              onClick={send}
            >
              评审
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}
