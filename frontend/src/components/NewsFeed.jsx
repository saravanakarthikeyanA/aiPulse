import React from "react"
import NewsCard from "./NewsCard"

function SkeletonCard() {
  return (
    <div className="bg-surface border border-border rounded-lg p-4 animate-pulse h-40" />
  )
}

export default function NewsFeed({ articles, loading }) {
  if (loading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <SkeletonCard />
        <SkeletonCard />
        <SkeletonCard />
        <SkeletonCard />
      </div>
    )
  }

  if (!articles || articles.length === 0) {
    return (
      <div className="py-12 text-center text-text-secondary">
        No articles found for this topic. Try selecting "All" or another topic.
      </div>
    )
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
      {articles.map((a, i) => (
        <NewsCard key={i} article={a} />
      ))}
    </div>
  )
}
