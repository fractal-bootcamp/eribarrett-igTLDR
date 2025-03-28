import { type NextRequest, NextResponse } from "next/server"

export async function GET(request: NextRequest) {
  // Get date from query params or use current date
  const searchParams = request.nextUrl.searchParams
  const dateParam = searchParams.get("date")
  const date = dateParam ? new Date(dateParam) : new Date()
  const useCached = searchParams.get("cached") === "true"
  const count = searchParams.get("count") || "5"

  try {
    // Call our TypeScript service API for summaries
    const apiUrl = process.env.TS_API_URL || "http://localhost:3001"
    
    const response = await fetch(
      `${apiUrl}/api/feed/summaries?count=${count}&cached=${useCached}`, 
      { next: { revalidate: 60 } } // Revalidate every minute
    )

    if (!response.ok) {
      throw new Error(`TS API returned ${response.status}`)
    }

    const data = await response.json()
    
    // Transform the data to match our frontend format
    const transformedData = {
      date: data.date,
      highlights: data.summaries.map((summary: any, index: number) => ({
        id: summary.postId || `summary-${index}`,
        emoji: summary.emoji,
        username: summary.username,
        content: summary.actionDescription,
        topics: [
          summary.primaryCategory,
          ...(summary.secondaryCategory ? [summary.secondaryCategory] : [])
        ],
        originalScore: summary.originalScore,
        originalPriority: summary.originalPriority,
        addedToCalendar: summary.primaryCategory === "Event" || summary.secondaryCategory === "Event"
      }))
    }

    return NextResponse.json(transformedData)
  } catch (error) {
    console.error(`Error fetching daily summary:`, error)
    
    // If API call fails, fall back to mock data
    console.warn("API call failed, falling back to mock data")
    const mockData = getMockData(date)
    
    return NextResponse.json(mockData)
  }
}

// Mock data function as fallback
function getMockData(date: Date) {
  // Check if it's today or yesterday to return different data
  const isToday = new Date().toDateString() === date.toDateString()

  if (isToday) {
    return {
      date: date.toISOString(),
      highlights: [
        {
          id: "1",
          emoji: "💆‍♀️",
          username: "tinivessel",
          content: "shared a selfie that had a lot of likes",
          topics: ["Selfie", "Lifestyle"],
        },
        {
          id: "2",
          emoji: "🗞️",
          username: "sainthoax",
          content: "did a weekly recap post that featured luigi's perp walk",
          topics: ["Meme", "Entertainment"],
        },
        {
          id: "3",
          emoji: "🎸",
          username: "wildyaks",
          content: "have a show on Friday at The Venue",
          addedToCalendar: true,
          topics: ["Music", "Event"],
        },
        {
          id: "4",
          emoji: "🎨",
          username: "artdaily",
          content: "showcased a new exhibition opening next week at Modern Gallery",
          addedToCalendar: true,
          topics: ["Art", "Exhibition"],
        },
        {
          id: "5",
          emoji: "📱",
          username: "techreview",
          content: "posted an in-depth comparison of the latest smartphones",
          topics: ["Technology", "Review"],
        },
      ],
    }
  } else {
    // Yesterday's data
    return {
      date: date.toISOString(),
      highlights: [
        {
          id: "6",
          emoji: "🍕",
          username: "foodlover",
          content: "shared a recipe for homemade pizza that went viral",
          topics: ["Food", "Recipe"],
        },
        {
          id: "7",
          emoji: "📚",
          username: "bookclub",
          content: "announced their book of the month meeting on Tuesday at City Library",
          addedToCalendar: true,
          topics: ["Books", "Meeting"],
        },
        {
          id: "8",
          emoji: "🏃‍♀️",
          username: "fitnesscoach",
          content: "posted a 30-day challenge starting next Monday at 8am",
          addedToCalendar: true,
          topics: ["Fitness", "Challenge"],
        },
        {
          id: "9",
          emoji: "🎬",
          username: "moviecritic",
          content: "reviewed the latest blockbuster with behind-the-scenes info",
          topics: ["Movies", "Review"],
        },
      ],
    }
  }
}