<script lang="ts">
	import favicon from '$lib/assets/favicon.svg';
	import Sidebar from '../components/Sidebar.svelte';
	import Drawer from '../components/Drawer.svelte';
	import Header from '../components/Header.svelte';
	import CardGrid from '../components/CardGrid.svelte';
	import Footer from '../components/Footer.svelte';

	let drawerOpen = false;
	function toggleDrawer() {
		drawerOpen = !drawerOpen;
	}
</script>

<svelte:head>
	<link rel="icon" href={favicon} />
</svelte:head>

<Drawer open={drawerOpen} />
<div class="app">
	<Sidebar onToggleDrawer={toggleDrawer} />
	<main class="main">
		<Header />
		<CardGrid />
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
		--text-dark: #0b1320;
		--text-muted: rgba(0, 0, 0, 0.6);
		--radius-xl: 22px;
	}
	body {
		margin: 0;
		min-height: 100vh;
		background: var(--bg-grey);
		color: var(--text-dark);
	}
	.app {
		display: grid;
		grid-template-columns: 80px 1fr;
		min-height: 100vh;
	}
	.main {
		padding: 40px;
	}
</style>
