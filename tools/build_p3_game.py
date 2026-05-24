#!/usr/bin/env python3
"""Build the standalone P3 recommendation game from MovieLens small data."""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path


LIKED_THRESHOLD = 3.5
DATASET_URL = "https://files.grouplens.org/datasets/movielens/ml-latest-small.zip"


HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>P3 Recommendation Engine</title>
    <style>
        :root {
            --bg: #101827;
            --panel: rgba(22, 33, 49, 0.9);
            --panel-strong: #1b293c;
            --line: rgba(148, 163, 184, 0.26);
            --text: #f8fafc;
            --muted: #b7c4d5;
            --muted-2: #8fa2b8;
            --accent: #14b8a6;
            --accent-2: #f59e0b;
            --accent-3: #38bdf8;
            --danger: #ef4444;
            --success: #84cc16;
            --movie: #f59e0b;
            --movie-soft: rgba(245, 158, 11, 0.16);
            --user: #a78bfa;
            --you: #14b8a6;
            --radius: 8px;
        }

        * {
            box-sizing: border-box;
        }

        body {
            margin: 0;
            min-height: 100vh;
            font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
            color: var(--text);
            background:
                radial-gradient(circle at 12% 14%, rgba(20, 184, 166, 0.16), transparent 34rem),
                radial-gradient(circle at 88% 7%, rgba(245, 158, 11, 0.14), transparent 30rem),
                linear-gradient(135deg, #0f172a 0%, #111827 44%, #1f2937 100%);
        }

        button,
        input {
            font: inherit;
        }

        button {
            border: 1px solid rgba(148, 163, 184, 0.34);
            background: rgba(34, 48, 68, 0.92);
            color: var(--text);
            border-radius: 999px;
            min-height: 40px;
            padding: 8px 13px;
            cursor: pointer;
            transition: background 0.14s ease, border-color 0.14s ease, transform 0.14s ease, opacity 0.14s ease;
        }

        button:hover:not(:disabled) {
            background: rgba(51, 65, 85, 0.96);
            border-color: rgba(20, 184, 166, 0.84);
        }

        button:active:not(:disabled) {
            transform: translateY(1px);
        }

        button:disabled {
            cursor: not-allowed;
            opacity: 0.5;
        }

        .primary {
            background: linear-gradient(135deg, #0f766e, #14b8a6);
            border-color: rgba(94, 234, 212, 0.82);
            color: white;
        }

        .danger {
            background: rgba(127, 29, 29, 0.78);
            border-color: rgba(248, 113, 113, 0.5);
        }

        .shell {
            width: min(1480px, calc(100vw - 28px));
            margin: 0 auto;
            padding: 22px 0 30px;
        }

        header {
            display: grid;
            grid-template-columns: 1fr auto;
            gap: 18px;
            align-items: end;
            margin-bottom: 16px;
        }

        h1 {
            margin: 0 0 6px;
            font-size: clamp(1.8rem, 3vw, 3.15rem);
            line-height: 1.05;
            font-weight: 780;
            letter-spacing: 0;
        }

        .subtitle {
            color: var(--muted);
            margin: 0;
            max-width: 850px;
            line-height: 1.45;
        }

        .dataset-pill {
            border: 1px solid rgba(148, 163, 184, 0.34);
            background: rgba(15, 23, 42, 0.74);
            color: var(--muted);
            border-radius: 999px;
            padding: 9px 13px;
            white-space: nowrap;
            font-size: 0.92rem;
        }

        .app {
            display: grid;
            grid-template-columns: minmax(0, 1fr) minmax(330px, 390px);
            gap: 14px;
            align-items: stretch;
        }

        .main,
        aside,
        .recommendations {
            background: var(--panel);
            border: 1px solid var(--line);
            border-radius: var(--radius);
            box-shadow: 0 18px 55px rgba(0, 0, 0, 0.27);
        }

        .main {
            display: flex;
            min-width: 0;
            flex-direction: column;
            overflow: hidden;
        }

        .canvas-toolbar {
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
            align-items: center;
            justify-content: space-between;
            padding: 12px;
            border-bottom: 1px solid rgba(148, 163, 184, 0.2);
            background: rgba(15, 23, 42, 0.5);
        }

        .legend {
            display: flex;
            flex-wrap: wrap;
            gap: 8px 12px;
            color: var(--muted);
            font-size: 0.9rem;
        }

        .legend-item {
            display: inline-flex;
            align-items: center;
            gap: 7px;
        }

        .dot {
            width: 10px;
            height: 10px;
            border-radius: 999px;
            display: inline-block;
        }

        .dot.you { background: var(--you); }
        .dot.movie { background: var(--movie); }
        .dot.user { background: var(--user); }
        .dot.walk { background: var(--accent-3); }

        .graph-wrap {
            position: relative;
            padding: 12px;
            flex: 1;
            min-height: 610px;
        }

        canvas {
            width: 100%;
            height: min(65vh, 680px);
            min-height: 560px;
            display: block;
            background:
                radial-gradient(circle at 50% 42%, rgba(56, 189, 248, 0.11), transparent 22rem),
                linear-gradient(180deg, #f8fafc 0%, #e2e8f0 100%);
            border-radius: var(--radius);
            border: 1px solid rgba(15, 23, 42, 0.18);
        }

        .graph-status {
            position: absolute;
            left: 24px;
            bottom: 24px;
            max-width: min(720px, calc(100% - 48px));
            padding: 10px 12px;
            border-radius: var(--radius);
            color: #0f172a;
            background: rgba(255, 255, 255, 0.9);
            border: 1px solid rgba(15, 23, 42, 0.16);
            font-size: 0.93rem;
            line-height: 1.36;
            box-shadow: 0 12px 26px rgba(15, 23, 42, 0.16);
        }

        aside {
            padding: 16px;
            overflow: auto;
            max-height: calc(100vh - 44px);
        }

        .panel-title {
            margin: 0 0 6px;
            font-size: 1.18rem;
            font-weight: 740;
        }

        .panel-copy {
            color: var(--muted);
            line-height: 1.45;
            margin: 0 0 14px;
        }

        .section {
            border-top: 1px solid rgba(148, 163, 184, 0.2);
            padding-top: 14px;
            margin-top: 14px;
        }

        .section:first-child {
            border-top: 0;
            padding-top: 0;
            margin-top: 0;
        }

        .movie-row {
            display: grid;
            grid-template-columns: minmax(0, 1fr) 46px;
            gap: 8px;
            align-items: start;
            margin-bottom: 10px;
        }

        .movie-row input {
            width: 100%;
            min-height: 40px;
            border-radius: var(--radius);
            border: 1px solid rgba(148, 163, 184, 0.34);
            background: rgba(15, 23, 42, 0.72);
            color: var(--text);
            padding: 9px 11px;
            outline: none;
        }

        .movie-row input:focus {
            border-color: rgba(20, 184, 166, 0.88);
            box-shadow: 0 0 0 3px rgba(20, 184, 166, 0.16);
        }

        .movie-row input.invalid {
            border-color: rgba(248, 113, 113, 0.9);
            box-shadow: 0 0 0 3px rgba(239, 68, 68, 0.14);
        }

        .arrow-button {
            width: 46px;
            min-width: 46px;
            padding-inline: 0;
            font-weight: 760;
        }

        .row-message {
            grid-column: 1 / -1;
            min-height: 18px;
            color: var(--muted-2);
            font-size: 0.82rem;
            line-height: 1.3;
            padding-left: 2px;
        }

        .row-message.ok { color: #bbf7d0; }
        .row-message.error { color: #fecaca; }
        .row-message.warn { color: #fde68a; }

        .button-row {
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            align-items: center;
        }

        .control-label {
            display: block;
            color: #dbeafe;
            font-weight: 680;
            margin-bottom: 8px;
        }

        .speed-grid {
            display: grid;
            grid-template-columns: 1fr auto;
            gap: 10px;
            align-items: center;
        }

        input[type="range"] {
            width: 100%;
            accent-color: var(--accent);
        }

        .speed-readout {
            color: var(--muted);
            min-width: 70px;
            text-align: right;
            font-size: 0.9rem;
        }

        .metric-grid {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 8px;
            margin-top: 12px;
        }

        .metric {
            background: rgba(15, 23, 42, 0.46);
            border: 1px solid rgba(148, 163, 184, 0.18);
            border-radius: var(--radius);
            padding: 10px;
        }

        .metric-value {
            font-size: 1.3rem;
            font-weight: 760;
            line-height: 1.05;
        }

        .metric-label {
            margin-top: 4px;
            color: var(--muted-2);
            font-size: 0.78rem;
            line-height: 1.2;
        }

        .explain-list {
            display: grid;
            gap: 8px;
            margin: 10px 0 0;
            padding: 0;
            list-style: none;
        }

        .explain-list li {
            display: grid;
            grid-template-columns: 26px 1fr;
            gap: 9px;
            color: var(--muted);
            line-height: 1.36;
        }

        .step-num {
            width: 26px;
            height: 26px;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            border-radius: 999px;
            background: rgba(20, 184, 166, 0.18);
            color: #ccfbf1;
            font-size: 0.82rem;
            font-weight: 760;
        }

        .recommendations {
            margin-top: 14px;
            overflow: hidden;
        }

        .recommendation-head {
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
            align-items: center;
            justify-content: space-between;
            padding: 12px 14px;
            border-bottom: 1px solid rgba(148, 163, 184, 0.2);
            background: rgba(15, 23, 42, 0.46);
        }

        .recommendation-head h2 {
            font-size: 1.05rem;
            margin: 0;
        }

        .recommendation-head span {
            color: var(--muted);
            font-size: 0.9rem;
        }

        table {
            width: 100%;
            border-collapse: collapse;
        }

        th,
        td {
            padding: 10px 12px;
            border-bottom: 1px solid rgba(148, 163, 184, 0.14);
            text-align: left;
            vertical-align: top;
        }

        th {
            color: #dbeafe;
            background: rgba(15, 23, 42, 0.32);
            font-size: 0.82rem;
            text-transform: uppercase;
            letter-spacing: 0.04em;
        }

        td {
            color: var(--muted);
            line-height: 1.35;
        }

        td.count-cell {
            color: var(--text);
            font-weight: 760;
            width: 82px;
        }

        .empty-row td {
            color: var(--muted-2);
            text-align: center;
            padding: 18px 12px;
        }

        .footnote {
            color: var(--muted-2);
            font-size: 0.82rem;
            line-height: 1.4;
            margin-top: 12px;
        }

        [hidden] {
            display: none !important;
        }

        @media (max-width: 980px) {
            header,
            .app {
                grid-template-columns: 1fr;
            }

            aside {
                max-height: none;
            }

            .graph-wrap {
                min-height: 520px;
            }

            canvas {
                height: 560px;
                min-height: 480px;
            }
        }

        @media (max-width: 620px) {
            .shell {
                width: min(100vw - 18px, 1480px);
                padding-top: 14px;
            }

            .dataset-pill {
                white-space: normal;
            }

            .metric-grid {
                grid-template-columns: 1fr;
            }

            th:nth-child(3),
            td:nth-child(3) {
                display: none;
            }
        }
    </style>
</head>
<body>
    <div class="shell">
        <header>
            <div>
                <h1>P3 Recommendation Engine</h1>
                <p class="subtitle">Type a few movies you like, build a user-movie graph, then watch three-hop random walks turn shared taste into recommendations.</p>
            </div>
            <div class="dataset-pill" id="datasetPill">MovieLens small</div>
        </header>

        <div class="app">
            <main class="main">
                <div class="canvas-toolbar">
                    <div class="legend" aria-label="Graph legend">
                        <span class="legend-item"><span class="dot you"></span>You</span>
                        <span class="legend-item"><span class="dot movie"></span>Movie</span>
                        <span class="legend-item"><span class="dot user"></span>MovieLens user</span>
                        <span class="legend-item"><span class="dot walk"></span>Current walk</span>
                    </div>
                    <div class="button-row">
                        <button id="clearGraphButton" type="button">Clear canvas</button>
                    </div>
                </div>
                <div class="graph-wrap">
                    <canvas id="graphCanvas" aria-label="Animated recommendation graph"></canvas>
                    <div class="graph-status" id="graphStatus">Start by adding a MovieLens title, for example <strong>Toy Story (1995)</strong> or <strong>Matrix, The (1999)</strong>.</div>
                </div>
            </main>

            <aside>
                <section class="section">
                    <h2 class="panel-title">Your liked movies</h2>
                    <p class="panel-copy">Use MovieLens titles. The year is optional when the title is unambiguous.</p>
                    <div id="movieRows"></div>
                    <div class="button-row">
                        <button id="addRowButton" type="button">Add movie box</button>
                    </div>
                    <datalist id="movieTitles"></datalist>
                </section>

                <section class="section">
                    <h2 class="panel-title">Random walks</h2>
                    <p class="panel-copy">P3 walks from you to a liked movie, from that movie to one of the displayed users, and from that user to another liked movie.</p>
                    <div class="button-row">
                        <button id="startWalkButton" class="primary" type="button" hidden>Start random walks</button>
                        <button id="stopWalkButton" class="danger" type="button" disabled>Stop</button>
                    </div>
                    <label class="control-label" for="speedControl">Animation speed</label>
                    <div class="speed-grid">
                        <input id="speedControl" type="range" min="0.5" max="3" step="0.25" value="1.25">
                        <span class="speed-readout" id="speedReadout">1.25x</span>
                    </div>
                    <div class="metric-grid">
                        <div class="metric">
                            <div class="metric-value" id="movieMetric">0</div>
                            <div class="metric-label">Movies on canvas</div>
                        </div>
                        <div class="metric">
                            <div class="metric-value" id="userMetric">0</div>
                            <div class="metric-label">Users on canvas</div>
                        </div>
                        <div class="metric">
                            <div class="metric-value" id="walkMetric">0</div>
                            <div class="metric-label">Walks this run</div>
                        </div>
                    </div>
                </section>

                <section class="section">
                    <h2 class="panel-title">What the animation means</h2>
                    <ul class="explain-list">
                        <li><span class="step-num">1</span><span>Your typed movie becomes an edge from <strong>You</strong> to that movie.</span></li>
                        <li><span class="step-num">2</span><span>The canvas first checks displayed users, then fills the rest with random MovieLens users who rated it at least 3.5 stars.</span></li>
                        <li><span class="step-num">3</span><span>Each P3 walk samples one of your movies, one displayed user linked to it, then one other movie that user liked.</span></li>
                    </ul>
                    <p class="footnote">Dataset: MovieLens ml-latest-small, generated 2018-09-26. User ids are anonymized. This demo uses ratings of 3.5 or higher as liked edges.</p>
                </section>
            </aside>
        </div>

        <section class="recommendations">
            <div class="recommendation-head">
                <h2>Recommendation counts</h2>
                <span id="recommendationNote">Cleared every time random walks start.</span>
            </div>
            <table>
                <thead>
                    <tr>
                        <th>Count</th>
                        <th>Movie</th>
                        <th>Last path</th>
                    </tr>
                </thead>
                <tbody id="recommendationBody">
                    <tr class="empty-row"><td colspan="3">Run random walks to build recommendations.</td></tr>
                </tbody>
            </table>
        </section>
    </div>

    <script id="movielens-data" type="application/json">__MOVIELENS_DATA__</script>
    <script>
    (() => {
        "use strict";

        const DATA = JSON.parse(document.getElementById("movielens-data").textContent);
        const canvas = document.getElementById("graphCanvas");
        const ctx = canvas.getContext("2d");
        const rowsContainer = document.getElementById("movieRows");
        const datalist = document.getElementById("movieTitles");
        const graphStatus = document.getElementById("graphStatus");
        const startWalkButton = document.getElementById("startWalkButton");
        const stopWalkButton = document.getElementById("stopWalkButton");
        const clearGraphButton = document.getElementById("clearGraphButton");
        const addRowButton = document.getElementById("addRowButton");
        const speedControl = document.getElementById("speedControl");
        const speedReadout = document.getElementById("speedReadout");
        const recommendationBody = document.getElementById("recommendationBody");
        const recommendationNote = document.getElementById("recommendationNote");
        const movieMetric = document.getElementById("movieMetric");
        const userMetric = document.getElementById("userMetric");
        const walkMetric = document.getElementById("walkMetric");
        const datasetPill = document.getElementById("datasetPill");

        const moviesById = new Map();
        const titleRecords = [];
        const aliasMap = new Map();
        const likesByMovie = new Map();
        const likesByUser = new Map();

        const state = {
            nodes: new Map(),
            links: [],
            edgeKeys: new Set(),
            seedMovieIds: new Set(),
            invalidRows: new Set(),
            recommendationCounts: new Map(),
            lastPaths: new Map(),
            highlightedNodes: new Set(),
            highlightedEdges: new Set(),
            running: false,
            discoveryInProgress: false,
            discoveryToken: 0,
            walkToken: 0,
            walkCount: 0,
            rowId: 0,
            viewWidth: 900,
            viewHeight: 620,
            animationFrame: null
        };

        function normalizeTitle(value) {
            return String(value || "")
                .normalize("NFD")
                .replace(/[\u0300-\u036f]/g, "")
                .toLowerCase()
                .replace(/&/g, " and ")
                .replace(/[^a-z0-9]+/g, " ")
                .trim()
                .replace(/\s+/g, " ");
        }

        function frontArticle(title) {
            const match = title.match(/^(.*), (The|A|An)( \([0-9]{4}\))$/);
            if (!match) return null;
            return `${match[2]} ${match[1]}${match[3]}`;
        }

        function withoutYear(title) {
            return title.replace(/\s+\([0-9]{4}\)$/, "");
        }

        function addAlias(alias, id) {
            const key = normalizeTitle(alias);
            if (!key) return;
            if (!aliasMap.has(key)) aliasMap.set(key, []);
            const ids = aliasMap.get(key);
            if (!ids.includes(id)) ids.push(id);
        }

        function shortTitle(title) {
            return title.replace(/\s+\([0-9]{4}\)$/, "");
        }

        function buildDataIndexes() {
            for (const [id, title, genres] of DATA.movies) {
                const movie = { id, title, genres };
                moviesById.set(id, movie);
                const alt = frontArticle(title);
                const aliases = [title, withoutYear(title)];
                if (alt) {
                    aliases.push(alt, withoutYear(alt));
                }
                for (const alias of aliases) addAlias(alias, id);
                titleRecords.push({
                    id,
                    title,
                    display: alt || title,
                    searchText: aliases.map(normalizeTitle).join(" ")
                });
            }

            for (const [movieIdText, users] of Object.entries(DATA.likesByMovie)) {
                const movieId = Number(movieIdText);
                likesByMovie.set(movieId, users);
                for (const userId of users) {
                    if (!likesByUser.has(userId)) likesByUser.set(userId, []);
                    likesByUser.get(userId).push(movieId);
                }
            }

            for (const movies of likesByUser.values()) {
                movies.sort((a, b) => a - b);
            }

            const fragment = document.createDocumentFragment();
            for (const record of titleRecords) {
                const option = document.createElement("option");
                option.value = record.title;
                fragment.appendChild(option);
            }
            datalist.appendChild(fragment);
            datasetPill.textContent = `${DATA.movieCount.toLocaleString()} movies, ${DATA.likedEdgeCount.toLocaleString()} liked edges`;
        }

        function edgeKey(a, b) {
            return a < b ? `${a}|${b}` : `${b}|${a}`;
        }

        function movieNodeId(movieId) {
            return `m${movieId}`;
        }

        function userNodeId(userId) {
            return `u${userId}`;
        }

        function radiusFor(node) {
            if (node.kind === "you") return 31;
            if (node.kind === "movie") {
                const count = state.recommendationCounts.get(node.movieId)?.count || 0;
                return Math.min(30, 18 + Math.sqrt(count) * 2.4 + (node.seed ? 4 : 0));
            }
            return 14;
        }

        function addNode(id, kind, label, options = {}) {
            const existing = state.nodes.get(id);
            if (existing) {
                Object.assign(existing, options);
                return existing;
            }
            const angle = options.angle ?? Math.random() * Math.PI * 2;
            const distance = options.distance ?? (kind === "movie" ? 170 : 240);
            const origin = options.origin || { x: state.viewWidth / 2, y: state.viewHeight / 2 };
            const node = {
                id,
                kind,
                label,
                x: options.x ?? origin.x + Math.cos(angle) * distance,
                y: options.y ?? origin.y + Math.sin(angle) * distance,
                vx: 0,
                vy: 0,
                seed: false,
                ...options
            };
            state.nodes.set(id, node);
            return node;
        }

        function addLink(source, target, kind = "taste") {
            const key = edgeKey(source, target);
            if (state.edgeKeys.has(key)) return false;
            state.edgeKeys.add(key);
            state.links.push({ source, target, kind, key });
            return true;
        }

        function resetGraph() {
            stopWalks();
            state.nodes.clear();
            state.links = [];
            state.edgeKeys.clear();
            state.seedMovieIds.clear();
            state.invalidRows.clear();
            state.recommendationCounts.clear();
            state.lastPaths.clear();
            state.highlightedNodes.clear();
            state.highlightedEdges.clear();
            state.discoveryInProgress = false;
            state.discoveryToken += 1;
            state.walkCount = 0;
            addNode("you", "you", "You", {
                x: state.viewWidth / 2,
                y: state.viewHeight / 2,
                fixed: true
            });
            graphStatus.innerHTML = 'Start by adding a MovieLens title, for example <strong>Toy Story (1995)</strong> or <strong>Matrix, The (1999)</strong>.';
            updateMetrics();
            updateRecommendationTable();
            updateWalkEligibility();
        }

        function clearInputs() {
            rowsContainer.innerHTML = "";
            state.rowId = 0;
            for (let i = 0; i < 4; i += 1) addMovieRow();
        }

        function setRowMessage(row, message, kind = "") {
            row.message.textContent = message;
            row.message.className = `row-message ${kind}`.trim();
            row.input.classList.toggle("invalid", kind === "error");
        }

        function addMovieRow(value = "") {
            const rowId = `row-${state.rowId += 1}`;
            const wrapper = document.createElement("div");
            wrapper.className = "movie-row";
            wrapper.dataset.rowId = rowId;

            const input = document.createElement("input");
            input.type = "text";
            input.placeholder = "Movie title";
            input.setAttribute("list", "movieTitles");
            input.value = value;
            input.autocomplete = "off";

            const button = document.createElement("button");
            button.type = "button";
            button.className = "arrow-button";
            button.textContent = "->";
            button.setAttribute("aria-label", "Add this movie to the graph");

            const message = document.createElement("div");
            message.className = "row-message";

            const row = { rowId, wrapper, input, button, message };
            input.addEventListener("input", () => {
                state.invalidRows.delete(rowId);
                setRowMessage(row, "", "");
                updateWalkEligibility();
            });
            input.addEventListener("keydown", (event) => {
                if (event.key === "Enter") {
                    event.preventDefault();
                    submitMovie(row);
                }
            });
            button.addEventListener("click", () => submitMovie(row));

            wrapper.append(input, button, message);
            rowsContainer.appendChild(wrapper);
        }

        function suggestionsFor(query, limit = 5) {
            const key = normalizeTitle(query);
            if (!key) return [];
            const exact = aliasMap.get(key);
            if (exact && exact.length) return exact.slice(0, limit).map(id => moviesById.get(id).title);
            const matches = [];
            const seen = new Set();
            for (const record of titleRecords) {
                if (record.searchText.includes(key) || key.includes(normalizeTitle(withoutYear(record.title)))) {
                    if (!seen.has(record.id)) {
                        seen.add(record.id);
                        matches.push(record.title);
                    }
                    if (matches.length >= limit) break;
                }
            }
            return matches;
        }

        function resolveMovie(query) {
            const key = normalizeTitle(query);
            if (!key) return { status: "empty" };
            const exact = aliasMap.get(key);
            if (exact && exact.length === 1) return { status: "ok", movie: moviesById.get(exact[0]) };
            if (exact && exact.length > 1) {
                return { status: "ambiguous", suggestions: exact.slice(0, 6).map(id => moviesById.get(id).title) };
            }
            const hits = [];
            const seen = new Set();
            for (const record of titleRecords) {
                if (record.searchText.includes(key)) {
                    if (!seen.has(record.id)) {
                        seen.add(record.id);
                        hits.push(record.id);
                    }
                    if (hits.length > 6) break;
                }
            }
            if (hits.length === 1) return { status: "ok", movie: moviesById.get(hits[0]) };
            if (hits.length > 1) return { status: "ambiguous", suggestions: hits.slice(0, 6).map(id => moviesById.get(id).title) };
            return { status: "unknown", suggestions: suggestionsFor(query, 5) };
        }

        function sampleArray(values, count, excluded = new Set()) {
            const pool = values.filter(value => !excluded.has(value));
            for (let i = pool.length - 1; i > 0; i -= 1) {
                const j = Math.floor(Math.random() * (i + 1));
                [pool[i], pool[j]] = [pool[j], pool[i]];
            }
            return pool.slice(0, count);
        }

        function sleep(ms) {
            return new Promise(resolve => window.setTimeout(resolve, ms));
        }

        function stepDelay() {
            return Math.round(620 / Number(speedControl.value));
        }

        async function submitMovie(row) {
            if (state.discoveryInProgress) return;
            const result = resolveMovie(row.input.value);
            if (result.status === "empty") {
                state.invalidRows.add(row.rowId);
                setRowMessage(row, "Type a MovieLens title first.", "error");
                updateWalkEligibility();
                return;
            }
            if (result.status === "unknown") {
                state.invalidRows.add(row.rowId);
                const suffix = result.suggestions.length ? ` Try: ${result.suggestions.join("; ")}` : "";
                setRowMessage(row, `Movie not found in MovieLens.${suffix}`, "error");
                updateWalkEligibility();
                return;
            }
            if (result.status === "ambiguous") {
                state.invalidRows.add(row.rowId);
                setRowMessage(row, `More than one match. Try: ${result.suggestions.join("; ")}`, "error");
                updateWalkEligibility();
                return;
            }

            state.invalidRows.delete(row.rowId);
            const movie = result.movie;
            row.input.value = movie.title;
            row.button.disabled = true;
            setRowMessage(row, "Adding movie and checking displayed users...", "ok");
            await addSeedMovie(movie, row);
            row.button.disabled = false;
            updateWalkEligibility();
        }

        async function addSeedMovie(movie, row) {
            const discoveryToken = state.discoveryToken + 1;
            state.discoveryToken = discoveryToken;
            const movieId = movie.id;
            const movieNode = addNode(movieNodeId(movieId), "movie", shortTitle(movie.title), {
                movieId,
                title: movie.title,
                seed: true,
                angle: (state.seedMovieIds.size / Math.max(1, state.seedMovieIds.size + 1)) * Math.PI * 2 - Math.PI / 2,
                distance: 150
            });
            movieNode.seed = true;
            state.seedMovieIds.add(movieId);
            addLink("you", movieNode.id, "seed");
            state.highlightedNodes = new Set(["you", movieNode.id]);
            state.highlightedEdges = new Set([edgeKey("you", movieNode.id)]);

            const likedUsers = likesByMovie.get(movieId) || [];
            updateMetrics();
            if (likedUsers.length === 0) {
                graphStatus.textContent = `${movie.title} is in MovieLens, but this demo has no 3.5+ ratings for it. Add another movie to make walks possible.`;
                setRowMessage(row, "Known title, but no liked-user edges at the 3.5 threshold.", "warn");
                await sleep(650);
                if (discoveryToken !== state.discoveryToken) return;
                state.highlightedNodes.clear();
                state.highlightedEdges.clear();
                return;
            }

            state.discoveryInProgress = true;
            updateWalkEligibility();
            const displayedUserIds = [...state.nodes.values()]
                .filter(node => node.kind === "user")
                .map(node => node.userId)
                .filter(userId => (likesByUser.get(userId) || []).includes(movieId));
            const chosen = [];
            const chosenSet = new Set();
            for (const userId of displayedUserIds) {
                if (chosen.length >= 10) break;
                chosen.push(userId);
                chosenSet.add(userId);
            }
            const randomRemainder = sampleArray(likedUsers, 10 - chosen.length, chosenSet);
            for (const userId of randomRemainder) {
                chosen.push(userId);
                chosenSet.add(userId);
            }

            const reused = displayedUserIds.length;
            graphStatus.textContent = `Found ${likedUsers.length.toLocaleString()} MovieLens users who liked ${movie.title}. Reusing ${Math.min(reused, chosen.length)} displayed users, then sampling the rest.`;

            for (let i = 0; i < chosen.length; i += 1) {
                const userId = chosen[i];
                const userNode = addNode(userNodeId(userId), "user", `User ${userId}`, {
                    userId,
                    origin: movieNode,
                    distance: 105 + Math.random() * 70,
                    angle: Math.random() * Math.PI * 2
                });
                addLink(userNode.id, movieNode.id, "taste");
                state.highlightedNodes = new Set([movieNode.id, userNode.id]);
                state.highlightedEdges = new Set([edgeKey(movieNode.id, userNode.id)]);
                updateMetrics();
                setRowMessage(row, `Linked ${i + 1} of ${chosen.length} users who liked this movie.`, "ok");
                await sleep(Math.max(90, stepDelay() * 0.38));
                if (discoveryToken !== state.discoveryToken) return;
            }

            if (discoveryToken !== state.discoveryToken) return;
            state.highlightedNodes.clear();
            state.highlightedEdges.clear();
            state.discoveryInProgress = false;
            setRowMessage(row, `Added ${movie.title} with ${chosen.length} liked-user links.`, "ok");
            graphStatus.textContent = `Ready: ${movie.title} is connected to You and ${chosen.length} users. Start random walks to see P3 recommendations.`;
            updateMetrics();
            updateWalkEligibility();
        }

        function displayedUsersForMovie(movieId) {
            const seedNodeId = movieNodeId(movieId);
            return [...state.nodes.values()].filter(node =>
                node.kind === "user" &&
                (likesByUser.get(node.userId) || []).includes(movieId) &&
                state.edgeKeys.has(edgeKey(seedNodeId, node.id))
            );
        }

        function walkableSeedMovieIds() {
            return [...state.seedMovieIds].filter(movieId => displayedUsersForMovie(movieId).length > 0);
        }

        function updateWalkEligibility() {
            const hasSeed = state.seedMovieIds.size > 0;
            const noInvalid = state.invalidRows.size === 0;
            startWalkButton.hidden = !(hasSeed && noInvalid);
            startWalkButton.disabled = state.running || state.discoveryInProgress || walkableSeedMovieIds().length === 0;
            stopWalkButton.disabled = !state.running;
        }

        function updateMetrics() {
            let movieCount = 0;
            let userCount = 0;
            for (const node of state.nodes.values()) {
                if (node.kind === "movie") movieCount += 1;
                if (node.kind === "user") userCount += 1;
            }
            movieMetric.textContent = movieCount.toLocaleString();
            userMetric.textContent = userCount.toLocaleString();
            walkMetric.textContent = state.walkCount.toLocaleString();
        }

        function startWalks() {
            if (state.running || walkableSeedMovieIds().length === 0) return;
            state.recommendationCounts.clear();
            state.lastPaths.clear();
            state.walkCount = 0;
            state.running = true;
            state.walkToken += 1;
            recommendationNote.textContent = "Counting this run only.";
            graphStatus.textContent = "Running P3 walks. Each highlighted path is You -> movie -> displayed user -> movie.";
            updateRecommendationTable();
            updateMetrics();
            updateWalkEligibility();
            runWalkLoop(state.walkToken);
        }

        function stopWalks() {
            if (!state.running) return;
            state.running = false;
            state.walkToken += 1;
            state.highlightedNodes.clear();
            state.highlightedEdges.clear();
            graphStatus.textContent = "Random walks stopped.";
            updateWalkEligibility();
        }

        function randomChoice(values) {
            return values[Math.floor(Math.random() * values.length)];
        }

        async function runWalkLoop(token) {
            while (state.running && token === state.walkToken) {
                await runSingleWalk(token);
                if (!state.running || token !== state.walkToken) break;
                await sleep(Math.max(120, stepDelay() * 0.55));
            }
        }

        async function runSingleWalk(token) {
            const seedIds = walkableSeedMovieIds();
            if (seedIds.length === 0) {
                stopWalks();
                graphStatus.textContent = "Add a movie with at least one liked-user edge before walking.";
                return;
            }

            const seedMovieId = randomChoice(seedIds);
            const seedMovie = moviesById.get(seedMovieId);
            const seedNodeId = movieNodeId(seedMovieId);
            const candidateUserNodes = displayedUsersForMovie(seedMovieId);
            if (candidateUserNodes.length === 0) return;
            const userNode = randomChoice(candidateUserNodes);
            const userId = userNode.userId;

            const userMovies = likesByUser.get(userId) || [];
            let nextMovieCandidates = userMovies.filter(movieId => !state.seedMovieIds.has(movieId));
            if (nextMovieCandidates.length === 0) nextMovieCandidates = userMovies.slice();
            if (nextMovieCandidates.length === 0) return;
            const nextMovieId = randomChoice(nextMovieCandidates);
            const nextMovie = moviesById.get(nextMovieId);
            const nextNode = addNode(movieNodeId(nextMovieId), "movie", shortTitle(nextMovie.title), {
                movieId: nextMovieId,
                title: nextMovie.title,
                seed: state.seedMovieIds.has(nextMovieId),
                origin: userNode,
                distance: 125 + Math.random() * 95,
                angle: Math.random() * Math.PI * 2
            });
            addLink(userNode.id, nextNode.id, "taste");

            const pathNodes = ["you", seedNodeId, userNode.id, nextNode.id];
            const firstEdge = edgeKey("you", seedNodeId);
            const secondEdge = edgeKey(seedNodeId, userNode.id);
            const thirdEdge = edgeKey(userNode.id, nextNode.id);

            state.highlightedNodes = new Set(["you", seedNodeId]);
            state.highlightedEdges = new Set([firstEdge]);
            graphStatus.textContent = `Hop 1: You -> ${seedMovie.title}`;
            await sleep(stepDelay());
            if (!state.running || token !== state.walkToken) return;

            state.highlightedNodes = new Set(["you", seedNodeId, userNode.id]);
            state.highlightedEdges = new Set([firstEdge, secondEdge]);
            graphStatus.textContent = `Hop 2: ${seedMovie.title} -> User ${userId}`;
            await sleep(stepDelay());
            if (!state.running || token !== state.walkToken) return;

            state.highlightedNodes = new Set(pathNodes);
            state.highlightedEdges = new Set([firstEdge, secondEdge, thirdEdge]);
            graphStatus.textContent = `Hop 3: User ${userId} -> ${nextMovie.title}`;
            if (!state.seedMovieIds.has(nextMovieId)) {
                const current = state.recommendationCounts.get(nextMovieId) || { count: 0, movie: nextMovie };
                current.count += 1;
                state.recommendationCounts.set(nextMovieId, current);
                state.lastPaths.set(nextMovieId, `${seedMovie.title} -> User ${userId}`);
            }
            state.walkCount += 1;
            updateMetrics();
            updateRecommendationTable();
            await sleep(Math.round(stepDelay() * 1.15));
            if (!state.running || token !== state.walkToken) return;

            state.highlightedNodes.clear();
            state.highlightedEdges.clear();
        }

        function updateRecommendationTable() {
            const rows = [...state.recommendationCounts.entries()]
                .sort((a, b) => b[1].count - a[1].count || a[1].movie.title.localeCompare(b[1].movie.title))
                .slice(0, 18);
            recommendationBody.innerHTML = "";
            if (rows.length === 0) {
                const row = document.createElement("tr");
                row.className = "empty-row";
                const cell = document.createElement("td");
                cell.colSpan = 3;
                cell.textContent = state.running ? "Waiting for the first non-seed recommendation..." : "Run random walks to build recommendations.";
                row.appendChild(cell);
                recommendationBody.appendChild(row);
                return;
            }
            for (const [movieId, entry] of rows) {
                const row = document.createElement("tr");
                const count = document.createElement("td");
                count.className = "count-cell";
                count.textContent = entry.count.toLocaleString();
                const title = document.createElement("td");
                title.textContent = entry.movie.title;
                const path = document.createElement("td");
                path.textContent = state.lastPaths.get(movieId) || "";
                row.append(count, title, path);
                recommendationBody.appendChild(row);
            }
        }

        function resizeCanvas() {
            const rect = canvas.getBoundingClientRect();
            const dpr = window.devicePixelRatio || 1;
            canvas.width = Math.max(1, Math.floor(rect.width * dpr));
            canvas.height = Math.max(1, Math.floor(rect.height * dpr));
            ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
            state.viewWidth = rect.width;
            state.viewHeight = rect.height;
            const you = state.nodes.get("you");
            if (you) {
                you.x = state.viewWidth / 2;
                you.y = state.viewHeight / 2;
            }
        }

        function tickPhysics() {
            const nodes = [...state.nodes.values()];
            const width = state.viewWidth;
            const height = state.viewHeight;
            const centerX = width / 2;
            const centerY = height / 2;

            for (let i = 0; i < nodes.length; i += 1) {
                const a = nodes[i];
                for (let j = i + 1; j < nodes.length; j += 1) {
                    const b = nodes[j];
                    let dx = b.x - a.x;
                    let dy = b.y - a.y;
                    let distSq = dx * dx + dy * dy;
                    if (distSq < 0.01) {
                        dx = Math.random() - 0.5;
                        dy = Math.random() - 0.5;
                        distSq = dx * dx + dy * dy;
                    }
                    const dist = Math.sqrt(distSq);
                    const minDist = radiusFor(a) + radiusFor(b) + 28;
                    const strength = Math.min(2.4, 2200 / Math.max(90, distSq));
                    const overlapBoost = dist < minDist ? (minDist - dist) * 0.012 : 0;
                    const fx = (dx / dist) * (strength + overlapBoost);
                    const fy = (dy / dist) * (strength + overlapBoost);
                    if (!a.fixed) {
                        a.vx -= fx;
                        a.vy -= fy;
                    }
                    if (!b.fixed) {
                        b.vx += fx;
                        b.vy += fy;
                    }
                }
            }

            for (const link of state.links) {
                const source = state.nodes.get(link.source);
                const target = state.nodes.get(link.target);
                if (!source || !target) continue;
                const dx = target.x - source.x;
                const dy = target.y - source.y;
                const dist = Math.max(1, Math.sqrt(dx * dx + dy * dy));
                const ideal = link.kind === "seed" ? 150 : 112;
                const force = (dist - ideal) * (link.kind === "seed" ? 0.012 : 0.018);
                const fx = (dx / dist) * force;
                const fy = (dy / dist) * force;
                if (!source.fixed) {
                    source.vx += fx;
                    source.vy += fy;
                }
                if (!target.fixed) {
                    target.vx -= fx;
                    target.vy -= fy;
                }
            }

            for (const node of nodes) {
                if (node.fixed) {
                    node.x = centerX;
                    node.y = centerY;
                    node.vx = 0;
                    node.vy = 0;
                    continue;
                }
                const pull = node.kind === "movie" ? 0.0009 : 0.00065;
                node.vx += (centerX - node.x) * pull;
                node.vy += (centerY - node.y) * pull;
                node.vx *= 0.86;
                node.vy *= 0.86;
                node.x += node.vx;
                node.y += node.vy;
                const r = radiusFor(node) + 8;
                node.x = Math.max(r, Math.min(width - r, node.x));
                node.y = Math.max(r, Math.min(height - r, node.y));
            }
        }

        function drawWrappedLabel(text, x, y, maxWidth, lineHeight, maxLines) {
            const words = text.split(/\s+/);
            const lines = [];
            let current = "";
            for (const word of words) {
                const test = current ? `${current} ${word}` : word;
                if (ctx.measureText(test).width <= maxWidth || !current) {
                    current = test;
                } else {
                    lines.push(current);
                    current = word;
                }
                if (lines.length === maxLines) break;
            }
            if (current && lines.length < maxLines) lines.push(current);
            if (words.length && lines.length === maxLines) {
                const last = lines[lines.length - 1];
                if (ctx.measureText(words.join(" ")).width > maxWidth * maxLines) {
                    lines[lines.length - 1] = last.length > 16 ? `${last.slice(0, 15)}...` : last;
                }
            }
            const startY = y - ((lines.length - 1) * lineHeight) / 2;
            lines.forEach((line, index) => ctx.fillText(line, x, startY + index * lineHeight));
        }

        function drawGraph() {
            ctx.clearRect(0, 0, state.viewWidth, state.viewHeight);
            tickPhysics();

            ctx.save();
            ctx.lineCap = "round";
            for (const link of state.links) {
                const source = state.nodes.get(link.source);
                const target = state.nodes.get(link.target);
                if (!source || !target) continue;
                const active = state.highlightedEdges.has(link.key);
                ctx.beginPath();
                ctx.moveTo(source.x, source.y);
                ctx.lineTo(target.x, target.y);
                ctx.strokeStyle = active ? "rgba(2, 132, 199, 0.95)" : (link.kind === "seed" ? "rgba(15, 118, 110, 0.36)" : "rgba(71, 85, 105, 0.24)");
                ctx.lineWidth = active ? 5 : (link.kind === "seed" ? 2.2 : 1.35);
                ctx.stroke();
            }
            ctx.restore();

            const nodes = [...state.nodes.values()].sort((a, b) => {
                const order = { user: 0, movie: 1, you: 2 };
                return order[a.kind] - order[b.kind];
            });

            for (const node of nodes) {
                const active = state.highlightedNodes.has(node.id);
                const radius = radiusFor(node);
                let fill = "#a78bfa";
                let stroke = "rgba(76, 29, 149, 0.55)";
                if (node.kind === "movie") {
                    fill = node.seed ? "#f59e0b" : "#38bdf8";
                    stroke = node.seed ? "rgba(180, 83, 9, 0.65)" : "rgba(2, 132, 199, 0.58)";
                }
                if (node.kind === "you") {
                    fill = "#14b8a6";
                    stroke = "rgba(15, 118, 110, 0.78)";
                }

                ctx.save();
                if (active) {
                    ctx.beginPath();
                    ctx.arc(node.x, node.y, radius + 9, 0, Math.PI * 2);
                    ctx.fillStyle = "rgba(56, 189, 248, 0.22)";
                    ctx.fill();
                }
                ctx.beginPath();
                ctx.arc(node.x, node.y, radius, 0, Math.PI * 2);
                ctx.fillStyle = fill;
                ctx.fill();
                ctx.lineWidth = active ? 4 : 2;
                ctx.strokeStyle = active ? "#0284c7" : stroke;
                ctx.stroke();

                ctx.fillStyle = node.kind === "movie" && !node.seed ? "#082f49" : "#ffffff";
                ctx.textAlign = "center";
                ctx.textBaseline = "middle";
                ctx.font = node.kind === "you" ? "700 16px system-ui, sans-serif" : "700 11px system-ui, sans-serif";
                const label = node.kind === "user" ? `U${node.userId}` : node.label;
                drawWrappedLabel(label, node.x, node.y, radius * 1.55, node.kind === "you" ? 17 : 12, node.kind === "movie" ? 2 : 1);

                if (node.kind === "movie") {
                    const entry = state.recommendationCounts.get(node.movieId);
                    if (entry && entry.count > 0) {
                        ctx.beginPath();
                        ctx.arc(node.x + radius * 0.72, node.y - radius * 0.72, 10, 0, Math.PI * 2);
                        ctx.fillStyle = "#0f172a";
                        ctx.fill();
                        ctx.fillStyle = "#f8fafc";
                        ctx.font = "700 10px system-ui, sans-serif";
                        ctx.fillText(String(Math.min(99, entry.count)), node.x + radius * 0.72, node.y - radius * 0.72);
                    }
                }
                ctx.restore();
            }

            state.animationFrame = window.requestAnimationFrame(drawGraph);
        }

        function updateSpeedReadout() {
            speedReadout.textContent = `${Number(speedControl.value).toFixed(2).replace(/\.00$/, "")}x`;
        }

        function init() {
            buildDataIndexes();
            resizeCanvas();
            resetGraph();
            clearInputs();
            updateSpeedReadout();
            window.addEventListener("resize", resizeCanvas);
            addRowButton.addEventListener("click", () => addMovieRow());
            clearGraphButton.addEventListener("click", () => {
                resetGraph();
                clearInputs();
                recommendationNote.textContent = "Cleared every time random walks start.";
            });
            startWalkButton.addEventListener("click", startWalks);
            stopWalkButton.addEventListener("click", stopWalks);
            speedControl.addEventListener("input", updateSpeedReadout);
            drawGraph();
        }

        init();
    })();
    </script>
</body>
</html>
"""


def build_payload(dataset_dir: Path) -> dict:
    movies_path = dataset_dir / "movies.csv"
    ratings_path = dataset_dir / "ratings.csv"
    if not movies_path.exists() or not ratings_path.exists():
        raise SystemExit(
            f"Expected movies.csv and ratings.csv in {dataset_dir}. "
            f"Download and unzip {DATASET_URL} first."
        )

    movies: list[list[object]] = []
    movie_ids: set[int] = set()
    with movies_path.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            movie_id = int(row["movieId"])
            movie_ids.add(movie_id)
            movies.append([movie_id, row["title"], row["genres"]])

    likes_by_movie: dict[int, list[int]] = {}
    rating_count = 0
    liked_edge_count = 0
    with ratings_path.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            rating_count += 1
            rating = float(row["rating"])
            if rating < LIKED_THRESHOLD:
                continue
            movie_id = int(row["movieId"])
            if movie_id not in movie_ids:
                continue
            user_id = int(row["userId"])
            likes_by_movie.setdefault(movie_id, []).append(user_id)
            liked_edge_count += 1

    compact_likes = {
        str(movie_id): sorted(set(user_ids))
        for movie_id, user_ids in sorted(likes_by_movie.items())
    }

    return {
        "source": DATASET_URL,
        "dataset": "MovieLens ml-latest-small",
        "datasetGenerated": "2018-09-26",
        "likedThreshold": LIKED_THRESHOLD,
        "movieCount": len(movies),
        "ratingCount": rating_count,
        "likedEdgeCount": liked_edge_count,
        "movies": movies,
        "likesByMovie": compact_likes,
    }


def main(argv: list[str]) -> int:
    if len(argv) not in {2, 3}:
        print(
            "Usage: tools/build_p3_game.py <path-to-ml-latest-small> "
            "[output-html]",
            file=sys.stderr,
        )
        return 2

    dataset_dir = Path(argv[1]).expanduser().resolve()
    output = Path(argv[2] if len(argv) == 3 else "p3-recommendation-engine.html").resolve()
    payload = build_payload(dataset_dir)
    data_json = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    output.write_text(HTML_TEMPLATE.replace("__MOVIELENS_DATA__", data_json), encoding="utf-8")
    print(f"Wrote {output}")
    print(
        f"Embedded {payload['movieCount']} movies and "
        f"{payload['likedEdgeCount']} liked edges from {payload['ratingCount']} ratings."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
