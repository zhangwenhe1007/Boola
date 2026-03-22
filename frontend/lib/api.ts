/**
 * API client for communicating with the Boola backend
 */

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  sources?: Source[];
  timestamp: Date;
}

export interface Source {
  url: string;
  title: string;
}

export interface ChatResponse {
  response: string;
  sources: Source[];
  conversation_id: string;
}

export interface HealthStatus {
  status: string;
  version: string;
  database: string;
  llm: string;
}

export interface Stats {
  total_documents: number;
  total_chunks: number;
  status: string;
}

class ApiClient {
  private baseUrl: string;

  constructor(baseUrl: string = API_URL) {
    this.baseUrl = baseUrl;
  }

  /**
   * Send a chat message and get a response
   */
  async chat(
    message: string,
    conversationId?: string,
    siteFilter?: string
  ): Promise<ChatResponse> {
    const response = await fetch(`${this.baseUrl}/chat`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        message,
        conversation_id: conversationId,
        site_filter: siteFilter,
      }),
    });

    if (!response.ok) {
      throw new Error(`Chat request failed: ${response.statusText}`);
    }

    return response.json();
  }

  /**
   * Check backend health status
   */
  async health(): Promise<HealthStatus> {
    const response = await fetch(`${this.baseUrl}/health`);

    if (!response.ok) {
      throw new Error(`Health check failed: ${response.statusText}`);
    }

    return response.json();
  }

  /**
   * Get indexing statistics
   */
  async stats(): Promise<Stats> {
    const response = await fetch(`${this.baseUrl}/stats`);

    if (!response.ok) {
      throw new Error(`Stats request failed: ${response.statusText}`);
    }

    return response.json();
  }
}

// Export singleton instance
export const api = new ApiClient();

// Export class for custom instances
export { ApiClient };
