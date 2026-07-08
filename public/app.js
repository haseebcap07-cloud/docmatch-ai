const $ = (id) => document.getElementById(id);

const STORAGE_PROFILE = "rtp_v5_master_profile";
const STORAGE_HISTORY = "rtp_v5_history";

const emptyProfile = () => ({
  contact: { full_name: "", email: "", phone: "", location: "", linkedin: "", github: "", portfolio: "" },
  target_titles: [],
  summary: "",
  technical_skills: [],
  professional_experience: [],
  projects: [],
  education: [],
  certifications: [],
  interests: [],
  languages: [],
  achievements: [],
  work_authorization: ""
});

document.addEventListener("DOMContentLoaded", () => {
  loadSavedProfileIntoUI();
  refreshDashboard();

  $("extractBtn").addEventListener("click", extractProfile);
  $("saveProfileBtn").addEventListener("click", saveProfile);
  $("generateBtn").addEventListener("click", generateResume);
});

function getTemplateSettings() {
  return {
    template_name: "ATS Modern",
    font_family: $("fontFamily").value.trim() || "Aptos",
    body_font_size: Number($("bodyFontSize").value || 10),
    heading_font_size: Number($("headingFontSize").value || 11),
    name_font_size: Number($("nameFontSize").value || 18),
    margin_inches: Number($("marginInches").value || 0.55),
    line_spacing: 1.0,
    page_limit: Number($("pageLimit").value || 2),
    show_projects: $("showProjects").checked,
    show_certifications: $("showCertifications").checked,
    show_interests: $("showInterests").checked,
    show_watermark: $("showWatermark").checked,
  };
}

function uiToProfile() {
  const profile = emptyProfile();

  profile.contact.full_name = $("fullName").value.trim();
  profile.contact.email = $("email").value.trim();
  profile.contact.phone = $("phone").value.trim();
  profile.contact.location = $("location").value.trim();
  profile.contact.linkedin = $("linkedin").value.trim();
  profile.contact.github = $("github").value.trim();
  profile.contact.portfolio = $("portfolio").value.trim();

  profile.target_titles = splitComma($("targetTitles").value);
  profile.summary = $("summary").value.trim();
  profile.technical_skills = splitSkills($("technicalSkills").value);

  const expBullets = splitLines($("expBullets").value);
  if ($("expTitle").value.trim() || $("expCompany").value.trim() || expBullets.length) {
    const dates = $("expDates").value.trim();
    const parts = dates.split(/\s+-\s+/);
    profile.professional_experience.push({
      title: $("expTitle").value.trim(),
      company: $("expCompany").value.trim(),
      location: "",
      start_date: parts[0] || "",
      end_date: parts[1] || "",
      bullets: expBullets,
    });
  }

  profile.projects = parseProjects($("projects").value);
  profile.education = splitLines($("education").value).map(line => ({ degree: line, school: "", location: "", graduation: "" }));
  profile.certifications = splitLines($("certifications").value);
  profile.interests = splitComma($("interests").value);

  return profile;
}

function profileToUI(profile) {
  if (!profile) return;

  $("fullName").value = profile.contact?.full_name || "";
  $("email").value = profile.contact?.email || "";
  $("phone").value = profile.contact?.phone || "";
  $("location").value = profile.contact?.location || "";
  $("linkedin").value = profile.contact?.linkedin || "";
  $("github").value = profile.contact?.github || "";
  $("portfolio").value = profile.contact?.portfolio || "";
  $("targetTitles").value = (profile.target_titles || []).join(", ");

  $("summary").value = profile.summary || "";
  $("technicalSkills").value = (profile.technical_skills || []).join(", ");

  const exp = (profile.professional_experience || [])[0] || {};
  $("expTitle").value = exp.title || "";
  $("expCompany").value = exp.company || "";
  $("expDates").value = [exp.start_date || "", exp.end_date || ""].filter(Boolean).join(" - ");
  $("expBullets").value = (exp.bullets || []).join("\n");

  $("projects").value = (profile.projects || []).map(p => {
    const bullets = (p.bullets || []).map(b => `- ${b}`).join("\n");
    return [p.name, p.description, bullets].filter(Boolean).join("\n");
  }).join("\n\n");

  $("education").value = (profile.education || []).map(e => [e.degree, e.school, e.location, e.graduation].filter(Boolean).join(" | ")).join("\n");
  $("certifications").value = (profile.certifications || []).join("\n");
  $("interests").value = (profile.interests || []).join(", ");
}

async function extractProfile() {
  const file = $("resumeFile").files[0];
  if (!file) {
    showStatus("extractStatus", "Upload a resume file first.", true);
    return;
  }

  const form = new FormData();
  form.append("file", file);

  showStatus("extractStatus", "Extracting profile sections from uploaded resume...", false);

  try {
    const response = await fetch("/api/v1/profiles/extract", { method: "POST", body: form });
    const data = await parseResponse(response);
    profileToUI(data.profile);
    localStorage.setItem("rtp_v5_last_resume_score", String(data.resume_only_score || 0));
    showStatus("extractStatus", `Profile extracted. Resume-only score: ${data.resume_only_score}/100. Review and click Save.`, false);
    refreshDashboard();
  } catch (error) {
    showStatus("extractStatus", error.message, true);
  }
}

