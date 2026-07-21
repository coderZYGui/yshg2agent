import {
  DeleteOutlined,
  EditOutlined,
  FileTextOutlined,
  LogoutOutlined,
  MoreOutlined,
  PlusOutlined,
  PushpinFilled,
  PushpinOutlined,
  SafetyCertificateFilled,
} from "@ant-design/icons";
import { Button, Dropdown, Input, Modal, Segmented, Tooltip, message } from "antd";
import type { MenuProps } from "antd";
import { useEffect, useState } from "react";
import {
  deleteLocalConversation,
  getLocalConversation,
  listLocalConversations,
  renameLocalConversation,
  setLocalConversationPinned,
} from "../services/localHistory";
import { useStore } from "../store/useStore";
import { colors } from "../theme";
import type { Conversation, RoleKey } from "../types";
import { sortConversations } from "../utils/sortConversations";

import "./conversation-menu.css";

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
    historyVersion,
    sending,
    themeMode,
    setThemeMode,
  } = useStore();
  const [convs, setConvs] = useState<Conversation[]>([]);
  const [renameTarget, setRenameTarget] = useState<Conversation | null>(null);
  const [renameValue, setRenameValue] = useState("");
  const [renameSaving, setRenameSaving] = useState(false);
  const toneIndex = toneOptions.findIndex((tone) => tone.key === themeMode);
  const currentTone = toneOptions[toneIndex] ?? toneOptions[0];
  const nextTone = toneOptions[(toneIndex + 1) % toneOptions.length];

  const owner = username ?? "anonymous";
  const refreshConvs = () =>
    listLocalConversations(owner)
      .then(setConvs)
      .catch(() => message.error("读取本地历史记录失败"));

  const openConversation = async (id: string) => {
    try {
      const conversation = await getLocalConversation(owner, id);
      if (!conversation) return;
      const messages = conversation.messages;
      const activeReview =
        [...messages].reverse().find((m) => m.role === "assistant" && m.review)?.review ??
        null;
      setConversationMessages(id, messages, activeReview);
    } catch {
      message.error("读取本地历史记录失败");
    }
  };

  const startRename = (conv: Conversation) => {
    setRenameTarget(conv);
    setRenameValue(conv.title);
  };

  const confirmRename = async () => {
    if (!renameTarget) return;
    const title = renameValue.replace(/\s+/g, " ").trim();
    if (!title) {
      message.warning("会话名称不能为空");
      return;
    }

    setRenameSaving(true);
    try {
      await renameLocalConversation(owner, renameTarget.id, title);
      setConvs((items) =>
        items.map((item) =>
          item.id === renameTarget.id ? { ...item, title } : item
        )
      );
      setRenameTarget(null);
      message.success("会话已重命名");
    } catch {
      message.error("重命名失败");
    } finally {
      setRenameSaving(false);
    }
  };

  const togglePinned = async (conv: Conversation) => {
    const pinned = !conv.pinned;
    try {
      await setLocalConversationPinned(owner, conv.id, pinned);
      setConvs((items) =>
        sortConversations(
          items.map((item) => (item.id === conv.id ? { ...item, pinned } : item))
        )
      );
      message.success(pinned ? "会话已置顶" : "已取消置顶");
    } catch {
      message.error(pinned ? "置顶失败" : "取消置顶失败");
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
          await deleteLocalConversation(owner, conv.id);
          setConvs((items) => items.filter((item) => item.id !== conv.id));
          if (conversationId === conv.id) newConversation();
          message.success("已删除会话");
        } catch (error) {
          message.error("删除本地会话失败");
          throw error;
        }
      },
    });
  };

  const getConversationMenu = (conv: Conversation): MenuProps => ({
    items: [
      {
        key: "rename",
        icon: <EditOutlined />,
        label: "重命名",
      },
      {
        key: "pin",
        icon: conv.pinned ? <PushpinFilled /> : <PushpinOutlined />,
        label: conv.pinned ? "取消置顶" : "置顶",
      },
      { type: "divider" as const },
      {
        key: "delete",
        danger: true,
        icon: <DeleteOutlined />,
        label: "删除会话",
      },
    ],
    onClick: ({ key, domEvent }) => {
      domEvent.stopPropagation();
      if (key === "rename") startRename(conv);
      else if (key === "pin") void togglePinned(conv);
      else if (key === "delete") removeConversation(conv);
    },
  });

  useEffect(() => {
    refreshConvs();
  }, [conversationId, historyVersion, owner]);

  return (
    <div className="sidebar">
      <div className="brand">
        <span className="brand-mark" aria-hidden="true">
          <SafetyCertificateFilled />
        </span>
        <span className="brand-title">隐私合规评审</span>
        <div style={{ flex: 1 }} />
        <Tooltip title={`当前：${currentTone.label}，点击切换为${nextTone.label}`}>
          <Button
            className="tone-trigger"
            type="default"
            size="small"
            icon={<span className="tone-dot" style={{ background: currentTone.color }} />}
            aria-label={`切换页面色调，当前${currentTone.label}`}
            onClick={() => setThemeMode(nextTone.key)}
          />
        </Tooltip>
      </div>

      <div>
        <div style={{ fontSize: 12, color: colors.textSecondary, marginBottom: 6 }}>
          当前评审角色
        </div>
        <Segmented
          block
          disabled={sending}
          options={roleOptions}
          value={role}
          onChange={(v) => setRole(v as RoleKey)}
        />
      </div>

      <Button icon={<PlusOutlined />} block disabled={sending} onClick={newConversation}>
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
            disabled={sending}
            trigger={["contextMenu"]}
            overlayClassName="conversation-action-menu"
            menu={getConversationMenu(c)}
          >
            <div
              className={`conv-item ${c.id === conversationId ? "active" : ""} ${
                c.pinned ? "pinned" : ""
              }`}
            >
              <button
                className="conv-open"
                type="button"
                disabled={sending}
                onClick={() => openConversation(c.id)}
              >
                <span className="conv-item-icon" aria-hidden="true">
                  {c.pinned ? <PushpinFilled /> : <FileTextOutlined />}
                </span>
                <span className="conv-item-title" title={c.title}>
                  {c.title}
                </span>
              </button>
              <Dropdown
                disabled={sending}
                trigger={["click"]}
                placement="bottomRight"
                overlayClassName="conversation-action-menu"
                menu={getConversationMenu(c)}
              >
                <Button
                  className="conv-more"
                  type="text"
                  size="small"
                  icon={<MoreOutlined />}
                  aria-label={`管理会话：${c.title}`}
                />
              </Dropdown>
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
          <Button
            type="text"
            size="small"
            icon={<LogoutOutlined />}
            disabled={sending}
            onClick={logout}
          />
        </Tooltip>
      </div>

      <Modal
        title="重命名会话"
        open={Boolean(renameTarget)}
        okText="保存"
        cancelText="取消"
        confirmLoading={renameSaving}
        okButtonProps={{ disabled: !renameValue.trim() }}
        onOk={confirmRename}
        onCancel={() => {
          if (!renameSaving) setRenameTarget(null);
        }}
      >
        <div className="rename-conversation-field">
          <label htmlFor="conversation-title">会话名称</label>
          <Input
            id="conversation-title"
            value={renameValue}
            maxLength={60}
            showCount
            autoFocus
            onChange={(event) => setRenameValue(event.target.value)}
            onPressEnter={() => {
              if (renameValue.trim() && !renameSaving) void confirmRename();
            }}
          />
        </div>
      </Modal>
    </div>
  );
}
