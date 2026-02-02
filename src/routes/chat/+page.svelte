<script lang="ts">
	import { session } from '$lib/state/session.svelte';
	import IconAi from '~icons/lucide/sparkles';
	import CodeIcon from '~icons/lucide/code';
	import GraduationCapIcon from '~icons/lucide/graduation-cap';
	import NewspaperIcon from '~icons/lucide/newspaper';
	import { Button } from '$lib/components/ui/button';
	import { usePrompt } from '$lib/state/prompt.svelte';
	import { scale } from 'svelte/transition';
	import { useCachedQuery } from '$lib/cache/cached-query.svelte';
	import { api } from '$lib/backend/convex/_generated/api';
	import { Provider } from '$lib/types';

	const defaultSuggestions = [
		'What was the price of Gold (GLD) yesterday?',
		'Compare AAPL and MSFT for the last 6 months with 50-day moving averages',
		'Give me a summary of Teslas latest balance sheet',
		'Analyze the correlation between Bitcoin and the S&P 500 over the past year',
		'What are the key financial ratios for NVIDIA right now?',
	];

	const settings = useCachedQuery(api.user_settings.get, {
		session_token: session.current?.session.token ?? '',
	});

	const prompt = usePrompt();
</script>

<svelte:head>
	<title>New Chat | Financial Analyst</title>
</svelte:head>

<div class="flex h-svh flex-col items-center justify-center">
	<div class="w-full p-2" in:scale={{ duration: 500, start: 0.9 }}>
		<h2 class="text-left font-serif text-3xl font-semibold">
			Welcome to <span class="text-primary italic">Financial Analyst</span>
		</h2>
		<p class="text-muted-foreground mt-1 text-left">
			Specialized Gemini Intelligence Active. Ask me about stocks, fundamentals, or market trends.
		</p>
		
		<div class="mt-8 flex flex-col gap-2 p-2">
			{#each defaultSuggestions as suggestion}
				<div class="border-border group not-last:border-b not-last:pb-2">
					<Button
						onclick={() => (prompt.current = suggestion)}
						variant="ghost"
						class="w-full cursor-pointer justify-start px-2 py-2 text-start"
					>
						{suggestion}
					</Button>
				</div>
			{/each}
		</div>
	</div>
</div>
