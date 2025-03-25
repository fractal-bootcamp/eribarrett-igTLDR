import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { fetchDailySummary } from "@/lib/api"
import { CalendarPlus } from "lucide-react"

interface HighlightItem {
  id: string
  emoji: string
  username: string
  content: string
  addedToCalendar?: boolean
  date: string
  topics?: string[]
}

interface DailySummaryProps {
  date?: string
}

export async function DailySummary({ date }: DailySummaryProps) {
  const summary = await fetchDailySummary(date)

  if (!summary || summary.highlights.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Daily Summary</CardTitle>
          <CardDescription>No highlights available for today</CardDescription>
        </CardHeader>
      </Card>
    )
  }

  const formattedDate = new Date(summary.date).toLocaleDateString(undefined, {
    weekday: "long",
    month: "long",
    day: "numeric",
    year: "numeric",
  })

  return (
    <Card className="overflow-hidden">
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle>{formattedDate}</CardTitle>
            <CardDescription>{summary.highlights.length} highlights from your feed</CardDescription>
          </div>
        </div>
      </CardHeader>
      <CardContent className="p-6">
        <ul className="space-y-5 list-none">
          {summary.highlights.map((highlight) => (
            <li key={highlight.id} className="border-b pb-5 last:border-b-0 last:pb-0">
              <div className="flex gap-3">
                <div className="text-2xl">{highlight.emoji}</div>
                <div className="flex-1">
                  <p className="mb-2">
                    <span className="font-medium">@{highlight.username}</span> {highlight.content}
                    {highlight.addedToCalendar && (
                      <Badge className="ml-2">
                        <CalendarPlus className="h-3 w-3 mr-1" />
                        Added to Calendar
                      </Badge>
                    )}
                  </p>

                  {highlight.topics && highlight.topics.length > 0 && (
                    <div className="flex flex-wrap gap-1 mt-2">
                      {highlight.topics.map((topic, i) => (
                        <Badge key={i} variant="outline" className="text-xs">
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
  )
}

