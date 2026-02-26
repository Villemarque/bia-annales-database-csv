<script lang="ts">
	import { log } from '$lib/log';
	import { onMount } from 'svelte';
	import { getDb } from '$lib/getDb';

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

	async function resetAllData() {
		if (confirm('ATTENTION: Cela va effacer TOUTES vos données (sessions, tentatives, réglages). Continuer ?')) {
			const db = await getDb;
			await db.clearDb();
			window.location.reload();
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

	<div class="card danger-zone">
		<div class="header">
			<h2>Zone de danger</h2>
		</div>
		<p class="description">
			Réinitialiser l'application effacera définitivement toutes vos données locales (sessions, historique, tentatives).
		</p>
		<button onclick={resetAllData} class="btn-reset">Tout réinitialiser</button>
	</div>
</div>

<style>
	.settings-page {
		max-width: 800px;
		margin: 0 auto;
		padding: 20px 0;
		display: flex;
		flex-direction: column;
		gap: 24px;
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

	.danger-zone {
		border-color: rgba(220, 53, 69, 0.2);
	}

	.description {
		color: var(--text-muted);
		font-size: 15px;
		line-height: 1.5;
		margin: 0;
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

	.btn-reset {
		background: var(--card-red);
		border: none;
		color: white;
		padding: 12px 24px;
		border-radius: 12px;
		font-weight: 700;
		cursor: pointer;
		transition: all 0.2s;
		align-self: flex-start;
	}

	.btn-reset:hover {
		transform: translateY(-2px);
		box-shadow: 0 4px 12px rgba(220, 53, 69, 0.3);
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
