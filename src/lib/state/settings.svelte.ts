import { createPersistedObj } from '$lib/spells/persisted-obj.svelte';

export const settings = createPersistedObj('settings', {
	// Static model ID for Financial Analyst
	modelId: 'financial-analyst',
	webSearchEnabled: false,
	reasoningEffort: 'low' as 'low' | 'medium' | 'high',
});
