"use client";
import {useEffect,useState} from "react";
import {ArrowRight,ArrowUpRight,Download,Network,RefreshCw,Search,X} from "lucide-react";
import {Button} from "@/components/ui/button";
import {Table,TableBody,TableCell,TableHead,TableHeader,TableRow} from "@/components/ui/table";

type Gene={id:number;symbol:string;name:string;ensembl:string};
type Evidence={gene_id:number;symbol:string;maximum_stage:string;mechanisms:{mechanism:string;action:string;target_ids:string[]}[];diseases:{id:string;name:string}[];reports:{id:string;source:string;url:string|null}[]};
type Drug={id:string;name:string;drug_class:string;maximum_stage:string;url:string;targets:string[];report_count:number;associations:Evidence[]};
type Pathway={id:string;name:string;genes:string[];overlap:number;selected_gene_count:number;url:string};
type Page<T>={items:T[];page:number;page_size:number;total:number};
type Dataset={id:number;name:string;sha256:string;retrieved_at:string;is_fixture:boolean;source:string;url:string};
type Result={dataset:Dataset;datasets:Dataset[];options:{genes:Gene[];drug_classes:string[];stages:string[];diseases:[string,string][]};summary:{selected_genes:number;drugs:number;target_links:number;pathways:number};selected_genes:Gene[];drugs:Page<Drug>;pathways:Page<Pathway>;method:string;computed_at:string;code_revision:string;limitations:string[];export_scope:string};
type Filters={dataset_id:string;genes:string;q:string;drug_class:string;disease:string;stage:string;sort:string;page:string;pathway_page:string};
const initial:Filters={dataset_id:"",genes:"",q:"",drug_class:"",disease:"",stage:"",sort:"name",page:"1",pathway_page:"1"};
const stageLabel=(s:string)=>s.toLowerCase().replaceAll("_"," ");
function Pages({data,label,onPage}:{data:Page<unknown>;label:string;onPage:(page:number)=>void}){
 const total=Math.max(1,Math.ceil(data.total/data.page_size));
 return <div className="pagination"><span>Page {data.page} of {total} · {data.total} {label}</span><Button variant="outline" disabled={data.page===1} onClick={()=>onPage(data.page-1)}>Previous {label}</Button><Button variant="outline" disabled={data.page===total} onClick={()=>onPage(data.page+1)}>Next {label}</Button></div>;
}
export function Research({initialGene=""}:{initialGene?:string}){
 const [filters,setFilters]=useState<Filters>({...initial,genes:initialGene});
 const [draft,setDraft]=useState<Filters>({...initial,genes:initialGene});
 const [data,setData]=useState<Result|null>(null);
 const [options,setOptions]=useState<Result["options"]|null>(null);
 const [datasets,setDatasets]=useState<Dataset[]>([]);
 const [busy,setBusy]=useState(true),[error,setError]=useState<string|null>(null),[retry,setRetry]=useState(0);
 const [selectedDrug,setSelectedDrug]=useState<string|null>(null),[selectedPathway,setSelectedPathway]=useState<string|null>(null);
 const [focus,setFocus]=useState(initialGene),[reportPage,setReportPage]=useState(1);
 useEffect(()=>{
  const controller=new AbortController();setBusy(true);setError(null);setData(null);setSelectedDrug(null);setSelectedPathway(null);
  const query=new URLSearchParams();Object.entries(filters).forEach(([k,v])=>{if(v)query.set(k,v);});
  fetch("/api/research?"+query,{cache:"no-store",signal:controller.signal}).then(async r=>{const body=await r.json();if(!r.ok)throw new Error(body.detail||"Research associations unavailable.");return body as Result;}).then(body=>{
   if(controller.signal.aborted)return;setData(body);setOptions(body.options);setDatasets(body.datasets);
   setFocus(previous=>body.selected_genes.some(g=>g.symbol===previous)?previous:body.selected_genes[0]?.symbol??"");
  }).catch(e=>{if(!controller.signal.aborted)setError(e instanceof Error?e.message:"Research associations unavailable.");}).finally(()=>{if(!controller.signal.aborted)setBusy(false);});
  return()=>controller.abort();
 },[filters,retry]);
 function update(key:keyof Filters,value:string){setDraft({...draft,[key]:value});}
 function apply(next:Filters){setFilters({...next});setDraft({...next});}
 const selected=draft.genes?draft.genes.split(","):options?.genes.map(g=>g.symbol)??[];
 function toggle(symbol:string){const next=selected.includes(symbol)?selected.filter(s=>s!==symbol):[...selected,symbol];if(next.length)update("genes",next.sort().join(","));}
 function chooseDrug(id:string){setSelectedDrug(id);setReportPage(1);}
 function download(){if(!data)return;const url=URL.createObjectURL(new Blob([JSON.stringify({kind:"research_associations",...data},null,2)],{type:"application/json"}));const a=document.createElement("a");a.href=url;a.download="pharmagenome-research-dataset-"+data.dataset.id+".json";a.click();URL.revokeObjectURL(url);}
 const drug=data?.drugs.items.find(d=>d.id===selectedDrug);
 const pathway=data?.pathways.items.find(p=>p.id===selectedPathway);
 const focusGene=data?.selected_genes.find(g=>g.symbol===focus);
 const networkDrugs=data?.drugs.items.filter(d=>d.targets.includes(focus)).slice(0,3)??[];
 const networkPaths=data?.pathways.items.filter(p=>p.genes.includes(focus)).slice(0,3)??[];
 const reports=drug?Array.from(new Map(drug.associations.flatMap(a=>a.reports).map(r=>[r.source+":"+r.id,r])).values()).sort((a,b)=>(a.source+a.id).localeCompare(b.source+b.id)):[];
 return <div className="research">
 <section className="panel filter-panel" aria-label="Research association filters"><form onSubmit={e=>{e.preventDefault();apply({...draft,page:"1",pathway_page:"1"});}}>
 <div className="research-filter-grid">
 <div><label htmlFor="research-dataset">Research snapshot</label><select id="research-dataset" value={draft.dataset_id} onChange={e=>{setDraft({...initial,dataset_id:e.target.value});}} disabled={busy}><option value="">Latest completed snapshot</option>{datasets.map(d=><option key={d.id} value={d.id}>{d.name} · {d.sha256.slice(0,8)}</option>)}</select></div>
 <div><label htmlFor="research-query">Drug name or identifier</label><input id="research-query" maxLength={80} value={draft.q} onChange={e=>update("q",e.target.value)} placeholder="Search the imported drugs" disabled={busy}/></div>
 <div><label htmlFor="research-class">Drug type</label><select id="research-class" value={draft.drug_class} onChange={e=>update("drug_class",e.target.value)} disabled={busy}><option value="">All types</option>{options?.drug_classes.map(s=><option key={s}>{s}</option>)}</select></div>
 <div><label htmlFor="research-stage">Source maximum stage</label><select id="research-stage" value={draft.stage} onChange={e=>update("stage",e.target.value)} disabled={busy}><option value="">All stages</option>{options?.stages.map(s=><option key={s} value={s}>{stageLabel(s)}</option>)}</select></div>
 <div><label htmlFor="research-disease">Associated research disease</label><select id="research-disease" value={draft.disease} onChange={e=>update("disease",e.target.value)} disabled={busy}><option value="">All source disease labels</option>{options?.diseases.map(([id,name])=><option key={id} value={id}>{name}</option>)}</select></div>
 <div><label htmlFor="research-sort">Drug order</label><select id="research-sort" value={draft.sort} onChange={e=>update("sort",e.target.value)} disabled={busy}><option value="name">Name A–Z</option><option value="reports">Source report count</option></select></div>
 </div>
 {options&&<fieldset className="research-genes" disabled={busy}><legend>Selected genes · choose at least one</legend>{options.genes.map(g=><label key={g.id}><input type="checkbox" checked={selected.includes(g.symbol)} onChange={()=>toggle(g.symbol)} disabled={selected.length===1&&selected[0]===g.symbol}/>{g.symbol}</label>)}</fieldset>}
 <div className="report-actions"><Button disabled={busy}><Search size={15}/>Apply research filters</Button><Button type="button" variant="outline" disabled={busy} onClick={()=>apply(initial)}>Reset research filters</Button></div>
 {JSON.stringify(draft)!==JSON.stringify(filters)&&<p role="status" className="chart-caption">Filters changed. Apply research filters to update the results below.</p>}
 <p className="chart-caption">Gene-level research associations. Drug filters affect drug results; pathway overlap uses the selected genes only. Clinical stage is a source snapshot label, not a current approval assessment.</p>
 </form></section>
 {busy&&<div className="analysis-state" role="status"><RefreshCw size={20} className="spin"/><h2>Loading source-linked research…</h2><p>Reading the selected snapshot and counting distinct relationships.</p></div>}
 {error&&<div className="analysis-state research-error" role="alert"><h2>Research associations unavailable</h2><p>{error}</p><Button variant="outline" onClick={()=>setRetry(retry+1)}>Retry research connection</Button></div>}
 {data&&<>
 <div className="research-source"><div><strong>{data.dataset.name}</strong><p>{data.dataset.is_fixture?"Synthetic development fixture":"Public source snapshot"} · retrieved {new Date(data.dataset.retrieved_at).toLocaleDateString()}</p></div><Button variant="outline" onClick={download}><Download size={15}/>Export research JSON</Button></div>
 <section className="inventory research-summary" aria-label="Research result summary">{[["Selected genes",data.summary.selected_genes],["Distinct drugs",data.summary.drugs],["Drug-target links",data.summary.target_links],["Overlapping pathways",data.summary.pathways]].map(([label,value])=><div key={label}><span>{label}</span><strong>{value}</strong></div>)}</section>
 <section className="panel association-network" aria-label="Focused association network"><div className="section-title"><div><h2>One gene. Connected evidence.</h2><p>Explore up to three pathways and three drugs from the current result pages.</p></div><Network size={22}/></div>
 <label htmlFor="network-gene">Focus gene</label><select id="network-gene" value={focus} onChange={e=>setFocus(e.target.value)}>{data.selected_genes.map(g=><option key={g.id}>{g.symbol}</option>)}</select>
 <div className="research-network-grid">
 <div className="network-column"><h3>Pathway membership</h3>{networkPaths.length?networkPaths.map(p=><button className="network-node" key={p.id} aria-pressed={p.id===selectedPathway} onClick={()=>setSelectedPathway(p.id)}><span>{p.name}</span><small>{p.id}</small></button>):<p>No pathways on this page for {focus}.</p>}</div>
 <div className="network-center"><div className="network-gene"><strong>{focus}</strong><span>{focusGene?.name}</span><a href={"https://platform.opentargets.org/target/"+focusGene?.ensembl} target="_blank" rel="noreferrer">Open source target <ArrowUpRight size={13}/></a></div><p>Source membership and mechanism links</p></div>
 <div className="network-column"><h3>Mapped drug mechanisms</h3>{networkDrugs.length?networkDrugs.map(d=><button className="network-node" key={d.id} aria-pressed={d.id===selectedDrug} onClick={()=>chooseDrug(d.id)}><span>{d.name}</span><small>{d.id}</small></button>):<p>No drugs on this page for {focus}.</p>}</div>
 </div><p className="chart-caption">Connections describe source relationships. This graph does not connect a variant to drug response or infer that a drug treats the selected cohort.</p>
 </section>
 <section className="panel research-drugs"><div className="section-title"><div><h2>Drug research catalogue</h2><p>Distinct compounds in the filtered target associations. Select a drug to inspect its evidence.</p></div></div>
 <Table><TableHeader><TableRow><TableHead>Drug</TableHead><TableHead>Type</TableHead><TableHead>Selected targets</TableHead><TableHead>Source maximum stage</TableHead><TableHead>Distinct reports</TableHead></TableRow></TableHeader><TableBody>{data.drugs.items.length?data.drugs.items.map(d=><TableRow key={d.id}><TableCell><button className="table-link" onClick={()=>chooseDrug(d.id)}>{d.name}</button><small>{d.id}</small></TableCell><TableCell>{d.drug_class}</TableCell><TableCell>{d.targets.join(", ")}</TableCell><TableCell>{stageLabel(d.maximum_stage)}</TableCell><TableCell>{d.report_count}</TableCell></TableRow>):<TableRow><TableCell colSpan={5}><div className="table-empty">No drugs match these filters.<span>Try another gene or reset the drug filters. A missing link does not establish biological absence.</span></div></TableCell></TableRow>}</TableBody></Table>
 <Pages data={data.drugs} label="drugs" onPage={page=>apply({...filters,page:String(page)})}/>
 {drug&&<div className="record-detail" aria-label={drug.name+" research details"}><div className="section-title"><div><h3>{drug.name}</h3><p>{drug.id} · {drug.drug_class}</p></div><button className="icon-button" aria-label="Close drug details" onClick={()=>setSelectedDrug(null)}><X size={18}/></button></div>
 <p className="body-copy">Historical source maximum stage: <strong>{stageLabel(drug.maximum_stage)}</strong>. This label is not an indication-specific authorization or a recommendation.</p>
 {drug.associations.map(a=><div className="research-evidence" key={a.gene_id}><h4>{a.symbol} · source-mapped mechanism</h4><ul>{a.mechanisms.map((m,i)=><li key={i}>{m.mechanism} <span>({m.action.toLowerCase()})</span>{m.target_ids.length>1&&<small>Mechanism maps to {m.target_ids.length} target identifiers; selectivity is not established.</small>}</li>)}</ul><details><summary>Associated research diseases ({a.diseases.length})</summary><ul>{a.diseases.map(d=><li key={d.id}><a href={"https://platform.opentargets.org/disease/"+d.id} target="_blank" rel="noreferrer">{d.name} <ArrowUpRight size={12}/></a></li>)}</ul>{!a.diseases.length&&<p>No mapped disease labels supplied.</p>}</details></div>)}
 <h4>Source reports · {reports.length} distinct records</h4><p className="chart-caption">Reports may include trials, labels and other source records. This is not a count of independent studies or supporting efficacy results.</p><ul className="research-reports">{reports.slice((reportPage-1)*10,reportPage*10).map(r=><li key={r.source+":"+r.id}>{r.url?<a href={r.url} target="_blank" rel="noreferrer">{r.source} · {r.id}<ArrowUpRight size={13}/></a>:<span>{r.source} · {r.id} · source URL not supplied</span>}</li>)}</ul>{!reports.length&&<p>No clinical report records supplied.</p>}
 {reports.length>10&&<Pages data={{items:[],total:reports.length,page:reportPage,page_size:10}} label="reports" onPage={setReportPage}/>}
 <a className="text-action" href={drug.url} target="_blank" rel="noreferrer">Inspect drug in Open Targets <ArrowUpRight size={14}/></a>
 </div>}
 </section>
 <section className="panel research-pathways"><div className="section-title"><div><h2>Pathway overlap</h2><p>Ranked by the number of distinct selected genes in each source pathway. This is descriptive overlap, not enrichment.</p></div></div>
 <Table><TableHeader><TableRow><TableHead>Reactome pathway</TableHead><TableHead>Selected gene overlap</TableHead><TableHead>Genes in common</TableHead></TableRow></TableHeader><TableBody>{data.pathways.items.length?data.pathways.items.map(p=><TableRow key={p.id}><TableCell><button className="table-link" onClick={()=>setSelectedPathway(p.id)}>{p.name}</button><small>{p.id}</small></TableCell><TableCell><strong>{p.overlap} / {p.selected_gene_count}</strong><div className="overlap-track" aria-hidden="true"><span style={{width:(p.overlap/p.selected_gene_count*100)+"%"}}/></div></TableCell><TableCell>{p.genes.join(", ")}</TableCell></TableRow>):<TableRow><TableCell colSpan={3}><div className="table-empty">No pathway membership supplied for these genes.</div></TableCell></TableRow>}</TableBody></Table>
 <Pages data={data.pathways} label="pathways" onPage={page=>apply({...filters,pathway_page:String(page)})}/>
 {pathway&&<div className="record-detail" aria-label="Pathway details"><div className="section-title"><h3>{pathway.name}</h3><button className="icon-button" aria-label="Close pathway details" onClick={()=>setSelectedPathway(null)}><X size={18}/></button></div><p className="body-copy">{pathway.overlap} of {pathway.selected_gene_count} selected genes: {pathway.genes.join(", ")}. The denominator is your selected gene set, not the full pathway size. No p-value is calculated.</p><a className="text-action" href={pathway.url} target="_blank" rel="noreferrer">Inspect Reactome pathway <ArrowRight size={14}/></a></div>}
 </section>
 <section className="panel research-provenance"><h2>Methods & source boundaries</h2><ul className="limitations">{data.limitations.map(l=><li key={l}>{l}</li>)}</ul><div className="checksum"><span>Snapshot SHA-256</span><code>{data.dataset.sha256}</code></div><p className="chart-caption">{data.method} · {new Date(data.computed_at).toISOString()} · code {data.code_revision.slice(0,12)}</p><p className="body-copy">{data.export_scope}</p><a className="text-action" href="https://github.com/292akhil2929-cmyk/pharmagenome/blob/main/docs/RESEARCH.md" target="_blank" rel="noreferrer">Read research association methods <ArrowUpRight size={14}/></a></section>
 </>}
 </div>;
}
