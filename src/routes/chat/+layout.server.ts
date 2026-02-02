// Auth disabled for testing
export async function load() {
	return {
		session: {
			user: {
				id: 'test-user',
				email: 'test@test.com',
				name: 'Test User',
				emailVerified: true,
				image: null,
				createdAt: new Date(),
				updatedAt: new Date()
			},
			session: {
				token: 'test-token',
				id: 'test-session-id',
				userId: 'test-user',
				expiresAt: new Date(Date.now() + 1000 * 60 * 60 * 24),
				createdAt: new Date(),
				updatedAt: new Date()
			}
		},
	};
}
