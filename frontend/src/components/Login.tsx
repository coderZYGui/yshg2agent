import { SafetyCertificateOutlined } from "@ant-design/icons";
import { Button, Input, Segmented, Tabs, Typography, message } from "antd";
import { useState } from "react";
import { login, register } from "../api/client";
import { useStore } from "../store/useStore";
import { colors } from "../theme";
import type { RoleKey } from "../types";

const roleOptions = [
  { label: "产品经理", value: "pm" },
  { label: "测试工程师", value: "qa" },
  { label: "法务", value: "legal" },
];

export default function Login() {
  const setAuth = useStore((s) => s.setAuth);
  const [tab, setTab] = useState("login");
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [role, setRole] = useState<RoleKey>("pm");
  const [loading, setLoading] = useState(false);

  const doLogin = async () => {
    if (!username || !password) return message.warning("请输入用户名和密码");
    setLoading(true);
    try {
      const data = await login(username, password);
      setAuth(data.access_token, data.username, data.role as RoleKey);
      message.success("登录成功");
    } catch {
      message.error("用户名或密码错误");
    } finally {
      setLoading(false);
    }
  };

  const doRegister = async () => {
    if (!username || !password) return message.warning("请输入用户名和密码");
    setLoading(true);
    try {
      await register(username, password, role);
      const data = await login(username, password);
      setAuth(data.access_token, data.username, data.role as RoleKey);
      message.success("注册成功");
    } catch {
      message.error("注册失败(用户名可能已存在)");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-wrap">
      <div className="login-card">
        <div style={{ textAlign: "center", marginBottom: 20 }}>
          <div
            style={{
              width: 52,
              height: 52,
              margin: "0 auto 12px",
              borderRadius: 14,
              background: "linear-gradient(135deg,#3b82f6,#60a5fa)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              fontSize: 26,
              boxShadow: "0 0 24px rgba(59,130,246,.6)",
            }}
          >
            <SafetyCertificateOutlined />
          </div>
          <Typography.Title level={4} style={{ margin: 0 }}>
            隐私合规智能评审
          </Typography.Title>
          <Typography.Text style={{ color: colors.textSecondary }}>
            AI 驱动的隐私合规评审助手
          </Typography.Text>
        </div>

        <Tabs
          activeKey={tab}
          onChange={setTab}
          centered
          items={[
            { key: "login", label: "登录" },
            { key: "register", label: "注册" },
          ]}
        />

        <Input
          size="large"
          placeholder="用户名"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          style={{ marginBottom: 12 }}
        />
        <Input.Password
          size="large"
          placeholder="密码"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          onPressEnter={tab === "login" ? doLogin : doRegister}
          style={{ marginBottom: 12 }}
        />

        {tab === "register" && (
          <Segmented
            block
            options={roleOptions}
            value={role}
            onChange={(v) => setRole(v as RoleKey)}
            style={{ marginBottom: 12 }}
          />
        )}

        <Button
          type="primary"
          size="large"
          block
          loading={loading}
          onClick={tab === "login" ? doLogin : doRegister}
        >
          {tab === "login" ? "登录" : "注册并登录"}
        </Button>

        <Typography.Paragraph
          style={{ color: colors.textSecondary, fontSize: 12, marginTop: 16, textAlign: "center" }}
        >
          演示账号: pm / qa / legal，密码分别为 pm123 / qa123 / legal123
        </Typography.Paragraph>
      </div>
    </div>
  );
}
