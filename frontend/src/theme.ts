import type { ThemeConfig } from "antd";
import { theme as antdTheme } from "antd";

export type ThemeMode = "dark" | "light";

export const colors = {
  bg: "var(--app-bg)",
  bgDeep: "var(--app-bg-deep)",
  surface: "var(--app-surface)",
  surfaceAlt: "var(--app-surface-alt)",
  border: "var(--app-border)",
  textPrimary: "var(--app-text-primary)",
  textSecondary: "var(--app-text-secondary)",
  accent: "var(--app-accent)",
  accentLight: "var(--app-accent-light)",
  risk: {
    high: "var(--risk-high)",
    medium: "var(--risk-medium)",
    low: "var(--risk-low)",
    compliant: "var(--risk-compliant)",
  },
};

export function getAntdTheme(mode: ThemeMode): ThemeConfig {
  const isLight = mode === "light";

  return {
    algorithm: isLight ? antdTheme.defaultAlgorithm : antdTheme.darkAlgorithm,
    token: {
      colorPrimary: "#3B82F6",
      colorBgBase: isLight ? "#F6F8FC" : "#0A0A0B",
      colorBgContainer: isLight ? "#FFFFFF" : "#141416",
      colorBorder: isLight ? "rgba(15,23,42,0.12)" : "rgba(255,255,255,0.08)",
      colorText: isLight ? "#172033" : "#F5F5F7",
      colorTextSecondary: isLight ? "#6B7280" : "#8A8A93",
      borderRadius: 12,
      fontFamily:
        '-apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC", "Microsoft YaHei", sans-serif',
    },
  };
}

export const riskLabel: Record<string, string> = {
  high: "高危",
  medium: "中危",
  low: "低危",
  compliant: "合规",
};
