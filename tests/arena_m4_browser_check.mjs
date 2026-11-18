/** M4 proof-view acceptance; no inference. */
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
const {chromium}=await import(process.env.TDK_PLAYWRIGHT_MODULE);
const browser=await chromium.launch({headless:true,executablePath:process.env.TDK_BROWSER_EXECUTABLE});
const temporary=await fs.mkdtemp(path.join(os.tmpdir(),'arena-m4-'));
const images=process.env.TDK_ARENA_M4_SCREENSHOT_DIR || temporary;
await fs.mkdir(images,{recursive:true});
const runs=async()=> (await fs.readdir('results/arena_runs')).filter(n=>/^[a-f0-9]{32}$/.test(n)).sort();
const before=await runs();
const errors=[];
let page;
async function settled(){await page.waitForTimeout(250);await page.locator('[data-testid="stApp"][data-test-script-state="notRunning"]').waitFor()}
async function mode(name){await settled();const input=page.getByRole('radio',{name,exact:true});await input.focus();await input.press('Space')}
async function select(name,option){
 await settled();
 const control=page.getByRole('combobox',{name,exact:true});
 await control.scrollIntoViewIfNeeded();await control.click();
 const target=page.getByRole('option',{name:option,exact:true});
 await target.waitFor();
 // The graph resizes during popup layout; select the visible option without
 // requiring its bounding box to stop moving between animation frames.
 await target.click({force:true});await settled();
 assert.equal(await control.inputValue(),option);
}

try {
 page=await browser.newPage({viewport:{width:1440,height:1180},acceptDownloads:true});
 page.on('pageerror',e=>errors.push(e.message));
 await page.goto(process.env.TDK_ARENA_URL || 'http://127.0.0.1:8501');
 await page.locator('.proof-verdict').filter({hasText:'VERIFIED'}).waitFor();
 await page.getByRole('button',{name:'Source conflict',exact:true}).click();
 await page.locator('.proof-verdict').filter({hasText:'CONFLICT'}).waitFor();
 assert.equal(await page.locator('.proof-source mark').count(),2);
 await page.getByRole('button',{name:'False source',exact:true}).click();
 await page.locator('.notice.fail').waitFor();
 assert.match(await page.locator('.proof-verdict').innerText(),/VERIFIED/);
 await mode('Proof examples');
 await page.locator('.proof-verdict').filter({hasText:'R6_ANSWER_MISMATCH'}).waitFor();
 await page.locator('[data-testid="stGraphVizChart"] svg').waitFor();
 assert.match(await page.locator('[data-testid="stGraphVizChart"]').innerText(),/Velvet Otters 19/);
 assert.match(await page.locator('.proof-source mark').innerText(),/Velvet Otters 19 took first place/);
 assert.match(await page.locator('.proof-checks').innerText(),/Full-source audit\s+PASSED/);
 await page.getByRole('heading',{name:'Inspect the proof, including its limits',exact:true}).scrollIntoViewIfNeeded();
 await page.screenshot({path:path.join(images,'arena_m4_refuted.png')});
 await select('Inspect a proof source','D1');
 assert.equal(await page.locator('.proof-source').count(),1);
 await page.locator('.proof-source').scrollIntoViewIfNeeded();
 await page.screenshot({path:path.join(images,'arena_m4_witness.png')});
 const pending=page.waitForEvent('download');
 await page.getByRole('button',{name:'Download example with provenance',exact:true}).click();
 const download=await pending;const file=path.join(temporary,'example.json');await download.saveAs(file);
 const exported=JSON.parse(await fs.readFile(file,'utf8'));
 assert.equal(exported.trace.decision.verdict,'REFUTED');
 assert.equal(exported.new_model_calls,0);
 assert.equal(exported.provenance.mode,'retrospective_candidate_replay');
 await select('Proof example','Extraction failure · saved M3 round');
 await page.locator('.proof-verdict').filter({hasText:'I1_ORIGINAL_EXTRACTION_INVALID'}).waitFor();
 assert.match(await page.locator('.proof-checks').innerText(),/Full-source audit\s+NOT REACHED/);
 assert.equal(await page.locator('.proof-source mark').count(),1);
 assert.match(await page.locator('.proof-source').first().innerText(),/not declared false/);
 assert.doesNotMatch(await page.locator('[data-testid="stGraphVizChart"]').innerText(),/NEURAL FACT/);
 await page.getByRole('heading',{name:'Inspect the proof, including its limits',exact:true}).scrollIntoViewIfNeeded();
 await page.screenshot({path:path.join(images,'arena_m4_extraction_failure.png')});
 await page.setViewportSize({width:390,height:844});
 // Collapse the sidebar after changing viewport, as a mobile user would.
 const collapse=page.getByRole('button',{name:'Close sidebar',exact:true});
 if(await collapse.isVisible())await collapse.click();
 assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),true);
 assert.equal(await page.locator('[data-testid="stException"]').count(),0);
 assert.deepEqual(errors,[]);assert.deepEqual(await runs(),before);
 console.log(JSON.stringify({status:'passed',scope:'M4 proof UI; zero model calls',
  checks:['graph','REFUTED witness','CONFLICT witnesses','false source remains VERIFIED','executed stages',
   'source selection','provenance export','extraction failure','mobile page width'],screenshots:images}));
} catch(error){if(page)console.error((await page.locator('body').innerText()).slice(-5000));throw error}
finally{await browser.close()}
