// =====================================================
//  GLOBAL STATE
// =====================================================
let histChart    = null;
let heatmapChart = null;
let missingChart = null;
let mainChart    = null;
let corrChart    = null;

let globalData       = null;
let activeChartType  = 'bar';


// =====================================================
//  NAVIGATION (sidebar section switching)
// =====================================================
function showSection(name) {
    document.querySelectorAll('.section').forEach(s => s.classList.remove('active'));
    document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));

    const sec = document.getElementById('section-' + name);
    if (sec) sec.classList.add('active');

    const navItem = document.querySelector(`[data-section="${name}"]`);
    if (navItem) navItem.classList.add('active');
}


// =====================================================
//  CHART TYPE PILLS
// =====================================================
document.querySelectorAll('.chart-pill').forEach(btn => {
    btn.addEventListener('click', () => {
        document.querySelectorAll('.chart-pill').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        activeChartType = btn.dataset.type;
    });
});


// =====================================================
//  DRAG AND DROP
// =====================================================
const dropZone = document.getElementById('dropZone');

if (dropZone) {
    dropZone.addEventListener('dragover', e => {
        e.preventDefault();
        dropZone.classList.add('drag-over');
    });

    dropZone.addEventListener('dragleave', () => {
        dropZone.classList.remove('drag-over');
    });

    dropZone.addEventListener('drop', e => {
        e.preventDefault();
        dropZone.classList.remove('drag-over');
        const f = e.dataTransfer.files[0];
        if (f) {
            document.getElementById('fileInput').files = e.dataTransfer.files;
            const nameEl = document.getElementById('fileName');
            if (nameEl) nameEl.textContent = '→ ' + f.name;
        }
    });
}

const fileInput = document.getElementById('fileInput');
if (fileInput) {
    fileInput.addEventListener('change', e => {
        const f = e.target.files[0];
        if (f) {
            const nameEl = document.getElementById('fileName');
            if (nameEl) nameEl.textContent = '→ ' + f.name;
        }
    });
}


// =====================================================
//  TOAST NOTIFICATION
// =====================================================
function toast(msg, duration = 3000) {
    const t = document.getElementById('toast');
    if (!t) return;
    t.textContent = msg;
    t.style.display = 'block';
    setTimeout(() => { t.style.display = 'none'; }, duration);
}


// =====================================================
//  TIMESTAMP HELPER
// =====================================================
function ts() {
    return new Date().toLocaleTimeString('en-GB');
}


// =====================================================
//  LIVE CODE DISPLAY (NEW!)
// =====================================================
function addLog(message) {
    const statusLog = document.getElementById('statusLog');
    if (!statusLog) return;

    const time = ts();
    const line = `[${time}] ${message}`;

    statusLog.textContent += (statusLog.textContent ? '\n' : '') + line;

    // Auto-scroll to bottom
    statusLog.parentElement.scrollTop = statusLog.parentElement.scrollHeight;
}


// =====================================================
//  UPLOAD + RUN EDA
// =====================================================
document.getElementById("uploadBtn")
.addEventListener("click", async () => {

    const file = document.getElementById("fileInput").files[0];

    if (!file) {
        toast('⚠ SELECT A FILE FIRST');
        alert("Select a file first");
        return;
    }

    const btn     = document.getElementById('uploadBtn');
    const btnText = document.getElementById('uploadBtnText');

    // Loading state
    if (btn)     btn.disabled = true;
    if (btnText) btnText.innerHTML = '<span class="spinner"></span>';

    const statusCard = document.getElementById('uploadStatus');
    const statusLog  = document.getElementById('statusLog');

    if (statusCard) statusCard.style.display = 'block';
    if (statusLog)  statusLog.textContent = '';

    addLog(`📁 Uploading file: ${file.name}`);
    addLog(`📊 File size: ${(file.size / 1024).toFixed(1)} KB`);
    addLog(`⚙️ Running EDA pipeline...`);

    try {
        // ✅ FormData built fresh inside try block — prevents DataCloneError
        const formData = new FormData();
        formData.append("file", file);

        addLog(`📤 Sending to server...`);

        const response = await fetch("/upload", {
            method: "POST",
            body: formData
        });

        addLog(`📡 Server response received`);

        const data = await response.json();

        if (!response.ok || data.error) {
            const errMsg = data.error || "Error processing dataset";
            addLog(`❌ ERROR: ${errMsg}`);
            alert(errMsg);
            if (btn)     btn.disabled = false;
            if (btnText) btnText.textContent = 'RUN ANALYSIS';
            return;
        }

        globalData = data;

        addLog(`✅ EDA Complete`);
        addLog(`📈 Dataset: ${data.overview.rows.toLocaleString()} rows × ${data.overview.columns} columns`);
        addLog(`🔢 Numeric columns: ${data.overview.numeric_columns.length}`);
        addLog(`📝 Categorical columns: ${data.overview.categorical_columns.length}`);
        addLog(`📅 DateTime columns: ${data.overview.datetime_columns.length}`);
        addLog(`🧹 Duplicate rows: ${data.data_quality?.duplicates ?? 0}`);
        addLog(`🔄 Rendering dashboard components...`);

        // ── Old-style loaders (keep working if old HTML is used) ──
        loadOverview(data);
        loadDatasetInfo(data);
        loadUniqueValues(data);
        loadMissingProcess(data);
        loadValueCounts(data);
        loadPreview(data);
        loadInsights(data);
        drawHistogram(data);
        drawCorrelation(data);

        // ── New-style renderers (new HTML sections) ──
        renderAll(data);

        addLog(`✨ Dashboard ready to explore!`);

        if (btn)     btn.disabled = false;
        if (btnText) btnText.textContent = 'RUN ANALYSIS';

        toast('✔ ANALYSIS COMPLETE');

        // Auto-navigate to overview after upload
        setTimeout(() => showSection('overview'), 800);

    } catch (err) {
        console.error(err);
        addLog(`💥 SERVER ERROR: ${err.message}`);
        alert("Server error: " + err.message);
        if (btn)     btn.disabled = false;
        if (btnText) btnText.textContent = 'RUN ANALYSIS';
    }
});


