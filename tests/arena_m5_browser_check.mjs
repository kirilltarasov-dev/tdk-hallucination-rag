/** M5 local UI and 20 browser-session read checks; no inference. Archives must be imported. */
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
const {chromium}=await import(process.env.TDK_PLAYWRIGHT_MODULE);
const browser=await chromium.launch({headless:true,executablePath:process.env.TDK_BROWSER_EXECUTABLE});
const temporary=await fs.mkdtemp(path.join(os.tmpdir(),'arena-m5-'));
const images=process.env.TDK_ARENA_M5_SCREENSHOT_DIR || temporary;
await fs.mkdir(images,{recursive:true});
const runs=async()=> (await fs.readdir('results/arena_runs')).filter(n=>/^[a-f0-9]{32}$/.test(n)).sort();
const before=await runs();
const errors=[];
const url=process.env.TDK_ARENA_URL || 'http://127.0.0.1:8501';
let page;
async function openLedger(page){
 page.on('pageerror',e=>errors.push(e.message));
 await page.goto(url);
 const control=page.getByRole('radio',{name:'Round ledger',exact:true});
 await page.locator('.proof-verdict').waitFor();
 await page.locator('[data-testid="stApp"][data-test-script-state="notRunning"]').waitFor();
 await control.focus();await control.press('Space');
 await page.getByRole('heading',{name:'Arena round ledger',exact:true}).waitFor({timeout:60000});
 await page.getByRole('button',{name:'Export population as JSONL',exact:true}).waitFor();
 assert.equal(await page.locator('[data-testid="stException"]').count(),0);
}
async function select(name,option){
 await page.waitForTimeout(250);
 await page.locator('[data-testid="stApp"][data-test-script-state="notRunning"]').waitFor();
 const control=page.getByRole('combobox',{name,exact:true});
 await control.scrollIntoViewIfNeeded();await page.waitForTimeout(250);await control.click();await control.fill(option);
 await page.getByRole('option',{name:option,exact:true}).click({force:true});
 await page.waitForTimeout(250);
 assert.equal(await control.inputValue(),option);
}
try {
 page=await browser.newPage({viewport:{width:1440,height:1180},acceptDownloads:true});
 await openLedger(page);
 await page.getByText('No completed evaluation rounds in this selection.',{exact:true}).waitFor();
 await select('Record population','Archived demo examples');
 await page.locator('.ledger-counts').waitFor();
 assert.equal(await page.locator('.ledger-counts tbody tr').count(),6);
 const metrics=await page.locator('[data-testid="stMetricValue"]').allTextContents();
 assert.deepEqual(metrics,['2','1','0','0']);
 await page.getByRole('heading',{name:'Arena round ledger',exact:true}).scrollIntoViewIfNeeded();
 await page.screenshot({path:path.join(images,'arena_m5_ledger.png')});
 await select('Attack origin filter','AI proposal');
 assert.equal(await page.locator('.ledger-counts tbody tr').count(),3);
 const pending=page.waitForEvent('download');
 await page.getByRole('button',{name:'Export population as JSONL',exact:true}).click();
 const download=await pending;const file=path.join(temporary,'ledger.jsonl');await download.saveAs(file);
 const records=(await fs.readFile(file,'utf8')).trim().split('\n').map(JSON.parse);
 assert.equal(records.length,3);
 assert.ok(records.every(r=>r.origin==='archived_demo'&&r.round.origin==='archived_demo'));
 assert.equal(records.filter(r=>r.round.task==='evaluation').length,2);
 const wrong=records.find(r=>r.round.run_id==='0084deabb5bb478488123c78f5af864b');
 assert.equal(wrong.round.exact_scores.S2.category,'WRONG');
 assert.equal(wrong.round.exact_scores.Candidate_NS.category,'ABSTAIN');
 await page.locator('[data-testid="stImage"] img').screenshot({path:path.join(images,'arena_m5_entry_qr.png')});
 await page.getByText('Local entry only:',{exact:false}).waitFor();
 await select('Record population','Software simulations (not observations)');
 await page.getByText('Software test records only. These are not model measurements.',{exact:true}).waitFor();
 assert.equal(await page.locator('.ledger-counts').count(),0);
 // Separate browser contexts give independent anonymous sessions. This reads the
 // ledger only; concurrent model-serving throughput is not being tested.
 const pages=await Promise.all(Array.from({length:20},()=>browser.newPage({viewport:{width:1100,height:800}})));
 await Promise.all(pages.map(p=>openLedger(p)));
 await Promise.all(pages.map(async p=>{
   await p.getByText('No completed evaluation rounds in this selection.',{exact:true}).waitFor();
   assert.equal(await p.locator('[data-testid="stException"]').count(),0);
 }));
 await Promise.all(pages.map(p=>p.close()));
 assert.deepEqual(await runs(),before);assert.deepEqual(errors,[]);
 const report={status:'passed',scope:'M5 local UI and 20 simultaneous read-only browser sessions; not inference throughput',
  model_calls:0,browser_sessions:20,archived_evaluations:2,archived_proposals:1,
  checks:['population isolation','exact count table','attack filter','complete JSONL export','entry QR display','no automatic inference']};
 console.log(JSON.stringify({...report,screenshots:images}));
 if(process.env.TDK_ARENA_M5_REPORT)await fs.writeFile(process.env.TDK_ARENA_M5_REPORT,JSON.stringify(report,null,2)+'\n',{flag:'wx'});
}catch(error){if(page){console.error((await page.locator('body').innerText()).slice(-5000));await page.screenshot({path:path.join(temporary,'failure.png')});console.error('Failure screenshot: '+temporary)}throw error}
finally{await browser.close()}
