let currentThreadId = localStorage.getItem("travel_thread_id") || null;
let latestAnswerMarkdown = "";
let tripMap = null;

function setPrompt(text) {
    document.getElementById("userInput").value = text;
    document.getElementById("userInput").focus();
}

function setLoading(isLoading) {
    const sendBtn = document.getElementById("sendBtn");
    const btnText = document.getElementById("btnText");
    const btnLoader = document.getElementById("btnLoader");

    sendBtn.disabled = isLoading;

    if (isLoading) {
        btnText.classList.add("hidden");
        btnLoader.classList.remove("hidden");
    } else {
        btnText.classList.remove("hidden");
        btnLoader.classList.add("hidden");
    }
}

function showError(message) {
    const errorBox = document.getElementById("errorBox");
    errorBox.innerHTML = '<i class="fas fa-triangle-exclamation" style="margin-right: 8px;"></i>' + message;
    errorBox.classList.remove("hidden");
}

function hideError() {
    const errorBox = document.getElementById("errorBox");
    errorBox.classList.add("hidden");
    errorBox.textContent = "";
}

function renderWeather(weatherText) {
    const weatherCard = document.getElementById("weatherCard");
    const weatherBox = document.getElementById("weatherBox");

    if (!weatherCard || !weatherBox) return;

    if (weatherText && weatherText.trim()) {
        weatherBox.textContent = weatherText.trim();
        weatherCard.classList.remove("hidden");
    } else {
        weatherCard.classList.add("hidden");
        weatherBox.textContent = "";
    }
}

function renderTripMap(locations) {
    const mapCard = document.getElementById("mapCard");
    if (!mapCard) return;

    if (!locations || !Array.isArray(locations) || locations.length === 0 || typeof L === "undefined") {
        mapCard.classList.add("hidden");
        return;
    }

    mapCard.classList.remove("hidden");

    if (tripMap) {
        tripMap.remove();
        tripMap = null;
    }

    const dayColors = ["#38bdf8", "#a855f7", "#2dd4bf", "#f59e0b", "#f43f5e", "#22c55e", "#6366f1"];

    tripMap = L.map("tripMap").setView([locations[0].lat, locations[0].lon], 12);

    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
        attribution: "&copy; OpenStreetMap contributors"
    }).addTo(tripMap);

    const latLngs = [];

    locations.forEach((loc) => {
        const point = [loc.lat, loc.lon];
        latLngs.push(point);

        const dayNum = loc.day || 1;
        const color = dayColors[(dayNum - 1) % dayColors.length];

        const dayIcon = L.divIcon({
            className: "custom-day-pin",
            html: `<div style="background:${color}; color:#060d18; width:28px; height:28px; border-radius:50%; display:flex; align-items:center; justify-content:center; font-weight:800; font-size:11px; border:2px solid #ffffff; box-shadow:0 4px 10px rgba(0,0,0,0.45);">D${dayNum}</div>`,
            iconSize: [28, 28],
            iconAnchor: [14, 14]
        });

        L.marker(point, { icon: dayIcon })
            .addTo(tripMap)
            .bindPopup(`<strong>Day ${dayNum}</strong><br>${loc.place}`);
    });

    if (latLngs.length > 1) {
        const polyline = L.polyline(latLngs, {
            color: "#38bdf8",
            weight: 3,
            dashArray: "6, 6",
            opacity: 0.85
        }).addTo(tripMap);

        tripMap.fitBounds(polyline.getBounds(), { padding: [40, 40] });
    } else {
        tripMap.setView(latLngs[0], 13);
    }

    // Recalculate Leaflet container dimensions after un-hiding #resultSection
    setTimeout(() => {
        if (tripMap) tripMap.invalidateSize();
    }, 180);
}

function showResult(data) {
    latestAnswerMarkdown = data.answer;

    const resultSection = document.getElementById("resultSection");
    const resultBox = document.getElementById("resultBox");
    const threadInfo = document.getElementById("threadInfo");

    if (typeof marked !== "undefined") {
        resultBox.innerHTML = marked.parse(data.answer);
    } else {
        resultBox.innerText = data.answer;
    }

    threadInfo.textContent = `Thread ID: ${data.thread_id}`;
    resultSection.classList.remove("hidden");

    renderWeather(data.weather_results);
    renderTripMap(data.map_locations);

    setTimeout(() => {
        resultSection.scrollIntoView({ behavior: "smooth", block: "start" });
    }, 80);
}

async function sendMessage() {
    hideError();

    const input = document.getElementById("userInput");
    const message = input.value.trim();

    if (!message) {
        showError("Please enter your travel request first.");
        return;
    }

    setLoading(true);

    try {
        const response = await fetch("/api/travel", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                message: message,
                thread_id: currentThreadId
            })
        });

        const data = await response.json();

        if (!response.ok || !data.success) {
            throw new Error(data.error || "Something went wrong.");
        }

        currentThreadId = data.thread_id;
        localStorage.setItem("travel_thread_id", currentThreadId);

        showResult(data);

    } catch (error) {
        showError(error.message);
    } finally {
        setLoading(false);
    }
}

function copyResult() {
    const resultBox = document.getElementById("resultBox");
    const text = resultBox.innerText;

    if (!text) return;

    navigator.clipboard.writeText(text)
        .then(() => {
            const copyBtn = document.querySelector(".copy-btn");
            const oldText = copyBtn.innerHTML;
            copyBtn.innerHTML = '<i class="fas fa-check"></i> Copied!';
            setTimeout(() => { copyBtn.innerHTML = oldText; }, 1500);
        })
        .catch(() => showError("Could not copy result."));
}

function downloadPDF() {
    const pdfContent = document.getElementById("pdfContent");

    if (!latestAnswerMarkdown || !pdfContent) {
        showError("No travel plan available to download.");
        return;
    }

    const downloadBtn = document.querySelector(".download-btn");
    const oldText = downloadBtn.innerHTML;

    downloadBtn.innerHTML = '<span class="loader" style="width:14px;height:14px;border-width:2px;"></span> Preparing...';
    downloadBtn.disabled = true;

    const options = {
        margin: 0.5,
        filename: "tabigo-ai-travel-plan.pdf",
        image: { type: "jpeg", quality: 0.98 },
        html2canvas: { scale: 2, useCORS: true, backgroundColor: "#ffffff" },
        jsPDF: { unit: "in", format: "a4", orientation: "portrait" },
        pagebreak: { mode: ["avoid-all", "css", "legacy"] }
    };

    html2pdf()
        .set(options)
        .from(pdfContent)
        .save()
        .then(() => {
            downloadBtn.innerHTML = oldText;
            downloadBtn.disabled = false;
        })
        .catch(() => {
            downloadBtn.innerHTML = oldText;
            downloadBtn.disabled = false;
            showError("Could not download PDF.");
        });
}

// Ctrl/Cmd + Enter to send
document.addEventListener("keydown", function (event) {
    if ((event.ctrlKey || event.metaKey) && event.key === "Enter") {
        sendMessage();
    }
});