// =====================================================
//  RENDER ALL (new-style dashboard)
// =====================================================
function renderAll(d) {
    renderOverview(d);
    renderQuality(d);
    renderStructure(d);
    renderValueCountsNew(d);
    renderChartBuilder(d);
    renderCorrelation(d);
    renderInsightsNew(d);
    renderPreviewNew(d);
}


// =====================================================
//  OLD-STYLE LOADERS (backward compatible)
// =====================================================

function loadOverview(data) {
    const set = (id, val) => {
        const el = document.getElementById(id);
        if (el) el.innerText = val;
    };

    set("rows",    data.overview.rows);
    set("columns", data.overview.columns);
    set("numericColumns",     data.overview.numeric_columns.join(", "));
    set("categoricalColumns", data.overview.categorical_columns.join(", "));
    set("datetimeColumns",    data.overview.datetime_columns.join(", "));
    set("dateColumns",        data.overview.datetime_columns.join(", "));
    set("duplicates",         data.data_quality?.duplicates ?? 0);
}

function loadDatasetInfo(data) {
    const el = document.getElementById("datasetInfo");
    if (el) el.innerHTML = `<pre>${data.dataset_info}</pre>`;
}

function loadUniqueValues(data) {
    const box = document.getElementById("uniqueValues");
    if (!box) return;

    let table = "<table><tr><th>Column</th><th>Unique Values</th></tr>";
    Object.entries(data.nunique).forEach(([col, val]) => {
        table += `<tr><td>${col}</td><td>${val}</td></tr>`;
    });
    table += "</table>";
    box.innerHTML = table;
}

function loadMissingProcess(data) {
    const box = document.getElementById("missingProcess");
    if (!box) return;

    let table = `
        <table>
            <tr>
                <th>Column</th>
                <th>Missing Before</th>
                <th>Missing After</th>
                <th>Method Used</th>
            </tr>
    `;
    Object.entries(data.missing_handling_process).forEach(([col, obj]) => {
        table += `
            <tr>
                <td>${col}</td>
                <td>${obj.missing_before}</td>
                <td>${obj.missing_after}</td>
                <td>${obj.method}</td>
            </tr>
        `;
    });
    table += "</table>";
    box.innerHTML = table;
}

function loadValueCounts(data) {
    const box = document.getElementById("valueCounts");
    if (!box) return;

    let html = "";
    Object.entries(data.value_counts).forEach(([col, counts]) => {
        html += `<h3>${col}</h3>`;
        html += "<table><tr><th>Value</th><th>Count</th></tr>";
        Object.entries(counts).forEach(([val, count]) => {
            html += `<tr><td>${val}</td><td>${count}</td></tr>`;
        });
        html += "</table><br>";
    });
    box.innerHTML = html;
}

function loadPreview(data) {
    const div = document.getElementById("preview");
    if (!div || !data.preview || !data.preview.length) return;

    let table = "<table><tr>";
    Object.keys(data.preview[0]).forEach(col => {
        table += `<th>${col}</th>`;
    });
    table += "</tr>";
    data.preview.forEach(row => {
        table += "<tr>";
        Object.values(row).forEach(val => {
            table += `<td>${val ?? ""}</td>`;
        });
        table += "</tr>";
    });
    table += "</table>";
    div.innerHTML = table;
}

function loadInsights(data) {
    const box = document.getElementById("insights");
    if (!box) return;
    box.innerHTML = "";
    data.insights.forEach(i => {
        const li = document.createElement("li");
        li.innerText = i;
        box.appendChild(li);
    });
}

function drawHistogram(data) {
    const numericCols = data.overview.numeric_columns;
    if (!numericCols.length) return;

    const firstCol = numericCols[0];
    const histData = data.visualization.histograms[firstCol];
    if (!histData) return;

    const canvas = document.getElementById("histChart");
    if (!canvas) return;

    if (histChart) histChart.destroy();
    histChart = new Chart(canvas, {
        type: "bar",
        data: {
            labels: histData.bins,
            datasets: [{
                label: firstCol,
                data: histData.counts,
                backgroundColor: "rgba(0,229,255,0.5)",
                borderColor: "rgba(0,229,255,0.8)",
                borderWidth: 1
            }]
        },
        options: { responsive: true }
    });
}

function drawCorrelation(data) {
    const corr = data.advanced_visualization?.correlation;
    if (!corr) return;

    const labels = Object.keys(corr);
    if (!labels.length) return;

    const canvas = document.getElementById("heatmapChart");
    if (!canvas) return;

    if (heatmapChart) heatmapChart.destroy();
    heatmapChart = new Chart(canvas, {
        type: "bar",
        data: {
            labels: labels,
            datasets: [{
                label: "Correlation",
                data: Object.values(corr[labels[0]]),
                backgroundColor: "rgba(124,77,255,0.6)"
            }]
        },
        options: { responsive: true }
    });
}


