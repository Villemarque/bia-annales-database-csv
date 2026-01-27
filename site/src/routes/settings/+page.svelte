<script lang="ts">
	import { log } from '$lib/log';
	import { onMount } from 'svelte';

	let logs = $state<string[]>([]);

	async function loadLogs() {
		logs = await log.get();
	}

	async function clearLogs() {
		if (confirm('Voulez-vous vraiment effacer tous les journaux ?')) {
			await log.clear();
			await loadLogs();
		}
	}

	onMount(() => {
		loadLogs();
	});
</script>

<div class="settings-page">
	<div class="card">
		<div class="header">
			<h2>Journal de débogage</h2>
			<button onclick={clearLogs} class="btn-clear">Effacer</button>
		</div>

		<div class="logs-container">
			{#if logs.length === 0}
				<div class="empty">Aucun journal</div>
			{:else}
				<div class="pre">
					{#each logs as l}
						<div class="log-entry">{l}</div>
					{/each}
				</div>
			{/if}
		</div>
	</div>
</div>

<style>
	.settings-page {
		max-width: 800px;
		margin: 0 auto;
		padding: 20px 0;
	}

	.card {
		background: var(--glass-bg-strong);
		backdrop-filter: blur(20px) saturate(160%);
		border: 1px solid var(--glass-border);
		border-radius: var(--radius-xl);
		box-shadow: var(--glass-shadow);
		padding: 32px;
		display: flex;
		flex-direction: column;
		gap: 20px;
	}

	.header {
		display: flex;
		justify-content: space-between;
		align-items: center;
	}

	h2 {
		margin: 0;
		font-size: 24px;
		color: var(--text-dark);
	}

	.btn-clear {
		background: var(--card-red);
		border: none;
		color: white;
		padding: 8px 16px;
		border-radius: 8px;
		font-weight: 600;
		cursor: pointer;
		transition: opacity 0.2s;
	}

	.btn-clear:hover {
		opacity: 0.9;
	}

	.logs-container {
		background: rgba(0, 0, 0, 0.05);
		border-radius: 12px;
		padding: 16px;
		max-height: 500px;
		overflow-y: auto;
		font-family: monospace;
		font-size: 13px;
	}

	.empty {
		color: var(--text-muted);
		text-align: center;
		padding: 20px;
		font-style: italic;
	}

	.pre {
		margin: 0;
		white-space: pre-wrap;
		word-break: break-all;
	}

	.log-entry {
		padding: 4px 0;
		border-bottom: 1px solid rgba(0, 0, 0, 0.05);
	}
	.log-entry:last-child {
		border-bottom: none;
	}
</style>
