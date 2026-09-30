const API_BASE_URL = "http://127.0.0.1:8000";

window.addEventListener("load", () => {
    setTimeout(() => {
        document.getElementById("intro").classList.add("hide");
    }, 1800);
});

const fileInput = document.getElementById("fileInput");
const uploadCard = document.getElementById("uploadCard");
const previewCard = document.getElementById("previewCard");
const processingCard = document.getElementById("processingCard");
const resultCard = document.getElementById("resultCard");
const previewImage = document.getElementById("previewImage");
const fileName = document.getElementById("fileName");
const removeBtn = document.getElementById("removeBtn");
const analyzeBtn = document.getElementById("analyzeBtn");
const newAnalysisBtn = document.getElementById("newAnalysisBtn");
const progressBar = document.getElementById("progressBar");
const progressPercent = document.getElementById("progressPercent");
const processingText = document.getElementById("processingText");
const stages = document.querySelectorAll(".stages span");
const errorMessage = document.getElementById("errorMessage");

let selectedFile = null;

fileInput.addEventListener("change", () => {
    if (fileInput.files.length) {
        showPreview(fileInput.files[0]);
    }
});

function showPreview(file) {
    if (!file.type.startsWith("image/")) {
        alert("Please select an image.");
        return;
    }

    selectedFile = file;
    previewImage.src = URL.createObjectURL(file);
    fileName.textContent = file.name;

    uploadCard.classList.add("hidden");
    processingCard.classList.add("hidden");
    resultCard.classList.add("hidden");
    previewCard.classList.remove("hidden");
}

uploadCard.addEventListener("dragover", (event) => {
    event.preventDefault();
    uploadCard.classList.add("dragging");
});

uploadCard.addEventListener("dragleave", () => {
    uploadCard.classList.remove("dragging");
});

uploadCard.addEventListener("drop", (event) => {
    event.preventDefault();
    uploadCard.classList.remove("dragging");

    const file = event.dataTransfer.files[0];
    if (file) {
        showPreview(file);
    }
});

removeBtn.addEventListener("click", resetUI);
newAnalysisBtn.addEventListener("click", resetUI);

analyzeBtn.addEventListener("click", async () => {
    if (!selectedFile) {
        return;
    }

    previewCard.classList.add("hidden");
    resultCard.classList.add("hidden");
    processingCard.classList.remove("hidden");

    await runAnalysis(selectedFile);
});

async function runAnalysis(file) {
    let progress = 0;
    progressBar.style.width = "0%";
    progressPercent.textContent = "0%";
    errorMessage.classList.add("hidden");

    stages.forEach((stage) => stage.classList.remove("active"));
    stages[0].classList.add("active");

    const progressTimer = setInterval(() => {
        if (progress < 90) {
            progress += 3;
            progressBar.style.width = `${progress}%`;
            progressPercent.textContent = `${progress}%`;
            updateStage(progress);
        }
    }, 120);

    try {
        const formData = new FormData();
        formData.append("file", file);

        const response = await fetch(`${API_BASE_URL}/predict`, {
            method: "POST",
            body: formData,
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail || "The backend could not analyze this image.");
        }

        clearInterval(progressTimer);
        progressBar.style.width = "100%";
        progressPercent.textContent = "100%";
        stages.forEach((stage) => stage.classList.remove("active"));
        stages[3].classList.add("active");
        processingText.textContent = "Analysis complete.";

        setTimeout(() => showResult(data), 250);
    } catch (error) {
        clearInterval(progressTimer);
        progressBar.style.width = "100%";
        progressPercent.textContent = "!";
        processingText.textContent = "Analysis failed.";
        errorMessage.textContent = `${error.message} Make sure the FastAPI backend is running on port 8000.`;
        errorMessage.classList.remove("hidden");
    }
}

function updateStage(progress) {
    stages.forEach((stage) => stage.classList.remove("active"));

    if (progress < 25) {
        stages[0].classList.add("active");
        processingText.textContent = "Preprocessing image...";
    } else if (progress < 50) {
        stages[1].classList.add("active");
        processingText.textContent = "Extracting image features...";
    } else if (progress < 80) {
        stages[2].classList.add("active");
        processingText.textContent = "Running quantum analysis...";
    } else {
        stages[3].classList.add("active");
        processingText.textContent = "Classifying image...";
    }
}

function showResult(data) {
    processingCard.classList.add("hidden");
    resultCard.classList.remove("hidden");

    document.getElementById("classificationText").textContent = data.classification;

    setProbability("real", data.percentages.completely_real);
    setProbability("modified", data.percentages.modified_using_ai);
    setProbability("ai", data.percentages.completely_ai_generated);

    const quantum = data.quantum_analysis;

    if (!quantum || quantum.enabled === false) {
        document.getElementById("quantumResult").classList.add("hidden");
        return;
    }

    document.getElementById("quantumResult").classList.remove("hidden");
    document.getElementById("qSearchSpace").textContent = quantum.search_space_size;
    document.getElementById("qQubits").textContent = quantum.qubits;
    document.getElementById("qIterations").textContent = quantum.grover_iterations;
    document.getElementById("qPatch").textContent = `#${quantum.selected_patch_index}`;
    document.getElementById("quantumNote").textContent = quantum.note;
}

function setProbability(prefix, value) {
    const safeValue = Math.max(0, Math.min(100, Number(value) || 0));
    document.getElementById(`${prefix}Percent`).textContent = `${safeValue.toFixed(2)}%`;
    document.getElementById(`${prefix}Bar`).style.width = `${safeValue}%`;
}

function resetUI() {
    if (previewImage.src.startsWith("blob:")) {
        URL.revokeObjectURL(previewImage.src);
    }

    selectedFile = null;
    fileInput.value = "";
    previewImage.src = "";
    fileName.textContent = "";

    uploadCard.classList.remove("hidden");
    previewCard.classList.add("hidden");
    processingCard.classList.add("hidden");
    resultCard.classList.add("hidden");
    errorMessage.classList.add("hidden");
}
