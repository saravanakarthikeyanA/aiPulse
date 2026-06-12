import React from "react"

export default function Header({ onOpenChat }) {
  return (
    <header className="bg-surface border-b border-border">
      <div className="max-w-6xl mx-auto px-4 py-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-accent-primary animate-pulse" />
            <h1 className="text-xl font-extrabold">AI Pulse</h1>
          </div>
          <p className="text-text-secondary text-sm">Live AI news intelligence</p>
        </div>
        <div>
          <button
            onClick={onOpenChat}
            className="px-3 py-1 bg-accent-primary hover:bg-accent-glow rounded-md text-sm font-medium"
          >
            Ask the News
          </button>
        </div>
      </div>
    </header>
  )
}
