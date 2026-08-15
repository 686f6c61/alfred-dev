#!/usr/bin/env python3
"""Servidor local de la UI de memoria de Alfred Dev."""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Dict, List, Optional
from urllib.parse import parse_qs, urlparse

if __package__ in {None, ""}:
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.memory import MemoryDB


UI_VERSION = "0.0.4"
_LOOPBACK_HOSTS = frozenset({"127.0.0.1", "::1", "localhost"})

_EVENT_TYPE_LABELS = {
    "session_started": "Sesión",
    "session_ended": "Sesión",
    "user_prompt": "Prompt",
    "phase_completed": "Fase",
    "gate_passed": "Gate",
    "command_executed": "Comando",
    "alfred_prefetched": "Prefetch",
    "helper_seeded": "Helper",
    "file_written": "Archivo",
    "commit_captured": "Commit",
}

HTML_TEMPLATE = """<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Alfred Dev Memory UI</title>
  <style>
    :root {
      color-scheme: dark;
      --bg: #081018;
      --panel: rgba(14, 24, 36, 0.92);
      --panel-2: rgba(10, 18, 28, 0.88);
      --border: rgba(146, 176, 209, 0.18);
      --text: #f4f7fb;
      --muted: #9db1c7;
      --accent: #54c4ff;
      --accent-2: #7df5d3;
      --warn: #ffcb6b;
      --danger: #ff7a90;
      --ok: #7ce38b;
      --shadow: 0 20px 60px rgba(0, 0, 0, 0.35);
      --radius: 18px;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      font-family: ui-sans-serif, -apple-system, BlinkMacSystemFont, "Segoe UI",
        sans-serif;
      background:
        radial-gradient(circle at top left, rgba(84, 196, 255, 0.14), transparent 32%),
        radial-gradient(circle at top right, rgba(125, 245, 211, 0.10), transparent 30%),
        linear-gradient(180deg, #081018 0%, #0c1621 100%);
      color: var(--text);
      min-height: 100vh;
    }
    a { color: var(--accent); }
    .app {
      max-width: 1520px;
      margin: 0 auto;
      padding: 28px 24px 72px;
    }
    .hero {
      display: flex;
      gap: 20px;
      justify-content: space-between;
      align-items: flex-start;
      flex-wrap: wrap;
      margin-bottom: 26px;
    }
    .hero-copy {
      flex: 1 1 720px;
      min-width: 0;
    }
    .hero-copy h1 {
      margin: 0 0 10px;
      font-size: clamp(2rem, 4vw, 3.4rem);
      line-height: 1;
      letter-spacing: -0.04em;
    }
    .hero-copy p {
      margin: 0;
      max-width: 72ch;
      color: var(--muted);
      line-height: 1.55;
    }
    .hero-meta {
      flex: 0 1 560px;
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 12px;
      min-width: min(100%, 420px);
      width: min(100%, 520px);
      padding: 18px;
      background: var(--panel);
      border: 1px solid var(--border);
      border-radius: var(--radius);
      box-shadow: var(--shadow);
    }
    .hero-meta > div {
      min-width: 0;
      padding: 12px 14px;
      border-radius: 14px;
      background: rgba(7, 13, 22, 0.64);
      border: 1px solid rgba(146, 176, 209, 0.12);
    }
    .hero-meta strong {
      display: block;
      font-size: 0.82rem;
      text-transform: uppercase;
      letter-spacing: 0.08em;
      color: var(--muted);
      margin-bottom: 3px;
    }
    .hero-meta .hero-meta-value {
      display: block;
      font-size: 0.96rem;
      word-break: normal;
      overflow-wrap: anywhere;
    }
    .hero-meta-inline {
      display: inline-flex;
      align-items: baseline;
      gap: 0.28rem;
      flex-wrap: nowrap;
      white-space: nowrap;
    }
    .hero-meta-inline #refreshSeconds {
      font-variant-numeric: tabular-nums;
      font-weight: 700;
    }
    .hero-version {
      display: inline-flex;
      align-items: center;
      gap: 10px;
      margin-top: 12px;
      flex-wrap: wrap;
    }
    .hero-links {
      display: flex;
      gap: 10px;
      flex-wrap: wrap;
      margin-top: 14px;
    }
    .hero-links a {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      padding: 8px 12px;
      border-radius: 999px;
      border: 1px solid var(--border);
      background: rgba(7, 13, 22, 0.82);
      color: var(--text);
      text-decoration: none;
      font-size: 0.9rem;
    }
    .hero-links a:hover {
      border-color: rgba(84, 196, 255, 0.45);
      color: var(--accent);
    }
    .toolbar {
      display: flex;
      gap: 10px;
      align-items: center;
      flex-wrap: wrap;
      margin: 0 0 22px;
    }
    .toolbar input,
    .toolbar select,
    .toolbar button {
      border: 1px solid var(--border);
      background: rgba(7, 13, 22, 0.82);
      color: var(--text);
      border-radius: 999px;
      padding: 11px 14px;
      font-size: 0.95rem;
    }
    .toolbar input { min-width: 280px; }
    .toolbar button {
      cursor: pointer;
      background: linear-gradient(135deg, rgba(84, 196, 255, 0.22), rgba(125, 245, 211, 0.14));
    }
    .toolbar button:hover { border-color: rgba(84, 196, 255, 0.45); }
    .status-chip {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      padding: 10px 14px;
      border-radius: 999px;
      border: 1px solid var(--border);
      background: rgba(5, 12, 19, 0.82);
      color: var(--muted);
      font-size: 0.9rem;
    }
    .status-dot {
      width: 9px;
      height: 9px;
      border-radius: 999px;
      background: var(--ok);
      box-shadow: 0 0 0 5px rgba(124, 227, 139, 0.12);
    }
    .notice-banner {
      margin: 0 0 18px;
      padding: 14px 16px;
      border-radius: 16px;
      border: 1px solid rgba(255, 203, 107, 0.22);
      background: rgba(255, 203, 107, 0.08);
      color: #ffe7b2;
      line-height: 1.55;
    }
    .notice-banner strong {
      display: block;
      margin-bottom: 4px;
      color: #fff3cf;
    }
    .grid {
      display: grid;
      grid-template-columns: repeat(12, minmax(0, 1fr));
      gap: 18px;
    }
    .panel {
      grid-column: span 12;
      background: var(--panel);
      border: 1px solid var(--border);
      border-radius: var(--radius);
      padding: 18px;
      box-shadow: var(--shadow);
      min-height: 100%;
    }
    .panel[data-span="4"] { grid-column: span 4; }
    .panel[data-span="5"] { grid-column: span 5; }
    .panel[data-span="6"] { grid-column: span 6; }
    .panel[data-span="7"] { grid-column: span 7; }
    .panel[data-span="8"] { grid-column: span 8; }
    .panel[data-span="12"] { grid-column: span 12; }
    .panel h2 {
      margin: 0 0 12px;
      font-size: 1.1rem;
      letter-spacing: -0.02em;
    }
    .subtle {
      color: var(--muted);
      margin: 0 0 14px;
      line-height: 1.5;
    }
    .stats {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
      gap: 12px;
    }
    .stat-card {
      border: 1px solid var(--border);
      border-radius: 16px;
      padding: 14px;
      background: var(--panel-2);
    }
    .stat-card strong {
      display: block;
      font-size: 0.78rem;
      text-transform: uppercase;
      letter-spacing: 0.08em;
      color: var(--muted);
      margin-bottom: 6px;
    }
    .stat-card span {
      display: block;
      font-size: 1.7rem;
      font-weight: 700;
      letter-spacing: -0.04em;
      overflow-wrap: anywhere;
    }
    .stat-card span.is-textual {
      font-size: 1.02rem;
      line-height: 1.3;
      letter-spacing: 0.02em;
      text-transform: uppercase;
    }
    .meta-list,
    .stack-list,
    .session-list,
    .activity-list,
    .search-results,
    .timeline,
    .decision-list,
    .commit-list {
      display: grid;
      gap: 12px;
      margin: 0;
      padding: 0;
      list-style: none;
    }
    .meta-list li,
    .session-list li,
    .activity-list li,
    .search-results li,
    .timeline li,
    .decision-list li,
    .commit-list li {
      border: 1px solid var(--border);
      border-radius: 16px;
      padding: 14px;
      background: var(--panel-2);
    }
    .lane-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
      gap: 12px;
    }
    .lane-card {
      border: 1px solid var(--border);
      border-radius: 16px;
      padding: 14px;
      background: var(--panel-2);
    }
    .hint-card {
      border: 1px dashed var(--border);
      border-radius: 16px;
      padding: 16px;
      background: rgba(6, 11, 18, 0.5);
      color: var(--muted);
      line-height: 1.6;
    }
    .lane-card h3 {
      margin: 0 0 8px;
      font-size: 0.95rem;
    }
    .lane-card ul {
      list-style: none;
      padding: 0;
      margin: 0;
      display: grid;
      gap: 8px;
      color: var(--muted);
    }
    .timeline small,
    .session-list small,
    .activity-list small,
    .commit-list small,
    .decision-list small,
    .search-results small {
      display: block;
      color: var(--muted);
      margin-bottom: 6px;
    }
    .decision-title,
    .commit-title,
    .search-title {
      font-size: 1rem;
      font-weight: 700;
      margin-bottom: 8px;
    }
    .decision-body,
    .commit-body,
    .event-body {
      color: var(--muted);
      line-height: 1.55;
      white-space: pre-wrap;
    }
    details.event-details {
      margin-top: 10px;
    }
    details.event-details summary {
      cursor: pointer;
      color: var(--accent);
      font-size: 0.88rem;
      user-select: none;
    }
    details.event-details ul {
      list-style: none;
      margin: 10px 0 0;
      padding: 0;
      display: grid;
      gap: 6px;
      color: var(--muted);
    }
    .chip-row {
      display: flex;
      gap: 8px;
      flex-wrap: wrap;
      margin: 10px 0 0;
    }
    .chip {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      border-radius: 999px;
      padding: 6px 10px;
      font-size: 0.85rem;
      border: 1px solid transparent;
      background: rgba(84, 196, 255, 0.12);
      color: #d4efff;
    }
    .chip.ok { background: rgba(124, 227, 139, 0.14); color: #d7ffd8; }
    .chip.warn { background: rgba(255, 203, 107, 0.14); color: #ffe7b2; }
    .chip.danger { background: rgba(255, 122, 144, 0.14); color: #ffd0d8; }
    .kv {
      display: grid;
      gap: 6px;
    }
    .kv strong {
      color: var(--muted);
      font-size: 0.78rem;
      text-transform: uppercase;
      letter-spacing: 0.08em;
    }
    .graph-shell {
      border: 1px solid var(--border);
      border-radius: 16px;
      background: rgba(4, 10, 16, 0.8);
      overflow: hidden;
    }
    #graph {
      width: 100%;
      height: 420px;
      display: block;
    }
    .legend {
      display: flex;
      gap: 10px;
      flex-wrap: wrap;
      padding: 12px 14px 0;
      color: var(--muted);
      font-size: 0.84rem;
    }
    .legend span {
      display: inline-flex;
      align-items: center;
      gap: 6px;
    }
    .legend i {
      width: 10px;
      height: 10px;
      border-radius: 999px;
      display: inline-block;
    }
    .empty {
      border: 1px dashed var(--border);
      border-radius: 16px;
      padding: 18px;
      color: var(--muted);
      background: rgba(6, 11, 18, 0.5);
    }
    .is-hidden {
      display: none !important;
    }
    code {
      background: rgba(255, 255, 255, 0.06);
      padding: 0.15rem 0.35rem;
      border-radius: 6px;
      font-family: ui-monospace, "SFMono-Regular", Menlo, monospace;
    }
    @media (max-width: 1100px) {
      .panel[data-span] { grid-column: span 12; }
      #graph { height: 360px; }
      .hero-meta {
        width: 100%;
      }
    }
    @media (max-width: 900px) {
      .hero-meta {
        grid-template-columns: 1fr;
        min-width: 0;
      }
    }
  </style>
</head>
<body>
  <div class="app">
    <section class="hero">
      <div class="hero-copy">
        <h1>Memory UI</h1>
        <p>
          Vista viva de la memoria SQLite de Alfred: timeline, decisiones, grafo,
          commits, búsqueda, salud del almacén y estado operativo del proyecto.
        </p>
        <div class="hero-version">
          <span class="chip ok" id="pluginBadge">Alfred Dev</span>
          <span class="chip" id="pluginVersion">Plugin —</span>
          <span class="chip" id="uiVersion">Memory UI —</span>
        </div>
        <div class="hero-links">
          <a href="https://alfred-dev.com/" target="_blank" rel="noopener noreferrer">Web</a>
          <a href="https://github.com/686f6c61/alfred-dev#readme" target="_blank" rel="noopener noreferrer">README</a>
          <a href="https://github.com/686f6c61/alfred-dev/tree/main/docs" target="_blank" rel="noopener noreferrer">Docs</a>
        </div>
      </div>
      <div class="hero-meta">
        <div><strong>Proyecto</strong><span class="hero-meta-value" id="projectName">Cargando…</span></div>
        <div><strong>SQLite</strong><span class="hero-meta-value" id="dbPath">—</span></div>
        <div><strong>Refresco</strong><span class="hero-meta-value hero-meta-inline">Automático cada <span id="refreshSeconds">4</span><span>s</span></span></div>
      </div>
    </section>

    <div class="toolbar">
      <form id="searchForm">
        <input id="searchInput" type="search" placeholder="Buscar en decisiones, commits, eventos y docs/project/" />
      </form>
      <select id="iterationSelect"></select>
      <button type="button" id="refreshButton">Actualizar ahora</button>
      <span class="status-chip"><span class="status-dot"></span><span id="lastRefresh">Conectando…</span></span>
    </div>
    <div id="workspaceNotice" class="notice-banner is-hidden"></div>

    <section class="grid">
      <article class="panel" data-span="12">
        <h2>Resumen</h2>
        <p class="subtle">Lo más importante del proyecto y del estado operativo en una sola vista.</p>
        <div class="stats" id="stats"></div>
      </article>

      <article class="panel" data-span="5">
        <h2>Estado actual</h2>
        <ul class="meta-list" id="stateSummary"></ul>
      </article>

      <article class="panel" data-span="7">
        <h2>Cronología</h2>
        <p class="subtle" id="timelineMeta">Eventos de la iteración seleccionada.</p>
        <ul class="timeline" id="timeline"></ul>
      </article>

      <article class="panel" data-span="12" id="projectSignalsPanel">
        <h2>Foco operativo</h2>
        <p class="subtle">Bloqueos, trabajo en curso, trazabilidad y señales útiles de SonIA sin repetir la cabecera.</p>
        <div class="lane-grid" id="projectSignals"></div>
      </article>

      <article class="panel" data-span="7">
        <h2>Sesiones recientes</h2>
        <p class="subtle">Iteraciones reales de Alfred con su contexto y volumen de actividad.</p>
        <ul class="session-list" id="sessions"></ul>
      </article>

      <article class="panel" data-span="5">
        <h2>Actividad reciente</h2>
        <p class="subtle">Eventos y prompts recientes, útiles incluso si todavía no hay ADRs ni commits enlazados.</p>
        <div class="chip-row" id="activityMix" style="margin-bottom:10px;"></div>
        <ul class="activity-list" id="activity"></ul>
      </article>

      <article class="panel" data-span="7" id="decisionsPanel">
        <h2>Decisiones</h2>
        <p class="subtle">Diseño, seguridad, cumplimiento y decisiones de implementación con sus relaciones visibles.</p>
        <ul class="decision-list" id="decisions"></ul>
      </article>

      <article class="panel" data-span="5" id="graphPanel">
        <h2>Grafo de decisiones</h2>
        <div class="legend">
          <span><i style="background:#54c4ff"></i> activa</span>
          <span><i style="background:#ffcb6b"></i> reemplazada</span>
          <span><i style="background:#ff7a90"></i> obsoleta</span>
        </div>
        <div class="graph-shell">
          <svg id="graph" viewBox="0 0 800 420" preserveAspectRatio="xMidYMid meet"></svg>
        </div>
        <div id="graphDetail" class="empty" style="margin-top:12px;">Haz clic en una decisión del grafo para ver el detalle.</div>
      </article>

      <article class="panel" data-span="6" id="commitsPanel">
        <h2>Commits</h2>
        <p class="subtle">Actividad reciente conectada con la memoria del proyecto.</p>
        <ul class="commit-list" id="commits"></ul>
      </article>

      <article class="panel" data-span="6" id="searchPanel">
        <h2>Búsqueda</h2>
        <p class="subtle">Cruza memoria SQLite y artefactos operativos de SonIA.</p>
        <ul class="search-results" id="searchResults">
          <li class="hint-card">
            <strong>Escribe algo para buscar en memoria y artefactos.</strong><br />
            Cuando haya memoria, busca por una decisión, un commit o un término de <code>docs/project/</code>.
          </li>
        </ul>
      </article>
    </section>
  </div>

  <script>
    const refreshEveryMs = 8000;
    const state = {
      selectedIterationId: null,
      selectedGraphNodeId: null,
      graph: { nodes: [], edges: [] },
    };

    function esc(text) {
      return String(text ?? "")
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#39;");
    }

    function formatDate(value) {
      if (!value) return "—";
      const date = new Date(value);
      if (Number.isNaN(date.getTime())) return value;
      return new Intl.DateTimeFormat("es-ES", {
        dateStyle: "short",
        timeStyle: "medium",
        hour12: false,
      }).format(date);
    }

    const STATUS_LABELS = Object.freeze({
      accepted: "aceptada",
      active: "activa",
      approved: "aprobada",
      blocked: "bloqueada",
      danger: "crítica",
      done: "completada",
      healthy: "saludable",
      inactive: "inactiva",
      pending: "pendiente",
      proposed: "propuesta",
      rejected: "rechazada",
      superseded: "reemplazada",
      deprecated: "obsoleta",
      unknown: "sin estado",
      warning: "aviso",
    });

    const URGENCY_META = Object.freeze({
      alta: { label: "prioridad alta", className: "danger" },
      media: { label: "prioridad media", className: "warn" },
      baja: { label: "prioridad baja", className: "" },
    });

    function statusLabel(status, { uppercase = false } = {}) {
      const raw = String(status || "unknown");
      const translated = STATUS_LABELS[raw.toLowerCase()] || raw;
      return esc(uppercase ? translated.toUpperCase() : translated);
    }

    function statusChip(status) {
      const raw = String(status || "unknown");
      const value = statusLabel(raw);
      const kind = /accepted|done|active|healthy|approved/.test(raw)
        ? "ok"
        : /warning|pending|proposed/.test(raw)
          ? "warn"
          : /error|rejected|superseded|blocked|deprecated/.test(raw)
            ? "danger"
            : "";
      return `<span class="chip ${kind}">${value}</span>`;
    }

    function urgencyChip(urgency) {
      const meta = URGENCY_META[String(urgency || "").toLowerCase()] || null;
      if (!meta) return "";
      return `<span class="chip ${meta.className}">${esc(meta.label)}</span>`;
    }

    async function fetchJson(path) {
      const response = await fetch(path, { cache: "no-store" });
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      return await response.json();
    }

    function renderEmpty(targetId, message) {
      document.getElementById(targetId).innerHTML = `<li class="empty">${message}</li>`;
    }

    function togglePanel(panelId, visible) {
      const element = document.getElementById(panelId);
      if (!element) return;
      element.classList.toggle("is-hidden", !visible);
    }

    function setPanelSpan(panelId, span) {
      const element = document.getElementById(panelId);
      if (!element) return;
      element.setAttribute("data-span", String(span));
    }

    function renderStats(data) {
      const stats = data.stats || {};
      const health = data.health || {};
      const progress = data.progress || {};
      const kanban = progress.kanban || {};
      const cards = [
        { label: "Iteraciones", value: stats.total_iterations ?? 0 },
        { label: "Decisiones", value: stats.total_decisions ?? 0 },
        { label: "Commits", value: stats.total_commits ?? 0 },
        { label: "Eventos", value: stats.total_events ?? 0 },
        { label: "Pendientes", value: (kanban.backlog || []).length },
        { label: "En curso", value: (kanban.in_progress || []).length },
        { label: "Bloqueadas", value: (kanban.blocked || []).length },
        {
          label: "Salud",
          value: statusLabel(health.status || "unknown", { uppercase: true }),
          kind: "text",
        },
      ];
      document.getElementById("stats").innerHTML = cards.map(({ label, value, kind = "metric" }) => `
        <div class="stat-card" data-kind="${kind}">
          <strong>${label}</strong>
          <span class="${kind === "text" ? "is-textual" : ""}">${value}</span>
        </div>
      `).join("");
    }

    function renderWorkspaceNotice(data) {
      const element = document.getElementById("workspaceNotice");
      const stats = data.stats || {};
      const workspace = data.workspace || {};
      const totalSignals = Number(stats.total_iterations || 0)
        + Number(stats.total_decisions || 0)
        + Number(stats.total_commits || 0)
        + Number(workspace.meaningful_event_count || 0);
      if (workspace.has_meaningful_memory || totalSignals > 0) {
        element.classList.add("is-hidden");
        element.innerHTML = "";
        return;
      }

      element.innerHTML = `
        <strong>No hay memoria de Alfred en este proyecto.</strong>
        Aquí solo aparece lo que Alfred ha registrado: sesiones, decisiones, eventos y commits enlazados. El historial de Git no se importa al abrir la UI.
      `;
      element.classList.remove("is-hidden");
    }

    function renderOverview(data) {
      document.getElementById("pluginBadge").textContent = data.plugin_name || "Alfred Dev";
      document.getElementById("pluginVersion").textContent = `Plugin ${data.plugin_version || "—"}`;
      document.getElementById("uiVersion").textContent = `Memory UI ${data.ui_version || "—"}`;
      document.getElementById("projectName").textContent = data.project_name || "Proyecto";
      document.getElementById("dbPath").textContent = data.db_path || "—";
      document.getElementById("lastRefresh").textContent = `Última actualización: ${formatDate(data.refreshed_at)}`;
      renderStats(data);
      renderWorkspaceNotice(data);

      const memoryEmpty = data.memory_empty === true
        || (
          !Number((data.stats || {}).total_iterations || 0)
          && !Number((data.stats || {}).total_decisions || 0)
          && !Number((data.stats || {}).total_commits || 0)
          && !Number((data.stats || {}).total_events || 0)
        );
      const progress = memoryEmpty ? {} : (data.progress || {});
      const nextAction = progress.next_action || {};
      const overviewCards = (progress.overview_cards || []).filter(
        (card) => card.label !== "Siguiente paso recomendado"
      );
      const health = data.health || {};
      const issues = health.issues || [];
      const lines = [];

      if (!memoryEmpty && nextAction.command) {
        lines.push(`
          <li>
            <small>Acción inmediata</small>
            <div class="decision-title">/alfred-dev:${esc(nextAction.command || "alfred")}</div>
            <div class="chip-row">
              ${urgencyChip(nextAction.urgency)}
              ${nextAction.source_label ? `<span class="chip">${esc(nextAction.source_label)}</span>` : ""}
            </div>
            <div class="event-body">${esc(nextAction.focus || "Siguiente paso recomendado")}</div>
            <div class="event-body" style="margin-top:8px;">${esc(nextAction.directive || nextAction.reason || "Sin detalle adicional.")}</div>
            ${
              nextAction.reason && nextAction.directive && nextAction.reason !== nextAction.directive
                ? `<div class="subtle" style="margin-top:8px;">${esc(nextAction.reason)}</div>`
                : ""
            }
          </li>
        `);
      }

      lines.push(...overviewCards.map((card) => `
        <li>
          <small>${esc(card.label || "Estado")}</small>
          <div class="decision-title">${esc(card.title || "sin detalle")}</div>
          ${card.chips && card.chips.length ? `<div class="chip-row">${card.chips.map((chip) => statusChip(chip)).join("")}</div>` : ""}
          <div class="event-body">${esc(card.body || "")}</div>
        </li>
      `));

      lines.push(`
        <li>
          <small>Salud de memoria</small>
          <div class="chip-row">${statusChip(health.status || "unknown")}</div>
          <div class="event-body">${issues.length ? issues.map((issue) => esc(issue)).join("\\n") : "Sin incidencias detectadas."}</div>
        </li>
      `);

      document.getElementById("stateSummary").innerHTML = lines.join("");
    }

    function renderSessions(data) {
      const items = data.items || [];
      if (!items.length) {
        renderEmpty("sessions", "Todavía no hay sesiones registradas.");
        return;
      }
      document.getElementById("sessions").innerHTML = items.map((item) => `
        <li>
          <small>Iteración #${item.id} · ${formatDate(item.started_at)}</small>
          <div class="decision-title">${esc(item.command || "session")} — ${esc(item.description || "sin descripción")}</div>
          <div class="chip-row">
            ${statusChip(item.status || "unknown")}
            <span class="chip">${esc(item.event_count || 0)} eventos</span>
            ${item.is_active ? '<span class="chip ok">activa</span>' : ''}
          </div>
          <div class="event-body">${item.last_title ? esc(item.last_title) : "Sin resumen reciente; la actividad puede venir solo por hooks básicos."}</div>
          ${item.last_body ? `<div class="event-body" style="margin-top:8px;">${esc(item.last_body)}</div>` : ""}
        </li>
      `).join("");
    }

    function renderActivity(data) {
      const items = data.recent_events || [];
      const counts = data.event_counts || [];
      const mix = document.getElementById("activityMix");
      mix.innerHTML = counts.length
        ? counts.map((item) => `<span class="chip">${esc(item.label || item.event_type || "evento")} · ${esc(item.total || 0)}</span>`).join("")
        : "";
      if (!items.length) {
        renderEmpty("activity", "Todavía no hay actividad reciente en la memoria.");
        return;
      }
      document.getElementById("activity").innerHTML = items.map((item) => `
        <li>
          <small>${formatDate(item.created_at)} · iteración #${esc(item.iteration_id || "—")}</small>
          <div class="decision-title">${esc(item.display_title || item.summary || item.event_type || "Evento")}</div>
          <div class="chip-row">
            ${statusChip(item.kind_label || item.event_type || "event")}
            ${item.status_label ? statusChip(item.status_label) : ""}
            ${item.phase_label ? statusChip(item.phase_label) : ""}
          </div>
          <div class="event-body">${esc(item.display_body || "Sin detalle adicional.")}</div>
          ${
            item.detail_lines && item.detail_lines.length
              ? `<details class="event-details"><summary>Ver detalle</summary><ul>${item.detail_lines.map((line) => `<li>${esc(line)}</li>`).join("")}</ul></details>`
              : ""
          }
        </li>
      `).join("");
    }

    function renderProjectSignals(data) {
      if (data.memory_empty === true) {
        togglePanel("projectSignalsPanel", false);
        return;
      }
      const progress = data.progress || {};
      const kanban = progress.kanban || {};
      const cards = (progress.project_signal_cards && progress.project_signal_cards.length)
        ? progress.project_signal_cards
        : [
            {
              title: "Current",
              subtitle: "Lo último que Alfred ha dejado listo para seguir.",
              items: progress.current_signals || [],
            },
            {
              title: "Bloqueos",
              subtitle: "Lo que ahora mismo impide avanzar o cerrar trabajo.",
              items: kanban.blocked || [],
            },
            {
              title: "En curso",
              subtitle: "Trabajo en marcha ahora mismo.",
              items: kanban.in_progress || [],
            },
            {
              title: "Progreso",
              subtitle: "Señales humanas del avance del proyecto.",
              items: progress.progress_signals || [],
            },
            {
              title: "Trazabilidad",
              subtitle: "Huecos o señales de criterios y cobertura.",
              items: progress.traceability_signals || [],
            },
            {
              title: "Backlog",
              subtitle: "Pendiente por atacar.",
              items: kanban.backlog || [],
            },
          ].filter((card) => card.items && card.items.length);
      const hasAnySignal = cards.some((card) => card.items && card.items.length);
      if (!hasAnySignal) {
        togglePanel("projectSignalsPanel", false);
        return;
      }
      togglePanel("projectSignalsPanel", true);
      document.getElementById("projectSignals").innerHTML = cards.map((card) => `
        <div class="lane-card">
          <h3>${esc(card.title || "Señales")}</h3>
          <div class="subtle" style="margin-bottom:10px;">${esc(card.subtitle || "")}</div>
          <ul>
            ${
              (card.items && card.items.length)
                ? card.items.slice(0, 4).map((item) => `<li>${esc(item)}</li>`).join("")
                : '<li>Sin datos todavía en este proyecto.</li>'
            }
          </ul>
        </div>
      `).join("");
    }

    function renderIterations(items) {
      const select = document.getElementById("iterationSelect");
      if (!items.length) {
        state.selectedIterationId = null;
        select.innerHTML = `<option value="">Sin iteraciones</option>`;
        return;
      }
      const selectedStillExists = items.some(
        (item) => String(item.id) === state.selectedIterationId
      );
      if (!state.selectedIterationId || !selectedStillExists) {
        const preferred = items.find((item) => item.is_active) || items[0];
        state.selectedIterationId = String(preferred.id);
      }
      select.innerHTML = items.map((item) => `
        <option value="${item.id}" ${String(item.id) === state.selectedIterationId ? "selected" : ""}>
          #${item.id} · ${esc(item.command || "session")} · ${statusLabel(item.status || "unknown")}
        </option>
      `).join("");
    }

    function renderTimeline(data) {
      const items = data.events || [];
      const iteration = data.iteration || {};
      const totalEvents = Number(data.event_count || items.length || 0);
      const returnedCount = Number(data.returned_count || items.length || 0);
      const timelineCountLabel = data.truncated
        ? `${returnedCount} de ${totalEvents} eventos`
        : `${totalEvents} eventos`;
      document.getElementById("timelineMeta").textContent = iteration.id
        ? `Iteración #${iteration.id} · ${iteration.command || "session"} · ${statusLabel(iteration.status || "unknown")} · ${timelineCountLabel}`
        : "No hay iteraciones con eventos todavía.";
      if (!items.length) {
        renderEmpty("timeline", "Todavía no hay eventos en esta iteración.");
        return;
      }
      document.getElementById("timeline").innerHTML = items.map((event) => `
        <li>
          <small>${formatDate(event.created_at)}</small>
          <div class="decision-title">${esc(event.display_title || event.summary || event.event_type || "Evento")}</div>
          <div class="chip-row">
            ${statusChip(event.kind_label || event.event_type || "evento")}
            ${event.status_label ? statusChip(event.status_label) : ""}
            ${event.phase_label ? statusChip(event.phase_label) : ""}
          </div>
          <div class="event-body">${esc(event.display_body || "Sin detalle adicional.")}</div>
          ${
            event.detail_lines && event.detail_lines.length
              ? `<details class="event-details"><summary>Ver detalle</summary><ul>${event.detail_lines.map((line) => `<li>${esc(line)}</li>`).join("")}</ul></details>`
              : ""
          }
        </li>
      `).join("");
    }

    function renderDecisions(data) {
      const items = data.items || [];
      if (!items.length) {
        togglePanel("decisionsPanel", false);
        return;
      }
      togglePanel("decisionsPanel", true);
      document.getElementById("decisions").innerHTML = items.map((item) => `
        <li>
          <small>Decisión #${item.id} · ${formatDate(item.decided_at)}</small>
          <div class="decision-title">${esc(item.title || "Sin título")}</div>
          <div class="chip-row">
            ${statusChip(item.status || "active")}
            ${(item.tags || []).map((tag) => `<span class="chip">${esc(tag)}</span>`).join("")}
          </div>
          <div class="kv" style="margin-top: 12px;">
            <div><strong>Elegido</strong><div class="decision-body">${esc(item.chosen || "—")}</div></div>
            ${item.rationale ? `<div><strong>Justificación</strong><div class="decision-body">${esc(item.rationale)}</div></div>` : ""}
            ${item.links && item.links.length ? `<div><strong>Relaciones</strong><div class="decision-body">${item.links.map((link) => `${esc(link.direction)} ${esc(link.link_type)} → ${esc(link.title)}`).join("\\n")}</div></div>` : ""}
          </div>
        </li>
      `).join("");
    }

    function renderCommits(data) {
      const items = data.items || [];
      if (!items.length) {
        togglePanel("commitsPanel", false);
        setPanelSpan("searchPanel", 12);
        return;
      }
      togglePanel("commitsPanel", true);
      setPanelSpan("searchPanel", 6);
      document.getElementById("commits").innerHTML = items.map((item) => `
        <li>
          <small>${formatDate(item.committed_at)} · ${esc(item.author || "autor desconocido")}</small>
          <div class="commit-title">${esc(item.sha_short || item.sha || "commit")} — ${esc(item.message || "sin mensaje")}</div>
          <div class="chip-row">
            ${statusChip(item.iteration_label || "sin iteración")}
            ${(item.files || []).slice(0, 4).map((file) => `<span class="chip">${esc(file)}</span>`).join("")}
          </div>
        </li>
      `).join("");
    }

    function renderSearch(data) {
      const docs = data.docs || [];
      const memory = data.memory || [];
      if (!docs.length && !memory.length) {
        renderEmpty("searchResults", "No hay coincidencias para esa búsqueda.");
        return;
      }
      const items = [];
      for (const item of docs) {
        items.push(`
          <li>
            <small>Artefacto</small>
            <div class="search-title">${esc(item.path || "docs/project/")}:${esc(item.line || "?")}</div>
            <div class="event-body">${esc(item.snippet || "")}</div>
          </li>
        `);
      }
      for (const item of memory) {
        items.push(`
          <li>
            <small>Memoria SQLite</small>
            <div class="search-title">${esc(item.label || item.source_type || "resultado")}</div>
          </li>
        `);
      }
      document.getElementById("searchResults").innerHTML = items.join("");
    }

    function graphStatusFill(status) {
      const raw = String(status || "active").toLowerCase();
      if (raw === "superseded") return "#ffcb6b";
      if (raw === "deprecated") return "#ff7a90";
      return "#54c4ff";
    }

    function showGraphDetail(node) {
      const element = document.getElementById("graphDetail");
      if (!element) return;
      if (!node) {
        element.className = "empty";
        element.textContent = "Haz clic en una decisión del grafo para ver el detalle.";
        return;
      }
      element.className = "";
      element.innerHTML = `
        <small>Decisión #${esc(node.decision_id || "")}</small>
        <div class="decision-title">${esc(node.title || node.label || "Decisión")}</div>
        <div class="chip-row">${statusChip(node.status || "active")}</div>
        <div class="kv" style="margin-top:12px;">
          <div><strong>Elegido</strong><div class="decision-body">${esc(node.chosen || "—")}</div></div>
          ${node.rationale ? `<div><strong>Justificación</strong><div class="decision-body">${esc(node.rationale)}</div></div>` : ""}
        </div>
      `;
    }

    function renderGraph(data) {
      state.graph = data || { nodes: [], edges: [] };
      const svg = document.getElementById("graph");
      const width = 800;
      const height = 420;
      const nodes = state.graph.nodes || [];
      const edges = state.graph.edges || [];
      if (!nodes.length) {
        togglePanel("graphPanel", false);
        svg.innerHTML = "";
        showGraphDetail(null);
        return;
      }
      togglePanel("graphPanel", true);
      const centerX = width / 2;
      const centerY = height / 2;
      const radius = Math.max(110, Math.min(160, 70 + nodes.length * 3));
      const positions = new Map();
      nodes.forEach((node, index) => {
        const angle = (Math.PI * 2 * index) / nodes.length - Math.PI / 2;
        positions.set(node.id, {
          x: centerX + Math.cos(angle) * radius,
          y: centerY + Math.sin(angle) * radius,
        });
      });
      const edgeMarkup = edges.map((edge) => {
        const source = positions.get(edge.source);
        const target = positions.get(edge.target);
        if (!source || !target) return "";
        return `
          <g>
            <line x1="${source.x}" y1="${source.y}" x2="${target.x}" y2="${target.y}" stroke="rgba(157,177,199,0.36)" stroke-width="1.6" />
            <text x="${(source.x + target.x) / 2}" y="${(source.y + target.y) / 2 - 6}" fill="#9db1c7" font-size="11" text-anchor="middle">${esc(edge.label || "")}</text>
          </g>
        `;
      }).join("");
      const nodeMarkup = nodes.map((node) => {
        const point = positions.get(node.id);
        const fill = graphStatusFill(node.status);
        return `
          <g data-node-id="${esc(node.id)}" style="cursor:pointer">
            <circle cx="${point.x}" cy="${point.y}" r="18" fill="${fill}" fill-opacity="0.95" />
            <text x="${point.x}" y="${point.y + 40}" text-anchor="middle" fill="#f4f7fb" font-size="12">${esc(node.label)}</text>
          </g>
        `;
      }).join("");
      svg.innerHTML = edgeMarkup + nodeMarkup;
      svg.onclick = (event) => {
        const target = event.target.closest("[data-node-id]");
        if (!target) return;
        const nodeId = target.getAttribute("data-node-id");
        state.selectedGraphNodeId = nodeId;
        showGraphDetail(nodes.find((item) => String(item.id) === String(nodeId)) || null);
      };
      const selected = nodes.find(
        (item) => String(item.id) === String(state.selectedGraphNodeId || "")
      ) || null;
      if (!selected) {
        state.selectedGraphNodeId = null;
      }
      showGraphDetail(selected);
    }

    async function refreshOverview() {
      const iterationId = state.selectedIterationId || "";
      const suffix = iterationId ? `?iteration_id=${encodeURIComponent(iterationId)}` : "";
      const snapshot = await fetchJson(`/api/snapshot${suffix}`);
      if (snapshot.selected_iteration_id && !state.selectedIterationId) {
        state.selectedIterationId = String(snapshot.selected_iteration_id);
      }
      renderOverview(snapshot.overview || {});
      renderIterations((snapshot.iterations && snapshot.iterations.items) || []);
      renderSessions(snapshot.iterations || {});
      renderActivity(snapshot.activity || {});
      renderProjectSignals(snapshot.overview || {});
      renderDecisions(snapshot.decisions || {});
      renderCommits(snapshot.commits || {});
      renderGraph(snapshot.graph || {});
      renderTimeline(snapshot.timeline || {});
    }

    async function runSearch(query) {
      const trimmed = (query || "").trim();
      if (!trimmed) {
        document.getElementById("searchResults").innerHTML = `
          <li class="hint-card">
            <strong>Escribe algo para buscar en memoria y artefactos.</strong><br />
            Cuando haya memoria, busca por una decisión, un commit o un término de <code>docs/project/</code>.
          </li>
        `;
        return;
      }
      const data = await fetchJson(`/api/search?q=${encodeURIComponent(trimmed)}`);
      renderSearch(data);
    }

    async function refreshAll() {
      try {
        await refreshOverview();
      } catch (error) {
        document.getElementById("lastRefresh").textContent = `Error al refrescar: ${error.message}`;
      }
    }

    document.getElementById("iterationSelect").addEventListener("change", async (event) => {
      state.selectedIterationId = event.target.value;
      await refreshAll();
    });

    document.getElementById("refreshButton").addEventListener("click", async () => {
      await refreshAll();
    });

    document.getElementById("searchForm").addEventListener("submit", async (event) => {
      event.preventDefault();
      await runSearch(document.getElementById("searchInput").value);
    });

    document.getElementById("refreshSeconds").textContent = String(refreshEveryMs / 1000);
    refreshAll();
    setInterval(refreshAll, refreshEveryMs);
  </script>
</body>
</html>
"""


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _plugin_root() -> str:
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _load_plugin_metadata() -> Dict[str, str]:
    plugin_json_path = os.path.join(_plugin_root(), ".claude-plugin", "plugin.json")
    try:
        with open(plugin_json_path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, json.JSONDecodeError):
        return {
            "name": "alfred-dev",
            "display_name": "Alfred Dev",
            "version": "desconocida",
        }
    name = str(data.get("name") or "alfred-dev")
    return {
        "name": name,
        "display_name": "Alfred Dev" if name == "alfred-dev" else name,
        "version": str(data.get("version") or "desconocida"),
    }


