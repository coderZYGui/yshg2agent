import { ConfigProvider } from "antd";
import zhCN from "antd/locale/zh_CN";
import ChatPanel from "./components/ChatPanel";
import Login from "./components/Login";
import ReviewPanel from "./components/ReviewPanel";
import Sidebar from "./components/Sidebar";
import { useStore } from "./store/useStore";
import { antdDarkTheme } from "./theme";

export default function App() {
  const token = useStore((s) => s.token);
  const activeReview = useStore((s) => s.activeReview);

  return (
    <ConfigProvider theme={antdDarkTheme} locale={zhCN}>
      <div className="app-glow" />
      {!token ? (
        <Login />
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
