"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import { api, ChatMessage, ChatResponse } from "@/lib/api";
import { Message, TypingIndicator } from "./Message";
import { ChatInput } from "./ChatInput";
import { EmptyState } from "./EmptyState";

export default function ChatInterface() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const messagesContainerRef = useRef<HTMLDivElement>(null);

  // Scroll to bottom when messages change
  const scrollToBottom = useCallback(() => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages, isLoading, scrollToBottom]);

  // Send message handler
  const sendMessage = async (content: string) => {
    if (!content.trim() || isLoading) return;

    // Clear any previous errors
    setError(null);

    // Create user message
    const userMessage: ChatMessage = {
      id: `user-${Date.now()}`,
      role: "user",
      content: content.trim(),
      timestamp: new Date(),
    };

    // Add user message to state
    setMessages((prev) => [...prev, userMessage]);
    setIsLoading(true);

    try {
      // Call API
      const response: ChatResponse = await api.chat(
        content,
        conversationId || undefined
      );

      // Create assistant message
      const assistantMessage: ChatMessage = {
        id: `assistant-${Date.now()}`,
        role: "assistant",
        content: response.response,
        sources: response.sources,
        timestamp: new Date(),
      };

      // Update state
      setMessages((prev) => [...prev, assistantMessage]);
      setConversationId(response.conversation_id);
    } catch (err) {
      console.error("Chat error:", err);
      setError(
        "Failed to get a response. Please check if the backend is running."
      );

      // Add error message
      const errorMessage: ChatMessage = {
        id: `error-${Date.now()}`,
        role: "assistant",
        content:
          "I'm sorry, I'm having trouble connecting to the server right now. Please make sure the backend is running and try again.",
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  // Handle suggestion click from empty state
  const handleSuggestionClick = (suggestion: string) => {
    sendMessage(suggestion);
  };

  // Clear conversation
  const clearConversation = () => {
    setMessages([]);
    setConversationId(null);
    setError(null);
  };

  return (
    <div className="flex flex-col h-[calc(100vh-72px)] max-w-4xl mx-auto">
      {/* Messages Area */}
      <div
        ref={messagesContainerRef}
        className="flex-1 overflow-y-auto px-4 py-6"
      >
        {messages.length === 0 ? (
          <EmptyState onSuggestionClick={handleSuggestionClick} />
        ) : (
          <div className="space-y-6">
            {messages.map((message) => (
              <Message key={message.id} message={message} />
            ))}

            {isLoading && <TypingIndicator />}

            <div ref={messagesEndRef} />
          </div>
        )}
      </div>

      {/* Error Banner */}
      {error && (
        <div className="mx-4 mb-2 px-4 py-2 bg-red-50 border border-red-200 rounded-lg text-sm text-red-600">
          {error}
        </div>
      )}

      {/* Clear Button (when there are messages) */}
      {messages.length > 0 && (
        <div className="flex justify-center pb-2">
          <button
            onClick={clearConversation}
            className="text-xs text-slate-400 hover:text-slate-600 transition-colors"
          >
            Clear conversation
          </button>
        </div>
      )}

      {/* Input Area */}
      <ChatInput onSend={sendMessage} disabled={isLoading} />
    </div>
  );
}
