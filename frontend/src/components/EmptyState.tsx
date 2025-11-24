import { MessageSquare } from "lucide-react";

export const EmptyState = () => {
  return (
    <div className="flex flex-col items-center justify-center h-full text-center p-8">
      <MessageSquare className="h-16 w-16 text-zinc-300 mb-4" />
      <h3 className="text-lg font-semibold text-zinc-900 mb-2">
        Start a conversation
      </h3>
      <p className="text-sm text-zinc-500 max-w-sm">
        Ask me anything! I'm here to help you with your questions.
      </p>
    </div>
  );
};
