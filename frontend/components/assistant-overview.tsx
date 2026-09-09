"use client";
import {useEffect,useState} from "react";
import {ArrowRight,BrainCircuit,Check,LockKeyhole,RefreshCw} from "lucide-react";
import {Button} from "@/components/ui/button";
type Props={onNavigate:(view:"Statistics"|"ML Analysis")=>void};
type Status={available:boolean;model:string;reason:string|null;policy:string};
export function AssistantOverview({onNavigate}:Props){
 const [status,setStatus]=useState<Status|null>(null),[failed,setFailed]=useState(false);
 async function load(){setStatus(null);setFailed(false);try{const response=await fetch("/api/research/explain/status",{cache:"no-store"});const body=await response.json();setStatus(body);setFailed(!response.ok||body.reason==="Explanation status is unavailable.");}catch{setFailed(true);setStatus({available:false,model:"gpt-6-astra",reason:"Explanation status is unavailable.",policy:"Optional explanation only."});}}
 useEffect(()=>{void load();},[]);
 return <div className="assistant-overview">
  <section className="panel assistant-intro"><BrainCircuit size={27}/><div><h2>Compute first. Explain second.</h2><p>The research assistant receives a compact result only after PharmaGenome has completed the actual statistics or model evaluation. It cannot change the calculation.</p></div><span className={status?.available?"assistant-access ready":"assistant-access"}>{!status?"Checking access":status.available?"Model available":"Model unavailable"}</span></section>
  <section className="assistant-flow" aria-label="Research explanation workflow">{[["Compute","Run a declared statistical test or repeated model evaluation."],["Inspect","Review metrics, assumptions, limitations and provenance."],["Explain","Ask GPT-6 Astra to summarize only the structured evidence."]].map(([title,copy],index)=><div className="panel" key={title}><span>{index+1}</span><h3>{title}</h3><p>{copy}</p></div>)}</section>
  <section className="panel assistant-entry"><div><h2>Choose an evidence path</h2><p>Start with a complete analysis. The explanation action appears beside its underlying evidence.</p></div><div><Button onClick={()=>onNavigate("Statistics")}>Open Statistics <ArrowRight size={15}/></Button><Button variant="outline" onClick={()=>onNavigate("ML Analysis")}>Open ML Analysis <ArrowRight size={15}/></Button></div></section>
  <section className="panel assistant-contract"><div>{status?.available?<Check size={19}/>:status?<LockKeyhole size={19}/>:<RefreshCw className="spin" size={19}/>}<div><h2>{status?.model||"gpt-6-astra"}</h2><p>{status?.reason||status?.policy||"Checking the server-side model boundary."}</p></div></div>{failed&&<Button variant="outline" onClick={load}>Retry model status</Button>}<ul><li>Raw measurements and sample or person identifiers stay outside model requests.</li><li>Every generated statement cites submitted evidence keys.</li><li>Unknown citations or invented numeric values are rejected.</li><li>AI prose never becomes medical advice or the analytical result.</li></ul></section>
 </div>;
}
