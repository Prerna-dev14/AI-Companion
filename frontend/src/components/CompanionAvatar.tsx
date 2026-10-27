import React from "react";
import { Sparkles, HeartHandshake, Smile, Frown, Flame, HelpCircle } from "lucide-react";
import type { EmotionCategory } from "../types";

interface CompanionAvatarProps {
  emotion: EmotionCategory;
  intensity: number;
  isThinking: boolean;
}

export const CompanionAvatar: React.FC<CompanionAvatarProps> = ({
  emotion,
  intensity,
  isThinking,
}) => {
  const getEmotionDetails = () => {
    switch (emotion) {
      case "happy":
        return {
          color: "from-emerald-500 to-teal-400",
          glow: "rgba(16, 185, 129, 0.35)",
          icon: <Smile className="w-8 h-8 text-white" />,
          label: "Positive & Warm",
        };
      case "sad":
        return {
          color: "from-blue-600 to-indigo-400",
          glow: "rgba(59, 130, 246, 0.35)",
          icon: <Frown className="w-8 h-8 text-white" />,
          label: "Empathetic & Calm",
        };
      case "angry":
        return {
          color: "from-rose-600 to-orange-500",
          glow: "rgba(239, 68, 68, 0.35)",
          icon: <Flame className="w-8 h-8 text-white" />,
          label: "Calm & De-escalating",
        };
      case "bored":
        return {
          color: "from-amber-500 to-yellow-400",
          glow: "rgba(245, 158, 11, 0.35)",
          icon: <HelpCircle className="w-8 h-8 text-white" />,
          label: "Engaging & Varied",
        };
      case "neutral":
      default:
        return {
          color: "from-indigo-500 via-purple-500 to-cyan-400",
          glow: "rgba(99, 102, 241, 0.35)",
          icon: <HeartHandshake className="w-8 h-8 text-white" />,
          label: "Attentive & Balanced",
        };
    }
  };

  const details = getEmotionDetails();

  return (
    <div className="flex flex-col items-center justify-center p-6 text-center select-none">
      <div className="relative flex items-center justify-center">
        {/* Ambient Pulsing Aura */}
        <div
          className="absolute rounded-full transition-all duration-700 blur-xl"
          style={{
            width: `${120 + intensity * 40}px`,
            height: `${120 + intensity * 40}px`,
            backgroundColor: details.glow,
            transform: isThinking ? "scale(1.15)" : "scale(1)",
          }}
        />

        {/* Outer Ring */}
        <div
          className={`w-28 h-28 rounded-full p-[2px] bg-gradient-to-tr ${details.color} relative shadow-2xl transition-all duration-500`}
        >
          {/* Inner Avatar Bubble */}
          <div className="w-full h-full rounded-full bg-slate-950/90 backdrop-blur-md flex items-center justify-center">
            {isThinking ? (
              <Sparkles className="w-8 h-8 text-cyan-400 animate-spin" />
            ) : (
              details.icon
            )}
          </div>
        </div>
      </div>

      <div className="mt-4">
        <h3 className="text-sm font-semibold text-white tracking-wide flex items-center justify-center space-x-1.5">
          <span>AI Companion</span>
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
        </h3>
        <p className="text-xs text-slate-400 mt-0.5">{details.label}</p>
      </div>
    </div>
  );
};
