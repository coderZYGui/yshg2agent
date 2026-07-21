import { ConfigProvider } from "antd";
import zhCN from "antd/locale/zh_CN";
import { useEffect, useState } from "react";
import { login } from "./api/client";
import AccessGate from "./components/AccessGate";
import ChatPanel from "./components/ChatPanel";
import Sidebar from "./components/Sidebar";
import { useStore } from "./store/useStore";
import { getAntdTheme } from "./theme";
import type { RoleKey } from "./types";

type AccessState = "checking" | "required" | "verified";

export default function App() {
  const token = useStore((s) => s.token);
  const setAuth = useStore((s) => s.setAuth);
  const themeMode = useStore((s) => s.themeMode);
  const [accessState, setAccessState] = useState<AccessState>("checking");
  const [autoLoginError, setAutoLoginError] = useState("");

  useEffect(() => {
    document.documentElement.dataset.theme = themeMode;
  }, [themeMode]);

  useEffect(() => {
    let cancelled = false;
    fetch("/api/access/status", { credentials: "include" })
      .then((response) => {
        if (!response.ok) throw new Error("status unavailable");
        return response.json() as Promise<{ authenticated: boolean }>;
      })
      .then((data) => {
        if (!cancelled) {
          setAccessState(data.authenticated ? "verified" : "required");
        }
      })
      .catch(() => {
        if (!cancelled) setAccessState("required");
      });

    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    if (accessState !== "verified" || token) return;

    let cancelled = false;
    login("pm", "pm123")
      .then((data) => {
        if (!cancelled) {
          setAuth(data.access_token, data.username, data.role as RoleKey);
        }
      })
      .catch(() => {
        if (!cancelled) setAutoLoginError("自动进入失败，请确认后端服务已启动。");
      });

    return () => {
      cancelled = true;
    };
  }, [accessState, setAuth, token]);

  return (
    <ConfigProvider theme={getAntdTheme(themeMode)} locale={zhCN}>
      {accessState === "checking" ? (
        <>
          <div className="app-glow" />
          <div className="app-shell" aria-label="正在验证访问状态" />
        </>
      ) : accessState === "required" ? (
        <AccessGate onVerified={() => setAccessState("verified")} />
      ) : (
        <>
          <div className="app-glow" />
          {!token && !autoLoginError ? (
            <div className="app-shell" />
          ) : autoLoginError ? (
            <div className="login-wrap">
              <div className="review-empty">{autoLoginError}</div>
            </div>
          ) : (
            <div className="app-shell">
              <Sidebar />
              <ChatPanel />
            </div>
          )}
        </>
      )}
    </ConfigProvider>
  );
}
