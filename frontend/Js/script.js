const fileInput = document.getElementById("fileInput");

fileInput.addEventListener("change", function () {

    const file = fileInput.files[0];
    if (!file) return;

    // Basic file info
    document.getElementById("fileName").textContent = file.name;

    const sizeKB = (file.size / 1024).toFixed(2);
    document.getElementById("fileSize").textContent = sizeKB + " KB";

    const fileType = file.name.split(".").pop().toLowerCase();
    document.getElementById("fileType").textContent = fileType.toUpperCase();

    const reader = new FileReader();

    reader.onload = function (event) {

        const content = event.target.result;

        // CSV PROCESSING
        if (fileType === "csv") {

            const rows = content.trim().split("\n");
            const headers = rows[0].split(",");

            document.getElementById("rows").textContent = rows.length - 1;
            document.getElementById("columns").textContent = headers.length;
            document.getElementById("columnNames").textContent =
                headers.join(", ");

            createTable(headers, rows);

        }

        // XML PROCESSING
        else if (fileType === "xml") {

            const parser = new DOMParser();
            const xmlDoc = parser.parseFromString(content, "text/xml");

            const records = xmlDoc.children[0].children;

            if (records.length === 0) return;

            let headers = [];
            const firstRecord = records[0].children;

            for (let i = 0; i < firstRecord.length; i++) {
                headers.push(firstRecord[i].nodeName);
            }

            document.getElementById("rows").textContent = records.length;
            document.getElementById("columns").textContent = headers.length;
            document.getElementById("columnNames").textContent =
                headers.join(", ");

            // Build rows array
            let rows = [];
            for (let i = 0; i < records.length; i++) {
                let rowData = [];
                for (let j = 0; j < headers.length; j++) {
                    rowData.push(records[i].children[j].textContent);
                }
                rows.push(rowData.join(","));
            }

            createTable(headers, ["", ...rows]);
        }

        else {
            alert("Currently supported formats: CSV and XML");
        }
    };

    reader.readAsText(file);
});


// TABLE CREATION FUNCTION
function createTable(headers, rows) {

    let table = "<table border='1' cellpadding='5'>";

    table += "<tr>";
    headers.forEach(h => table += `<th>${h}</th>`);
    table += "</tr>";

    for (let i = 1; i <= Math.min(5, rows.length - 1); i++) {

        const cols = rows[i].split(",");
        table += "<tr>";

        cols.forEach(c => table += `<td>${c}</td>`);

        table += "</tr>";
    }

    table += "</table>";

    document.getElementById("tableContainer").innerHTML = table;
}
