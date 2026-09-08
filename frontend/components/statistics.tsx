"use client";
import {useEffect,useRef,useState} from "react";
import {ArrowLeft,ArrowRight,Download,Play,RefreshCw} from "lucide-react";
import {CartesianGrid,Line,LineChart,ResponsiveContainer,Scatter,ScatterChart,Tooltip,XAxis,YAxis} from "recharts";
import {Button} from "@/components/ui/button";
import {Textarea} from "@/components/ui/textarea";
import {Table,TableHeader,TableBody,TableRow,TableHead,TableCell} from "@/components/ui/table";

type Tab="measurements"|"contingency"|"enrichment";
type Method="welch"|"mann_whitney"|"pearson"|"spearman"|"anova"|"kruskal";
type Dataset={id:number;name:string;sha256:string;retrieved_at:string;is_fixture:boolean};
type Options={dataset:Dataset;datasets:Dataset[];genes:{id:number;symbol:string}[];pathway_count:number};
type Description={n:number;mean:number;median:number;variance:number;standard_deviation:number;q1:number;q3:number;minimum:number;maximum:number;distribution?:{value:number;count:number;cumulative_fraction:number}[]};
type Pathway={id:string;name:string;overlap:number;pathway_genes_in_universe:number;genes:string[];expected_overlap:number;fold_enrichment:number;p_value:number;q_bh:number;q_by:number;url:string};
type Result={method:string;method_version:string;computed_at:string;code_revision:string;software:{scipy:string;numpy:string};parameters:{universe?:string[];selected_genes?:string[]};inputs?:{groups?:number[][];unit?:string;table?:number[][]};input_sha256?:string;statistic?:number|null;p_value?:number;effect?:{label:string;value:number|null;boundary?:string|null};confidence_interval?:{label:string;low:number|null;high:number|null}|null;descriptive?:Description[];null_hypothesis:string;alternative_hypothesis:string;assumptions:string[];limitations:string[];interpretation:string;details?:{expected_counts?:number[][];degrees_of_freedom?:number|number[];p_value_method?:string;resamples?:number;seed?:number};dataset?:Dataset;rows?:Pathway[];tested_pathways?:number;rejected_by?:number;rejected_bh?:number};
const methods:Record<Method,{name:string;help:string}>={
 welch:{name:"Welch t-test",help:"Two independent groups · compares population means, allowing unequal variances."},
 mann_whitney:{name:"Mann–Whitney U",help:"Two independent groups · rank-based comparison; a median interpretation requires comparable shapes."},
 pearson:{name:"Pearson correlation",help:"Two paired vectors · position 1 pairs with position 1. Measures linear association."},
 spearman:{name:"Spearman correlation",help:"Two paired vectors · average ranks for ties; a seeded pairing-permutation p-value."},
 anova:{name:"One-way ANOVA",help:"Three to six independent groups · omnibus mean comparison; assumes equal variances and normal residuals."},
 kruskal:{name:"Kruskal–Wallis",help:"Three to six independent groups · at least five values per group; an omnibus rank-based comparison."}
};
const tabs:Tab[]=["measurements","contingency","enrichment"];
const tabLabels=["Measurements","2 × 2 counts","Pathway enrichment"];
const num=(n:number|null|undefined)=>n==null?"Not estimable":Math.abs(n)>0&&(Math.abs(n)<0.0001||Math.abs(n)>=1e7)?n.toExponential(4):new Intl.NumberFormat("en",{maximumSignificantDigits:6}).format(n);
const pval=(n:number)=>n===0?"< machine precision":num(n);
function parseGroups(text:string){
 const lines=text.trim().split(/\r?\n/);
 if(lines.length<2||lines.length>6)throw new Error("Enter two to six groups, one group per line.");
 return lines.map((line,i)=>{
  if(!line.trim()||/(^|,)\s*(,|$)/.test(line))throw new Error("Group "+String.fromCharCode(65+i)+" contains a missing value.");
  const parts=line.trim().split(/[\s,]+/);
  if(parts.length<2||parts.length>500)throw new Error("Each group needs 2–500 values.");
  return parts.map(value=>{if(!/^[+-]?(?:\d+\.?\d*|\.\d+)(?:e[+-]?\d+)?$/i.test(value)||!Number.isFinite(Number(value))||Math.abs(Number(value))>1e12)throw new Error("Use finite numbers between −10¹² and 10¹². Missing values and text are not accepted.");return Number(value);});
 });
}
function save(result:Result){const url=URL.createObjectURL(new Blob([JSON.stringify({kind:"statistical_analysis",...result},null,2)],{type:"application/json"}));const a=document.createElement("a");a.href=url;a.download="pharmagenome-statistics.json";a.click();URL.revokeObjectURL(url);}