// =====================================================
//  NEW OVERVIEW SECTION
// =====================================================
function renderOverview(d) {
    const ov = d.overview;

    const set = (id, val) => { const el = document.getElementById(id); if (el) el.textContent = val; };

    set('s-rows', ov.rows.toLocaleString());
    set('s-cols', ov.columns);
    set('s-num',  ov.numeric_columns.length);
    set('s-cat',  ov.categorical_columns.length);

    const numNames = document.getElementById('s-num-names');
    const catNames = document.getElementById('s-cat-names');
    if (numNames) numNames.textContent = ov.numeric_columns.slice(0, 4).join(', ') + (ov.numeric_columns.length > 4 ? '...' : '');
    if (catNames) catNames.textContent = ov.categorical_columns.slice(0, 4).join(', ') + (ov.categorical_columns.length > 4 ? '...' : '');

    const tbody = document.getElementById('colOverviewBody');
    if (!tbody) return;
    tbody.innerHTML = '';

    const mp      = d.missing_handling_process;
    const nu      = d.nunique;
    const typeMap = {};

    ov.numeric_columns.forEach(c    => typeMap[c] = 'Numeric');
    ov.categorical_columns.forEach(c => typeMap[c] = 'Categorical');
    ov.datetime_columns.forEach(c   => typeMap[c] = 'DateTime');

    const allCols = [...ov.numeric_columns, ...ov.categorical_columns, ...ov.datetime_columns];

    allCols.forEach((col, i) => {
        const mb   = mp[col]?.missing_before ?? 0;
        const pct  = ov.rows > 0 ? ((mb / ov.rows) * 100).toFixed(1) : 0;
        const cov  = (100 - pct).toFixed(1);
        const type = typeMap[col] || 'Unknown';

        tbody.innerHTML += `
            <tr>
                <td>${i + 1}</td>
                <td style="font-family:var(--font-mono);color:var(--accent);font-size:11px;">${col}</td>
                <td><span class="badge ${type === 'Numeric' ? 'active' : ''}">${type}</span></td>
                <td>${nu[col] ?? '—'}</td>
                <td style="color:${mb > 0 ? 'var(--red)' : 'var(--green)'}">${mb}</td>
                <td style="color:${mb > 0 ? 'var(--yellow)' : 'var(--text-dim)'}">${pct}%</td>
                <td>
                    <div class="progress-wrap" style="min-width:80px;">
                        <div class="progress-fill" style="width:${cov}%"></div>
                    </div>
                </td>
            </tr>
        `;
    });
}


// =====================================================
//  NEW DATA QUALITY SECTION WITH FIXED TOGGLE
// =====================================================
function renderQuality(d) {
    const mp    = d.missing_handling_process;
    const dupes = d.data_quality?.duplicates ?? 0;

    const set = (id, val) => { const el = document.getElementById(id); if (el) el.textContent = val; };
    set('q-dupes', dupes);

    const missingCols = Object.entries(mp).filter(([, v]) => v.missing_before > 0);
    set('q-missing-cols', missingCols.length);

    // ── Setup toggle buttons ──
    setupMissingToggle(d);

    // ── Cleaning table ──
    const tbody = document.getElementById('cleaningBody');
    if (!tbody) return;
    tbody.innerHTML = '';

    Object.entries(mp).forEach(([col, val]) => {
        const fixed = val.missing_before > val.missing_after;
        const status = val.missing_before === 0 ? '✔ Clean'
                     : fixed ? '✔ Fixed'
                     : '⚠ Remaining';

        tbody.innerHTML += `
            <tr>
                <td style="font-family:var(--font-mono);font-size:11px;color:var(--accent)">${col}</td>
                <td style="font-family:var(--font-mono);font-size:11px;color:var(--text-dim)">${val.col_type || '—'}</td>
                <td style="color:${val.missing_before > 0 ? 'var(--red)' : 'var(--text-dim)'}">${val.missing_before}</td>
                <td style="color:${val.missing_after  > 0 ? 'var(--yellow)' : 'var(--green)'}">${val.missing_after}</td>
                <td style="font-family:var(--font-mono);font-size:10px;color:var(--text-dim)">${val.fill_value ?? '—'}</td>
                <td style="font-family:var(--font-mono);font-size:10px;color:var(--accent)">${val.method || '—'}</td>
                <td style="color:${val.missing_before === 0 || fixed ? 'var(--green)' : 'var(--yellow)'}">
                    ${status}
                </td>
            </tr>
        `;
    });
}

