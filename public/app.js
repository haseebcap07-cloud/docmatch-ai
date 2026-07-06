const form = document.getElementById("tailorForm");
const fileInput = document.getElementById("documentFile");
const fileName = document.getElementById("fileName");
const statusBox = document.getElementById("statusBox");
const resultBox = document.getElementById("resultBox");
const downloadLink = document.getElementById("downloadLink");
const generateBtn = document.getElementById("generateBtn");
const dropZone = document.getElementById("dropZone");

fileInput.addEventListener("change", () => {
  fileName.textContent = fileInput.files?.[0]?.name || "No file selected";
});

["dragenter", "dragover"].forEach((eventName) => {
  dropZone.addEventListener(eventName, (event) => {
    event.preventDefault();
    dropZone.classList.add("dragover");
  });
});

["dragleave", "drop"].forEach((eventName) => {
  dropZone.addEventListener(eventName, (event) => {
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

  const jobDescription = document.getElementById("jobDescription").value.trim();
  const targetRole = document.getElementById("targetRole").value.trim();
  const file = fileInput.files[0];

  if (!jobDescription || jobDescription.length < 20) {
    showStatus("Please paste the full job description.", true);
    return;
  }

  if (!file) {
    showStatus("Please upload a DOCX, TXT, or MD file.", true);
    return;
  }

  const formData = new FormData();
  formData.append("job_description", jobDescription);
  formData.append("target_role", targetRole);
  formData.append("file", file);

  resultBox.classList.add("hidden");
  showStatus("Generating your tailored document. Please wait...", false);
  generateBtn.disabled = true;
  generateBtn.textContent = "Generating...";

  try {
    const response = await fetch("/api/v1/documents/tailor-file", {
      method: "POST",
      body: formData,
    });

    if (!response.ok) {
      let message = "Failed to generate document.";
      try {
        const errorData = await response.json();
        message = errorData.detail || message;
      } catch (_) {}
      throw new Error(message);
    }

    const blob = await response.blob();
    const url = URL.createObjectURL(blob);
    const outputName = getOutputFilename(response) || "tailored_document.docx";

    downloadLink.href = url;
    downloadLink.download = outputName;

    statusBox.classList.add("hidden");
    resultBox.classList.remove("hidden");
  } catch (error) {
    showStatus(error.message, true);
  } finally {
    generateBtn.disabled = false;
    generateBtn.textContent = "Generate tailored document";
  }
});

function showStatus(message, isError) {
  statusBox.textContent = message;
  statusBox.classList.remove("hidden");
  statusBox.style.background = isError ? "#ffecec" : "#fff8e6";
  statusBox.style.borderColor = isError ? "#ffb3b3" : "#ffe1a2";
}

function getOutputFilename(response) {
  const disposition = response.headers.get("content-disposition");
  if (!disposition) return null;

  const match = disposition.match(/filename="?([^"]+)"?/);
  return match ? match[1] : null;
}
