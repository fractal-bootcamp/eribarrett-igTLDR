"use client"

import type React from "react"

import { useState } from "react"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { updateSessionCookies } from "@/lib/api"
import { useToast } from "@/components/ui/use-toast"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Code } from "lucide-react"

interface CookieValues {
  csrftoken: string
  sessionid: string
}

export function CookieDialog() {
  const [open, setOpen] = useState(false)
  const [isLoading, setIsLoading] = useState(false)
  const [cookies, setCookies] = useState<CookieValues>({
    csrftoken: "",
    sessionid: "",
  })
  const { toast } = useToast()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsLoading(true)

    try {
      // Format cookies as expected by the backend
      const cookieString = `csrftoken=${cookies.csrftoken}; sessionid=${cookies.sessionid}`
      await updateSessionCookies(cookieString)

      toast({
        title: "Cookies updated",
        description: "Your Instagram session cookies have been updated successfully.",
      })
      setOpen(false)
    } catch (error) {
      toast({
        title: "Error updating cookies",
        description: "There was a problem updating your cookies. Please try again.",
        variant: "destructive",
      })
    } finally {
      setIsLoading(false)
    }
  }

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target
    setCookies((prev) => ({
      ...prev,
      [name]: value,
    }))
  }

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button variant="outline">Update Instagram Cookies</Button>
      </DialogTrigger>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle>Instagram Session Cookies</DialogTitle>
          <DialogDescription>Enter your Instagram cookies to enable data scraping</DialogDescription>
        </DialogHeader>

        <Tabs defaultValue="manual" className="mt-4">
          <TabsList className="grid w-full grid-cols-2">
            <TabsTrigger value="manual">Manual Entry</TabsTrigger>
            <TabsTrigger value="instructions">Instructions</TabsTrigger>
          </TabsList>

          <TabsContent value="manual">
            <form onSubmit={handleSubmit} className="space-y-4 py-4">
              <div className="grid gap-2">
                <Label htmlFor="csrftoken" className="text-left">
                  CSRF Token
                </Label>
                <Input
                  id="csrftoken"
                  name="csrftoken"
                  placeholder="Enter your csrftoken value"
                  value={cookies.csrftoken}
                  onChange={handleInputChange}
                  className="font-mono text-sm"
                />
              </div>

              <div className="grid gap-2">
                <Label htmlFor="sessionid" className="text-left">
                  Session ID
                </Label>
                <Input
                  id="sessionid"
                  name="sessionid"
                  placeholder="Enter your sessionid value"
                  value={cookies.sessionid}
                  onChange={handleInputChange}
                  className="font-mono text-sm"
                />
              </div>

              <DialogFooter className="mt-6">
                <Button type="submit" disabled={isLoading || !cookies.csrftoken || !cookies.sessionid}>
                  {isLoading ? "Updating..." : "Save Cookies"}
                </Button>
              </DialogFooter>
            </form>
          </TabsContent>

          <TabsContent value="instructions" className="space-y-4 py-4">
            <div className="rounded-md bg-muted p-4 space-y-3">
              <h3 className="font-medium flex items-center gap-2">
                <Code size={16} />
                How to get your Instagram cookies:
              </h3>
              <ol className="space-y-2 ml-6 list-decimal">
                <li>Log in to Instagram in your browser</li>
                <li>Open developer tools (F12 or right-click → Inspect)</li>
                <li>Go to Application tab → Cookies → instagram.com</li>
                <li>Find and copy the values for 'sessionid' and 'csrftoken'</li>
                <li>Paste them in the corresponding fields in the Manual Entry tab</li>
              </ol>
              <div className="mt-4 text-sm text-muted-foreground">
                Note: These cookies are only stored locally and used to authenticate with Instagram's API.
              </div>
            </div>

            <Button
              variant="secondary"
              className="w-full"
              onClick={() => {
                const element = document.querySelector('[data-value="manual"]');
                if (element instanceof HTMLElement) {
                  element.click();
                }
              }}
            >
              Go to Manual Entry
            </Button>
          </TabsContent>
        </Tabs>
      </DialogContent>
    </Dialog>
  )
}

