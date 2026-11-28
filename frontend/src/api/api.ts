import type { LessonWithWords } from "@/types/lesson"
import type { AIWordResponse, Word } from "@/types/word"
import type { LandmarkCapture } from "@/types/landmarks"

class API {
  readonly baseUrl: string

  constructor() {
    this.baseUrl = import.meta.env.VITE_API_URL ?? "http://localhost:8000"
  }

  async getLessons(): Promise<LessonWithWords[]> {
    const response = await fetch(`${this.baseUrl}/lessons`)
    if (!response.ok) {
      throw new Error(`Failed to fetch lessons: ${response.statusText}`)
    }
    return response.json()
  }

  async getLessonById(id: number): Promise<LessonWithWords> {
    const response = await fetch(`${this.baseUrl}/lessons/${id}`)
    if (!response.ok) {
      throw new Error(`Failed to fetch lesson with id ${id}: ${response.statusText}`)
    }
    return response.json()
  }

  async getWords(): Promise<Word[]> {
    const response = await fetch(`${this.baseUrl}/words`)
    if (!response.ok) {
      throw new Error(`Failed to fetch words: ${response.statusText}`)
    }
    return response.json()
  }

  async getWordById(id: number): Promise<{ word: Word }> {
    const response = await fetch(`${this.baseUrl}/words/${id}`)
    if (!response.ok) {
      throw new Error(`Failed to fetch word with id ${id}: ${response.statusText}`)
    }
    return response.json()
  }

  async tryWord(
    capture: LandmarkCapture,
    expectedWord: string,
    signal?: AbortSignal,
  ): Promise<AIWordResponse> {
    const response = await fetch(`${this.baseUrl}/ai/interrogate`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ ...capture, expected_word: expectedWord }),
      signal,
    })
    if (!response.ok) {
      const error = await response.json().catch(() => null)
      throw new Error(
        typeof error?.detail === "string"
          ? error.detail
          : "Impossible d'analyser l'enregistrement. Réessayez.",
      )
    }
    return response.json()
  }
}

export const ApiClass = new API()
