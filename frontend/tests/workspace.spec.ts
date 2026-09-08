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
