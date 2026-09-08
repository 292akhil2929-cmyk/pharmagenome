"use client";
import {useEffect,useRef,useState} from "react";
import {Activity,BrainCircuit,Database,Download,FlaskConical,LoaderCircle,Play,RefreshCw,ShieldCheck} from "lucide-react";
import {Bar,BarChart,CartesianGrid,Cell,ComposedChart,Line,ReferenceLine,ResponsiveContainer,Scatter,Tooltip,XAxis,YAxis} from "recharts";
import {Button} from "@/components/ui/button";
import {ResearchExplanation} from "@/components/research-explanation";

type Dataset={id:number;name:string;version:string;sha256:string;retrieved_at:string;source:string;url:string;manifest:{activity_metric:string;database_version:string;selection:string}};
type Drug={id:string;name:string;mechanism:string;status:string};
type Options={dataset:Dataset;datasets:Dataset[];drugs:Drug[];features:string[];algorithms:{id:string;name:string}[];mutation_groups:{gene:string;mutated:number;wild_type:number}[];protocol:{cross_validation:string;target:string;positive_class:string;pipeline:string}};
type ResponseResult={dataset:Dataset;drug:Drug;gene:string;metric:string;direction:string;groups:{label:string;n:number;median:number;q1:number;q3:number}[];test:{method:string;statistic:number;p_value:number;effect:number};points:{cell_line:string;tissue:string;value:number;group:string}[];limitations:string[]};
type Metric={mean:number;standard_deviation:number};
type ModelResult={dataset:Dataset;drug:Drug;method:string;algorithm:string;features:string[];n:number;threshold:number;class_counts:{more_sensitive:number;less_sensitive_or_equal:number};metrics:Record<string,Metric>;baseline_metrics:Record<string,Metric>;confusion_matrix:number[][];roc_curve:{false_positive_rate:number;true_positive_rate:number}[];importance:{feature:string;mean_decrease_roc_auc:number;direction:string}[];predictions:unknown[];parameters:Record<string,unknown>;software:Record<string,string>;computed_at:string;code_revision:string;input_sha256:string;interpretation:string;limitations:string[]};

const nice=(value:number)=>Math.abs(value)<.001?value.toExponential(2):value.toLocaleString(undefined,{maximumFractionDigits:3});
async function json<T>(url:string,init?:RequestInit):Promise<T>{const response=await fetch(url,{cache:"no-store",...init});const body=await response.json();if(!response.ok)throw new Error(body.detail||"Request failed.");return body;}
function modelEvidence(model:ModelResult){
 return {dataset:{name:model.dataset.name,version:model.dataset.version,sha256:model.dataset.sha256,retrieved_at:model.dataset.retrieved_at,source:model.dataset.source},drug:model.drug,method:model.method,algorithm:model.algorithm,features:model.features,n:model.n,target_threshold:model.threshold,class_counts:model.class_counts,metrics:model.metrics,baseline_metrics:model.baseline_metrics,confusion_matrix:model.confusion_matrix,importance:model.importance.slice(0,8),parameters:model.parameters,software:model.software,computed_at:model.computed_at,code_revision:model.code_revision,input_sha256:model.input_sha256,interpretation:model.interpretation,limitations:model.limitations};
}
function download(name:string,data:unknown){const url=URL.createObjectURL(new Blob([JSON.stringify(data,null,2)],{type:"application/json"}));const a=document.createElement("a");a.href=url;a.download=name;a.click();URL.revokeObjectURL(url);}

