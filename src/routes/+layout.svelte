<script lang="ts">
	import { goto } from '$app/navigation';
	import { PUBLIC_CONVEX_URL } from '$env/static/public';
	import { shortcut } from '$lib/actions/shortcut.svelte';
	import GlobalModal from '$lib/components/ui/modal/global-modal.svelte';
	import { models } from '$lib/state/models.svelte';
	import { setupConvex } from 'convex-svelte';
	import { ModeWatcher } from 'mode-watcher';
	import '../app.css';
	import { browser } from '$app/environment';
	import { MetaTags } from 'svelte-meta-tags';
	import { page } from '$app/state';
	import { setupLastChat } from '$lib/state/last-chat.svelte';

	let { children } = $props();

	setupConvex(PUBLIC_CONVEX_URL);
	const lastChat = setupLastChat();
	models.init();

	$effect(() => {
		if (page.url.pathname.startsWith('/chat')) {
			lastChat.current = page.params?.id ?? null;
		}
	});
</script>

<MetaTags
	title="Financial Analyst"
	description="AI-Powered Stock Analysis Tool"
	keywords={['svelte', 'finance', 'stocks', 'ai', 'analyst']}
	twitter={{
		cardType: 'summary_large_image',
		title: 'Financial Analyst',
		description: 'AI-Powered Stock Analysis Tool',
		image: '/favicon.png',
		creator: '@financial_analyst',
	}}
	openGraph={{
		url: page.url.toString(),
		type: 'website',
		title: 'Financial Analyst',
		description: 'AI-Powered Stock Analysis Tool',
		siteName: 'Financial Analyst',
		images: [
			{
				url: '/favicon.png',
				width: 180,
				height: 180,
				alt: 'Financial Analyst',
			},
		],
	}}
/>

<svelte:window
	use:shortcut={{ ctrl: true, shift: true, key: 'o', callback: () => goto('/chat') }}
/>

<ModeWatcher />
{#if browser}
	{@render children()}
{/if}

<GlobalModal />
