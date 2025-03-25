import { type NextRequest, NextResponse } from "next/server"

// This is a mock API endpoint that would connect to your Python backend
export async function GET(request: NextRequest, { params }: { params: { username: string } }) {
  const username = params.username

  try {
    // In a real implementation, this would call your Python backend
    // For example:
    // const response = await fetch(`${process.env.PYTHON_API_URL}/summary/${username}`);
    // const data = await response.json();

    // For now, return mock data
    const mockData = getMockData(username)

    return NextResponse.json(mockData)
  } catch (error) {
    console.error(`Error fetching summary for ${username}:`, error)
    return NextResponse.json({ error: "Failed to fetch summary" }, { status: 500 })
  }
}

// Mock data function - replace with actual API call to Python backend
function getMockData(username: string) {
  // This is just for demonstration
  if (username === "design.inspiration") {
    return {
      profileImage: "/placeholder.svg?height=100&width=100",
      highlights: [
        "Shared 3 new minimalist interior designs featuring Scandinavian influences with @nordic.design",
        "Story highlighted an upcoming collaboration with @ikea launching next month",
        "Posted a reel about sustainable materials that received 50k+ views",
        "Shared a tutorial on color palette selection with @color.expert",
        "Announced a design workshop in collaboration with @creative.minds",
      ],
      events: [
        { title: "IKEA Collaboration Launch", date: "2025-04-15", type: "Launch" },
        { title: "Design Workshop", date: "2025-04-28", type: "Workshop" },
      ],
      topics: ["Interior Design", "Minimalism", "Scandinavian"],
      mentions: ["ikea", "nordic.design", "color.expert", "creative.minds"],
      followers: "245K",
      verified: true,
    }
  } else if (username === "tech.news") {
    return {
      profileImage: "/placeholder.svg?height=100&width=100",
      highlights: [
        "Covered the latest smartphone releases from @apple and @samsung",
        "Compared battery performance across models with detailed benchmarks",
        "Shared an exclusive interview with @startup.founder about AI innovations",
        "Posted about upcoming tech legislation with insights from @tech.lawyer",
        "Reviewed the new VR headset from @meta with comparison to competitors",
        "Analyzed the impact of recent chip shortages on @nvidia and @amd products",
      ],
      events: [
        { title: "Tech Conference", date: "2025-04-10", type: "Conference" },
        { title: "Product Launch", date: "2025-04-22", type: "Launch" },
        { title: "Developer Meetup", date: "2025-04-10", type: "Meetup" },
      ],
      topics: ["Technology", "Smartphones", "Startups", "AI"],
      mentions: ["apple", "samsung", "startup.founder", "tech.lawyer", "meta", "nvidia", "amd"],
      followers: "1.2M",
      verified: true,
    }
  } else {
    return {
      profileImage: "/placeholder.svg?height=100&width=100",
      highlights: [`No recent updates from @${username}`, `Check back tomorrow for new content`],
      topics: ["Instagram", "Social Media"],
      followers: "10K",
      verified: false,
    }
  }
}

