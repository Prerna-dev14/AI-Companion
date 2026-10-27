import React, { useState, useRef, useEffect } from "react";
import { Send, User, Bot, Sparkles } from "lucide-react";
import type { Message, EmotionalState } from "../types";
import { formatTime, getEmotionColor } from "../utils/formatters";

interface ChatAreaProps {
  messages: Message[];
  onSendMessage: (text: string) => void;
  isGenerating: boolean;
  activeEmotion?: EmotionalState;
}

export const ChatArea: React.FC<ChatAreaProps> = ({
  messages,
  onSendMessage,
  isGenerating,
}) => {
  const [inputText, setInputText] = useState("");
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isGenerating]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputText.trim() || isGenerating) return;
    onSendMessage(inputText.trim());
    setInputText("");
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  return (
    <div className="flex-1 flex flex-col h-full overflow-hidden">
      {/* Messages Scroll Area */}
      <div className="flex-1 overflow-y-auto p-4 md:p-6 space-y-4">
        {messages.map((message) => {
          const isUser = message.role === "user";
          return (
            <div
              key={message.id}
              className={`flex items-start space-x-3 max-w-2xl ${
                isUser ? "ml-auto flex-row-reverse space-x-reverse" : "mr-auto"
              }`}
            >
              {/* Avatar Icon */}
              <div
                className={`w-8 h-8 rounded-xl flex items-center justify-center flex-shrink-0 ${
                  isUser
                    ? "bg-indigo-600 text-white shadow-md shadow-indigo-600/30"
                    : "bg-slate-800 text-cyan-400 border border-slate-700"
                }`}
              >
                {isUser ? <User className="w-4 h-4" /> : <Bot className="w-4 h-4" />}
              </div>

              {/* Message Bubble */}
              <div
                className={`rounded-2xl px-4 py-3 text-sm leading-relaxed ${
                  isUser
                    ? "bg-indigo-600 text-white rounded-tr-none shadow-lg shadow-indigo-600/20"
                    : "glass-card text-slate-200 rounded-tl-none border border-slate-800/80"
                }`}
              >
                <div className="whitespace-pre-wrap">{message.content}</div>

                {/* Metadata & Timestamp */}
                <div className="mt-1.5 flex items-center justify-end space-x-2 text-[10px] opacity-70">
                  {message.emotional_state?.dominant_emotion && (
                    <span
                      className={`capitalize px-1.5 py-0.2 rounded border ${getEmotionColor(
                        message.emotional_state.dominant_emotion
                      )}`}
                    >
                      {message.emotional_state.dominant_emotion}
                    </span>
                  )}
                  <span>{formatTime(message.timestamp)}</span>
                </div>
              </div>
            </div>
          );
        })}

        {/* Loading Indicator */}
        {isGenerating && (
          <div className="flex items-center space-x-3 mr-auto max-w-2xl">
            <div className="w-8 h-8 rounded-xl bg-slate-800 text-cyan-400 flex items-center justify-center border border-slate-700 animate-pulse">
              <Bot className="w-4 h-4" />
            </div>
            <div className="glass-card rounded-2xl rounded-tl-none px-4 py-3 text-xs text-slate-400 flex items-center space-x-2 border border-slate-800">
              <Sparkles className="w-3.5 h-3.5 text-cyan-400 animate-spin" />
              <span>AI Companion is synthesizing multimodal context...</span>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input Form Bar */}
      <div className="p-4 bg-slate-950/60 border-t border-slate-800/80">
        <form onSubmit={handleSubmit} className="relative flex items-center">
          <textarea
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Type your message to AI Companion (Phase 1 Foundation Shell)..."
            rows={1}
            className="w-full bg-slate-900/90 border border-slate-700/80 rounded-2xl pl-4 pr-24 py-3.5 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500/50 resize-none transition-all"
          />

          <div className="absolute right-2.5 flex items-center space-x-1.5">
            <button
              type="submit"
              disabled={!inputText.trim() || isGenerating}
              className={`p-2 rounded-xl transition-all ${
                inputText.trim() && !isGenerating
                  ? "bg-indigo-600 hover:bg-indigo-500 text-white shadow-md shadow-indigo-600/30"
                  : "bg-slate-800 text-slate-500 cursor-not-allowed"
              }`}
              title="Send message (Enter)"
            >
              <Send className="w-4 h-4" />
            </button>
          </div>
        </form>

        <div className="mt-2 flex items-center justify-between text-[11px] text-slate-500 px-1">
          <span className="flex items-center space-x-1">
            <span>Shift + Enter for new line</span>
          </span>
          <span className="hidden sm:inline">
            Phase 1 Foundation UI Shell &bull; Phase 2 connects live RLPI/LLM chat
          </span>
        </div>
      </div>
    </div>
  );
};
