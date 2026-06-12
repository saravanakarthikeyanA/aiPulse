import React from "react"

const TOPIC_COLOR = {
  "LLM Releases": "#7C3AED",
  Research: "#0EA5E9",
  Regulation: "#F59E0B",
  Industry: "#10B981",
  Tools: "#EC4899",
}

export default function NewsCard({ article }) {
  const color = TOPIC_COLOR[article.topic] || "#6366F1"
  return (
    <article className="bg-surface border border-border rounded-lg p-4 relative overflow-hidden">
      <div style={{ position: "absolute", left: 0, top: 0, bottom: 0, width: 4, background: color, borderRadius: 4 }} />
      <h3 className="text-lg font-semibold ml-3">{article.title}</h3>
      <p className="text-text-secondary text-sm mt-2 ml-3">{article.summary}</p>
      <div className="flex items-center justify-between mt-3 ml-3">
        <span className="text-xs text-text-secondary">{article.source}</span>
        <div className="flex items-center gap-2">
          <span className="text-xs text-text-secondary">{new Date(article.timestamp).toLocaleString()}</span>
          <span className="w-2 h-2 rounded-full bg-accent-primary animate-pulse" />
        </div>
      </div>
    </article>
  )
}
