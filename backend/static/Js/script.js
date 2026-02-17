let histChart = null;
let catChart = null;
let globalData = null;


// ================= UPLOAD =================
document.getElementById("uploadBtn")
.addEventListener("click", async () => {

    const file = document.getElementById("fileInput").files[0];
    if (!file) return alert("Select file first");

    const formData = new FormData();
    formData.append("file", file);

    const response = await fetch("/upload", {
        method: "POST",
        body: formData
    });

    const data = await response.json();
    globalData = data;

    loadOverview(data);
    loadDropdowns(data);
    loadPreview(data.preview);
    drawCharts(data.preview);
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

    document.getElementById("duplicates").innerText =
        data.data_quality.duplicates;
}


// ================= DROPDOWNS =================
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


// ================= FILTER VALUES =================
document.getElementById("filterColumn")
.addEventListener("change", updateFilterValues);

function updateFilterValues() {

    const col =
        document.getElementById("filterColumn").value;

    const filterValue =
        document.getElementById("filterValue");

    filterValue.innerHTML = "";

    // unique values from preview data
    const uniqueValues = [
        ...new Set(globalData.preview.map(r => r[col]))
    ];

    uniqueValues.forEach(v => {
        filterValue.innerHTML += `<option value="${v}">${v}</option>`;
    });
}


// ================= APPLY FILTER =================
document.getElementById("applyFilter")
.addEventListener("click", () => {

    const filterCol =
        document.getElementById("filterColumn").value;

    const filterVal =
        document.getElementById("filterValue").value;

    // FILTER DATA
    const filteredData =
        globalData.preview.filter(
            row => String(row[filterCol]) === String(filterVal)
        );

    loadPreview(filteredData);
    drawCharts(filteredData);
});


// ================= PREVIEW TABLE =================
function loadPreview(dataRows) {

    const previewDiv = document.getElementById("preview");
    previewDiv.innerHTML = "";

    if (!dataRows.length) return;

    let table = "<table border='1'><tr>";

    Object.keys(dataRows[0]).forEach(col => {
        table += `<th>${col}</th>`;
    });

    table += "</tr>";

    dataRows.forEach(row => {
        table += "<tr>";
        Object.values(row).forEach(val => {
            table += `<td>${val}</td>`;
        });
        table += "</tr>";
    });

    table += "</table>";
    previewDiv.innerHTML = table;
}


// ================= DRAW CHARTS =================
function drawCharts(dataRows) {

    const numCol =
        document.getElementById("numericSelect").value;

    const catCol =
        document.getElementById("categorySelect").value;

    // ---------- HISTOGRAM ----------
    const numericValues =
        dataRows.map(r => Number(r[numCol]))
                .filter(v => !isNaN(v));

    if (histChart) histChart.destroy();

    histChart = new Chart(
        document.getElementById("histChart"),
        {
            type: "bar",
            data: {
                labels: numericValues.slice(0,20),
                datasets: [{
                    label: numCol,
                    data: numericValues.slice(0,20)
                }]
            }
        }
    );


    // ---------- CATEGORY COUNT ----------
    const counts = {};
    dataRows.forEach(r => {
        const key = r[catCol];
        counts[key] = (counts[key] || 0) + 1;
    });

    if (catChart) catChart.destroy();

    catChart = new Chart(
        document.getElementById("catChart"),
        {
            type: "bar",
            data: {
                labels: Object.keys(counts),
                datasets: [{
                    label: catCol,
                    data: Object.values(counts)
                }]
            }
        }
    );
}
