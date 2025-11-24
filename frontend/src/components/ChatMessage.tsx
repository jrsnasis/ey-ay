import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";
import { Bot, User } from "lucide-react";
import type { Message } from "@/types/chat";

interface ChatMessageProps {
  message: Message;
  isUser: boolean;
}

export const ChatMessage = ({ message, isUser }: ChatMessageProps) => {
  return (
    <div
      className={`flex gap-2 sm:gap-3 mb-3 sm:mb-4 ${
        isUser ? "flex-row-reverse" : ""
      }`}
    >
      <Avatar className="h-7 w-7 sm:h-8 sm:w-8 shrink-0">
        <AvatarFallback
          className={
            isUser ? "bg-zinc-900 text-white" : "bg-white text-zinc-900 border"
          }
        >
          {isUser ? (
            <User className="h-3 w-3 sm:h-4 sm:w-4" />
          ) : (
            <Bot className="h-3 w-3 sm:h-4 sm:w-4" />
          )}
        </AvatarFallback>
      </Avatar>

      <div
        className={`flex flex-col max-w-[75%] sm:max-w-[70%] ${
          isUser ? "items-end" : "items-start"
        }`}
      >
        <div
          className={`rounded-lg px-3 py-2 sm:px-4 sm:py-2 ${
            isUser
              ? "bg-zinc-900 text-white"
              : "bg-zinc-100 text-zinc-900 border border-zinc-200"
          }`}
        >
          <p className="text-xs sm:text-sm leading-relaxed whitespace-pre-wrap wrap-break-words">
            {message.content}
          </p>
        </div>

        {message.intent && !isUser && (
          <div className="flex items-center gap-1.5 sm:gap-2 mt-1 sm:mt-1.5 px-1">
            <span className="text-[10px] sm:text-xs text-zinc-500">
              {new Date(message.timestamp).toLocaleTimeString("en-US", {
                hour: "2-digit",
                minute: "2-digit",
              })}
            </span>
            <Badge
              variant="outline"
              className="text-[10px] sm:text-xs h-4 sm:h-5 px-1.5"
            >
              {message.intent}
            </Badge>
            {message.confidence !== undefined && (
              <span className="text-[10px] sm:text-xs text-zinc-500">
                {(message.confidence * 100).toFixed(0)}%
              </span>
            )}
          </div>
        )}
      </div>
    </div>
  );
};
