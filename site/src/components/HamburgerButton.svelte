<script lang="ts">
	let {
		ontoggle
	}: {
		ontoggle: () => void;
	} = $props();
</script>

<button class="hamburger" onclick={ontoggle} aria-label="Toggle Navigation"> ☰ </button>

<style>
	.hamburger {
		width: 48px;
		height: 48px;
		border-radius: 50%;
		background: var(--glass-bg-strong);
		backdrop-filter: blur(12px);
		border: 1px solid var(--glass-border);
		cursor: pointer;
		display: flex;
		align-items: center;
		justify-content: center;
		font-size: 20px;
		color: var(--text-dark);
		padding: 0;
		box-shadow: none;
		outline: none;
		/* No transition as requested */
	}
</style>
