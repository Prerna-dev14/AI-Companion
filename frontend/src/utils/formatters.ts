export function formatTime(isoString: string): string {
  try {
    const date = new Date(isoString);
    return date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
  } catch {
    return "";
  }
}

export function formatPercentage(value: number): string {
  return `${Math.round(value * 100)}%`;
}

export function getEmotionColor(emotion: string): string {
  switch (emotion.toLowerCase()) {
    case "happy":
      return "text-emerald-400 bg-emerald-500/10 border-emerald-500/30";
    case "sad":
      return "text-blue-400 bg-blue-500/10 border-blue-500/30";
    case "angry":
      return "text-rose-400 bg-rose-500/10 border-rose-500/30";
    case "bored":
      return "text-amber-400 bg-amber-500/10 border-amber-500/30";
    case "neutral":
    default:
      return "text-indigo-400 bg-indigo-500/10 border-indigo-500/30";
  }
}
