// ================= GLOBAL VARIABLES =================
let histChart = null;
let heatmapChart = null;
let missingChart = null;

let globalData = null;


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

        if (!response.ok || data.error) {
            alert(data.error || "Error processing dataset");
            return;
        }

        globalData = data;

        loadOverview(data);
        loadDatasetInfo(data);
        loadUniqueValues(data);
        loadMissingProcess(data);
        loadValueCounts(data);
        loadPreview(data);
        loadInsights(data);

        drawHistogram(data);
        drawCorrelation(data);

    } catch (err) {
        console.error(err);
        alert("Server error.");
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

    if (document.getElementById("dateColumns")) {
        document.getElementById("dateColumns").innerText =
            data.overview.datetime_columns.join(", ");
    }

    if (document.getElementById("duplicates")) {
        document.getElementById("duplicates").innerText =
            data.data_quality?.duplicates ?? 0;
    }
}


// ================= DATASET INFO (df.info) =================
function loadDatasetInfo(data) {

    const infoBox = document.getElementById("datasetInfo");

    if (!infoBox) return;

    infoBox.innerHTML =
        `<pre>${data.dataset_info}</pre>`;
}


// ================= UNIQUE VALUES =================
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


// ================= MISSING HANDLING PROCESS =================
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

    Object.entries(data.missing_handling_process)
    .forEach(([col, obj]) => {

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


// ================= VALUE COUNTS =================
function loadValueCounts(data) {

    const box = document.getElementById("valueCounts");

    if (!box) return;

    let html = "";

    Object.entries(data.value_counts)
    .forEach(([col, counts]) => {

        html += `<h3>${col}</h3>`;
        html += "<table><tr><th>Value</th><th>Count</th></tr>";

        Object.entries(counts)
        .forEach(([val, count]) => {

            html += `
                <tr>
                    <td>${val}</td>
                    <td>${count}</td>
                </tr>
            `;
        });

        html += "</table><br>";
    });

    box.innerHTML = html;
}


// ================= PREVIEW =================
function loadPreview(data) {

    const previewDiv = document.getElementById("preview");

    if (!previewDiv || !data.preview) return;

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


// ================= INSIGHTS =================
function loadInsights(data) {

    const insightBox = document.getElementById("insights");

    if (!insightBox) return;

    insightBox.innerHTML = "";

    data.insights.forEach(i => {
        const li = document.createElement("li");
        li.innerText = i;
        insightBox.appendChild(li);
    });
}


// ================= HISTOGRAM =================
function drawHistogram(data) {

    const numericCols =
        data.overview.numeric_columns;

    if (!numericCols.length) return;

    const firstCol = numericCols[0];

    const histData =
        data.visualization.histograms[firstCol];

    if (!histData) return;

    if (histChart) histChart.destroy();

    histChart = new Chart(
        document.getElementById("histChart"),
        {
            type: "bar",
            data: {
                labels: histData.bins,
                datasets: [{
                    label: firstCol,
                    data: histData.counts
                }]
            },
            options: { responsive: true }
        }
    );
}


// ================= CORRELATION =================
function drawCorrelation(data) {

    const corr =
        data.advanced_visualization.correlation;

    if (!corr) return;

    const labels = Object.keys(corr);

    if (!labels.length) return;

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
