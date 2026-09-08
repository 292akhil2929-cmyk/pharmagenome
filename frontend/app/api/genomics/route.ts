import {NextResponse} from "next/server";
export const dynamic="force-dynamic";
const allowed=new Set(["dataset_id","study","disease","gene","chromosome","variant_type","q","min_samples","page","page_size","sort","heatmap_page"]);
export async function GET(request:Request){
 const base=process.env.API_BASE_URL;
 if(!base)return NextResponse.json({detail:"API connection is not configured."},{status:503});
 const target=new URL("/api/genomics",base);
 for(const [key,value] of new URL(request.url).searchParams){
  if(!allowed.has(key)||value.length>160)return NextResponse.json({detail:"Invalid explorer parameters."},{status:400});
  target.searchParams.set(key,value);
 }
 try{
  const response=await fetch(target,{cache:"no-store",signal:AbortSignal.timeout(20000)});
  if(!response.ok)return NextResponse.json({detail:response.status===404?"No completed genomic dataset is available.":response.status===422?"Check the selected filters and try again.":"Genomic results are temporarily unavailable."},{status:response.status===404?404:response.status===422?422:503});
  return NextResponse.json(await response.json(),{headers:{"Cache-Control":"no-store"}});
 }catch{return NextResponse.json({detail:"Could not reach genomic analysis. Try again."},{status:503});}
}
