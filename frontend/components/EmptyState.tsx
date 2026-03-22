"use client";

import { BookOpen, Calendar, Users, Coffee } from "lucide-react";

interface EmptyStateProps {
  onSuggestionClick: (suggestion: string) => void;
}

const CATEGORIES = [
  {
    icon: BookOpen,
    title: "Courses",
    suggestions: [
      "What CS courses are offered this term?",
      "When is add/drop deadline?",
    ],
  },
  {
    icon: Calendar,
    title: "Deadlines",
    suggestions: [
      "When does reading period start?",
      "What are the final exam dates?",
    ],
  },
  {
    icon: Users,
    title: "Campus Life",
    suggestions: [
      "What clubs are there for music?",
      "How do I join intramural sports?",
    ],
  },
  {
    icon: Coffee,
    title: "Resources",
    suggestions: [
      "Library hours this week?",
      "How do I connect to Yale WiFi?",
    ],
  },
];

export function EmptyState({ onSuggestionClick }: EmptyStateProps) {
  return (
    <div className="flex flex-col items-center justify-center py-12 px-4">
      {/* Logo */}
      <div className="w-20 h-20 bg-yale-blue/10 rounded-full flex items-center justify-center mb-6">
        <span className="text-yale-blue text-3xl font-bold">B</span>
      </div>

      {/* Welcome Text */}
      <h2 className="text-2xl font-semibold text-slate-800 mb-2">
        Welcome to Boola
      </h2>
      <p className="text-slate-500 text-center max-w-md mb-8">
        Your AI assistant for all things Yale. Ask me about courses, deadlines,
        campus resources, and more.
      </p>

      {/* Suggestion Categories */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 w-full max-w-2xl">
        {CATEGORIES.map((category) => (
          <div
            key={category.title}
            className="bg-white rounded-xl border border-slate-200 p-4 shadow-sm"
          >
            <div className="flex items-center gap-2 mb-3">
              <category.icon className="w-5 h-5 text-yale-blue" />
              <h3 className="font-medium text-slate-700">{category.title}</h3>
            </div>
            <div className="space-y-2">
              {category.suggestions.map((suggestion) => (
                <button
                  key={suggestion}
                  onClick={() => onSuggestionClick(suggestion)}
                  className="w-full text-left text-sm text-slate-600 hover:text-yale-blue hover:bg-slate-50 rounded-lg px-3 py-2 transition-colors"
                >
                  {suggestion}
                </button>
              ))}
            </div>
          </div>
        ))}
      </div>

      {/* Footer Note */}
      <p className="mt-8 text-xs text-slate-400 text-center">
        Boola provides information based on indexed Yale resources.
        <br />
        Always verify important information with official sources.
      </p>
    </div>
  );
}
