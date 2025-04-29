document.addEventListener("DOMContentLoaded", function () {
    const fileInput = document.getElementById("file");
    const preview = document.getElementById("preview");

    fileInput.addEventListener("change", function (event) {
        const file = event.target.files[0];
        if (file && file.type.startsWith("image/")) {
            const reader = new FileReader();
            reader.onload = function (e) {
                preview.src = e.target.result;
                preview.style.display = "block";
            };
            reader.readAsDataURL(file);
        } else {
            preview.src = "#";
            preview.style.display = "none";
        }
    });
});
