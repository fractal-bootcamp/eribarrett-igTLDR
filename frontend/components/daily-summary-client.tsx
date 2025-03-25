'use client';

import { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { fetchDailySummary } from "@/lib/api";
import { CalendarPlus } from "lucide-react";

interface HighlightItem {
    id: string;
    emoji: string;
    username: string;
    content: string;
    addedToCalendar?: boolean;
    topics?: string[];
}

interface DailySummary {
    date: string;
    highlights: HighlightItem[];
}

interface DailySummaryClientProps {
    date?: string;
}

export function DailySummaryClient({ date }: DailySummaryClientProps) {
    const [summary, setSummary] = useState<DailySummary | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        async function loadSummary() {
            try {
                setLoading(true);
                const data = await fetchDailySummary(date);
                setSummary(data);
            } catch (err) {
                setError('Failed to load summary');
                console.error(err);
            } finally {
                setLoading(false);
            }
        }

        loadSummary();
    }, [date]);

    if (loading) {
        return (
            <Card>
                <CardHeader>
                    <CardTitle>Daily Summary</CardTitle>
                    <CardDescription>Loading summary...</CardDescription>
                </CardHeader>
            </Card>
        );
    }

    if (error || !summary) {
        return (
            <Card>
                <CardHeader>
                    <CardTitle>Daily Summary</CardTitle>
                    <CardDescription>{error || 'No data available'}</CardDescription>
                </CardHeader>
            </Card>
        );
    }

    if (summary.highlights.length === 0) {
        return (
            <Card>
                <CardHeader>
                    <CardTitle>Daily Summary</CardTitle>
                    <CardDescription>No highlights available for today</CardDescription>
                </CardHeader>
            </Card>
        );
    }

    const formattedDate = new Date(summary.date).toLocaleDateString(undefined, {
        weekday: "long",
        month: "long",
        day: "numeric",
        year: "numeric",
    });

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
    );
} 