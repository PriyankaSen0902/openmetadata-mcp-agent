/*
 *  Copyright 2026 Collate Inc.
 *  Licensed under the Apache License, Version 2.0 (the "License"); you may
 *  not use this file except in compliance with the License. You may obtain
 *  a copy of the License at
 *
 *  http://www.apache.org/licenses/LICENSE-2.0
 */

import { useState } from 'react';

const API_URL = import.meta.env['VITE_API_URL'] ?? 'http://localhost:8000';

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

interface PendingConfirmation {
  summary?: string;
}

interface ChatResponse {
  request_id: string;
  session_id: string;
  response: string;
  pending_confirmation?: PendingConfirmation;
}

interface ChatEntry {
  role: 'user' | 'assistant';
  text: string;
}

export function App(): JSX.Element {
  const [message, setMessage] = useState('');
  const [healthStatus, setHealthStatus] = useState<HealthStatus | null>(null);
  const [healthError, setHealthError] = useState<string | null>(null);
  const [chatError, setChatError] = useState<string | null>(null);
  const [chatEntries, setChatEntries] = useState<ChatEntry[]>([]);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [isSending, setIsSending] = useState(false);

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

  async function sendMessage(): Promise<void> {
    const trimmedMessage = message.trim();
    if (!trimmedMessage || isSending) {
      return;
    }

    setIsSending(true);
    setChatError(null);
    setChatEntries((previous) => [...previous, { role: 'user', text: trimmedMessage }]);
    setMessage('');

    try {
      const payload: { message: string; session_id?: string } = { message: trimmedMessage };
      if (sessionId) {
        payload.session_id = sessionId;
      }

      const response = await fetch(`${API_URL}/api/v1/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        let envelope: ErrorEnvelope | null = null;
        try {
          envelope = (await response.json()) as ErrorEnvelope;
        } catch {
          envelope = null;
        }

        if (envelope) {
          setChatError(`${envelope.code}: ${envelope.message}`);
        } else {
          setChatError(`Request failed with status ${response.status}`);
        }
        return;
      }

      const data = (await response.json()) as ChatResponse;
      setSessionId(data.session_id);
      const assistantText =
        data.pending_confirmation?.summary !== undefined
          ? `${data.response}\n\nPending confirmation: ${data.pending_confirmation.summary}`
          : data.response;
      setChatEntries((previous) => [
        ...previous,
        { role: 'assistant', text: assistantText || 'No response body returned by backend.' },
      ]);
    } catch (e) {
      setChatError(e instanceof Error ? e.message : 'Unknown error');
    } finally {
      setIsSending(false);
    }
  }

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
          <p className="app__chat-placeholder">Send a message to `POST /api/v1/chat`.</p>

          {sessionId !== null && <p className="app__chat-session">session_id: {sessionId}</p>}

          <div className="app__chat-log" aria-live="polite">
            {chatEntries.length === 0 && (
              <p className="app__chat-empty">No messages yet. Try asking for metadata insights.</p>
            )}
            {chatEntries.map((entry, index) => (
              <article
                key={`${entry.role}-${index}`}
                className={`app__chat-message app__chat-message--${entry.role}`}
              >
                <p className="app__chat-message-role">{entry.role}</p>
                <pre className="app__chat-message-text">{entry.text}</pre>
              </article>
            ))}
            {isSending && <p className="app__chat-loading">Sending...</p>}
          </div>

          <textarea
            className="app__chat-input"
            placeholder="Type a query..."
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            rows={3}
          />
          <button
            type="button"
            className="app__chat-send"
            onClick={() => void sendMessage()}
            disabled={isSending || message.trim().length === 0}
          >
            {isSending ? 'Sending...' : 'Send'}
          </button>
          {chatError !== null && <p className="app__chat-error">{chatError}</p>}
        </section>
      </main>

      <footer className="app__footer">
        <p>
          Phase 1 scaffold | Apache 2.0 |{' '}
          <a href="https://github.com/GunaPalanivel/openmetadata-mcp-agent">repo</a>
        </p>
      </footer>
    </div>
  );
}
