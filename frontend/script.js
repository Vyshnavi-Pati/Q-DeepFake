// ============================================================
// QDEEPFAKE FRONTEND
// ============================================================

const API_BASE_URL = "http://127.0.0.1:8000";


// ============================================================
// INTRO
// ============================================================

window.addEventListener("load", () => {

    setTimeout(() => {

        const intro =
            document.getElementById("intro");

        if (intro) {
            intro.classList.add("hide");
        }

    }, 1800);

});


// ============================================================
// DOM REFERENCES
// ============================================================

const fileInput =
    document.getElementById("fileInput");

const uploadCard =
    document.getElementById("uploadCard");

const previewCard =
    document.getElementById("previewCard");

const processingCard =
    document.getElementById("processingCard");

const resultCard =
    document.getElementById("resultCard");

const previewImage =
    document.getElementById("previewImage");

const fileName =
    document.getElementById("fileName");

const removeBtn =
    document.getElementById("removeBtn");

const analyzeBtn =
    document.getElementById("analyzeBtn");

const newAnalysisBtn =
    document.getElementById("newAnalysisBtn");

const progressBar =
    document.getElementById("progressBar");

const progressPercent =
    document.getElementById("progressPercent");

const processingText =
    document.getElementById("processingText");

const stages =
    document.querySelectorAll(".stages span");

const errorMessage =
    document.getElementById("errorMessage");

const forensicImage =
    document.getElementById("forensicImage");

const patchOverlay =
    document.getElementById("patchOverlay");

const patchGrid =
    document.getElementById("patchGrid");

const candidateList =
    document.getElementById("candidateList");

const foundPatchesList =
    document.getElementById("foundPatchesList");

const roundsList =
    document.getElementById("roundsList");

const measurementChart =
    document.getElementById("measurementChart");


// ============================================================
// STATE
// ============================================================

let selectedFile = null;
let currentResult = null;


// ============================================================
// FILE INPUT
// ============================================================

fileInput.addEventListener(
    "change",
    () => {

        if (fileInput.files.length) {

            showPreview(
                fileInput.files[0]
            );

        }

    }
);


// ============================================================
// SHOW PREVIEW
// ============================================================

function showPreview(file) {

    if (!file.type.startsWith("image/")) {

        alert(
            "Please select an image."
        );

        return;
    }

    selectedFile = file;

    previewImage.src =
        URL.createObjectURL(file);

    fileName.textContent =
        file.name;

    uploadCard.classList.add(
        "hidden"
    );

    processingCard.classList.add(
        "hidden"
    );

    resultCard.classList.add(
        "hidden"
    );

    previewCard.classList.remove(
        "hidden"
    );
}


// ============================================================
// DRAG & DROP
// ============================================================

uploadCard.addEventListener(
    "dragover",
    (event) => {

        event.preventDefault();

        uploadCard.classList.add(
            "dragging"
        );

    }
);

uploadCard.addEventListener(
    "dragleave",
    () => {

        uploadCard.classList.remove(
            "dragging"
        );

    }
);

uploadCard.addEventListener(
    "drop",
    (event) => {

        event.preventDefault();

        uploadCard.classList.remove(
            "dragging"
        );

        const file =
            event.dataTransfer.files[0];

        if (file) {

            showPreview(
                file
            );

        }

    }
);


// ============================================================
// BUTTONS
// ============================================================

removeBtn.addEventListener(
    "click",
    resetUI
);

newAnalysisBtn.addEventListener(
    "click",
    resetUI
);


analyzeBtn.addEventListener(
    "click",
    async () => {

        if (!selectedFile) {
            return;
        }

        previewCard.classList.add(
            "hidden"
        );

        resultCard.classList.add(
            "hidden"
        );

        processingCard.classList.remove(
            "hidden"
        );

        await runAnalysis(
            selectedFile
        );

    }
);


// ============================================================
// RUN ANALYSIS
// ============================================================

