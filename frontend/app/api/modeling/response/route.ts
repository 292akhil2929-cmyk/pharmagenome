import {NextRequest,NextResponse} from "next/server";
const backend=process.env.BACKEND_URL||"http://localhost:8000";
export async function GET(request:NextRequest){
 try{const response=await fetch(backend+"/api/modeling/response?"+request.nextUrl.searchParams.toString(),{cache:"no-store"});
  return NextResponse.json(await response.json(),{status:response.status});}
 catch{return NextResponse.json({detail:"Drug-response service unavailable."},{status:503});}
}
