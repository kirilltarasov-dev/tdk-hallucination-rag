/** M3 editor acceptance. Optional AI + three-system smoke: TDK_ARENA_M3_SMOKE=1. */
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
const {chromium} = await import(process.env.TDK_PLAYWRIGHT_MODULE);
const browser = await chromium.launch({headless:true, executablePath:process.env.TDK_BROWSER_EXECUTABLE});
const runRoot = path.resolve('results/arena_runs');
const runs = async () => (await fs.readdir(runRoot)).filter(n => /^[a-f0-9]{32}$/.test(n)).sort();
const before = await runs();
const errors = [];
const temporary = await fs.mkdtemp(path.join(os.tmpdir(),'arena-m3-check-'));
async function toggle(page, name) {
  const control = page.getByRole('switch',{name,exact:true});
  await control.focus(); await control.press('Space');
}
async function select(page, name, option) {
  await page.locator('[data-testid="stStatusWidget"]').waitFor({state:'hidden'});
  await page.getByRole('combobox',{name,exact:true}).click();
  await page.getByRole('option',{name:option,exact:true}).click();
  await page.locator('[data-testid="stStatusWidget"]').waitFor({state:'hidden'});
}
try {
  const page = await browser.newPage({viewport:{width:1440,height:1180},acceptDownloads:true});
  page.on('pageerror',e=>errors.push(e.message));
  await page.goto(process.env.TDK_ARENA_URL || 'http://127.0.0.1:8501');
  await page.locator('.hero').filter({hasText:'E044-005'}).waitFor();
  const mode = page.getByRole('radio',{name:'Live local run',exact:true});
  await mode.focus(); await mode.press('Space');
  await page.getByText('Attack editor',{exact:true}).click();
  await toggle(page,'Insert an attack passage');
  await page.getByText('Enter a nonempty attack passage or disable insertion',{exact:true}).waitFor();
  assert.equal(await page.getByRole('button',{name:'Run three systems locally',exact:true}).count(),0);
  for (const [kind, snippet] of [['Date shift','2136 Willow Cup'], ['Ordinal swap','first, not second'],
    ['Entity swap','Obsidian Otters won'], ['Contradicting number','two joint winners'],
    ['Fake correction notice','Correction notice'], ['Similar-topic distractor','Junior Willow Cup']]) {
    await select(page,'Attack template',kind);
    await page.getByRole('button',{name:'Load template into editor',exact:true}).click();
    await page.locator('.source').first().filter({hasText:snippet}).waitFor();
    assert.equal(await page.locator('.answer-card').count(),0);
  }
  await select(page,'Insertion position','2 of 2');
  await page.locator('.source').last().filter({hasText:'Junior Willow Cup'}).waitFor();
  assert.match(await page.locator('.source').first().innerText(),/Crimson Swans/);
  await page.getByRole('textbox',{name:'Attack passage',exact:true}).fill('Custom adversarial source text.');
  await page.getByRole('textbox',{name:'Attack passage',exact:true}).press('Tab');
  await page.locator('.source').last().filter({hasText:'Custom adversarial source text.'}).waitFor();
  assert.deepEqual(await runs(),before);
  await toggle(page,'Insert an attack passage');
  await page.locator('.hero').filter({hasText:'1 supplied passage(s)'}).waitFor();
  assert.equal(await page.locator('.source').count(),1);
  await toggle(page,'Insert an attack passage');
  await select(page,'Attack template','Entity swap');
  await page.getByRole('button',{name:'Load template into editor',exact:true}).click();
  await page.locator('.source').filter({hasText:'Obsidian Otters'}).waitFor();
  let smoke = null;
  if (process.env.TDK_ARENA_M3_SMOKE === '1') {
    await page.getByRole('button',{name:'Ask local AI for an attack',exact:true}).click();
    await page.getByText('Editable AI proposal',{exact:false}).waitFor({timeout:120000});
    assert.equal((await runs()).length,before.length+1);
    assert.equal(await page.locator('.answer-card').count(),0);
    const proposal = await page.getByRole('textbox',{name:'Attack passage',exact:true}).inputValue();
    assert.ok(proposal.trim().length>0);
    await page.getByRole('button',{name:'Run three systems locally',exact:true}).click();
    await page.getByRole('heading',{name:'Local run answers',exact:true}).waitFor({timeout:120000});
    assert.equal(await page.locator('.answer-card').count(),3);
    const downloadPromise = page.waitForEvent('download');
    await page.getByRole('button',{name:'Download this case and full trace',exact:true}).click();
    const download = await downloadPromise;
    const file = path.join(temporary,'export.json'); await download.saveAs(file);
    const exported = JSON.parse(await fs.readFile(file,'utf8'));
    assert.equal(exported.attack.text,proposal);
    assert.equal(exported.attack.input_hash,exported.result.input_hash);
    assert.equal(exported.attack.origin,'AI proposal');
    assert.ok(exported.attack.proposal_run_id);
    assert.equal((await runs()).length,before.length+2);
    smoke = {run_id:exported.run_id,proposal_run_id:exported.attack.proposal_run_id,
      systems:exported.systems_with_exact_scores.map(s=>({system:s.system_id,answer:s.answer,
        verdict:s.verdict,score:s.score.category}))};
    await page.getByRole('textbox',{name:'Attack passage',exact:true}).fill(proposal+' A revised passage.');
    await page.getByRole('textbox',{name:'Attack passage',exact:true}).press('Tab');
    await page.getByText('No local run for these inputs in this session.',{exact:false}).waitFor();
    assert.equal(await page.locator('.answer-card').count(),0);
    assert.equal((await runs()).length,before.length+2);
  }
  await page.getByRole('heading',{name:'Run three verification approaches',exact:true}).scrollIntoViewIfNeeded();
  const imagePath = process.env.TDK_ARENA_M3_SCREENSHOT || path.join(temporary,'arena_m3_editor.png');
  await page.screenshot({path:imagePath});
  assert.equal(await page.locator('[data-testid="stException"]').count(),0);
  assert.deepEqual(errors,[]);
  if (!smoke) assert.deepEqual(await runs(),before);
  console.log(JSON.stringify({status:'passed',scope:'M3 software acceptance; not an efficacy experiment',
    templates_checked:6,automatic_calls:0,smoke,screenshot:imagePath}));
} finally {await browser.close()}
