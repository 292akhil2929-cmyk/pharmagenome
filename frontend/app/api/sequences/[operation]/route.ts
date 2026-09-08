import {NextResponse} from "next/server";
export const dynamic="force-dynamic";
export async function POST(request:Request,{params}:{params:Promise<{operation:string}>}){
 const {operation}=await params;
 if(operation!=="statistics"&&operation!=="align")return NextResponse.json({detail:"Unknown sequence operation."},{status:404});
 const base=process.env.API_BASE_URL;
 if(!base)return NextResponse.json({detail:"API connection is not configured."},{status:503});
 // Bound the streamed request before JSON parsing; do not trust Content-Length.
 const reader=request.body?.getReader();if(!reader)return NextResponse.json({detail:"A sequence request is required."},{status:400});
 let size=0;const chunks:Uint8Array[]=[];
 try{while(true){const {done,value}=await reader.read();if(done)break;size+=value.byteLength;if(size>250000){await reader.cancel();return NextResponse.json({detail:"Sequence request exceeds the 250 KB limit."},{status:413});}chunks.push(value);}}catch{return NextResponse.json({detail:"Could not read the sequence request."},{status:400});}
 const bytes=new Uint8Array(size);let offset=0;for(const chunk of chunks){bytes.set(chunk,offset);offset+=chunk.length;}
 let body:unknown;try{body=JSON.parse(new TextDecoder().decode(bytes));}catch{return NextResponse.json({detail:"Request must contain valid JSON."},{status:400});}
 try{
  const response=await fetch(new URL("/api/sequences/"+operation,base),{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(body),cache:"no-store",signal:AbortSignal.timeout(20000)});
  if(!response.ok){const detail=response.status===422?(await response.json()).detail:"Sequence computation is temporarily unavailable. Try again.";return NextResponse.json({detail:typeof detail==="string"?detail:"Check the sequence and scoring parameters."},{status:response.status===422?422:503});}
  return NextResponse.json(await response.json(),{headers:{"Cache-Control":"no-store"}});
 }catch{return NextResponse.json({detail:"Could not reach sequence computation. Try again."},{status:503});}
}