// ══════════════════════════════════════════════════════
// MISSING VALUE TOGGLE HANDLER (NEW!)
// ══════════════════════════════════════════════════════
function setupMissingToggle(d) {
    const btnBefore    = document.getElementById('btnMissingBefore');
    const btnHandling  = document.getElementById('btnMissingHandling');
    const btnAfter     = document.getElementById('btnMissingAfter');
    const panelDiv     = document.getElementById('missingPanel');

    if (!btnBefore || !btnHandling || !btnAfter || !panelDiv) return;

    // Remove old listeners
    const newBtnBefore   = btnBefore.cloneNode(true);
    const newBtnHandling = btnHandling.cloneNode(true);
    const newBtnAfter    = btnAfter.cloneNode(true);

    btnBefore.parentNode.replaceChild(newBtnBefore, btnBefore);
    btnHandling.parentNode.replaceChild(newBtnHandling, btnHandling);
    btnAfter.parentNode.replaceChild(newBtnAfter, btnAfter);

    // Default: show BEFORE
    renderMissingBefore(d, panelDiv);
    newBtnBefore.classList.add('active');

    newBtnBefore.addEventListener('click', () => {
        newBtnBefore.classList.add('active');
        newBtnHandling.classList.remove('active');
        newBtnAfter.classList.remove('active');
        renderMissingBefore(d, panelDiv);
    });

    newBtnHandling.addEventListener('click', () => {
        newBtnBefore.classList.remove('active');
        newBtnHandling.classList.add('active');
        newBtnAfter.classList.remove('active');
        renderMissingHandling(d, panelDiv);
    });

    newBtnAfter.addEventListener('click', () => {
        newBtnBefore.classList.remove('active');
        newBtnHandling.classList.remove('active');
        newBtnAfter.classList.add('active');
        renderMissingAfter(d, panelDiv);
    });
}

function renderMissingBefore(d, panelDiv) {
    const mp = d.missing_handling_process;
    let html = `
        <div class="mv-view-title">📋 DATASET STATE BEFORE CLEANING</div>
        <div class="mv-summary">
            <div class="mv-chip red">${Object.values(mp).filter(v => v.missing_before > 0).length} columns with missing</div>
            <div class="mv-chip yellow">${Object.values(mp).reduce((a, v) => a + v.missing_before, 0)} total missing values</div>
        </div>
    `;

    Object.entries(mp).forEach(([col, val]) => {
        if (val.missing_before === 0) return;
        const pct = d.overview.rows > 0 ? ((val.missing_before / d.overview.rows) * 100).toFixed(1) : 0;
        html += `
            <div class="mv-block" style="margin-bottom:12px;">
                <div style="display:flex;justify-content:space-between;margin-bottom:8px;">
                    <span style="font-family:var(--font-mono);color:var(--accent);font-size:11px;">${col}</span>
                    <span style="color:var(--red);font-family:var(--font-mono);font-size:11px;">${val.missing_before} missing (${pct}%)</span>
                </div>
                <div class="progress-wrap">
                    <div class="progress-fill" style="width:${pct}%;background:var(--red);"></div>
                </div>
            </div>
        `;
    });

    panelDiv.innerHTML = html;
}

function renderMissingHandling(d, panelDiv) {
    const mp = d.missing_handling_process;
    let html = `
        <div class="mv-view-title">⚙️ HANDLING STRATEGY</div>
    `;

    const numeric = [];
    const categorical = [];

    Object.entries(mp).forEach(([col, val]) => {
        if (val.col_type === 'Numeric') numeric.push([col, val]);
        else if (val.col_type === 'Categorical') categorical.push([col, val]);
    });

    if (numeric.length > 0) {
        html += `<div style="margin-bottom:16px;">
            <div style="color:var(--green);font-family:var(--font-mono);font-size:12px;margin-bottom:8px;">🔢 NUMERIC COLUMNS</div>`;
        numeric.forEach(([col, val]) => {
            html += `
                <div class="mv-block" style="margin-bottom:8px;">
                    <div style="color:var(--accent);font-family:var(--font-mono);font-size:11px;margin-bottom:6px;">${col}</div>
                    <div style="color:var(--text-dim);font-size:12px;">→ ${val.fill_strategy || 'No missing values'}</div>
                </div>
            `;
        });
        html += '</div>';
    }

    if (categorical.length > 0) {
        html += `<div>
            <div style="color:var(--yellow);font-family:var(--font-mono);font-size:12px;margin-bottom:8px;">📝 CATEGORICAL COLUMNS</div>`;
        categorical.forEach(([col, val]) => {
            html += `
                <div class="mv-block" style="margin-bottom:8px;">
                    <div style="color:var(--accent);font-family:var(--font-mono);font-size:11px;margin-bottom:6px;">${col}</div>
                    <div style="color:var(--text-dim);font-size:12px;">→ ${val.fill_strategy || 'No missing values'}</div>
                </div>
            `;
        });
        html += '</div>';
    }

    panelDiv.innerHTML = html;
}

function renderMissingAfter(d, panelDiv) {
    const mp = d.missing_handling_process;
    const remaining = Object.values(mp).filter(v => v.missing_after > 0);
    let html = `
        <div class="mv-view-title">✅ DATASET STATE AFTER CLEANING</div>
        <div class="mv-summary">
            <div class="mv-chip green">${remaining.length === 0 ? '✔ All missing values handled!' : remaining.length + ' columns still have missing'}</div>
            <div class="mv-chip accent2">${d.overview.rows.toLocaleString()} rows preserved</div>
        </div>
    `;

    Object.entries(mp).forEach(([col, val]) => {
        const status = val.missing_after === 0 ? '✔ Clean' : '⚠ Remaining';
        const statusColor = val.missing_after === 0 ? 'var(--green)' : 'var(--yellow)';
        html += `
            <div class="mv-block" style="margin-bottom:12px;">
                <div style="display:flex;justify-content:space-between;margin-bottom:8px;">
                    <span style="font-family:var(--font-mono);color:var(--accent);font-size:11px;">${col}</span>
                    <span style="color:${statusColor};font-family:var(--font-mono);font-size:11px;">${status}</span>
                </div>
                <div style="color:var(--text-dim);font-size:11px;margin-bottom:6px;">Method: ${val.method}</div>
                ${val.missing_after > 0 ? `<div style="color:var(--yellow);font-size:11px;">⚠ ${val.missing_after} still missing</div>` : ''}
            </div>
        `;
    });

    panelDiv.innerHTML = html;
}


