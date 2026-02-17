// ================= GLOBAL VARIABLES =================
let histChart = null;
let catChart = null;
let heatmapChart = null;
let missingChart = null;

let globalData = null;
let chartScale = 1;


// ================= UPLOAD DATASET =================
document.getElementById("uploadBtn")
.addEventListener("click", async () => {

    const file = document.getElementById("fileInput").files[0];

    if (!file) {
        alert("Select file first");
        return;
    }

    const formData = new FormData();
    formData.append("file", file);

    try {

        const response = await fetch("/upload", {
            method: "POST",
            body: formData
        });

        const data = await response.json();

        // ✅ FIX — only show error if backend sends error
        if (!response.ok || data.error) {
            console.error(data);
            alert(data.error || "Error processing dataset");
            return;
        }

        globalData = data;

        loadOverview(data);
        loadInsights(data);
        loadPreview(data);
        loadDropdowns(data);

        drawCharts(data);
        drawHeatmap(data);
        drawMissing(data);

    } catch (err) {
        console.error(err);
        alert("Server error. Please try again.");
    }
});


// ================= OVERVIEW =================
function loadOverview(data) {

    document.getElementById("rows").innerText =
        data.overview.rows;

    document.getElementById("columns").innerText =
        data.overview.columns;

    document.getElementById("numericColumns").innerText =
        data.overview.numeric_columns.join(", ");

    document.getElementById("categoricalColumns").innerText =
        data.overview.categorical_columns.join(", ");

    if (document.getElementById("duplicates") &&
        data.data_quality?.duplicates !== undefined) {

        document.getElementById("duplicates").innerText =
            data.data_quality.duplicates;
    }
}


// ================= INSIGHTS =================
function loadInsights(data) {

    const insightBox = document.getElementById("insights");
    insightBox.innerHTML = "";

    data.insights.forEach(i => {
        const li = document.createElement("li");
        li.innerText = i;
        insightBox.appendChild(li);
    });
}


// ================= PREVIEW TABLE =================
function loadPreview(data) {

    const previewDiv = document.getElementById("preview");
    previewDiv.innerHTML = "";

    if (!data.preview || data.preview.length === 0) return;

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

    previewDiv.innerHTML = table;
}


// ================= DROPDOWNS =================
function loadDropdowns(data) {

    const numSelect = document.getElementById("numericSelect");
    const catSelect = document.getElementById("categorySelect");
    const filterColumn = document.getElementById("filterColumn");
    const xAxis = document.getElementById("xAxis");
    const yAxis = document.getElementById("yAxis");

    numSelect.innerHTML = "";
    catSelect.innerHTML = "";
    filterColumn.innerHTML = "";
    xAxis.innerHTML = "";
    yAxis.innerHTML = "";

    data.overview.numeric_columns.forEach(col => {
        numSelect.innerHTML += `<option>${col}</option>`;
        xAxis.innerHTML += `<option>${col}</option>`;
        yAxis.innerHTML += `<option>${col}</option>`;
    });

    data.overview.categorical_columns.forEach(col => {
        catSelect.innerHTML += `<option>${col}</option>`;
        filterColumn.innerHTML += `<option>${col}</option>`;
    });

    updateFilterValues();
}


// ================= FILTER VALUES =================
document.getElementById("filterColumn")
.addEventListener("change", updateFilterValues);

function updateFilterValues() {

    if (!globalData) return;

    const col =
        document.getElementById("filterColumn").value;

    const values =
        globalData.visualization?.category_counts?.[col];

    const filterValue =
        document.getElementById("filterValue");

    filterValue.innerHTML = "";

    if (!values) return;

    Object.keys(values).forEach(v => {
        filterValue.innerHTML += `<option>${v}</option>`;
    });
}


// ================= APPLY FILTER =================
document.getElementById("applyFilter")
.addEventListener("click", () => {
    if (globalData) drawCharts(globalData);
});


// ================= MAIN CHARTS =================
function drawCharts(data) {

    const numCol =
        document.getElementById("numericSelect").value;

    const catCol =
        document.getElementById("categorySelect").value;

    // ================= HISTOGRAM =================
    if (histChart) histChart.destroy();

    const histData =
        data.visualization.histograms[numCol];

    if (!histData) return;

    histChart = new Chart(
        document.getElementById("histChart"),
        {
            type: "bar",
            data: {
                labels: histData.bins,
                datasets: [{
                    label: numCol,
                    data: histData.counts
                }]
            },
            options: { responsive: true }
        }
    );

    // ================= CATEGORY COUNT =================
    if (catChart) catChart.destroy();

    const obj =
        data.visualization.category_counts[catCol];

    if (!obj) return;

    catChart = new Chart(
        document.getElementById("catChart"),
        {
            type: "bar",
            data: {
                labels: Object.keys(obj),
                datasets: [{
                    label: catCol,
                    data: Object.values(obj)
                }]
            },
            options: { responsive: true }
        }
    );
}


// ================= ADVANCED CHART =================
document.getElementById("updateChart")
.addEventListener("click", () => {
    if (globalData) drawAdvancedChart(globalData);
});

function drawAdvancedChart(data) {

    const type =
        document.getElementById("chartType").value;

    const xCol =
        document.getElementById("xAxis").value;

    const yCol =
        document.getElementById("yAxis").value;

    if (histChart) histChart.destroy();

    if (type === "histogram") {
        drawCharts(data);
        return;
    }

    if (type === "scatter") {

        const xData =
            data.visualization.histograms[xCol]?.bins;

        const yData =
            data.visualization.histograms[yCol]?.counts;

        if (!xData || !yData) return;

        const len = Math.min(xData.length, yData.length);

        const scatterData = [];

        for (let i = 0; i < len; i++) {
            scatterData.push({ x: xData[i], y: yData[i] });
        }

        histChart = new Chart(
            document.getElementById("histChart"),
            {
                type: "scatter",
                data: {
                    datasets: [{
                        label: `${xCol} vs ${yCol}`,
                        data: scatterData
                    }]
                }
            }
        );
    }
}


// ================= HEATMAP =================
function drawHeatmap(data) {

    const corr =
        data.advanced_visualization?.correlation;

    if (!corr) return;

    const labels = Object.keys(corr);
    if (labels.length === 0) return;

    if (heatmapChart) heatmapChart.destroy();

    heatmapChart = new Chart(
        document.getElementById("heatmapChart"),
        {
            type: "bar",
            data: {
                labels: labels,
                datasets: [{
                    label: "Correlation",
                    data: Object.values(corr[labels[0]])
                }]
            }
        }
    );
}


// ================= MISSING VALUES =================
function drawMissing(data) {

    const obj =
        data.data_quality?.missing_values;

    if (!obj) return;

    if (missingChart) missingChart.destroy();

    missingChart = new Chart(
        document.getElementById("missingChart"),
        {
            type: "bar",
            data: {
                labels: Object.keys(obj),
                datasets: [{
                    label: "Missing Values",
                    data: Object.values(obj)
                }]
            }
        }
    );
}


// ================= CHART RESIZE =================
document.getElementById("zoomIn")
.addEventListener("click", () => {
    chartScale += 0.2;
    document.getElementById("histChart").style.transform =
        `scale(${chartScale})`;
});

document.getElementById("zoomOut")
.addEventListener("click", () => {
    chartScale = Math.max(0.5, chartScale - 0.2);
    document.getElementById("histChart").style.transform =
        `scale(${chartScale})`;
});
