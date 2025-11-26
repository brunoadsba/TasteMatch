import * as React from "react"
import { cn } from "@/lib/utils"

export interface TooltipProps {
  children: React.ReactNode;
  content: string;
  side?: "top" | "bottom" | "left" | "right";
  className?: string;
}

export function Tooltip({ children, content, side = "top", className }: TooltipProps) {
  const [isVisible, setIsVisible] = React.useState(false);

  return (
    <div
      className={cn("relative inline-block", className)}
      onMouseEnter={() => setIsVisible(true)}
      onMouseLeave={() => setIsVisible(false)}
      onFocus={() => setIsVisible(true)}
      onBlur={() => setIsVisible(false)}
    >
      {children}
      {isVisible && (
        <div
          role="tooltip"
          className={cn(
            "absolute z-50 px-3 py-2 text-sm text-white bg-gray-900 rounded-md shadow-lg whitespace-normal max-w-xs",
            side === "top" && "bottom-full left-1/2 transform -translate-x-1/2 mb-2",
            side === "bottom" && "top-full left-1/2 transform -translate-x-1/2 mt-2",
            side === "left" && "right-full top-1/2 transform -translate-y-1/2 mr-2",
            side === "right" && "left-full top-1/2 transform -translate-y-1/2 ml-2"
          )}
        >
          {content}
          <div
            className={cn(
              "absolute w-2 h-2 bg-gray-900 transform rotate-45",
              side === "top" && "top-full left-1/2 -translate-x-1/2 -translate-y-1/2",
              side === "bottom" && "bottom-full left-1/2 -translate-x-1/2 translate-y-1/2",
              side === "left" && "left-full top-1/2 -translate-y-1/2 -translate-x-1/2",
              side === "right" && "right-full top-1/2 -translate-y-1/2 translate-x-1/2"
            )}
          />
        </div>
      )}
    </div>
  );
}