def _safe_int(value: Optional[str], default: int, minimum: int = 1, maximum: int = 200) -> int:
    try:
        parsed = int(value or "")
    except (TypeError, ValueError):
        return default
    return max(minimum, min(maximum, parsed))


def _project_path(project_dir: str, relative_path: str) -> str:
    return os.path.join(project_dir, relative_path)


def _parse_json_list(raw: Any) -> List[str]:
    if isinstance(raw, list):
        return [str(item) for item in raw]
    if not raw:
        return []
    try:
        decoded = json.loads(raw)
    except (TypeError, json.JSONDecodeError):
        return []
    if not isinstance(decoded, list):
        return []
    return [str(item) for item in decoded]


def _compact_text(value: Any, limit: int = 220) -> str:
    text = " ".join(str(value or "").split()).strip()
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + "…"


def _event_payload_dict(raw_payload: Any) -> Dict[str, Any]:
    if not raw_payload:
        return {}
    try:
        decoded = json.loads(raw_payload)
    except (TypeError, json.JSONDecodeError):
        return {}
    return decoded if isinstance(decoded, dict) else {}


def _parse_task_notification(raw_content: str) -> Dict[str, str]:
    result: Dict[str, str] = {}
    for field in ("task-id", "tool-use-id", "output-file", "status", "summary", "result"):
        match = re.search(
            rf"<{field}>(.*?)</{field}>",
            raw_content or "",
            flags=re.DOTALL,
        )
        if match:
            result[field] = " ".join(match.group(1).split()).strip()

    transcript_match = re.search(
        r"Full transcript available at:\s*(.+)$",
        raw_content or "",
        flags=re.MULTILINE,
    )
    if transcript_match:
        result["transcript-path"] = transcript_match.group(1).strip()
    return result


