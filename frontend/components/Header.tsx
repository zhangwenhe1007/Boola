"use client";

import { useState, useEffect } from "react";
import { Circle, RefreshCw } from "lucide-react";
import { api, HealthStatus } from "@/lib/api";
import { cn } from "@/lib/utils";

export function Header() {
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [checking, setChecking] = useState(false);

  const checkHealth = async () => {
    setChecking(true);
    try {
      const status = await api.health();
      setHealth(status);
    } catch {
      setHealth(null);
    } finally {
      setChecking(false);
    }
  };

  useEffect(() => {
    checkHealth();
    // Check health every 30 seconds
    const interval = setInterval(checkHealth, 30000);
    return () => clearInterval(interval);
  }, []);

  const isHealthy = health?.status === "healthy";
  const isDegraded = health?.status === "degraded";

  return (
    <header className="bg-yale-blue text-white shadow-lg">
      <div className="max-w-4xl mx-auto px-4 py-4">
        <div className="flex items-center justify-between">
          {/* Logo and Title */}
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-white rounded-full flex items-center justify-center shadow-md">
              <span className="text-yale-blue font-bold text-xl">B</span>
            </div>
            <div>
              <h1 className="text-xl font-semibold tracking-tight">Boola</h1>
              <p className="text-sm text-blue-200">Yale AI Assistant</p>
            </div>
          </div>

          {/* Status Indicator */}
          <div className="flex items-center gap-2">
            <button
              onClick={checkHealth}
              disabled={checking}
              className="p-1.5 hover:bg-white/10 rounded-full transition-colors"
              title="Refresh status"
            >
              <RefreshCw
                className={cn("w-4 h-4", checking && "animate-spin")}
              />
            </button>

            <div
              className={cn(
                "flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium",
                isHealthy && "bg-green-500/20 text-green-200",
                isDegraded && "bg-yellow-500/20 text-yellow-200",
                !health && "bg-red-500/20 text-red-200"
              )}
              title={
                health
                  ? `Database: ${health.database}, LLM: ${health.llm}`
                  : "Backend unavailable"
              }
            >
              <Circle
                className={cn(
                  "w-2 h-2 fill-current",
                  isHealthy && "text-green-400",
                  isDegraded && "text-yellow-400",
                  !health && "text-red-400"
                )}
              />
              {isHealthy ? "Online" : isDegraded ? "Degraded" : "Offline"}
            </div>
          </div>
        </div>
      </div>
    </header>
  );
}
