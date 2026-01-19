<script lang="ts">
	import { fly } from 'svelte/transition';

	let isOpen = $state(false);
	const toggle = () => (isOpen = !isOpen);
</script>

{#if isOpen}
	<!-- svelte-ignore a11y_click_events_have_key_events -->
	<!-- svelte-ignore a11y_no_static_element_interactions -->
	<div class="drawer" transition:fly={{ x: -320, duration: 450, opacity: 1 }} onclick={toggle}>
		<h2>BIA Air France</h2>
		<ul>
			<li>Accueil</li>
			<li>Programme</li>
			<li>Ressources</li>
			<li>Progression</li>
			<li>Paramètres</li>
		</ul>
	</div>
{/if}

<!-- svelte-ignore a11y_click_events_have_key_events -->
<!-- svelte-ignore a11y_no_static_element_interactions -->
<aside class="sidebar" onclick={toggle}>
	<div class="dot">☰</div>
	<div class="dot">✈︎</div>
	<div class="dot">🧭</div>
</aside>

<style>
	.sidebar {
		position: relative;
		backdrop-filter: blur(28px) saturate(160%);
		background: var(--glass-bg);
		border-right: 1px solid var(--glass-border);
		display: flex;
		flex-direction: column;
		align-items: center;
		padding: 20px 0;
		gap: 22px;
		cursor: pointer;
		z-index: 10;
	}
	.dot {
		width: 44px;
		height: 44px;
		border-radius: 14px;
		background: var(--glass-bg-strong);
		backdrop-filter: blur(12px);
		border: 1px solid var(--glass-border);
		display: flex;
		align-items: center;
		justify-content: center;
		font-weight: 600;
	}
	.drawer {
		position: fixed;
		top: 0;
		left: 0;
		height: 100vh;
		width: 220px;
		background: var(--glass-bg-strong);
		backdrop-filter: blur(36px) saturate(180%);
		border-right: 1px solid var(--glass-border);
		box-shadow: var(--glass-shadow);
		padding: 40px 28px;
		z-index: 20;
		cursor: default;
	}
	.drawer h2 {
		margin-top: 0;
		font-size: 22px;
	}
	.drawer ul {
		list-style: none;
		padding: 0;
		margin: 30px 0 0;
		display: grid;
		gap: 18px;
	}
	.drawer li {
		padding: 14px 18px;
		border-radius: 16px;
		background: rgba(255, 255, 255, 0.6);
		border: 1px solid var(--glass-border);
		cursor: pointer;
	}
</style>
