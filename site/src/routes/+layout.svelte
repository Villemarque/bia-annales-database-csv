<script lang="ts">
	import type { LayoutProps } from './$types';

	import favicon from '$lib/assets/favicon.svg';
	import Navigation from '../components/Navigation.svelte';
	import Header from '../components/Header.svelte';
	import Footer from '../components/Footer.svelte';

	let { children }: LayoutProps = $props();
</script>

<svelte:head>
	<link rel="icon" href={favicon} />
</svelte:head>

<div class="app">
	<Navigation />
	<main class="main">
		<Header />
		<div class="content">
			{@render children()}
		</div>
		<Footer />
	</main>
</div>

<style>
	:root {
		--glass-bg: rgba(255, 255, 255, 0.55);
		--glass-bg-strong: rgba(255, 255, 255, 0.75);
		--glass-border: rgba(255, 255, 255, 0.6);
		--glass-shadow: 0 12px 40px rgba(0, 0, 0, 0.15);
		--bg-grey: #f2f4f7;
		--card-blue: linear-gradient(135deg, #2f80ed, #56ccf2);
		--card-indigo: linear-gradient(135deg, #5f2cff, #9b6bff);
		--card-green: linear-gradient(135deg, #1fa971, #6ee7b7);
		--card-orange: linear-gradient(135deg, #f2994a, #f2c94c);
		--card-red: linear-gradient(135deg, #eb5757, #f29999);
		--card-pink: linear-gradient(135deg, #d946ef, #f472b6);
		--text-dark: #0b1320;
		--text-muted: rgba(0, 0, 0, 0.6);
		--radius-xl: 22px;
		font-family: 'Open Sans', sans-serif;
	}
	:global(body) {
		margin: 0;
		min-height: 100vh;
		background: var(--bg-grey);
		color: var(--text-dark);
	}
	.app {
		display: grid;
		grid-template-columns: auto 1fr;
		min-height: 100vh;
	}
	.main {
		display: flex;
		flex-direction: column;
		min-width: 0;
	}
	.content {
		flex: 1;
		padding: 15px 20px 0px 0px;
		min-width: 0;
	}
	@media (max-width: 900px) {
		.app {
			display: block;
		}
		.main {
			margin-left: 80px;
		}
	}
</style>
