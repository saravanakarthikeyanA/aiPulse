import React, { useState, useEffect } from "react"
import { fetchNews } from "./api/client"
import Header from "./components/Header"
import TopicFilter from "./components/TopicFilter"
import NewsFeed from "./components/NewsFeed"
import ChatPanel from "./components/ChatPanel"

export default function App() {
  const [topic, setTopic] = useState("All")
  const [articles, setArticles] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [chatOpen, setChatOpen] = useState(false)
  const [chatHistory, setChatHistory] = useState([])

  // Load news for a topic. Called on mount and every topic click (even if same topic).
  const loadNews = async (topicToLoad = topic) => {
    setLoading(true)
    setError(null)
    // Clear existing articles immediately to avoid showing stale content
    setArticles([])
    try {
      const res = await fetchNews(topicToLoad)
      setArticles(res.articles || [])
    } catch (e) {
      console.error(e)
      setError("Failed to load news. Please try again.")
      // Clear articles on error to avoid stale UI
      setArticles([])
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    // initial load on mount
    let mounted = true
    if (mounted) loadNews(topic)
    return () => {
      mounted = false
    }
  }, [])

  // Handler passed to TopicFilter: always triggers a fresh agent call
  const handleTopicClick = (t) => {
    setTopic(t)
    loadNews(t)
  }

  return (
    <div className="min-h-screen bg-background text-text-primary">
      <Header onOpenChat={() => setChatOpen(true)} />
      <main className="max-w-6xl mx-auto px-4 py-6">
        <TopicFilter value={topic} onChange={setTopic} onTopicClick={handleTopicClick} />
        {error && (
          <div className="mb-4 p-3 bg-red-700 text-white rounded">
            <div className="flex items-center justify-between">
              <div>{error}</div>
              <button
                onClick={() => {
                  setError(null)
                  setTopic((t) => t) // trigger refetch
                }}
                className="ml-4 underline"
              >
                Retry
              </button>
            </div>
          </div>
        )}

        <NewsFeed articles={articles} loading={loading} />
      </main>
      <ChatPanel
        open={chatOpen}
        onClose={() => setChatOpen(false)}
        history={chatHistory}
        setHistory={setChatHistory}
        topic={topic}
      />
    </div>
  )
}
