<script>
	export let onToggleDrawer;
</script>

<aside class="sidebar" on:click={onToggleDrawer}>
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
</style>