def _event_status_label(event_type: str, parsed_payload: Dict[str, Any], task_notification: Dict[str, str]) -> str:
    if task_notification.get("status"):
        return task_notification["status"]
    if parsed_payload.get("status"):
        return str(parsed_payload["status"])
    if event_type == "session_started":
        return "activa"
    if event_type == "session_ended":
        return "cerrada"
    return ""


def _humanize_event(event: Dict[str, Any]) -> Dict[str, Any]:
    event_type = str(event.get("event_type") or "event")
    payload = _event_payload_dict(event.get("payload"))
    content = str(event.get("content") or "").strip()
    summary = str(event.get("summary") or "").strip()
    first_line = content.splitlines()[0].strip() if content else ""
    task_notification = (
        _parse_task_notification(content)
        if event_type == "user_prompt" and content.lstrip().startswith("<task-notification>")
        else {}
    )

    title = summary or _EVENT_TYPE_LABELS.get(event_type, event_type.replace("_", " "))
    body = ""
    detail_lines: List[str] = []
    kind_label = _EVENT_TYPE_LABELS.get(event_type, "Evento")

    if event_type == "session_started":
        title = "Sesión iniciada"
        source = payload.get("source")
        body = (
            f"Alfred abrió una sesión general y dejó la memoria lista para capturar actividad."
            if not source
            else f"Sesión abierta automáticamente por `{source}`."
        )
    elif event_type == "session_ended":
        title = summary or "Sesión finalizada"
        source = payload.get("source")
        body = f"Cierre registrado por `{source}`." if source else "La sesión terminó correctamente."
    elif event_type == "user_prompt" and task_notification:
        kind_label = "Subagente"
        title = task_notification.get("summary") or "Notificación de subagente"
        body = task_notification.get("result") or "Un subagente devolvió actividad al hilo principal."
        if task_notification.get("status"):
            detail_lines.append(f"Estado: {task_notification['status']}")
        if task_notification.get("task-id"):
            detail_lines.append(f"Task: {task_notification['task-id']}")
        if task_notification.get("tool-use-id"):
            detail_lines.append(f"Tool use: {task_notification['tool-use-id']}")
        transcript = task_notification.get("transcript-path") or task_notification.get("output-file")
        if transcript:
            detail_lines.append(f"Transcript: {os.path.basename(transcript)}")
    elif event_type == "user_prompt":
        if first_line.startswith("/"):
            kind_label = "Comando"
            title = f"Comando {first_line}"
            body = "Prompt enviado a Alfred desde Claude Code."
            if len(content.splitlines()) > 1:
                detail_lines.extend(_compact_text(line, 180) for line in content.splitlines()[1:4] if line.strip())
        else:
            title = summary or "Prompt del usuario"
            body = _compact_text(first_line or content or "Prompt sin contenido legible.", 260)
            extra_lines = [line.strip() for line in content.splitlines()[1:4] if line.strip()]
            detail_lines.extend(_compact_text(line, 180) for line in extra_lines)
    elif event_type == "phase_completed":
        title = summary or f"Fase {event.get('phase') or 'desconocida'} completada"
        body = _compact_text(content or "La fase se marcó como completada.", 260)
    elif event_type == "helper_seeded":
        kind_label = "Helper"
        helper_name = str(payload.get("helper") or "helper").strip()
        title = summary or f"{helper_name} preparado"
        artifacts = payload.get("artifacts") or []
        if isinstance(artifacts, list) and artifacts:
            detail_lines.append("Artefactos: " + ", ".join(str(item) for item in artifacts[:4]))
        recommended = payload.get("recommended_command") or payload.get("next_command")
        if recommended:
            recommended_text = str(recommended).strip()
            if recommended_text.startswith("/alfred-dev:"):
                detail_lines.append(f"Siguiente paso: {recommended_text}")
            else:
                detail_lines.append(f"Siguiente paso: /alfred-dev:{recommended_text}")
        body = _compact_text(
            content or f"Alfred dejó contexto listo para continuar con {helper_name}.",
            260,
        )
    elif event_type == "command_executed":
        title = summary or "Comando ejecutado"
        body = _compact_text(content or payload.get("command") or "Alfred registró la ejecución de un comando.", 260)
    elif summary:
        body = _compact_text(content or "Evento registrado en la memoria del proyecto.", 260)
    else:
        title = _EVENT_TYPE_LABELS.get(event_type, event_type.replace("_", " ").capitalize())
        body = _compact_text(content or ", ".join(f"{k}={v}" for k, v in payload.items()) or "Sin detalle adicional.", 260)

    if not detail_lines and payload:
        for key, value in payload.items():
            if key in {"length", "source", "status"}:
                continue
            detail_lines.append(f"{key}: {_compact_text(value, 120)}")

    return {
        **event,
        "kind_label": kind_label,
        "status_label": _event_status_label(event_type, payload, task_notification),
        "display_title": title,
        "display_body": body,
        "detail_lines": detail_lines[:6],
        "phase_label": str(event.get("phase") or ""),
    }


