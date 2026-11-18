/** Arena M1 acceptance checks against an already running local Streamlit app. */
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';

const modulePath = process.env.TDK_PLAYWRIGHT_MODULE;
const executablePath = process.env.TDK_BROWSER_EXECUTABLE;
if (!modulePath || !executablePath) throw new Error('Set TDK_PLAYWRIGHT_MODULE and TDK_BROWSER_EXECUTABLE.');
const { chromium } = await import(modulePath);
const browser = await chromium.launch({ headless: true, executablePath });
const temporary = await fs.mkdtemp(path.join(os.tmpdir(), 'arena-m1-check-'));
const baseURL = process.env.TDK_ARENA_URL || 'http://127.0.0.1:8501';
const images = process.env.TDK_ARENA_SCREENSHOT_DIR || temporary;
await fs.mkdir(images, { recursive: true });
const errors = [];

async function ready(page, id) {
  await page.locator('.hero').filter({ hasText: id }).waitFor();
  await page.getByRole('button', { name: 'Download this case and full trace', exact: true }).waitFor();
  assert.equal(await page.locator('[data-testid="stException"]').count(), 0);
}

async function family(page, label) {
  await page.getByRole('combobox', { name: 'Source scenario', exact: true }).click();
  await page.getByRole('option', { name: label, exact: true }).click();
}

try {
  const context = await browser.newContext({ viewport: { width: 1440, height: 1180 }, acceptDownloads: true });
  const page = await context.newPage();
  page.on('pageerror', error => errors.push(error.message));
  await page.goto(baseURL);
  await ready(page, 'E044-005');
  assert.deepEqual(await page.locator('.answer-card .name').allTextContents(),
    ['Standard RAG draft', 'Original NS', 'Candidate NS']);
  assert.deepEqual(await page.locator('.answer-card .answer').allTextContents(),
    ['Crimson Swans won.', 'I cannot determine the winner.', 'Crimson Swans won.']);

  await page.getByRole('button', { name: 'False source', exact: true }).click();
  await ready(page, 'E044-021');
  await page.locator('.notice.fail').filter({ hasText: 'Source-consistent, but wrong.' }).waitFor();
  assert.match(await page.locator('.answer-card.candidate').innerText(), /WRONG.*exact scorer/s);
  assert.match(await page.locator('.answer-card.candidate').innerText(), /VERIFIED/);
  await page.screenshot({ path: path.join(images, 'arena_m1_false_source.png') });

  await page.getByRole('button', { name: 'Source conflict', exact: true }).click();
  await ready(page, 'E044-013');
  assert.match(await page.locator('.trace-step').last().innerText(), /R5_CONFLICT/);
  assert.equal(await page.locator('.answer-card.candidate .answer').innerText(), 'I cannot determine the winner.');

  await page.getByRole('button', { name: 'Recovered answer', exact: true }).click();
  await ready(page, 'E044-005');
  await page.getByRole('switch', { name: 'Reveal fictional reference', exact: true }).focus();
  await page.getByRole('switch', { name: 'Reveal fictional reference', exact: true }).press('Space');
  await page.getByText('Reference hidden.', { exact: false }).waitFor();
  assert.equal(await page.locator('.answer-card .score').count(), 0);
  await page.getByRole('switch', { name: 'Reveal fictional reference', exact: true }).focus();
  await page.getByRole('switch', { name: 'Reveal fictional reference', exact: true }).press('Space');
  await page.locator('.reference .value').filter({ hasText: 'Crimson Swans' }).waitFor();

  for (const [label, id] of [
    ['Clean evidence', 'E044-001'], ['Same fact, different wording', 'E044-005'],
    ['Negated distractor', 'E044-009'], ['Conflicting sources', 'E044-013'],
    ['False source', 'E044-021'], ['Wrong-year evidence', 'E044-017'],
  ]) {
    await family(page, label);
    await ready(page, id);
    await page.getByText('4 of 24 recorded challenges', { exact: true }).waitFor();
    assert.equal(await page.locator('.answer-card').count(), 3);
  }
  assert.match(await page.locator('.answer-card').first().innerText(), /UNSCORABLE/);
  assert.match(await page.locator('.answer-card.candidate').innerText(), /UNKNOWN/);
  await page.getByRole('button', { name: 'Next', exact: true }).click();
  await ready(page, 'E044-018');
  await page.getByRole('button', { name: 'Previous', exact: true }).click();
  await ready(page, 'E044-017');

  const downloadPromise = page.waitForEvent('download');
  await page.getByRole('button', { name: 'Download this case and full trace', exact: true }).click();
  const download = await downloadPromise;
  const file = path.join(temporary, 'case.json');
  await download.saveAs(file);
  const exported = JSON.parse(await fs.readFile(file, 'utf8'));
  assert.equal(exported.case_id, 'E044-017');
  assert.equal(exported.new_model_calls, 0);
  assert.equal(exported.original_raw_record.scores.S1.category, 'UNSCORABLE');
  assert.ok(exported.original_raw_record.calls.V3.prompt);

  const mobile = await browser.newPage({ viewport: { width: 390, height: 844 } });
  mobile.on('pageerror', error => errors.push(error.message));
  await mobile.goto(baseURL);
  await ready(mobile, 'E044-005');
  assert.equal(await mobile.evaluate(() => document.documentElement.scrollWidth <= innerWidth), true);
  await mobile.screenshot({ path: path.join(images, 'arena_m1_mobile.png') });
  await mobile.close();
  assert.deepEqual(errors, []);
  console.log(JSON.stringify({ status: 'passed', scope: 'recorded UI only; no inference',
    checks: ['three honestly named arms', 'false-source failure', 'conflict rule', 'reference toggle',
      'all six family filters', 'previous and next', 'unscorable preserved', 'full trace download',
      'mobile width', 'no browser exceptions'], screenshotDirectory: images }));
  await context.close();
} finally {
  await browser.close();
}