// =====================================================
//  NEW STRUCTURE SECTION
// =====================================================
function renderStructure(d) {
    const dfInfoEl = document.getElementById('dfInfo');
    if (dfInfoEl) dfInfoEl.textContent = d.dataset_info;

    const tbody = document.getElementById('nuniqBody');
    if (!tbody) return;
    tbody.innerHTML = '';

    const rows = d.overview.rows;
    Object.entries(d.nunique).forEach(([col, cnt]) => {
        const card = cnt === rows     ? 'Likely ID'
                   : cnt <= 2        ? 'Binary'
                   : cnt <= 10       ? 'Low'
                   : cnt <= 50       ? 'Medium'
                   :                   'High';
        tbody.innerHTML += `
            <tr>
                <td style="font-family:var(--font-mono);font-size:11px;color:var(--accent)">${col}</td>
                <td>${cnt}</td>
                <td><span class="badge">${card}</span></td>
            </tr>
        `;
    });
}


// =====================================================
//  NEW VALUE COUNTS SECTION
// =====================================================
function renderValueCountsNew(d) {
    const sel = document.getElementById('vcColSelect');
    if (!sel) return;

    sel.innerHTML = '';
    Object.keys(d.value_counts).forEach(col => {
        sel.innerHTML += `<option value="${col}">${col}</option>`;
    });

    // Remove duplicate listeners by replacing element
    const newSel = sel.cloneNode(true);
    sel.parentNode.replaceChild(newSel, sel);
    newSel.addEventListener('change', () => fillVCTable(d, newSel.value));

    if (newSel.options.length > 0) fillVCTable(d, newSel.options[0].value);
}

function fillVCTable(d, col) {
    const counts = d.value_counts[col];
    if (!counts) return;

    const total = Object.values(counts).reduce((a, b) => a + b, 0);
    const tbody = document.getElementById('vcBody');
    if (!tbody) return;
    tbody.innerHTML = '';

    const titleEl = document.getElementById('vcTitle');
    if (titleEl) titleEl.textContent = `Value Distribution — ${col}`;

    Object.entries(counts)
        .sort((a, b) => b[1] - a[1])
        .slice(0, 50)
        .forEach(([val, cnt]) => {
            const pct = total > 0 ? ((cnt / total) * 100).toFixed(1) : 0;
            tbody.innerHTML += `
                <tr>
                    <td>${val}</td>
                    <td>${cnt.toLocaleString()}</td>
                    <td style="color:var(--text-dim)">${pct}%</td>
                </tr>
            `;
        });
}


// =====================================================
//  CHART BUILDER (new section)
// =====================================================
function renderChartBuilder(d) {
    const xSel = document.getElementById('xAxisCol');
    const ySel = document.getElementById('yAxisCol');
    if (!xSel || !ySel) return;

    xSel.innerHTML = '';
    ySel.innerHTML = '<option value="count">Count (auto)</option>';

    const allCols = [...d.overview.numeric_columns, ...d.overview.categorical_columns];
    allCols.forEach(col => {
        xSel.innerHTML += `<option value="${col}">${col}</option>`;
        ySel.innerHTML += `<option value="${col}">${col}</option>`;
    });

    // Also populate old Advanced EDA selects if they exist
    const xAxisOld = document.getElementById('xAxis');
    const yAxisOld = document.getElementById('yAxis');
    if (xAxisOld) {
        xAxisOld.innerHTML = '';
        allCols.forEach(col => { xAxisOld.innerHTML += `<option value="${col}">${col}</option>`; });
    }
    if (yAxisOld) {
        yAxisOld.innerHTML = '<option value="">None</option>';
        allCols.forEach(col => { yAxisOld.innerHTML += `<option value="${col}">${col}</option>`; });
    }

    // Wire up build button (avoid duplicate listeners)
    const btn = document.getElementById('buildChartBtn');
    if (btn) {
        const newBtn = btn.cloneNode(true);
        btn.parentNode.replaceChild(newBtn, btn);
        newBtn.addEventListener('click', () => buildChart(d));
    }

    // Wire up old updateChart button
    const oldBtn = document.getElementById('updateChart');
    if (oldBtn) {
        const newOld = oldBtn.cloneNode(true);
        oldBtn.parentNode.replaceChild(newOld, oldBtn);
        newOld.addEventListener('click', () => buildChartOld(d));
    }

    // Wire up numeric/category selects for auto charts
    const numSel = document.getElementById('numericSelect');
    const catSel = document.getElementById('categorySelect');
    if (numSel) {
        numSel.innerHTML = '';
        d.overview.numeric_columns.forEach(col => {
            numSel.innerHTML += `<option value="${col}">${col}</option>`;
        });
    }
    if (catSel) {
        catSel.innerHTML = '';
        d.overview.categorical_columns.forEach(col => {
            catSel.innerHTML += `<option value="${col}">${col}</option>`;
        });
    }
}

