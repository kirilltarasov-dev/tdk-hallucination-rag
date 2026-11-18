/** M2 UI checks. Actual 3-call smoke inference requires TDK_ARENA_LIVE_SMOKE=1. */
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';

if (!process.env.TDK_PLAYWRIGHT_MODULE || !process.env.TDK_BROWSER_EXECUTABLE)
  throw new Error('Set the installed Playwright module and Chromium executable paths.');
const {chromium} = await import(process.env.TDK_PLAYWRIGHT_MODULE);
const browser = await chromium.launch({headless:true, executablePath:process.env.TDK_BROWSER_EXECUTABLE});
const runRoot = path.resolve('results/arena_runs');
async function runs() {
  return (await fs.readdir(runRoot).catch(e => e.code === 'ENOENT' ? [] : Promise.reject(e)))
    .filter(name => /^[a-f0-9]{32}$/.test(name)).sort();
}
const before = await runs();
const errors = [];
try {
  const page = await browser.newPage({viewport:{width:1440,height:1180},acceptDownloads:true});
  page.on('pageerror', error => errors.push(error.message));
  await page.goto(process.env.TDK_ARENA_URL || 'http://127.0.0.1:8501');
  await page.locator('.hero').filter({hasText:'E044-005'}).waitFor();
  await page.getByRole('radio',{name:'Live local run',exact:true}).focus();
  await page.getByRole('radio',{name:'Live local run',exact:true}).press('Space');
  await page.getByText('No local run for these inputs in this session.',{exact:false}).waitFor();
  assert.equal(await page.locator('.answer-card').count(),0);
  assert.deepEqual(await runs(),before);
  await page.getByRole('button',{name:'Source conflict',exact:true}).click();
  await page.locator('.hero').filter({hasText:'E044-013'}).waitFor();
  assert.equal(await page.locator('.answer-card').count(),0);
  await page.getByRole('button',{name:'Paraphrase example',exact:true}).click();
  await page.locator('.hero').filter({hasText:'E044-005'}).waitFor();
  assert.deepEqual(await runs(),before);

  let smoke = null;
  if (process.env.TDK_ARENA_LIVE_SMOKE === '1') {
    await page.getByRole('button',{name:'Run three systems locally',exact:true}).click();
    await page.getByRole('heading',{name:'Local run answers',exact:true}).waitFor({timeout:120000});
    assert.deepEqual(await page.locator('.answer-card .name').allTextContents(),
      ['Standard RAG draft','Self-review (S2)','Neuro-symbolic']);
    const pending = page.waitForEvent('download');
    await page.getByRole('button',{name:'Download this case and full trace',exact:true}).click();
    const download = await pending;
    const temp = await fs.mkdtemp(path.join(os.tmpdir(),'arena-m2-smoke-'));
    const file = path.join(temp,'export.json');
    await download.saveAs(file);
    const exported = JSON.parse(await fs.readFile(file,'utf8'));
    assert.equal(exported.mode,'live_local');
    assert.equal(exported.case_id,'E044-005');
    assert.deepEqual(Object.keys(exported.result.calls),['S1','S2','V3']);
    assert.equal(exported.result.systems[1].verdict,null);
    assert.equal(exported.result.systems[1].trace.symbolic_verification,false);
    assert.equal((await runs()).length,before.length+1);
    await page.screenshot({path:'results/figures/arena_m2_live.png'});
    await page.getByRole('switch',{name:'Reveal fictional reference',exact:true}).focus();
    await page.getByRole('switch',{name:'Reveal fictional reference',exact:true}).press('Space');
    await page.getByText('Reference hidden.',{exact:false}).waitFor();
    assert.equal(await page.locator('.answer-card .score').count(),0);
    await page.getByRole('button',{name:'Source conflict',exact:true}).click();
    await page.locator('.hero').filter({hasText:'E044-013'}).waitFor();
    await page.getByText('No local run for these inputs in this session.',{exact:false}).waitFor();
    assert.equal(await page.locator('.answer-card').count(),0);
    assert.equal((await runs()).length,before.length+1);
    smoke = {run_id:exported.run_id,saved_directory:exported.saved_directory,
      systems:exported.systems_with_exact_scores.map(s=>({system:s.system_id,answer:s.answer,
        exact_score:s.score.category,source_verdict:s.verdict,latency_seconds:s.latency_seconds}))};
  }
  assert.equal(await page.locator('[data-testid="stException"]').count(),0);
  assert.deepEqual(errors,[]);
  console.log(JSON.stringify({status:'passed',scope:'software acceptance, not an efficacy experiment',
    no_automatic_inference:true,actual_smoke:smoke}));
} finally {await browser.close()}