async function runAnalysis(file) {

    let progress = 0;

    progressBar.style.width =
        "0%";

    progressPercent.textContent =
        "0%";

    processingText.textContent =
        "Preparing image...";

    errorMessage.classList.add(
        "hidden"
    );


    stages.forEach(
        (stage) =>
            stage.classList.remove(
                "active"
            )
    );

    stages[0].classList.add(
        "active"
    );


    const progressTimer =
        setInterval(
            () => {

                if (progress < 90) {

                    progress += 3;

                    progressBar.style.width =
                        `${progress}%`;

                    progressPercent.textContent =
                        `${progress}%`;

                    updateStage(
                        progress
                    );

                }

            },
            120
        );


    try {

        const formData =
            new FormData();

        formData.append(
            "file",
            file
        );


        const response =
            await fetch(
                `${API_BASE_URL}/predict`,
                {
                    method: "POST",
                    body: formData,
                }
            );


        const data =
            await response.json();


        if (!response.ok) {

            throw new Error(
                data.detail ||
                "The backend could not analyze this image."
            );

        }


        clearInterval(
            progressTimer
        );


        progressBar.style.width =
            "100%";

        progressPercent.textContent =
            "100%";


        stages.forEach(
            (stage) =>
                stage.classList.remove(
                    "active"
                )
        );

        stages[3].classList.add(
            "active"
        );


        processingText.textContent =
            "Analysis complete.";


        currentResult =
            data;


        setTimeout(
            () => {

                showResult(
                    data
                );

            },
            250
        );


    } catch (error) {

        clearInterval(
            progressTimer
        );

        progressBar.style.width =
            "100%";

        progressPercent.textContent =
            "!";

        processingText.textContent =
            "Analysis failed.";

        errorMessage.textContent =
            `${error.message} Make sure the FastAPI backend is running on port 8000.`;

        errorMessage.classList.remove(
            "hidden"
        );

    }

}


// ============================================================
// PROCESSING STAGES
// ============================================================

function updateStage(progress) {

    stages.forEach(
        (stage) =>
            stage.classList.remove(
                "active"
            )
    );


    if (progress < 25) {

        stages[0].classList.add(
            "active"
        );

        processingText.textContent =
            "Preprocessing image...";

    } else if (progress < 50) {

        stages[1].classList.add(
            "active"
        );

        processingText.textContent =
            "Running classical AI...";

    } else if (progress < 75) {

        stages[2].classList.add(
            "active"
        );

        processingText.textContent =
            "Scoring image patches...";

    } else {

        stages[3].classList.add(
            "active"
        );

        processingText.textContent =
            "Running Grover search...";

    }

}


// ============================================================
// SHOW FINAL RESULT
// ============================================================

function showResult(data) {

    processingCard.classList.add(
        "hidden"
    );

    resultCard.classList.remove(
        "hidden"
    );


    // --------------------------------------------------------
    // CLASSIFICATION
    // --------------------------------------------------------

    document.getElementById(
        "classificationText"
    ).textContent =
        data.classification;


    // --------------------------------------------------------
    // PROBABILITIES
    // --------------------------------------------------------

    setProbability(
        "real",
        data.percentages.completely_real
    );

    setProbability(
        "ai",
        data.percentages.completely_ai_generated
    );

    setProbability(
        "modified",
        data.percentages.modified_using_ai
    );


    // --------------------------------------------------------
    // IMAGE
    // --------------------------------------------------------

    forensicImage.src =
        previewImage.src;


    forensicImage.onload = () => {

        renderForensicOverlay(
            data.quantum_analysis
        );

    };


    // --------------------------------------------------------
    // QUANTUM
    // --------------------------------------------------------

    const quantum =
        data.quantum_analysis;


    if (
        !quantum
        || quantum.enabled === false
    ) {

        hideQuantum();

        return;
    }


    renderQuantum(
        quantum
    );

}


// ============================================================
// PROBABILITY BARS
// ============================================================

function setProbability(
    prefix,
    value
) {

    const safeValue =
        Math.max(
            0,
            Math.min(
                100,
                Number(value) || 0
            )
        );


    document.getElementById(
        `${prefix}Percent`
    ).textContent =
        `${safeValue.toFixed(2)}%`;


    document.getElementById(
        `${prefix}Bar`
    ).style.width =
        `${safeValue}%`;

}


// ============================================================
// RENDER QUANTUM SECTION
// ============================================================

