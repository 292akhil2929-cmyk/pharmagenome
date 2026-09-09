import {test,expect,type Page} from "@playwright/test";
const system={version:"0.9.0",phase:9,checked_at:"2026-09-08T10:00:00Z",database:{status:"ready",schema_version:"005_drug_response_modeling"},counts:{samples:566,variants:506,genes:10,drugs:10,pathways:72},datasets:[],limitations:[]};
const genomics={dataset:{name:"LUAD SNV cohort",sha256:"a".repeat(64)},summary:{eligible_samples:566,variants:506,observations:839},genes:[{symbol:"TP53",frequency:.51,mutated_samples:289,eligible_samples:566,variants:160},{symbol:"KRAS",frequency:.29,mutated_samples:164,eligible_samples:566,variants:89},{symbol:"STK11",frequency:.17,mutated_samples:96,eligible_samples:566,variants:48}],chromosomes:[{label:"17",count:160},{label:"12",count:105},{label:"19",count:72}],variant_types:[{label:"SNV",count:506}],vaf_histogram:[{label:"0–0.1",count:30},{label:"0.1–0.2",count:90},{label:"0.2–0.3",count:160}]};
const research={dataset:{name:"Open Targets / Reactome research snapshot",sha256:"b".repeat(64)},summary:{selected_genes:10,drugs:10,target_links:24,pathways:72},drugs:{items:[{id:"CHEMBL1",name:"Erlotinib",targets:["EGFR"],report_count:18},{id:"CHEMBL2",name:"Trametinib",targets:["BRAF","KRAS"],report_count:11}]},pathways:{items:[]}};
async function mock(page:Page){
 await page.route("**/api/system",route=>route.fulfill({json:system}));
 await page.route("**/api/genomics**",route=>route.fulfill({json:genomics}));
 await page.route("**/api/research?**",route=>route.fulfill({json:research}));
 await page.route("**/api/research/explain/status",route=>route.fulfill({json:{available:false,model:"gpt-6-astra",reason:"Model credentials are not configured.",policy:"Optional explanation only."}}));
}
for(const width of [1440,700,390]){
 test("analytical dashboard renders real evidence "+width,async({page},testInfo)=>{
  await page.setViewportSize({width,height:1000});
  await page.addInitScript(()=>localStorage.setItem("pharmagenome-analysis-history-v1",JSON.stringify([{id:"run-1",kind:"Drug-response model",title:"Repeated stratified logistic regression · Erlotinib",summary:"ROC-AUC 0.721 · 60 cell lines",view:"ML Analysis",created_at:"2026-09-08T09:00:00Z",source:"NCI-60 curated release"}])));
  await mock(page);await page.goto("/");
  await expect(page.getByRole("heading",{name:"Top mutated genes"})).toBeVisible();
  await expect(page.getByRole("heading",{name:"Mutation trends"})).toBeVisible();
  await expect(page.getByRole("heading",{name:"Variant distribution"})).toBeVisible();
  await expect(page.getByRole("heading",{name:"Drug-target network"})).toBeVisible();
  await expect(page.getByText("24",{exact:true})).toBeVisible();
  await expect(page.getByText("ROC-AUC 0.721 · 60 cell lines")).toBeVisible();
  expect(await page.evaluate(()=>document.documentElement.scrollWidth<=window.innerWidth)).toBe(true);
  await page.screenshot({path:testInfo.outputPath("dashboard-"+width+".png"),fullPage:true});
  if(width<760){
   await page.getByRole("button",{name:"Open navigation"}).click();
   for(const label of ["Dashboard","Genomics","Variants","Genes","Pathways","Drugs","Drug Response","Statistics","ML Analysis","Sequence Analysis","Research Assistant","Data Sources"])await expect(page.getByRole("button",{name:label,exact:true})).toBeVisible();
  }
 });
}
test("dashboard failure can be retried",async({page})=>{
 await page.route("**/api/system",route=>route.fulfill({json:system}));
 let failed=true;
 await page.route("**/api/genomics**",route=>failed?route.fulfill({status:503,json:{detail:"Genomic dashboard unavailable."}}):route.fulfill({json:genomics}));
 await page.route("**/api/research?**",route=>route.fulfill({json:research}));
 await page.goto("/");
 await expect(page.getByRole("heading",{name:"Dashboard evidence unavailable"})).toBeVisible();
 failed=false;await page.getByRole("button",{name:"Retry dashboard evidence"}).click();
 await expect(page.getByRole("heading",{name:"Top mutated genes"})).toBeVisible();
});
test("research assistant preserves the computation boundary",async({page})=>{
 await mock(page);await page.goto("/");
 await page.getByRole("button",{name:"Research Assistant",exact:true}).click();
 await expect(page.getByRole("heading",{name:"Compute first. Explain second."})).toBeVisible();
 await expect(page.getByText("Raw measurements and sample or person identifiers stay outside model requests.")).toBeVisible();
 await expect(page.getByText("Model credentials are not configured.")).toBeVisible();
});
