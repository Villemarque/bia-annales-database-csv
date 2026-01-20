<script lang="ts">
	import { fade } from 'svelte/transition';

	let isExpanded = $state(false);
	const toggle = () => (isExpanded = !isExpanded);

	const items = [
		{ icon: '🏠', label: 'Accueil', href: '/' },
		{ icon: '✈︎', label: 'Programme', href: '/quiz' },
		{ icon: '📚', label: 'Ressources', href: '/ressources' },
		{ icon: '📊', label: 'Progression', href: '/progression' },
		{ icon: '⚙️', label: 'Paramètres', href: '/settings' }
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
					<a href={item.href} class="menu-item" style="text-decoration: none;">
						<div class="dot icon-container">{item.icon}</div>
						{#if isExpanded}
							<span class="label" transition:fade={{ duration: 200 }}>{item.label}</span>
						{/if}
					</a>
				</li>
			{/each}
		</ul>
	</nav>
</aside>

<style>
	.navigation {
		width: 80px;
		display: flex;
		flex-direction: column;
		padding: 26.8px 0 20px 0;
		gap: 20px;
		transition: width 0.3s cubic-bezier(0.4, 0, 0.2, 1);
		z-index: 20;
		flex-shrink: 0;
		align-items: flex-start;
		overflow: hidden;
	}

	@media (max-width: 600px) {
		.navigation {
			padding-top: 15.2px;
		}
	}

	.navigation.expanded {
		width: 220px;
	}

	.header-section {
		display: flex;
		justify-content: flex-start;
		width: 100%;
		padding-left: 18px;
		box-sizing: border-box;
	}

	.menu {
		width: calc(100% - 24px);
		margin-left: 12px;
		background: var(--glass-bg-strong);
		backdrop-filter: blur(28px) saturate(160%);
		border: 1px solid var(--glass-border);
		border-radius: 32px;
		padding: 12px 0;
		transition: width 0.3s cubic-bezier(0.4, 0, 0.2, 1);
		overflow: hidden;
	}

	.menu ul {
		list-style: none;
		padding: 0;
		margin: 0;
		display: flex;
		flex-direction: column;
		gap: 8px;
	}

	.menu-item {
		display: flex;
		align-items: center;
		justify-content: flex-start;
		height: 52px;
		gap: 12px;
		cursor: pointer;
		white-space: nowrap;
		border-radius: 22px;
		margin: 0 8px;
		transition: background 0.2s ease;
		padding: 0;
	}

	.menu-item:hover {
		background: rgba(0, 0, 0, 0.04);
	}

	.dot {
		width: 40px;
		height: 40px;
		min-width: 40px;
		border-radius: 50%;
		display: flex;
		align-items: center;
		justify-content: center;
		font-weight: 600;
		transition: all 0.2s ease;
	}

	.hamburger {
		width: 44px;
		height: 44px;
		background: var(--glass-bg-strong);
		backdrop-filter: blur(12px);
		border: 1px solid var(--glass-border);
		cursor: pointer;
		border-radius: 50%;
	}

	.hamburger:hover {
		transform: scale(1.05);
	}

	.icon-container {
		background: rgba(0, 0, 0, 0.05);
		border: 1px solid rgba(0, 0, 0, 0.03);
		font-size: 18px;
	}

	.label {
		font-size: 15px;
		font-weight: 600;
		color: var(--text-dark);
		letter-spacing: -0.01em;
	}

	@media (max-width: 900px) {
		.navigation {
			position: fixed;
			top: 0;
			left: 0;
			height: 100vh;
		}
	}
</style>
