"use client"

import type React from "react"

import { useState } from "react"
import { CalendarPlus, Clock, MapPin } from "lucide-react"
import { Button } from "@/components/ui/button"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip"
import { EventCard } from "./event-card"

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

interface UpcomingEventsProps {
  events: Event[]
  onSelectDate: (date: string) => void
  expanded?: boolean
}

export function UpcomingEvents({ events, onSelectDate, expanded = false }: UpcomingEventsProps) {
  const [addedToCalendar, setAddedToCalendar] = useState<Record<string, boolean>>({})

  if (events.length === 0) {
    return <p className="text-sm text-muted-foreground">No upcoming events found.</p>
  }

  // Format date for display
  const formatDate = (dateString: string) => {
    const date = new Date(dateString)
    return date.toLocaleDateString(undefined, {
      month: "short",
      day: "numeric",
    })
  }

  // Create Google Calendar URL
  const createGoogleCalendarUrl = (event: Event) => {
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

  const handleAddToCalendar = (event: Event, e: React.MouseEvent) => {
    e.stopPropagation()
    window.open(createGoogleCalendarUrl(event), "_blank")
    setAddedToCalendar((prev) => ({ ...prev, [event.id]: true }))
  }

  // Group events by date
  const groupedByDate: Record<string, Event[]> = {}
  events.forEach((event) => {
    if (!groupedByDate[event.date]) {
      groupedByDate[event.date] = []
    }
    groupedByDate[event.date].push(event)
  })

  if (expanded) {
    return (
      <div className="space-y-6">
        {Object.entries(groupedByDate).map(([date, dateEvents]) => {
          const displayDate = new Date(date).toLocaleDateString(undefined, {
            weekday: "long",
            month: "long",
            day: "numeric",
            year: "numeric",
          })

          return (
            <div key={date} className="space-y-3">
              <h3 className="text-md font-medium">{displayDate}</h3>
              <div className="grid grid-cols-1 gap-3">
                {dateEvents.map((event) => (
                  <EventCard key={event.id} event={event} compact />
                ))}
              </div>
            </div>
          )
        })}
      </div>
    )
  }

  return (
    <ScrollArea className="h-[200px] rounded-md border">
      <div className="p-2">
        {events.map((event) => (
          <div
            key={event.id}
            className="flex items-center gap-2 p-2 rounded-md hover:bg-muted cursor-pointer mb-1 last:mb-0"
            onClick={() => onSelectDate(event.date)}
          >
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-1">
                <span className="text-xs font-medium">{formatDate(event.date)}</span>
                {event.startTime && (
                  <>
                    <Clock className="h-3 w-3 text-muted-foreground" />
                    <span className="text-xs text-muted-foreground">{event.startTime}</span>
                  </>
                )}
              </div>
              <div className="truncate text-sm font-medium">{event.title}</div>
              {event.location && (
                <div className="flex items-center gap-1 text-xs text-muted-foreground truncate">
                  <MapPin className="h-3 w-3" />
                  <span>{event.location}</span>
                </div>
              )}
            </div>
            <TooltipProvider>
              <Tooltip>
                <TooltipTrigger asChild>
                  <Button
                    variant="ghost"
                    size="icon"
                    className="h-6 w-6 shrink-0"
                    onClick={(e) => handleAddToCalendar(event, e)}
                  >
                    <CalendarPlus
                      className={`h-4 w-4 ${addedToCalendar[event.id] ? "text-primary" : "text-muted-foreground"}`}
                    />
                  </Button>
                </TooltipTrigger>
                <TooltipContent side="left">
                  <p>{addedToCalendar[event.id] ? "Added to Google Calendar" : "Add to Google Calendar"}</p>
                </TooltipContent>
              </Tooltip>
            </TooltipProvider>
          </div>
        ))}
      </div>
    </ScrollArea>
  )
}

