export type AnalysisHistoryItem={id:string;kind:string;title:string;summary:string;view:"Statistics"|"ML Analysis";created_at:string;source:string};
const KEY="pharmagenome-analysis-history-v1";
export function readAnalysisHistory():AnalysisHistoryItem[]{
 if(typeof window==="undefined")return[];
 try{const value=JSON.parse(localStorage.getItem(KEY)||"[]");return Array.isArray(value)?value.slice(0,6):[];}catch{return[];}
}
export function recordAnalysis(item:Omit<AnalysisHistoryItem,"id"|"created_at">){
 if(typeof window==="undefined")return;
 try{
  const next:AnalysisHistoryItem={...item,id:crypto.randomUUID(),created_at:new Date().toISOString()};
  localStorage.setItem(KEY,JSON.stringify([next,...readAnalysisHistory()].slice(0,6)));
  window.dispatchEvent(new Event("pharmagenome:analysis-history"));
 }catch{
  // Recent navigation metadata is optional and must never change a completed analysis.
 }
}
