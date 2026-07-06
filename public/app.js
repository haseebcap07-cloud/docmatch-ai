const form = document.getElementById("tailorForm");
const fileInput = document.getElementById("resumeFile");
const fileName = document.getElementById("fileName");
const dropZone = document.getElementById("dropZone");
const statusBox = document.getElementById("statusBox");
const generateBtn = document.getElementById("generateBtn");
const results = document.getElementById("results");

const scoreBefore = document.getElementById("scoreBefore");
const scoreAfter = document.getElementById("scoreAfter");
const resultTitle = document.getElementById("resultTitle");
const scoreReason = document.getElementById("scoreReason");
const downloadLink = document.getElementById("downloadLink");
const layoutProfile = document.getElementById("layoutProfile");
const layoutNotes = document.getElementById("layoutNotes");
const matchedMustHaves = document.getElementById("matchedMustHaves");
const missingKeywords = document.getElementById("missingKeywords");
const shortlistWords = document.getElementById("shortlistWords");
const actionPlan = document.getElementById("actionPlan");
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
  showStatus("V4 is reading resume layout, analyzing JD fit, and preserving DOCX formatting when possible...", false);
  generateBtn.disabled = true;
  generateBtn.textContent = "Generating...";

  try {
    const response = await fetch("/api/v1/resumes/tailor-file", {
      method: "POST",
      body: formData,
    });

    const raw = await response.text();
    let data;

    try {
      data = JSON.parse(raw);
    } catch {
      throw new Error(raw || "Server returned a non-JSON response. Check Render logs.");
    }

    if (!response.ok) {
      throw new Error(data.detail || data.error || "Generation failed.");
    }

    renderResults(data);
    statusBox.classList.add("hidden");
    results.classList.remove("hidden");
    results.scrollIntoView({ behavior: "smooth", block: "start" });
  } catch (error) {
    showStatus(error.message, true);
  } finally {
    generateBtn.disabled = false;
    generateBtn.textContent = "Generate V4 Tailored Resume";
  }
});

function renderResults(data) {
  scoreBefore.textContent = data.ats_score_before || 0;
  scoreAfter.textContent = data.ats_score_after || 0;
  resultTitle.textContent = `${data.job_title_guess || "Target Role"} — ${data.score_gap_to_90 === 0 ? "90+ Target Met" : "Needs " + data.score_gap_to_90 + " points"}`;
  scoreReason.textContent = data.score_reason || "";
  downloadLink.href = data.download_url || "#";
  downloadLink.download = data.filename || "tailored_resume_v4.docx";

  renderProfile(data.resume_profile || {});
  renderList(layoutNotes, (data.resume_profile && data.resume_profile.layout_notes) || []);
  renderTags(matchedMustHaves, data.matched_must_haves || data.matched_keywords || []);
  renderList(missingKeywords, data.missing_keywords || []);
  renderTags(shortlistWords, data.role_shortlist_words || []);
  renderList(actionPlan, data.truthful_90_plus_actions || []);
  preview.textContent = data.preview_text || "";
}

function renderProfile(profile) {
  layoutProfile.innerHTML = "";
  const items = [
    ["Source", profile.source_type || "unknown"],
    ["Mode", profile.preserve_mode || "unknown"],
    ["Pages", profile.estimated_page_count || 1],
    ["Paragraphs", profile.paragraph_count || 0],
    ["Words", profile.word_count || 0],
    ["Sections", (profile.detected_sections || []).join(", ") || "Not detected"],
    ["Fonts", (profile.detected_fonts || []).join(", ") || "Inherited/unknown"],
    ["Font sizes", (profile.detected_font_sizes || []).join(", ") || "Inherited/unknown"],
  ];

  items.forEach(([label, value]) => {
    const div = document.createElement("div");
    div.innerHTML = `<small>${escapeHtml(label)}</small><strong>${escapeHtml(String(value))}</strong>`;
    layoutProfile.appendChild(div);
  });
}

function renderTags(container, items) {
  container.innerHTML = "";
  if (!items.length) {
    const span = document.createElement("span");
    span.textContent = "No strong matches detected";
    container.appendChild(span);
    return;
  }

  items.slice(0, 35).forEach((item) => {
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

function escapeHtml(value) {
  return value.replace(/[&<>"']/g, (char) => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#039;"
  }[char]));
}
