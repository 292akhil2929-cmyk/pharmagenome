import * as React from "react";
import {cn} from "@/lib/utils";
// Native textarea pattern adapted from the shadcn/ui registry.
export function Textarea({className,...props}:React.ComponentProps<"textarea">){
 return <textarea data-slot="textarea" className={cn("sequence-textarea",className)} {...props}/>;
}
