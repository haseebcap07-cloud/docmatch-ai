const API_BASE_URL = "http://localhost:8000/api/v1";

async function extractJobDescription(jobDescription) {
  const response = await fetch(`${API_BASE_URL}/documents/extract-jd`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ job_description: jobDescription }),
  });

  if (!response.ok) {
    throw new Error("Failed to extract job description.");
  }

  return response.json();
}

async function tailorDocument(jobDescription, documentText, targetRole = null) {
  const response = await fetch(`${API_BASE_URL}/documents/tailor`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      job_description: jobDescription,
      document_text: documentText,
      target_role: targetRole,
    }),
  });

  if (!response.ok) {
    throw new Error("Failed to tailor document.");
  }

  return response.json();
}

async function rephraseText(text, tone = "professional") {
  const response = await fetch(`${API_BASE_URL}/documents/rephrase`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ text, tone }),
  });

  if (!response.ok) {
    throw new Error("Failed to rephrase text.");
  }

  return response.json();
}

async function formatDocument(documentText, formatStyle = "resume") {
  const response = await fetch(`${API_BASE_URL}/documents/format`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      document_text: documentText,
      format_style: formatStyle,
    }),
  });

  if (!response.ok) {
    throw new Error("Failed to format document.");
  }

  return response.json();
}

async function submitLead(name, email, company = "", message = "") {
  const response = await fetch(`${API_BASE_URL}/leads`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ name, email, company, message }),
  });

  if (!response.ok) {
    throw new Error("Failed to submit lead.");
  }

  return response.json();
}
