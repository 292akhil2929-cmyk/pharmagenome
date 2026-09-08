import {NextResponse} from "next/server";
export const dynamic="force-dynamic";
export async function GET(){
 const base=process.env.API_BASE_URL;
 if(!base)return NextResponse.json({available:false,model:"gpt-6-astra",provider:"OpenAI Responses API",policy:"Optional explanation only.",reason:"Research API connection is not configured."});
 try{
  const response=await fetch(new URL("/api/research/explain/status",base),{cache:"no-store",signal:AbortSignal.timeout(8000)});
  const body=await response.json();
  return NextResponse.json(response.ok?body:{available:false,model:"gpt-6-astra",provider:"OpenAI Responses API",policy:"Optional explanation only.",reason:"Explanation status is unavailable."},{status:200});
 }catch{return NextResponse.json({available:false,model:"gpt-6-astra",provider:"OpenAI Responses API",policy:"Optional explanation only.",reason:"Explanation status is unavailable."});}
}