function renderQuantum(
    quantum
) {

    const markedIndices =
        Array.isArray(
            quantum.marked_indices
        )
            ? quantum.marked_indices
            : [];


    const foundIndices =
        Array.isArray(
            quantum.found_indices
        )
            ? quantum.found_indices
            : [];


    const patches =
        Array.isArray(
            quantum.patches
        )
            ? quantum.patches
            : [];


    const rounds =
        Array.isArray(
            quantum.search_rounds
        )
            ? quantum.search_rounds
            : [];


    const threshold =
        Number(
            quantum.suspicion_threshold || 0
        );


    // --------------------------------------------------------
    // PATCH SUMMARY
    // --------------------------------------------------------

    document.getElementById(
        "totalPatches"
    ).textContent =
        quantum.search_space_size;


    document.getElementById(
        "markedPatches"
    ).textContent =
        markedIndices.length;


    const coverage =
        Number(
            quantum.patch_coverage || 0
        ) * 100;


    document.getElementById(
        "patchCoverage"
    ).textContent =
        `${coverage.toFixed(1)}%`;


    document.getElementById(
        "thresholdValue"
    ).textContent =
        `${(threshold * 100).toFixed(0)}%`;


    // --------------------------------------------------------
    // QUANTUM FLOW
    // --------------------------------------------------------

    document.getElementById(
        "quantumSearchSpace"
    ).textContent =
        quantum.search_space_size;


    document.getElementById(
        "quantumQubits"
    ).textContent =
        quantum.qubits;


    document.getElementById(
        "quantumMarked"
    ).textContent =
        markedIndices.length;


    document.getElementById(
        "quantumFound"
    ).textContent =
        foundIndices.length;


    // --------------------------------------------------------
    // METRICS
    // --------------------------------------------------------

    document.getElementById(
        "qSearchSpace"
    ).textContent =
        quantum.search_space_size;


    document.getElementById(
        "qQubits"
    ).textContent =
        quantum.qubits;


    document.getElementById(
        "qThreshold"
    ).textContent =
        `${(threshold * 100).toFixed(0)}%`;


    document.getElementById(
        "qFoundCount"
    ).textContent =
        `${foundIndices.length}/${markedIndices.length}`;


    // --------------------------------------------------------
    // STATUS
    // --------------------------------------------------------

    const quantumStatus =
        document.getElementById(
            "quantumStatus"
        );


    const quantumCheck =
        document.getElementById(
            "quantumCheck"
        );


    if (markedIndices.length === 0) {

        quantumStatus.textContent =
            "No patches crossed the threshold — Grover search skipped.";

        quantumCheck.textContent =
            "—";

        quantumCheck.classList.add(
            "neutral"
        );

    } else {

        quantumStatus.textContent =
            `${foundIndices.length} of ${markedIndices.length} marked patches found by Grover.`;

        quantumCheck.textContent =
            foundIndices.length ===
            markedIndices.length
                ? "✓"
                : "!";

        quantumCheck.classList.remove(
            "neutral"
        );

    }


    // --------------------------------------------------------
    // FOUND PATCHES
    // --------------------------------------------------------

    foundPatchesList.innerHTML =
        "";


    if (foundIndices.length === 0) {

        const empty =
            document.createElement(
                "div"
            );

        empty.className =
            "empty-message";

        empty.textContent =
            "No suspicious patches were found.";

        foundPatchesList.appendChild(
            empty
        );

    } else {

        foundIndices.forEach(
            (index) => {

                const chip =
                    document.createElement(
                        "div"
                    );

                chip.className =
                    "found-chip";

                chip.textContent =
                    `Patch #${index}`;

                foundPatchesList.appendChild(
                    chip
                );

            }
        );

    }


    // --------------------------------------------------------
    // PATCH GRID
    // --------------------------------------------------------

    renderPatchGrid(
        patches,
        markedIndices,
        foundIndices
    );


    // --------------------------------------------------------
    // TOP CANDIDATES
    // --------------------------------------------------------

    renderTopCandidates(
        quantum.top_candidates || []
    );


    // --------------------------------------------------------
    // SEARCH ROUNDS
    // --------------------------------------------------------

    renderSearchRounds(
        rounds
    );


    // --------------------------------------------------------
    // MEASUREMENT
    // --------------------------------------------------------

    if (
        rounds.length > 0
        && rounds[0].counts
    ) {

        renderMeasurementChart(
            rounds[0].counts
        );

    } else {

        measurementChart.innerHTML =
            '<div class="empty-message">No quantum measurement was performed.</div>';

    }


    // --------------------------------------------------------
    // NOTE
    // --------------------------------------------------------

    document.getElementById(
        "quantumNote"
    ).textContent =
        quantum.note;

}


