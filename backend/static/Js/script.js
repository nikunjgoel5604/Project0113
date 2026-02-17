// =============================
// GLOBAL VARIABLES
// =============================
let histChart = null;
let catChart = null;
let globalData = null;


// =============================
// UPLOAD BUTTON EVENT
// =============================
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

        console.log("EDA RESPONSE:", data);

        if (data.error) {
            alert(data.error);
            return;
        }

        globalData = data;

        loadOverview(data);
        loadInsights(data);
        loadPreview(data);
        loadDropdowns(data);
        drawCharts(data);

    } catch (err) {
        console.error(err);
        alert("Backend error. Check server.");
    }
});


// =============================
// LOAD OVERVIEW
// =============================
function loadOverview(data) {

    document.getElementById("rows").innerText =
        data.overview?.rows ?? "-";

    document.getElementById("columns").innerText =
        data.overview?.columns ?? "-";

    document.getElementById("numericColumns").innerText =
        data.overview?.numeric_columns?.join(", ") ?? "-";

    document.getElementById("categoricalColumns").innerText =
        data.overview?.categorical_columns?.join(", ") ?? "-";

    if (document.getElementById("duplicates")) {
        document.getElementById("duplicates").innerText =
            data.data_quality?.duplicates ?? "-";
    }
}


// =============================
// LOAD INSIGHTS
// =============================
function loadInsights(data) {

    const insightBox = document.getElementById("insights");
    insightBox.innerHTML = "";

    if (!data.insights) return;

    data.insights.forEach(i => {
        const li = document.createElement("li");
        li.innerText = i;
        insightBox.appendChild(li);
    });
}


// =============================
// LOAD PREVIEW TABLE
// =============================
function loadPreview(data) {

    const previewDiv = document.getElementById("preview");
    previewDiv.innerHTML = "";

    if (!data.preview || data.preview.length === 0) return;

    let table = "<table border='1'><tr>";

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


// =============================
// LOAD DROPDOWNS
// =============================
function loadDropdowns(data) {

    const numSelect = document.getElementById("numericSelect");
    const catSelect = document.getElementById("categorySelect");
    const filterColumn = document.getElementById("filterColumn");

    numSelect.innerHTML = "";
    catSelect.innerHTML = "";
    filterColumn.innerHTML = "";

    data.overview.numeric_columns.forEach(col => {
        numSelect.innerHTML += `<option value="${col}">${col}</option>`;
    });

    data.overview.categorical_columns.forEach(col => {
        catSelect.innerHTML += `<option value="${col}">${col}</option>`;
        filterColumn.innerHTML += `<option value="${col}">${col}</option>`;
    });

    updateFilterValues();
}


// =============================
// FILTER VALUES UPDATE
// =============================
document.getElementById("filterColumn")
.addEventListener("change", updateFilterValues);

function updateFilterValues() {

    if (!globalData) return;

    const col = document.getElementById("filterColumn").value;

    const values =
        globalData.visualization?.category_counts?.[col];

    const filterValue =
        document.getElementById("filterValue");

    filterValue.innerHTML = "";

    if (!values) return;

    Object.keys(values).forEach(v => {
        filterValue.innerHTML += `<option value="${v}">${v}</option>`;
    });
}


// =============================
// APPLY FILTER BUTTON
// =============================
document.getElementById("applyFilter")
.addEventListener("click", () => {

    if (!globalData) return;
    drawCharts(globalData);
});


// =============================
// DRAW CHARTS
// =============================
function drawCharts(data) {

    const numCol =
        document.getElementById("numericSelect").value;

    const catCol =
        document.getElementById("categorySelect").value;


    // ---------- HISTOGRAM ----------
    if (histChart) histChart.destroy();

    const histValues =
        data.visualization?.histograms?.[numCol];

    if (histValues) {

        histChart = new Chart(
            document.getElementById("histChart"),
            {
                type: "bar",
                data: {
                    labels: histValues.slice(0, 20),
                    datasets: [{
                        label: numCol,
                        data: histValues.slice(0, 20)
                    }]
                },
                options: {
                    responsive: true
                }
            }
        );
    }


    // ---------- CATEGORY COUNT ----------
    if (catChart) catChart.destroy();

    const catObj =
        data.visualization?.category_counts?.[catCol];

    if (catObj) {

        catChart = new Chart(
            document.getElementById("catChart"),
            {
                type: "bar",
                data: {
                    labels: Object.keys(catObj),
                    datasets: [{
                        label: catCol,
                        data: Object.values(catObj)
                    }]
                },
                options: {
                    responsive: true
                }
            }
        );
    }
}
