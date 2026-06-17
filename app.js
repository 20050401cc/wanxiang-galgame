const SAVE_KEY = "wanxiang-galgame-save-v2";
const BUILD_ID = "20260610-sharefix";

const app = document.querySelector("#app");
const background = document.querySelector("#background");
const titleScreen = document.querySelector("#titleScreen");
const titleMeta = document.querySelector("#titleMeta");
const chapterLabel = document.querySelector("#chapterLabel");
const progressLabel = document.querySelector("#progressLabel");
const speaker = document.querySelector("#speaker");
const kindLabel = document.querySelector("#kindLabel");
const storyText = document.querySelector("#storyText");
const charLu = document.querySelector("#charLu");
const charLin = document.querySelector("#charLin");
const charQin = document.querySelector("#charQin");
const charYun = document.querySelector("#charYun");
const charXiaozhu = document.querySelector("#charXiaozhu");
const charShen = document.querySelector("#charShen");
const charLuChuan = document.querySelector("#charLuChuan");
const charLuChengyuan = document.querySelector("#charLuChengyuan");
const chapterPanel = document.querySelector("#chapterPanel");
const logPanel = document.querySelector("#logPanel");
const chapterList = document.querySelector("#chapterList");
const textLog = document.querySelector("#textLog");
const sourceInfo = document.querySelector("#sourceInfo");

const state = {
  data: null,
  chapterIndex: 0,
  beatIndex: 0,
  titleVisible: true,
  auto: false,
  autoTimer: null,
  currentBackground: "",
  chapter: null,
  chapterCache: new Map(),
  loadingChapter: false,
};

const fallbackBackgrounds = {
  system_void: "key_art",
};

const characterElements = {
  lu_chenyuan: charLu,
  lin_qingxue: charLin,
  qin_wuque: charQin,
  yunheng_zhenren: charYun,
  xiaozhu: charXiaozhu,
  shen_qingluan: charShen,
  lu_chuan: charLuChuan,
  lu_chengyuan: charLuChengyuan,
};

function q(id) {
  return document.querySelector(id);
}

function chapterSummary(index = state.chapterIndex) {
  return state.data.chapters[index];
}

function currentChapter() {
  return state.chapter;
}

function currentBeat() {
  return currentChapter()?.beats[state.beatIndex];
}

function assetPath(kind, key) {
  if (kind === "backgrounds") {
    const mapped = state.data.assets.backgrounds[key] || state.data.assets.backgrounds[fallbackBackgrounds[key]];
    return mapped || state.data.assets.backgrounds.key_art;
  }
  return state.data.assets.characters[key];
}

function setBackground(key) {
  const bgKey = key === "system_void" ? "key_art" : key;
  const src = assetPath("backgrounds", bgKey);
  if (!src || state.currentBackground === src) {
    if (background.complete && background.naturalWidth > 0) background.classList.add("is-ready");
    return;
  }
  state.currentBackground = src;
  background.classList.remove("is-ready");
  background.onload = () => background.classList.add("is-ready");
  background.src = src;
}

function setCharacters(beat) {
  const names = new Set(beat.characters || []);
  if (beat.speaker === "陆沉渊") names.add("lu_chenyuan");
  if (beat.speaker === "林清雪") names.add("lin_qingxue");
  if (beat.speaker === "秦无缺") names.add("qin_wuque");
  if (beat.speaker === "云衡真人") names.add("yunheng_zhenren");
  if (beat.speaker === "小竹") names.add("xiaozhu");
  if (beat.speaker === "沈清鸾") names.add("shen_qingluan");
  if (beat.speaker === "陆川") names.add("lu_chuan");
  if (beat.speaker === "陆承远") names.add("lu_chengyuan");

  for (const [key, element] of Object.entries(characterElements)) {
    const visible = names.has(key);
    if (visible && !element.src) {
      const src = assetPath("characters", key);
      if (src) element.src = src;
    }
    element.classList.toggle("is-visible", visible);
  }
}

function kindName(kind) {
  if (kind === "dialogue") return "对白";
  if (kind === "system") return "系统";
  return "原文";
}

function setControlsDisabled(disabled) {
  for (const selector of ["#startBtn", "#continueBtn", "#nextBtn", "#prevBtn", "#autoBtn", "#chapterBtn", "#logBtn", "#saveBtn"]) {
    const button = q(selector);
    if (button) button.disabled = disabled;
  }
}

