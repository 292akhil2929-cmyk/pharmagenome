"use client";
import {useCallback,useEffect,useState} from "react";
import {Activity,ArrowRight,Clock3,GitBranch,RefreshCw} from "lucide-react";
import {Bar,BarChart,CartesianGrid,ResponsiveContainer,Tooltip,XAxis,YAxis} from "recharts";
import {Button} from "@/components/ui/button";
import {readAnalysisHistory,type AnalysisHistoryItem} from "@/lib/analysis-history";

type View="Statistics"|"ML Analysis"|"Genomics"|"Variants"|"Drugs";
type Genomic={dataset:{name:string;sha256:string};summary:{eligible_samples:number;variants:number;observations:number};genes:{symbol:string;frequency:number|null;mutated_samples:number;eligible_samples:number;variants:number}[];chromosomes:{label:string;count:number}[];variant_types:{label:string;count:number}[];vaf_histogram:{label:string;count:number}[]};
type Research={dataset:{name:string;sha256:string};summary:{selected_genes:number;drugs:number;target_links:number;pathways:number};drugs:{items:{id:string;name:string;targets:string[];report_count:number}[]};pathways:{items:{id:string;name:string;genes:string[];overlap:number}[]}};
type Props={onNavigate:(view:View)=>void};

export function Dashboard({onNavigate}:Props){
 const [genomics,setGenomics]=useState<Genomic|null>(null),[research,setResearch]=useState<Research|null>(null),[history,setHistory]=useState<AnalysisHistoryItem[]>([]);
 const [loading,setLoading]=useState(true),[error,setError]=useState("");
 const load=useCallback(async()=>{
  setLoading(true);setError("");
  try{
   const [g,r]=await Promise.all([fetch("/api/genomics?page_size=5",{cache:"no-store"}),fetch("/api/research?page_size=6&sort=reports",{cache:"no-store"})]);
   const [gb,rb]=await Promise.all([g.json(),r.json()]);
   if(!g.ok||!r.ok)throw new Error(gb.detail||rb.detail||"Dashboard evidence is unavailable.");
   setGenomics(gb);setResearch(rb);
  }catch(e){setError(e instanceof Error?e.message:"Dashboard evidence is unavailable.");}
  finally{setLoading(false);}
 },[]);
 useEffect(()=>{void load();setHistory(readAnalysisHistory());const update=()=>setHistory(readAnalysisHistory());window.addEventListener("pharmagenome:analysis-history",update);return()=>window.removeEventListener("pharmagenome:analysis-history",update);},[load]);
 const top=genomics?.genes.slice(0,6).map(g=>({...g,percent:g.frequency==null?0:g.frequency*100}))||[];
 const chromosomes=[...(genomics?.chromosomes||[])].sort((a,b)=>b.count-a.count).slice(0,10);
 const genes=[...new Set(research?.drugs.items.flatMap(drug=>drug.targets)||[])].slice(0,6);
 if(loading)return <section className="panel dashboard-state" aria-live="polite"><RefreshCw className="spin" size={19}/><div><h2>Assembling the evidence dashboard</h2><p>Reading genomic distributions and source-linked pharmaceutical context.</p></div></section>;
 if(error||!genomics||!research)return <section className="panel dashboard-state dashboard-error" role="alert"><Activity size={19}/><div><h2>Dashboard evidence unavailable</h2><p>{error}</p><Button variant="outline" onClick={load}>Retry dashboard evidence</Button></div></section>;
 return <div className="dashboard-evidence">
  <div className="dashboard-grid">
   <section className="panel dashboard-chart-panel"><header><div><h2>Top mutated genes</h2><p>Distinct mutated samples divided by eligible profiled samples.</p></div><button className="text-action" onClick={()=>onNavigate("Genomics")}>Open genomics <ArrowRight size={14}/></button></header><div className="dashboard-chart" role="img" aria-label="Top mutated genes by profiled-sample frequency"><ResponsiveContainer width="100%" height="100%"><BarChart data={top} layout="vertical" margin={{left:8,right:25}}><CartesianGrid strokeDasharray="2 5" horizontal={false}/><XAxis type="number" domain={[0,100]} tickFormatter={v=>v+"%"}/><YAxis type="category" dataKey="symbol" width={54}/><Tooltip formatter={(value)=>Number(value).toFixed(1)+"%"}/><Bar dataKey="percent" fill="var(--accent)" radius={[0,3,3,0]} isAnimationActive={false}/></BarChart></ResponsiveContainer></div><p className="dashboard-foot">{genomics.dataset.name} · {genomics.summary.eligible_samples} eligible samples</p></section>
   <section className="panel dashboard-chart-panel"><header><div><h2>Mutation trends</h2><p>Cohort VAF pattern, not a temporal trend or population frequency.</p></div></header><div className="dashboard-chart" role="img" aria-label="Variant allele fraction histogram"><ResponsiveContainer width="100%" height="100%"><BarChart data={genomics.vaf_histogram} margin={{left:0,right:8}}><CartesianGrid strokeDasharray="2 5" vertical={false}/><XAxis dataKey="label" interval={1}/><YAxis width={38}/><Tooltip/><Bar dataKey="count" fill="var(--accent)" radius={[3,3,0,0]} isAnimationActive={false}/></BarChart></ResponsiveContainer></div><p className="dashboard-foot">{genomics.summary.observations} accepted sample observations · VAF is tumour read fraction</p></section>
   <section className="panel dashboard-chart-panel dashboard-variants"><header><div><h2>Variant distribution</h2><p>Distinct imported variant identities by chromosome.</p></div><button className="text-action" onClick={()=>onNavigate("Variants")}>Inspect variants <ArrowRight size={14}/></button></header><div className="dashboard-chart" role="img" aria-label="Distinct imported variants by chromosome"><ResponsiveContainer width="100%" height="100%"><BarChart data={chromosomes} margin={{left:0,right:8}}><CartesianGrid strokeDasharray="2 5" vertical={false}/><XAxis dataKey="label"/><YAxis width={38}/><Tooltip/><Bar dataKey="count" fill="var(--chart-two)" radius={[3,3,0,0]} isAnimationActive={false}/></BarChart></ResponsiveContainer></div><div className="dashboard-type-ledger">{genomics.variant_types.map(type=><div key={type.label}><span>{type.label}</span><strong>{type.count}</strong></div>)}</div></section>
   <section className="panel dashboard-network"><header><div><h2>Drug-target network</h2><p>Source-linked associations for the imported ten-gene panel.</p></div><button className="text-action" onClick={()=>onNavigate("Drugs")}>Open drug evidence <ArrowRight size={14}/></button></header><div className="dashboard-network-map"><div><h3>Genes</h3>{genes.map(gene=><span className="dashboard-gene" key={gene}>{gene}</span>)}</div><div className="dashboard-link-axis"><GitBranch size={18}/><strong>{research.summary.target_links}</strong><span>selected-gene links</span></div><div><h3>Source-ranked drugs</h3>{research.drugs.items.slice(0,6).map(drug=><div className="dashboard-drug" key={drug.id}><strong>{drug.name}</strong><span>{drug.targets.join(", ")} · {drug.report_count} reports</span></div>)}</div></div><p className="dashboard-foot">{research.dataset.name} · associations do not establish efficacy or variant response</p></section>
  </div>
  <section className="panel dashboard-recent"><header><div><h2>Recent analyses</h2><p>Metadata saved only in this browser; raw measurements are never stored here.</p></div></header>{history.length?<ol>{history.map(item=><li key={item.id}><Clock3 size={15}/><button onClick={()=>onNavigate(item.view)}><strong>{item.title}</strong><span>{item.summary}</span></button><time dateTime={item.created_at}>{new Date(item.created_at).toLocaleString()}</time></li>)}</ol>:<div className="dashboard-empty-history"><p>No analyses have been saved in this browser yet.</p><div><Button onClick={()=>onNavigate("Statistics")}>Run statistics</Button><Button variant="outline" onClick={()=>onNavigate("ML Analysis")}>Evaluate a model</Button></div></div>}</section>
 </div>;
}
