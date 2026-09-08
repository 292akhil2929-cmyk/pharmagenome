"use client";
import {useEffect,useRef,useState} from "react";
import {ArrowDown,ArrowRight,ArrowUpRight,Check,ChevronRight,Database,Dna,ExternalLink,FileJson,GitBranch,Layers,LayoutDashboard,LoaderCircle,Menu,Moon,Network,RefreshCw,ShieldCheck,Sun,X} from "lucide-react";
import {Button} from "@/components/ui/button";
import {Table,TableHeader,TableBody,TableRow,TableHead,TableCell} from "@/components/ui/table";

type Dataset = {id:number;name:string;source:string;version:string;retrieved_at:string;is_fixture:boolean;url:string;license:string;valid:number|null;invalid:number|null;duplicates:number|null};
type System = {version:string;phase:number;checked_at:string;database:{status:string;schema_version:string|null};counts:Record<string,number>|null;datasets:Dataset[];limitations:string[]};
type View = "Workspace"|"Data sources"|"Architecture";
const repo="https://github.com/292akhil2929-cmyk/pharmagenome";
const sourcePlans = [
 {name:"cBioPortal",type:"Somatic variants · profiled cohorts",purpose:"Mutation observations and explicit sample denominators",url:"https://docs.cbioportal.org/web-api-and-clients/"},
 {name:"NCBI Gene",type:"Gene identifiers · genomic locations",purpose:"Stable gene identity and assembly-specific coordinates",url:"https://www.ncbi.nlm.nih.gov/gene/"},
 {name:"ChEMBL",type:"Compounds · target evidence",purpose:"Sourced drug-target research relationships",url:"https://www.ebi.ac.uk/chembl/"},
 {name:"Reactome",type:"Curated biological pathways",purpose:"Gene membership for transparent pathway overlap",url:"https://reactome.org/"}
];
export function Workspace() {
 const [view,setView]=useState<View>("Workspace");
 const [data,setData]=useState<System|null>(null);
 const [error,setError]=useState<string|null>(null);
 const [loading,setLoading]=useState(true);
 const [dark,setDark]=useState(false);
 const [menu,setMenu]=useState(false);
 const [mobile,setMobile]=useState(false);
 const sidebar=useRef<HTMLElement>(null);
 const menuTrigger=useRef<HTMLButtonElement>(null);
 useEffect(()=>{const mq=window.matchMedia("(max-width:650px)");const update=()=>{setMobile(mq.matches);if(!mq.matches)setMenu(false);};update();mq.addEventListener("change",update);return()=>mq.removeEventListener("change",update);},[]);
 useEffect(()=>{
  if(!menu||!mobile)return;
  const drawer=sidebar.current;
  const focusable=()=>Array.from(drawer?.querySelectorAll<HTMLElement>("a[href],button:not([disabled])")||[]);
  focusable()[0]?.focus();
  function handleKey(e:KeyboardEvent){
   if(e.key==="Escape"){e.preventDefault();setMenu(false);}
   if(e.key==="Tab"){const items=focusable();const first=items[0];const last=items[items.length-1];
    if(e.shiftKey&&document.activeElement===first){e.preventDefault();last?.focus();}
    else if(!e.shiftKey&&document.activeElement===last){e.preventDefault();first?.focus();}
   }
  }
  document.addEventListener("keydown",handleKey);
  const oldOverflow=document.body.style.overflow;document.body.style.overflow="hidden";
  return()=>{document.removeEventListener("keydown",handleKey);document.body.style.overflow=oldOverflow;menuTrigger.current?.focus();};
 },[menu,mobile]);
 useEffect(()=>{const value=localStorage.getItem("pharmagenome-theme")==="dark";setDark(value);document.documentElement.dataset.theme=value?"dark":"light";},[]);
 async function refresh() {
  setLoading(true);setError(null);
  try {const res=await fetch("/api/system",{cache:"no-store"});const body=await res.json();if(!res.ok) throw new Error(body.detail||"Connection failed.");setData(body);}
  catch(e){setData(null);setError(e instanceof Error?e.message:"Connection failed.");}
  finally{setLoading(false);}
 }
 useEffect(()=>{void refresh();},[]);
 function theme(){const value=!dark;setDark(value);document.documentElement.dataset.theme=value?"dark":"light";localStorage.setItem("pharmagenome-theme",value?"dark":"light");}
 function navigate(next:View){setView(next);setMenu(false);}
 const ready=data?.database.status==="ready";
 const label=loading?"Checking connection":error?"API unavailable":ready?"Database connected":data?.database.status==="not_configured"?"Database not configured":data?.database.status==="migration_required"?"Migration required":"Database unavailable";
 function exportSnapshot(){if(!data)return;const url=URL.createObjectURL(new Blob([JSON.stringify({kind:"system_snapshot",...data},null,2)],{type:"application/json"}));const a=document.createElement("a");a.href=url;a.download="pharmagenome-system-snapshot.json";a.click();URL.revokeObjectURL(url);}
 return <div className="shell">
  <a className="skip-link" href="#main">Skip to workspace</a>
  <aside ref={sidebar} id="research-navigation" inert={mobile&&!menu?true:undefined} role={mobile&&menu?"dialog":undefined} aria-modal={mobile&&menu?true:undefined} className={menu?"sidebar open":"sidebar"} aria-label="Workspace navigation">
   <a href="/" className="brand"><span className="brand-mark"><Dna size={24}/></span><span>PharmaGenome<span className="brand-sub">Genomics. In context.</span></span></a>
   <div className="workspace-selector"><span className="workspace-avatar">PG</span><div>Research workspace<small>Public research · v0.1</small></div><Layers size={16}/></div>
   <nav>{([{name:"Workspace",icon:LayoutDashboard},{name:"Data sources",icon:Database},{name:"Architecture",icon:Network}] as const).map(item=><button key={item.name} onClick={()=>navigate(item.name)} aria-current={view===item.name?"page":undefined}><item.icon size={18}/>{item.name}{view===item.name&&<ChevronRight size={15}/>}</button>)}</nav>
   <div className="sidebar-note"><GitBranch size={18}/><strong>A foundation for evidence.</strong><p>Every result begins with a dataset. Every relationship keeps its source.</p><a href={repo+"/blob/main/docs/ROADMAP.md"} target="_blank" rel="noreferrer">View the build roadmap <ArrowUpRight size={14}/></a></div>
   <div className="sidebar-bottom"><a href={repo} target="_blank" rel="noreferrer"><GitBranch size={16}/>Source code<ExternalLink size={13}/></a><span><ShieldCheck size={16}/>Research use only</span></div>
  </aside>
  {menu&&<button aria-label="Close navigation overlay" className="overlay" onClick={()=>setMenu(false)}/>}
  <div className="main-shell" inert={mobile&&menu?true:undefined}>
   <header className="topbar"><div className="breadcrumb"><button ref={menuTrigger} aria-expanded={menu} aria-controls="research-navigation" className="icon-button mobile-menu" aria-label={menu?"Close navigation":"Open navigation"} onClick={()=>setMenu(!menu)}>{menu?<X size={20}/>:<Menu size={20}/>}</button><span>Research workspace</span><ChevronRight size={14}/><strong>{view}</strong></div><div className="top-actions"><span className="release-chip">Foundation release</span><button className="icon-button" aria-label={dark?"Switch to light mode":"Switch to dark mode"} onClick={theme}>{dark?<Sun size={19}/>:<Moon size={19}/>}</button><span className="profile">PG</span></div></header>
   <main id="main">
    <div className="page-heading"><div><h1>{view==="Workspace"?"Research starts with evidence.":view==="Data sources"?"Know where your data begins.":"Built to make results traceable."}</h1><p>{view==="Workspace"?"Your genomic and pharmaceutical analytics workspace.":view==="Data sources"?"A transparent record of source, version, retrieval and quality.":"A computational pipeline with provenance at every step."}</p></div><Button variant="outline" onClick={refresh} disabled={loading}>{loading?<LoaderCircle className="spin" size={16}/>:<RefreshCw size={16}/>}Refresh connection</Button></div>
    <div className={"connection-strip "+(error?"connection-error":"")} role="status"><span className={"status-dot "+(ready?"ready":"")}/><strong>{label}</strong><span>{loading?"Contacting the research API…":error|| (ready?"PostgreSQL is responding. Dataset counts are read from the database.":"Dataset counts remain unavailable until the database is ready.")}</span>{data&&<time dateTime={data.checked_at}>{new Date(data.checked_at).toLocaleTimeString([],{hour:"2-digit",minute:"2-digit"})}</time>}</div>
    {view==="Workspace"&&<>
     <section className="inventory" aria-label="Dataset inventory">{["samples","variants","genes","drugs","pathways"].map((key)=><div key={key}><span>{key==="samples"?"Total samples":key==="genes"?"Catalogued genes":key==="variants"?"Unique variants":key==="drugs"?"Compounds":"Pathways"}</span><strong>{data?.counts?data.counts[key].toLocaleString():"—"}</strong><small>{data?.counts?"Records in database":"Awaiting connection"}</small></div>)}</section>
     <div className="primary-grid">
      <section className="panel cohort-panel"><div className="section-title"><div><h2>Your research collection</h2><p>Verified datasets will appear here after ingestion.</p></div><Database size={20}/></div><div className="empty-collection"><div className="empty-symbol"><Database size={30}/><span><Layers size={14}/></span></div><h3>{!ready?(loading?"Checking your collection…":"Collection unavailable."):data?.datasets.length?"Your datasets are ready to inspect.":"No datasets imported yet."}</h3><p>{!ready?"A database connection is required to confirm the contents of your research collection.":data?.datasets.length?"Open the data catalogue to review provenance and ingestion status.":"The workspace is ready for its first scientific dataset. Counts, visualizations and findings will come from validated records."}</p><Button onClick={()=>navigate("Data sources")}>Explore data sources <ArrowRight size={16}/></Button></div><div className="collection-footer"><ShieldCheck size={16}/><span>No generated measurements. No implied clinical validity.</span></div></section>
      <section className="panel relationship-panel"><div className="section-title"><div><h2>From variation to context</h2><p>The research model</p></div><Network size={20}/></div><div className="relationship-flow">{[{name:"Genomic variation",detail:"Assembly · locus · alleles",icon:Dna},{name:"Genes & disease",detail:"Cohort · annotation · phenotype",icon:GitBranch},{name:"Pathways & targets",detail:"Membership · overlap · evidence",icon:Network},{name:"Pharmaceutical context",detail:"Compound · mechanism · source",icon:Layers}].map((item,i)=><div className="flow-step" key={item.name}><span className="flow-icon"><item.icon size={20}/></span><div><strong>{item.name}</strong><small>{item.detail}</small></div>{i<3&&<ArrowDown className="flow-arrow" size={15}/>}</div>)}</div><p className="model-note">Schema relationships shown here describe the data model, not observed biological findings.</p></section>
     </div>
     <div className="secondary-grid"><section className="panel"><div className="section-title"><div><h2>Dataset health</h2><p>Quality is measured, never assumed.</p></div><ShieldCheck size={20}/></div><div className="health-empty"><span>Validation coverage</span><strong>Not measured</strong><p>A completed ingestion report is required before quality percentages can be calculated.</p></div><button className="text-action" onClick={()=>navigate("Data sources")}>Review provenance requirements <ArrowUpRight size={16}/></button></section><section className="panel"><div className="section-title"><div><h2>Reproducibility, by design</h2><p>Inspect the foundation behind the workspace.</p></div><FileJson size={20}/></div><ul className="evidence-list"><li><Check size={16}/>Versioned datasets and source checksums</li><li><Check size={16}/>Explicit cohort and genome assembly</li><li><Check size={16}/>Analysis parameters and code revision</li></ul><Button variant="outline" onClick={exportSnapshot} disabled={!data||loading}><FileJson size={15}/>Export system snapshot</Button><small className="export-note">Exports infrastructure state, not an analytical result.</small></section></div>
    </>}
    {view==="Data sources"&&<><section className="panel source-panel"><div className="section-title"><div><h2>Imported datasets</h2><p>{ready?data?.datasets.length: "Unknown"} registered versions · source metadata stays with each import</p></div><Database size={20}/></div><Table><TableHeader><TableRow><TableHead>Dataset</TableHead><TableHead>Source</TableHead><TableHead>Version</TableHead><TableHead>Retrieved</TableHead><TableHead>Data type</TableHead></TableRow></TableHeader><TableBody>{data?.datasets.length?data.datasets.map(d=><TableRow key={d.id}><TableCell>{d.name}</TableCell><TableCell><a href={d.url}>{d.source}</a></TableCell><TableCell>{d.version}</TableCell><TableCell>{new Date(d.retrieved_at).toLocaleDateString()}</TableCell><TableCell>{d.is_fixture?"Development fixture":"Source data"}</TableCell></TableRow>):<TableRow><TableCell colSpan={5}><div className="table-empty">{ready?"No imports to report.":loading?"Checking imported datasets…":"Imported dataset inventory unavailable."}<span>{ready?"Data-source plans below are not ingested datasets.":"Refresh the connection to verify whether datasets have been imported."}</span></div></TableCell></TableRow>}</TableBody></Table></section><h2 className="standalone-title">Planned source connections</h2><div className="source-list">{sourcePlans.map((s)=><a href={s.url} key={s.name} target="_blank" rel="noreferrer"><div><h3>{s.name}</h3><span>{s.type}</span></div><p>{s.purpose}</p><span className="planned-chip">Planned</span><ArrowUpRight size={18}/></a>)}</div><p className="source-footnote">Access terms, fields, retrieval dates and dataset versions must be recorded before import. <a href={repo+"/blob/main/DATA_SOURCES.md"}>Read the source policy <ArrowUpRight size={13}/></a></p></>}
    {view==="Architecture"&&<><section className="panel architecture-panel"><div className="section-title"><div><h2>Computation comes first.</h2><p>The optional explanation layer only receives computed, structured evidence.</p></div><GitBranch size={22}/></div><ol className="pipeline">{["Source snapshot","Validation & normalization","PostgreSQL analytical datasets","Statistics & bioinformatics","Model evaluation","Visualization & export","Optional research explanation"].map((step,i)=><li key={step}><span>{String(i+1).padStart(2,"0")}</span><div><strong>{step}</strong><small>{i===2?"Phase 1 · schema foundation":"Planned in subsequent phases"}</small></div>{i<6&&<ArrowDown size={17}/>}</li>)}</ol></section><div className="secondary-grid"><section className="panel"><h2>Correct denominators</h2><p className="body-copy">Profile membership includes eligible samples with no observed mutations. Mutation frequency will count distinct mutated samples, not variant rows.</p></section><section className="panel"><h2>Separate observation from identity</h2><p className="body-copy">Genome assembly is part of every variant identity. Sample allele fractions remain separate from population frequencies and clinical annotations.</p></section></div><a className="text-action architecture-link" href={repo+"/blob/main/ARCHITECTURE.md"} target="_blank" rel="noreferrer">Read the full architecture <ArrowUpRight size={16}/></a></>}
    <footer><ShieldCheck size={17}/><p>This platform is intended for educational, research, and analytical purposes. Results are not medical advice and should not be used to diagnose disease or make treatment decisions.</p><a href={repo+"/blob/main/docs/ROADMAP.md"}>Phase 1 / 10 <ArrowUpRight size={13}/></a></footer>
   </main>
  </div>
 </div>;
}
