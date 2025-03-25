"use client"

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { CookieDialog } from "@/components/cookie-dialog"
import { Button } from "@/components/ui/button"
import { useState } from "react"
import { Shield, RefreshCw } from "lucide-react"

export function CookieManager() {
  const [lastUpdated, setLastUpdated] = useState<string | null>(null)

  // In a real app, you would fetch this from your backend
  const cookieStatus = lastUpdated ? "active" : "not set"

  return (
    <Card>
      <CardHeader>
        <CardTitle>Instagram Session</CardTitle>
        <CardDescription>Manage your Instagram session cookies for data scraping</CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        <div className="rounded-md border p-4">
          <div className="flex justify-between items-start">
            <div className="space-y-1">
              <h3 className="font-medium">Cookie Status</h3>
              <p className="text-sm text-muted-foreground">Your Instagram cookies are currently {cookieStatus}</p>
              {lastUpdated && <p className="text-xs text-muted-foreground">Last updated: {lastUpdated}</p>}
            </div>
            <div
              className={`p-2 rounded-full ${cookieStatus === "active" ? "bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400" : "bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400"}`}
            >
              <Shield size={20} />
            </div>
          </div>
        </div>

        <div className="flex flex-col gap-4 sm:flex-row">
          <CookieDialog />

          <Button variant="outline" className="flex items-center gap-2" disabled={cookieStatus !== "active"}>
            <RefreshCw size={16} />
            Refresh Session
          </Button>
        </div>

        <div className="text-sm text-muted-foreground border-t pt-4">
          <p className="mb-2">
            <strong>Privacy Note:</strong> Your Instagram session cookies are only used to fetch data from your
            Instagram feed. They are stored securely and never shared with third parties.
          </p>
          <p>Cookies expire after a certain period, so you may need to update them periodically.</p>
        </div>
      </CardContent>
    </Card>
  )
}

