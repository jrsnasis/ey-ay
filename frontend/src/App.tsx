import { useState, useRef, useEffect } from "react";
import {
  Card,
  CardContent,
  CardFooter,
  CardHeader,
} from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";
import { ChatMessage } from "@/components/ChatMessage";
import { TypingIndicator } from "@/components/TypingIndicator";
import { ChatInput } from "@/components/ChatInput";
import { ChatHeader } from "@/components/ChatHeader";
import { ErrorAlert } from "@/components/ErrorAlert";
import { chatApi } from "@/services/api";
import type { Message } from "@/types/chat";

function App() {
  const [messages, setMessages] = useState<Message[]>([
    {
      role: "assistant",
      content: "Hello! I'm your AI assistant. How can I help you today?",
      timestamp: new Date().toISOString(),
      intent: "greeting",
      confidence: 1.0,
    },
  ]);
  const [isTyping, setIsTyping] = useState(false);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isOnline, setIsOnline] = useState(true);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    checkHealth();
  }, []);

  useEffect(() => {
    scrollRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isTyping]);

  const checkHealth = async () => {
    try {
      await chatApi.checkHealth();
      setIsOnline(true);
    } catch (err) {
      setIsOnline(false);
      setError("Backend server is offline. Please start the FastAPI server.");
    }
  };

  const handleSend = async (message: string) => {
    const userMessage: Message = {
      role: "user",
      content: message,
      timestamp: new Date().toISOString(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setIsTyping(true);
    setError(null);

    try {
      const response = await chatApi.sendMessage({
        message: message,
        session_id: sessionId,
      });

      const botMessage: Message = {
        role: "assistant",
        content: response.message,
        timestamp: response.timestamp,
        intent: response.intent,
        confidence: response.confidence,
      };

      setSessionId(response.session_id);
      setMessages((prev) => [...prev, botMessage]);
      setIsOnline(true);
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : "An error occurred";
      console.error("Error:", err);
      setError(errorMessage);
      setIsOnline(false);

      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content:
            "Sorry, I encountered an error. Please make sure the backend server is running.",
          timestamp: new Date().toISOString(),
          intent: "error",
          confidence: 0,
        },
      ]);
    } finally {
      setIsTyping(false);
    }
  };

  return (
    <div className="flex items-center justify-center min-h-screen bg-zinc-50 p-2 sm:p-4">
      <Card className="w-full max-w-4xl h-screen sm:h-[700px] flex flex-col shadow-lg sm:rounded-lg rounded-none">
        <CardHeader className="border-b bg-white p-3 sm:p-6">
          <ChatHeader sessionId={sessionId} isOnline={isOnline} />
        </CardHeader>

        <CardContent className="flex-1 overflow-hidden p-3 sm:p-6 bg-white">
          <ErrorAlert error={error} onDismiss={() => setError(null)} />

          <ScrollArea className="h-full pr-2 sm:pr-4">
            {messages.map((message, index) => (
              <ChatMessage
                key={`${message.timestamp}-${index}`}
                message={message}
                isUser={message.role === "user"}
              />
            ))}
            {isTyping && <TypingIndicator />}
            <div ref={scrollRef} />
          </ScrollArea>
        </CardContent>

        <CardFooter className="border-t p-3 sm:p-4 bg-white">
          <ChatInput onSend={handleSend} disabled={isTyping} />
        </CardFooter>
      </Card>
    </div>
  );
}

export default App;
