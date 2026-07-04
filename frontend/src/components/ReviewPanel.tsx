import { AuditOutlined } from "@ant-design/icons";
import { Segmented, Tag } from "antd";
import { useState } from "react";
import { colors, riskLabel } from "../theme";
import type { ReviewResult } from "../types";

const filterOptions = [
  { label: "全部", value: "all" },
  { label: "高危", value: "high" },
  { label: "中危", value: "medium" },
  { label: "低危", value: "low" },
];

export default function ReviewPanel({ review }: { review: ReviewResult | null }) {
  const [filter, setFilter] = useState("all");

  const items =
    review?.items.filter((i) => filter === "all" || i.risk_level === filter) ?? [];

  return (
    <div className="review-col">
      <div className="review-header">
        <AuditOutlined style={{ color: colors.accentLight }} />
        结构化评审意见
      </div>
      <div className="review-body">
        {!review && (
          <div className="review-empty">
            发起评审后，风险项与整改建议将在此结构化展示
          </div>
        )}

        {review && (
          <>
            <div className="review-summary">{review.summary}</div>
            <Segmented
              size="small"
              block
              options={filterOptions}
              value={filter}
              onChange={(v) => setFilter(v as string)}
            />
            {items.map((item, idx) => (
              <div className="risk-card" key={idx}>
                <div className="risk-head">
                  <span className="risk-loc">{item.location || "评审项"}</span>
                  <Tag
                    style={{
                      color: colors.risk[item.risk_level] ?? colors.accent,
                      borderColor: colors.risk[item.risk_level] ?? colors.accent,
                      background: "transparent",
                      fontWeight: 600,
                    }}
                  >
                    {riskLabel[item.risk_level] ?? item.risk_level}
                  </Tag>
                </div>
                <div className="risk-field">
                  <b>合规判定：</b>
                  {item.verdict}
                </div>
                <div className="risk-field">
                  <b>整改建议：</b>
                  {item.suggestion}
                </div>
                {item.citations?.length > 0 && (
                  <div>
                    <div style={{ fontSize: 11.5, color: colors.textSecondary, margin: "6px 0 2px" }}>
                      引用来源：
                    </div>
                    {item.citations.map((c, ci) => (
                      <div className="cite" key={ci}>
                        《{c.document}》 · 相关度 {c.score?.toFixed?.(2) ?? c.score}
                        <div style={{ marginTop: 2 }}>{c.snippet}</div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            ))}
            {items.length === 0 && (
              <div className="review-empty">当前筛选条件下无风险项</div>
            )}
          </>
        )}
      </div>
    </div>
  );
}
