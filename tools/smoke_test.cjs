const fs = require("fs");
const path = require("path");
const { chromium } = require("playwright");

const ROOT = path.resolve(__dirname, "..");
const OUT_DIR = path.join(ROOT, "verification");
const URL = process.argv[2] || "http://127.0.0.1:8787/";
const EDGE_CANDIDATES = [
  "C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe",
  "C:\\Program Files\\Microsoft\\Edge\\Application\\msedge.exe",
];

function assert(condition, message) {
  if (!condition) {
    throw new Error(message);
  }
}

async function imageVariance(page, selector) {
  return page.locator(selector).evaluate((img) => {
    const el = img;
    const canvas = document.createElement("canvas");
    canvas.width = 32;
    canvas.height = 18;
    const ctx = canvas.getContext("2d");
    ctx.drawImage(el, 0, 0, canvas.width, canvas.height);
    const data = ctx.getImageData(0, 0, canvas.width, canvas.height).data;
    let min = 255;
    let max = 0;
    for (let i = 0; i < data.length; i += 4) {
      const v = Math.round((data[i] + data[i + 1] + data[i + 2]) / 3);
      min = Math.min(min, v);
      max = Math.max(max, v);
    }
    return { min, max, variance: max - min, naturalWidth: el.naturalWidth, naturalHeight: el.naturalHeight };
  });
}

async function waitTitleHidden(page) {
  await page.waitForFunction(() => document.querySelector("#titleScreen")?.classList.contains("is-hidden"));
}

async function runDesktop(browser) {
  const page = await browser.newPage({ viewport: { width: 1440, height: 900 }, deviceScaleFactor: 1 });
  const errors = [];
  page.on("console", (msg) => {
    if (msg.type() === "error") errors.push(msg.text());
  });
  page.on("pageerror", (err) => errors.push(err.message));

  await page.goto(URL, { waitUntil: "networkidle" });
  await page.waitForSelector("#titleMeta:text('430 章')");
  await page.waitForSelector("#background.is-ready");
  const titleText = await page.locator("#titleMeta").innerText();
  assert(titleText.includes("25330"), "title meta did not show full beat count");

  const titleVariance = await imageVariance(page, "#background");
  assert(titleVariance.naturalWidth >= 1600, "title background did not load at expected resolution");
  assert(titleVariance.variance > 20, "title background appears blank");

  await page.locator("#startBtn").click();
  await waitTitleHidden(page);
  await page.waitForSelector("#storyText:text('烈火从骨缝里钻出来。')");
  assert((await page.locator("#chapterLabel").innerText()).includes("第一章"), "first chapter label missing");

  for (let i = 0; i < 4; i += 1) {
    await page.locator("#nextBtn").click();
  }
  await page.waitForSelector("#charYun.is-visible");
  await page.locator("#nextBtn").click();
  await page.waitForSelector("#charQin.is-visible");
  for (let i = 0; i < 2; i += 1) {
    await page.locator("#nextBtn").click();
  }
  await page.waitForSelector("#storyText:text('死得其所？')");
  for (let i = 0; i < 4; i += 1) {
    await page.locator("#nextBtn").click();
  }
  await page.waitForSelector("#charLin.is-visible");
  await page.locator("#saveBtn").click();

  await page.locator("#chapterBtn").click();
  await page.waitForSelector("#chapterPanel.is-open");
  const chapterCount = await page.locator(".chapter-item").count();
  assert(chapterCount === 430, `expected 430 chapter buttons, got ${chapterCount}`);
  await page.locator(".chapter-item").nth(39).click();
  await page.waitForSelector("#chapterLabel:text('第四十章')");

  await page.locator("#logBtn").click();
  await page.waitForSelector("#logPanel.is-open");
  const sourceInfo = await page.locator("#sourceInfo").innerText();
  assert(sourceInfo.includes("SHA-256"), "source hash not shown in log panel");
  await page.locator("#closeLogBtn").click();

  await page.reload({ waitUntil: "networkidle" });
  await page.waitForSelector("#continueBtn:text('继续 40章')");
  await page.locator("#continueBtn").click();
  await page.waitForSelector("#chapterLabel:text('第四十章')");
  await waitTitleHidden(page);
  await page.waitForTimeout(320);
  await page.waitForSelector("#background.is-ready");

  const bgVariance = await imageVariance(page, "#background");
  assert(bgVariance.variance > 20, "in-game background appears blank");

  await page.screenshot({ path: path.join(OUT_DIR, "desktop.png"), fullPage: true });
  assert(errors.length === 0, `browser console/page errors: ${errors.join(" | ")}`);
  await page.close();
}

async function runMobile(browser) {
  const page = await browser.newPage({ viewport: { width: 390, height: 844 }, isMobile: true, deviceScaleFactor: 2 });
  await page.goto(URL, { waitUntil: "networkidle" });
  await page.waitForSelector("#titleMeta:text('430 章')");
  await page.locator("#startBtn").click();
  await waitTitleHidden(page);
  await page.waitForTimeout(320);
  await page.waitForSelector("#background.is-ready");
  await page.waitForSelector("#storyText");
  const box = await page.locator(".textbox").boundingBox();
  assert(box && box.width <= 390 && box.height > 180, "mobile textbox sizing is invalid");
  await page.screenshot({ path: path.join(OUT_DIR, "mobile.png"), fullPage: true });
  await page.close();
}

(async () => {
  fs.mkdirSync(OUT_DIR, { recursive: true });
  const edgePath = EDGE_CANDIDATES.find((candidate) => fs.existsSync(candidate));
  const launchOptions = edgePath ? { headless: true, executablePath: edgePath } : { headless: true };
  const browser = await chromium.launch(launchOptions);
  try {
    await runDesktop(browser);
    await runMobile(browser);
  } finally {
    await browser.close();
  }
  console.log(`OK: smoke test passed at ${URL}`);
  console.log(`screenshots=${path.join(OUT_DIR, "desktop.png")} | ${path.join(OUT_DIR, "mobile.png")}`);
})();
