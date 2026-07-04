import type { ThemeConfig } from "antd";
import { theme as antdTheme } from "antd";

// 深色科技风: 近黑背景 + 蓝色发光弧线
export const colors = {
  bg: "#0A0A0B",
  bgDeep: "#050506",
  surface: "#141416",
  surfaceAlt: "#1B1B1F",
  border: "rgba(255,255,255,0.08)",
  textPrimary: "#F5F5F7",
  textSecondary: "#8A8A93",
  accent: "#3B82F6",
  accentLight: "#60A5FA",
  risk: {
    high: "#EF4444",
    medium: "#F59E0B",
    low: "#3B82F6",
    compliant: "#22C55E",
  },
};

export const antdDarkTheme: ThemeConfig = {
  algorithm: antdTheme.darkAlgorithm,
  token: {
    colorPrimary: colors.accent,
    colorBgBase: colors.bg,
    colorBgContainer: colors.surface,
    colorBorder: colors.border,
    colorText: colors.textPrimary,
    colorTextSecondary: colors.textSecondary,
    borderRadius: 12,
    fontFamily:
      '-apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC", "Microsoft YaHei", sans-serif',
  },
};

export const riskLabel: Record<string, string> = {
  high: "高危",
  medium: "中危",
  low: "低危",
  compliant: "合规",
};
