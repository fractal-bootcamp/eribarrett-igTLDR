// This file contains functions to parse event information from text

interface ExtractedEvent {
  id: string
  title: string
  date: string // ISO format YYYY-MM-DD
  username: string
  type?: string
  description?: string
  location?: string
  startTime?: string
  endTime?: string
  rawText: string // The original text that contained the event
}

/**
 * Parse a date reference like "on Friday" relative to a base date
 */
export function parseRelativeDate(text: string, baseDate: Date = new Date()): Date | null {
  // Clone the base date to avoid modifying the original
  const date = new Date(baseDate)

  // Reset time to midnight
  date.setHours(0, 0, 0, 0)

  // Days of the week
  const days = ["sunday", "monday", "tuesday", "wednesday", "thursday", "friday", "saturday"]

  // Match patterns like "on Friday", "this Friday", "next Friday", etc.
  const dayPattern = new RegExp(`\\b(on|this|next)\\s+(${days.join("|")})\\b`, "i")
  const dayMatch = text.match(dayPattern)

  if (dayMatch) {
    const prefix = dayMatch[1].toLowerCase() // "on", "this", or "next"
    const dayName = dayMatch[2].toLowerCase() // day of week
    const targetDay = days.indexOf(dayName)

    if (targetDay !== -1) {
      const currentDay = date.getDay()
      let daysToAdd = 0

      if (prefix === "next") {
        // "Next Friday" means the Friday of next week
        daysToAdd = 7 - currentDay + targetDay
        if (daysToAdd < 7) daysToAdd += 7
      } else {
        // "On Friday" or "this Friday" means the coming Friday
        daysToAdd = targetDay - currentDay
        if (daysToAdd <= 0) daysToAdd += 7 // If today is Friday or after, go to next week
      }

      date.setDate(date.getDate() + daysToAdd)
      return date
    }
  }

  // Match patterns like "tomorrow", "today", etc.
  if (/\btoday\b/i.test(text)) {
    return date
  }

  if (/\btomorrow\b/i.test(text)) {
    date.setDate(date.getDate() + 1)
    return date
  }

  // Match specific date patterns like "March 28", "28th of March", etc.
  const months = [
    "january",
    "february",
    "march",
    "april",
    "may",
    "june",
    "july",
    "august",
    "september",
    "october",
    "november",
    "december",
  ]
  const datePattern = new RegExp(
    `\\b(${months.join("|")})\\s+(\\d{1,2})(?:st|nd|rd|th)?\\b|\\b(\\d{1,2})(?:st|nd|rd|th)?\\s+(?:of\\s+)?(${months.join("|")})\\b`,
    "i",
  )
  const dateMatch = text.match(datePattern)

  if (dateMatch) {
    let month, day

    if (dateMatch[1] && dateMatch[2]) {
      month = months.indexOf(dateMatch[1].toLowerCase())
      day = Number.parseInt(dateMatch[2], 10)
    } else {
      month = months.indexOf(dateMatch[4].toLowerCase())
      day = Number.parseInt(dateMatch[3], 10)
    }

    if (month !== -1 && day >= 1 && day <= 31) {
      date.setMonth(month)
      date.setDate(day)

      // If the date is in the past, assume it's for next year
      if (date < baseDate) {
        date.setFullYear(date.getFullYear() + 1)
      }

      return date
    }
  }

  // Match time patterns like "at 8pm", "8:30 PM", etc.
  const timePattern = /\b(?:at\s+)?(\d{1,2})(?::(\d{2}))?\s*(am|pm|AM|PM)\b/
  const timeMatch = text.match(timePattern)

  if (timeMatch) {
    let hours = Number.parseInt(timeMatch[1], 10)
    const minutes = timeMatch[2] ? Number.parseInt(timeMatch[2], 10) : 0
    const period = timeMatch[3].toLowerCase()

    // Convert to 24-hour format
    if (period === "pm" && hours < 12) {
      hours += 12
    } else if (period === "am" && hours === 12) {
      hours = 0
    }

    date.setHours(hours, minutes)
    return date
  }

  return null
}

/**
 * Extract location information from text
 */
