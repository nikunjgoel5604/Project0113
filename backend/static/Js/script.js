// =============================
// GLOBAL CHART VARIABLES
// =============================
let histChart = null;
let catChart = null;


// =============================
// UPLOAD BUTTON EVENT
// =============================
document.getElementById("uploadBtn")
.addEventListener("click", async () => {

    const fileInput = document.getElementById("fileInput");
    const file = fileInput.files[0];

    if (!file) {
        alert("Please select a file first");
        return;
    }

    // Prepare form data
    const formData = new FormData();
    formData.append("file", file);

    try {

        // Send file to backend
        const response = await fetch("/upload", {
            method: "POST",
            body: formData
        });

        const data = await response.json();

        console.log("EDA RESPONSE:", data);

        // If backend error
        if (data.error) {
            alert(data.error);
            return;
        }

        // =============================
        // DATASET OVERVIEW
        // =============================
        document.getElementById("rows").innerText =
            data.overview?.rows ?? "-";

        document.getElementById("columns").innerText =
            data.overview?.columns ?? "-";

        document.getElementById("numericColumns").innerText =
            data.overview?.numeric_columns?.join(", ") ?? "-";

        document.getElementById("categoricalColumns").innerText =
            data.overview?.categorical_columns?.join(", ") ?? "-";


        // =============================
        // DUPLICATE COUNT
        // =============================
        if (document.getElementById("duplicates")) {
            document.getElementById("duplicates").innerText =
                data.data_quality?.duplicates ?? "-";
        }


        // =============================
        // INSIGHTS
        // =============================
        const insightBox = document.getElementById("insights");
        insightBox.innerHTML = "";

        if (data.insights) {
            data.insights.forEach(i => {
                const li = document.createElement("li");
                li.innerText = i;
                insightBox.appendChild(li);
            });
        }


        // =============================
        // PREVIEW TABLE
        // =============================
        const previewDiv = document.getElementById("preview");
        previewDiv.innerHTML = "";

        if (data.preview && data.preview.length > 0) {

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


        // =============================
        // HISTOGRAM CHART
        // =============================
        if (data.visualization &&
            data.visualization.histograms) {

            const numericCols =
                Object.keys(data.visualization.histograms);

            if (numericCols.length > 0) {

                const col = numericCols[0];
                const values =
                    data.visualization.histograms[col];

                if (histChart) histChart.destroy();

                histChart = new Chart(
                    document.getElementById("histChart"),
                    {
                        type: "bar",
                        data: {
                            labels: values.slice(0, 20),
                            datasets: [{
                                label: col,
                                data: values.slice(0, 20)
                            }]
                        },
                        options: {
                            responsive: true,
                            plugins: {
                                legend: { display: true }
                            }
                        }
                    }
                );
            }
        }


        // =============================
        // CATEGORY COUNT CHART
        // =============================
        if (data.visualization &&
            data.visualization.category_counts) {

            const catCols =
                Object.keys(data.visualization.category_counts);

            if (catCols.length > 0) {

                const col = catCols[0];
                const obj =
                    data.visualization.category_counts[col];

                if (catChart) catChart.destroy();

                catChart = new Chart(
                    document.getElementById("catChart"),
                    {
                        type: "bar",
                        data: {
                            labels: Object.keys(obj),
                            datasets: [{
                                label: col,
                                data: Object.values(obj)
                            }]
                        },
                        options: {
                            responsive: true
                        }
                    }
                );
            }
        }

    } catch (error) {
        console.error(error);
        alert("Error processing file. Check backend.");
    }

});
