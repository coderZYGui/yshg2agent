import {
  BgColorsOutlined,
  CheckOutlined,
  DeleteOutlined,
  FileTextOutlined,
  LogoutOutlined,
  PlusOutlined,
  SafetyCertificateFilled,
} from "@ant-design/icons";
import { Button, Dropdown, Modal, Segmented, Tooltip, message } from "antd";
import { useEffect, useState } from "react";
import {
  deleteConversation,
  getConversationMessages,
  listConversations,
} from "../api/client";
import { useStore } from "../store/useStore";
import { colors } from "../theme";
import type { Conversation, RoleKey } from "../types";

const roleOptions = [
  { label: "产品", value: "pm" },
  { label: "测试", value: "qa" },
  { label: "法务", value: "legal" },
];

const toneOptions = [
  { key: "editorial", label: "暖米青", color: "#087F73" },
  { key: "precision", label: "明净蓝", color: "#2563EB" },
  { key: "night", label: "深海蓝", color: "#07111F" },
] as const;

export default function Sidebar() {
  const {
    role,
    setRole,
    username,
    logout,
    newConversation,
    setConversationMessages,
    conversationId,
    themeMode,
    setThemeMode,
  } = useStore();
  const [convs, setConvs] = useState<Conversation[]>([]);

  const refreshConvs = () => listConversations().then(setConvs).catch(() => {});

  const openConversation = async (id: number) => {
    try {
      const rows = await getConversationMessages(id);
      const messages = rows.map((m) => ({
        id: String(m.id),
        role: m.role,
        content: m.content,
        review: m.review_result ?? undefined,
      }));
      const activeReview =
        [...rows].reverse().find((m) => m.role === "assistant" && m.review_result)
          ?.review_result ?? null;
      setConversationMessages(id, messages, activeReview);
    } catch {
      message.error("鍔犺浇浼氳瘽澶辫触");
    }
  };

  const removeConversation = (conv: Conversation) => {
    Modal.confirm({
      title: "删除历史会话",
      content: `确定删除「${conv.title}」吗？删除后不可恢复。`,
      okText: "删除",
      okButtonProps: { danger: true },
      cancelText: "取消",
      onOk: async () => {
        try {
          await deleteConversation(conv.id);
          setConvs((items) => items.filter((item) => item.id !== conv.id));
          if (conversationId === conv.id) newConversation();
          message.success("已删除会话");
        } catch (error) {
          message.error("删除会话失败，请确认后端服务已重启");
          throw error;
        }
      },
    });
  };

  useEffect(() => {
    refreshConvs();
  }, [conversationId]);

  return (
    <div className="sidebar">
      <div className="brand">
        <span className="brand-mark" aria-hidden="true">
          <SafetyCertificateFilled />
        </span>
        <span className="brand-title">隐私合规评审</span>
        <div style={{ flex: 1 }} />
        <Dropdown
          trigger={["click"]}
          placement="bottomRight"
          menu={{
            selectable: true,
            selectedKeys: [themeMode],
            items: toneOptions.map((tone) => ({
              key: tone.key,
              icon: <span className="tone-dot" style={{ background: tone.color }} />,
              label: (
                <span className="tone-option-label">
                  <span>{tone.label}</span>
                  {tone.key === themeMode && <CheckOutlined />}
                </span>
              ),
            })),
            onClick: ({ key }) => setThemeMode(key as typeof themeMode),
          }}
        >
          <Tooltip title="切换页面色调">
            <Button
              className="tone-trigger"
              type="default"
              size="small"
              icon={<BgColorsOutlined />}
              aria-label="切换页面色调"
            >
              色调
            </Button>
          </Tooltip>
        </Dropdown>
      </div>

      <div>
        <div style={{ fontSize: 12, color: colors.textSecondary, marginBottom: 6 }}>
          当前评审角色
        </div>
        <Segmented
          block
          options={roleOptions}
          value={role}
          onChange={(v) => setRole(v as RoleKey)}
        />
      </div>

      <Button icon={<PlusOutlined />} block onClick={newConversation}>
        新建会话
      </Button>

      <div style={{ fontSize: 12, color: colors.textSecondary, marginTop: 4 }}>
        历史会话
      </div>
      <div className="conv-list">
        {convs.length === 0 && (
          <div style={{ fontSize: 12, color: colors.textSecondary, padding: 8 }}>
            暂无会话
          </div>
        )}
        {convs.map((c) => (
          <Dropdown
            key={c.id}
            trigger={["contextMenu"]}
            menu={{
              items: [
                {
                  key: "delete",
                  danger: true,
                  icon: <DeleteOutlined />,
                  label: "删除会话",
                },
              ],
              onClick: () => removeConversation(c),
            }}
          >
            <div
              className={`conv-item ${c.id === conversationId ? "active" : ""}`}
              onClick={() => openConversation(c.id)}
              role="button"
              tabIndex={0}
              onKeyDown={(e) => {
                if (e.key === "Enter" || e.key === " ") openConversation(c.id);
              }}
            >
              <FileTextOutlined style={{ marginRight: 8 }} />
              {c.title}
            </div>
          </Dropdown>
        ))}
      </div>

      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          borderTop: `1px solid ${colors.border}`,
          paddingTop: 10,
          fontSize: 13,
          color: colors.textSecondary,
        }}
      >
        <span>{username}</span>
        <Tooltip title="退出登录">
          <Button type="text" size="small" icon={<LogoutOutlined />} onClick={logout} />
        </Tooltip>
      </div>

    </div>
  );
}
