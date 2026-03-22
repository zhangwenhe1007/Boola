"use client";

import { useState, useRef, useEffect } from "react";
import { Send, Sparkles } from "lucide-react";
import { cn } from "@/lib/utils";

interface ChatInputProps {
  onSend: (message: string) => void;
  disabled?: boolean;
  placeholder?: string;
}

export function ChatInput({
  onSend,
  disabled = false,
  placeholder = "Ask about courses, clubs, deadlines...",
}: ChatInputProps) {
  const [input, setInput] = useState("");
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
      textareaRef.current.style.height = `${Math.min(
        textareaRef.current.scrollHeight,
        200
      )}px`;
    }
  }, [input]);

  const handleSubmit = () => {
    if (!input.trim() || disabled) return;
    onSend(input.trim());
    setInput("");
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  return (
    <div className="relative flex items-end gap-2 p-4 bg-white border-t border-slate-200">
      <div className="flex-1 relative">
        <textarea
          ref={textareaRef}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={placeholder}
          disabled={disabled}
          rows={1}
          className={cn(
            "w-full resize-none rounded-xl border border-slate-300 px-4 py-3 pr-12",
            "focus:outline-none focus:ring-2 focus:ring-yale-blue/50 focus:border-yale-blue",
            "placeholder:text-slate-400 text-slate-700",
            "disabled:opacity-50 disabled:cursor-not-allowed",
            "transition-all duration-200"
          )}
        />
        <div className="absolute right-3 bottom-3 text-xs text-slate-400">
          {input.length > 0 && `${input.length}`}
        </div>
      </div>

      <button
        onClick={handleSubmit}
        disabled={!input.trim() || disabled}
        className={cn(
          "flex-shrink-0 p-3 rounded-xl transition-all duration-200",
          "bg-yale-blue text-white hover:bg-yale-blue-light",
          "disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:bg-yale-blue",
          "focus:outline-none focus:ring-2 focus:ring-yale-blue/50 focus:ring-offset-2"
        )}
      >
        <Send className="w-5 h-5" />
      </button>
    </div>
  );
}

interface SuggestionChipsProps {
  suggestions: string[];
  onSelect: (suggestion: string) => void;
}

export function SuggestionChips({ suggestions, onSelect }: SuggestionChipsProps) {
  return (
    <div className="flex flex-wrap justify-center gap-2 px-4">
      {suggestions.map((suggestion) => (
        <button
          key={suggestion}
          onClick={() => onSelect(suggestion)}
          className={cn(
            "inline-flex items-center gap-1.5 px-3 py-1.5 text-sm",
            "bg-white border border-slate-200 rounded-full",
            "hover:bg-slate-50 hover:border-slate-300",
            "transition-all duration-200",
            "text-slate-600 hover:text-slate-900"
          )}
        >
          <Sparkles className="w-3 h-3 text-yale-blue" />
          {suggestion}
        </button>
      ))}
    </div>
  );
}
