import { type NextRequest, NextResponse } from "next/server"

export async function GET(request: NextRequest) {
  // Get date from query params or use current date
  const searchParams = request.nextUrl.searchParams
  const dateParam = searchParams.get("date")
  const date = dateParam ? new Date(dateParam) : new Date()

  try {
    // In a real implementation, this would call your Python backend
    // For example:
    // const response = await fetch(`${process.env.PYTHON_API_URL}/daily-summary?date=${date.toISOString()}`);
    // const data = await response.json();

    // For now, return mock data
    const mockData = getMockData(date)

    return NextResponse.json(mockData)
  } catch (error) {
    console.error(`Error fetching daily summary:`, error)
    return NextResponse.json({ error: "Failed to fetch daily summary" }, { status: 500 })
  }
}

// Mock data function - replace with actual API call to Python backend
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

