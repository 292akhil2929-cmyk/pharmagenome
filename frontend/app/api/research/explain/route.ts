import {NextResponse} from "next/server";
export const dynamic="force-dynamic";
export async function POST(request:Request){
 const base=process.env.API_BASE_URL;
 if(!base)return NextResponse.json({detail:"Research API connection is not configured."},{status:503});
 const text=await request.text();
 if(new TextEncoder().encode(text).byteLength>55000)return NextResponse.json({detail:"Explanation evidence exceeds 55 KB."},{status:413});
 let body:unknown;
 try{body=JSON.parse(text);}catch{return NextResponse.json({detail:"Request must contain valid JSON."},{status:400});}
 try{
  const response=await fetch(new URL("/api/research/explain",base),{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(body),cache:"no-store",signal:AbortSignal.timeout(60000)});
  const result=await response.json();
  return NextResponse.json(response.ok?result:{detail:typeof result.detail==="string"?result.detail:"AI explanation unavailable."},{status:response.ok?200:response.status});
 }catch{return NextResponse.json({detail:"AI explanation service unavailable."},{status:503});}
}
