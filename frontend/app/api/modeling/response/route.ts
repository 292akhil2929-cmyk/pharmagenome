import {NextResponse} from "next/server";
export const dynamic="force-dynamic";
const allowed=new Set(["drug_id","gene","dataset_id"]);
export async function GET(request:Request){
 const base=process.env.API_BASE_URL;if(!base)return NextResponse.json({detail:"API connection is not configured."},{status:503});
 const target=new URL("/api/modeling/response",base);
 for(const [key,value] of new URL(request.url).searchParams){if(!allowed.has(key)||value.length>40)return NextResponse.json({detail:"Invalid comparison parameters."},{status:400});target.searchParams.set(key,value);}
 try{const response=await fetch(target,{cache:"no-store",signal:AbortSignal.timeout(20000)});const body=await response.json();
  return NextResponse.json(response.ok?body:{detail:typeof body.detail==="string"?body.detail:"Drug-response comparison unavailable."},{status:response.ok?200:response.status});}
 catch{return NextResponse.json({detail:"Drug-response service unavailable."},{status:503});}
}
