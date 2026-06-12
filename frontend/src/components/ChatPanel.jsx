import React, { useState } from "react"
import { chat } from "../api/client"

export default function ChatPanel({ open, onClose, history, setHistory, topic }) {
  const [input, setInput] = useState("")
  const [loading, setLoading] = useState(false)
  const [reply, setReply] = useState(null)
  const [citations, setCitations] = useState([])
  const [replyArticles, setReplyArticles] = useState(null)

  const send = async () => {
    if (!input.trim()) return
    setLoading(true)

    // Include current topic as a system message to provide context for the agent.
    const systemMsg = { role: "system", content: `topic: ${topic}` }
    const userMsg = { role: "user", content: input }

    // Build history to send: system context + existing conversation + new user message
    const sendHistory = [systemMsg, ...(history || []), userMsg]

    try {
      const res = await chat(input, sendHistory)
      // Try to detect if the assistant reply is JSON (array of articles)
      const clean = (res.reply || "").trim()
      let parsed = null
      try {
        // remove code fences if present
        const unclipped = clean.replace(/^```json\s*/i, "").replace(/```$/i, "").trim()
        parsed = JSON.parse(unclipped)
      } catch (e) {
        parsed = null
      }

      if (Array.isArray(parsed)) {
        // Render articles in the chat panel and extract sources as citations
        setReplyArticles(parsed)
        const sources = parsed.map((a) => a.source).filter(Boolean)
        setCitations(sources)
        setReply(null)
        // Persist conversation: assistant content will be a short summary text
        const assistantContent = parsed
          .slice(0, 3)
          .map((a) => `${a.title} — ${a.summary}`)
          .join("\n\n")
        setHistory([...(history || []), userMsg, { role: "assistant", content: assistantContent }])
      } else {
        setReply(res.reply)
        setCitations(res.citations || [])
        setReplyArticles(null)
        // Persist conversation in App-level history
        setHistory([...(history || []), userMsg, { role: "assistant", content: res.reply }])
      }
    } catch (e) {
      setReply("Sorry, something went wrong. Please try again.")
    } finally {
      setLoading(false)
      setInput("")
    }
  }

  return (
    <div className={`fixed top-0 right-0 h-full w-full md:w-96 bg-surface transform transition-transform ${open ? "translate-x-0" : "translate-x-full"}`}>
      <div className="p-4 border-b border-border flex items-center justify-between">
        <h2 className="font-semibold">Ask the News</h2>
        <button onClick={onClose} className="text-text-secondary">Close</button>
      </div>
      <div className="p-4 flex-1 overflow-auto">
        <div className="space-y-3">
          {(history || []).map((h, i) => (
            <div key={i} className={h.role === "user" ? "text-right" : "text-left"}>
              <div className="inline-block bg-surface p-2 rounded">{h.content}</div>
            </div>
          ))}
          {reply && (
            <div className="text-left">
              <div className="inline-block bg-surface p-2 rounded">{reply}</div>
              {citations && citations.length > 0 && (
                <div className="mt-2 text-xs text-text-secondary">
                  <div className="font-medium">Citations:</div>
                  <ul className="list-disc list-inside">
                    {citations.map((c, idx) => (
                      <li key={idx}>
                        <a className="underline" href={c} target="_blank" rel="noreferrer">
                          {c}
                        </a>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}
          {replyArticles && (
            <div className="space-y-4">
              {replyArticles.map((a, idx) => (
                <article key={idx} className="bg-surface border border-border rounded-lg p-3">
                  <h4 className="font-semibold">{a.title}</h4>
                  <p className="text-sm text-text-secondary mt-1">{a.summary}</p>
                  <div className="mt-2 text-xs text-text-secondary flex items-center justify-between">
                    <span>{a.source}</span>
                    <span>{new Date(a.timestamp).toLocaleString()}</span>
                  </div>
                </article>
              ))}
              {citations && citations.length > 0 && (
                <div className="mt-2 text-xs text-text-secondary">
                  <div className="font-medium">Citations:</div>
                  <ul className="list-disc list-inside">
                    {citations.map((c, idx) => (
                      <li key={idx}>
                        <a className="underline" href={c} target="_blank" rel="noreferrer">
                          {c}
                        </a>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
      <div className="p-4 border-t border-border">
        <div className="flex gap-2">
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            className="flex-1 px-3 py-2 rounded bg-background border border-border text-sm"
            placeholder="Ask a question about the news..."
            onKeyDown={(e) => e.key === "Enter" && send()}
          />
          <button onClick={send} disabled={loading} className="px-3 py-2 bg-accent-primary rounded text-sm">
            Send
          </button>
        </div>
      </div>
    </div>
  )
}
