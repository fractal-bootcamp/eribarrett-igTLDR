// This file contains the API functions to communicate with the Python backend

interface Summary {
  profileImage: string
  highlights: string[]
  events?: {
    title: string
    date: string
  }[]
  topics?: string[]
  mentions?: string[]
  followers: string
  verified?: boolean
}

interface DailySummary {
  date: string
  highlights: {
    id: string
    emoji: string
    username: string
    content: string
    addedToCalendar?: boolean
    topics?: string[]
  }[]
}

interface Event {
  id: string
  title: string
  date: string
  username: string
  type?: string
  description?: string
  location?: string
  startTime?: string
  endTime?: string
}

// Fetch summary for a specific Instagram user
export async function fetchUserSummary(username: string): Promise<Summary | null> {
  try {
    const response = await fetch(`/api/summary/${username}`)

    if (!response.ok) {
      throw new Error(`Failed to fetch summary for ${username}`)
    }

    return await response.json()
  } catch (error) {
    console.error(`Error fetching summary for ${username}:`, error)
    return null
  }
}

// Fetch daily summary across all users
export async function fetchDailySummary(date?: string): Promise<DailySummary | null> {
  try {
    const queryParams = date ? `?date=${date}` : ""
    const response = await fetch(`/api/daily-summary${queryParams}`)

    if (!response.ok) {
      throw new Error(`Failed to fetch daily summary`)
    }

    return await response.json()
  } catch (error) {
    console.error(`Error fetching daily summary:`, error)
    return null
  }
}

// Update Instagram session cookies
export async function updateSessionCookies(cookies: string): Promise<boolean> {
  try {
    const response = await fetch("/api/cookies", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ cookies }),
    })

    if (!response.ok) {
      throw new Error("Failed to update cookies")
    }

    return true
  } catch (error) {
    console.error("Error updating cookies:", error)
    throw error
  }
}

// Fetch all events from the calendar
export async function fetchEvents(): Promise<Event[]> {
  try {
    const response = await fetch("/api/events")

    if (!response.ok) {
      throw new Error("Failed to fetch events")
    }

    return await response.json()
  } catch (error) {
    console.error("Error fetching events:", error)
    return []
  }
}

