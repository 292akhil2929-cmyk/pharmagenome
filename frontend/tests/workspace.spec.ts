import {test,expect} from "@playwright/test";
const snapshot={version:"0.1.0",phase:1,checked_at:"2026-09-08T10:00:00Z",database:{status:"ready",schema_version:"001_foundation"},counts:{samples:0,variants:0,genes:0,drugs:0,pathways:0},datasets:[],limitations:[]};
test("empty database, navigation, export and theme",async({page})=>{
 await page.route("**/api/system",route=>route.fulfill({json:snapshot}));
 await page.goto("/");
 await expect(page.getByRole("status")).toContainText("Database connected");
 await expect(page.getByRole("heading",{name:"No datasets imported yet."})).toBeVisible();
 await page.getByRole("button",{name:"Explore data sources"}).click();
 await expect(page.getByRole("heading",{name:"Imported datasets"})).toBeVisible();
 await page.getByRole("button",{name:"Architecture",exact:true}).click();
 await expect(page.getByRole("heading",{name:"Computation comes first."})).toBeVisible();
 await page.getByRole("button",{name:"Workspace",exact:true}).click();
 const download=page.waitForEvent("download");
 await page.getByRole("button",{name:"Export system snapshot"}).click();
 expect((await download).suggestedFilename()).toBe("pharmagenome-system-snapshot.json");
 await page.getByRole("button",{name:"Switch to dark mode"}).click();
 await expect(page.locator("html")).toHaveAttribute("data-theme","dark");
 await page.reload();
 await expect(page.locator("html")).toHaveAttribute("data-theme","dark");
});
test("API error remains unavailable and can recover",async({page})=>{
 await page.route("**/api/system",route=>route.fulfill({status:503,json:{detail:"API unavailable"}}));
 await page.goto("/");
 await expect(page.getByRole("status")).toContainText("API unavailable");
 await expect(page.getByRole("button",{name:"Export system snapshot"})).toBeDisabled();
 await expect(page.getByRole("heading",{name:"Collection unavailable."})).toBeVisible();
 await expect(page.getByRole("heading",{name:"No datasets imported yet."})).toHaveCount(0);
 await page.getByRole("button",{name:"Data sources",exact:true}).click();
 await expect(page.getByText("Imported dataset inventory unavailable.")).toBeVisible();
 await expect(page.getByText(/Unknown registered versions/)).toBeVisible();
 await page.unroute("**/api/system");
 await page.route("**/api/system",route=>route.fulfill({json:snapshot}));
 await page.getByRole("button",{name:"Refresh connection"}).click();
 await expect(page.getByRole("status")).toContainText("Database connected");
});
for(const width of [1440,390]){
 test("responsive evidence "+width,async({page},testInfo)=>{
  await page.setViewportSize({width,height:1000});
  await page.route("**/api/system",route=>route.fulfill({json:snapshot}));
  await page.goto("/");
  await expect(page.getByRole("status")).toContainText("Database connected");
  expect(await page.evaluate(()=>document.documentElement.scrollWidth<=window.innerWidth)).toBe(true);
  await page.screenshot({path:testInfo.outputPath("workspace-"+width+".png"),fullPage:true});
  if(width===390){
   await page.getByRole("button",{name:"Open navigation"}).click();
   await page.getByRole("button",{name:"Data sources",exact:true}).click();
   await expect(page.getByRole("heading",{name:"Imported datasets"})).toBeVisible();
  }
 });
}

test("mobile drawer handles keyboard focus and Escape",async({page})=>{
 await page.setViewportSize({width:390,height:844});
 await page.route("**/api/system",route=>route.fulfill({json:snapshot}));
 await page.goto("/");
 await expect(page.locator("#research-navigation")).toHaveAttribute("inert","");
 const trigger=page.getByRole("button",{name:"Open navigation"});
 await trigger.click();
 await expect(page.getByRole("dialog")).toBeVisible();
 await expect(page.locator(".mobile-menu")).toHaveAttribute("aria-expanded","true");
 await page.keyboard.press("Shift+Tab");
 await expect(page.getByRole("link",{name:"Source code",exact:true})).toBeFocused();
 await page.keyboard.press("Tab");
 await expect(page.locator("#research-navigation .brand")).toBeFocused();
 await page.keyboard.press("Escape");
 await expect(page.locator("#research-navigation")).toHaveAttribute("inert","");
 await expect(page.getByRole("button",{name:"Open navigation"})).toBeFocused();
});

