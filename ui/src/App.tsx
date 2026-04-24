/*
 *  Copyright 2026 Collate Inc.
 *  Licensed under the Apache License, Version 2.0 (the "License"); you may
 *  not use this file except in compliance with the License. You may obtain
 *  a copy of the License at
 *
 *  http://www.apache.org/licenses/LICENSE-2.0
 */

import { useState, useCallback, useRef, useEffect } from 'react';

const API_URL = import.meta.env['VITE_API_URL'] ?? 'http://localhost:8000';

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface AuditEntry {
  tool_name: string;
  duration_ms?: number | null;
  success?: boolean;
  confirmed_by_user?: boolean;
}

interface PendingConfirmation {
  proposal_id: string;
  tool_name: string;
  risk_level: 'read' | 'soft_write' | 'hard_write';
  rationale: string;
  arguments: Record<string, unknown>;
  expires_at: string | null;
}

interface ChatResponse {
  request_id: string;
  session_id: string;
  response: string;
  response_format?: string;
  pending_confirmation?: PendingConfirmation;
  audit_log?: AuditEntry[];
  tokens_used?: { prompt: number; completion: number };
  ts: string;
}

interface HealthStatus {
  status: string;
  version: string;
  ts: string;
}

interface ErrorEnvelope {
  code: string;
  message: string;
  request_id: string;
  ts: string;
}

interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
  pending?: PendingConfirmation;
}

// ---------------------------------------------------------------------------
// Risk badge
// ---------------------------------------------------------------------------

function RiskBadge({ level }: { level: string }): JSX.Element {
  const cls =
    level === 'hard_write'
      ? 'risk-badge risk-badge--hard'
      : level === 'soft_write'
        ? 'risk-badge risk-badge--soft'
        : 'risk-badge risk-badge--read';
  const label =
    level === 'hard_write' ? 'HIGH RISK' : level === 'soft_write' ? 'MEDIUM' : 'READ';
  return <span className={cls}>{label}</span>;
}

// ---------------------------------------------------------------------------
// Confirmation modal
// ---------------------------------------------------------------------------

