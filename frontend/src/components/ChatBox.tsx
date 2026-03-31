"use client";

import React, { useState, useEffect, useRef } from "react";
import { Send, User, Bot, Key, Loader2 } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: Date;
}

export default function ChatBox() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  const handleSend = async () => {
    if (!input.trim() || isLoading) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      role: "user",
      content: input,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setIsLoading(true);

    try {
      const response = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: input }),
      });

      if (!response.ok) throw new Error("Failed to get response");

      const data = await response.json();

      const botMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: data.answer,
        timestamp: new Date(),
      };

      setMessages((prev) => [...prev, botMessage]);
    } catch (error) {
      console.error("Chat Error:", error);
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: "Lo siento, hubo un error al procesar tu solicitud. Por favor intenta de nuevo.",
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-full w-full max-w-4xl mx-auto glass shadow-2xl overflow-hidden relative border-white/10">
      {/* Header */}
      <div className="p-6 border-b border-white/10 bg-white/5 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-full bg-[#ed1c24] flex items-center justify-center shadow-lg shadow-red-500/20">
            <Key className="text-white w-6 h-6" />
          </div>
          <div>
            <h1 className="text-2xl font-black text-white tracking-tight italic">Mi Llave</h1>
            <p className="text-xs text-[#ffcb05] font-bold uppercase tracking-wider">Banco de Bogotá</p>
          </div>
        </div>
        <div className="flex gap-2">
           <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
           <span className="text-[10px] text-white/40 uppercase tracking-widest font-bold">Online</span>
        </div>
      </div>

      {/* Messages */}
      <div 
        ref={scrollRef}
        className="flex-1 overflow-y-auto p-6 space-y-6 scroll-smooth"
      >
        <AnimatePresence initial={false}>
          {messages.length === 0 && (
            <motion.div 
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="flex flex-col items-center justify-center h-full text-center space-y-4 opacity-50"
            >
              <Key className="w-16 h-16 text-[#ffcb05]" />
              <div>
                <p className="text-lg font-medium text-white">¡Hola! Soy Mi Llave, tu parcero para todo lo que necesites del Banco.</p>
                <p className="text-sm">Pregúntame sobre productos, reseñas o el documento BRE-B. ¿En qué te puedo colaborar hoy?</p>
              </div>
            </motion.div>
          )}

          {messages.map((m) => (
            <motion.div
              key={m.id}
              initial={{ opacity: 0, y: 10, scale: 0.95 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              className={cn(
                "flex w-full gap-4",
                m.role === "user" ? "flex-row-reverse" : "flex-row"
              )}
            >
              <div className={cn(
                "w-10 h-10 rounded-2xl flex items-center justify-center shrink-0 shadow-lg",
                m.role === "user" ? "bg-white/10 text-white" : "bg-[#ed1c24] text-white border border-red-500/30"
              )}>
                {m.role === "user" ? <User size={20} /> : <Key size={20} />}
              </div>
              
              <div className={cn(
                "max-w-[80%] rounded-2xl p-4 shadow-sm",
                m.role === "user" 
                  ? "bg-white/10 text-white rounded-tr-none border border-white/5" 
                  : "bg-white/20 text-white rounded-tl-none border border-white/20"
              )}>
                <p className="text-sm leading-relaxed whitespace-pre-wrap">{m.content}</p>
                <span className="text-[10px] opacity-30 mt-2 block">
                  {m.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                </span>
              </div>
            </motion.div>
          ))}

          {isLoading && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="flex gap-4"
            >
              <div className="w-10 h-10 rounded-2xl bg-[#ed1c24]/20 text-[#ffcb05] flex items-center justify-center border border-red-500/30">
                <Loader2 size={20} className="animate-spin" />
              </div>
              <div className="bg-white/10 rounded-2xl rounded-tl-none p-4 border border-white/10">
                <div className="flex gap-1">
                  <span className="w-1.5 h-1.5 bg-[#ffcb05] rounded-full animate-bounce [animation-delay:-0.3s]" />
                  <span className="w-1.5 h-1.5 bg-[#ffcb05] rounded-full animate-bounce [animation-delay:-0.15s]" />
                  <span className="w-1.5 h-1.5 bg-[#ffcb05] rounded-full animate-bounce" />
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Input */}
      <div className="p-6 bg-white/5 border-t border-white/10">
        <form 
          onSubmit={(e) => { e.preventDefault(); handleSend(); }}
          className="relative flex items-center gap-3"
        >
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="¿En qué te puedo colaborar hoy?"
            className="flex-1 bg-white/5 border border-white/10 rounded-2xl px-6 py-4 text-white placeholder:text-white/30 focus:outline-none focus:ring-2 focus:ring-[#ffcb05]/50 transition-all"
            disabled={isLoading}
          />
          <button
            type="submit"
            disabled={!input.trim() || isLoading}
            className="bg-[#ed1c24] hover:bg-[#c1121c] disabled:opacity-50 disabled:hover:bg-[#ed1c24] text-white p-4 rounded-xl shadow-lg shadow-red-600/20 transition-all active:scale-95"
          >
            <Send size={20} />
          </button>
        </form>
        <p className="text-[10px] text-center text-white/20 mt-4 uppercase tracking-[0.2em]">
          Banco de Bogotá • Mi Llave Engine • 2026
        </p>
      </div>
    </div>
  );
}
