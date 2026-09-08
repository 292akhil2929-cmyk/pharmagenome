import {test,expect} from "@playwright/test";
const dataset={id:1,name:"Synthetic genomic browser fixture",sha256:"a".repeat(64),retrieved_at:"2026-09-08T07:40:20Z",is_fixture:true,source:"Synthetic test data",url:"https://www.cbioportal.org/"};
const genes=[{id:7157,symbol:"TP53",gene_type:"protein-coding",mutated_samples:1,eligible_samples:3,frequency:1/3,variants:2,observed_chromosomes:["17"]},{id:1956,symbol:"EGFR",gene_type:"protein-coding",mutated_samples:0,eligible_samples:3,frequency:0,variants:0,observed_chromosomes:[]}];
const row={variant_id:1,assembly:"GRCh37",chromosome:"17",position:100,ref:"A",alt:"T",variant_type:"SNV",genes:["TP53"],consequences:["Missense_Mutation"],samples:1,vaf_min:0.25,vaf_max:0.25,vaf_measured:1};
const base={dataset,method:"distinct-profiled-samples-v1",computed_at:"2026-09-08T08:00:00Z",code_revision:"test-fixture",filters:{},limitations:["Synthetic test fixture, not scientific evidence."],options:{studies:[["study-a","Synthetic study"]],diseases:[["1","Synthetic disease"]],genes:["EGFR","TP53"],chromosomes:["17"],variant_types:["SNV"]},summary:{eligible_samples:3,mutated_samples:1,variants:2,observations:2,affected_genes:1,missing_vaf:0},genes,variants:{items:[row],total:2,page:1,page_size:1},chromosomes:[{label:"17",count:2}],variant_types:[{label:"SNV",count:2}],vaf_histogram:Array.from({length:10},(_,i)=>({label:i*10+"–"+(i+1)*10+"%",count:i===2?2:0})),heatmap:{page:1,page_size:40,total:3,samples:["TEST-A","TEST-B","TEST-C"],rows:[{symbol:"TP53",values:[1,0,0]},{symbol:"EGFR",values:[0,0,0]}]}};
async function setup(page:import("@playwright/test").Page){
 await page.route("**/api/system",route=>route.fulfill({json:{version:"0.3.0",phase:3,checked_at:base.computed_at,database:{status:"ready",schema_version:"003_genomics"},counts:{samples:0,variants:0,genes:0,drugs:0,pathways:0},datasets:[],limitations:[]}}));
 await page.route("**/api/genomics?*",route=>{
  const params=new URL(route.request().url()).searchParams;
  const empty=params.get("q")==="MISSING";
  const pageNum=Number(params.get("page")||1);
  return route.fulfill({json:{...base,filters:Object.fromEntries(params),summary:empty?{...base.summary,variants:0,observations:0,mutated_samples:0,affected_genes:0}:base.summary,genes:empty?[]:params.get("gene")==="TP53"?[genes[0]]:genes,variants:empty?{items:[],total:0,page:1,page_size:25}:{...base.variants,page:pageNum,items:[{...row,variant_id:pageNum,position:pageNum===1?100:200}]}}});
 });
}
async function openGenomics(page:import("@playwright/test").Page,width:number){
 await page.goto("/");
 if(width<=650)await page.getByRole("button",{name:"Open navigation"}).click();
 await page.getByRole("button",{name:"Genomics",exact:true}).click();
 await expect(page.getByText("Synthetic development fixture",{exact:false})).toBeVisible();
}
for(const width of [1440,390]){
 test("genomic charts, detail, export and responsive evidence "+width,async({page},info)=>{
  await page.setViewportSize({width,height:1000});await setup(page);await openGenomics(page,width);
  await expect(page.getByRole("heading",{name:"Observed SNV frequency"})).toBeVisible();
  await expect(page.getByRole("heading",{name:"Sample mutation matrix"})).toBeVisible();
  await expect(page.locator(".analysis-inventory")).toContainText("Eligible samples3");
  await expect(page.locator(".genomics .data-table").first()).toContainText("33.3%");
  await page.getByRole("button",{name:"TP53",exact:true}).click();
  await expect(page.getByText("Full name / gene coordinates")).toBeVisible();
  await expect(page.getByText("Not yet imported",{exact:true})).toBeVisible();
  await page.getByRole("button",{name:"17:100:A>T",exact:true}).click();
  await expect(page.getByText("Not supplied; no clinical interpretation")).toBeVisible();
  const download=page.waitForEvent("download");await page.getByRole("button",{name:"Export analysis JSON"}).click();
  expect((await download).suggestedFilename()).toBe("pharmagenome-genomics-dataset-1.json");
  expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);
  await page.screenshot({path:info.outputPath("genomics-"+width+".png"),fullPage:true});
  await page.getByRole("button",{name:"Switch to dark mode"}).click();
  await page.screenshot({path:info.outputPath("genomics-dark-"+width+".png"),fullPage:true});
 });
}
test("filters, pagination, empty result and service recovery",async({page})=>{
 await setup(page);await openGenomics(page,1440);
 await page.getByRole("button",{name:"Next variant page"}).click();
 await expect(page.getByRole("button",{name:"17:200:A>T"})).toBeVisible();
 await page.getByLabel("Gene",{exact:true}).selectOption("TP53");
 await page.getByRole("button",{name:"Apply filters",exact:true}).click();
 await expect(page.getByText("Applied: gene TP53",{exact:false})).toBeVisible();
 await expect(page.locator(".analysis-inventory")).toContainText("Eligible samples3");
 await page.getByLabel("Search gene or variant locus").fill("MISSING");
 await page.getByRole("button",{name:"Apply filters",exact:true}).click();
 await expect(page.getByText("No variants match these filters.",{exact:false})).toBeVisible();
 await expect(page.getByRole("button",{name:"Next variant page"})).toBeDisabled();
 await page.unroute("**/api/genomics?*");
 await page.route("**/api/genomics?*",route=>route.fulfill({status:503,json:{detail:"Analysis temporarily unavailable."}}));
 await page.getByRole("button",{name:"Reset",exact:true}).click();
 await expect(page.getByRole("heading",{name:"Genomic results unavailable",exact:true})).toBeVisible();
 await expect(page.getByRole("button",{name:"Export analysis JSON"})).toHaveCount(0);
 await page.unroute("**/api/genomics?*");
 await page.route("**/api/genomics?*",route=>route.fulfill({json:base}));
 await page.getByRole("button",{name:"Retry analysis"}).click();
 await expect(page.getByRole("heading",{name:"Observed SNV frequency"})).toBeVisible();
});
test("dedicated explorer navigation",async({page})=>{
 await setup(page);await openGenomics(page,1440);
 await page.getByRole("button",{name:"Gene explorer",exact:true}).click();
 await expect(page.getByRole("heading",{name:"Gene explorer",exact:true})).toBeVisible();
 await expect(page.getByRole("heading",{name:"Variant explorer",exact:true})).toHaveCount(0);
 await page.getByRole("button",{name:"Variant explorer",exact:true}).click();
 await expect(page.getByRole("heading",{name:"Variant explorer",exact:true})).toBeVisible();
 await expect(page.getByRole("heading",{name:"Gene explorer",exact:true})).toHaveCount(0);
});
