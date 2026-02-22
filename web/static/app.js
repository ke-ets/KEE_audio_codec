/* ===== State ===== */
let lastKeeBlob = null;   // Blob of the last encoded .kee
let lastKeeName = "";      // filename for download
let lastWavBlob = null;    // Blob of the last decoded WAV
let lastWavName = "";

/* ===== Panel switching ===== */
function showPanel(which) {
  document.getElementById("panel-encode").classList.toggle("hidden", which !== "encode");
  document.getElementById("panel-decode").classList.toggle("hidden", which !== "decode");
  document.getElementById("btn-mode-encode").classList.toggle("active", which === "encode");
  document.getElementById("btn-mode-decode").classList.toggle("active", which === "decode");
  updateDecReuseAvailability();
}

/* ===== Encode: file selection ===== */
function onEncFileSelected(input) {
  const file = input.files[0];
  const nameEl = document.getElementById("enc-file-name");
  const btn = document.getElementById("btn-encode");
  if (file) {
    nameEl.textContent = file.name + " (" + formatBytes(file.size) + ")";
    btn.disabled = false;
  } else {
    nameEl.textContent = "";
    btn.disabled = true;
  }
}

/* ===== Encode: run ===== */
async function runEncode() {
  const fileInput = document.getElementById("enc-file-input");
  const file = fileInput.files[0];
  if (!file) return;

  const dFactor = document.getElementById("enc-d-factor").value.trim();

  const formData = new FormData();
  formData.append("file", file);
  if (dFactor) formData.append("downsample_factor", dFactor);

  hideEl("enc-result");
  hideEl("enc-error");
  showEl("enc-progress");
  document.getElementById("btn-encode").disabled = true;

  try {
    const resp = await fetch("/encode", { method: "POST", body: formData });
    if (!resp.ok) {
      const err = await resp.json().catch(() => ({ error: "Server error" }));
      throw new Error(err.error || "Encoding failed");
    }

    lastKeeBlob = await resp.blob();
    const baseName = file.name.replace(/\.[^.]+$/, "");
    lastKeeName = baseName + ".kee";

    const origSize = parseInt(resp.headers.get("X-Codec-Original-Size") || "0", 10);
    const compSize = parseInt(resp.headers.get("X-Codec-Compressed-Size") || "0", 10);
    const ratio = compSize > 0 ? (origSize / compSize).toFixed(2) : "N/A";

    document.getElementById("enc-orig-size").textContent = formatBytes(origSize);
    document.getElementById("enc-comp-size").textContent = formatBytes(compSize);
    document.getElementById("enc-ratio").textContent = ratio + "x";
    document.getElementById("enc-fs-orig").textContent = (resp.headers.get("X-Codec-Fs-Original") || "—") + " Hz";
    document.getElementById("enc-fs-new").textContent  = (resp.headers.get("X-Codec-Fs-New") || "—") + " Hz";
    document.getElementById("enc-d").textContent        = resp.headers.get("X-Codec-D") || "—";
    document.getElementById("enc-channels").textContent = resp.headers.get("X-Codec-Channels") || "—";
    document.getElementById("enc-duration").textContent  = (resp.headers.get("X-Codec-Duration") || "—") + " s";

    showEl("enc-result");
  } catch (e) {
    document.getElementById("enc-error").textContent = e.message;
    showEl("enc-error");
  } finally {
    hideEl("enc-progress");
    document.getElementById("btn-encode").disabled = false;
  }
}

function downloadKee() {
  if (!lastKeeBlob) return;
  triggerDownload(lastKeeBlob, lastKeeName);
}

/* ===== Decode: file selection ===== */
function onDecFileSelected(input) {
  const file = input.files[0];
  const nameEl = document.getElementById("dec-file-name");
  if (file) {
    nameEl.textContent = file.name + " (" + formatBytes(file.size) + ")";
  } else {
    nameEl.textContent = "";
  }
  updateDecodeButton();
}

function onReuseToggle() {
  const checked = document.getElementById("dec-reuse-checkbox").checked;
  const infoEl = document.getElementById("dec-reuse-info");
  if (checked && lastKeeBlob) {
    infoEl.textContent = "Using: " + lastKeeName;
  } else {
    infoEl.textContent = "";
  }
  updateDecodeButton();
}

function updateDecReuseAvailability() {
  const row = document.getElementById("dec-reuse-row");
  const cb = document.getElementById("dec-reuse-checkbox");
  if (lastKeeBlob) {
    row.style.opacity = "1";
    cb.disabled = false;
  } else {
    row.style.opacity = "0.4";
    cb.disabled = true;
    cb.checked = false;
  }
  updateDecodeButton();
}

function updateDecodeButton() {
  const fileInput = document.getElementById("dec-file-input");
  const reuse = document.getElementById("dec-reuse-checkbox").checked && lastKeeBlob;
  const hasFile = fileInput.files && fileInput.files.length > 0;
  document.getElementById("btn-decode").disabled = !(hasFile || reuse);
}

/* ===== Decode: run ===== */
async function runDecode() {
  const reuse = document.getElementById("dec-reuse-checkbox").checked && lastKeeBlob;
  const fileInput = document.getElementById("dec-file-input");

  let blob, fileName;
  if (reuse) {
    blob = lastKeeBlob;
    fileName = lastKeeName;
  } else if (fileInput.files[0]) {
    blob = fileInput.files[0];
    fileName = fileInput.files[0].name;
  } else {
    return;
  }

  const formData = new FormData();
  formData.append("file", new File([blob], fileName));

  hideEl("dec-result");
  hideEl("dec-error");
  showEl("dec-progress");
  document.getElementById("btn-decode").disabled = true;

  try {
    const resp = await fetch("/decode", { method: "POST", body: formData });
    if (!resp.ok) {
      const err = await resp.json().catch(() => ({ error: "Server error" }));
      throw new Error(err.error || "Decoding failed");
    }

    lastWavBlob = await resp.blob();
    const baseName = fileName.replace(/\.[^.]+$/, "");
    lastWavName = baseName + "_restored.wav";

    document.getElementById("dec-fs-orig").textContent  = (resp.headers.get("X-Codec-Fs-Original") || "—") + " Hz";
    document.getElementById("dec-d").textContent         = resp.headers.get("X-Codec-D") || "—";
    document.getElementById("dec-duration").textContent   = (resp.headers.get("X-Codec-Duration") || "—") + " s";

    showEl("dec-result");
  } catch (e) {
    document.getElementById("dec-error").textContent = e.message;
    showEl("dec-error");
  } finally {
    hideEl("dec-progress");
    updateDecodeButton();
  }
}

function downloadWav() {
  if (!lastWavBlob) return;
  triggerDownload(lastWavBlob, lastWavName);
}

/* ===== Helpers ===== */
function showEl(id) { document.getElementById(id).classList.remove("hidden"); }
function hideEl(id) { document.getElementById(id).classList.add("hidden"); }

function formatBytes(bytes) {
  if (bytes === 0) return "0 B";
  const k = 1024;
  const sizes = ["B", "KB", "MB", "GB"];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + " " + sizes[i];
}

function triggerDownload(blob, name) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = name;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

/* ===== Init ===== */
document.addEventListener("DOMContentLoaded", () => {
  updateDecReuseAvailability();
});
