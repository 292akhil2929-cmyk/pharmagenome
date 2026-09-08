import {NextRequest,NextResponse} from "next/server";
const backend=process.env.BACKEND_URL||"http://localhost:8000";
export async function GET(request:NextRequest){
 const query=request.nextUrl.searchParams.toString();
 try{const response=await fetch(backend+"/api/modeling/options"+(query?"?"+query:""),{cache:"no-store"});
  return NextResponse.json(await response.json(),{status:response.status});}
 catch{return NextResponse.json({detail:"Modeling service unavailable."},{status:503});}
}
