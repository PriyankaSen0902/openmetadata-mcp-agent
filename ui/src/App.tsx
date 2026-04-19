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

export function App(): JSX.Element {
  const [message, setMessage] = useState('');
  const [healthStatus, setHealthStatus] = useState<HealthStatus | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function checkHealth(): Promise<void> {
    setError(null);
    try {
      const response = await fetch(`${API_URL}/api/v1/healthz`);
      if (!response.ok) {
        throw new Error(`Backend returned ${response.status}`);
      }
      const data = (await response.json()) as HealthStatus;
      setHealthStatus(data);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Unknown error');
      setHealthStatus(null);
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
          {error !== null && (
            <p className="app__status-error">Backend not reachable: {error}</p>
          )}
        </section>

        <section className="app__chat">
          <p className="app__chat-placeholder">
            Chat scaffold. Real wiring lands in P1-04 (LangGraph agent +{' '}
            <code>data-ai-sdk</code> MCP client). For now, this proves the build pipeline,
            CSS tokens, and Vite dev server work.
          </p>

          <textarea
            className="app__chat-input"
            placeholder="Type a query (Phase 2 will wire this to /api/v1/chat) ..."
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            rows={3}
          />
          <button type="button" disabled className="app__chat-send">
            Send (disabled until P1-04)
          </button>
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