// ============================================================
// PATCH GRID
// ============================================================

function renderPatchGrid(
    patches,
    markedIndices,
    foundIndices
) {

    patchGrid.innerHTML =
        "";


    const ordered =
        [...patches].sort(
            (a, b) =>
                a.index - b.index
        );


    ordered.forEach(
        (patch) => {

            const cell =
                document.createElement(
                    "div"
                );


            const marked =
                markedIndices.includes(
                    patch.index
                );


            const found =
                foundIndices.includes(
                    patch.index
                );


            cell.className =
                "patch-cell";


            if (marked) {

                cell.classList.add(
                    "marked"
                );

            }


            if (found) {

                cell.classList.add(
                    "found"
                );

            }


            const tag =
                found
                    ? "GROVER FOUND"
                    : marked
                        ? "MARKED"
                        : "";


            const suspicious =
                (
                    Number(
                        patch.suspiciousness
                    ) || 0
                ) * 100;


            cell.innerHTML = `

                <div class="patch-index">
                    #${patch.index}
                </div>

                <div class="patch-score">
                    ${suspicious.toFixed(1)}%
                </div>

                <div class="patch-score-label">
                    SUSPICIOUS
                </div>

                ${
                    tag
                        ? `
                            <div class="patch-tag ${
                                found
                                    ? "found-tag"
                                    : ""
                            }">
                                ${tag}
                            </div>
                        `
                        : ""
                }

            `;


            patchGrid.appendChild(
                cell
            );

        }
    );

}


// ============================================================
// FORENSIC IMAGE OVERLAY
// ============================================================

function renderForensicOverlay(
    quantum
) {

    patchOverlay.innerHTML =
        "";


    if (!quantum) {
        return;
    }


    const patches =
        quantum.patches || [];


    const markedIndices =
        quantum.marked_indices || [];


    const foundIndices =
        quantum.found_indices || [];


    const naturalWidth =
        forensicImage.naturalWidth;


    const naturalHeight =
        forensicImage.naturalHeight;


    if (
        !naturalWidth
        || !naturalHeight
    ) {

        return;
    }


    patches.forEach(
        (patch) => {

            if (
                !markedIndices.includes(
                    patch.index
                )
            ) {

                return;
            }


            const box =
                document.createElement(
                    "div"
                );


            box.className =
                "patch-box";


            if (
                foundIndices.includes(
                    patch.index
                )
            ) {

                box.classList.add(
                    "found"
                );

            }


            const [
                left,
                top,
                right,
                bottom
            ] = patch.bbox;


            const leftPercent =
                (
                    left /
                    naturalWidth
                ) * 100;


            const topPercent =
                (
                    top /
                    naturalHeight
                ) * 100;


            const widthPercent =
                (
                    (right - left) /
                    naturalWidth
                ) * 100;


            const heightPercent =
                (
                    (bottom - top) /
                    naturalHeight
                ) * 100;


            box.style.left =
                `${leftPercent}%`;

            box.style.top =
                `${topPercent}%`;

            box.style.width =
                `${widthPercent}%`;

            box.style.height =
                `${heightPercent}%`;


            const label =
                document.createElement(
                    "span"
                );


            label.className =
                "patch-overlay-label";

            label.textContent =
                `#${patch.index}`;


            box.appendChild(
                label
            );


            patchOverlay.appendChild(
                box
            );

        }
    );

}


// ============================================================
// TOP CANDIDATES
// ============================================================

function renderTopCandidates(
    candidates
) {

    candidateList.innerHTML =
        "";


    if (
        !candidates.length
    ) {

        candidateList.innerHTML =
            '<div class="empty-message">No patch candidates available.</div>';

        return;
    }


    candidates.forEach(
        (candidate) => {

            const item =
                document.createElement(
                    "div"
                );


            const suspicious =
                (
                    Number(
                        candidate.suspiciousness
                    ) || 0
                ) * 100;


            item.className =
                "candidate-chip";


            item.innerHTML = `

                <span>
                    Patch #${candidate.index}
                </span>

                <strong>
                    ${suspicious.toFixed(1)}%
                </strong>

            `;


            candidateList.appendChild(
                item
            );

        }
    );

}