export function Statistics(){
 const [tab,setTab]=useState<Tab>("measurements"),[method,setMethod]=useState<Method>("welch");
 const [values,setValues]=useState(""),[unit,setUnit]=useState(""),[countMethod,setCountMethod]=useState("fisher"),[cells,setCells]=useState(["","","",""]);
 const [options,setOptions]=useState<Options|null>(null),[optionError,setOptionError]=useState(""),[loadingOptions,setLoadingOptions]=useState(false);
 const [genes,setGenes]=useState<string[]>([]),[dataset,setDataset]=useState("");
 const [result,setResult]=useState<Result|null>(null),[error,setError]=useState(""),[busy,setBusy]=useState(false),[example,setExample]=useState(false),[page,setPage]=useState(1);
 const resultHeading=useRef<HTMLHeadingElement>(null);
 useEffect(()=>{if(result){resultHeading.current?.focus({preventScroll:true});resultHeading.current?.scrollIntoView({block:"start",behavior:"instant"});}},[result]);
 function clear(){setResult(null);setError("");setPage(1);}
 function switchTab(next:Tab){setTab(next);clear();setExample(false);}
 async function getOptions(id?:string){
  setLoadingOptions(true);setOptionError("");
  try{const r=await fetch("/api/statistics/options"+(id?"?dataset_id="+encodeURIComponent(id):""),{cache:"no-store"});const body=await r.json();if(!r.ok)throw new Error(body.detail||"Research source unavailable.");setOptions(body);setDataset(String(body.dataset.id));setGenes([]);}
  catch(e){setOptionError(e instanceof Error?e.message:"Research source unavailable.");}finally{setLoadingOptions(false);}
 }
 useEffect(()=>{if(tab==="enrichment"&&!options&&!loadingOptions&&!optionError)void getOptions();},[tab,options,loadingOptions,optionError]);
 function teaching(){
  clear();setExample(true);
  if(tab==="measurements"){setUnit("synthetic units");setValues(method==="anova"||method==="kruskal"?"1, 3, 5, 7, 9\n2, 4, 6, 8, 10\n11, 12, 13, 14, 15":method==="pearson"||method==="spearman"?"1, 2, 3, 4, 5\n2, 4, 3, 7, 6":"1, 2, 3, 4, 5\n4, 5, 6, 7, 8");}
  else setCells(["6","2","1","4"]);
 }
 async function run(e:React.FormEvent){
  e.preventDefault();clear();
  let payload:unknown;
  try{
   if(tab==="measurements")payload={method,groups:parseGroups(values),unit:unit.trim()||"unspecified units"};
   else if(tab==="contingency"){if(cells.some(c=>!/^\d+$/.test(c)||Number(c)>1000000))throw new Error("Enter four whole-number counts from 0 to 1,000,000.");payload={method:countMethod,table:[cells.slice(0,2).map(Number),cells.slice(2).map(Number)]};}
   else payload={genes,dataset_id:Number(dataset)};
  }catch(e){setError(e instanceof Error?e.message:"Check the inputs.");return;}
  setBusy(true);
  try{const r=await fetch("/api/statistics/"+tab,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(payload)});const body=await r.json();if(!r.ok)throw new Error(typeof body.detail==="string"?body.detail:"Check the inputs and sample sizes.");setResult(body);}
  catch(e){setError(e instanceof Error?e.message:"Computation is unavailable. Try again.");}finally{setBusy(false);}
 }
 const paired=method==="pearson"||method==="spearman";
 const pairedResult=result?.inputs?.groups&&(result.method==="pearson"||result.method==="spearman")?result.inputs.groups[0].map((x,i)=>({x,y:result.inputs!.groups![1][i]})):null;
 const disabled=busy||(tab==="measurements"?!values.trim():tab==="contingency"?cells.some(c=>!c):!genes.length||!dataset||loadingOptions);
 return <div className="statistics-workspace">
 <section className="panel statistics-input">
 <div className="section-title"><div><h2>Statistical workbench</h2><p>State a question. Inspect the assumptions. Keep the full result.</p></div></div>
 <div className="sequence-tabs" role="tablist" aria-label="Statistical analyses">{tabs.map((t,i)=><button type="button" role="tab" id={"statistics-tab-"+t} aria-controls="statistics-editor" aria-selected={tab===t} tabIndex={tab===t?0:-1} disabled={busy} key={t} onClick={()=>switchTab(t)} onKeyDown={e=>{const index=e.key==="ArrowRight"?(i+1)%3:e.key==="ArrowLeft"?(i+2)%3:e.key==="Home"?0:e.key==="End"?2:-1;if(index>=0){e.preventDefault();switchTab(tabs[index]);document.getElementById("statistics-tab-"+tabs[index])?.focus();}}}>{tabLabels[i]}</button>)}</div>
 <form id="statistics-editor" role="tabpanel" aria-labelledby={"statistics-tab-"+tab} onSubmit={run}>
 {tab==="measurements"?<>
 <div className="statistics-fields"><label htmlFor="stat-method">Statistical method<select id="stat-method" value={method} disabled={busy} onChange={e=>{setMethod(e.target.value as Method);clear();setExample(false);}}>{Object.entries(methods).map(([key,m])=><option key={key} value={key}>{m.name}</option>)}</select></label><label htmlFor="stat-unit">Units / measurement context<input id="stat-unit" value={unit} maxLength={60} placeholder="e.g. normalized expression" disabled={busy} onChange={e=>{setUnit(e.target.value);clear();setExample(false);}}/></label></div>
 <p id="stat-method-help" className="body-copy">{methods[method].help}</p>
 <label className="stat-values-label" htmlFor="stat-values">{paired?"Paired vectors A and B":"Groups A, B"+(method==="anova"||method==="kruskal"?", C…":"")}</label>
 <Textarea id="stat-values" aria-describedby="stat-method-help stat-input-help" value={values} disabled={busy} maxLength={70000} placeholder={paired?"Vector A on line 1; vector B on line 2":"One group per line; numbers separated by commas or spaces"} onChange={e=>{setValues(e.target.value);clear();setExample(false);}} spellCheck={false}/>
 <p id="stat-input-help" className="sequence-help">2–500 finite values per group. One group per line; separate values with commas or spaces. No headers or missing values. {paired?"Pairs must refer to the same observations and have equal lengths (at least 3).":"Use independent observations, not technical replicates as independent samples."}</p>
 </>:tab==="contingency"?<>
 <div className="statistics-fields"><label htmlFor="count-method">Count test<select id="count-method" value={countMethod} disabled={busy} onChange={e=>{setCountMethod(e.target.value);clear();}}><option value="fisher">Fisher exact · two-sided</option><option value="chi_square">Chi-square · no Yates correction</option></select></label></div>
 <p className="body-copy">Two disjoint groups and two mutually exclusive outcomes. Use independent observations and counts, not percentages. Chi-square requires every expected cell count to be at least five.</p>
 <div className="count-table"><table><caption>Observed 2 × 2 counts</caption><thead><tr><th scope="col">Group / outcome</th><th scope="col">Outcome 1</th><th scope="col">Outcome 2</th></tr></thead><tbody>{[0,1].map(row=><tr key={row}><th scope="row">Group {row===0?"A":"B"}</th>{[0,1].map(col=><td key={col}><input type="number" min="0" max="1000000" step="1" required aria-label={"Group "+(row===0?"A":"B")+", outcome "+(col+1)} value={cells[row*2+col]} disabled={busy} onChange={e=>{setCells(cells.map((c,i)=>i===row*2+col?e.target.value:c));clear();setExample(false);}}/></td>)}</tr>)}</tbody></table></div>
 </>:<>
 <p className="statistics-scope"><strong>Restricted ten-gene universe</strong>Over-representation is conditional on the selected source snapshot. This is not a genome-wide test. Choose genes before inspecting pathways; post-hoc selection is exploratory.</p>
 {loadingOptions&&<p role="status">Loading the research universe…</p>}
 {optionError&&<div role="alert" className="statistics-error"><p>{optionError}</p><Button type="button" variant="outline" onClick={()=>void getOptions()}>Retry source connection</Button></div>}
 {options&&<><div className="statistics-fields"><label htmlFor="enrichment-source">Research source snapshot<select id="enrichment-source" value={dataset} disabled={busy||loadingOptions} onChange={e=>{clear();void getOptions(e.target.value);}}>{options.datasets.map(d=><option key={d.id} value={d.id}>{d.name} · {d.sha256.slice(0,8)}</option>)}</select></label></div>
 <fieldset className="statistics-genes" disabled={busy||loadingOptions}><legend>Select genes · {genes.length} chosen</legend>{options.genes.map(g=><label key={g.id}><input type="checkbox" checked={genes.includes(g.symbol)} onChange={()=>{setGenes(genes.includes(g.symbol)?genes.filter(s=>s!==g.symbol):[...genes,g.symbol]);clear();}}/>{g.symbol}</label>)}</fieldset>
 <p className="sequence-help">The declared import covers {options.genes.length} genes. Every pathway in the chosen snapshot enters the correction family, including zero overlaps. BY controls false discovery rate under arbitrary dependence; BH is also reported.</p></>}
 </>}
 <div className="sequence-actions"><Button type="submit" disabled={disabled}>{busy?<RefreshCw className="spin" size={15}/>:<Play size={15}/>} {busy?"Computing…":tab==="enrichment"?"Test pathway enrichment":"Run statistical test"}</Button>{tab!=="enrichment"&&<Button type="button" variant="outline" disabled={busy} onClick={teaching}>Load synthetic example</Button>}<button type="button" className="text-action" disabled={busy} onClick={()=>{clear();setValues("");setCells(["","","",""]);setGenes([]);setUnit("");setExample(false);}}>Clear inputs</button></div>
 {example&&<p className="example-note">Synthetic teaching values · not observed biological measurements</p>}
 </form>
 <p className="sequence-privacy">{tab==="enrichment"?"Uses source-backed pathway membership from PostgreSQL; no LLM inference.":"Values are sent to the research API for computation. The application does not save them to its database. JSON exports contain the submitted measurements."}</p>
 </section>
 {busy&&<p role="status" className="sequence-pending">Computing the declared test and its assumptions…</p>}
 {error&&<section role="alert" className="panel statistics-error"><h2>Check the analysis request</h2><p>{error}</p><p>Edit the input or method, then run again.</p></section>}
 {result&&<>
 <div className="sequence-result-heading"><div><h2 ref={resultHeading} tabIndex={-1} className="stat-result-heading">Analysis result</h2><p>{result.method in methods?methods[result.method as Method].name:result.method==="fisher"?"Fisher exact":result.method==="chi_square"?"Chi-square":result.method} · method v{result.method_version}</p></div><Button variant="outline" onClick={()=>save(result)}><Download size={15}/>Export statistics JSON</Button></div>
 <p className="statistics-interpretation">{result.interpretation}</p>
 {result.rows?<><section className="inventory sequence-inventory" aria-label="Enrichment summary">{[["Universe",result.parameters.universe?.length+" genes"],["Selected",result.parameters.selected_genes?.length+" genes"],["Test family",result.tested_pathways+" pathways"],["BY q < 0.05",String(result.rejected_by)]].map(([label,value])=><div key={label}><span>{label}</span><strong>{value}</strong></div>)}</section>
 <section className="panel"><h2>Pathway tests · complete family</h2><p className="body-copy">Ranked by BY-adjusted q, then raw p. Overlap lists selected genes in each pathway; pathway size counts only genes in the declared universe. No pathways are removed before correction.</p>{result.rejected_by===0&&<p className="example-note">No pathway meets BY q &lt; 0.05. This does not demonstrate the absence of a biological relationship.</p>}
 <Table><TableHeader><TableRow>{["Pathway","Overlap / pathway size","Expected","Fold","Raw p","BH q","BY q · primary"].map(h=><TableHead key={h}>{h}</TableHead>)}</TableRow></TableHeader><TableBody>{result.rows.slice((page-1)*20,page*20).map(r=><TableRow key={r.id}><TableCell><a href={r.url} target="_blank" rel="noreferrer">{r.name}</a><small className="stat-pathway-id">{r.id} · {r.genes.join(", ")||"No selected genes"}</small></TableCell><TableCell>{r.overlap} / {r.pathway_genes_in_universe}</TableCell><TableCell>{num(r.expected_overlap)}</TableCell><TableCell>{num(r.fold_enrichment)}</TableCell><TableCell>{pval(r.p_value)}</TableCell><TableCell>{pval(r.q_bh)}</TableCell><TableCell>{pval(r.q_by)}</TableCell></TableRow>)}</TableBody></Table>
 <div className="pagination-row"><span>Page {page} of {Math.max(1,Math.ceil(result.rows.length/20))} · {result.rows.length} tests</span><Button variant="outline" aria-label="Previous pathway test page" disabled={page===1} onClick={()=>setPage(page-1)}><ArrowLeft size={14}/></Button><Button variant="outline" aria-label="Next pathway test page" disabled={page*20>=result.rows.length} onClick={()=>setPage(page+1)}><ArrowRight size={14}/></Button></div></section>
 </>:<>
 <section className="inventory statistics-metrics" aria-label="Statistical test results"><div><span>Test statistic</span><strong>{result.effect?.boundary||num(result.statistic)}</strong></div><div><span>Unadjusted p-value</span><strong>{pval(result.p_value!)}</strong></div><div><span>{result.effect?.label}</span><strong>{result.effect?.boundary||num(result.effect?.value)}</strong></div></section>
 <section className="panel"><h2>Estimate & uncertainty</h2>{result.confidence_interval?<p className="body-copy">{result.confidence_interval.label}: <strong>{num(result.confidence_interval.low)} to {num(result.confidence_interval.high)}</strong>.</p>:<p className="body-copy">A confidence interval is not supplied for this method and sample size. The effect estimate and p-value answer different questions.</p>}{result.details?.p_value_method&&<p className="body-copy">P-value method: {result.details.p_value_method}. {result.details.seed&&"Seed "+result.details.seed+"; at most "+result.details.resamples+" resamples."}</p>}{result.details?.degrees_of_freedom!==undefined&&<p className="body-copy">Degrees of freedom: {Array.isArray(result.details.degrees_of_freedom)?result.details.degrees_of_freedom.join(", "):num(result.details.degrees_of_freedom)}.</p>}</section>
 {!!result.descriptive?.length&&<section className="panel"><h2>Descriptive statistics</h2><p className="body-copy">{result.inputs?.unit}. Variance and standard deviation use n − 1; quartiles use linear interpolation.</p><Table><TableHeader><TableRow>{["Group / vector","n","Mean","Median","Sample SD","Sample variance","Q1","Q3","Min","Max"].map(h=><TableHead key={h}>{h}</TableHead>)}</TableRow></TableHeader><TableBody>{result.descriptive.map((d,i)=><TableRow key={i}><TableCell>{String.fromCharCode(65+i)}</TableCell>{[d.n,d.mean,d.median,d.standard_deviation,d.variance,d.q1,d.q3,d.minimum,d.maximum].map((n,j)=><TableCell key={j}>{num(n)}</TableCell>)}</TableRow>)}</TableBody></Table></section>}
 {!!result.descriptive?.some(d=>d.distribution?.length)&&<section className="panel"><h2>Empirical distributions</h2><p className="body-copy">Each step is the fraction of values at or below that measurement. No smoothing or fitted distribution; axes are scaled separately for each group.</p><div className="statistics-distributions">{result.descriptive.map((d,i)=>{if(!d.distribution?.length)return null;const pad=(d.maximum-d.minimum||Math.max(1,Math.abs(d.minimum)))*.05;const points=[{value:d.minimum-pad,cumulative_fraction:0},...d.distribution,{value:d.maximum+pad,cumulative_fraction:1}];return <div key={i}><h3>Group / vector {String.fromCharCode(65+i)} · n = {d.n}</h3><div className="statistics-ecdf" role="img" aria-label={"Empirical cumulative distribution for "+String.fromCharCode(65+i)+"; exact values in the JSON export"}><ResponsiveContainer width="100%" height="100%"><LineChart data={points} margin={{top:10,right:12,bottom:10,left:0}}><CartesianGrid strokeDasharray="3 3"/><XAxis dataKey="value" type="number" domain={["dataMin","dataMax"]} tickFormatter={n=>num(n)} tick={{fill:"var(--muted)"}}/><YAxis domain={[0,1]} tickFormatter={n=>Math.round(n*100)+"%"} width={42} tick={{fill:"var(--muted)"}}/><Tooltip formatter={value=>num(Number(value)*100)+"%"} labelFormatter={value=>"Value "+num(Number(value))}/><Line type="stepAfter" dataKey="cumulative_fraction" name="At or below" stroke="var(--accent)" strokeWidth={2} dot={false} isAnimationActive={false}/></LineChart></ResponsiveContainer></div></div>;})}</div></section>}
 {pairedResult&&<section className="panel"><h2>Paired observations</h2><p className="body-copy">Vector A on the horizontal axis, vector B on the vertical axis. Each mark is an input pair; overlapping marks may hide duplicates. Inspect every pair in the JSON export.</p><div className="statistics-scatter" role="img" aria-label="Scatter plot of submitted paired observations; exact pairs included in JSON export"><ResponsiveContainer width="100%" height="100%"><ScatterChart margin={{top:20,right:24,bottom:24,left:12}}><CartesianGrid strokeDasharray="3 3"/><XAxis type="number" dataKey="x" name="Vector A" tick={{fill:"var(--muted)"}} label={{value:"Vector A",position:"bottom",fill:"var(--muted)"}}/><YAxis type="number" dataKey="y" name="Vector B" tick={{fill:"var(--muted)"}}/><Tooltip cursor={{strokeDasharray:"3 3"}}/><Scatter data={pairedResult} fill="var(--accent)" isAnimationActive={false}/></ScatterChart></ResponsiveContainer></div></section>}
 {result.details?.expected_counts&&<section className="panel"><h2>Expected counts under independence</h2><Table><TableHeader><TableRow><TableHead>Group</TableHead><TableHead>Outcome 1</TableHead><TableHead>Outcome 2</TableHead></TableRow></TableHeader><TableBody>{result.details.expected_counts.map((row,i)=><TableRow key={i}><TableCell>{i===0?"A":"B"}</TableCell>{row.map((n,j)=><TableCell key={j}>{num(n)}</TableCell>)}</TableRow>)}</TableBody></Table></section>}
 </>}
 <section className="analysis-method"><h2>Hypotheses, assumptions & provenance</h2><dl className="stat-hypotheses"><div><dt>Null hypothesis</dt><dd>{result.null_hypothesis}</dd></div><div><dt>Alternative</dt><dd>{result.alternative_hypothesis}</dd></div></dl><h3>Assumptions</h3><ul>{result.assumptions.map(s=><li key={s}>{s}</li>)}</ul><h3>Interpretation limits</h3><ul>{result.limitations.map(s=><li key={s}>{s}</li>)}</ul>
 {result.dataset&&<><p>Source: {result.dataset.name} · retrieved {new Date(result.dataset.retrieved_at).toISOString()}. Universe: {result.parameters.universe?.join(", ")}. Selected: {result.parameters.selected_genes?.join(", ")}.</p><div className="checksum"><span>Source SHA-256</span><code>{result.dataset.sha256}</code></div></>}
 {result.input_sha256&&<div className="checksum"><span>Input SHA-256</span><code>{result.input_sha256}</code></div>}
 <p>Computed {new Date(result.computed_at).toISOString()} · SciPy {result.software.scipy} / NumPy {result.software.numpy} · code <code>{result.code_revision.slice(0,12)}</code>. JSON includes full inputs or the source snapshot reference, every result, method parameters and limitations.</p>
 </section></>}
 </div>;
}