def _decision_links_payload(db: MemoryDB, decision_id: int) -> List[Dict[str, Any]]:
    links: List[Dict[str, Any]] = []
    for link in db.get_decision_links(decision_id):
        if link.get("source_id") == decision_id:
            other_id = link.get("target_id")
            direction = "→"
        else:
            other_id = link.get("source_id")
            direction = "←"
        other = db.get_decision(int(other_id)) if other_id is not None else None
        links.append(
            {
                "direction": direction,
                "link_type": link.get("link_type", "relates"),
                "decision_id": other_id,
                "title": (other or {}).get("title", f"Decisión #{other_id}"),
            }
        )
    return links


def _serialize_decision(db: MemoryDB, item: Dict[str, Any]) -> Dict[str, Any]:
    return {
        **item,
        "tags": _parse_json_list(item.get("tags")),
        "links": _decision_links_payload(db, int(item["id"])),
    }


def _serialize_commit(item: Dict[str, Any], iteration_lookup: Dict[int, Dict[str, Any]]) -> Dict[str, Any]:
    files = _parse_json_list(item.get("files"))
    iteration = iteration_lookup.get(int(item["iteration_id"])) if item.get("iteration_id") else None
    return {
        **item,
        "sha_short": str(item.get("sha", ""))[:8],
        "files": files,
        "iteration_label": (
            f"#{iteration['id']} · {iteration.get('command', 'session')}"
            if iteration
            else "sin iteración"
        ),
    }


