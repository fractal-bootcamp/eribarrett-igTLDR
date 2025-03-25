import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { Badge } from "@/components/ui/badge"
import { fetchUserSummary } from "@/lib/api"

interface UserSummaryProps {
  username: string
}

export async function UserSummary({ username }: UserSummaryProps) {
  const summary = await fetchUserSummary(username)

  if (!summary) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>@{username}</CardTitle>
          <CardDescription>No summary available</CardDescription>
        </CardHeader>
      </Card>
    )
  }

  return (
    <Card className="overflow-hidden border-t-4" style={{ borderTopColor: "hsl(var(--accent))" }}>
      <CardHeader className="flex flex-row items-center gap-4 bg-accent/10">
        <Avatar className="border-2 border-accent">
          <AvatarImage src={summary.profileImage} alt={username} />
          <AvatarFallback className="bg-accent text-accent-foreground">
            {username.slice(0, 2).toUpperCase()}
          </AvatarFallback>
        </Avatar>
        <div>
          <CardTitle className="flex items-center gap-2">
            @{username}
            {summary.verified && (
              <span className="text-instagram-blue">
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" className="w-5 h-5">
                  <path
                    fillRule="evenodd"
                    d="M8.603 3.799A4.49 4.49 0 0112 2.25c1.357 0 2.573.6 3.397 1.549a4.49 4.49 0 013.498 1.307 4.491 4.491 0 011.307 3.497A4.49 4.49 0 0121.75 12a4.49 4.49 0 01-1.549 3.397 4.491 4.491 0 01-1.307 3.497 4.491 4.491 0 01-3.497 1.307A4.49 4.49 0 0112 21.75a4.49 4.49 0 01-3.397-1.549 4.49 4.49 0 01-3.498-1.306 4.491 4.491 0 01-1.307-3.498A4.49 4.49 0 012.25 12c0-1.357.6-2.573 1.549-3.397a4.49 4.49 0 011.307-3.497 4.49 4.49 0 013.497-1.307zm7.007 6.387a.75.75 0 10-1.22-.872l-3.236 4.53L9.53 12.22a.75.75 0 00-1.06 1.06l2.25 2.25a.75.75 0 001.14-.094l3.75-5.25z"
                    clipRule="evenodd"
                  />
                </svg>
              </span>
            )}
          </CardTitle>
          <CardDescription className="flex items-center gap-2">
            <span>{new Date().toLocaleDateString()}</span>
            <span className="inline-block w-2 h-2 rounded-full bg-accent"></span>
            <span>{summary.followers} followers</span>
          </CardDescription>
        </div>
      </CardHeader>
      <CardContent className="p-6">
        <div className="space-y-6">
          <div>
            <h3 className="text-lg font-medium mb-3 flex items-center">
              <span className="inline-block w-3 h-3 rounded-full bg-instagram-pink mr-2"></span>
              Today's Highlights
            </h3>
            <ul className="space-y-3 list-none pl-5">
              {summary.highlights.map((highlight, index) => (
                <li
                  key={index}
                  className="relative pl-6 before:absolute before:left-0 before:top-2 before:w-3 before:h-3 before:bg-accent/70 before:rounded-full"
                >
                  {highlight}
                </li>
              ))}
            </ul>
          </div>

          {summary.events && summary.events.length > 0 && (
            <div>
              <h3 className="text-lg font-medium mb-3 flex items-center">
                <span className="inline-block w-3 h-3 rounded-full bg-instagram-blue mr-2"></span>
                Upcoming Events
              </h3>
              <div className="flex flex-wrap gap-2">
                {summary.events.map((event, index) => (
                  <Badge key={index} className="bg-instagram-blue hover:bg-instagram-blue/80">
                    {event.title} - {new Date(event.date).toLocaleDateString()}
                  </Badge>
                ))}
              </div>
            </div>
          )}

          {summary.topics && (
            <div>
              <h3 className="text-lg font-medium mb-3 flex items-center">
                <span className="inline-block w-3 h-3 rounded-full bg-instagram-purple mr-2"></span>
                Topics
              </h3>
              <div className="flex flex-wrap gap-2">
                {summary.topics.map((topic, index) => (
                  <Badge key={index} variant="outline" className="border-instagram-purple text-instagram-purple">
                    {topic}
                  </Badge>
                ))}
              </div>
            </div>
          )}

          {summary.mentions && summary.mentions.length > 0 && (
            <div>
              <h3 className="text-lg font-medium mb-3 flex items-center">
                <span className="inline-block w-3 h-3 rounded-full bg-instagram-orange mr-2"></span>
                Mentioned Users
              </h3>
              <div className="flex flex-wrap gap-2">
                {summary.mentions.map((user, index) => (
                  <Badge key={index} className="bg-instagram-orange hover:bg-instagram-orange/80">
                    @{user}
                  </Badge>
                ))}
              </div>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  )
}

