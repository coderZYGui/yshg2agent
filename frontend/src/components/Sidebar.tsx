import {
  DeleteOutlined,
  FileTextOutlined,
  LogoutOutlined,
  MoonOutlined,
  PlusOutlined,
  SafetyCertificateOutlined,
  SunOutlined,
  UploadOutlined,
} from "@ant-design/icons";
import { Button, Dropdown, Modal, Segmented, Tag, Tooltip, Upload, message } from "antd";
import { useEffect, useState } from "react";
import {
  deleteConversation,
  deleteKnowledge,
  getConversationMessages,
  listConversations,
  listKnowledge,
  uploadKnowledge,
} from "../api/client";
import { useStore } from "../store/useStore";
import { colors } from "../theme";
import type { Conversation, DocumentItem, RoleKey } from "../types";

const roleOptions = [
  { label: "产品", value: "pm" },
  { label: "测试", value: "qa" },
  { label: "法务", value: "legal" },
];

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
  const [kbOpen, setKbOpen] = useState(false);
  const [kb, setKb] = useState<DocumentItem[]>([]);
  const [loadingKb, setLoadingKb] = useState(false);

  const refreshConvs = () => listConversations().then(setConvs).catch(() => {});
  const refreshKb = () => {
    setLoadingKb(true);
    listKnowledge()
      .then(setKb)
      .catch(() => {})
      .finally(() => setLoadingKb(false));
  };

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

  const handleUpload = async (file: File) => {
    try {
      await uploadKnowledge(file);
      message.success(`已入库 ${file.name}`);
      refreshKb();
    } catch {
      message.error("入库失败");
    }
    return false;
  };

  return (
    <div className="sidebar">
      <div className="brand">
        <span className="brand-dot" />
        <span>隐私合规评审</span>
        <div style={{ flex: 1 }} />
        <Tooltip title={themeMode === "dark" ? "切换浅色" : "切换深色"}>
          <Button
            type="text"
            size="small"
            icon={themeMode === "dark" ? <SunOutlined /> : <MoonOutlined />}
            onClick={() => setThemeMode(themeMode === "dark" ? "light" : "dark")}
          />
        </Tooltip>
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

      <Button
        icon={<SafetyCertificateOutlined />}
        block
        onClick={() => {
          setKbOpen(true);
          refreshKb();
        }}
      >
        知识库管理
      </Button>

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

      <Modal
        title="隐私合规知识库"
        open={kbOpen}
        onCancel={() => setKbOpen(false)}
        footer={null}
        width={560}
      >
        <Upload beforeUpload={(f) => handleUpload(f as File)} showUploadList={false} multiple>
          <Button icon={<UploadOutlined />} type="primary" style={{ marginBottom: 12 }}>
            上传知识库文档（Word/PDF/PPT/Excel/Markdown）
          </Button>
        </Upload>
        <div style={{ maxHeight: 360, overflowY: "auto" }}>
          {loadingKb && <div style={{ color: colors.textSecondary }}>加载中...</div>}
          {kb.map((d) => (
            <div
              key={d.id}
              style={{
                display: "flex",
                alignItems: "center",
                justifyContent: "space-between",
                padding: "8px 10px",
                border: `1px solid ${colors.border}`,
                borderRadius: 10,
                marginBottom: 8,
              }}
            >
              <div style={{ minWidth: 0 }}>
                <div style={{ fontSize: 13, whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>
                  <FileTextOutlined style={{ marginRight: 8 }} />
                  {d.filename}
                </div>
                <div style={{ fontSize: 11, color: colors.textSecondary, marginTop: 2 }}>
                  {d.summary?.slice(0, 40)}
                </div>
              </div>
              <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                <Tag color={d.parse_status === "done" ? "green" : "orange"}>
                  {d.parse_status}
                </Tag>
                <Button
                  type="text"
                  danger
                  size="small"
                  icon={<DeleteOutlined />}
                  onClick={async () => {
                    await deleteKnowledge(d.id);
                    refreshKb();
                  }}
                />
              </div>
            </div>
          ))}
          {!loadingKb && kb.length === 0 && (
            <div style={{ color: colors.textSecondary }}>知识库为空，请先上传文档</div>
          )}
        </div>
      </Modal>
    </div>
  );
}