def _recent_iteration_events(
    db: MemoryDB,
    iteration_id: int,
    limit: int = 3,
) -> List[Dict[str, Any]]:
    """Devuelve los eventos más recientes ya humanizados."""
    return [
        _humanize_event(event)
        for event in db.get_events(iteration_id=iteration_id, limit=limit)
    ]


def _pick_latest_event_value(
    events: List[Dict[str, Any]],
    *field_names: str,
) -> str:
    """Extrae el primer valor útil de una lista de eventos recientes."""
    for event in events:
        for field_name in field_names:
            value = event.get(field_name)
            if value:
                return str(value)
    return ""


def _build_progress(project_dir: str) -> Dict[str, Any]:
    from core.continuity import build_progress_snapshot

    return build_progress_snapshot(project_dir)


def _is_git_repo(project_dir: str) -> bool:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--is-inside-work-tree"],
            cwd=project_dir,
            capture_output=True,
            text=True,
            check=False,
        )
        return result.returncode == 0 and result.stdout.strip() == "true"
    except Exception:
        return False


def _has_codebase(project_dir: str) -> bool:
    code_exts = {
        ".py", ".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs", ".rs", ".go", ".java",
        ".kt", ".rb", ".php", ".cs", ".swift", ".scala", ".html", ".astro", ".vue", ".svelte",
    }
    skip_dirs = {".git", ".hg", ".svn", "node_modules", ".venv", "venv", "dist", "build", ".claude"}
    for root, dirs, files in os.walk(project_dir):
        dirs[:] = [item for item in dirs if item not in skip_dirs]
        for filename in files:
            if os.path.splitext(filename)[1].lower() in code_exts:
                return True
    return False