function saveProfile() {
  const profile = uiToProfile();
  localStorage.setItem(STORAGE_PROFILE, JSON.stringify(profile));
  localStorage.setItem("rtp_v5_last_resume_score", estimateResumeOnly(profile));
  refreshDashboard();
  alert("Master profile saved to dashboard.");
}

async function generateResume() {
  const saved = localStorage.getItem(STORAGE_PROFILE);
  const profile = saved ? JSON.parse(saved) : uiToProfile();
  const jd = $("jobDescription").value.trim();

  if (jd.length < 40) {
    showStatus("generateStatus", "Paste the full job description first.", true);
    return;
  }

  if (!profile.summary && !profile.technical_skills.length && !profile.professional_experience.length) {
    showStatus("generateStatus", "Your profile is too empty. Build or extract a profile first.", true);
    return;
  }

  const payload = {
    profile,
    job_description: jd,
    target_role: $("targetRole").value.trim(),
    custom_instructions: $("customInstructions").value.trim(),
    user_requested_additions: parseUserRequestedAdditions(),
    user_requested_replacements: [],
    template_settings: getTemplateSettings(),
  };

  $("generateBtn").disabled = true;
  $("generateBtn").textContent = "Generating...";
  showStatus("generateStatus", "Generating ATS-targeted resume from your saved master profile...", false);

  try {
    const response = await fetch("/api/v1/resumes/generate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    const data = await parseResponse(response);
    renderResults(data);
    saveHistory(data, payload.target_role);
    refreshDashboard();
    $("results").classList.remove("hidden");
    $("generateStatus").classList.add("hidden");
    $("results").scrollIntoView({ behavior: "smooth" });
  } catch (error) {
    showStatus("generateStatus", error.message, true);
  } finally {
    $("generateBtn").disabled = false;
    $("generateBtn").textContent = "Generate ATS Resume";
  }
}

function renderResults(data) {
  const b = data.score_breakdown || {};
  $("scoreResume").textContent = b.resume_only_score || 0;
  $("scoreJD").textContent = b.jd_match_score || 0;
  $("scoreKeyword").textContent = b.keyword_score || 0;
  $("scoreFinal").textContent = b.final_ats_estimate || 0;
  $("scoreReason").textContent = data.score_reason || "";
  $("downloadLink").href = data.download_url || "#";
  $("downloadLink").download = data.filename || "resume_tailor_pro_v5.docx";
  renderTags("matchedKeywords", data.matched_keywords || []);
  renderList("missingKeywords", data.missing_keywords || []);
  renderList("actionPlan", data.truthful_90_plus_actions || []);
  renderList("warnings", data.recruiter_warnings || []);
  renderChangeLog(data.change_log || {});
  renderFinalResult(data.final_result || {});
  renderAdaptiveAnalysis(data.adaptive_analysis || {});
  $("previewText").textContent = data.preview_text || "";
}

function refreshDashboard() {
  const profile = localStorage.getItem(STORAGE_PROFILE);
  const history = getHistory();
  $("savedProfileStatus").textContent = profile ? "Yes" : "No";
  $("savedResumeScore").textContent = localStorage.getItem("rtp_v5_last_resume_score") || "0";
  $("lastAtsScore").textContent = history[0]?.score || "0";
  $("historyCount").textContent = history.length;

  const list = $("historyList");
  list.innerHTML = "";
  if (!history.length) {
    list.innerHTML = `<div class="history-item">No generated resumes yet.</div>`;
    return;
  }
  history.slice(0, 8).forEach(item => {
    const div = document.createElement("div");
    div.className = "history-item";
    div.innerHTML = `<strong>${escapeHtml(item.role || "Target Role")}</strong><br><span>Final ATS: ${item.score}/100 · ${escapeHtml(item.date)}</span>`;
    list.appendChild(div);
  });
}

function loadSavedProfileIntoUI() {
  const saved = localStorage.getItem(STORAGE_PROFILE);
  if (saved) profileToUI(JSON.parse(saved));
}

function saveHistory(data, role) {
  const history = getHistory();
  history.unshift({
    role: role || "Target Role",
    score: data.score_breakdown?.final_ats_estimate || 0,
    filename: data.filename,
    date: new Date().toLocaleString(),
  });
  localStorage.setItem(STORAGE_HISTORY, JSON.stringify(history.slice(0, 25)));
}

function getHistory() {
  try { return JSON.parse(localStorage.getItem(STORAGE_HISTORY) || "[]"); }
  catch { return []; }
}

async function parseResponse(response) {
  const raw = await response.text();
  let data;
  try { data = JSON.parse(raw); }
  catch { throw new Error(raw || "Server returned a non-JSON response. Check logs."); }
  if (!response.ok) throw new Error(data.detail || data.error || "Request failed.");
  return data;
}

function showStatus(id, message, error) {
  const box = $(id);
  box.textContent = message;
  box.classList.remove("hidden");
  box.style.background = error ? "#ffecec" : "#fff8e6";
  box.style.borderColor = error ? "#ffb3b3" : "#ffe1a2";
}

function splitLines(value) {
  return value.split(/\n+/).map(x => x.replace(/^[•\-*–—]\s*/, "").trim()).filter(Boolean);
}

function splitComma(value) {
  return value.split(/,|;/).map(x => x.trim()).filter(Boolean);
}

function splitSkills(value) {
  return value.split(/,|;|\n/).map(x => x.trim()).filter(Boolean);
}

function parseProjects(value) {
  const blocks = value.split(/\n\s*\n/).map(x => x.trim()).filter(Boolean);
  return blocks.map(block => {
    const lines = block.split(/\n/).map(x => x.trim()).filter(Boolean);
    return {
      name: lines[0] || "Project",
      description: lines.length > 1 && !lines[1].startsWith("-") ? lines[1] : "",
      technologies: [],
      bullets: lines.slice(1).filter(x => x.startsWith("-") || x.startsWith("•")).map(x => x.replace(/^[•\-*–—]\s*/, "")),
    };
  });
}

function renderTags(id, items) {
  const box = $(id);
  box.innerHTML = "";
  if (!items.length) {
    box.innerHTML = "<span>No matches detected</span>";
    return;
  }
  items.slice(0, 35).forEach(item => {
    const span = document.createElement("span");
    span.textContent = item;
    box.appendChild(span);
  });
}

function renderList(id, items) {
  const list = $(id);
  list.innerHTML = "";
  if (!items.length) {
    list.innerHTML = "<li>No major issue detected.</li>";
    return;
  }
  items.slice(0, 12).forEach(item => {
    const li = document.createElement("li");
    li.textContent = item;
    list.appendChild(li);
  });
}

function estimateResumeOnly(profile) {
  let score = 0;
  if (profile.contact.full_name) score += 10;
  if (profile.contact.email || profile.contact.phone) score += 10;
  if (profile.summary && profile.summary.split(/\s+/).length >= 25) score += 15;
  if (profile.technical_skills.length >= 10) score += 20;
  if (profile.professional_experience.length) score += 20;
  if ((profile.professional_experience[0]?.bullets || []).length >= 5) score += 15;
  if (profile.education.length) score += 10;
  return Math.min(100, Math.max(20, score));
}

function escapeHtml(value) {
  return String(value).replace(/[&<>"']/g, char => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#039;"
  }[char]));
}


