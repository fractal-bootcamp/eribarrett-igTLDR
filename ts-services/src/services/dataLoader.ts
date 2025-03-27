import fs from 'fs';
import path from 'path';
import { Post } from './postScorer.js';

// Path to Python backend data directory
const PYTHON_DATA_DIR = path.resolve(import.meta.dirname, '../../../backend/data');

export interface RawInstagramPost {
    id: string;
    user_id: string;
    user: {
        is_verified: boolean;
        username: string;
        follower_count?: number;
    };
    caption?: {
        text: string;
    };
    like_count: number;
    comment_count: number;
    taken_at: number; // Unix timestamp
    // Add other fields as needed
}

export class DataLoader {
    /**
     * Loads the most recent direct feed data file
     */
    public loadLatestDirectFeed(): RawInstagramPost[] {
        const directFeedDir = path.join(PYTHON_DATA_DIR, 'direct_feed');
        
        // Get all JSON files and sort by modification time (newest first)
        const files = fs.readdirSync(directFeedDir)
            .filter(file => file.endsWith('.json'))
            .map(file => path.join(directFeedDir, file))
            .sort((a, b) => {
                return fs.statSync(b).mtime.getTime() - fs.statSync(a).mtime.getTime();
            });
            
        if (files.length === 0) {
            throw new Error('No direct feed data files found');
        }
        
        // Read the most recent file
        const latestFile = files[0];
        const data = fs.readFileSync(latestFile, 'utf-8');
        return JSON.parse(data);
    }
    
    /**
     * Get close friends data for a specific user
     */
    public getCloseFriends(username: string): string[] {
        try {
            const closeFriendsPath = path.join(
                PYTHON_DATA_DIR, 
                'userMedia', 
                username, 
                'close_friends_latest.json'
            );
            
            if (fs.existsSync(closeFriendsPath)) {
                const data = fs.readFileSync(closeFriendsPath, 'utf-8');
                return JSON.parse(data);
            }
            
            // Alternative: look for date-named files if latest doesn't exist
            const userDir = path.join(PYTHON_DATA_DIR, 'userMedia', username);
            if (fs.existsSync(userDir)) {
                const files = fs.readdirSync(userDir)
                    .filter(file => file.startsWith('close_friends_') && file.endsWith('.json'))
                    .sort()
                    .reverse();
                    
                if (files.length > 0) {
                    const data = fs.readFileSync(path.join(userDir, files[0]), 'utf-8');
                    return JSON.parse(data);
                }
            }
            
            return []; // No close friends data found
        } catch (error) {
            console.error(`Error loading close friends for ${username}:`, error);
            return [];
        }
    }
    
    /**
     * Convert raw Instagram post data to our Post format
     */
    public convertToPost(rawPost: RawInstagramPost, closeFriends: string[] = []): Post {
        return {
            postId: rawPost.id,
            userId: rawPost.user_id,
            isCloseFriend: closeFriends.includes(rawPost.user.username),
            isVerified: rawPost.user.is_verified,
            caption: rawPost.caption?.text,
            // Sum likes and comments for total engagement
            engagementCount: rawPost.like_count + rawPost.comment_count,
            // Use follower count if available, or default to a reasonable value
            followerCount: rawPost.user.follower_count || 1000,
            // Convert Unix timestamp to Date
            createdAt: new Date(rawPost.taken_at * 1000)
        };
    }
}

export default new DataLoader();