def _workspace_summary(project_dir: str, db: Optional[MemoryDB] = None) -> Dict[str, Any]:
    sample_paths: List[str] = []
    try:
        for entry in sorted(os.listdir(project_dir)):
            if entry in {".", "..", ".claude"}:
                continue
            sample_paths.append(entry)
            if len(sample_paths) >= 6:
                break
    except OSError:
        pass
    summary = {
        "is_git_repo": _is_git_repo(project_dir),
        "has_codebase": _has_codebase(project_dir),
        "has_docs_project": os.path.isdir(os.path.join(project_dir, "docs", "project")),
        "sample_paths": sample_paths,
    }
    if db is not None:
        stats = db.get_stats()
        bootstrap_event_count = int(
            db.count_events(event_type="session_started")
            + db.count_events(event_type="session_ended")
        )
        meaningful_event_count = max(
            0,
            int(stats.get("total_events", 0) or 0) - bootstrap_event_count,
        )
        summary.update(
            {
                "bootstrap_event_count": bootstrap_event_count,
                "meaningful_event_count": meaningful_event_count,
                "has_meaningful_memory": bool(
                    int(stats.get("total_iterations", 0) or 0) > 0
                    or int(stats.get("total_decisions", 0) or 0) > 0
                    or int(stats.get("total_commits", 0) or 0) > 0
                    or meaningful_event_count > 0
                ),
            }
        )
    return summary


