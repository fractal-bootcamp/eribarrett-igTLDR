import { Suspense } from "react"
import { ThemeToggle } from "@/components/theme-toggle"
import { CookieManager } from "@/components/cookie-manager"
import { CalendarView } from "@/components/calendar-view"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Skeleton } from "@/components/ui/skeleton"
import { DailySummaryClient } from "@/components/daily-summary-client"
import { InstagramSummary } from "@/components/instagram-summary"

export default function Home() {
  return (
    <main className="min-h-screen p-4 md:p-8 bg-[hsl(var(--background))]">
      <div className="max-w-5xl mx-auto">
        <header className="flex justify-between items-center mb-8">
          <h1 className="text-3xl font-bold">Instagram TLDR</h1>
          <ThemeToggle />
        </header>

        <Tabs defaultValue="summary" className="w-full">
          {/* <TabsList className="mb-6">
            <TabsTrigger value="summary">Daily Feed</TabsTrigger> */}
          {/* <TabsTrigger value="calendar">Calendar</TabsTrigger>
            <TabsTrigger value="settings">Settings</TabsTrigger> */}
          {/* </TabsList> */}

          <TabsContent value="summary" className="space-y-6">
            <Suspense fallback={<Skeleton className="h-[400px] w-full" />}>
              <InstagramSummary refreshInterval={60000} maxItems={5} />
            </Suspense>
            <Suspense fallback={<Skeleton className="h-[400px] w-full" />}>
              <DailySummaryClient date={new Date(Date.now() - 86400000).toISOString()} />
            </Suspense>
          </TabsContent>

          {/* <TabsContent value="calendar">
            <CalendarView />
          </TabsContent>

          <TabsContent value="settings">
            <CookieManager />
          </TabsContent> */}
        </Tabs>
      </div>
    </main>
  )
}