// New chart builder renderer
function buildChart(d) {
    const type  = activeChartType;
    const xCol  = document.getElementById('xAxisCol')?.value;
    const yCol  = document.getElementById('yAxisCol')?.value;
    const title = document.getElementById('chartTitle')?.value || xCol;

    const titleEl = document.getElementById('chartDisplayTitle');
    if (titleEl) titleEl.textContent = title;

    const canvas = document.getElementById('mainChart');
    if (!canvas) return;

    if (mainChart) mainChart.destroy();

    const colors = generateColors(30);
    const ctx    = canvas.getContext('2d');

    // ── Histogram ──
    if (type === 'histogram') {
        const histData = d.visualization.histograms[xCol];
        if (!histData) { toast('⚠ SELECT A NUMERIC COLUMN'); return; }
        mainChart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: histData.bins.map(b => Number(b).toFixed(1)),
                datasets: [{
                    label: xCol,
                    data: histData.counts,
                    backgroundColor: 'rgba(0,229,255,0.5)',
                    borderColor:     'rgba(0,229,255,0.8)',
                    borderWidth: 1,
                    borderRadius: 2
                }]
            },
            options: buildChartOptions(title)
        });
        return;
    }

    // ── Scatter ──
    if (type === 'scatter') {
        if (!d.preview || yCol === 'count') { toast('⚠ SELECT Y AXIS COLUMN FOR SCATTER'); return; }
        const pts = d.preview
            .map(row => ({ x: row[xCol], y: row[yCol] }))
            .filter(p => p.x != null && p.y != null);
        mainChart = new Chart(ctx, {
            type: 'scatter',
            data: {
                datasets: [{
                    label: `${xCol} vs ${yCol}`,
                    data: pts,
                    backgroundColor: 'rgba(124,77,255,0.6)',
                    pointRadius: 5
                }]
            },
            options: buildChartOptions(title)
        });
        return;
    }

    // ── Categorical charts (bar / line / pie / doughnut / radar) ──
    const vc = d.value_counts[xCol];

    if (!vc) {
        // Fallback: numeric histogram
        const histData = d.visualization.histograms[xCol];
        if (histData) {
            mainChart = new Chart(ctx, {
                type: (type === 'line') ? 'line' : 'bar',
                data: {
                    labels: histData.bins.map(b => Number(b).toFixed(1)),
                    datasets: [{
                        label: xCol,
                        data: histData.counts,
                        backgroundColor: colors[0],
                        borderColor:     colors[0],
                        borderWidth: 1,
                        borderRadius: 2
                    }]
                },
                options: buildChartOptions(title)
            });
        } else {
            toast('⚠ NO DATA FOR SELECTED COLUMN');
        }
        return;
    }

    const sorted = Object.entries(vc).sort((a, b) => b[1] - a[1]).slice(0, 30);
    const labels = sorted.map(e => e[0]);
    const vals   = sorted.map(e => e[1]);

    mainChart = new Chart(ctx, {
        type: type,
        data: {
            labels,
            datasets: [{
                label: xCol,
                data:  vals,
                backgroundColor: colors,
                borderColor:     type === 'line' ? colors[0] : colors,
                borderWidth:     type === 'line' ? 2 : 1,
                fill:            type === 'line',
                tension:         0.3,
                pointRadius:     type === 'line' ? 4 : undefined
            }]
        },
        options: buildChartOptions(title)
    });
}

// Old advanced EDA chart builder (backward compatible)
function buildChartOld(d) {
    const type   = document.getElementById('chartType')?.value || 'bar';
    const xCol   = document.getElementById('xAxis')?.value;
    const yCol   = document.getElementById('yAxis')?.value;
    const canvas = document.getElementById('histChart');

    if (!canvas || !xCol) return;
    if (histChart) histChart.destroy();

    const colors = generateColors(20);
    const ctx    = canvas.getContext('2d');

    if (type === 'histogram') {
        const histData = d.visualization.histograms[xCol];
        if (!histData) { toast('⚠ SELECT A NUMERIC COLUMN FOR HISTOGRAM'); return; }
        histChart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: histData.bins.map(b => Number(b).toFixed(1)),
                datasets: [{
                    label: xCol,
                    data: histData.counts,
                    backgroundColor: 'rgba(0,229,255,0.5)',
                    borderColor:     'rgba(0,229,255,0.8)',
                    borderWidth: 1
                }]
            },
            options: buildChartOptions(xCol)
        });
        return;
    }

    if (type === 'scatter' && yCol) {
        const pts = d.preview
            .map(row => ({ x: row[xCol], y: row[yCol] }))
            .filter(p => p.x != null && p.y != null);
        histChart = new Chart(ctx, {
            type: 'scatter',
            data: { datasets: [{ label: `${xCol} vs ${yCol}`, data: pts, backgroundColor: 'rgba(124,77,255,0.6)' }] },
            options: buildChartOptions(`${xCol} vs ${yCol}`)
        });
        return;
    }

    const vc = d.value_counts[xCol];
    if (vc) {
        const sorted = Object.entries(vc).sort((a, b) => b[1] - a[1]).slice(0, 20);
        histChart = new Chart(ctx, {
            type: type,
            data: {
                labels: sorted.map(e => e[0]),
                datasets: [{
                    label: xCol,
                    data:  sorted.map(e => e[1]),
                    backgroundColor: colors,
                    borderColor:     colors,
                    borderWidth: 1
                }]
            },
            options: buildChartOptions(xCol)
        });
    } else {
        const histData = d.visualization.histograms[xCol];
        if (!histData) return;
        histChart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: histData.bins.map(b => Number(b).toFixed(1)),
                datasets: [{ label: xCol, data: histData.counts, backgroundColor: colors[0] }]
            },
            options: buildChartOptions(xCol)
        });
    }
}