def _list_iterations(db: MemoryDB, limit: int = 50) -> List[Dict[str, Any]]:
    return db.get_iterations(limit=limit)


def build_overview_payload(project_dir: str, db_path: str, host: str, port: int) -> Dict[str, Any]:
    db = MemoryDB(db_path)
    try:
        plugin_meta = _load_plugin_metadata()
        stats = db.get_stats()
        memory_empty = not any(
            int(stats.get(key, 0) or 0)
            for key in (
                "total_iterations",
                "total_decisions",
                "total_commits",
                "total_events",
            )
        )
        return {
            "plugin_name": plugin_meta["display_name"],
            "plugin_version": plugin_meta["version"],
            "ui_version": UI_VERSION,
            "project_name": os.path.basename(project_dir.rstrip(os.sep)) or project_dir,
            "project_dir": project_dir,
            "db_path": db_path,
            "refreshed_at": _iso_now(),
            "stats": stats,
            "health": db.check_health(),
            "workspace": _workspace_summary(project_dir, db=db),
            "active_iteration": db.get_active_iteration(),
            "latest_iteration": db.get_latest_iteration(),
            "memory_empty": memory_empty,
            "progress": {} if memory_empty else _build_progress(project_dir),
            "server": {
                "host": host,
                "port": port,
                "url": f"http://{host}:{port}",
            },
        }
    finally:
        db.close()


def build_iterations_payload(db_path: str, limit: int = 50) -> Dict[str, Any]:
    db = MemoryDB(db_path)
    try:
        items: List[Dict[str, Any]] = []
        for item in _list_iterations(db, limit=limit):
            recent_events = _recent_iteration_events(db, int(item["id"]), limit=3)
            items.append(
                {
                    **item,
                    "event_count": db.count_events(iteration_id=int(item["id"])),
                    "last_summary": _pick_latest_event_value(
                        recent_events, "summary", "content", "event_type"
                    ),
                    "last_title": _pick_latest_event_value(recent_events, "display_title"),
                    "last_body": _pick_latest_event_value(recent_events, "display_body"),
                    "is_active": item.get("status") == "active",
                }
            )
        return {"items": items}
    finally:
        db.close()


def build_timeline_payload(
    db_path: str,
    iteration_id: Optional[int],
    limit: Optional[int] = None,
) -> Dict[str, Any]:
    db = MemoryDB(db_path)
    try:
        if iteration_id is None:
            iteration = db.get_active_iteration() or db.get_latest_iteration()
            if iteration is None:
                return {"iteration": None, "events": []}
            iteration_id = int(iteration["id"])
        else:
            iteration = db.get_iteration(iteration_id)
            if iteration is None:
                return {"iteration": None, "events": []}
        event_count = db.count_events(iteration_id=iteration_id)
        effective_limit = event_count if limit is None else min(max(limit, 1), event_count or 1)
        events = [_humanize_event(event) for event in db.get_timeline(iteration_id, limit=effective_limit)]
        return {
            "iteration": iteration,
            "events": events,
            "event_count": event_count,
            "returned_count": len(events),
            "truncated": event_count > len(events),
        }
    finally:
        db.close()


def build_decisions_payload(
    db_path: str,
    limit: int = 40,
    status: Optional[str] = None,
    iteration_id: Optional[int] = None,
) -> Dict[str, Any]:
    db = MemoryDB(db_path)
    try:
        items = [
            _serialize_decision(db, item)
            for item in db.get_decisions(limit=limit, status=status, iteration_id=iteration_id)
        ]
        return {"items": items}
    finally:
        db.close()


def build_graph_payload(
    db_path: str,
    limit: int = 18,
    iteration_id: Optional[int] = None,
) -> Dict[str, Any]:
    db = MemoryDB(db_path)
    try:
        decisions = db.get_decisions(limit=limit, iteration_id=iteration_id)
        decision_ids = {int(item["id"]) for item in decisions}
        nodes = [
            {
                "id": f"d{item['id']}",
                "decision_id": int(item["id"]),
                "label": (item.get("title", f"D#{item['id']}"))[:28],
                "title": item.get("title", f"Decisión #{item['id']}"),
                "status": item.get("status") or "active",
                "chosen": item.get("chosen") or "",
                "rationale": item.get("rationale") or "",
            }
            for item in decisions
        ]
        seen_edges = set()
        edges: List[Dict[str, Any]] = []
        for item in decisions:
            for link in db.get_decision_links(int(item["id"])):
                source = int(link["source_id"])
                target = int(link["target_id"])
                if source not in decision_ids or target not in decision_ids:
                    continue
                key = (source, target, link.get("link_type"))
                if key in seen_edges:
                    continue
                seen_edges.add(key)
                edges.append(
                    {
                        "source": f"d{source}",
                        "target": f"d{target}",
                        "label": link.get("link_type", "relates"),
                    }
                )
        return {"nodes": nodes, "edges": edges}
    finally:
        db.close()


def build_commits_payload(
    db_path: str,
    project_dir: str,
    limit: int = 30,
    iteration_id: Optional[int] = None,
) -> Dict[str, Any]:
    db = MemoryDB(db_path)
    try:
        raw_items = db.get_commits(limit=limit, iteration_id=iteration_id)
        iteration_ids = {
            int(item["iteration_id"])
            for item in raw_items
            if item.get("iteration_id")
        }
        iterations = {
            iteration_id_value: iteration
            for iteration_id_value in iteration_ids
            for iteration in [db.get_iteration(iteration_id_value)]
            if iteration is not None
        }
        items = [
            _serialize_commit(item, iterations)
            for item in raw_items
        ]
        return {"items": items}
    finally:
        db.close()


def build_search_payload(project_dir: str, query: str, limit: int = 12) -> Dict[str, Any]:
    from core.continuity import search_project_context

    return search_project_context(project_dir, query, limit=limit)