async function loadChapter(index) {
  const safeIndex = Math.max(0, Math.min(index, state.data.chapters.length - 1));
  const summary = chapterSummary(safeIndex);
  if (state.chapterCache.has(summary.id)) {
    return state.chapterCache.get(summary.id);
  }

  state.loadingChapter = true;
  setControlsDisabled(true);
  progressLabel.textContent = `读取第 ${summary.index} 章中...`;
  storyText.textContent = "正在读取本章原文。";

  const response = await fetch(`${summary.path}?v=${BUILD_ID}`);
  if (!response.ok) throw new Error(`章节加载失败 ${summary.title}: HTTP ${response.status}`);
  const chapter = await response.json();
  if (chapter.id !== summary.id || chapter.beatCount !== summary.beatCount || !Array.isArray(chapter.beats)) {
    throw new Error(`章节数据校验失败：${summary.title}`);
  }
  state.chapterCache.set(summary.id, chapter);
  state.loadingChapter = false;
  setControlsDisabled(false);
  return chapter;
}

async function goToChapter(index, beatIndex = 0) {
  const chapter = await loadChapter(index);
  state.chapterIndex = Math.max(0, Math.min(index, state.data.chapters.length - 1));
  state.chapter = chapter;
  state.beatIndex = Math.max(0, Math.min(beatIndex, chapter.beats.length - 1));
  showTitle(false);
  renderBeat();
  preloadAround(state.chapterIndex);
}

function preloadAround(index) {
  for (const nextIndex of [index + 1, index - 1]) {
    if (nextIndex < 0 || nextIndex >= state.data.chapters.length) continue;
    const summary = chapterSummary(nextIndex);
    if (state.chapterCache.has(summary.id)) continue;
    fetch(`${summary.path}?v=${BUILD_ID}`)
      .then((response) => (response.ok ? response.json() : null))
      .then((chapter) => {
        if (chapter?.id === summary.id) state.chapterCache.set(summary.id, chapter);
      })
      .catch(() => {});
  }
}

function renderBeat() {
  const chapter = currentChapter();
  const beat = currentBeat();
  if (!chapter || !beat) return;

  setBackground(beat.background);
  setCharacters(beat);
  chapterLabel.textContent = chapter.title;
  progressLabel.textContent = `${chapter.index}章 · ${state.beatIndex + 1} / ${chapter.beatCount}`;
  speaker.textContent = beat.speaker || "旁白";
  kindLabel.textContent = kindName(beat.kind);
  storyText.textContent = beat.text;
  storyText.scrollTop = 0;
  storyText.classList.toggle("system", beat.kind === "system");
  markActiveChapter();
  save(false);
  renderLog();
}

async function nextBeat() {
  if (state.loadingChapter || !state.chapter) return;
  const chapter = currentChapter();
  if (state.beatIndex < chapter.beats.length - 1) {
    state.beatIndex += 1;
    renderBeat();
  } else if (state.chapterIndex < state.data.chapters.length - 1) {
    await goToChapter(state.chapterIndex + 1, 0);
  }
}

async function prevBeat() {
  if (state.loadingChapter || !state.chapter) return;
  if (state.beatIndex > 0) {
    state.beatIndex -= 1;
    renderBeat();
  } else if (state.chapterIndex > 0) {
    const previousIndex = state.chapterIndex - 1;
    const previous = await loadChapter(previousIndex);
    await goToChapter(previousIndex, previous.beats.length - 1);
  }
}

function showTitle(show) {
  state.titleVisible = show;
  titleScreen.classList.toggle("is-hidden", !show);
}

function save(forceToast = true) {
  localStorage.setItem(
    SAVE_KEY,
    JSON.stringify({
      chapterIndex: state.chapterIndex,
      beatIndex: state.beatIndex,
      time: new Date().toISOString(),
    }),
  );
  if (forceToast && state.chapter) {
    progressLabel.textContent = `已保存 · ${state.chapter.index}章 · ${state.beatIndex + 1}`;
  }
}

function loadSave() {
  try {
    const raw = localStorage.getItem(SAVE_KEY) || localStorage.getItem("wanxiang-galgame-save-v1");
    if (!raw) return null;
    const parsed = JSON.parse(raw);
    if (!Number.isInteger(parsed.chapterIndex) || !Number.isInteger(parsed.beatIndex)) return null;
    return parsed;
  } catch {
    return null;
  }
}

async function continueFromSave() {
  const saved = loadSave();
  if (saved) {
    const index = Math.min(saved.chapterIndex, state.data.chapters.length - 1);
    await goToChapter(index, saved.beatIndex);
  } else {
    await goToChapter(0, 0);
  }
}