// =====================================================
//  CHART HELPERS
// =====================================================
function generateColors(n) {
    const palette = [
        'rgba(0,229,255,0.7)',   'rgba(124,77,255,0.7)', 'rgba(255,107,53,0.7)',
        'rgba(0,230,118,0.7)',   'rgba(255,215,64,0.7)', 'rgba(255,82,82,0.7)',
        'rgba(64,196,255,0.7)',  'rgba(197,17,98,0.7)',  'rgba(0,191,165,0.7)',
        'rgba(255,171,64,0.7)'
    ];
    const out = [];
    for (let i = 0; i < n; i++) out.push(palette[i % palette.length]);
    return out;
}

function buildChartOptions(title) {
    return {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: {
                labels: { color: '#7986a3', font: { size: 12 } }
            },
            title: {
                display: !!title,
                text:    title,
                color:   '#e8eaf6',
                font:    { size: 13 }
            }
        },
        scales: {
            x: {
                ticks: { color: '#7986a3', font: { size: 11 }, maxRotation: 45 },
                grid:  { color: 'rgba(37,45,61,0.6)' }
            },
            y: {
                ticks: { color: '#7986a3', font: { size: 11 } },
                grid:  { color: 'rgba(37,45,61,0.6)' }
            }
        }
    };
}


// =====================================================
//  CORRELATION SECTION
// =====================================================
function renderCorrelation(d) {
    const corr = d.advanced_visualization?.correlation;

    const tableDiv = document.getElementById('correlationTable');
    const corrCanvas = document.getElementById('corrChart');
    const heatCanvas = document.getElementById('heatmapChart');

    if (!corr || !Object.keys(corr).length) {
        if (tableDiv) tableDiv.innerHTML = '<p style="color:var(--text-dim)">No numeric columns found for correlation.</p>';
        return;
    }

    const cols = Object.keys(corr);

    // ── HTML correlation table ──
    if (tableDiv) {
        let html = '<table><thead><tr><th></th>';
        cols.forEach(c => { html += `<th style="font-size:10px;">${c}</th>`; });
        html += '</tr></thead><tbody>';

        cols.forEach(row => {
            html += `<tr><td style="font-family:var(--font-mono);font-size:11px;color:var(--accent)">${row}</td>`;
            cols.forEach(col => {
                const val = corr[row]?.[col] ?? 0;
                const abs = Math.abs(val);
                const color = val >= 0.7  ? 'var(--green)'
                            : val >= 0.3  ? 'var(--yellow)'
                            : abs >= 0.7  ? 'var(--red)'
                            :               'var(--text-dim)';
                html += `<td style="color:${color};font-family:var(--font-mono);font-size:11px">${val.toFixed(2)}</td>`;
            });
            html += '</tr>';
        });

        html += '</tbody></table>';
        tableDiv.innerHTML = html;
    }

    // ── Correlation bar chart (new canvas) ──
    if (corrCanvas) {
        const firstCol = cols[0];
        const barLabels = cols.filter(c => c !== firstCol);
        const barVals   = barLabels.map(c => corr[firstCol]?.[c] ?? 0);

        if (corrChart) corrChart.destroy();
        corrChart = new Chart(corrCanvas.getContext('2d'), {
            type: 'bar',
            data: {
                labels: barLabels,
                datasets: [{
                    label: `Correlation with ${firstCol}`,
                    data:  barVals,
                    backgroundColor: barVals.map(v => v >= 0 ? 'rgba(0,229,255,0.6)' : 'rgba(255,82,82,0.6)'),
                    borderRadius: 3
                }]
            },
            options: {
                ...buildChartOptions(`Correlation — ${firstCol}`),
                scales: {
                    x: { ticks: { color: '#7986a3' }, grid: { color: 'rgba(37,45,61,0.6)' } },
                    y: { ticks: { color: '#7986a3' }, grid: { color: 'rgba(37,45,61,0.6)' }, min: -1, max: 1 }
                }
            }
        });
    }

    // ── Old heatmap canvas (backward compatible) ──
    if (heatCanvas) {
        if (heatmapChart) heatmapChart.destroy();
        heatmapChart = new Chart(heatCanvas.getContext('2d'), {
            type: 'bar',
            data: {
                labels: cols,
                datasets: [{
                    label: 'Correlation',
                    data: Object.values(corr[cols[0]]),
                    backgroundColor: 'rgba(124,77,255,0.6)'
                }]
            },
            options: { responsive: true }
        });
    }
}


// =====================================================
//  INSIGHTS SECTION
// =====================================================
function renderInsightsNew(d) {
    const box = document.getElementById('insightsBox');
    if (!box) return;
    box.innerHTML = '';
    d.insights.forEach(insight => {
        box.innerHTML += `
            <div class="insight-item">
                <div class="insight-dot"></div>
                <span>${insight}</span>
            </div>
        `;
    });
}


