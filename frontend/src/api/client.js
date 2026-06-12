import axios from "axios"

const api = axios.create({
  baseURL: "http://localhost:8000/api",
  timeout: 10000,
  headers: { "Content-Type": "application/json" },
})

export async function getHealth() {
  const resp = await api.get("/health")
  return resp.data
}

export async function fetchNews(topic) {
  const resp = await api.post("/news", { topic })
  return resp.data
}

export async function chat(message, history = []) {
  const resp = await api.post("/chat", { message, history })
  return resp.data
}

export default api
