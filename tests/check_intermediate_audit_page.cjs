const assert = require("node:assert/strict");
const fs = require("node:fs/promises");
const path = require("node:path");
const { pathToFileURL } = require("node:url");
const { chromium } = require("playwright");

async function main() {
  const bundle = path.resolve(process.argv[2]);
  const output = path.resolve(process.argv[3]);
  await fs.mkdir(output, { recursive: true });
  const browser = await chromium.launch({
    executablePath: process.env.AUDIT_CHROME_PATH || "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    headless: true,
  });
  try {
    const context = await browser.newContext({ viewport: { width: 1280, height: 900 }, acceptDownloads: true });
    const page = await context.newPage();
    const errors = [];
    page.on("pageerror", e => errors.push(e.message));
    const url = pathToFileURL(path.join(bundle, "human/reader_a/index.html")).href;
    await page.goto(url);
    assert.equal(await page.locator("#criticism").isVisible(), false);
    await page.locator("#record").click();
    assert.match(await page.locator("#error").textContent(), /記入/);
    await page.locator("#paraphrase").fill("Synthetic browser test. Not a human observation.");
    await page.locator("#answer").selectOption("underdetermined");
    await page.locator("#confidence").selectOption("2");
    await page.locator("#prior_exposure").selectOption("unsure");
    await page.locator("#record").click();
    assert.equal(await page.locator("#paraphrase").isDisabled(), true);
    assert.equal(await page.locator("#criticism").isVisible(), true);
    await page.locator("#beauty").selectOption("3");
    await page.locator("#critique").fill("Synthetic preference for export verification only.");
    await page.reload();
    assert.equal(await page.locator("#beauty").inputValue(), "3");
    await page.locator("#edit").click();
    await page.locator("#record").click();
    const pendingDownload = page.waitForEvent("download");
    await page.locator("#download").click();
    const download = await pendingDownload;
    const responsePath = path.join(output, "synthetic_responses.json");
    await download.saveAs(responsePath);
    const response = JSON.parse(await fs.readFile(responsePath, "utf8"));
    assert.equal(response.responses.length, 1);
    assert.equal(response.responses[0].reading_edited_after_critique, true);
    assert.equal(response.responses[0].ratings.beauty, 3);
    assert.equal(response.responses[0].ratings.imagery, null);
    await page.locator("#next").click();
    assert.equal(await page.locator("#paraphrase").inputValue(), "");
    assert.equal(await page.locator("#criticism").isVisible(), false);
    await page.screenshot({ path: path.join(output, "desktop.png") });
    const mobile = await browser.newContext({ viewport: { width: 375, height: 812 } });
    const mp = await mobile.newPage();
    mp.on("pageerror", e => errors.push(e.message));
    await mp.goto(url);
    await mp.locator("#restore").setInputFiles(responsePath);
    assert.equal(await mp.locator("#beauty").inputValue(), "3");
    for (let i = 0; i < 12; i++) {
      assert.equal(await mp.evaluate(() => document.documentElement.scrollWidth <= innerWidth), true);
      assert.ok((await mp.locator("#text").textContent()).length > 10);
      if (i !== 11) await mp.locator("#next").click();
    }
    assert.equal(await mp.locator("#next").isDisabled(), true);
    await mp.screenshot({ path: path.join(output, "mobile.png") });
    await mp.goto(pathToFileURL(path.join(bundle, "human/reader_b/index.html")).href);
    await mp.locator("#restore").setInputFiles(responsePath);
    await mp.waitForFunction(() => document.getElementById("error").textContent.includes("確認"));
    assert.equal(await mp.locator("#paraphrase").inputValue(), "");
    assert.deepEqual(errors, []);
    console.log(JSON.stringify({ desktop: "passed", mobile: "passed", export_restore: "passed", wrong_packet_rejected: true, page_errors: errors, synthetic_responses_only: true }));
    await mobile.close();
    await context.close();
  } finally {
    await browser.close();
  }
}
main().catch(error => { console.error(error); process.exitCode = 1; });
