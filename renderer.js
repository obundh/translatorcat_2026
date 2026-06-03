const petShell = document.querySelector("#petShell");
const bubbleText = document.querySelector("#bubbleText");
const settingsButton = document.querySelector("#settingsButton");
const settingsPanel = document.querySelector("#settingsPanel");
const scaleRange = document.querySelector("#scaleRange");
const scaleValue = document.querySelector("#scaleValue");
const minimizeButton = document.querySelector("#minimizeButton");
const quitButton = document.querySelector("#quitButton");

const motion = {
  x: 8,
  y: 12,
  targetX: 8,
  targetY: 12,
  face: 1,
  mode: "idle",
  nextDecisionAt: 0
};

function clamp(value, min, max) {
  return Math.min(Math.max(value, min), max);
}

function pickMode() {
  const roll = Math.random();

  if (roll > 0.86) {
    return "nap";
  }

  if (roll > 0.68) {
    return "stretch";
  }

  if (roll > 0.32) {
    return "walk";
  }

  return "idle";
}

function chooseNextMove(now) {
  motion.mode = pickMode();

  const maxX = 20;
  const maxY = 14;
  const nextX = motion.x + (Math.random() * maxX - maxX / 2);
  const nextY = motion.y + (Math.random() * maxY - maxY / 2);

  motion.targetX = clamp(nextX, -8, 22);
  motion.targetY = clamp(nextY, -3, 20);
  motion.face = motion.targetX >= motion.x ? 1 : -1;
  motion.nextDecisionAt = now + 1700 + Math.random() * 2800;
}

function moveToward(current, target, amount) {
  if (Math.abs(current - target) <= amount) {
    return target;
  }

  return current + Math.sign(target - current) * amount;
}

function updatePet(now) {
  if (now > motion.nextDecisionAt) {
    chooseNextMove(now);
  }

  const walking = motion.mode === "walk";
  const step = walking ? 0.14 : 0.04;

  motion.x = moveToward(motion.x, motion.targetX, step);
  motion.y = moveToward(motion.y, motion.targetY, step * 0.55);

  petShell.classList.toggle("is-walking", walking);
  petShell.classList.toggle("is-napping", motion.mode === "nap");
  petShell.classList.toggle("is-stretching", motion.mode === "stretch");
  petShell.style.setProperty("--pet-x", `${motion.x.toFixed(2)}px`);
  petShell.style.setProperty("--pet-y", `${motion.y.toFixed(2)}px`);
  petShell.style.setProperty("--pet-face", motion.face);

  requestAnimationFrame(updatePet);
}

function showClipboardText(payload) {
  const text = payload?.text || "";
  bubbleText.textContent = text.length > 0 ? text : "...";
  petShell.classList.toggle("has-text", text.length > 0);
  petShell.dataset.status = payload?.status || "idle";
}

window.translatorCat?.onClipboardText(showClipboardText);

function scaleToPercent(scale) {
  const value = clamp(Number(scale) || 1, 0.7, 1.35);
  return {
    value,
    label: `${Math.round(value * 100)}%`
  };
}

function updateScaleControl(scale) {
  const next = scaleToPercent(scale);
  scaleRange.value = String(next.value);
  scaleValue.textContent = next.label;
  return next.value;
}

function applyScale(scale) {
  const value = updateScaleControl(scale);
  document.documentElement.style.setProperty("--ui-scale", value);
}

async function loadSettings() {
  const currentSettings = await window.translatorCat?.getSettings();
  applyScale(currentSettings?.scale || 1);
}

settingsButton.addEventListener("click", () => {
  settingsPanel.hidden = !settingsPanel.hidden;
});

scaleRange.addEventListener("input", () => {
  updateScaleControl(scaleRange.value);
});

scaleRange.addEventListener("change", () => {
  applyScale(scaleRange.value);
  window.translatorCat?.setScale(Number(scaleRange.value));
});

minimizeButton.addEventListener("click", () => {
  window.translatorCat?.minimize();
});

quitButton.addEventListener("click", () => {
  window.translatorCat?.quit();
});

chooseNextMove(performance.now());
requestAnimationFrame(updatePet);
loadSettings();
