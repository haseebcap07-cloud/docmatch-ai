const form = document.getElementById("tailorForm");
const fileInput = document.getElementById("resumeFile");
const fileName = document.getElementById("fileName");
const dropZone = document.getElementById("dropZone");
const statusBox = document.getElementById("statusBox");
const generateBtn = document.getElementById("generateBtn");
const results = document.getElementById("results");

const score = document.getElementById("score");
const resultTitle = document.getElementById("resultTitle");
const scoreReason = document.getElementById("scoreReason");
const downloadLink = document.getElementById("downloadLink");
const matchedMustHaves = document.getElementById("matchedMustHaves");
const missingKeywords = document.getElementById("missingKeywords");
const actionPlan = document.getElementById("actionPlan");
const warnings = document.getElementById("warnings");
const preview = document.getElementById("preview");

fileInput.addEventListener("change", () => {
  fileName.textContent = fileInput.files?.[0]?.name || "No file selected";
});

["dragenter", "dragover"].forEach((name) => {
  dropZone.addEventListener(name, (event) => {
    event.preventDefault();
    dropZone.classList.add("dragover");
  });
});

["dragleave", "drop"].forEach((name) => {
  dropZone.addEventListener(name, (event) => {
    event.preventDefault();
    dropZone.classList.remove("dragover");
  });
});

dropZone.addEventListener("drop", (event) => {
  const files = event.dataTransfer.files;
  if (files.length) {
    fileInput.files = files;
    fileName.textContent = files[0].name;
  }
});

form.addEventListener("submit", async (event) => {
  event.preventDefault();

  const jd = document.getElementById("jobDescription").value.trim();
  const role = document.getElementById("targetRole").value.trim();
  const file = fileInput.files[0];

  if (jd.length < 40) {
    showStatus("Paste the full job description before generating.", true);
    return;
  }

  if (!file) {
    showStatus("Upload a resume/document first.", true);
    return;
  }

  const formData = new FormData();
  formData.append("job_description", jd);
  formData.append("target_role", role);
  formData.append("file", file);

  results.classList.add("hidden");
  showStatus("Analyzing resume against JD. AI mode can take 20–60 seconds...", false);
  generateBtn.disabled = true;
  generateBtn.textContent = "Generating...";

  try {
    const response = await fetch("/api/v1/resumes/tailor-file", {
      method: "POST",
      body: formData,
    });

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.detail || "Generation failed.");
    }

    renderResults(data);
    statusBox.classList.add("hidden");
    results.classList.remove("hidden");
    results.scrollIntoView({ behavior: "smooth", block: "start" });
  } catch (error) {
    showStatus(error.message, true);
  } finally {
    generateBtn.disabled = false;
    generateBtn.textContent = "Generate 90+ Target Resume";
  }
});

function renderResults(data) {
  score.textContent = data.ats_score || 0;
  resultTitle.textContent = `${data.job_title_guess || "Target Role"} — ${data.score_gap_to_90 === 0 ? "90+ Ready" : "Needs " + data.score_gap_to_90 + " points"}`;
  scoreReason.textContent = data.score_reason || "";
  downloadLink.href = data.download_url || "#";
  downloadLink.download = data.filename || "tailored_resume.docx";

  renderTags(matchedMustHaves, data.matched_must_haves || data.matched_keywords || []);
  renderList(missingKeywords, data.missing_keywords || []);
  renderList(actionPlan, data.truthful_90_plus_actions || []);
  renderList(warnings, data.recruiter_warnings || []);
  preview.textContent = data.preview_text || "";
}

function renderTags(container, items) {
  container.innerHTML = "";
  if (!items.length) {
    const span = document.createElement("span");
    span.textContent = "No strong matches detected";
    container.appendChild(span);
    return;
  }

  items.slice(0, 30).forEach((item) => {
    const span = document.createElement("span");
    span.textContent = item;
    container.appendChild(span);
  });
}

function renderList(container, items) {
  container.innerHTML = "";
  if (!items.length) {
    const li = document.createElement("li");
    li.textContent = "No major issue detected.";
    container.appendChild(li);
    return;
  }

  items.slice(0, 12).forEach((item) => {
    const li = document.createElement("li");
    li.textContent = item;
    container.appendChild(li);
  });
}

function showStatus(message, isError) {
  statusBox.textContent = message;
  statusBox.classList.remove("hidden");
  statusBox.style.background = isError ? "#ffecec" : "#fff8e6";
  statusBox.style.borderColor = isError ? "#ffb3b3" : "#ffe1a2";
}
