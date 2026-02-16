async function uploadFile() {

    const fileInput = document.getElementById("fileInput");
    const file = fileInput.files[0];

    if (!file) {
        alert("Please select file");
        return;
    }

    let formData = new FormData();
    formData.append("file", file);

    const response = await fetch("/upload", {
        method: "POST",
        body: formData
    });

    const data = await response.json();

    console.log(data);

    // OVERVIEW
    document.getElementById("rows").innerText = data.overview.rows;
    document.getElementById("columns").innerText = data.overview.columns;
    document.getElementById("numeric").innerText =
        data.overview.numeric_columns.join(", ");
    document.getElementById("categorical").innerText =
        data.overview.categorical_columns.join(", ");

    // DATA QUALITY
    document.getElementById("duplicates").innerText =
        data.data_quality.duplicates;

    let missingHTML = "";
    for (let key in data.data_quality.missing_values) {
        missingHTML += `${key}: ${data.data_quality.missing_values[key]}<br>`;
    }
    document.getElementById("missing").innerHTML = missingHTML;

    // INSIGHTS
    let insightsHTML = "";
    data.insights.forEach(i => {
        insightsHTML += `<li>${i}</li>`;
    });
    document.getElementById("insights").innerHTML = insightsHTML;

    // PREVIEW TABLE
    let table = "<table border='1'><tr>";
    Object.keys(data.preview[0]).forEach(col => {
        table += `<th>${col}</th>`;
    });
    table += "</tr>";

    data.preview.forEach(row => {
        table += "<tr>";
        Object.values(row).forEach(val => {
            table += `<td>${val}</td>`;
        });
        table += "</tr>";
    });

    table += "</table>";
    document.getElementById("preview").innerHTML = table;
}
