document.addEventListener('DOMContentLoaded', () => {
  const stockInput = document.getElementById('stockInput');
  const autocompleteDropdown = document.getElementById('autocompleteDropdown');
  const generateBtn = document.getElementById('generateBtn');
  const horizonGroup = document.getElementById('horizonGroup');
  const popularChips = document.querySelectorAll('.chip');
  const loadingOverlay = document.getElementById('loadingOverlay');
  const loadingSteps = document.querySelectorAll('.loading-steps .step');
  const reportContainer = document.getElementById('reportContainer');
  const terminalOutput = document.getElementById('terminalOutput');
  const reportHeaderTitle = document.getElementById('reportHeaderTitle');
  const downloadBtn = document.getElementById('downloadBtn');
  const printBtn = document.getElementById('printBtn');

  let selectedHorizon = 3;
  let activeQuery = '';
  let searchTimeout = null;
  let selectedAcIndex = -1;
  let acItems = [];

  // Global tab switcher for report tabs
  window.switchTab = function(evt, tabId) {
    const container = document.getElementById('terminalOutput');
    if (!container) return;
    const tabs = container.getElementsByClassName('tab-content');
    for (let i = 0; i < tabs.length; i++) {
      tabs[i].classList.remove('active');
    }
    const btns = container.getElementsByClassName('tab-btn');
    for (let i = 0; i < btns.length; i++) {
      btns[i].classList.remove('active');
    }
    const target = document.getElementById(tabId);
    if (target) {
      target.classList.add('active');
    }
    if (evt && evt.currentTarget) {
      evt.currentTarget.classList.add('active');
    }
    if (tabId === 'tab-charts' && window.onChartsTabActivated) {
      window.onChartsTabActivated();
    }
  };


  // Horizon Selection
  horizonGroup.addEventListener('click', (e) => {
    if (e.target.classList.contains('pill-btn')) {
      horizonGroup.querySelectorAll('.pill-btn').forEach(btn => btn.classList.remove('active'));
      e.target.classList.add('active');
      selectedHorizon = parseInt(e.target.dataset.horizon, 10);
      const horizonLabel = document.getElementById('horizonLabel');
      if (horizonLabel) {
        horizonLabel.textContent = `${selectedHorizon} Year${selectedHorizon > 1 ? 's' : ''}`;
      }
      if (activeQuery) {
        runReport(activeQuery, selectedHorizon);
      }
    }
  });

  // Popular Chips
  popularChips.forEach(chip => {
    chip.addEventListener('click', () => {
      const ticker = chip.dataset.ticker;
      stockInput.value = ticker;
      runReport(ticker, selectedHorizon);
    });
  });

  // Autocomplete search
  stockInput.addEventListener('input', () => {
    clearTimeout(searchTimeout);
    const q = stockInput.value.trim();
    if (!q) {
      autocompleteDropdown.classList.add('hidden');
      return;
    }
    searchTimeout = setTimeout(() => {
      fetch(`/api/search?q=${encodeURIComponent(q)}`)
        .then(res => res.json())
        .then(data => {
          renderAutocomplete(data.results || []);
        })
        .catch(() => {});
    }, 200);
  });

  function renderAutocomplete(results) {
    if (!results || results.length === 0) {
      autocompleteDropdown.classList.add('hidden');
      return;
    }
    acItems = results;
    selectedAcIndex = -1;
    autocompleteDropdown.innerHTML = '';
    results.forEach((item, index) => {
      const div = document.createElement('div');
      div.className = 'ac-item';
      div.innerHTML = `
        <span class="ac-name">${escapeHtml(item.name)}</span>
        <span class="ac-ticker">${escapeHtml(item.ticker)}</span>
      `;
      div.addEventListener('click', () => {
        stockInput.value = item.name;
        autocompleteDropdown.classList.add('hidden');
        runReport(item.ticker, selectedHorizon);
      });
      autocompleteDropdown.appendChild(div);
    });
    autocompleteDropdown.classList.remove('hidden');
  }

  // Keyboard navigation
  stockInput.addEventListener('keydown', (e) => {
    const items = autocompleteDropdown.querySelectorAll('.ac-item');
    if (!autocompleteDropdown.classList.contains('hidden') && items.length > 0) {
      if (e.key === 'ArrowDown') {
        e.preventDefault();
        selectedAcIndex = (selectedAcIndex + 1) % items.length;
        updateAcSelection(items);
        return;
      } else if (e.key === 'ArrowUp') {
        e.preventDefault();
        selectedAcIndex = (selectedAcIndex - 1 + items.length) % items.length;
        updateAcSelection(items);
        return;
      } else if (e.key === 'Enter') {
        e.preventDefault();
        if (selectedAcIndex >= 0 && selectedAcIndex < acItems.length) {
          const item = acItems[selectedAcIndex];
          stockInput.value = item.name;
          autocompleteDropdown.classList.add('hidden');
          runReport(item.ticker, selectedHorizon);
          return;
        }
      } else if (e.key === 'Escape') {
        autocompleteDropdown.classList.add('hidden');
        return;
      }
    }

    if (e.key === 'Enter') {
      const val = stockInput.value.trim();
      if (val) {
        autocompleteDropdown.classList.add('hidden');
        runReport(val, selectedHorizon);
      }
    }
  });

  function updateAcSelection(items) {
    items.forEach((item, idx) => {
      if (idx === selectedAcIndex) {
        item.classList.add('selected');
        item.scrollIntoView({ block: 'nearest' });
      } else {
        item.classList.remove('selected');
      }
    });
  }

  // Click outside to close autocomplete
  document.addEventListener('click', (e) => {
    if (!stockInput.contains(e.target) && !autocompleteDropdown.contains(e.target)) {
      autocompleteDropdown.classList.add('hidden');
    }
  });

  generateBtn.addEventListener('click', () => {
    const val = stockInput.value.trim();
    if (val) {
      autocompleteDropdown.classList.add('hidden');
      runReport(val, selectedHorizon);
    }
  });

  // Execute report generation
  function runReport(query, horizon) {
    activeQuery = query;
    loadingOverlay.classList.remove('hidden');
    reportContainer.classList.add('hidden');

    // Simulate progressive loading steps
    loadingSteps.forEach((s, i) => {
      s.className = 'step';
      if (i === 0) s.classList.add('active');
    });

    const stepInterval = setInterval(() => {
      const activeIdx = Array.from(loadingSteps).findIndex(s => s.classList.contains('active'));
      if (activeIdx >= 0 && activeIdx < loadingSteps.length - 1) {
        loadingSteps[activeIdx].className = 'step done';
        loadingSteps[activeIdx + 1].className = 'step active';
      }
    }, 450);

    fetch(`/api/report?query=${encodeURIComponent(query)}&horizon=${horizon}`)
      .then(async res => {
        if (!res.ok) {
          let detail = 'Stock not found or network error';
          try {
            const errData = await res.json();
            if (errData && errData.detail) detail = errData.detail;
          } catch (_) {}
          throw new Error(detail);
        }
        return res.json();
      })
      .then(data => {
        clearInterval(stepInterval);
        loadingOverlay.classList.add('hidden');
        if (data.success && data.report) {
          renderTerminal(data.report, data.html);
          reportContainer.classList.remove('hidden');
          reportContainer.scrollIntoView({ behavior: 'smooth' });
        }
      })
      .catch(err => {
        clearInterval(stepInterval);
        loadingOverlay.classList.add('hidden');
        alert('Could not generate report: ' + err.message);
      });
  }

  // Render Full Terminal in the UI
  function renderTerminal(r, rawHtml) {
    reportHeaderTitle.textContent = `REPORT · ${r.ticker} · ${r.horizon_years}Y HORIZON`;

    downloadBtn.onclick = () => {
      window.location.href = `/api/download?query=${encodeURIComponent(r.ticker)}&horizon=${r.horizon_years}`;
    };
    printBtn.onclick = () => {
      window.print();
    };

    if (rawHtml) {
      const parser = new DOMParser();
      const doc = parser.parseFromString(rawHtml, 'text/html');
      const container = doc.querySelector('.terminal-container');
      if (container) {
        terminalOutput.innerHTML = container.outerHTML;
        const tabBtns = terminalOutput.querySelectorAll('.tab-btn');
        tabBtns.forEach(btn => {
          btn.addEventListener('click', (e) => {
            const onclickAttr = btn.getAttribute('onclick') || '';
            const match = onclickAttr.match(/switchTab\([^,]+,\s*['"]([^'"]+)['"]\)/);
            if (match) {
              window.switchTab(e, match[1]);
            }
          });
        });
        initTerminalCharts(r);
        return;
      }
    }


    const strokeColor = r.confidence_score >= 9 ? '#34D399' : (r.confidence_score >= 6 ? '#FBBF24' : '#F87171');
    const mosClass = r.mos_pct >= 0 ? 'fv-mos-pos' : 'fv-mos-neg';
    const mosStr = r.mos_pct >= 0 ? `+${r.mos_pct}%` : `${r.mos_pct}%`;

    // 8 quarters rows
    let qRows = '';
    (r.last_8_quarters || []).forEach(q => {
      const yoyColor = (String(q.yoy).includes('+') || String(q.yoy).includes('Turnaround')) ? 'style="color: #10b981;"' : '';
      qRows += `
        <tr>
          <td>${escapeHtml(q.quarter)}</td>
          <td class="num">${Number(q.sales).toLocaleString()}</td>
          <td class="num">${q.opm}%</td>
          <td class="num">${Number(q.net_profit).toLocaleString()}</td>
          <td class="num">₹${Number(q.eps).toFixed(2)}</td>
          <td class="num" ${yoyColor}>${q.yoy}</td>
        </tr>
      `;
    });

    // Beat miss chips
    let bmChips = '';
    (r.beat_miss_list || []).forEach(bm => {
      bmChips += `
        <div class="${bm.badge}">
          <div class="bmc-q">${escapeHtml(bm.quarter)}</div>
          <div class="bmc-res">₹${Number(bm.eps).toFixed(2)}</div>
          <div class="bmc-diff">${bm.diff}</div>
        </div>
      `;
    });

    // Red flags
    let rfHtml = '';
    if (r.has_red_flags) {
      const items = (r.red_flags || []).map(f => `<li>${escapeHtml(f)}</li>`).join('');
      rfHtml = `
        <div class="rf-warn">
          <div style="font-size: 15px; font-weight: 700; color: #ef4444; margin-bottom: 6px;">⚠️ Red Flags Detected</div>
          <ul style="font-size: 13px; color: #cbd5e1; padding-left: 20px;">${items}</ul>
        </div>
      `;
    } else {
      rfHtml = `
        <div class="rf-ok">
          <div style="font-size: 28px;">✅</div>
          <div>
            <div style="font-size: 14px; font-weight: 700; color: #10b981;">No Critical Red Flags Detected</div>
            <div style="font-size: 12px; color: #94a3b8; margin-top: 2px;">
              Pledging clean (0%) · Statutory audit clean · Debt-to-equity within safety limits · Operating cash flow confirms authentic reported profit.
            </div>
          </div>
        </div>
      `;
    }

    // Verification table
    let vRows = '';
    (r.verification_table || []).forEach(row => {
      vRows += `
        <tr>
          <td>${row.num}</td>
          <td><strong>${escapeHtml(row.item)}</strong></td>
          <td class="num">${escapeHtml(String(row.val))}</td>
          <td>${escapeHtml(row.src)}</td>
          <td style="color: #10b981; font-weight: 700; text-align: center;">${row.confirmed}</td>
        </tr>
      `;
    });

    const scenarios = r.scenarios || {};
    const bullW = 100.0;
    const baseW = scenarios.bull_rev > 0 ? Math.round((scenarios.base_rev / scenarios.bull_rev) * 100) : 80;
    const bearW = scenarios.bull_rev > 0 ? Math.round((scenarios.bear_rev / scenarios.bull_rev) * 100) : 60;

    let cfRows = '';
    (r.cf_quality_table || []).forEach(row => {
      cfRows += `
        <tr>
          <td>${row.year}</td>
          <td class="num">₹${Number(row.cfo).toLocaleString()} Cr</td>
          <td class="num">₹${Number(row.np).toLocaleString()} Cr</td>
          <td class="num" style="color: #10b981; font-weight: 700;">${row.ratio}×</td>
        </tr>
      `;
    });

    terminalOutput.innerHTML = `
      <!-- Terminal Header -->
      <div class="terminal-header">
        <div class="ticker-block">
          <h1>${escapeHtml(r.name)} <span class="badge-ticker">${escapeHtml(r.ticker)}</span></h1>
          <div style="font-size: 13px; color: var(--text-muted); margin-top: 4px;">
            Sector: ${escapeHtml(r.sector)} · Industry: ${escapeHtml(r.industry)} · Horizon: ${r.horizon_years} Years
          </div>
        </div>
        <div class="confbar">
          <div class="vbadge">✓ Web-verified data</div>
          <div style="display: flex; align-items: center; gap: 8px;">
            <svg width="40" height="40" viewBox="0 0 100 100">
              <circle cx="50" cy="50" r="40" stroke="#1f293d" stroke-width="10" fill="transparent"/>
              <circle cx="50" cy="50" r="40" stroke="${strokeColor}" stroke-width="10" fill="transparent"
                      stroke-dasharray="251.33"
                      stroke-dashoffset="${r.dashoffset}"
                      stroke-linecap="round"
                      transform="rotate(-90 50 50)"/>
            </svg>
            <div>
              <div style="font-size: 13px; font-weight: 700; color: ${strokeColor};">${r.confidence_score} / 11</div>
              <div style="font-size: 10px; color: var(--text-muted); text-transform: uppercase;">Confidence</div>
            </div>
          </div>
        </div>
      </div>

      <!-- Quick KPI Strip -->
      <div class="quick-kpis">
        <div class="kpi-tile">
          <div class="kpi-title">Current Market Price (CMP)</div>
          <div class="kpi-val">₹${Number(r.cmp).toLocaleString()}</div>
          <div style="font-size: 12px; color: var(--text-muted); margin-top: 2px;">Market Cap: ₹${Number(r.mcap).toLocaleString()} Cr</div>
        </div>
        <div class="kpi-tile">
          <div class="kpi-title">52-Week Range</div>
          <div class="kpi-val" style="font-size: 16px;">₹${Number(r.low_52w).toLocaleString()} – ₹${Number(r.high_52w).toLocaleString()}</div>
          <div class="range-meter">
            <div class="range-track">
              <div class="range-fill" style="width: ${r.range_52w_pct}%;"></div>
              <div class="range-cursor" style="left: ${r.range_52w_pct}%;"></div>
            </div>
          </div>
        </div>
        <div class="kpi-tile">
          <div class="kpi-title">Valuation Multiples</div>
          <div class="kpi-val" style="font-size: 17px;">P/E ${r.pe}× · P/B ${r.price_to_book}×</div>
          <div style="font-size: 12px; color: var(--text-muted); margin-top: 2px;">PEG: ${r.peg} (${r.peg_class})</div>
        </div>
        <div class="kpi-tile">
          <div class="kpi-title">Pre-computed CAGR (3Y)</div>
          <div class="kpi-val" style="font-size: 17px;">Sales ${r.sales_3y}% · PAT ${r.profit_3y}%</div>
          <div style="font-size: 12px; color: var(--text-muted); margin-top: 2px;">ROCE: ${r.roce}% · ROE: ${r.roe}%</div>
        </div>
      </div>

      <!-- Navigation Tabs -->
      <div class="terminal-nav" id="terminalTabs">
        <button class="tab-btn star-tab active" data-tab="tab-t-view">★ Master View</button>
        <button class="tab-btn" data-tab="tab-t-val">1. Valuation & Fair Value</button>
        <button class="tab-btn" data-tab="tab-t-growth">2. Growth & Beat/Miss</button>
        <button class="tab-btn" data-tab="tab-t-health">3. Health & Cash Flows</button>
        <button class="tab-btn" data-tab="tab-t-returns">4. Returns & Capital Alloc</button>
        <button class="tab-btn" data-tab="tab-t-verification">5. Data Verification Table (25+)</button>
      </div>

      <!-- Tab Content Area -->
      <div id="tab-t-view" class="tab-content active">
        <div class="dashboard-grid">
          <div class="col-8">
            <div class="card" style="height: 100%;">
              <div class="card-title">
                <span>Terminal Radar & Signal Matrix</span>
                <span class="sg">OVERALL: ${r.overall_status}</span>
              </div>
              <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; margin-bottom: 20px;">
                <div style="background: #111a2c; padding: 12px; border-radius: 6px; border: 1px solid var(--border);">
                  <div style="font-size: 11px; color: var(--text-muted);">Valuation</div>
                  <div style="font-weight: 700; margin-top: 4px; display: flex; justify-content: space-between;">
                    <span>${r.val_status}</span>
                    <span class="${r.val_badge}">P/E ${r.pe}×</span>
                  </div>
                </div>
                <div style="background: #111a2c; padding: 12px; border-radius: 6px; border: 1px solid var(--border);">
                  <div style="font-size: 11px; color: var(--text-muted);">Growth</div>
                  <div style="font-weight: 700; margin-top: 4px; display: flex; justify-content: space-between;">
                    <span>${r.growth_status}</span>
                    <span class="${r.growth_badge}">3Y Rev ${r.sales_3y}%</span>
                  </div>
                </div>
                <div style="background: #111a2c; padding: 12px; border-radius: 6px; border: 1px solid var(--border);">
                  <div style="font-size: 11px; color: var(--text-muted);">Balance Sheet</div>
                  <div style="font-weight: 700; margin-top: 4px; display: flex; justify-content: space-between;">
                    <span>${r.health_status}</span>
                    <span class="${r.health_badge}">D/E ${r.debt_to_equity}×</span>
                  </div>
                </div>
                <div style="background: #111a2c; padding: 12px; border-radius: 6px; border: 1px solid var(--border);">
                  <div style="font-size: 11px; color: var(--text-muted);">Returns Profile</div>
                  <div style="font-weight: 700; margin-top: 4px; display: flex; justify-content: space-between;">
                    <span>ROCE ${r.roce}%</span>
                    <span class="sa">ROE ${r.roe}%</span>
                  </div>
                </div>
                <div style="background: #111a2c; padding: 12px; border-radius: 6px; border: 1px solid var(--border);">
                  <div style="font-size: 11px; color: var(--text-muted);">Capital Allocation</div>
                  <div style="font-weight: 700; margin-top: 4px; display: flex; justify-content: space-between;">
                    <span>${r.alloc_status}</span>
                    <span class="sg">${r.alloc_score}/3</span>
                  </div>
                </div>
                <div style="background: #111a2c; padding: 12px; border-radius: 6px; border: 1px solid var(--border);">
                  <div style="font-size: 11px; color: var(--text-muted);">Predictability</div>
                  <div style="font-weight: 700; margin-top: 4px; display: flex; justify-content: space-between;">
                    <span>${r.predictability_status}</span>
                    <span class="${r.predictability_badge}">${r.beats_count}/8</span>
                  </div>
                </div>
              </div>

              <!-- Fair Value Range Box -->
              <div class="fair-value-box">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                  <div>
                    <span style="font-size: 11px; text-transform: uppercase; color: var(--text-muted); font-weight: 700;">Fair Value Range (Forward EPS: ₹${r.forward_eps})</span>
                    <div style="font-size: 18px; font-weight: 700; margin-top: 2px;">
                      Base FV: ₹${Number(r.base_fv).toLocaleString()} <span style="font-size: 12px; font-weight: normal; color: var(--text-muted);">(Bear: ₹${Number(r.bear_fv).toLocaleString()} | Bull: ₹${Number(r.bull_fv).toLocaleString()})</span>
                    </div>
                  </div>
                  <span class="${mosClass}">${mosStr} Margin of Safety</span>
                </div>

                <div class="fv-bar-container">
                  <div class="fv-bar">
                    <div class="fvz-u" style="width: ${r.fv_u_width}%;"></div>
                    <div class="fvz-f" style="width: ${r.fv_f_width}%;"></div>
                    <div class="fvz-p" style="width: ${r.fv_p_width}%;"></div>
                  </div>
                  <div class="fv-cursor" style="left: ${r.fv_cursor_pos}%;">
                    <div class="fv-cursor-label">CMP ₹${Number(r.cmp).toLocaleString()} (${r.entry_zone})</div>
                  </div>
                </div>
              </div>

            </div>
          </div>

          <div class="col-4">
            <div class="card" style="height: 100%;">
              <div class="card-title">Investment Thesis Highlights</div>
              <div style="font-size: 12px; line-height: 1.6; color: #cbd5e1;">
                <div style="margin-bottom: 12px;">
                  <strong style="color: #10b981;">CORE ADVANTAGES:</strong>
                  <div>Pre-computed 3-year profit CAGR of ${r.profit_3y}% with high capital efficiency and zero promoter pledging.</div>
                </div>
                <div style="margin-bottom: 12px;">
                  <strong style="color: #f59e0b;">VALUATION MULTIPLE:</strong>
                  <div>Current PEG of ${r.peg} offers a favorable entry buffer for ${r.horizon_years}-year horizon compounding.</div>
                </div>
                <div>
                  <strong style="color: #38bdf8;">ENTRY RECOMMENDATION:</strong>
                  <div style="margin-top: 4px;"><span class="${r.entry_badge}">${r.entry_zone}</span></div>
                </div>
              </div>
            </div>
          </div>

          <div class="col-12">${rfHtml}</div>

          <div class="col-12">
            <div class="card">
              <div class="card-title">Forward Revenue & Margin Projections (${r.horizon_years} Years)</div>
              <div class="scenario-row">
                <div class="scenario-info">
                  <span><strong>Bull Scenario</strong> (${scenarios.bull_cagr}% CAGR)</span>
                  <span class="num">₹${Number(scenarios.bull_rev).toLocaleString()} Cr Rev · ₹${Number(scenarios.bull_ebitda).toLocaleString()} Cr EBITDA</span>
                </div>
                <div class="scenario-bar-bg"><div class="scenario-bar-fill s-bull" style="width: ${bullW}%;"></div></div>
              </div>
              <div class="scenario-row">
                <div class="scenario-info">
                  <span><strong>Base Scenario</strong> (${scenarios.base_cagr}% CAGR)</span>
                  <span class="num">₹${Number(scenarios.base_rev).toLocaleString()} Cr Rev · ₹${Number(scenarios.base_ebitda).toLocaleString()} Cr EBITDA</span>
                </div>
                <div class="scenario-bar-bg"><div class="scenario-bar-fill s-base" style="width: ${baseW}%;"></div></div>
              </div>
              <div class="scenario-row">
                <div class="scenario-info">
                  <span><strong>Bear Scenario</strong> (${scenarios.bear_cagr}% CAGR)</span>
                  <span class="num">₹${Number(scenarios.bear_rev).toLocaleString()} Cr Rev · ₹${Number(scenarios.bear_ebitda).toLocaleString()} Cr EBITDA</span>
                </div>
                <div class="scenario-bar-bg"><div class="scenario-bar-fill s-bear" style="width: ${bearW}%;"></div></div>
              </div>
            </div>
          </div>

        </div>
      </div>

      <!-- Tab: Valuation -->
      <div id="tab-t-val" class="tab-content">
        <div class="card">
          <div class="card-title">Valuation Multiples & Target Bands</div>
          <table class="term-table">
            <thead><tr><th>Parameter</th><th class="num">Value</th><th>Interpretation</th></tr></thead>
            <tbody>
              <tr><td>Stock P/E Ratio</td><td class="num">${r.pe}×</td><td>5Y Median: ${r.median_pe}× · Sector Avg: ${r.sector_pe}×</td></tr>
              <tr><td>Price to Book (P/B)</td><td class="num">${r.price_to_book}×</td><td>Book Value per share: ₹${r.pb}</td></tr>
              <tr><td>PEG Ratio</td><td class="num" style="color: #10b981; font-weight: 700;">${r.peg}</td><td><span class="${r.peg_badge}">${r.peg_class} (&lt; 1.0 = CHEAP)</span></td></tr>
              <tr><td>Forward Base EPS</td><td class="num">₹${r.forward_eps}</td><td>Projected over ${r.horizon_years}-Year Horizon</td></tr>
              <tr><td>Bear Fair Value</td><td class="num">₹${Number(r.bear_fv).toLocaleString()}</td><td>Conservative Lower Bound</td></tr>
              <tr><td>Base Fair Value</td><td class="num" style="color: #38bdf8; font-weight: 700;">₹${Number(r.base_fv).toLocaleString()}</td><td>Target Valuation Target</td></tr>
              <tr><td>Bull Fair Value</td><td class="num">₹${Number(r.bull_fv).toLocaleString()}</td><td>Optimistic Expansion Target</td></tr>
              <tr><td>Margin of Safety</td><td class="num"><span class="${mosClass}">${mosStr}</span></td><td>Discount to Base Fair Value</td></tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- Tab: Growth -->
      <div id="tab-t-growth" class="tab-content">
        <div class="dashboard-grid">
          <div class="col-6">
            <div class="card">
              <div class="card-title">Pre-computed Compounded Growth Rates (Screener.in)</div>
              <table class="term-table">
                <thead><tr><th>Metric</th><th class="num">3 Years</th><th class="num">5 Years</th><th class="num">10 Years</th></tr></thead>
                <tbody>
                  <tr><td>Sales Growth</td><td class="num" style="color: #10b981; font-weight: 700;">${r.sales_3y}%</td><td class="num">${r.sales_5y}%</td><td class="num">${r.sales_10y}%</td></tr>
                  <tr><td>Profit Growth</td><td class="num" style="color: #10b981; font-weight: 700;">${r.profit_3y}%</td><td class="num">${r.profit_5y}%</td><td class="num">${r.profit_10y}%</td></tr>
                </tbody>
              </table>
            </div>
          </div>
          <div class="col-6">
            <div class="card">
              <div class="card-title">Consensus Predictability (Beat / Miss History)</div>
              <div class="beat-miss-grid">${bmChips}</div>
            </div>
          </div>
          <div class="col-12">
            <div class="card">
              <div class="card-title">Last 8 Quarters Financial Performance</div>
              <table class="term-table">
                <thead><tr><th>Quarter</th><th class="num">Sales (₹ Cr)</th><th class="num">OPM %</th><th class="num">Net Profit (₹ Cr)</th><th class="num">EPS (₹)</th><th class="num">YoY Change</th></tr></thead>
                <tbody>${qRows}</tbody>
              </table>
            </div>
          </div>
        </div>
      </div>

      <!-- Tab: Health -->
      <div id="tab-t-health" class="tab-content">
        <div class="dashboard-grid">
          <div class="col-6">
            <div class="card">
              <div class="card-title">Solvency & Debt Ratios</div>
              <table class="term-table">
                <thead><tr><th>Ratio</th><th class="num">Value</th><th>Status</th></tr></thead>
                <tbody>
                  <tr><td>Debt to Equity</td><td class="num">${r.debt_to_equity}×</td><td><span class="${r.health_badge}">${r.health_status}</span></td></tr>
                  <tr><td>Interest Coverage Ratio</td><td class="num">${r.icr}×</td><td><span class="sg">HEALTHY (&gt; 3.0×)</span></td></tr>
                  <tr><td>Liquid Cash & Investments</td><td class="num">₹${Number(r.liquid_reserves).toLocaleString()} Cr</td><td><span class="sg">PRISTINE</span></td></tr>
                </tbody>
              </table>
            </div>
          </div>
          <div class="col-6">
            <div class="card">
              <div class="card-title">Cash Flow & Earnings Quality (3 Years)</div>
              <table class="term-table">
                <thead><tr><th>Year</th><th class="num">Operating CF</th><th class="num">Net Profit</th><th class="num">OCF / NP</th></tr></thead>
                <tbody>${cfRows}</tbody>
              </table>
            </div>
          </div>
        </div>
      </div>

      <!-- Tab: Returns -->
      <div id="tab-t-returns" class="tab-content">
        <div class="card">
          <div class="card-title">Return On Capital & Allocation Profile</div>
          <table class="term-table">
            <thead><tr><th>Metric</th><th class="num">Value</th><th>Benchmark</th></tr></thead>
            <tbody>
              <tr><td>ROCE %</td><td class="num" style="font-weight: 700;">${r.roce}%</td><td>&gt; 15% Good</td></tr>
              <tr><td>ROE %</td><td class="num" style="font-weight: 700;">${r.roe}%</td><td>&gt; 15% Good</td></tr>
              <tr><td>Core Operating ROIC (ex-cash)</td><td class="num" style="color: #10b981; font-weight: 700;">~${r.core_roic}%</td><td>WACC Benchmark: 11.5%</td></tr>
              <tr><td>Capital Allocation Score</td><td class="num" style="color: #10b981; font-weight: 700;">${r.alloc_score}/3</td><td><span class="sg">${r.alloc_status}</span></td></tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- Tab: Verification -->
      <div id="tab-t-verification" class="tab-content">
        <div class="card">
          <div class="card-title">Mandatory Data Verification Table (25+ Data Points)</div>
          <table class="term-table">
            <thead><tr><th>#</th><th>Data Point</th><th class="num">Value</th><th>Source</th><th style="text-align: center;">Confirmed?</th></tr></thead>
            <tbody>${vRows}</tbody>
          </table>
        </div>
      </div>
    `;

    // Hook tab buttons
    const tabButtons = terminalOutput.querySelectorAll('.tab-btn');
    tabButtons.forEach(btn => {
      btn.addEventListener('click', () => {
        tabButtons.forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        const targetId = btn.dataset.tab;
        terminalOutput.querySelectorAll('.tab-content').forEach(tc => tc.classList.remove('active'));
        const targetContent = document.getElementById(targetId);
        if (targetContent) targetContent.classList.add('active');
      });
    });

    initTerminalCharts(r);
  }

  let chartJsInstance = null;
  let tvWidgetInstanceLoaded = false;
  let currentChartMetric = 'Price-DMA50-DMA200-Volume';
  let currentChartDays = 1095;
  let activeStockData = null;

  function initTerminalCharts(r) {
    activeStockData = r;
    currentChartMetric = 'Price-DMA50-DMA200-Volume';
    currentChartDays = r.chart_days || (r.horizon_years * 365);
    chartJsInstance = null;
    tvWidgetInstanceLoaded = false;

    // Connect metric buttons
    const metricBtns = terminalOutput.querySelectorAll('.chart-metric-btn');
    metricBtns.forEach(btn => {
      btn.addEventListener('click', (e) => {
        e.preventDefault();
        metricBtns.forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        const onclickAttr = btn.getAttribute('onclick') || '';
        const match = onclickAttr.match(/switchScreenerMetric\(['"]([^'"]+)['"]/);
        if (match) {
          currentChartMetric = match[1];
          reloadChartData();
        }
      });
    });

    // Connect time buttons
    const timeBtns = terminalOutput.querySelectorAll('.chart-time-btn');
    timeBtns.forEach(btn => {
      btn.addEventListener('click', (e) => {
        e.preventDefault();
        timeBtns.forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        const onclickAttr = btn.getAttribute('onclick') || '';
        const match = onclickAttr.match(/switchScreenerDays\((\d+)/);
        if (match) {
          currentChartDays = parseInt(match[1], 10);
          reloadChartData();
        }
      });
    });

    window.onChartsTabActivated = () => {
      setTimeout(() => {
        if (!chartJsInstance) {
          drawScreenerChart(activeStockData.chart_data || {}, currentChartMetric);
        } else {
          chartJsInstance.resize();
        }
        if (!tvWidgetInstanceLoaded) {
          loadTradingViewWidget(activeStockData);
        }
      }, 50);
    };
  }

  function reloadChartData() {
    if (!activeStockData || !activeStockData.company_id) {
      if (activeStockData && activeStockData.chart_data) {
        drawScreenerChart(activeStockData.chart_data, currentChartMetric);
      }
      return;
    }
    fetch(`/api/chart?company_id=${encodeURIComponent(activeStockData.company_id)}&metric=${encodeURIComponent(currentChartMetric)}&days=${currentChartDays}`)
      .then(res => res.json())
      .then(data => {
        if (data.success && data.chart) {
          drawScreenerChart(data.chart, currentChartMetric);
        }
      })
      .catch(() => {
        if (activeStockData.chart_data) {
          drawScreenerChart(activeStockData.chart_data, currentChartMetric);
        }
      });
  }

  function drawScreenerChart(chartData, metric) {
    const canvas = document.getElementById('screenerOfficialCanvas');
    if (!canvas || typeof Chart === 'undefined') return;
    const ctx = canvas.getContext('2d');
    const datasets = (chartData && chartData.datasets) ? chartData.datasets : [];
    if (datasets.length === 0) return;

    let dateLabels = [];
    const primaryDs = datasets[0];
    if (primaryDs && primaryDs.values) {
      dateLabels = primaryDs.values.map(v => v[0]);
    }

    const chartDatasets = [];

    if (metric === 'Price-DMA50-DMA200-Volume') {
      const priceMap = {}, dma50Map = {}, dma200Map = {}, volMap = {};
      datasets.forEach(d => {
        if (d.metric === 'Price') {
          d.values.forEach(v => { priceMap[v[0]] = parseFloat(v[1]); });
        } else if (d.metric === 'DMA50') {
          d.values.forEach(v => { dma50Map[v[0]] = parseFloat(v[1]); });
        } else if (d.metric === 'DMA200') {
          d.values.forEach(v => { dma200Map[v[0]] = parseFloat(v[1]); });
        } else if (d.metric === 'Volume') {
          d.values.forEach(v => { volMap[v[0]] = v[1]; });
        }
      });

      chartDatasets.push({
        label: 'Price (₹)',
        data: dateLabels.map(d => priceMap[d] !== undefined ? priceMap[d] : null),
        borderColor: '#38bdf8',
        backgroundColor: 'rgba(56, 189, 248, 0.08)',
        borderWidth: 2,
        fill: true,
        yAxisID: 'yPrice',
        pointRadius: 0,
        tension: 0.1
      });

      chartDatasets.push({
        label: '50 DMA (₹)',
        data: dateLabels.map(d => dma50Map[d] !== undefined ? dma50Map[d] : null),
        borderColor: '#f59e0b',
        borderWidth: 1.8,
        borderDash: [3, 2],
        fill: false,
        yAxisID: 'yPrice',
        pointRadius: 0,
        tension: 0.1
      });

      chartDatasets.push({
        label: '200 DMA (₹)',
        data: dateLabels.map(d => dma200Map[d] !== undefined ? dma200Map[d] : null),
        borderColor: '#a855f7',
        borderWidth: 2,
        fill: false,
        yAxisID: 'yPrice',
        pointRadius: 0,
        tension: 0.1
      });

      chartDatasets.push({
        type: 'bar',
        label: 'Volume',
        data: dateLabels.map(d => volMap[d] !== undefined ? volMap[d] : null),
        backgroundColor: 'rgba(16, 185, 129, 0.25)',
        yAxisID: 'yVol',
        barPercentage: 0.8
      });

    } else if (metric === 'Price to Earning-Median PE-EPS') {
      const peMap = {}, medPeMap = {}, epsMap = {};
      datasets.forEach(d => {
        if (d.metric === 'Price to Earning') {
          d.values.forEach(v => { peMap[v[0]] = parseFloat(v[1]); });
        } else if (d.metric === 'Median PE') {
          d.values.forEach(v => { medPeMap[v[0]] = parseFloat(v[1]); });
        } else if (d.metric === 'EPS') {
          d.values.forEach(v => { epsMap[v[0]] = parseFloat(v[1]); });
        }
      });

      chartDatasets.push({
        label: 'P/E Multiple',
        data: dateLabels.map(d => peMap[d] !== undefined ? peMap[d] : null),
        borderColor: '#06b6d4',
        borderWidth: 2,
        yAxisID: 'yPrice',
        pointRadius: 0
      });

      chartDatasets.push({
        label: '10Y Median P/E',
        data: dateLabels.map(d => medPeMap[d] !== undefined ? medPeMap[d] : null),
        borderColor: '#f59e0b',
        borderDash: [4, 3],
        borderWidth: 1.8,
        yAxisID: 'yPrice',
        pointRadius: 0
      });

      chartDatasets.push({
        type: 'bar',
        label: 'TTM EPS (₹)',
        data: dateLabels.map(d => epsMap[d] !== undefined ? epsMap[d] : null),
        backgroundColor: 'rgba(52, 211, 153, 0.3)',
        yAxisID: 'yVol',
        barPercentage: 0.6
      });
    } else {
      const colors = ['#38bdf8', '#f59e0b', '#10b981', '#a855f7'];
      datasets.forEach((ds, idx) => {
        const vMap = {};
        ds.values.forEach(v => { vMap[v[0]] = parseFloat(v[1]); });
        chartDatasets.push({
          label: ds.metric,
          data: dateLabels.map(d => vMap[d] !== undefined ? vMap[d] : null),
          borderColor: colors[idx % colors.length],
          borderWidth: 2,
          yAxisID: 'yPrice',
          pointRadius: 0
        });
      });
    }

    if (chartJsInstance) chartJsInstance.destroy();

    chartJsInstance = new Chart(ctx, {
      type: 'line',
      data: { labels: dateLabels, datasets: chartDatasets },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        interaction: { mode: 'index', intersect: false },
        plugins: {
          legend: {
            position: 'top',
            labels: { color: '#cbd5e1', font: { size: 11, family: 'system-ui' }, usePointStyle: true }
          },
          tooltip: {
            backgroundColor: '#0f172a',
            borderColor: '#334155',
            borderWidth: 1,
            titleColor: '#38bdf8',
            bodyColor: '#e2e8f0'
          }
        },
        scales: {
          x: {
            ticks: { color: '#64748b', maxTicksLimit: 10, font: { size: 10 } },
            grid: { color: 'rgba(51, 65, 85, 0.3)' }
          },
          yPrice: {
            type: 'linear',
            position: 'left',
            ticks: { color: '#94a3b8', font: { size: 10 } },
            grid: { color: 'rgba(51, 65, 85, 0.4)' }
          },
          yVol: {
            type: 'linear',
            position: 'right',
            grid: { drawOnChartArea: false },
            ticks: { display: false }
          }
        }
      }
    });
  }

  function loadTradingViewWidget(r) {
    const container = document.getElementById('tv_chart_container');
    if (!container || tvWidgetInstanceLoaded) return;
    if (typeof TradingView === 'undefined') return;

    const symb = r.bse_code && !r.ticker ? ('BSE:' + r.bse_code) : ('NSE:' + r.ticker);

    new TradingView.widget({
      "autosize": true,
      "symbol": symb,
      "interval": "D",
      "timezone": "Asia/Kolkata",
      "theme": "dark",
      "style": "1",
      "locale": "en",
      "toolbar_bg": "#0b0f19",
      "enable_publishing": false,
      "hide_top_toolbar": false,
      "hide_legend": false,
      "save_image": false,
      "container_id": "tv_chart_container",
      "studies": [
        "MASimple@tv-basicstudies",
        "Volume@tv-basicstudies"
      ]
    });
    tvWidgetInstanceLoaded = true;
  }

  function escapeHtml(str) {

    if (!str) return '';
    return String(str)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;');
  }
});
