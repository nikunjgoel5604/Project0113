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

        if (!response.ok || data.error) {
            alert(data.error || "Error processing dataset");
            return;
        }

        globalData = data;

        loadOverview(data);
        loadInsights(data);
        loadPreview(data);
        loadDropdowns(data);

        loadDatasetInfo(data);
        loadNunique(data);
        loadValueCounts(data);
        loadMissingProcess(data);

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

    if (document.getElementById("datetimeColumns")) {
        document.getElementById("datetimeColumns").innerText =
            data.overview.datetime_columns.join(", ");
    }

    document.getElementById("duplicates").innerText =
        data.data_quality.duplicates;
}


// ================= DATASET STRUCTURE (df.info) =================
function loadDatasetInfo(data) {

    const box = document.getElementById("datasetInfo");
    if (!box) return;

    let text = "";

    Object.keys(data.column_profile).forEach(col => {

        const obj = data.column_profile[col];

        text += `${col} | Type: ${obj.dtype} | Unique: ${obj.unique_values} | Missing: ${obj.missing_values}\n`;
    });

    box.innerText = text;
}


// ================= UNIQUE COUNT =================
function loadNunique(data) {

    const div = document.getElementById("nuniqueTable");
    if (!div) return;

    let table = "<table><tr><th>Column</th><th>Unique Values</th></tr>";

    Object.keys(data.column_profile).forEach(col => {
        table += `<tr>
                    <td>${col}</td>
                    <td>${data.column_profile[col].unique_values}</td>
                  </tr>`;
    });

    table += "</table>";

    div.innerHTML = table;
}


// ================= VALUE COUNTS =================
function loadValueCounts(data) {

    const div = document.getElementById("valueCounts");
    if (!div) return;

    div.innerHTML = "";

    const counts = data.visualization.category_counts;

    Object.keys(counts).forEach(col => {

        div.innerHTML += `<h4>${col}</h4>`;

        let table = "<table><tr><th>Value</th><th>Count</th></tr>";

        Object.keys(counts[col]).forEach(value => {
            table += `<tr>
                        <td>${value}</td>
                        <td>${counts[col][value]}</td>
                      </tr>`;
        });

        table += "</table><br>";

        div.innerHTML += table;
    });
}


// ================= MISSING HANDLING PROCESS =================
function loadMissingProcess(data) {

    const div = document.getElementById("missingProcess");
    if (!div) return;

    const missing = data.data_quality.missing_values;

    let table = "<table><tr><th>Column</th><th>Missing Count</th></tr>";

    Object.keys(missing).forEach(col => {
        table += `<tr>
                    <td>${col}</td>
                    <td>${missing[col]}</td>
                  </tr>`;
    });

    table += "</table>";

    div.innerHTML = table;
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


// ================= PREVIEW =================
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

    if (!numSelect || !catSelect) return;

    numSelect.innerHTML = "";
    catSelect.innerHTML = "";

    data.overview.numeric_columns.forEach(col => {
        numSelect.innerHTML += `<option>${col}</option>`;
    });

    data.overview.categorical_columns.forEach(col => {
        catSelect.innerHTML += `<option>${col}</option>`;
    });
}


// ================= CHARTS =================
function drawCharts(data) {

    const numCol = document.getElementById("numericSelect").value;
    const catCol = document.getElementById("categorySelect").value;

    if (histChart) histChart.destroy();
    if (catChart) catChart.destroy();

    const histData = data.visualization.histograms[numCol];
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
            }
        }
    );

    const obj = data.visualization.category_counts[catCol];
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
            }
        }
    );
}
