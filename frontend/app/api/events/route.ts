import { type NextRequest, NextResponse } from "next/server"

export async function GET(request: NextRequest) {
  try {
    // In a real implementation, this would call your Python backend
    // For example:
    // const response = await fetch(`${process.env.PYTHON_API_URL}/events`);
    // const data = await response.json();

    // For now, return mock data
    const mockEvents = [
      {
        id: "1",
        title: "IKEA Collaboration Launch",
        date: "2025-04-15",
        username: "design.inspiration",
        type: "Launch",
        description:
          "Join us for the launch of our new collaboration with IKEA featuring minimalist Scandinavian designs.",
        location: "IKEA Brooklyn, NY",
      },
      {
        id: "2",
        title: "Tech Conference",
        date: "2025-04-10",
        username: "tech.news",
        type: "Conference",
        description: "Annual tech conference featuring the latest innovations and industry leaders.",
        location: "Moscone Center, San Francisco",
        startTime: "09:00",
        endTime: "18:00",
      },
      {
        id: "3",
        title: "Product Launch",
        date: "2025-04-22",
        username: "tech.news",
        type: "Launch",
        description: "Exclusive product launch event for the newest smartphone models.",
        location: "Tech Hub, Seattle",
        startTime: "14:00",
        endTime: "16:00",
      },
      {
        id: "4",
        title: "Photography Workshop",
        date: "2025-04-05",
        username: "photo.daily",
        type: "Workshop",
        description: "Learn advanced photography techniques from professional photographers.",
        location: "Creative Studio, Los Angeles",
        startTime: "10:00",
        endTime: "15:00",
      },
      {
        id: "5",
        title: "Fashion Week Coverage",
        date: "2025-04-18",
        username: "fashion.trends",
        type: "Conference",
        description: "Live coverage of Fashion Week featuring upcoming designers and trends.",
        location: "Fashion District, New York",
      },
    ]

    return NextResponse.json(mockEvents)
  } catch (error) {
    console.error("Error fetching events:", error)
    return NextResponse.json({ error: "Failed to fetch events" }, { status: 500 })
  }
}

