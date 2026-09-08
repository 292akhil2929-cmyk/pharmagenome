import { NextResponse } from "next/server";
export const dynamic = "force-dynamic";
export async function GET() {
 const base = process.env.API_BASE_URL;
 if (!base) return NextResponse.json({detail:"API connection is not configured."},{status:503});
 try {
  const response = await fetch(new URL("/api/system",base),{cache:"no-store",signal:AbortSignal.timeout(12000)});
  if (!response.ok) return NextResponse.json({detail:"The research API is temporarily unavailable."},{status:503});
  return NextResponse.json(await response.json(), {headers:{"Cache-Control":"no-store"}});
 } catch {
  return NextResponse.json({detail:"Could not reach the research API. Try refreshing the connection."},{status:503});
 }
}
