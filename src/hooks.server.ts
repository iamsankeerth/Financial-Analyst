// Auth removed - using mock auth for testing
import type { Handle } from '@sveltejs/kit';

// Mock session for testing
const mockSession = {
	session: {
		token: 'test-token',
		id: 'test-session-id',
		userId: 'test-user',
		expiresAt: new Date(Date.now() + 1000 * 60 * 60 * 24),
		createdAt: new Date(),
		updatedAt: new Date()
	},
	user: {
		id: 'test-user',
		email: 'test@test.com',
		name: 'Test User',
		emailVerified: true,
		image: null,
		createdAt: new Date(),
		updatedAt: new Date()
	}
};

export const handle: Handle = async ({ event, resolve }) => {
	// Return mock session instead of real auth
	event.locals.auth = () => Promise.resolve(mockSession);
	return resolve(event);
};
