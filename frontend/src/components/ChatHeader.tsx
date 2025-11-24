import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";
import { Bot } from "lucide-react";

interface ChatHeaderProps {
  sessionId: string | null;
  isOnline?: boolean;
}

export const ChatHeader = ({ sessionId, isOnline = true }: ChatHeaderProps) => {
  return (
    <div className="flex items-center justify-between">
      <div className="flex items-center gap-2 sm:gap-3">
        <Avatar className="h-8 w-8 sm:h-10 sm:w-10">
          <AvatarFallback className="bg-[#13294b] text-[#ffa400]">
            <Bot className="h-4 w-4 sm:h-5 sm:w-5" />
          </AvatarFallback>
        </Avatar>
        <div>
          <h2 className="text-sm sm:text-lg font-semibold text-[#13294b]">
            SFA Assistant
          </h2>
          <p className="text-[10px] sm:text-sm text-zinc-500 hidden sm:block">
            Your support companion for all SFA concerns
          </p>
        </div>
      </div>

      <div className="flex items-center gap-2 sm:gap-3">
        {sessionId && (
          <Badge
            variant="outline"
            className="text-[10px] sm:text-xs font-mono hidden sm:inline-flex"
          >
            {sessionId.slice(0, 8)}
          </Badge>
        )}
        <div className="flex items-center gap-1.5 sm:gap-2">
          <div
            className={`h-1.5 w-1.5 sm:h-2 sm:w-2 rounded-full ${
              isOnline ? "bg-green-500 animate-pulse" : "bg-red-500"
            }`}
          />
          <span className="text-[10px] sm:text-xs text-zinc-500">
            {isOnline ? "Online" : "Offline"}
          </span>
        </div>
      </div>
    </div>
  );
};
