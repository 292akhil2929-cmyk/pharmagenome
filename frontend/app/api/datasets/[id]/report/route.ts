import {NextResponse} from "next/server";
export const dynamic="force-dynamic";
export async function GET(_request:Request,{params}:{params:Promise<{id:string}>}){
 const {id}=await params;
 if(!/^[1-9][0-9]*$/.test(id))return NextResponse.json({detail:"Invalid dataset identifier."},{status:400});
 const base=process.env.API_BASE_URL;
 if(!base)return NextResponse.json({detail:"API connection is not configured."},{status:503});
 try{
  const response=await fetch(new URL("/api/datasets/"+id+"/report",base),{cache:"no-store",signal:AbortSignal.timeout(12000)});
  if(!response.ok)return NextResponse.json({detail:response.status===404?"Dataset report not found.":"Report unavailable."},{status:response.status===404?404:503});
  return NextResponse.json(await response.json(),{headers:{"Cache-Control":"no-store","Content-Disposition":'attachment; filename="pharmagenome-dataset-'+id+'-report.json"'}});
 }catch{return NextResponse.json({detail:"Could not retrieve the report. Try again."},{status:503});}
}
