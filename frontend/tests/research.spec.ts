import {test,expect,Page} from "@playwright/test";
const dataset={id:2,name:"Synthetic association browser fixture",sha256:"b".repeat(64),retrieved_at:"2026-09-08T13:52:00Z",is_fixture:true,source:"Synthetic test source",url:"https://platform.opentargets.org/"};
const genes=[{id:1956,symbol:"EGFR",name:"Synthetic target one",ensembl:"ENSG00000146648"},{id:7157,symbol:"TP53",name:"Synthetic target two",ensembl:"ENSG00000141510"}];
const association={gene_id:1956,symbol:"EGFR",maximum_stage:"PHASE_2",mechanisms:[{mechanism:"Synthetic mechanism for layout testing",action:"INHIBITOR",target_ids:["ENSG00000146648"]}],diseases:[{id:"EFO_TEST",name:"Synthetic disease"}],reports:[{id:"fixture-report",source:"TEST",url:"https://example.org/research"}]};
const drug={id:"TEST_DRUG",name:"Synthetic compound",drug_class:"Small molecule",maximum_stage:"PHASE_2",url:"https://example.org/drug",targets:["EGFR"],report_count:1,associations:[association]};
const pathway={id:"R-HSA-TEST",name:"Synthetic pathway membership",genes:["EGFR","TP53"],overlap:2,selected_gene_count:2,url:"https://example.org/pathway"};
const base={dataset,datasets:[dataset],method:"Synthetic browser fixture",computed_at:dataset.retrieved_at,code_revision:"test-fixture",limitations:["Synthetic test fixture, not scientific evidence."],export_scope:"Current pages with source parameters.",selected_genes:genes,options:{genes,drug_classes:["Small molecule"],stages:["PHASE_2"],diseases:[["EFO_TEST","Synthetic disease"]]},summary:{selected_genes:2,drugs:21,target_links:21,pathways:21},drugs:{items:[drug],page:1,page_size:20,total:21},pathways:{items:[pathway],page:1,page_size:20,total:21}};
async function setup(page:Page){
 await page.route("**/api/system",r=>r.fulfill({json:{version:"0.5.0",phase:5,checked_at:dataset.retrieved_at,database:{status:"ready",schema_version:"004_research_associations"},counts:{samples:0,variants:0,genes:2,drugs:1,pathways:1},datasets:[{...dataset,version:dataset.sha256,license:"Synthetic fixture",manifest:{kind:"research_associations",limitations:["Synthetic browser fixture"]},valid:1,downloaded:1,excluded:0,invalid:0,duplicates:0,report:{unit:"source drug-target candidate rows",method:"Synthetic validation",exclusion_reasons:{},validation_reasons:{}}}],limitations:[]}}));
 await page.route("**/api/research?*",r=>{
  const p=new URL(r.request().url()).searchParams;
  const empty=p.get("q")==="MISSING", selected=p.get("genes")==="EGFR"?[genes[0]]:genes;
  return r.fulfill({json:{...base,selected_genes:selected,summary:{...base.summary,selected_genes:selected.length,drugs:empty?0:21},drugs:{...base.drugs,items:empty?[]:[drug],total:empty?0:21,page:Number(p.get("page")||1)},pathways:{...base.pathways,page:Number(p.get("pathway_page")||1)}}});
 });
 await page.goto("/");await expect(page.getByText("Database connected",{exact:true})).toBeVisible();
}
async function open(page:Page,width=1440){if(width===390)await page.getByRole("button",{name:"Open navigation",exact:true}).click();await page.getByRole("button",{name:"Drugs",exact:true}).click();await expect(page.getByRole("heading",{name:"Drug research catalogue",exact:true})).toBeVisible();}
for(const width of [1440,390])test("research evidence, navigation and responsive states "+width,async({page},testInfo)=>{
 await page.setViewportSize({width,height:1000});await page.emulateMedia({reducedMotion:"reduce"});await setup(page);await open(page,width);
 await expect(page.locator(".research-source")).toContainText("Synthetic development fixture");
 await page.screenshot({path:testInfo.outputPath("research-"+width+".png"),fullPage:true});
 await page.locator(".research-drugs").getByRole("button",{name:"Synthetic compound",exact:true}).click();
 await expect(page.getByText("Synthetic mechanism for layout testing",{exact:false})).toBeVisible();
 await page.getByText("Associated research diseases (1)",{exact:true}).click();await expect(page.getByRole("link",{name:"Synthetic disease",exact:true})).toBeVisible();
 await expect(page.getByRole("link",{name:"TEST · fixture-report",exact:true})).toHaveAttribute("href","https://example.org/research");
 await page.locator(".research-pathways").getByRole("button",{name:"Synthetic pathway membership",exact:true}).click();
 await expect(page.getByLabel("Pathway details",{exact:true})).toContainText("No p-value is calculated.");
 const download=page.waitForEvent("download");await page.getByRole("button",{name:"Export research JSON",exact:true}).click();expect((await download).suggestedFilename()).toBe("pharmagenome-research-dataset-2.json");
 await page.emulateMedia({reducedMotion:"reduce"});await page.getByRole("button",{name:"Switch to dark mode",exact:true}).click();
 await page.screenshot({path:testInfo.outputPath("research-dark-"+width+".png"),fullPage:true});
 expect(await page.evaluate(()=>document.documentElement.scrollWidth<=window.innerWidth)).toBeTruthy();
 await page.getByRole("button",{name:"Next drugs",exact:true}).click();await expect(page.locator(".research-drugs .pagination")).toContainText("Page 2 of 2");
 await expect(page.getByRole("button",{name:"Close drug details",exact:true})).toHaveCount(0);
 await page.getByRole("button",{name:"Next pathways",exact:true}).click();await expect(page.locator(".research-pathways .pagination")).toContainText("Page 2 of 2");
});
test("filter scope, pending state, empty results and recovery",async({page})=>{
 await setup(page);await open(page);
 await page.getByRole("checkbox",{name:"TP53",exact:true}).uncheck();
 await expect(page.getByRole("checkbox",{name:"EGFR",exact:true})).toBeDisabled();
 await expect(page.getByText("Filters changed. Apply research filters to update the results below.",{exact:true})).toBeVisible();
 await page.getByLabel("Drug name or identifier",{exact:true}).fill("MISSING");
 const request=page.waitForRequest(r=>r.url().includes("/api/research?")&&r.url().includes("MISSING"));
 await page.getByRole("button",{name:"Apply research filters",exact:true}).click();
 expect(new URL((await request).url()).searchParams.get("genes")).toBe("EGFR");
 await expect(page.getByText("No drugs match these filters.",{exact:false})).toBeVisible();
 await expect(page.locator(".research-pathways")).toContainText("Synthetic pathway membership");
 await page.route("**/api/research?*",r=>r.fulfill({status:503,json:{detail:"Synthetic outage"}}));
 await page.getByRole("button",{name:"Reset research filters",exact:true}).click();
 await expect(page.locator(".research-error")).toContainText("Synthetic outage");
 await expect(page.getByRole("button",{name:"Export research JSON",exact:true})).toHaveCount(0);
 await page.route("**/api/research?*",r=>r.fulfill({json:base}));
 await page.getByRole("button",{name:"Retry research connection",exact:true}).click();
 await expect(page.getByRole("heading",{name:"Drug research catalogue",exact:true})).toBeVisible();
});
test("mixed source inventory uses correct record semantics",async({page})=>{
 await setup(page);await page.getByRole("button",{name:"Data Sources",exact:true}).click();
 await expect(page.getByText("Accepted target links",{exact:true})).toBeVisible();
 await expect(page.getByText("Missing tumour VAF",{exact:true})).toHaveCount(0);
 await expect(page.getByText("Accepted records are source drug-target links",{exact:false})).toBeVisible();
});
