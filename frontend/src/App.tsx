import { ConfigProvider } from "antd";
import zhCN from "antd/locale/zh_CN";
import { useEffect, useState } from "react";
import { login } from "./api/client";
import ChatPanel from "./components/ChatPanel";
import ReviewPanel from "./components/ReviewPanel";
import Sidebar from "./components/Sidebar";
import { useStore } from "./store/useStore";
import { getAntdTheme } from "./theme";
import type { RoleKey } from "./types";

export default function App() {
  const token = useStore((s) => s.token);
  const setAuth = useStore((s) => s.setAuth);
  const activeReview = useStore((s) => s.activeReview);
  const themeMode = useStore((s) => s.themeMode);
  const [autoLoginError, setAutoLoginError] = useState("");

  useEffect(() => {
    document.documentElement.dataset.theme = themeMode;
  }, [themeMode]);

  useEffect(() => {
    if (token) return;

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
  }, [setAuth, token]);

  return (
    <ConfigProvider theme={getAntdTheme(themeMode)} locale={zhCN}>
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
          <ReviewPanel review={activeReview} />
        </div>
      )}
    </ConfigProvider>
  );
}
