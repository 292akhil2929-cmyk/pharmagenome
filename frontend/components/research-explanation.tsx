"use client";
import {useEffect,useState} from "react";
import {ArrowUp,BrainCircuit,LockKeyhole,RefreshCw,Sparkles} from "lucide-react";
import {Button} from "@/components/ui/button";

type Status={available:boolean;model:string;provider:string;policy:string;reason:string|null};
type Statement={statement:string;evidence_ids:string[]};
type Explanation={summary:Statement;findings:Statement[];caveats:Statement[];model:string;provider:string;response_id:string|null;generated_at:string;evidence_sha256:string;boundary:string};
type Props={analysisType:"statistical_analysis"|"drug_response_model";evidence:Record<string,unknown>;underlyingId:string};

function StatementRow({item,index}:{item:Statement;index:string}){
 return <li><span className="assistant-index">{index}</span><div><p>{item.statement}</p><div className="assistant-citations" aria-label="Supporting evidence keys">{item.evidence_ids.map(id=><code key={id}>{id}</code>)}</div></div></li>;
}

export function ResearchExplanation({analysisType,evidence,underlyingId}:Props){
 const [status,setStatus]=useState<Status|null>(null),[statusFailed,setStatusFailed]=useState(false),[result,setResult]=useState<Explanation|null>(null),[error,setError]=useState(""),[busy,setBusy]=useState(false);
 async function checkStatus(){
  setStatus(null);setStatusFailed(false);
  try{const response=await fetch("/api/research/explain/status",{cache:"no-store"});const body=await response.json();setStatus(body);setStatusFailed(!response.ok||body.reason==="Explanation status is unavailable.");}
  catch{setStatusFailed(true);setStatus({available:false,model:"gpt-6-astra",provider:"OpenAI Responses API",policy:"Optional explanation only.",reason:"Explanation status is unavailable."});}
 }
 useEffect(()=>{void checkStatus();},[]);
 async function explain(){
  setBusy(true);setError("");setResult(null);
  try{const response=await fetch("/api/research/explain",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({analysis_type:analysisType,evidence})});const body=await response.json();if(!response.ok)throw new Error(body.detail||"AI explanation unavailable.");setResult(body);}
  catch(e){setError(e instanceof Error?e.message:"AI explanation unavailable.");}finally{setBusy(false);}
 }
 function underlying(){const target=document.getElementById(underlyingId);target?.focus();target?.scrollIntoView({block:"start"});}
 return <section className="panel research-assistant" aria-labelledby={"assistant-title-"+analysisType}>
  <div className="assistant-rail" aria-hidden="true"><BrainCircuit size={21}/></div>
  <div className="assistant-body">
   <header><div><h2 id={"assistant-title-"+analysisType}>Read the result with its evidence attached.</h2></div><span className="assistant-model">{status?.model||"GPT-6 Astra"}</span></header>
   {!status?<p role="status" className="assistant-status"><RefreshCw className="spin" size={15}/>Checking server-side model access…</p>:!status.available?<div className="assistant-unavailable"><LockKeyhole size={18}/><div><strong>Explanation unavailable</strong><p>{status.reason} The calculated result above remains complete and authoritative.</p>{statusFailed&&<Button variant="outline" onClick={checkStatus}>Retry model status</Button>}</div></div>:!result?<div className="assistant-ready"><p>Send only the compact computed evidence shown in this result. Raw measurements and sample or person identifiers stay outside the explanation request; source names and provenance hashes are included.</p><Button onClick={explain} disabled={busy}>{busy?<RefreshCw className="spin" size={15}/>:<Sparkles size={15}/>} {busy?"Generating from evidence…":"Explain this analysis"}</Button></div>:<>
    <div className="assistant-summary"><span>Evidence-bound reading</span><p>{result.summary.statement}</p><div className="assistant-citations">{result.summary.evidence_ids.map(id=><code key={id}>{id}</code>)}</div></div>
    <div className="assistant-columns"><div><h3>Supported findings</h3><ol>{result.findings.map((item,index)=><StatementRow key={index} item={item} index={String(index+1).padStart(2,"0")}/>)}</ol></div><div><h3>Scope checks</h3><ol>{result.caveats.map((item,index)=><StatementRow key={index} item={item} index={"C"+(index+1)}/>)}</ol></div></div>
    <p className="assistant-provenance">Generated {new Date(result.generated_at).toISOString()} · {result.provider} · evidence <code>{result.evidence_sha256.slice(0,16)}…</code></p>
   </>}
   {error&&<div role="alert" className="assistant-error"><p>{error}</p><Button variant="outline" onClick={explain}>Retry explanation</Button></div>}
   <button type="button" className="text-action assistant-underlying" onClick={underlying}><ArrowUp size={14}/>View underlying analysis</button>
   <p className="assistant-boundary">AI prose never changes the calculation, source values or interpretation limits.</p>
  </div>
 </section>;
}