export function extractLocation(text: string): string | null {
  // Match patterns like "at The Venue", "at Madison Square Garden", etc.
  const locationPattern = /\bat\s+([A-Z][A-Za-z0-9\s']+(?:,\s*[A-Za-z\s]+)?)/
  const locationMatch = text.match(locationPattern)

  if (locationMatch) {
    return locationMatch[1].trim()
  }

  return null
}

/**
 * Extract event information from a highlight
 */
export function extractEventFromHighlight(
  highlight: {
    id: string
    emoji: string
    username: string
    content: string
    addedToCalendar?: boolean
    topics?: string[]
  },
  baseDate: Date = new Date(),
): ExtractedEvent | null {
  const text = highlight.content.toLowerCase()

  // Check if this highlight likely contains an event
  const eventIndicators = [
    "show",
    "concert",
    "performance",
    "gig",
    "tour",
    "festival",
    "exhibition",
    "gallery",
    "showcase",
    "opening",
    "meetup",
    "meeting",
    "conference",
    "workshop",
    "seminar",
    "party",
    "celebration",
    "launch",
    "release",
    "on friday",
    "on saturday",
    "on sunday",
    "on monday",
    "on tuesday",
    "on wednesday",
    "on thursday",
    "this friday",
    "this saturday",
    "this sunday",
    "this monday",
    "this tuesday",
    "this wednesday",
    "this thursday",
    "next friday",
    "next saturday",
    "next sunday",
    "next monday",
    "next tuesday",
    "next wednesday",
    "next thursday",
    "tomorrow",
    "tonight",
  ]

  // Check if any event indicator is present in the text
  const hasEventIndicator = eventIndicators.some((indicator) => text.includes(indicator.toLowerCase()))

  if (!hasEventIndicator && !highlight.addedToCalendar) {
    return null
  }

  // Extract date
  let eventDate = parseRelativeDate(highlight.content, baseDate)

  // If we can't determine a date but it's marked for calendar, use tomorrow as default
  if (!eventDate && highlight.addedToCalendar) {
    const tomorrow = new Date(baseDate)
    tomorrow.setDate(tomorrow.getDate() + 1)
    tomorrow.setHours(0, 0, 0, 0)
    eventDate = tomorrow
  } else if (!eventDate) {
    // If we can't determine a date and it's not marked for calendar, use a default date (next week)
    const nextWeek = new Date(baseDate)
    nextWeek.setDate(nextWeek.getDate() + 7)
    nextWeek.setHours(0, 0, 0, 0)
    eventDate = nextWeek
  }

  // Extract location
  const location = extractLocation(highlight.content)

  // Determine event type based on content and emoji
  let eventType = "Event"
  if (/\bshow|\bconcert|\bperformance|\bgig|\btour|\bfestival/i.test(highlight.content)) {
    eventType = "Concert"
  } else if (/\bexhibition|\bgallery|\bshowcase|\bopening/i.test(highlight.content)) {
    eventType = "Exhibition"
  } else if (/\bmeetup|\bmeeting|\bconference|\bworkshop|\bseminar/i.test(highlight.content)) {
    eventType = "Meeting"
  } else if (/\bparty|\bcelebration|\blaunch|\brelease/i.test(highlight.content)) {
    eventType = "Party"
  }

  // Create a title based on the content
  let title = highlight.content

  // Try to extract a more specific title
  const titlePatterns = [
    /have a ([^.!?]+) on/i,
    /attending ([^.!?]+) at/i,
    /going to ([^.!?]+) at/i,
    /announced ([^.!?]+) on/i,
    /hosting ([^.!?]+) at/i,
  ]

  for (const pattern of titlePatterns) {
    const match = highlight.content.match(pattern)
    if (match) {
      title = match[1].trim()
      break
    }
  }

  // If we couldn't extract a specific title, create one based on username and event type
  if (title === highlight.content) {
    title = `@${highlight.username}'s ${eventType}`
  }

  // Format the date as ISO string (YYYY-MM-DD)
  const dateStr = eventDate.toISOString().split("T")[0]

  return {
    id: `event-${highlight.id}`,
    title,
    date: dateStr,
    username: highlight.username,
    type: eventType,
    description: highlight.content,
    location,
    rawText: highlight.content,
  }
}