function renderAdaptiveAnalysis(analysis) {
  const items = [];
  if (analysis.resume_role_family) items.push(`Resume role family: ${analysis.resume_role_family}`);
  if (analysis.jd_role_family) items.push(`JD role family: ${analysis.jd_role_family}`);
  if (analysis.role_alignment) items.push(`Role alignment: ${analysis.role_alignment}`);
  if (analysis.selected_playbook) items.push(`Selected playbook: ${analysis.selected_playbook}`);
  (analysis.rewrite_focus || []).slice(0, 5).forEach(x => items.push(`Rewrite focus: ${x}`));
  (analysis.unsupported_requirements || []).slice(0, 4).forEach(x => items.push(`Gap: ${x}`));
  (analysis.validator_warnings || []).slice(0, 4).forEach(x => items.push(`Validator: ${x}`));
  renderList("adaptiveAnalysis", items);
}


function parseUserRequestedAdditions() {
  const field = document.getElementById("userRequestedAdditions");
  if (!field) return [];
  return field.value.split(/\n+/).map(x => x.trim()).filter(Boolean);
}

function renderChangeLog(log) {
  const items = [];
  (log.semantic_mappings_applied || []).slice(0, 8).forEach(x => items.push(`Semantic mapping: ${x}`));
  (log.keyword_rephrasing || []).slice(0, 8).forEach(x => items.push(`Keyword rephrasing: ${x}`));
  (log.user_requested_additions_replacements || []).slice(0, 8).forEach(x => items.push(`User-requested: ${x}`));
  (log.unsupported_jd_skills_not_added || []).slice(0, 8).forEach(x => items.push(`Not added: ${x}`));
  (log.title_or_structure_adjustments || []).slice(0, 5).forEach(x => items.push(`Structure/title: ${x}`));
  renderList("changeLog", items);
}

function renderFinalResult(result) {
  const items = [];
  if (result.post_optimization_ats_score !== undefined) items.push(`Post-optimization ATS score: ${result.post_optimization_ats_score}/100`);
  if (result.score_improvement) items.push(`Score improvement: ${result.score_improvement}`);
  renderList("finalResult", items);
}
