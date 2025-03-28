'use client';

import { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { RefreshCcw, CalendarPlus, Check } from "lucide-react";
import { Button } from "@/components/ui/button";
import { extractEventFromHighlight } from "@/lib/event-parser";
import { useAppStore } from "@/lib/store";
import { toast } from "@/components/ui/use-toast";

interface SummaryItem {
  id: string;
  emoji: string;
  username: string;
  content: string;
  topics?: string[];
  addedToCalendar?: boolean;
  originalScore?: number;
  originalPriority?: string;
}

interface InstagramSummaryProps {
  initialData?: {
    date: string;
    highlights: SummaryItem[];
  };
  refreshInterval?: number; // in milliseconds
  maxItems?: number;
}

export function InstagramSummary({ 
  initialData, 
  refreshInterval = 60000, // 1 minute default refresh
  maxItems = 5 
}: InstagramSummaryProps) {
  const [summaryData, setSummaryData] = useState(initialData);
  const [loading, setLoading] = useState(!initialData);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = useState<Date>(new Date());

  async function fetchSummaryData() {
    try {
      setLoading(true);
      const response = await fetch(`/api/daily-summary?count=${maxItems}&cached=true`);
      
      if (!response.ok) {
        throw new Error(`Failed to fetch summary data: ${response.status}`);
      }
      
      const data = await response.json();
      setSummaryData(data);
      setLastUpdated(new Date());
      setError(null);
    } catch (err) {
      console.error('Error fetching summary:', err);
      setError('Failed to load the latest summaries');
    } finally {
      setLoading(false);
    }
  }

  // Initial fetch if no data provided
  useEffect(() => {
    if (!initialData) {
      fetchSummaryData();
    }
  }, [initialData]);

  // Set up refresh interval
  useEffect(() => {
    const intervalId = setInterval(() => {
      fetchSummaryData();
    }, refreshInterval);
    
    return () => clearInterval(intervalId);
  }, [refreshInterval]);

  // Function to create Google Calendar URL
  const createGoogleCalendarUrl = (event: any) => {
    try {
      const extractedEvent = extractEventFromHighlight({
        id: event.id,
        emoji: event.emoji,
        username: event.username,
        content: event.content,
        addedToCalendar: event.addedToCalendar,
        topics: event.topics
      });

      if (!extractedEvent) return '#';

      const eventDate = new Date(extractedEvent.date);
      
      // Default to 7 PM if no time specified
      let startDateTime = `${extractedEvent.date}T19:00:00`;
      let endDateTime = `${extractedEvent.date}T21:00:00`;
      
      // Format for Google Calendar
      startDateTime = startDateTime.replace(/-|:|\.\d+/g, "");
      endDateTime = endDateTime.replace(/-|:|\.\d+/g, "");
      
      const params = new URLSearchParams({
        action: 'TEMPLATE',
        text: extractedEvent.title || `Event with @${event.username}`,
        dates: `${startDateTime}/${endDateTime}`,
        details: `${event.content}\n\nPosted by @${event.username} on Instagram`,
        location: extractedEvent.location || '',
      });
      
      return `https://calendar.google.com/calendar/render?${params.toString()}`;
    } catch (error) {
      console.error('Error creating calendar URL:', error);
      return '#';
    }
  };
  
  // Access the global app store
  const { addEvent, hasEvent } = useAppStore();
  
  // Handle adding an event to calendar
  const handleAddToCalendar = (item: SummaryItem) => {
    try {
      // Get the extracted event data
      const extractedEvent = extractEventFromHighlight({
        id: item.id,
        emoji: item.emoji,
        username: item.username,
        content: item.content,
        addedToCalendar: true,
        topics: item.topics
      });
      
      if (!extractedEvent) {
        console.error('Could not extract event information');
        return;
      }
      
      // Add the event to the global store
      addEvent({
        id: `event-${item.id}`,
        title: extractedEvent.title || `Event with @${item.username}`,
        username: item.username,
        date: extractedEvent.date,
        description: item.content,
        location: extractedEvent.location || '',
      });
      
      // Show toast notification
      toast({
        title: "Event Added to Calendar",
        description: `"${extractedEvent.title || item.content}" has been added to your calendar.`,
        duration: 3000
      });
      
      // Also open Google Calendar
      const url = createGoogleCalendarUrl(item);
      window.open(url, '_blank');
    } catch (error) {
      console.error('Error adding to calendar:', error);
      toast({
        title: "Error",
        description: "Could not add event to calendar",
        variant: "destructive",
        duration: 3000
      });
    }
  };
  
  // Check if an item is already in the calendar
  const isInCalendar = (id: string): boolean => {
    return hasEvent(`event-${id}`);
  };

  const handleManualRefresh = () => {
    fetchSummaryData();
  };

  if (loading && !summaryData) {
    return (
      <Card className="w-full">
        <CardHeader>
          <CardTitle>Instagram Highlights</CardTitle>
          <CardDescription>Loading the latest posts...</CardDescription>
        </CardHeader>
        <CardContent className="flex justify-center p-6">
          <RefreshCcw className="animate-spin h-8 w-8 text-muted-foreground" />
        </CardContent>
      </Card>
    );
  }

  if (error && !summaryData) {
    return (
      <Card className="w-full">
        <CardHeader>
          <CardTitle>Instagram Highlights</CardTitle>
          <CardDescription className="text-destructive">{error}</CardDescription>
        </CardHeader>
        <CardContent className="p-6">
          <Button onClick={handleManualRefresh} variant="outline" className="w-full">
            <RefreshCcw className="mr-2 h-4 w-4" /> Retry
          </Button>
        </CardContent>
      </Card>
    );
  }

  if (!summaryData || summaryData.highlights.length === 0) {
    return (
      <Card className="w-full">
        <CardHeader>
          <CardTitle>Instagram Highlights</CardTitle>
          <CardDescription>No highlights available right now</CardDescription>
        </CardHeader>
        <CardContent className="p-6">
          <Button onClick={handleManualRefresh} variant="outline" className="w-full">
            <RefreshCcw className="mr-2 h-4 w-4" /> Refresh
          </Button>
        </CardContent>
      </Card>
    );
  }

  const formattedDate = new Date(summaryData.date).toLocaleDateString(undefined, {
    weekday: "long",
    month: "long",
    day: "numeric",
    year: "numeric",
  });

  const formattedUpdateTime = lastUpdated.toLocaleTimeString(undefined, {
    hour: '2-digit',
    minute: '2-digit'
  });

  return (
    <Card className="w-full overflow-hidden">
      <CardHeader className="pb-4">
        <div className="flex items-center justify-between">
          <div>
            <CardTitle>Instagram Highlights</CardTitle>
            <CardDescription className="mt-1">
              <span className="font-medium">{formattedDate}</span> • {summaryData.highlights.length} posts
            </CardDescription>
          </div>
          <Button 
            onClick={handleManualRefresh} 
            variant="ghost" 
            size="sm" 
            className="h-8 px-2"
            title={`Last updated: ${formattedUpdateTime}`}
          >
            <RefreshCcw className="h-4 w-4" />
          </Button>
        </div>
      </CardHeader>
      
      <CardContent className="p-4">
        <ul className="space-y-4 list-none">
          {summaryData.highlights.map((item) => (
            <li key={item.id} className="border-b pb-4 last:border-b-0 last:pb-0">
              <div className="flex gap-3">
                <div className="text-2xl leading-tight pt-1">{item.emoji}</div>
                <div className="flex-1">
                  <p className="mb-1 leading-snug">
                    <span className="font-semibold">@{item.username}</span>{' '}
                    <span>{item.content}</span>
                    
                    {(item.addedToCalendar || item.topics?.includes('Event')) && (
                      <Badge 
                        variant="secondary" 
                        className={`ml-2 cursor-pointer transition-colors ${
                          isInCalendar(item.id)
                            ? "bg-green-200 text-green-800 dark:bg-green-900 dark:text-green-100"
                            : "bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-100 hover:bg-blue-200 dark:hover:bg-blue-800"
                        }`}
                        onClick={() => handleAddToCalendar(item)}
                      >
                        {isInCalendar(item.id) ? (
                          <>
                            <Check className="h-3 w-3 mr-1" />
                            Added to Calendar
                          </>
                        ) : (
                          <>
                            <CalendarPlus className="h-3 w-3 mr-1" />
                            Add to Calendar
                          </>
                        )}
                      </Badge>
                    )}
                  </p>

                  {item.topics && item.topics.length > 0 && (
                    <div className="flex flex-wrap gap-1 mt-2">
                      {item.topics.map((topic, i) => (
                        <Badge key={i} variant="outline" className="text-xs px-2 py-0 h-5">
                          {topic}
                        </Badge>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            </li>
          ))}
        </ul>
      </CardContent>
    </Card>
  );
}