function ConfirmationModal({
  pending,
  sessionId,
  onResolved,
}: {
  pending: PendingConfirmation;
  sessionId: string;
  onResolved: (response: ChatResponse) => void;
}): JSX.Element {
  const [loading, setLoading] = useState(false);

  async function handleDecision(accepted: boolean): Promise<void> {
    setLoading(true);
    try {
      const res = await fetch(`${API_URL}/api/v1/chat/confirm`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: sessionId,
          proposal_id: pending.proposal_id,
          accepted,
        }),
      });
      const data = (await res.json()) as ChatResponse & Partial<ErrorEnvelope>;
      if (!res.ok) {
        onResolved({
          request_id: data.request_id ?? '',
          session_id: sessionId,
          response: `${data.code ?? 'error'}: ${data.message ?? res.statusText}`,
          ts: new Date().toISOString(),
        });
        return;
      }
      onResolved(data as ChatResponse);
    } catch {
      onResolved({
        request_id: '',
        session_id: sessionId,
        response: 'Failed to reach backend. Please try again.',
        ts: new Date().toISOString(),
      });
    } finally {
      setLoading(false);
    }
  }

  const argEntries = Object.entries(pending.arguments ?? {}).map(([k, v]) => {
    const val = typeof v === 'string' && v.length > 80 ? v.slice(0, 80) + '…' : String(v);
    return { key: k, value: val };
  });

  return (
    <div className="modal-overlay" id="hitl-modal-overlay">
      <div className="modal" id="hitl-confirmation-modal">
        <div className="modal__header">
          <h2>⚠️ Confirmation Required</h2>
          <RiskBadge level={pending.risk_level} />
        </div>

        <div className="modal__body">
          <div className="modal__field">
            <span className="modal__label">Proposal ID</span>
            <code className="modal__value">{pending.proposal_id}</code>
          </div>

          <div className="modal__field">
            <span className="modal__label">Tool</span>
            <code className="modal__value">{pending.tool_name}</code>
          </div>

          {pending.rationale && (
            <div className="modal__field">
              <span className="modal__label">Rationale</span>
              <span className="modal__value">{pending.rationale}</span>
            </div>
          )}

          {argEntries.length > 0 && (
            <div className="modal__field">
              <span className="modal__label">Arguments</span>
              <div className="modal__args">
                {argEntries.map((a) => (
                  <div key={a.key} className="modal__arg-row">
                    <code>{a.key}</code>: <span>{a.value}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {pending.expires_at && (
            <div className="modal__field">
              <span className="modal__label">Expires</span>
              <span className="modal__value">
                {new Date(pending.expires_at).toLocaleTimeString()}
              </span>
            </div>
          )}
        </div>

        <div className="modal__actions">
          <button
            id="hitl-confirm-btn"
            type="button"
            className="btn btn--confirm"
            disabled={loading}
            onClick={() => void handleDecision(true)}
          >
            {loading ? 'Applying…' : '✓ Confirm'}
          </button>
          <button
            id="hitl-cancel-btn"
            type="button"
            className="btn btn--cancel"
            disabled={loading}
            onClick={() => void handleDecision(false)}
          >
            ✗ Cancel
          </button>
        </div>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// App
// ---------------------------------------------------------------------------

export function App(): JSX.Element {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');
  const [sending, setSending] = useState(false);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [pendingConfirmation, setPendingConfirmation] =
    useState<PendingConfirmation | null>(null);
  const [healthStatus, setHealthStatus] = useState<HealthStatus | null>(null);
  const [healthError, setHealthError] = useState<string | null>(null);
  const [chatError, setChatError] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  async function checkHealth(): Promise<void> {
    setHealthError(null);
    try {
      const response = await fetch(`${API_URL}/api/v1/healthz`);
      if (!response.ok) {
        throw new Error(`Backend returned ${response.status}`);
      }
      const data = (await response.json()) as HealthStatus;
      setHealthStatus(data);
    } catch (e) {
      setHealthError(e instanceof Error ? e.message : 'Unknown error');
      setHealthStatus(null);
    }
  }

  const sendMessage = useCallback(async () => {
    const text = input.trim();
    if (!text || sending) return;

    setSending(true);
    setChatError(null);
    setMessages((prev) => [...prev, { role: 'user', content: text }]);
    setInput('');

    try {
      const res = await fetch(`${API_URL}/api/v1/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: text,
          ...(sessionId ? { session_id: sessionId } : {}),
        }),
      });

      if (!res.ok) {
        let errText = `Request failed (${res.status})`;
        try {
          const envelope = (await res.json()) as ErrorEnvelope;
          errText = `${envelope.code}: ${envelope.message}`;
        } catch {
          /* ignore parse errors */
        }
        setChatError(errText);
        setMessages((prev) => [
          ...prev,
          { role: 'assistant', content: `Could not complete request: ${errText}` },
        ]);
        return;
      }

      const data = (await res.json()) as ChatResponse;
      setSessionId(data.session_id);

      const assistantMsg: ChatMessage = {
        role: 'assistant',
        content: data.response ?? '',
        ...(data.pending_confirmation ? { pending: data.pending_confirmation } : {}),
      };
      setMessages((prev) => [...prev, assistantMsg]);

      if (data.pending_confirmation) {
        setPendingConfirmation(data.pending_confirmation);
      } else {
        setPendingConfirmation(null);
      }
    } catch (e) {
      const msg = e instanceof Error ? e.message : 'Unknown error';
      setChatError(msg);
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: 'Failed to reach backend. Is the server running?',
        },
      ]);
    } finally {
      setSending(false);
    }
  }, [input, sending, sessionId]);

  const handleConfirmationResolved = useCallback((response: ChatResponse) => {
    setPendingConfirmation(null);
    setMessages((prev) => [...prev, { role: 'assistant', content: response.response ?? '' }]);
  }, []);

  return (
    <div className="app">
      <header className="app__header">
        <h1>openmetadata-mcp-agent</h1>
        <p>Conversational governance agent for OpenMetadata.</p>
      </header>

      <main className="app__main">
        <section className="app__status">
          <button type="button" onClick={() => void checkHealth()}>
            Check backend health
          </button>
          {healthStatus !== null && (
            <pre className="app__status-output">
              status: {healthStatus.status}
              {'\n'}version: {healthStatus.version}
              {'\n'}ts: {healthStatus.ts}
            </pre>
          )}
          {healthError !== null && (
            <p className="app__status-error">Backend not reachable: {healthError}</p>
          )}
        </section>

        <section className="app__chat">
          <div className="chat__messages" id="chat-messages">
            {messages.length === 0 && (
              <p className="chat__empty">Ask a question about your OpenMetadata catalog…</p>
            )}
            {messages.map((msg, i) => (
              <div key={i} className={`chat__bubble chat__bubble--${msg.role}`}>
                <span className="chat__role">{msg.role === 'user' ? 'You' : 'Agent'}</span>
                <div className="chat__content">{msg.content}</div>
                {msg.pending && (
                  <div className="chat__pending-hint">
                    ⚠️ Write operation pending — see confirmation dialog above.
                  </div>
                )}
              </div>
            ))}
            <div ref={messagesEndRef} />
          </div>

          <div className="chat__input-row">
            <textarea
              id="chat-input"
              className="app__chat-input"
              placeholder="Type a query…"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault();
                  void sendMessage();
                }
              }}
              rows={2}
            />
            <button
              id="chat-send-btn"
              type="button"
              className="app__chat-send"
              disabled={sending || !input.trim()}
              onClick={() => void sendMessage()}
            >
              {sending ? 'Sending…' : 'Send'}
            </button>
          </div>
          {chatError !== null && <p className="app__chat-error">{chatError}</p>}
          {sessionId !== null && (
            <p className="app__chat-session" data-testid="session-id">
              session_id: {sessionId}
            </p>
          )}
        </section>
      </main>

      {pendingConfirmation !== null && sessionId !== null && (
        <ConfirmationModal
          pending={pendingConfirmation}
          sessionId={sessionId}
          onResolved={handleConfirmationResolved}
        />
      )}

      <footer className="app__footer">
        <p>
          Phase 2 | Apache 2.0 |{' '}
          <a href="https://github.com/GunaPalanivel/openmetadata-mcp-agent">repo</a>
        </p>
      </footer>
    </div>
  );
}
