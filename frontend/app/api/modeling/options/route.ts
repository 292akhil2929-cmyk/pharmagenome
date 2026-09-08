import {NextResponse} from "next/server";
export const dynamic="force-dynamic";
export async function GET(request:Request){
 const base=process.env.API_BASE_URL;if(!base)return NextResponse.json({detail:"API connection is not configured."},{status:503});
 const target=new URL("/api/modeling/options",base);const value=new URL(request.url).searchParams.get("dataset_id");if(value)target.searchParams.set("dataset_id",value);
 try{const response=await fetch(target,{cache:"no-store",signal:AbortSignal.timeout(20000)});
  if(!response.ok)return NextResponse.json({detail:"Modeling source unavailable."},{status:503});
  return NextResponse.json(await response.json(),{headers:{"Cache-Control":"no-store"}});}
 catch{return NextResponse.json({detail:"Modeling source unavailable."},{status:503});}
}
