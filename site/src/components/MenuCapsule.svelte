<script lang="ts">
	let {
		expanded = false,
		items = []
	}: {
		expanded?: boolean;
		items?: Array<{ icon: string; label: string; action: { href: string } | { onToggle: () => void } }>;
	} = $props();
</script>

{#snippet menu_item(icon, label, expanded)}
	<div class="icon-circle">{icon}</div>
	{#if expanded}
		<span class="label">{label}</span>
	{/if}
{/snippet}

<nav class="menu-capsule" class:expanded>
	<ul>
		{#each items as item}
			<li>
				{#if item.action.href}
					<a href={item.action.href} class="menu-item" class:expanded>
						{@render menu_item(item.icon, item.label, expanded)}
					</a>
				{:else if item.action.onToggle}
					<a onclick={item.action.onToggle} class="menu-item button-noop" class:expanded aria-label="Toggle Navigation">
						{@render menu_item(item.icon, item.label, expanded)}
					</a>
				{/if}
			</li>
		{/each}
	</ul>
</nav>

<style>
	.menu-capsule {
		width: 56px;
		background: var(--glass-bg-strong);
		backdrop-filter: blur(28px) saturate(160%);
		border: 1px solid var(--glass-border);
		border-radius: 32px;
		padding: 12px 0;
		box-shadow: var(--glass-shadow);
		overflow: hidden;
		transition: none; /* Instant as requested */
	}

	.menu-capsule.expanded {
		width: 200px;
	}

	.menu-capsule ul {
		list-style: none;
		padding: 0;
		margin: 0;
		display: flex;
		flex-direction: column;
		gap: 8px;
	}

	button.button-noop {
		all: unset;
	}

	.menu-item {
		display: flex;
		align-items: center;
		justify-content: center;
		height: 52px;
		gap: 12px;
		cursor: pointer;
		white-space: nowrap;
		border-radius: 22px;
		margin: 0 8px;
		padding: 0;
		text-decoration: none;
		transition: background 0.2s ease;
	}

	.expanded .menu-item {
		justify-content: flex-start;
		padding-left: 6px;
	}

	.menu-item.expanded:hover {
		background: rgba(0, 0, 0, 0.04);
	}

	.icon-circle {
		width: 40px;
		height: 40px;
		min-width: 40px;
		border-radius: 50%;
		background: rgba(0, 0, 0, 0.05);
		border: 1px solid rgba(0, 0, 0, 0.03);
		display: flex;
		align-items: center;
		justify-content: center;
		font-size: 18px;
	}

	.label {
		font-size: 15px;
		font-weight: 600;
		color: var(--text-dark);
		letter-spacing: -0.01em;
	}
</style>
