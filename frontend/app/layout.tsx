import type { Metadata } from "next";
import "@fontsource-variable/manrope";
import "@fontsource-variable/ibm-plex-sans";
import "@fontsource/ibm-plex-mono/400.css";
import "./globals.css";
export const metadata: Metadata = {title:"PharmaGenome — Research workspace",
 description:"A transparent foundation for reproducible genomic and pharmaceutical data analysis."};
export default function Layout({children}:{children:React.ReactNode}) {
 return <html lang="en"><body>{children}</body></html>;
}