// ============================================================
// GROVER SEARCH ROUNDS
// ============================================================

function renderSearchRounds(
    rounds
) {

    roundsList.innerHTML =
        "";


    if (!rounds.length) {

        roundsList.innerHTML =
            '<div class="empty-message">Grover search was skipped because no patches crossed the threshold.</div>';

        return;
    }


    rounds.forEach(
        (round) => {

            const card =
                document.createElement(
                    "div"
                );

            card.className =
                "round-card";


            const marked =
                round.marked_indices || [];


            card.innerHTML = `

                <div class="round-number">
                    ROUND ${round.round}
                </div>

                <div class="round-main">

                    <div class="round-info">

                        <span>
                            SEARCHING AMONG
                        </span>

                        <strong>
                            ${
                                marked
                                    .map(
                                        (index) =>
                                            `#${index}`
                                    )
                                    .join(
                                        ", "
                                    )
                            }
                        </strong>

                    </div>


                    <div class="round-result">

                        <span>
                            RESULT
                        </span>

                        <strong>
                            #${round.selected_index}
                        </strong>

                    </div>

                </div>


                <div class="round-meta">

                    <span>
                        ${round.grover_iterations}
                        iteration${
                            round.grover_iterations === 1
                                ? ""
                                : "s"
                        }
                    </span>

                    <span>
                        ${round.shots}
                        shots
                    </span>

                    <span>
                        |${round.selected_bitstring}⟩
                    </span>

                </div>

            `;


            roundsList.appendChild(
                card
            );

        }
    );

}


// ============================================================
// MEASUREMENT COUNTS
// ============================================================

function renderMeasurementChart(
    counts
) {

    measurementChart.innerHTML =
        "";


    const entries =
        Object.entries(
            counts
        )
        .sort(
            (a, b) =>
                Number(b[1]) -
                Number(a[1])
        );


    if (!entries.length) {

        measurementChart.innerHTML =
            '<div class="empty-message">No measurements available.</div>';

        return;
    }


    const maxCount =
        Math.max(
            ...entries.map(
                ([, count]) =>
                    Number(count)
            )
        );


    entries.forEach(
        ([bitstring, count]) => {

            const row =
                document.createElement(
                    "div"
                );


            row.className =
                "measurement-row";


            const percentage =
                maxCount > 0
                    ? (
                        Number(count) /
                        maxCount
                    ) * 100
                    : 0;


            row.innerHTML = `

                <div class="measurement-code">
                    |${bitstring}⟩
                </div>

                <div class="measurement-track">

                    <div
                        class="measurement-fill"
                        style="width: ${percentage}%"
                    ></div>

                </div>

                <div class="measurement-count">
                    ${count}
                </div>

            `;


            measurementChart.appendChild(
                row
            );

        }
    );

}


// ============================================================
// HIDE QUANTUM
// ============================================================

function hideQuantum() {

    document.getElementById(
        "quantumStatus"
    ).textContent =
        "Quantum analysis unavailable.";

    document.getElementById(
        "quantumCheck"
    ).textContent =
        "—";

}


// ============================================================
// RESET
// ============================================================

function resetUI() {

    if (
        previewImage.src.startsWith(
            "blob:"
        )
    ) {

        URL.revokeObjectURL(
            previewImage.src
        );

    }


    selectedFile = null;

    currentResult = null;

    fileInput.value = "";

    previewImage.src = "";

    fileName.textContent =
        "";


    forensicImage.src =
        "";

    patchOverlay.innerHTML =
        "";

    patchGrid.innerHTML =
        "";

    candidateList.innerHTML =
        "";

    foundPatchesList.innerHTML =
        "";

    roundsList.innerHTML =
        "";

    measurementChart.innerHTML =
        "";


    uploadCard.classList.remove(
        "hidden"
    );

    previewCard.classList.add(
        "hidden"
    );

    processingCard.classList.add(
        "hidden"
    );

    resultCard.classList.add(
        "hidden"
    );

    errorMessage.classList.add(
        "hidden"
    );

}