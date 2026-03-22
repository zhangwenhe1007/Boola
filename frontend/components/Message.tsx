"use client";

import { ExternalLink, User, Bot } from "lucide-react";
import { cn } from "@/lib/utils";
import type { ChatMessage } from "@/lib/api";

interface MessageProps {
  message: ChatMessage;
}

export function Message({ message }: MessageProps) {
  const isUser = message.role === "user";

  return (
    <div
      className={cn(
        "flex gap-3 animate-fade-in",
        isUser ? "flex-row-reverse" : "flex-row"
      )}
    >
      {/* Avatar */}
      <div
        className={cn(
          "flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center",
          isUser ? "bg-yale-blue text-white" : "bg-slate-200 text-slate-600"
        )}
      >
        {isUser ? <User className="w-4 h-4" /> : <Bot className="w-4 h-4" />}
      </div>

      {/* Message Content */}
      <div
        className={cn(
          "max-w-[80%] rounded-2xl px-4 py-3",
          isUser
            ? "bg-yale-blue text-white"
            : "bg-white border border-slate-200 shadow-sm"
        )}
      >
        <div className="message-content whitespace-pre-wrap">
          {message.content}
        </div>

        {/* Sources */}
        {message.sources && message.sources.length > 0 && (
          <div className="mt-3 pt-3 border-t border-slate-100">
            <p className="text-xs text-slate-500 mb-2 font-medium">Sources:</p>
            <div className="space-y-1.5">
              {message.sources.map((source, idx) => (
                <a
                  key={idx}
                  href={source.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center gap-1.5 text-xs text-yale-blue-light hover:underline group"
                >
                  <ExternalLink className="w-3 h-3 flex-shrink-0 group-hover:translate-x-0.5 transition-transform" />
                  <span className="truncate">
                    [{idx + 1}] {source.title || source.url}
                  </span>
                </a>
              ))}
            </div>
          </div>
        )}

        {/* Timestamp */}
        <div
          className={cn(
            "mt-2 text-xs",
            isUser ? "text-blue-200" : "text-slate-400"
          )}
        >
          {message.timestamp.toLocaleTimeString([], {
            hour: "2-digit",
            minute: "2-digit",
          })}
        </div>
      </div>
    </div>
  );
}

export function TypingIndicator() {
  return (
    <div className="flex gap-3 animate-fade-in">
      <div className="flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center bg-slate-200 text-slate-600">
        <Bot className="w-4 h-4" />
      </div>
      <div className="bg-white border border-slate-200 rounded-2xl shadow-sm">
        <div className="typing-indicator">
          <span></span>
          <span></span>
          <span></span>
        </div>
      </div>
    </div>
  );
}
