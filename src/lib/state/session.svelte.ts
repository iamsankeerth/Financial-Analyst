// Auth removed - using static test user
export const session = {
	get current() {
		return {
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
	},
};