function renderChapterList() {
  chapterList.innerHTML = "";
  for (const chapter of state.data.chapters) {
    const item = document.createElement("button");
    item.type = "button";
    item.className = "chapter-item";
    item.dataset.index = String(chapter.index - 1);
    item.textContent = `${chapter.index}. ${chapter.title}`;
    item.addEventListener("click", async () => {
      chapterPanel.classList.remove("is-open");
      await goToChapter(chapter.index - 1, 0);
    });
    chapterList.appendChild(item);
  }
  markActiveChapter();
}

function markActiveChapter() {
  for (const item of chapterList.querySelectorAll(".chapter-item")) {
    item.classList.toggle("is-active", Number(item.dataset.index) === state.chapterIndex);
  }
}

function renderLog() {
  const chapter = currentChapter();
  if (!chapter) {
    textLog.innerHTML = "";
    return;
  }
  const start = Math.max(0, state.beatIndex - 10);
  const beats = chapter.beats.slice(start, state.beatIndex + 1);
  textLog.innerHTML = beats
    .map((beat) => {
      const who = beat.speaker || kindName(beat.kind);
      return `<p class="log-item"><strong>${escapeHtml(who)}</strong>${escapeHtml(beat.text)}</p>`;
    })
    .join("");
}

function renderSourceInfo() {
  const meta = state.data.meta;
  sourceInfo.innerHTML = [
    `原文：${escapeHtml(meta.sourceFile)}`,
    `SHA-256：${escapeHtml(meta.sourceSha256)}`,
    `章节：${meta.chapterCount} · 段落：${meta.beatCount} · 字符：${meta.sourceCharacters}`,
    `加载方式：轻量目录 + 单章懒加载`,
  ].join("<br />");
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function toggleAuto() {
  state.auto = !state.auto;
  q("#autoBtn").classList.toggle("is-active", state.auto);
  q("#autoBtn").textContent = state.auto ? "暂停" : "自动";
  if (state.auto) {
    state.autoTimer = window.setInterval(() => {
      void nextBeat();
    }, 3200);
  } else {
    window.clearInterval(state.autoTimer);
  }
}

function wireControls() {
  q("#startBtn").addEventListener("click", () => {
    void goToChapter(0, 0);
  });
  q("#continueBtn").addEventListener("click", () => {
    void continueFromSave();
  });
  q("#nextBtn").addEventListener("click", () => {
    void nextBeat();
  });
  q("#prevBtn").addEventListener("click", () => {
    void prevBeat();
  });
  q("#autoBtn").addEventListener("click", toggleAuto);
  q("#saveBtn").addEventListener("click", () => save(true));
  q("#chapterBtn").addEventListener("click", () => chapterPanel.classList.add("is-open"));
  q("#logBtn").addEventListener("click", () => logPanel.classList.add("is-open"));
  q("#closeChapterBtn").addEventListener("click", () => chapterPanel.classList.remove("is-open"));
  q("#closeLogBtn").addEventListener("click", () => logPanel.classList.remove("is-open"));
  q("#fullBtn").addEventListener("click", () => {
    if (document.fullscreenElement) {
      document.exitFullscreen();
    } else {
      document.documentElement.requestFullscreen();
    }
  });

  window.addEventListener("keydown", (event) => {
    if (state.titleVisible && event.key !== "Enter") return;
    if (event.key === "ArrowRight" || event.key === " ") {
      event.preventDefault();
      void nextBeat();
    }
    if (event.key === "ArrowLeft") {
      event.preventDefault();
      void prevBeat();
    }
    if (event.key.toLowerCase() === "l") {
      logPanel.classList.toggle("is-open");
    }
    if (event.key.toLowerCase() === "c") {
      chapterPanel.classList.toggle("is-open");
    }
  });
}

async function boot() {
  try {
    const response = await fetch(`data/manifest.json?v=${BUILD_ID}`);
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    state.data = await response.json();
    titleMeta.textContent = `${state.data.meta.chapterCount} 章 · ${state.data.meta.beatCount} 段原文 · 分章加载 · 音频未接入`;
    setBackground("key_art");
    renderChapterList();
    renderSourceInfo();
    wireControls();
    app.classList.remove("is-loading");
    const saved = loadSave();
    if (saved) {
      q("#continueBtn").disabled = false;
      q("#continueBtn").textContent = `继续 ${saved.chapterIndex + 1}章`;
    } else {
      q("#continueBtn").disabled = true;
    }
  } catch (error) {
    app.classList.remove("is-loading");
    storyText.textContent = `脚本读取失败：${error.message}。请用 run.bat 或本地服务器打开，不要直接双击 index.html。`;
  }
}

boot();
