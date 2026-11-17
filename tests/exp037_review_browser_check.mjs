/** Disposable synthetic browser checks: never persist confirmations into study artifacts. */
import fs from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import assert from 'node:assert/strict';
import {pathToFileURL} from 'node:url';

const playwrightModule=process.env.TDK_PLAYWRIGHT_MODULE;
const executablePath=process.env.TDK_BROWSER_EXECUTABLE;
if(!playwrightModule||!executablePath)throw new Error('Set TDK_PLAYWRIGHT_MODULE and TDK_BROWSER_EXECUTABLE to installed dependencies.');
const {chromium}=await import(playwrightModule);
const temp=await fs.mkdtemp(path.join(os.tmpdir(),'exp037-ui-test-'));
const choices={false_assertion:['NO','UNCLEAR','YES'],answer_status:['ABSTAINS','CORRECT','INCORRECT','MIXED','UNCLEAR'],evidence_status:['CONTRADICTED','MIXED','NO_CLAIM','SUPPORTED','UNCLEAR','UNSUPPORTED'],context_answerable:['NO','UNCLEAR','YES'],conflict_acknowledged:['NO','NOT_APPLICABLE','UNCLEAR','YES']};
const labels={false_assertion:'NO',answer_status:'CORRECT',evidence_status:'SUPPORTED',context_answerable:'YES',conflict_acknowledged:'NOT_APPLICABLE'};
const valid={valid:true,validation_error:null,proposal:{...labels,rationale:'Synthetic UI control, not human review.',response_spans:['Cedar Hawks won.'],context_spans:[{doc_id:'D1',quote:'Cedar Hawks won.'}]}};
const payload={source_sha256:'test-source',raw_sha256:'test-raw',proposals_sha256:'test-proposals',label_choices:choices,cases:Array.from({length:100},(_,i)=>({case_id:'TOY-'+String(i).padStart(3,'0'),question:'Who won?',benchmark_reference_answer:'Cedar Hawks',context_A:'D1: Cedar Hawks won.',context_B:'D1: Cedar Hawks won.',response_A:'Cedar Hawks won.',response_B:'Cedar Hawks won.',proposals:{A:valid,B:i===1?{valid:false,validation_error:'Synthetic invalid quote',proposal:null}:valid}}))};
const template=await fs.readFile('docs/exp037_author_review_template.html','utf8');
const fixture=path.join(temp,'fixture.html');
await fs.writeFile(fixture,template.replace('__DATA_JSON__',JSON.stringify(payload)));
const browser=await chromium.launch({headless:true,executablePath});
try{
 const context=await browser.newContext({acceptDownloads:true,viewport:{width:1440,height:1000}});
 const page=await context.newPage();const errors=[];page.on('pageerror',e=>errors.push(e.message));
 await page.goto(pathToFileURL(fixture).href);
 assert.equal(await page.locator('#progress').textContent(),'0 / 200 responses reviewed');
 assert.equal(await page.locator('article').count(),2);
 const checks=page.locator('.check input');
 await checks.nth(0).click();assert.equal(await checks.nth(0).isChecked(),false);
 assert.match(await page.locator('#status').textContent(),/reviewer ID/);
 await page.locator('#reviewer').fill('SYNTHETIC_UI_TEST');await page.locator('#reviewer').blur();
 await checks.nth(0).check();assert.equal(await page.locator('#progress').textContent(),'1 / 200 responses reviewed');
 await page.getByLabel('A answer_status',{exact:true}).selectOption('UNCLEAR');
 assert.equal(await page.locator('#progress').textContent(),'0 / 200 responses reviewed');
 await checks.nth(0).check();
 const downloadPromise=page.waitForEvent('download');await page.locator('#save').click();const download=await downloadPromise;
 const saved=path.join(temp,'synthetic_review.json');await download.saveAs(saved);
 const data=JSON.parse(await fs.readFile(saved,'utf8'));assert.equal(data.records.filter(r=>r.human_reviewed).length,1);assert.equal(data.independent_review,false);assert.equal(data.status,'author_review_partial');
 await page.locator('#next').click();assert.equal(await page.getByLabel('B answer_status',{exact:true}).inputValue(),'');
 await page.reload();assert.equal(await page.locator('#progress').textContent(),'1 / 200 responses reviewed');
 page.on('dialog',d=>d.accept());await page.locator('#file').setInputFiles(saved);
 await page.waitForFunction(()=>document.getElementById('status').textContent==='Saved review restored.');
 const bad={...data,source_sha256:'another-source'};const badFile=path.join(temp,'wrong_source.json');await fs.writeFile(badFile,JSON.stringify(bad));await page.locator('#file').setInputFiles(badFile);await page.waitForFunction(()=>document.getElementById('status').textContent.includes('different study inputs'));
 assert.equal(await page.locator('#progress').textContent(),'1 / 200 responses reviewed');
 await page.setViewportSize({width:390,height:844});
 assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),true);
 assert.deepEqual(errors,[]);
 console.log(JSON.stringify({status:'passed',scope:'synthetic fixture only',checks:['initially unreviewed','reviewer required','per-response confirmation','edit clears confirmation','partial export','invalid proposal blanks','local restore','backup import','wrong-source rejection','mobile width','no browser errors'],temporaryDirectory:temp}));
 await context.close();
}finally{await browser.close()}
