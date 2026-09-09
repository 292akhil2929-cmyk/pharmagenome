import {test,expect} from "@playwright/test";
const meta={method:"Teaching fixture statistics",method_version:"1.0.0",parameters:{k:2},computed_at:"2026-09-08T08:00:00Z",code_revision:"synthetic-browser-fixture",source:"Synthetic test",limitations:["Synthetic browser fixture; not scientific evidence."]};
const input={sequence:"AACGTN",length:6,sha256:"a".repeat(64)};
const stats={...meta,input,known_bases:5,unknown_bases:1,gc_percent:40,at_percent:60,composition:[{base:"A",count:2,percent:100/3},{base:"C",count:1,percent:100/6},{base:"G",count:1,percent:100/6},{base:"T",count:1,percent:100/6},{base:"N",count:1,percent:100/6}],kmers:{k:2,total_windows:5,valid_windows:4,excluded_windows:1,unique:4,items:["AA","AC","CG","GT"].map(kmer=>({kmer,count:1,frequency:0.25}))}};
const alignment={...meta,method:"Teaching fixture alignment",parameters:{mode:"global",match:2,mismatch:-1,gap:-2},input_a:{...input,sequence:"ACGTACGT",length:8},input_b:{...input,sequence:"ACGTCGT",length:7},score:12,aligned_a:"ACGTACGT",aligned_b:"ACGT-CGT",markers:"|||| |||",columns:8,matches:7,mismatches:0,unknown_pairs:0,gap_columns:1,identity_percent:87.5,range_a:[1,8],range_b:[1,7],matrix:{scores:[[0,-2],[-2,2]],path:[[0,0],[1,1]],row_bases:"A",column_bases:"A"}};
async function setup(page:import("@playwright/test").Page,width:number){
 await page.setViewportSize({width,height:1000});
 await page.route("**/api/system",route=>route.fulfill({json:{version:"0.4.0",phase:4,checked_at:meta.computed_at,database:{status:"not_configured",schema_version:null},counts:null,datasets:[],limitations:[]}}));
 await page.route("**/api/sequences/statistics",route=>route.fulfill({json:stats}));
 await page.route("**/api/sequences/align",route=>route.fulfill({json:alignment}));
 await page.goto("/");
 await expect(page.getByRole("status")).toContainText("Database not configured");
 if(width<=650)await page.getByRole("button",{name:"Open navigation"}).click();
 await page.getByRole("button",{name:"Sequence Analysis",exact:true}).click();
}
for(const width of [1440,390]){
 test("statistics, alignment, exports and responsive states "+width,async({page},info)=>{
  await setup(page,width);
  await expect(page.getByRole("button",{name:"Calculate statistics"})).toBeDisabled();
  await page.getByRole("button",{name:"Load teaching example"}).click();
  await expect(page.getByText("Synthetic teaching example",{exact:false})).toBeVisible();
  const request=page.waitForRequest("**/api/sequences/statistics");
  await page.getByRole("button",{name:"Calculate statistics"}).click();
  expect((await request).postDataJSON().k).toBe(2);
  await expect(page.locator(".sequence-inventory")).toContainText("GC / known bases40.00%");
  await expect(page.getByRole("heading",{name:"Nucleotide composition"})).toBeVisible();
  const download=page.waitForEvent("download");await page.getByRole("button",{name:"Export sequence JSON"}).click();
  expect((await download).suggestedFilename()).toBe("pharmagenome-sequence-statistics.json");
  expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);
  await page.screenshot({path:info.outputPath("statistics-"+width+".png"),fullPage:true});
  await page.getByRole("tab",{name:"Pairwise alignment"}).click();
  await page.getByRole("button",{name:"Load teaching example"}).click();
  await page.getByRole("button",{name:"Align sequences",exact:true}).click();
  await expect(page.locator(".sequence-inventory")).toContainText("Alignment score12");
  await expect(page.getByRole("heading",{name:"Dynamic-programming matrix"})).toBeVisible();
  await expect(page.locator(".alignment-block pre")).toContainText("ACGT-CGT");
  expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);
  await page.screenshot({path:info.outputPath("alignment-"+width+".png"),fullPage:true});
  await page.emulateMedia({reducedMotion:"reduce"});
  await page.getByRole("button",{name:"Switch to dark mode"}).click();
  await page.screenshot({path:info.outputPath("alignment-dark-"+width+".png"),fullPage:true});
  await page.getByLabel("Sequence A",{exact:true}).fill("ACGT");
  await expect(page.getByRole("button",{name:"Export sequence JSON"})).toHaveCount(0);
 });
}
test("file input, validation, retry and keyboard tabs",async({page})=>{
 await setup(page,1440);
 await page.getByLabel("Upload dna sequence",{exact:true}).setInputFiles({name:"teaching.fa",mimeType:"text/plain",buffer:Buffer.from(">teaching\nAACGTN")});
 await expect(page.getByLabel("DNA sequence",{exact:true})).toHaveValue(">teaching\nAACGTN");
 await page.unroute("**/api/sequences/statistics");
 await page.route("**/api/sequences/statistics",route=>route.fulfill({status:422,json:{detail:"DNA must contain only A, C, G, T or N."}}));
 await page.getByRole("button",{name:"Calculate statistics"}).click();
 await expect(page.locator(".sequence-error")).toContainText("DNA must contain only");
 await expect(page.getByRole("button",{name:"Calculate statistics"})).toBeEnabled();
 await page.unroute("**/api/sequences/statistics");
 await page.route("**/api/sequences/statistics",route=>route.fulfill({json:stats}));
 await page.getByRole("button",{name:"Calculate statistics"}).click();
 await expect(page.getByRole("heading",{name:"Nucleotide composition"})).toBeVisible();
 await page.getByRole("tab",{name:"Sequence statistics"}).press("ArrowRight");
 await expect(page.getByRole("tab",{name:"Pairwise alignment"})).toBeFocused();
 await expect(page.getByRole("tab",{name:"Pairwise alignment"})).toHaveAttribute("aria-selected","true");
});
test("no positive local alignment and all-N statistics",async({page})=>{
 await setup(page,1440);
 await page.unroute("**/api/sequences/statistics");
 await page.route("**/api/sequences/statistics",route=>route.fulfill({json:{...stats,gc_percent:null,at_percent:null,known_bases:0,unknown_bases:3,input:{...input,sequence:"NNN",length:3},kmers:{k:2,total_windows:2,valid_windows:0,excluded_windows:2,unique:0,items:[]}}}));
 await page.getByLabel("DNA sequence",{exact:true}).fill("NNN");
 await page.getByRole("button",{name:"Calculate statistics"}).click();
 await expect(page.locator(".sequence-inventory")).toContainText("Not defined");
 await expect(page.getByText("No valid windows.",{exact:false})).toBeVisible();
 await page.getByRole("tab",{name:"Pairwise alignment"}).click();
 await page.getByRole("button",{name:"Load teaching example"}).click();
 await page.getByLabel("Alignment method").selectOption("local");
 await page.unroute("**/api/sequences/align");
 await page.route("**/api/sequences/align",route=>route.fulfill({json:{...alignment,score:0,aligned_a:"",aligned_b:"",markers:"",columns:0,matches:0,gap_columns:0,identity_percent:null,range_a:null,range_b:null}}));
 await page.getByRole("button",{name:"Align sequences",exact:true}).click();
 await expect(page.getByText("No positive local alignment was found",{exact:false})).toBeVisible();
 await expect(page.locator(".alignment-block")).toHaveCount(0);
});