def _recent_event_counts(events: List[Dict[str, Any]], limit: int = 8) -> List[Dict[str, Any]]:
    """Resume la mezcla de tipos dentro de la misma ventana reciente."""
    counts: Dict[str, Dict[str, Any]] = {}
    for event in events:
        event_type = str(event.get("event_type") or "event")
        bucket = counts.setdefault(
            event_type,
            {
                "event_type": event_type,
                "label": str(
                    event.get("kind_label")
                    or _EVENT_TYPE_LABELS.get(event_type, event_type.replace("_", " "))
                ),
                "total": 0,
            },
        )
        bucket["total"] += 1

    return sorted(
        counts.values(),
        key=lambda item: (-int(item.get("total", 0) or 0), str(item.get("label", ""))),
    )[:limit]


def _resolve_snapshot_iteration_id(
    iterations_payload: Dict[str, Any],
    iteration_id: Optional[int],
) -> Optional[int]:
    if iteration_id is not None:
        return iteration_id
    items = iterations_payload.get("items") or []
    active = next((item for item in items if item.get("is_active")), None)
    chosen = active or (items[0] if items else None)
    if chosen is None:
        return None
    return int(chosen["id"])


def build_snapshot_payload(
    project_dir: str,
    db_path: str,
    host: str,
    port: int,
    iteration_id: Optional[int] = None,
) -> Dict[str, Any]:
    overview = build_overview_payload(project_dir, db_path, host, port)
    iterations = build_iterations_payload(db_path)
    selected_iteration_id = _resolve_snapshot_iteration_id(iterations, iteration_id)
    return {
        "overview": overview,
        "iterations": iterations,
        "decisions": build_decisions_payload(
            db_path,
            iteration_id=selected_iteration_id,
        ),
        "commits": build_commits_payload(
            db_path,
            project_dir,
            iteration_id=selected_iteration_id,
        ),
        "graph": build_graph_payload(
            db_path,
            iteration_id=selected_iteration_id,
        ),
        "activity": build_activity_payload(db_path),
        "timeline": build_timeline_payload(db_path, selected_iteration_id),
        "selected_iteration_id": selected_iteration_id,
    }


def build_activity_payload(db_path: str, limit: int = 18) -> Dict[str, Any]:
    db = MemoryDB(db_path)
    try:
        recent_events = [_humanize_event(event) for event in db.get_events(limit=limit)]
        return {
            "recent_events": recent_events,
            "event_counts": _recent_event_counts(recent_events, limit=8),
            "total_event_counts": db.get_event_counts_by_type(limit=8),
        }
    finally:
        db.close()


class AlfredMemoryUIServer(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = True

    def __init__(self, host: str, port: int, project_dir: str, db_path: str):
        self.project_dir = project_dir
        self.db_path = db_path
        self.host = host
        self.port = port
        super().__init__((host, port), AlfredMemoryUIHandler)


class AlfredMemoryUIHandler(BaseHTTPRequestHandler):
    server_version = "AlfredMemoryUI/0.1"

    def _send_json(self, payload: Dict[str, Any], status: int = 200) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_html(self, body: str) -> None:
        encoded = body.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def log_message(self, format: str, *args: Any) -> None:
        message = "%s - - [%s] %s\n" % (
            self.address_string(),
            self.log_date_time_string(),
            format % args,
        )
        sys.stderr.write(message)

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        params = parse_qs(parsed.query)
        server: AlfredMemoryUIServer = self.server  # type: ignore[assignment]

        try:
            if parsed.path in {"/", "/index.html"}:
                self._send_html(HTML_TEMPLATE)
                return
            if parsed.path == "/api/healthz":
                self._send_json(
                    {
                        "ok": True,
                        "project_dir": server.project_dir,
                        "db_path": server.db_path,
                        "server_time": _iso_now(),
                    }
                )
                return
            if parsed.path == "/api/overview":
                self._send_json(
                    build_overview_payload(server.project_dir, server.db_path, server.host, server.port)
                )
                return
            if parsed.path == "/api/iterations":
                limit = _safe_int((params.get("limit") or [None])[0], default=50)
                self._send_json(build_iterations_payload(server.db_path, limit=limit))
                return
            if parsed.path == "/api/timeline":
                raw_iteration = (params.get("iteration_id") or [None])[0]
                iteration_id = int(raw_iteration) if raw_iteration and raw_iteration.isdigit() else None
                raw_limit = (params.get("limit") or [None])[0]
                limit = _safe_int(raw_limit, default=120) if raw_limit is not None else None
                self._send_json(build_timeline_payload(server.db_path, iteration_id, limit=limit))
                return
            if parsed.path == "/api/decisions":
                raw_iteration = (params.get("iteration_id") or [None])[0]
                iteration_id = int(raw_iteration) if raw_iteration and raw_iteration.isdigit() else None
                limit = _safe_int((params.get("limit") or [None])[0], default=40)
                status = (params.get("status") or [None])[0]
                self._send_json(
                    build_decisions_payload(
                        server.db_path,
                        limit=limit,
                        status=status,
                        iteration_id=iteration_id,
                    )
                )
                return
            if parsed.path == "/api/graph":
                raw_iteration = (params.get("iteration_id") or [None])[0]
                iteration_id = int(raw_iteration) if raw_iteration and raw_iteration.isdigit() else None
                limit = _safe_int((params.get("limit") or [None])[0], default=18, maximum=40)
                self._send_json(
                    build_graph_payload(
                        server.db_path,
                        limit=limit,
                        iteration_id=iteration_id,
                    )
                )
                return
            if parsed.path == "/api/snapshot":
                raw_iteration = (params.get("iteration_id") or [None])[0]
                iteration_id = int(raw_iteration) if raw_iteration and raw_iteration.isdigit() else None
                self._send_json(
                    build_snapshot_payload(
                        server.project_dir,
                        server.db_path,
                        server.host,
                        server.port,
                        iteration_id=iteration_id,
                    )
                )
                return
            if parsed.path == "/api/commits":
                raw_iteration = (params.get("iteration_id") or [None])[0]
                iteration_id = int(raw_iteration) if raw_iteration and raw_iteration.isdigit() else None
                limit = _safe_int((params.get("limit") or [None])[0], default=30)
                self._send_json(
                    build_commits_payload(
                        server.db_path,
                        project_dir=server.project_dir,
                        limit=limit,
                        iteration_id=iteration_id,
                    )
                )
                return
            if parsed.path == "/api/activity":
                limit = _safe_int((params.get("limit") or [None])[0], default=18, maximum=80)
                self._send_json(build_activity_payload(server.db_path, limit=limit))
                return
            if parsed.path == "/api/search":
                query = (params.get("q") or [""])[0].strip()
                if not query:
                    self._send_json({"query": "", "docs": [], "memory": []})
                    return
                limit = _safe_int((params.get("limit") or [None])[0], default=12, maximum=40)
                self._send_json(build_search_payload(server.project_dir, query, limit=limit))
                return
            self._send_json({"error": "Not found"}, status=404)
        except Exception as exc:  # pragma: no cover - fallback defensivo
            self._send_json({"error": str(exc)}, status=500)


def _assert_loopback_host(host: str) -> str:
    normalized = str(host or "").strip().lower()
    if normalized not in _LOOPBACK_HOSTS:
        raise ValueError(
            "Memory UI solo acepta host de loopback "
            f"(127.0.0.1, ::1 o localhost), no {host!r}."
        )
    return host


def run_server(project_dir: str, db_path: str, host: str, port: int) -> int:
    host = _assert_loopback_host(host)
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    db = MemoryDB(db_path)
    db.close()
    httpd = AlfredMemoryUIServer(host, port, project_dir, db_path)
    try:
        httpd.serve_forever(poll_interval=0.5)
    except KeyboardInterrupt:
        pass
    finally:
        httpd.server_close()
    return 0


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Servidor local de la UI de memoria de Alfred Dev")
    parser.add_argument("--project-dir", required=True)
    parser.add_argument("--db-path", required=True)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, required=True)
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    try:
        host = _assert_loopback_host(args.host)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    return run_server(
        project_dir=os.path.abspath(args.project_dir),
        db_path=os.path.abspath(args.db_path),
        host=host,
        port=args.port,
    )


if __name__ == "__main__":
    raise SystemExit(main())
