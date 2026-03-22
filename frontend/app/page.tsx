"use client";

import { Header } from "@/components/Header";
import ChatInterface from "@/components/ChatInterface";

export default function Home() {
  return (
    <main className="min-h-screen bg-slate-50">
      <Header />
      <ChatInterface />
    </main>
  );
}
