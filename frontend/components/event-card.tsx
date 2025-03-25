"use client"

import { Button } from "@/components/ui/button"
import { Card, CardContent, CardFooter } from "@/components/ui/card"
import { CalendarIcon, Clock, MapPin, User, MessageSquare } from "lucide-react"
import { useState } from "react"

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
  rawText?: string
}

interface EventCardProps {
  event: Event
  compact?: boolean
}

export function EventCard({ event, compact = false }: EventCardProps) {
  const [isAdded, setIsAdded] = useState(false)

  // Format the date for display
  const formatDate = (dateString: string) => {
    const date = new Date(dateString)
    return date.toLocaleDateString(undefined, {
      weekday: "long",
      month: "long",
      day: "numeric",
      year: "numeric",
    })
  }

  // Create Google Calendar URL
  const createGoogleCalendarUrl = () => {
    const eventDate = new Date(event.date)

    // Format start and end times
    let startDateTime, endDateTime

    if (event.startTime) {
      const [startHours, startMinutes] = event.startTime.split(":").map(Number)
      eventDate.setHours(startHours, startMinutes)
      startDateTime = eventDate.toISOString().replace(/-|:|\.\d+/g, "")

      // If end time is provided, use it; otherwise, add 1 hour to start time
      if (event.endTime) {
        const endDate = new Date(eventDate)
        const [endHours, endMinutes] = event.endTime.split(":").map(Number)
        endDate.setHours(endHours, endMinutes)
        endDateTime = endDate.toISOString().replace(/-|:|\.\d+/g, "")
      } else {
        const endDate = new Date(eventDate)
        endDate.setHours(endDate.getHours() + 1)
        endDateTime = endDate.toISOString().replace(/-|:|\.\d+/g, "")
      }
    } else {
      // If no start time, set to all day event
      startDateTime = eventDate.toISOString().split("T")[0].replace(/-/g, "")
      const endDate = new Date(eventDate)
      endDate.setDate(endDate.getDate() + 1)
      endDateTime = endDate.toISOString().split("T")[0].replace(/-/g, "")
    }

    const params = new URLSearchParams({
      action: "TEMPLATE",
      text: event.title,
      dates: `${startDateTime}/${endDateTime}`,
      details: `${event.description || ""}\n\nPosted by @${event.username} on Instagram`,
      location: event.location || "",
    })

    return `https://calendar.google.com/calendar/render?${params.toString()}`
  }

  const handleAddToCalendar = () => {
    window.open(createGoogleCalendarUrl(), "_blank")
    setIsAdded(true)
  }

  if (compact) {
    return (
      <div className="border rounded-md p-3 bg-card hover:bg-muted/50 transition-colors">
        <div className="flex justify-between items-start gap-2">
          <div className="flex-1 min-w-0">
            <h4 className="text-sm font-medium truncate">{event.title}</h4>
            <div className="flex items-center gap-2 mt-1 text-xs text-muted-foreground">
              {event.startTime && (
                <div className="flex items-center gap-1">
                  <Clock className="h-3 w-3" />
                  <span>{event.startTime}</span>
                </div>
              )}
              {event.location && (
                <div className="flex items-center gap-1 truncate">
                  <MapPin className="h-3 w-3" />
                  <span className="truncate">{event.location}</span>
                </div>
              )}
            </div>
          </div>
          <Button variant="ghost" size="icon" className="h-6 w-6 shrink-0" onClick={handleAddToCalendar}>
            <CalendarIcon className={`h-4 w-4 ${isAdded ? "text-primary" : "text-muted-foreground"}`} />
          </Button>
        </div>
      </div>
    )
  }

  return (
    <Card className="overflow-hidden">
      <CardContent className="p-6">
        <h4 className="text-lg font-medium mb-4">{event.title}</h4>

        {event.description && <p className="text-sm text-muted-foreground mb-4">{event.description}</p>}

        <div className="space-y-2 text-sm">
          <div className="flex items-center gap-2">
            <CalendarIcon className="h-4 w-4 text-muted-foreground" />
            <span>{formatDate(event.date)}</span>
          </div>

          {(event.startTime || event.endTime) && (
            <div className="flex items-center gap-2">
              <Clock className="h-4 w-4 text-muted-foreground" />
              <span>
                {event.startTime && `${event.startTime}`}
                {event.startTime && event.endTime && " - "}
                {event.endTime && `${event.endTime}`}
              </span>
            </div>
          )}

          {event.location && (
            <div className="flex items-center gap-2">
              <MapPin className="h-4 w-4 text-muted-foreground" />
              <span>{event.location}</span>
            </div>
          )}

          <div className="flex items-center gap-2">
            <User className="h-4 w-4 text-muted-foreground" />
            <span>@{event.username}</span>
          </div>

          {event.rawText && (
            <div className="flex items-center gap-2 mt-2 pt-2 border-t">
              <MessageSquare className="h-4 w-4 text-muted-foreground" />
              <span className="italic text-muted-foreground">"{event.rawText}"</span>
            </div>
          )}
        </div>
      </CardContent>

      <CardFooter className="px-6 py-4 bg-muted/50">
        <Button variant={isAdded ? "secondary" : "default"} className="w-full" onClick={handleAddToCalendar}>
          {isAdded ? "Added to Google Calendar" : "Add to Google Calendar"}
        </Button>
      </CardFooter>
    </Card>
  )
}

