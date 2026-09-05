/**
 * NeoFinesse Phase 8 Demo & Audit UI Engine
 * Reactive State Manager, SVG Provenance Graph Renderer, Evidence Inspector, and Demo Stepper.
 */

(function () {
  'use strict';

  // Application State
  const state = {
    data: null,
    activeTab: 'dashboard',
    activeScenarioId: 'VAR-001_REFUND_VARIANCE',
    activeDemoId: 'demo_1',
    selectedEvidence: null,
    searchFilter: '',
    statusFilter: 'ALL',
  };

  // DOM Element Selectors
  const elements = {
    demoBanner: document.getElementById('demo-banner'),
    demoPills: document.querySelectorAll('.demo-pill'),
    navTabs: document.querySelectorAll('.tab-btn'),
    viewPanels: document.querySelectorAll('.view-panel'),
    caseTableBody: document.getElementById('case-table-body'),
    searchInput: document.getElementById('search-cases-input'),
    filterBtns: document.querySelectorAll('.filter-btn'),
    // KPI elements
    kpiSettlements: document.getElementById('kpi-total-settlements'),
    kpiVariances: document.getElementById('kpi-total-variances'),
    kpiResolved: document.getElementById('kpi-resolved-count'),
    kpiEscalated: document.getElementById('kpi-escalated-count'),
    kpiFalseClosure: document.getElementById('kpi-false-closure-rate'),
    kpiEvidenceCoverage: document.getElementById('kpi-evidence-coverage'),
    // Investigation View elements
    currentCaseBadge: document.getElementById('current-case-badge'),
    graphSvg: document.getElementById('provenance-svg-container'),
    evidenceDrawer: document.getElementById('evidence-drawer-content'),
    // AI vs Verifier elements
    aiHypothesisText: document.getElementById('ai-hypothesis-text'),
    aiToolsList: document.getElementById('ai-tools-list'),
    verifierVerdictBadge: document.getElementById('verifier-verdict-badge'),
    verifierChecklist: document.getElementById('verifier-constraints-list'),
    // Escalation View elements
    escalationCaseId: document.getElementById('escalation-case-id'),
    escalationVariance: document.getElementById('escalation-variance-amount'),
    escalationReason: document.getElementById('escalation-reason-text'),
    escalationChecklist: document.getElementById('escalation-checklist'),
    escalationAction: document.getElementById('escalation-action-text'),
  };

  // Initialize App
  async function init() {
    setupEventListeners();
    await loadData();
    renderAll();
  }

  // Load Data from API or embedded payload
  async function loadData() {
    try {
      const response = await fetch('/api/data');
      if (response.ok) {
        state.data = await response.json();
      } else {
        throw new Error('API fetch failed, checking embedded data');
      }
    } catch (err) {
      console.warn('Loading fallback embedded dataset:', err);
      if (window.__NEOFINESSE_DATA__) {
        state.data = window.__NEOFINESSE_DATA__;
      }
    }
  }

  // Event Listeners
  function setupEventListeners() {
    // Navigation tabs
    elements.navTabs.forEach((tab) => {
      tab.addEventListener('click', (e) => {
        const targetView = tab.getAttribute('data-view');
        switchView(targetView);
      });
    });

    // Demo pills
    elements.demoPills.forEach((pill) => {
      pill.addEventListener('click', () => {
        const demoId = pill.getAttribute('data-demo');
        switchDemo(demoId);
      });
    });

    // Search and filter
    if (elements.searchInput) {
      elements.searchInput.addEventListener('input', (e) => {
        state.searchFilter = e.target.value.toLowerCase();
        renderCaseTable();
      });
    }

    elements.filterBtns.forEach((btn) => {
      btn.addEventListener('click', () => {
        elements.filterBtns.forEach((b) => b.classList.remove('active'));
        btn.classList.add('active');
        state.statusFilter = btn.getAttribute('data-filter');
        renderCaseTable();
      });
    });
  }

  // View Switcher
  function switchView(viewName) {
    state.activeTab = viewName;
    elements.navTabs.forEach((tab) => {
      tab.classList.toggle('active', tab.getAttribute('data-view') === viewName);
    });
    elements.viewPanels.forEach((panel) => {
      panel.classList.toggle('active', panel.id === `view-${viewName}`);
    });

    if (viewName === 'graph') {
      renderInvestigationGraph();
    }
  }

  // Demo Case Switcher
  function switchDemo(demoId) {
    state.activeDemoId = demoId;
    elements.demoPills.forEach((p) => p.classList.toggle('active', p.getAttribute('data-demo') === demoId));

    const demo = state.data?.demo_cases?.find((d) => d.demo_id === demoId);
    if (demo) {
      state.activeScenarioId = demo.scenario_id;
      renderDemoBanner(demo);
      renderInvestigationGraph();
      renderAIVsVerifier();
      renderEscalationView();
    }
  }

  // Render All Views
  function renderAll() {
    if (!state.data) return;

    renderKPIs();
    renderCaseTable();
    const activeDemo = state.data.demo_cases?.find((d) => d.demo_id === state.activeDemoId);
    if (activeDemo) renderDemoBanner(activeDemo);
    renderInvestigationGraph();
    renderAIVsVerifier();
    renderEscalationView();
  }

  // 1. Render Dashboard KPIs
  function renderKPIs() {
    const kpis = state.data.kpis;
    if (!kpis) return;

    if (elements.kpiSettlements) elements.kpiSettlements.textContent = kpis.total_settlements;
    if (elements.kpiVariances) elements.kpiVariances.textContent = kpis.total_variances;
    if (elements.kpiResolved) elements.kpiResolved.textContent = `${kpis.resolved_count} (${Math.round((kpis.resolved_count / kpis.total_variances) * 100)}%)`;
    if (elements.kpiEscalated) elements.kpiEscalated.textContent = `${kpis.escalated_count} (${Math.round((kpis.escalated_count / kpis.total_variances) * 100)}%)`;
    if (elements.kpiFalseClosure) elements.kpiFalseClosure.textContent = `${kpis.false_closure_rate_pct.toFixed(1)}%`;
    if (elements.kpiEvidenceCoverage) elements.kpiEvidenceCoverage.textContent = `${kpis.evidence_coverage_pct.toFixed(0)}%`;
  }

  // 2. Render Demo Banner
  function renderDemoBanner(demo) {
    if (!elements.demoBanner) return;
    elements.demoBanner.innerHTML = `
      <div class="demo-banner-content">
        <h3><span>🎯</span> ${demo.title} — ${demo.subtitle}</h3>
        <p>${demo.core_lesson}</p>
      </div>
      <div class="demo-banner-tag">
        <strong>${demo.case_id}</strong> &bull; Variance: ${demo.variance_display}
      </div>
    `;
  }

  // 3. Render Case Table
  function renderCaseTable() {
    if (!elements.caseTableBody || !state.data?.scenarios) return;

    let filtered = state.data.scenarios;

    // Apply Search
    if (state.searchFilter) {
      filtered = filtered.filter(
        (s) =>
          s.case_id.toLowerCase().includes(state.searchFilter) ||
          s.scenario_id.toLowerCase().includes(state.searchFilter) ||
          s.settlement_id.toLowerCase().includes(state.searchFilter) ||
          s.primary_cause.toLowerCase().includes(state.searchFilter)
      );
    }

    // Apply Status Filter
    if (state.statusFilter !== 'ALL') {
      filtered = filtered.filter((s) => s.expected_outcome === state.statusFilter);
    }

    elements.caseTableBody.innerHTML = filtered
      .map((s) => {
        const badgeClass =
          s.expected_outcome === 'RESOLVED' || s.expected_outcome === 'VALID_DELAYED_CREDIT'
            ? 'resolved'
            : s.expected_outcome === 'PARTIALLY_RESOLVED'
            ? 'partial'
            : 'escalated';

        const varFormatted = s.variance_inr < 0 ? `-₹${Math.abs(s.variance_inr).toFixed(2)}` : `+₹${s.variance_inr.toFixed(2)}`;

        return `
        <tr>
          <td><strong style="color: var(--cyan-primary);">${s.case_id}</strong></td>
          <td><span style="font-family: var(--font-mono); font-size: 0.75rem;">${s.scenario_id}</span></td>
          <td><span style="font-family: var(--font-mono);">${s.settlement_id}</span></td>
          <td>₹${s.expected_amount_inr.toFixed(2)}</td>
          <td>₹${s.actual_bank_credit_inr.toFixed(2)}</td>
          <td><strong style="color: ${s.variance_inr < 0 ? 'var(--rose-primary)' : 'var(--emerald-primary)'}; font-family: var(--font-mono);">${varFormatted}</strong></td>
          <td><span class="badge ${badgeClass}">${s.expected_outcome}</span></td>
          <td><span style="font-size: 0.75rem;">${s.primary_cause}</span></td>
          <td><span class="badge verified">${s.evidence_level}</span></td>
          <td>
            <button class="btn-inspect" data-scenario="${s.scenario_id}">Inspect</button>
          </td>
        </tr>
      `;
      })
      .join('');

    // Attach inspect button handlers
    elements.caseTableBody.querySelectorAll('.btn-inspect').forEach((btn) => {
      btn.addEventListener('click', (e) => {
        const scenId = btn.getAttribute('data-scenario');
        selectScenario(scenId);
        switchView('graph');
      });
    });
  }

  // Select Scenario Helper
  function selectScenario(scenId) {
    state.activeScenarioId = scenId;
    const scenario = state.data?.scenarios?.find((s) => s.scenario_id === scenId);
    if (scenario) {
      if (elements.currentCaseBadge) {
        elements.currentCaseBadge.textContent = `${scenario.case_id} (${scenario.scenario_id})`;
      }
      renderInvestigationGraph();
      renderAIVsVerifier();
      renderEscalationView();
    }
  }

  // 4. Render Flagship Interactive SVG Provenance Graph
  function renderInvestigationGraph() {
    if (!elements.graphSvg || !state.data?.scenarios) return;

    const scenario = state.data.scenarios.find((s) => s.scenario_id === state.activeScenarioId) || state.data.scenarios[0];
    if (!scenario) return;

    if (elements.currentCaseBadge) {
      elements.currentCaseBadge.textContent = `${scenario.case_id} — ${scenario.scenario_id}`;
    }

    const width = 880;
    const height = 500;

    const rootX = 440;
    const rootY = 60;

    const verifiedEvents = scenario.evidence_nodes || [];
    const decoyEvents = scenario.rejected_decoys || [];
    const allCandidateEvents = [...verifiedEvents, ...decoyEvents];

    let svgHtml = `
      <svg class="provenance-svg" viewBox="0 0 ${width} ${height}" xmlns="http://www.w3.org/2000/svg">
        <defs>
          <filter id="glow-emerald" x="-20%" y="-20%" width="140%" height="140%">
            <feDropShadow dx="0" dy="0" stdDeviation="6" flood-color="#10B981" flood-opacity="0.6"/>
          </filter>
          <filter id="glow-cyan" x="-20%" y="-20%" width="140%" height="140%">
            <feDropShadow dx="0" dy="0" stdDeviation="6" flood-color="#06B6D4" flood-opacity="0.6"/>
          </filter>
          <filter id="glow-rose" x="-20%" y="-20%" width="140%" height="140%">
            <feDropShadow dx="0" dy="0" stdDeviation="6" flood-color="#EF4444" flood-opacity="0.6"/>
          </filter>
          <filter id="glow-amber" x="-20%" y="-20%" width="140%" height="140%">
            <feDropShadow dx="0" dy="0" stdDeviation="6" flood-color="#F59E0B" flood-opacity="0.6"/>
          </filter>
        </defs>
    `;

    // Root Node: Settlement Variance
    const varDisplay = scenario.variance_inr < 0 ? `-₹${Math.abs(scenario.variance_inr).toFixed(2)}` : `+₹${scenario.variance_inr.toFixed(2)}`;
    svgHtml += `
      <!-- ROOT NODE: SETTLEMENT VARIANCE -->
      <g class="svg-node" data-node="root" onclick="window.inspectNode('root')">
        <rect x="${rootX - 120}" y="${rootY - 30}" width="240" height="60" rx="10" 
              fill="#1E293B" stroke="#F59E0B" stroke-width="2" filter="url(#glow-amber)" />
        <text x="${rootX}" y="${rootY - 6}" text-anchor="middle" fill="#94A3B8" font-size="11" font-weight="600" letter-spacing="1">SETTLEMENT VARIANCE</text>
        <text x="${rootX}" y="${rootY + 18}" text-anchor="middle" fill="#F8FAFC" font-size="16" font-weight="800" font-family="'JetBrains Mono', monospace">${varDisplay}</text>
      </g>
    `;

    // Candidate Event Nodes Layer (Y = 190)
    const eventY = 190;
    const numEvents = allCandidateEvents.length;
    const spacing = numEvents > 1 ? 560 / (numEvents - 1) : 0;
    const startX = numEvents > 1 ? 160 : 440;

    allCandidateEvents.forEach((ev, idx) => {
      const evX = numEvents > 1 ? startX + idx * spacing : 440;
      const isRejected = ev.status === 'REJECTED';
      const strokeColor = isRejected ? '#EF4444' : '#10B981';
      const glowFilter = isRejected ? 'url(#glow-rose)' : 'url(#glow-emerald)';
      const dashArray = isRejected ? '5,5' : 'none';

      // Connector from Root to Event
      svgHtml += `
        <line x1="${rootX}" y1="${rootY + 30}" x2="${evX}" y2="${eventY - 30}" 
              stroke="${strokeColor}" stroke-width="2" stroke-dasharray="${dashArray}" opacity="0.85" />
      `;

      // Event Card
      const amountText = ev.amount_inr < 0 ? `-₹${Math.abs(ev.amount_inr).toFixed(2)}` : `₹${ev.amount_inr.toFixed(2)}`;
      const nodeKey = isRejected ? `decoy_${idx}` : `ev_${idx}`;

      svgHtml += `
        <g class="svg-node ${isRejected ? 'rejected' : 'verified'}" data-ev-id="${ev.evidence_id}" onclick="window.inspectEvidence('${ev.evidence_id}')">
          <rect x="${evX - 95}" y="${eventY - 30}" width="190" height="60" rx="8" 
                fill="#0F172A" stroke="${strokeColor}" stroke-width="2" filter="${glowFilter}" />
          <text x="${evX}" y="${eventY - 10}" text-anchor="middle" fill="${isRejected ? '#EF4444' : '#10B981'}" font-size="10" font-weight="700">
            ${isRejected ? '✗ DECOY REJECTED' : '✓ ' + ev.entity_type}
          </text>
          <text x="${evX}" y="${eventY + 12}" text-anchor="middle" fill="#FFFFFF" font-size="13" font-weight="800" font-family="'JetBrains Mono', monospace">
            ${amountText}
          </text>
          <text x="${evX}" y="${eventY + 24}" text-anchor="middle" fill="#64748B" font-size="9" font-family="'JetBrains Mono', monospace">
            ${ev.evidence_id} &bull; ${ev.evidence_level}
          </text>
        </g>
      `;
    });

    // Verifier Constraint Adder Layer (Y = 320)
    const verifierY = 320;
    const verifierX = 440;
    const isApproved = scenario.expected_outcome !== 'ESCALATE';
    const verifierColor = isApproved ? '#06B6D4' : '#EF4444';
    const verifierFilter = isApproved ? 'url(#glow-cyan)' : 'url(#glow-rose)';

    // Connect verified events to Verifier Constraint Node
    allCandidateEvents.forEach((ev, idx) => {
      const evX = numEvents > 1 ? startX + idx * spacing : 440;
      const isRejected = ev.status === 'REJECTED';
      if (!isRejected) {
        svgHtml += `
          <line x1="${evX}" y1="${eventY + 30}" x2="${verifierX}" y2="${verifierY - 25}" 
                stroke="#06B6D4" stroke-width="2" opacity="0.85" />
        `;
      }
    });

    svgHtml += `
      <!-- DETERMINISTIC VERIFIER CONSTRAINT NODE -->
      <g class="svg-node" onclick="window.inspectNode('verifier')">
        <rect x="${verifierX - 140}" y="${verifierY - 25}" width="280" height="50" rx="8" 
              fill="#111827" stroke="${verifierColor}" stroke-width="2" filter="${verifierFilter}" />
        <text x="${verifierX}" y="${verifierY - 4}" text-anchor="middle" fill="${verifierColor}" font-size="10" font-weight="700" letter-spacing="1">
          DETERMINISTIC FINANCIAL VERIFIER
        </text>
        <text x="${verifierX}" y="${verifierY + 14}" text-anchor="middle" fill="#FFFFFF" font-size="11" font-weight="600">
          5 / 5 Constraints Evaluated
        </text>
      </g>
    `;

    // Terminal Decision Node (Y = 440)
    const termY = 440;
    const termColor = isApproved ? '#10B981' : '#EF4444';
    const termFilter = isApproved ? 'url(#glow-emerald)' : 'url(#glow-rose)';

    svgHtml += `
      <line x1="${verifierX}" y1="${verifierY + 25}" x2="${verifierX}" y2="${termY - 25}" 
            stroke="${termColor}" stroke-width="2" opacity="0.9" />

      <!-- TERMINAL OUTCOME NODE -->
      <g class="svg-node">
        <rect x="${verifierX - 110}" y="${termY - 25}" width="220" height="50" rx="25" 
              fill="#080C14" stroke="${termColor}" stroke-width="2" filter="${termFilter}" />
        <text x="${verifierX}" y="${termY - 4}" text-anchor="middle" fill="#94A3B8" font-size="9" font-weight="700" letter-spacing="1">
          TERMINAL DECISION
        </text>
        <text x="${verifierX}" y="${termY + 15}" text-anchor="middle" fill="${termColor}" font-size="14" font-weight="800">
          ${isApproved ? '✓ ' + scenario.expected_outcome : '🚨 ESCALATE TO HUMAN'}
        </text>
      </g>
    `;

    svgHtml += `</svg>`;
    elements.graphSvg.innerHTML = svgHtml;

    // Default select first verified evidence in drawer
    if (verifiedEvents.length > 0) {
      renderEvidenceDrawer(verifiedEvents[0]);
    } else if (decoyEvents.length > 0) {
      renderEvidenceDrawer(decoyEvents[0]);
    }
  }

  // 5. Render Cell-Level Evidence Inspector Drawer
  function renderEvidenceDrawer(evidenceItem) {
    if (!elements.evidenceDrawer || !evidenceItem) return;

    const isRejected = evidenceItem.status === 'REJECTED';
    const badgeColor = isRejected ? 'escalated' : 'resolved';

    elements.evidenceDrawer.innerHTML = `
      <div class="evidence-prop-group">
        <div class="evidence-prop-label">Evidence Identifier & Level</div>
        <div class="evidence-prop-value">
          <strong style="color: var(--cyan-primary);">${evidenceItem.evidence_id}</strong> 
          &bull; <span class="badge verified">${evidenceItem.evidence_level} (Cell-Level Provenance)</span>
        </div>
      </div>

      <div class="evidence-prop-group">
        <div class="evidence-prop-label">Entity & Amount</div>
        <div class="evidence-prop-value mono">
          ${evidenceItem.entity_type} &bull; <strong style="color: ${isRejected ? 'var(--rose-primary)' : 'var(--emerald-primary)'};">${evidenceItem.amount_inr < 0 ? `-₹${Math.abs(evidenceItem.amount_inr).toFixed(2)}` : `₹${evidenceItem.amount_inr.toFixed(2)}`}</strong>
        </div>
      </div>

      <div class="evidence-prop-group">
        <div class="evidence-prop-label">Relational Path</div>
        <div class="evidence-prop-value" style="font-size: 0.775rem; color: var(--text-secondary);">
          ${evidenceItem.relationship_path}
        </div>
      </div>

      <div class="evidence-prop-group">
        <div class="evidence-prop-label">Excel / CSV File Coordinate</div>
        <div class="evidence-prop-value" style="display: flex; gap: 0.5rem; align-items: center; flex-wrap: wrap;">
          <span class="cell-coordinate-badge">📄 ${evidenceItem.source_file}</span>
          <span class="cell-coordinate-badge">Sheet: ${evidenceItem.sheet}</span>
          <span class="cell-coordinate-badge" style="background: rgba(43, 89, 209, 0.2); color: var(--cyan-primary); font-weight: 700;">Cell: ${evidenceItem.cell}</span>
          <button class="btn btn-secondary" style="padding: 0.25rem 0.6rem; font-size: 0.725rem;" onclick='window.openSourceEvidenceModal(${JSON.stringify(evidenceItem)})'>
            📊 View Source Context
          </button>
        </div>
      </div>

      <div class="evidence-prop-group">
        <div class="evidence-prop-label">SHA-256 Cryptographic Record Hash</div>
        <div class="hash-container">
          <span id="hash-text">${evidenceItem.record_hash}</span>
          <button onclick="window.copyHash('${evidenceItem.record_hash}')" title="Copy Hash">📋</button>
        </div>
      </div>

      ${
        isRejected
          ? `
        <div class="evidence-prop-group" style="margin-top: 1rem; padding: 0.75rem; background: var(--rose-bg); border: 1px solid var(--rose-border); border-radius: var(--radius-sm);">
          <div class="evidence-prop-label" style="color: var(--rose-primary);">Rejection Reason & Core Lesson</div>
          <div class="evidence-prop-value" style="font-size: 0.775rem; color: var(--text-primary); margin-bottom: 0.35rem;">
            <strong>${evidenceItem.rejection_reason}</strong>
          </div>
          <div style="font-size: 0.725rem; color: var(--text-secondary); font-style: italic;">
            💡 ${evidenceItem.lesson}
          </div>
        </div>
      `
          : `
        <div class="evidence-prop-group" style="margin-top: 1rem; padding: 0.75rem; background: var(--emerald-bg); border: 1px solid var(--emerald-border); border-radius: var(--radius-sm);">
          <div class="evidence-prop-label" style="color: var(--emerald-primary);">Verification Note</div>
          <div class="evidence-prop-value" style="font-size: 0.775rem; color: var(--text-primary);">
            ${evidenceItem.description}
          </div>
        </div>
      `
      }
    `;
  }

  // 6. Render AI Investigator vs Deterministic Verifier Panel
  function renderAIVsVerifier() {
    if (!state.data?.scenarios) return;

    const scenario = state.data.scenarios.find((s) => s.scenario_id === state.activeScenarioId) || state.data.scenarios[0];
    if (!scenario) return;

    // AI Investigator side
    if (elements.aiHypothesisText) {
      elements.aiHypothesisText.textContent = scenario.ai_hypothesis.proposed_explanation;
    }

    if (elements.aiToolsList) {
      elements.aiToolsList.innerHTML = scenario.ai_hypothesis.tools_requested.map((t) => `<li><code>${t}</code></li>`).join('');
    }

    // Verifier side
    if (elements.verifierVerdictBadge) {
      const isApproved = scenario.verifier_outcome.verdict === 'APPROVED';
      elements.verifierVerdictBadge.className = `badge ${isApproved ? 'resolved' : 'escalated'}`;
      elements.verifierVerdictBadge.textContent = scenario.verifier_outcome.verdict;
    }

    if (elements.verifierChecklist) {
      elements.verifierChecklist.innerHTML = scenario.constraint_checks
        .map((c) => {
          const isPass = c.status === 'PASS';
          return `
          <li class="constraint-item ${isPass ? 'pass' : 'fail'}">
            <span class="constraint-icon">${isPass ? '✓' : '✗'}</span>
            <div class="constraint-text">
              <h4>${c.name} [${c.rule}]</h4>
              <p>${c.description}</p>
            </div>
          </li>
        `;
        })
        .join('');
    }
  }

  // 7. Render Escalation View
  function renderEscalationView() {
    if (!state.data?.scenarios) return;

    const scenario = state.data.scenarios.find((s) => s.scenario_id === state.activeScenarioId) || state.data.scenarios[0];
    if (!scenario) return;

    if (elements.escalationCaseId) {
      elements.escalationCaseId.textContent = `${scenario.case_id} (${scenario.scenario_id})`;
    }

    if (elements.escalationVariance) {
      const v = scenario.variance_inr;
      elements.escalationVariance.textContent = v < 0 ? `-₹${Math.abs(v).toFixed(2)}` : `+₹${v.toFixed(2)}`;
    }

    if (elements.escalationReason) {
      elements.escalationReason.textContent = scenario.escalation_info
        ? scenario.escalation_info.escalation_reason
        : 'All 5 financial constraints were verified. Case resolved without escalation.';
    }

    if (elements.escalationChecklist) {
      if (scenario.escalation_info) {
        elements.escalationChecklist.innerHTML = scenario.escalation_info.rejection_summary.map((item) => `<li>${item}</li>`).join('');
      } else {
        elements.escalationChecklist.innerHTML = `<li style="color: var(--emerald-primary);">✓ All causal and monetary constraints passed</li>`;
      }
    }

    if (elements.escalationAction) {
      elements.escalationAction.textContent = scenario.escalation_info
        ? scenario.escalation_info.recommended_action
        : 'Case closed. No human intervention required.';
    }
  }

  // Global window helpers for SVG node clicks & copy actions
  window.inspectEvidence = function (evidenceId) {
    const scenario = state.data?.scenarios?.find((s) => s.scenario_id === state.activeScenarioId);
    if (!scenario) return;

    const allEvents = [...(scenario.evidence_nodes || []), ...(scenario.rejected_decoys || [])];
    const ev = allEvents.find((e) => e.evidence_id === evidenceId);
    if (ev) {
      renderEvidenceDrawer(ev);
    }
  };

  window.inspectNode = function (nodeType) {
    if (nodeType === 'verifier') {
      switchView('comparator');
    }
  };

  window.copyHash = function (hash) {
    navigator.clipboard.writeText(hash).then(() => {
      alert('Copied SHA-256 Record Hash to clipboard:\n' + hash);
    });
  };

  let activeModalEvidence = null;

  window.openSourceEvidenceModal = function (ev) {
    activeModalEvidence = ev;
    const modal = document.getElementById('source-modal');
    if (!modal) return;

    modal.style.display = 'flex';

    document.getElementById('modal-filename').textContent = ev.source_file;
    document.getElementById('modal-sheet').textContent = ev.sheet || 'Sheet1';
    document.getElementById('modal-cell').textContent = ev.cell;
    document.getElementById('modal-ev-id').textContent = ev.evidence_id;
    document.getElementById('modal-ev-level').textContent = ev.evidence_level;
    document.getElementById('modal-ev-hash').textContent = ev.record_hash;

    const isRejected = ev.status === 'REJECTED';
    const statusBadge = document.getElementById('modal-status-badge');
    const rejBanner = document.getElementById('modal-rejection-banner');

    if (isRejected) {
      statusBadge.className = 'badge escalated';
      statusBadge.textContent = '✕ Rejected Decoy';
      rejBanner.style.display = 'block';
      document.getElementById('modal-rejection-reason').textContent = ev.rejection_reason || 'Constraint validation failed.';
    } else {
      statusBadge.className = 'badge verified';
      statusBadge.textContent = '✓ Provenance Verified';
      rejBanner.style.display = 'none';
    }

    const spinner = document.getElementById('modal-loading-spinner');
    const content = document.getElementById('modal-spreadsheet-content');
    spinner.style.display = 'block';
    content.innerHTML = '';

    const params = new URLSearchParams({
      file: ev.source_file,
      sheet: ev.sheet || 'Sheet1',
      cell: ev.cell,
      row: String(ev.row || 1),
      row_radius: '3',
      column_radius: '3',
    });

    fetch(`/api/evidence/source-context?${params.toString()}`)
      .then((res) => res.json())
      .then((data) => {
        spinner.style.display = 'none';
        if (data.status === 'SUCCESS' && data.context) {
          renderSpreadsheetMatrix(data.context, isRejected);
        } else {
          content.innerHTML = `<div style="padding: 2rem; color: var(--rose-primary); text-align: center;">Error loading context: ${data.error || 'Unknown'}</div>`;
        }
      })
      .catch((err) => {
        spinner.style.display = 'none';
        content.innerHTML = `<div style="padding: 2rem; color: var(--rose-primary); text-align: center;">Network error loading spreadsheet data.</div>`;
      });
  };

  function renderSpreadsheetMatrix(ctx, isRejected) {
    const content = document.getElementById('modal-spreadsheet-content');
    if (!content) return;

    let html = '<table class="excel-grid-table"><thead><tr><th class="row-num-cell">#</th>';
    for (const col of ctx.columns) {
      html += `<th class="${col.is_target_column ? 'col-header-target' : ''}">${col.letter}<br><span style="font-size:0.65rem;font-weight:normal;">${col.header}</span></th>`;
    }
    html += '</tr></thead><tbody>';

    for (const row of ctx.rows) {
      html += `<tr class="${row.is_target_row ? 'row-target' : ''}"><td class="row-num-cell">${row.row_number}</td>`;
      for (const cell of row.cells) {
        const isTarget = cell.is_target;
        const targetClass = isTarget ? (isRejected ? 'cell-target cell-decoy' : 'cell-target') : '';
        const badge = isTarget ? `<span class="${isRejected ? 'decoy-target-badge' : 'evidence-target-badge'}">${isRejected ? '✕ Decoy' : '← Evidence'}</span>` : '';
        const val = cell.value !== null && cell.value !== undefined ? (typeof cell.value === 'number' && !Number.isInteger(cell.value) ? cell.value.toFixed(2) : cell.value) : '';
        html += `<td class="${targetClass}">${val} ${badge}</td>`;
      }
      html += '</tr>';
    }

    html += '</tbody></table>';
    content.innerHTML = html;
  }

  window.closeSourceModal = function () {
    const modal = document.getElementById('source-modal');
    if (modal) modal.style.display = 'none';
  };

  window.copyModalCellRef = function () {
    if (!activeModalEvidence) return;
    const ref = `${activeModalEvidence.sheet || 'Sheet1'}!${activeModalEvidence.cell}`;
    navigator.clipboard.writeText(ref).then(() => {
      const btn = document.getElementById('btn-copy-ref');
      if (btn) {
        const originalText = btn.textContent;
        btn.textContent = '✓ Copied Reference!';
        setTimeout(() => { btn.textContent = originalText; }, 2000);
      }
    });
  };

  // Close modal on Escape or backdrop click
  window.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') window.closeSourceModal();
  });

  const modalBackdrop = document.getElementById('source-modal');
  if (modalBackdrop) {
    modalBackdrop.addEventListener('click', (e) => {
      if (e.target === modalBackdrop) window.closeSourceModal();
    });
  }

  // Start the application
  window.addEventListener('DOMContentLoaded', init);
})();
