import fs from 'fs';
import path from 'path';
import { Post } from './postScorer.js';

// Import utility functions
import { Paths } from './utils.js';

// Path to Python backend data directory
const PYTHON_DATA_DIR = Paths.PYTHON_DATA_DIR;

export interface RawInstagramPost {
    post_id: string;
    shortcode: string;
    taken_at: string;
    media_type: string;
    like_count: number;
    comment_count: number;
    caption?: string;
    user: {
        user_id: string;
        username: string;
        full_name: string;
        profile_pic_url: string;
        is_private: boolean;
        is_verified: boolean;
        follower_count?: number;
    };
    location: any;
    images: any[];
    // Add other fields as needed
}

export interface DirectFeedResponse {
    collector_info: {
        username: string;
        user_id: string;
        session_id: string;
        started_at: string;
    };
    posts: RawInstagramPost[];
}

export class DataLoader {
    /**
     * Loads the most recent direct feed data file
     */
    public loadLatestDirectFeed(): RawInstagramPost[] {
        try {
            console.log("Starting to load latest direct feed...");
            const directFeedDir = path.join(PYTHON_DATA_DIR, 'direct_feed');
            console.log(`PYTHON_DATA_DIR: ${PYTHON_DATA_DIR}`);
            console.log(`Looking for files in: ${directFeedDir}`);

            // Check if directory exists
            if (!fs.existsSync(directFeedDir)) {
                console.error(`Directory does not exist: ${directFeedDir}`);
                throw new Error(`Directory not found: ${directFeedDir}`);
            }

            // Get all JSON files and sort by modification time (newest first)
            const allFiles = fs.readdirSync(directFeedDir);
            console.log(`All files in directory: ${allFiles.join(', ')}`);

            const files = allFiles
                .filter(file => file.endsWith('.json'))
                .map(file => path.join(directFeedDir, file))
                .sort((a, b) => {
                    return fs.statSync(b).mtime.getTime() - fs.statSync(a).mtime.getTime();
                });

            console.log(`JSON files found (sorted): ${files.map(f => path.basename(f)).join(', ')}`);

            if (files.length === 0) {
                throw new Error('No direct feed data files found');
            }

            // Read the most recent file
            const latestFile = files[0];
            console.log(`Reading feed data file: ${latestFile}`);
            const data = fs.readFileSync(latestFile, 'utf-8');
            console.log(`File size: ${data.length} bytes`);

            try {
                const feedData = JSON.parse(data) as DirectFeedResponse;
                console.log(`Posts found in file: ${feedData.posts?.length || 0}`);
                return feedData.posts;
            } catch (parseError) {
                console.error(`Error parsing JSON data: ${parseError}`);
                throw new Error(`Invalid JSON data in file: ${latestFile}`);
            }
        } catch (error) {
            console.error("ERROR IN loadLatestDirectFeed:", error);
            console.error("Stack trace:", (error as Error).stack);
            return []; // Return empty array on error
        }
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
            postId: rawPost.post_id,
            userId: rawPost.user.user_id,
            isCloseFriend: closeFriends.includes(rawPost.user.username),
            isVerified: rawPost.user.is_verified,
            caption: rawPost.caption,
            // Sum likes and comments for total engagement
            engagementCount: rawPost.like_count + rawPost.comment_count,
            // Use follower count if available, or default to a reasonable value
            followerCount: rawPost.user.follower_count || 1000,
            // Convert date string to Date object
            createdAt: new Date(rawPost.taken_at)
        };
    }
}

export default new DataLoader();