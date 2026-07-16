import type { ThemeConfig } from "antd";
import { theme as antdTheme } from "antd";

export type ThemeMode = "editorial" | "precision" | "night";

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
  const isNight = mode === "night";
  const isEditorial = mode === "editorial";

  return {
    algorithm: isNight ? antdTheme.darkAlgorithm : antdTheme.defaultAlgorithm,
    token: {
      colorPrimary: isEditorial ? "#087F73" : isNight ? "#3B82F6" : "#2563EB",
      colorBgBase: isEditorial ? "#F5F1E8" : isNight ? "#07111F" : "#F6F8FC",
      colorBgContainer: isEditorial ? "#FFFCF5" : isNight ? "#0D1726" : "#FFFFFF",
      colorBorder: isNight ? "rgba(148,163,184,0.18)" : "rgba(15,23,42,0.12)",
      colorText: isNight ? "#F8FAFC" : "#172033",
      colorTextSecondary: isNight ? "#94A3B8" : "#64748B",
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
