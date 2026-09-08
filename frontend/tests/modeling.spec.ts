import {test,expect,type Page} from "@playwright/test";
import {readFile} from "node:fs/promises";

const dataset={id:3,name:"CellMiner NCI-60 · ten-gene / ten-drug modeling panel",version:"cellminer-2025.3-curated-v1",sha256:"c".repeat(64),retrieved_at:"2026-09-08T00:00:00Z",source:"NCI CellMiner",url:"https://discover.nci.nih.gov/cellminer/",manifest:{activity_metric:"CellMiner compound activity average z score; higher means greater sensitivity",database_version:"2.15",selection:"Predeclared panel"}};
const drugs=[{id:"NSC:718781",name:"Erlotinib",mechanism:"PK:YK,EGFR",status:"FDA approved"},{id:"NSC:119875",name:"Cisplatin",mechanism:"A7|AlkAg",status:"FDA approved"}];
const features=["expression_BRAF","expression_EGFR","expression_KRAS","expression_MET","expression_NF1","expression_PIK3CA","expression_RB1","expression_STK11","expression_TP53","expression_KEAP1","mutation_count"];
const options={dataset,datasets:[dataset],drugs,features,algorithms:[{id:"logistic",name:"Regularized logistic regression"},{id:"random_forest",name:"Random forest"},{id:"gradient_boosting",name:"Histogram gradient boosting"}],mutation_groups:[{gene:"TP53",mutated:30,wild_type:30},{gene:"KRAS",mutated:11,wild_type:49}],protocol:{cross_validation:"5 folds × 3 repeats, stratified, seed 20260908",target:"Activity z score above the independently pinned zero threshold",positive_class:"more sensitive",pipeline:"Median imputation and scaling fit inside each training fold"}};
const comparison={dataset,drug:drugs[0],gene:"TP53",metric:"CellMiner compound activity average z score",direction:"Higher means greater sensitivity",groups:[{label:"mutation present",n:30,median:.21,q1:-.4,q3:.7},{label:"no called mutation",n:29,median:-.13,q1:-.7,q3:.4}],test:{method:"two-sided Mann–Whitney U, asymptotic tie correction",statistic:510,p_value:.27,effect:.17},points:Array.from({length:59},(_,i)=>({cell_line:"LINE:"+i,tissue:"LC",value:(i-29)/20,group:i<30?"mutation present":"no called mutation"})),limitations:["Synthetic browser fixture; no biological inference.","No-called-mutation does not prove wild type."]};
const metric={mean:.72,standard_deviation:.08};
const model={dataset,drug:drugs[0],method:"Regularized logistic regression",algorithm:"logistic",features,n:59,threshold:0,class_counts:{more_sensitive:29,less_sensitive_or_equal:30},metrics:{accuracy:metric,balanced_accuracy:metric,precision:metric,recall:metric,f1:metric,roc_auc:{mean:.78,standard_deviation:.07}},baseline_metrics:{accuracy:{mean:.51,standard_deviation:.02},balanced_accuracy:{mean:.5,standard_deviation:0},precision:{mean:.2,standard_deviation:.1},recall:{mean:.2,standard_deviation:.1},f1:{mean:.2,standard_deviation:.1},roc_auc:{mean:.5,standard_deviation:0}},confusion_matrix:[[70,20],[25,62]],roc_curve:[{false_positive_rate:0,true_positive_rate:0},{false_positive_rate:.2,true_positive_rate:.65},{false_positive_rate:1,true_positive_rate:1}],importance:features.map((feature,i)=>({feature,mean_decrease_roc_auc:.12-i*.012,direction:"magnitude only"})),predictions:Array.from({length:177},(_,i)=>({cell_line:"LINE:"+(i%59),repeat:Math.floor(i/59)+1,fold:i%5+1,actual:i%2,predicted:i%2,probability:.7})),parameters:{cross_validation:{folds:5,repeats:3}},software:{scikit_learn:"1.9.0",numpy:"2.3.3",scipy:"1.18.0"},computed_at:"2026-09-08T16:00:00Z",code_revision:"synthetic-browser-fixture",input_sha256:"d".repeat(64),interpretation:"Repeated cross-validation estimates discrimination inside this small cell-line panel; it is not external validation.",limitations:["Synthetic browser fixture; not biological evidence.","Performance must not guide treatment."]};
async function setup(page:Page,width=1440){
 await page.setViewportSize({width,height:1000});await page.emulateMedia({reducedMotion:"reduce"});
 await page.route("**/api/system",route=>route.fulfill({json:{version:"0.7.0",phase:7,checked_at:"2026-09-08T16:00:00Z",database:{status:"ready",schema_version:"005_drug_response_modeling"},counts:{samples:626,variants:506,genes:10,drugs:193,pathways:220},datasets:[],limitations:[]}}));
 await page.route("**/api/modeling/options",route=>route.fulfill({json:options}));
 await page.route("**/api/modeling/response*",route=>route.fulfill({json:comparison}));
 await page.route("**/api/modeling/evaluate",route=>route.fulfill({json:model}));
 await page.goto("/");await expect(page.getByRole("status")).toContainText("Database connected");
 if(width<=650)await page.getByRole("button",{name:"Open navigation"}).click();
 await page.getByRole("button",{name:"Drug response",exact:true}).click();
 await expect(page.getByRole("heading",{name:dataset.name})).toBeVisible();
}
for(const width of [1440,390]){
 test("response and model evidence remain usable "+width,async({page},info)=>{
  await setup(page,width);
  await expect(page.getByRole("heading",{name:"Erlotinib response by TP53 call"})).toBeVisible();
  await expect(page.getByText("0.27",{exact:true})).toBeVisible();
  expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);
  await page.screenshot({path:info.outputPath("modeling-response-"+width+".png"),fullPage:true});
  const request=page.waitForRequest("**/api/modeling/evaluate");
  await page.getByRole("button",{name:"Run repeated cross-validation"}).click();
  const payload=(await request).postDataJSON();expect(payload.drug_id).toBe("NSC:718781");expect(payload.features).toHaveLength(11);
  await expect(page.getByRole("heading",{name:"Evaluation ledger"})).toBeFocused();
  await expect(page.getByText("0.78",{exact:true})).toBeVisible();
  await expect(page.getByLabel("Confusion matrix")).toContainText("70");
  const event=page.waitForEvent("download");await page.getByRole("button",{name:"Export complete JSON"}).click();
  const exported=JSON.parse(await readFile((await (await event).path())!,"utf8"));expect(exported.predictions).toHaveLength(177);expect(exported.input_sha256).toBe(model.input_sha256);
  expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);
  await page.screenshot({path:info.outputPath("modeling-evaluation-"+width+".png"),fullPage:true});
 });
}
test("feature guard, reset and service error are recoverable",async({page})=>{
 await setup(page);
 for(const feature of features.slice(0,10)){const name=feature.replace("expression_","").replace("_"," ");await page.locator(".modeling-features label").filter({hasText:name}).getByRole("checkbox").uncheck();}
 await expect(page.getByRole("button",{name:"Run repeated cross-validation"})).toBeDisabled();
 await page.locator(".modeling-features label").filter({hasText:"BRAF"}).getByRole("checkbox").check();
 await expect(page.getByRole("button",{name:"Run repeated cross-validation"})).toBeEnabled();
 await page.unroute("**/api/modeling/evaluate");await page.route("**/api/modeling/evaluate",route=>route.fulfill({status:422,json:{detail:"At least 30 response measurements are required."}}));
 await page.getByRole("button",{name:"Run repeated cross-validation"}).click();
 await expect(page.locator(".modeling-inline-error")).toContainText("At least 30");
 await expect(page.getByRole("button",{name:"Run repeated cross-validation"})).toBeEnabled();
});
