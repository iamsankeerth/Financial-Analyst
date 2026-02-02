import { Provider } from '$lib/types';
import type { LayoutServerLoad } from './$types';

export const load: LayoutServerLoad = async () => {
	// Mock session for testing (auth disabled)
	const mockSession = {
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
	};

	return {
		session: mockSession,
		models: {
			[Provider.OpenRouter]: [
				{
					id: 'financial-analyst',
					name: 'Financial Analyst (Gemini)',
					description: 'Specialized model for stock analysis and financial data.',
					architecture: {
						input_modalities: ['text', 'image'],
						output_modalities: ['text'],
					},
					supported_parameters: ['temperature', 'top_p', 'max_tokens'],
				}
			],
		},
	};
};

export const ssr = false;
