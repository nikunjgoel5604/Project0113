const uploadBtn = document.getElementById("uploadBtn");

uploadBtn.addEventListener("click", async () => {

    const fileInput = document.getElementById("fileInput");
    const file = fileInput.files[0];

    if (!file) {
        alert("Select a file first");
        return;
    }

    const formData = new FormData();
    formData.append("file", file);

    const response = await fetch("/upload", {
        method: "POST",
        body: formData
    });

    const data = await response.json();

    console.log(data);

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

    const insightBox = document.getElementById("insights");
    insightBox.innerHTML = "";

    data.insights.forEach(i => {
        const li = document.createElement("li");
        li.innerText = i;
        insightBox.appendChild(li);
    });

    const previewDiv = document.getElementById("preview");
    previewDiv.innerHTML = "";

    if (data.preview.length > 0) {

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
        previewDiv.innerHTML = table;
    }
});
