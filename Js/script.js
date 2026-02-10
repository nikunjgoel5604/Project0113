const fileInput = document.getElementById("fileInput");

fileInput.addEventListener("change", function () {

    const file = fileInput.files[0];

    if (file) {

        // File name
        document.getElementById("fileName").textContent = file.name;

        // File size
        const sizeKB = (file.size / 1024).toFixed(2);
        document.getElementById("fileSize").textContent = sizeKB + " KB";
    }
});
