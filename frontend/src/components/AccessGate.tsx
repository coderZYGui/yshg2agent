import { type FormEvent, useEffect, useRef, useState } from "react";

import "./access-gate.css";

interface AccessGateProps {
  onVerified: () => void;
}

export default function AccessGate({ onVerified }: AccessGateProps) {
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  const submit = async (event: FormEvent) => {
    event.preventDefault();
    if (!password || submitting) return;

    setSubmitting(true);
    setError("");
    try {
      const response = await fetch("/api/access/verify", {
        method: "POST",
        credentials: "include",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ password }),
      });
      if (!response.ok) {
        setError(
          response.status === 401
            ? "访问密码不正确，请重新输入"
            : "校验服务暂时不可用，请稍后重试",
        );
        return;
      }
      onVerified();
    } catch {
      setError("无法连接后端服务，请确认服务已启动");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <main className="access-gate">
      <div className="access-gate__shade" />
      <div className="access-gate__brand">
        <span className="access-gate__mark" aria-hidden="true" />
        <div>
          <strong>隐私合规智能评审</strong>
          <span>PRIVACY REVIEW · AI ASSISTANT</span>
        </div>
      </div>

      <section className="access-gate__panel" aria-labelledby="access-title">
        <p className="access-gate__eyebrow">SECURE ACCESS</p>
        <h1 id="access-title">进入评审工作台</h1>
        <p className="access-gate__description">请输入访问密码，继续使用隐私合规智能评审。</p>

        <form className="access-gate__form" onSubmit={submit}>
          <label className="access-gate__input-wrap">
            <span className="access-gate__sr-only">访问密码</span>
            <input
              ref={inputRef}
              type="password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              placeholder="输入访问密码"
              autoComplete="current-password"
              disabled={submitting}
            />
          </label>
          <button type="submit" disabled={submitting || !password}>
            {submitting ? "校验中" : "校验"}
          </button>
        </form>
        <div className="access-gate__feedback" role="status" aria-live="polite">
          {error}
        </div>
      </section>

      <p className="access-gate__footer">AUTHORIZED PERSONNEL ONLY</p>
    </main>
  );
}