const dataset={id:1,name:"Synthetic LUAD test subset",source:"Synthetic cBioPortal-shaped fixture",version:"a".repeat(64),sha256:"a".repeat(64),retrieved_at:"2026-09-08T07:40:20Z",is_fixture:true,url:"https://www.cbioportal.org/",license:"Synthetic test data",downloaded:966,valid:839,invalid:0,duplicates:0,excluded:127,manifest:{assembly:"GRCh37",limitations:["Ten selected genes only; not an exome-wide mutation catalogue.","Profile membership does not establish per-base callability or confirm a wild-type genotype."],snapshot_git_revision:"a".repeat(40)},report:{samples:566,genes:10,unique_variants:506,missing_vaf:0,coverage:"10 selected genes; SNVs only; full mutation-profile cohort",method:"Synthetic import test",exclusion_reasons:{non_SNV:127},validation_reasons:{}}};
for(const width of [1440,390]){
 test("populated provenance and report download "+width,async({page},testInfo)=>{
  await page.setViewportSize({width,height:1000});
  await page.route("**/api/system",route=>route.fulfill({json:{...snapshot,version:"0.2.0",phase:2,counts:{samples:566,variants:506,genes:10,drugs:0,pathways:0},datasets:[dataset]}}));
  await page.route("**/api/datasets/1/report",route=>route.fulfill({json:{dataset,report:dataset.report}}));
  await page.goto("/");
  await expect(page.getByRole("heading",{name:dataset.name,exact:true})).toBeVisible();
  await expect(page.getByText("Development fixture",{exact:true})).toBeVisible();
  await expect(page.locator(".cohort-facts")).toContainText("839");
  await expect(page.locator(".cohort-facts")).toContainText("506");
  await expect(page.getByText("Not measured",{exact:true})).toHaveCount(0);
  expect(await page.evaluate(()=>document.documentElement.scrollWidth<=window.innerWidth)).toBe(true);
  await page.screenshot({path:testInfo.outputPath("populated-"+width+".png"),fullPage:true});
  await page.getByRole("button",{name:"Inspect import & provenance"}).click();
  await expect(page.getByRole("heading",{name:"Import quality & provenance"})).toBeVisible();
  await expect(page.locator(".report-counts")).toContainText("Excluded127");
  await expect(page.locator(".report-counts")).toContainText("Invalid0");
  await expect(page.getByText("Imported subset",{exact:true})).toBeVisible();
  expect(await page.evaluate(()=>document.documentElement.scrollWidth<=window.innerWidth)).toBe(true);
  await page.screenshot({path:testInfo.outputPath("provenance-"+width+".png"),fullPage:true});
  const download=page.waitForEvent("download");
  await page.getByRole("button",{name:"Download quality report"}).click();
  expect((await download).suggestedFilename()).toBe("pharmagenome-dataset-1-report.json");
  await page.unroute("**/api/datasets/1/report");
  await page.route("**/api/datasets/1/report",route=>route.fulfill({status:503,json:{detail:"Unavailable"}}));
  await page.getByRole("button",{name:"Download quality report"}).click();
  await expect(page.locator(".report-error")).toHaveText("Report unavailable. Please try again.");
  await expect(page.getByRole("button",{name:"Download quality report"})).toBeEnabled();
  await page.getByRole("button",{name:"Switch to dark mode"}).click();
  await page.screenshot({path:testInfo.outputPath("provenance-dark-"+width+".png"),fullPage:true});
 });
}
