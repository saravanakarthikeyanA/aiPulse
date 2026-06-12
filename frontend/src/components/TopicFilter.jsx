import React from "react"

const TOPICS = ["All", "LLM Releases", "Research", "Regulation", "Industry", "Tools"]

export default function TopicFilter({ value, onChange, onTopicClick }) {
  // onTopicClick(topic) will always be called on button click (useful to force-refresh same topic)
  // onChange(topic) remains for backward compatibility but may not trigger when topic is unchanged.
  const handleClick = (t) => {
    if (typeof onChange === "function") onChange(t)
    if (typeof onTopicClick === "function") onTopicClick(t)
  }

  return (
    <div className="flex gap-3 overflow-x-auto py-3 mb-4">
      {TOPICS.map((t) => (
        <button
          key={t}
          onClick={() => handleClick(t)}
          className={`whitespace-nowrap px-3 py-1 rounded-full text-sm font-medium border ${
            value === t ? "bg-accent-primary text-white" : "bg-surface text-text-secondary"
          }`}
        >
          {t}
        </button>
      ))}
    </div>
  )
}
