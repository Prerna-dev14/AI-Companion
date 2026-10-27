import React, { useState, useRef, useEffect } from "react";
import { Send, User, Bot, Sparkles, Volume2, Mic, Square } from "lucide-react";
import type { Message, EmotionalState } from "../types";
import { formatTime, getEmotionColor } from "../utils/formatters";

interface ChatAreaProps {
  messages: Message[];
  onSendMessage: (text: string) => void;
  isGenerating: boolean;
  activeEmotion?: EmotionalState;
  onSpeakMessage?: (text: string) => void;
  isSpeaking?: boolean;
  isRecording?: boolean;
  onStartVoiceInput?: () => void;
  onStopVoiceInput?: () => void;
  speechError?: string | null;
}

export const ChatArea: React.FC<ChatAreaProps> = ({
  messages,
  onSendMessage,
  isGenerating,
  onSpeakMessage,
  isSpeaking = false,
  isRecording = false,
  onStartVoiceInput,
  onStopVoiceInput,
  speechError,
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
                      : message.metadata_payload?.safety_triggered
                      ? "bg-slate-900/90 text-slate-200 rounded-tl-none border-2 border-rose-500/60 shadow-lg shadow-rose-950/40"
                      : "glass-card text-slate-200 rounded-tl-none border border-slate-800/80"
                  }`}
                >
                  {message.metadata_payload?.safety_triggered && (
                    <div className="mb-2.5 pb-2 border-b border-rose-500/30 flex items-center space-x-2 text-rose-400 font-semibold text-xs">
                      <span>🛡️ Immediate Crisis Support & Helplines (Free & Confidential)</span>
                    </div>
                  )}

                  <div className="whitespace-pre-wrap">{message.content}</div>

                  {message.metadata_payload?.safety_triggered && (
                    <div className="mt-3 pt-2.5 border-t border-rose-500/20 flex flex-wrap gap-2">
                      <a
                        href="tel:988"
                        className="px-2.5 py-1 rounded-lg bg-rose-500/20 border border-rose-500/40 text-rose-300 font-medium text-[11px] hover:bg-rose-500/30 transition-colors"
                      >
                        📞 Call or Text 988
                      </a>
                      <a
                        href="https://findahelpline.com"
                        target="_blank"
                        rel="noreferrer"
                        className="px-2.5 py-1 rounded-lg bg-slate-800 border border-slate-700 text-slate-300 text-[11px] hover:bg-slate-700 transition-colors"
                      >
                        🌐 International Helplines
                      </a>
                    </div>
                  )}

                  {/* Metadata & Actions */}
                  <div className="mt-2 flex items-center justify-between text-[10px] opacity-80 pt-1 border-t border-slate-700/40">
                    <div className="flex items-center space-x-2">
                      {!isUser && onSpeakMessage && (
                        <button
                          onClick={() => onSpeakMessage(message.content)}
                          className="hover:text-cyan-300 transition-colors flex items-center space-x-1"
                          title="Listen to spoken response (TTS)"
                        >
                          <Volume2 className="w-3.5 h-3.5" />
                          <span>Speak</span>
                        </button>
                      )}
                    </div>

                    <div className="flex items-center space-x-2">
                      {message.metadata_payload?.safety_triggered && (
                        <span className="px-1.5 py-0.2 rounded bg-rose-500/20 text-rose-300 border border-rose-500/30 uppercase font-mono text-[9px]">
                          Safety Grounding
                        </span>
                      )}
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
              <span>AI Companion is synthesizing conversational reply...</span>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Speech Error Banner (Graceful Degradation Notice) */}
      {speechError && (
        <div className="px-4 py-2 bg-amber-950/40 border-t border-amber-800/50 text-xs text-amber-300 flex items-center justify-between">
          <span>{speechError}</span>
        </div>
      )}

      {/* Input Form Bar */}
      <div className="p-4 bg-slate-950/60 border-t border-slate-800/80">
        <form onSubmit={handleSubmit} className="relative flex items-center">
          <textarea
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={
              isRecording
                ? "Listening to voice input... Click mic icon to finish and transcribe."
                : "Type a message or click mic for voice input..."
            }
            rows={1}
            className={`w-full bg-slate-900/90 border rounded-2xl pl-4 pr-32 py-3.5 text-sm text-slate-100 placeholder-slate-500 focus:outline-none resize-none transition-all ${
              isRecording
                ? "border-rose-500/80 ring-1 ring-rose-500/50 bg-rose-950/20"
                : "border-slate-700/80 focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500/50"
            }`}
          />

          <div className="absolute right-2.5 flex items-center space-x-1.5">
            {/* Voice Dictation Mic Button */}
            {onStartVoiceInput && onStopVoiceInput && (
              <button
                type="button"
                onClick={isRecording ? onStopVoiceInput : onStartVoiceInput}
                className={`p-2 rounded-xl transition-all ${
                  isRecording
                    ? "bg-rose-600 text-white animate-pulse shadow-md shadow-rose-600/40"
                    : "bg-slate-800/80 hover:bg-slate-700 text-slate-300 hover:text-white border border-slate-700"
                }`}
                title={isRecording ? "Stop recording and transcribe" : "Voice input (Microphone)"}
              >
                {isRecording ? <Square className="w-4 h-4 fill-white" /> : <Mic className="w-4 h-4" />}
              </button>
            )}

            {/* Send Button */}
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
            {isSpeaking && (
              <span className="ml-2 flex items-center space-x-1 text-cyan-400 font-medium">
                <Volume2 className="w-3.5 h-3.5 animate-pulse" />
                <span>Speaking response...</span>
              </span>
            )}
          </span>
          <span className="hidden sm:inline">
            Phase 3 Speech Active &bull; STT/TTS adapters with graceful text fallback
          </span>
        </div>
      </div>
    </div>
  );
};
