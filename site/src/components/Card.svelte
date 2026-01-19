<script lang="ts">
	let {
		icon = '',
		color = '',
		title = '',
		desc = '',
		href = ''
	}: {
		icon?: string;
		color?: string;
		title?: string;
		desc?: string;
		href?: string;
	} = $props();
</script>

{#if href}
	<a {href} class="card" style="background: {color}; text-decoration: none;">
		<div class="icon">{icon}</div>
		<h3>{title}</h3>
		<p>{desc}</p>
	</a>
{:else}
	<div class="card" style="background: {color}">
		<div class="icon">{icon}</div>
		<h3>{title}</h3>
		<p>{desc}</p>
	</div>
{/if}

<style>
	.card {
		padding: 26px;
		border-radius: var(--radius-xl);
		color: white;
		box-shadow: var(--glass-shadow);
		transition: transform 0.35s ease;
	}
	.card:hover {
		transform: translateY(-8px) scale(1.02);
	}
	.card h3 {
		margin: 16px 0 8px;
		font-size: 18px;
	}
	.card p {
		margin: 0;
		font-size: 14px;
		opacity: 0.9;
	}
	.icon {
		width: 46px;
		height: 46px;
		border-radius: 14px;
		background: rgba(255, 255, 255, 0.25);
		display: flex;
		align-items: center;
		justify-content: center;
		font-weight: 700;
	}
</style>
