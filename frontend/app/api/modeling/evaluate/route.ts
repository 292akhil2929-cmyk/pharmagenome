import {NextRequest,NextResponse} from "next/server";
const backend=process.env.BACKEND_URL||"http://localhost:8000";
export async function POST(request:NextRequest){
 try{const response=await fetch(backend+"/api/modeling/evaluate",{method:"POST",headers:{"Content-Type":"application/json"},body:await request.text(),cache:"no-store"});
  return NextResponse.json(await response.json(),{status:response.status});}
 catch{return NextResponse.json({detail:"Model evaluation service unavailable."},{status:503});}
}