// =====================================================
//  PREVIEW SECTION WITH VIEW OPTIONS (NEW!)
// =====================================================
function renderPreviewNew(d) {
    const div = document.getElementById('previewTable');
    if (!div || !d.preview?.length) return;

    const controlsDiv = document.createElement('div');
    controlsDiv.style.cssText = 'margin-bottom:16px;display:flex;gap:10px;flex-wrap:wrap;';
    controlsDiv.innerHTML = `
        <button class="btn btn-outline" data-view="head5">HEAD(5)</button>
        <button class="btn btn-outline" data-view="head20">HEAD(20)</button>
        <button class="btn btn-outline" data-view="tail5">TAIL(5)</button>
        <button class="btn btn-outline" data-view="tail20">TAIL(20)</button>
        <button class="btn btn-primary" data-view="full">FULL DATASET</button>
    `;

    div.parentElement.insertBefore(controlsDiv, div);

    // Button handlers
    controlsDiv.querySelectorAll('button').forEach(btn => {
        btn.addEventListener('click', () => {
            controlsDiv.querySelectorAll('button').forEach(b => b.classList.remove('btn-primary'));
            controlsDiv.querySelectorAll('button').forEach(b => b.classList.add('btn-outline'));
            btn.classList.remove('btn-outline');
            btn.classList.add('btn-primary');

            const view = btn.dataset.view;
            renderDataPreview(d, div, view);
        });
    });

    // Default: HEAD(10)
    renderDataPreview(d, div, 'head10');
}

function renderDataPreview(d, div, view) {
    let data = d.preview;

    if (view === 'head5')  data = d.preview.slice(0, 5);
    else if (view === 'head20') data = d.preview.slice(0, 20);
    else if (view === 'tail5')  data = d.preview.slice(-5);
    else if (view === 'tail20') data = d.preview.slice(-20);
    // else view === 'full' — use all

    const cols = Object.keys(data[0]);
    let html = '<table><thead><tr>';
    cols.forEach((c, i) => { html += `<th>#${i + 1}<br>${c}</th>`; });
    html += '</tr></thead><tbody>';

    data.forEach((row, rowIdx) => {
        html += '<tr>';
        cols.forEach(c => { html += `<td>${row[c] ?? '—'}</td>`; });
        html += '</tr>';
    });

    html += '</tbody></table>';
    html = `<p style="color:var(--text-dim);font-size:12px;margin-bottom:12px;font-family:var(--font-mono);">Showing ${data.length} of ${d.preview.length} rows</p>` + html;
    div.innerHTML = html;
}


// =====================================================
//  FILTER CONTROLS (backward compatible)
// =====================================================
const filterColEl = document.getElementById('filterColumn');
const applyFilterBtn = document.getElementById('applyFilter');

if (filterColEl && applyFilterBtn) {
    filterColEl.addEventListener('change', () => {
        if (!globalData) return;
        const col    = filterColEl.value;
        const valSel = document.getElementById('filterValue');
        if (!valSel) return;
        valSel.innerHTML = '<option value="">All</option>';
        const counts = globalData.value_counts[col];
        if (counts) {
            Object.keys(counts).forEach(v => {
                valSel.innerHTML += `<option value="${v}">${v}</option>`;
            });
        }
    });

    applyFilterBtn.addEventListener('click', () => {
        if (!globalData) return;
        toast('Filter applied (preview only — server-side filtering coming soon)');
    });
}


// =====================================================
//  ZOOM CONTROLS (backward compatible)
// =====================================================
let chartScale = 1;
const zoomIn  = document.getElementById('zoomIn');
const zoomOut = document.getElementById('zoomOut');

if (zoomIn) {
    zoomIn.addEventListener('click', () => {
        chartScale = Math.min(chartScale + 0.1, 2);
        applyZoom();
    });
}

if (zoomOut) {
    zoomOut.addEventListener('click', () => {
        chartScale = Math.max(chartScale - 0.1, 0.5);
        applyZoom();
    });
}

function applyZoom() {
    document.querySelectorAll('.chart-box').forEach(box => {
        box.style.transform = `scale(${chartScale})`;
        box.style.transformOrigin = 'top left';
    });
}


// =====================================================
//  NUMERIC / CATEGORY SELECT → auto draw (old HTML)
// =====================================================
const numericSelectEl  = document.getElementById('numericSelect');
const categorySelectEl = document.getElementById('categorySelect');

if (numericSelectEl) {
    numericSelectEl.addEventListener('change', () => {
        if (!globalData) return;
        const col      = numericSelectEl.value;
        const histData = globalData.visualization.histograms[col];
        if (!histData) return;
        if (histChart) histChart.destroy();
        histChart = new Chart(
            document.getElementById('histChart').getContext('2d'),
            {
                type: 'bar',
                data: {
                    labels: histData.bins.map(b => Number(b).toFixed(1)),
                    datasets: [{
                        label: col,
                        data: histData.counts,
                        backgroundColor: 'rgba(0,229,255,0.5)',
                        borderColor:     'rgba(0,229,255,0.8)',
                        borderWidth: 1
                    }]
                },
                options: buildChartOptions(col)
            }
        );
    });
}

if (categorySelectEl) {
    categorySelectEl.addEventListener('change', () => {
        if (!globalData) return;
        const col    = categorySelectEl.value;
        const counts = globalData.value_counts[col];
        if (!counts) return;
        const sorted = Object.entries(counts).sort((a, b) => b[1] - a[1]).slice(0, 20);
        const canvas = document.getElementById('catChart');
        if (!canvas) return;

        // Destroy previous catChart if tracked
        if (window._catChart) window._catChart.destroy();
        window._catChart = new Chart(canvas.getContext('2d'), {
            type: 'bar',
            data: {
                labels: sorted.map(e => e[0]),
                datasets: [{
                    label: col,
                    data:  sorted.map(e => e[1]),
                    backgroundColor: generateColors(sorted.length)
                }]
            },
            options: buildChartOptions(col)
        });
    });
}
