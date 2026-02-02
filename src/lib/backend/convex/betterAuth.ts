import { query as convexQuery, internalQuery, internalMutation } from './_generated/server';
import { v } from 'convex/values';

// Mock session for testing - auth removed
const mockSession = {
	_creationTime: Date.now(),
	_id: 'test-session-id',
	expiresAt: new Date(Date.now() + 1000 * 60 * 60 * 24).toISOString(),
	ipAddress: '127.0.0.1',
	token: 'test-token',
	updatedAt: new Date().toISOString(),
	userAgent: 'test-agent',
	userId: 'test-user',
};

export type SessionObj = {
	_creationTime: number;
	_id: string;
	expiresAt: string;
	ipAddress: string;
	token: string;
	updatedAt: string;
	userAgent: string;
	userId: string;
};

// 1. Mock getSession (internal)
export const getSession = internalQuery({
	args: { sessionToken: v.string() },
	handler: async () => {
		return mockSession;
	}
});

// 2. Mock publicGetSession (api)
export const publicGetSession = convexQuery({
	args: {
		session_token: v.string(),
	},
	handler: async () => {
		return mockSession as SessionObj;
	},
});

// 3. Mock betterAuth object for internal use
export const betterAuth = {
	getSession: getSession,
};

// 4. Mock CRUD helpers if needed (most files use ctx.db directly but some might use these)
export const query = convexQuery;
export const insert = internalMutation;
export const update = internalMutation;
export const delete_ = internalMutation;
export const count = convexQuery;
