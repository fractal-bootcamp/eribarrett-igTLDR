"use client"

import type React from "react"

import { useState, useEffect } from "react"
import { Card, CardContent } from "@/components/ui/card"
import { Calendar } from "@/components/ui/calendar"
import { fetchDailySummary } from "@/lib/api"
import { extractEventFromHighlight } from "@/lib/event-parser"
import { Badge } from "@/components/ui/badge"
import { CalendarPlus, Clock, MapPin, User } from "lucide-react"
import { Button } from "@/components/ui/button"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip"
import { useAppStore } from "@/lib/store"

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

export function CalendarView() {
  const [date, setDate] = useState<Date>(new Date())
  const [events, setEvents] = useState<Event[]>([])
  const [selectedDayEvents, setSelectedDayEvents] = useState<Event[]>([])
  const [eventDates, setEventDates] = useState<string[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [addedToCalendar, setAddedToCalendar] = useState<Record<string, boolean>>({})

  // Get events from global store
  const { events: storedEvents } = useAppStore();

  // Extract events from stored events only
  useEffect(() => {
    const loadEvents = async () => {
      setIsLoading(true)
      try {
        // Get today's and yesterday's summaries
        const today = new Date()
        
        let extractedEvents: Event[] = []
        const dates: string[] = []
        
        // Use events from the global store only
        if (storedEvents && storedEvents.length > 0) {
          // Create a map to ensure uniqueness by ID
          const eventMap = new Map<string, Event>();
          
          // Add all stored events to the map
          storedEvents.forEach(event => {
            eventMap.set(event.id, {
              ...event,
              // Add default values for any missing fields
              rawText: event.description || ''
            } as Event);
          });
          
          // Convert map back to array
          extractedEvents = Array.from(eventMap.values());
          
          // Add the dates to our dates array
          extractedEvents.forEach(event => {
            if (!dates.includes(event.date)) {
              dates.push(event.date);
            }
          });
          
          console.log('Loaded stored events:', extractedEvents.length);
        }
        
        // If we have no events from storage, add a default one for demo purposes
        if (extractedEvents.length === 0) {
          // Add a specific event for the Wild Yaks show on Friday
          const fridayDate = new Date(today)
          // Find the next Friday
          const daysUntilFriday = (5 - fridayDate.getDay() + 7) % 7
          fridayDate.setDate(fridayDate.getDate() + daysUntilFriday)
          const fridayStr = fridayDate.toISOString().split("T")[0]

          const wildYaksEvent: Event = {
            id: "wild-yaks-event",
            title: "Wild Yaks Live Show",
            date: fridayStr,
            username: "wildyaks",
            type: "Concert",
            description: "Join Wild Yaks for their album release party! Special guests and exclusive merchandise available.",
            location: "The Venue, 123 Music St, Brooklyn, NY",
            startTime: "20:00",
            endTime: "23:00",
            rawText: "have a show on Friday at The Venue",
          }

          extractedEvents.push(wildYaksEvent)
          if (!dates.includes(fridayStr)) {
            dates.push(fridayStr)
          }
        }

        setEvents(extractedEvents)
        setEventDates(dates)

        // Update selected day events
        updateSelectedDayEvents(date, extractedEvents)
      } catch (error) {
        console.error("Error loading events:", error)
        setEvents([])
        setEventDates([])
      } finally {
        setIsLoading(false)
      }
    }

    loadEvents()
  }, [storedEvents, date])

  useEffect(() => {
    if (events.length > 0) {
      updateSelectedDayEvents(date, events)
    }
  }, [date, events])

  const updateSelectedDayEvents = (selectedDate: Date, eventList: Event[]) => {
    if (!selectedDate) return

    try {
      const dateStr = selectedDate.toISOString().split("T")[0]
      const dayEvents = eventList.filter((event) => event.date === dateStr)
      setSelectedDayEvents(dayEvents)
    } catch (error) {
      console.error("Error updating selected day events:", error)
      setSelectedDayEvents([])
    }
  }

  const handleDateSelect = (newDate: Date | undefined) => {
    if (!newDate) return

    setDate(newDate)
  }

  // Function to check if a date has events
  const isDateWithEvent = (date: Date) => {
    if (!date) return false

    try {
      const dateStr = date.toISOString().split("T")[0]
      return eventDates.includes(dateStr)
    } catch (error) {
      return false
    }
  }

  // Get upcoming events (sorted by date)
  const getUpcomingEvents = () => {
    const today = new Date()
    today.setHours(0, 0, 0, 0)

    return events
      .filter((event) => {
        const eventDate = new Date(event.date)
        return eventDate >= today
      })
      .sort((a, b) => {
        return new Date(a.date).getTime() - new Date(b.date).getTime()
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

  const upcomingEvents = getUpcomingEvents()

  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
      <div className="md:col-span-1">
        <Card className="overflow-hidden">
          <CardContent className="p-4">
            <div className="flex justify-center">
              <Calendar
                mode="single"
                selected={date}
                onSelect={handleDateSelect}
                className="rounded-md w-full"
                modifiers={{
                  event: (date) => isDateWithEvent(date),
                }}
                modifiersClassNames={{
                  event:
                    "font-bold relative before:absolute before:top-1 before:right-1 before:h-2 before:w-2 before:rounded-full before:bg-primary",
                }}
              />
            </div>

            {selectedDayEvents.length > 0 && (
              <div className="mt-4 border-t pt-4">
                <h3 className="text-sm font-medium mb-2">
                  {date.toLocaleDateString(undefined, { month: "long", day: "numeric" })}
                </h3>
                <ul className="space-y-2">
                  {selectedDayEvents.map((event) => (
                    <li key={event.id} className="text-sm">
                      <div className="flex items-center justify-between gap-2">
                        <div className="flex-1 min-w-0">
                          <div className="font-medium truncate">{event.title}</div>
                          <div className="flex items-center gap-1 text-xs text-muted-foreground">
                            {event.startTime && (
                              <span className="flex items-center gap-0.5">
                                <Clock className="h-3 w-3" />
                                {event.startTime}
                              </span>
                            )}
                            {event.location && (
                              <span className="flex items-center gap-0.5 truncate">
                                <MapPin className="h-3 w-3" />
                                <span className="truncate">{event.location}</span>
                              </span>
                            )}
                          </div>
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
                            <TooltipContent side="right">
                              <p>{addedToCalendar[event.id] ? "Added to Google Calendar" : "Add to Google Calendar"}</p>
                            </TooltipContent>
                          </Tooltip>
                        </TooltipProvider>
                      </div>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      <div className="md:col-span-2">
        <Card className="h-full">
          <CardContent className="p-4 h-full">
            <h2 className="text-lg font-medium mb-4">Upcoming Events</h2>

            {upcomingEvents.length === 0 ? (
              <p className="text-sm text-muted-foreground">No upcoming events found.</p>
            ) : (
              <ScrollArea className="h-[calc(100vh-220px)]">
                <div className="space-y-6 pr-4">
                  {/* Group events by date */}
                  {(() => {
                    const groupedByDate: Record<string, Event[]> = {}
                    upcomingEvents.forEach((event) => {
                      if (!groupedByDate[event.date]) {
                        groupedByDate[event.date] = []
                      }
                      groupedByDate[event.date].push(event)
                    })

                    return Object.entries(groupedByDate).map(([date, dateEvents]) => {
                      const displayDate = new Date(date).toLocaleDateString(undefined, {
                        weekday: "long",
                        month: "long",
                        day: "numeric",
                      })

                      return (
                        <div key={date} className="space-y-2">
                          <h3 className="text-sm font-medium text-muted-foreground">{displayDate}</h3>
                          <ul className="space-y-2">
                            {dateEvents.map((event) => (
                              <li
                                key={event.id}
                                className="flex items-center gap-2 p-2 rounded-md hover:bg-muted cursor-pointer border"
                                onClick={() => setDate(new Date(event.date))}
                              >
                                <div className="flex-1 min-w-0">
                                  <div className="font-medium">{event.title}</div>
                                  <div className="flex flex-wrap items-center gap-x-3 gap-y-1 mt-1 text-xs text-muted-foreground">
                                    <span className="flex items-center gap-1">
                                      <User className="h-3 w-3" />@{event.username}
                                    </span>

                                    {event.startTime && (
                                      <span className="flex items-center gap-1">
                                        <Clock className="h-3 w-3" />
                                        {event.startTime}
                                        {event.endTime && ` - ${event.endTime}`}
                                      </span>
                                    )}

                                    {event.location && (
                                      <span className="flex items-center gap-1 truncate">
                                        <MapPin className="h-3 w-3" />
                                        <span className="truncate">{event.location}</span>
                                      </span>
                                    )}
                                  </div>

                                  {event.type && (
                                    <Badge variant="outline" className="mt-2 text-xs">
                                      {event.type}
                                    </Badge>
                                  )}
                                </div>

                                <TooltipProvider>
                                  <Tooltip>
                                    <TooltipTrigger asChild>
                                      <Button
                                        variant="ghost"
                                        size="icon"
                                        className="h-7 w-7 shrink-0"
                                        onClick={(e) => handleAddToCalendar(event, e)}
                                      >
                                        <CalendarPlus
                                          className={`h-4 w-4 ${addedToCalendar[event.id] ? "text-primary" : "text-muted-foreground"}`}
                                        />
                                      </Button>
                                    </TooltipTrigger>
                                    <TooltipContent side="left">
                                      <p>
                                        {addedToCalendar[event.id]
                                          ? "Added to Google Calendar"
                                          : "Add to Google Calendar"}
                                      </p>
                                    </TooltipContent>
                                  </Tooltip>
                                </TooltipProvider>
                              </li>
                            ))}
                          </ul>
                        </div>
                      )
                    })
                  })()}
                </div>
              </ScrollArea>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  )
}

