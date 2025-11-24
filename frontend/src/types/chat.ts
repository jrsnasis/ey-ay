export interface Message {
  role: "user" | "assistant";
  content: string;
  timestamp: string;
  intent?: string;
  confidence?: number;
}

export interface ChatRequest {
  message: string;
  session_id?: string | null;
}

export interface ChatResponse {
  message: string;
  intent: string;
  confidence: number;
  timestamp: string;
  session_id: string;
}

export interface HealthResponse {
  status: string;
  chatbot_ready: boolean;
  timestamp: string;
}
