<script lang="ts">
	import { fade } from 'svelte/transition';

	let isExpanded = $state(false);
	const toggle = () => (isExpanded = !isExpanded);

	const items = [
		{ icon: '🏠', label: 'Accueil' },
		{ icon: '✈︎', label: 'Programme' },
		{ icon: '📚', label: 'Ressources' },
		{ icon: '📊', label: 'Progression' },
		{ icon: '⚙️', label: 'Paramètres' }
	];
</script>

<aside class="navigation" class:expanded={isExpanded}>
	<div class="header-section">
		<!-- svelte-ignore a11y_click_events_have_key_events -->
		<!-- svelte-ignore a11y_no_static_element_interactions -->
		<div class="dot hamburger" onclick={toggle}>☰</div>
	</div>

	<nav class="menu">
		<ul>
			{#each items as item}
				<li>
					<div class="menu-item">
						<div class="dot icon-container">{item.icon}</div>
						{#if isExpanded}
							<span class="label" transition:fade={{ duration: 200 }}>{item.label}</span>
						{/if}
					</div>
				</li>
			{/each}
		</ul>
	</nav>
</aside>

<style>
	.navigation {
		width: 80px;
		height: 100vh;
		backdrop-filter: blur(28px) saturate(160%);
		background: var(--glass-bg);
		border-right: 1px solid var(--glass-border);
		display: flex;
		flex-direction: column;
		padding: 20px 0;
		gap: 30px;
		transition: width 0.15s cubic-bezier(0.4, 0, 0.2, 1);
		overflow: hidden;
		z-index: 20;
		flex-shrink: 0;
	}

	.navigation.expanded {
		width: 200px;
	}

	.header-section {
		display: flex;
		justify-content: flex-start;
		padding: 0 18px;
		width: 100%;
	}

	.menu {
		width: 100%;
	}

	.menu ul {
		list-style: none;
		padding: 0;
		margin: 0;
		display: flex;
		flex-direction: column;
		gap: 18px;
	}

	.menu-item {
		display: flex;
		align-items: center;
		padding: 0 18px;
		gap: 15px;
		cursor: pointer;
		white-space: nowrap;
	}

	.dot {
		width: 44px;
		height: 44px;
		min-width: 44px;
		border-radius: 14px;
		background: var(--glass-bg-strong);
		backdrop-filter: blur(12px);
		border: 1px solid var(--glass-border);
		display: flex;
		align-items: center;
		justify-content: center;
		font-weight: 600;
		transition: transform 0.2s ease;
	}

	.hamburger {
		cursor: pointer;
	}

	.hamburger:hover {
		transform: scale(1.05);
	}

	.label {
		font-size: 16px;
		font-weight: 500;
		color: var(--text-dark);
	}

	.icon-container {
		font-size: 18px;
	}
</style>