export function Modeling(){
 const [options,setOptions]=useState<Options|null>(null),[drug,setDrug]=useState(""),[gene,setGene]=useState("TP53");
 const [algorithm,setAlgorithm]=useState("logistic"),[features,setFeatures]=useState<string[]>([]);
 const [response,setResponse]=useState<ResponseResult|null>(null),[model,setModel]=useState<ModelResult|null>(null);
 const [error,setError]=useState<string|null>(null),[loading,setLoading]=useState(true),[running,setRunning]=useState(false);
 const resultHeading=useRef<HTMLHeadingElement>(null);
 async function load(){
  setLoading(true);setError(null);
  try{const value=await json<Options>("/api/modeling/options");setOptions(value);
   const selected=value.drugs.find(d=>d.name.toLowerCase()==="erlotinib")?.id||value.drugs[0]?.id||"";
   setDrug(selected);setFeatures(value.features);}
  catch(e){setError(e instanceof Error?e.message:"Modeling source unavailable.");}
  finally{setLoading(false);}
 }
 useEffect(()=>{void load();},[]);
 useEffect(()=>{if(model)resultHeading.current?.focus();},[model]);
 useEffect(()=>{if(!options||!drug)return;setResponse(null);setModel(null);setError(null);
  void json<ResponseResult>("/api/modeling/response?drug_id="+encodeURIComponent(drug)+"&gene="+gene)
   .then(setResponse).catch(e=>setError(e instanceof Error?e.message:"Comparison failed."));},[options,drug,gene]);
 async function run(){
  if(!drug||features.length<2)return;setRunning(true);setError(null);setModel(null);
  try{const value=await json<ModelResult>("/api/modeling/evaluate",{method:"POST",headers:{"Content-Type":"application/json"},
    body:JSON.stringify({drug_id:drug,algorithm,features})});setModel(value);}
  catch(e){setError(e instanceof Error?e.message:"Evaluation failed.");}finally{setRunning(false);}
 }
 if(loading)return <section className="panel modeling-state" aria-live="polite"><LoaderCircle className="spin"/><h2>Loading the CellMiner panel</h2><p>Checking aligned cell lines, drugs and genomic features.</p></section>;
 if(!options)return <section className="panel modeling-state modeling-error"><BrainCircuit/><h2>Modeling source unavailable</h2><p>{error}</p><Button onClick={load}><RefreshCw size={15}/>Retry source connection</Button></section>;
 const selectedDrug=options.drugs.find(d=>d.id===drug);
 const points=response?.points.map((p,i)=>({...p,index:p.group==="mutation present"?0:1,jitter:(p.group==="mutation present"?0:1)+((i%7)-3)*.025}));
 const metrics=[["ROC AUC","roc_auc"],["Balanced accuracy","balanced_accuracy"],["Precision","precision"],["Recall","recall"],["F1","f1"]] as const;
 return <div className="modeling-workspace">
  <section className="modeling-manifest" aria-label="Modeling protocol">
   <div className="manifest-source"><Database size={19}/><div><strong>{options.dataset.source}</strong><a href={options.dataset.url} target="_blank" rel="noreferrer">{options.dataset.version}</a></div></div>
   <h2>{options.dataset.name}</h2>
   <p>{options.dataset.manifest.activity_metric}</p>
   <dl><div><dt>Panel</dt><dd>60 cancer cell lines</dd></div><div><dt>Scope</dt><dd>10 genes · 10 FDA-status drugs</dd></div><div><dt>Validation</dt><dd>{options.protocol.cross_validation}</dd></div><div><dt>Positive class</dt><dd>{options.protocol.positive_class}</dd></div></dl>
   <code title={options.dataset.sha256}>retrieved {options.dataset.retrieved_at.slice(0,10)} · sha256 {options.dataset.sha256.slice(0,16)}…</code>
  </section>

  <section className="panel modeling-controls">
   <div className="section-title"><div><h2>Set the experimental question</h2><p>Choose one drug response and one mutation split. Higher activity z scores mean greater sensitivity.</p></div><FlaskConical size={21}/></div>
   <div className="modeling-selectors"><label>Drug<select aria-label="Modeling drug" value={drug} onChange={e=>setDrug(e.target.value)}>{options.drugs.map(d=><option key={d.id} value={d.id}>{d.name} · {d.id}</option>)}</select></label><label>Mutation group<select aria-label="Response mutation gene" value={gene} onChange={e=>setGene(e.target.value)}>{options.mutation_groups.map(g=><option key={g.gene} value={g.gene}>{g.gene} · {g.mutated} called</option>)}</select></label><label>Model<select aria-label="Model algorithm" value={algorithm} onChange={e=>{setAlgorithm(e.target.value);setModel(null);}}>{options.algorithms.map(a=><option key={a.id} value={a.id}>{a.name}</option>)}</select></label></div>
   {selectedDrug&&<div className="drug-record"><Activity size={18}/><div><strong>{selectedDrug.name}</strong><span>{selectedDrug.mechanism} · {selectedDrug.status}</span></div></div>}
   <fieldset className="modeling-features"><legend>Predictor panel{" "}<span>{features.length} selected</span></legend>{options.features.map(feature=><label key={feature}><input type="checkbox" checked={features.includes(feature)} onChange={e=>{setModel(null);setFeatures(current=>e.target.checked?[...current,feature]:current.filter(x=>x!==feature));}}/><span>{feature.replace("expression_","").replace("_"," ")}</span><small>{feature.startsWith("expression")?"RNA z score":"called variants"}</small></label>)}</fieldset>
   <div className="modeling-run"><Button onClick={run} disabled={running||features.length<2}>{running?<LoaderCircle className="spin" size={16}/>:<Play size={16}/>}Run repeated cross-validation</Button><p>{features.length<2?"Select at least two predictors.":options.protocol.pipeline+"."}</p></div>
   {error&&<div className="modeling-inline-error" role="alert"><strong>Analysis stopped</strong><span>{error}</span></div>}
  </section>

  {response&&<section className="panel response-lens" aria-label="Drug response comparison">
   <div className="section-title"><div><h2>{response.drug.name} response by {response.gene} call</h2><p>{response.test.method}. This is one unadjusted exploratory comparison.</p></div><Activity size={21}/></div>
   <div className="response-layout"><div className="response-chart" aria-label="Cell-line response distribution chart"><ResponsiveContainer width="100%" height="100%"><ComposedChart data={points} margin={{top:20,right:20,bottom:36,left:5}}><CartesianGrid strokeDasharray="2 5" vertical={false}/><XAxis type="number" dataKey="jitter" domain={[-.3,1.3]} ticks={[0,1]} tickFormatter={v=>v===0?"Mutation present":"No called mutation"}/><YAxis dataKey="value" name="Activity z score"/><Tooltip formatter={(v)=>[nice(Number(v)),"Activity z score"]} labelFormatter={(_,payload)=>payload?.[0]?.payload.cell_line||""}/><ReferenceLine y={0} strokeDasharray="4 4"/><Scatter dataKey="value" fill="var(--accent)">{points?.map((p,i)=><Cell key={p.cell_line} fill={p.group==="mutation present"?"var(--accent)":"var(--chart-two)"} opacity={.78}/>)}</Scatter></ComposedChart></ResponsiveContainer></div>
    <div className="response-ledger">{response.groups.map(g=><div key={g.label}><span>{g.label}</span><strong>{nice(g.median)}</strong><small>median · n={g.n}<br/>IQR {nice(g.q1)} to {nice(g.q3)}</small></div>)}<div className="test-reading"><span>Unadjusted p</span><strong>{nice(response.test.p_value)}</strong><small>rank-biserial effect {nice(response.test.effect)}</small></div></div></div>
   <details><summary>Interpretation boundary</summary><ul>{response.limitations.map(x=><li key={x}>{x}</li>)}</ul></details>
  </section>}

  {model&&<section className="modeling-results" aria-label="Model evaluation results">
   <div className="model-result-heading"><div><h2 id="modeling-analysis-result" ref={resultHeading} tabIndex={-1}>Evaluation ledger</h2><p>{model.method} · {model.n} measured cell lines · positive above z={nice(model.threshold)}</p></div><Button variant="outline" onClick={()=>download("pharmagenome-model-evaluation.json",model)}><Download size={15}/>Export complete JSON</Button></div>
   <section className="metric-ledger">{metrics.map(([label,key])=><div key={key}><span>{label}</span><strong>{nice(model.metrics[key].mean)}</strong><small>± {nice(model.metrics[key].standard_deviation)} across folds<br/>prior baseline {nice(model.baseline_metrics[key].mean)}</small></div>)}</section>
   <div className="model-evidence-grid">
    <section className="panel"><h3>Held-out ROC curve</h3><p>Pooled predictions from all 15 test folds; each cell line appears once per repeat.</p><div className="roc-chart"><ResponsiveContainer width="100%" height="100%"><ComposedChart data={model.roc_curve}><CartesianGrid strokeDasharray="2 5"/><XAxis dataKey="false_positive_rate" domain={[0,1]} type="number"/><YAxis domain={[0,1]}/><Tooltip/><Line dataKey="true_positive_rate" stroke="var(--accent)" dot={false} strokeWidth={2}/><ReferenceLine segment={[{x:0,y:0},{x:1,y:1}]} strokeDasharray="4 4"/></ComposedChart></ResponsiveContainer></div></section>
    <section className="panel confusion-panel"><h3>Pooled confusion matrix</h3><p>Rows are actual class; columns are predicted at probability 0.5.</p><div className="confusion-grid" aria-label="Confusion matrix"><span/><b>Predicted lower</b><b>Predicted sensitive</b><b>Actual lower</b><strong>{model.confusion_matrix[0][0]}</strong><strong>{model.confusion_matrix[0][1]}</strong><b>Actual sensitive</b><strong>{model.confusion_matrix[1][0]}</strong><strong>{model.confusion_matrix[1][1]}</strong></div></section>
   </div>
   <section className="panel importance-panel"><h3>What changed held-out discrimination?</h3><p>Mean ROC-AUC decrease after permuting one feature inside each test fold. Negative values can occur through sampling noise.</p><div className="importance-chart"><ResponsiveContainer width="100%" height="100%"><BarChart data={model.importance.slice(0,8)} layout="vertical" margin={{left:24,right:30}}><CartesianGrid strokeDasharray="2 5" horizontal={false}/><XAxis type="number"/><YAxis dataKey="feature" type="category" width={112} tickFormatter={v=>String(v).replace("expression_","")}/><Tooltip formatter={v=>nice(Number(v))}/><Bar dataKey="mean_decrease_roc_auc" fill="var(--accent)" radius={[0,3,3,0]}/></BarChart></ResponsiveContainer></div></section>
   <ResearchExplanation key={model.input_sha256} analysisType="drug_response_model" evidence={modelEvidence(model)} underlyingId="modeling-analysis-result"/>
   <section className="panel model-boundary"><ShieldCheck size={20}/><div><h3>Read this as internal panel performance</h3><p>{model.interpretation}</p><ul>{model.limitations.map(x=><li key={x}>{x}</li>)}</ul><code>input {model.input_sha256.slice(0,16)}… · revision {model.code_revision.slice(0,12)}</code></div></section>
  </section>}
 </div>;
}
