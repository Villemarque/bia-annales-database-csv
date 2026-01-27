<script lang="ts">
	let {
		expanded = false,
		items = []
	}: {
		expanded?: boolean;
		items?: Array<{
			icon: string;
			label: string;
			action: { tpe: 'href'; href: string } | { tpe: 'toggle'; onToggle: () => void };
		}>;
	} = $props();
</script>

{#snippet menu_item(icon: string, label: string)}
	<div class="icon-circle">{icon}</div>
	<span class="label">{label}</span>
{/snippet}

<nav class="menu-capsule" class:expanded>
	<ul>
		{#each items as item}
			<li>
				{#if item.action.tpe == 'href'}
					<a href={item.action.href} class="menu-item" class:expanded>
						{@render menu_item(item.icon, item.label)}
					</a>
				{:else if item.action.tpe == 'toggle'}
					<a
						onclick={item.action.onToggle}
						role="button"
						class="menu-item"
						class:expanded
						aria-label="Toggle Navigation">
						{@render menu_item(item.icon, item.label)}
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
		// border: 1px solid var(--glass-border);
		border-radius: 32px;
		// padding: 12px 0;
		box-shadow: var(--glass-shadow);
		overflow: hidden;
		transition: width 0.2s ease;
	}

	.menu-capsule.expanded {
		width: 176px;
	}

	.menu-capsule ul {
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
		padding: 0;
		text-decoration: none;
		transition: background 0.2s ease;
	}

	.expanded .menu-item {
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
