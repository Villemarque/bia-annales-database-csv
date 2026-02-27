<script lang="ts">
	import { goto } from '$app/navigation';
	import type { PageProps } from './$types';

	import { pastSessions } from '$lib/stores/session.svelte';
	import { questions } from '$lib/stores/questions';
	import { formatTime } from '$lib/utils';
	import type { Session, Attempt } from '$lib/types';
	import { attempts } from '$lib/stores/attempt';

	let { params }: PageProps = $props();

	const sessionId = params.session_id;

	// typing is a lie, but check is made just after to conform to it
	let session: Session = $derived($pastSessions.find((s) => s.id === sessionId))!;
	if (!session) {
		goto('/');
	}

	let sessAtts: Attempt[] = $derived(
		session.questions.flatMap((qid) => $attempts[qid].filter((q) => q.sessionId == session.id))
	);

	let score: number = $derived(sessAtts.filter((q) => q.correct).length);
</script>

<div class="summary-page">
	{#if session}
		<div class="summary-card">
			<h2>Session Terminée</h2>
			<div class="score-display">
				<div class="score-circle">
					<span class="score-value">{Math.round((score / session.questions.length) * 100)}%</span>
					<span class="score-label">Score</span>
				</div>
				<div class="stats-grid">
					<div class="stat-item">
						<span class="stat-value">{score} / {session.questions.length}</span>
						<span class="stat-label">Réponses correctes</span>
					</div>
					<div class="stat-item">
						<span class="stat-value">{formatTime(session.duration_s)}</span>
						<span class="stat-label">Temps total</span>
					</div>
				</div>
			</div>
			<div class="actions">
				<button class="primary-btn" onclick={() => goto('/')}>Retour à l'accueil</button>
			</div>
		</div>
	{:else}
		<div class="error-container">
			<p>Session introuvable.</p>
			<button class="primary-btn" onclick={() => goto('/')}>Retour à l'accueil</button>
		</div>
	{/if}
</div>

<style>
	.summary-page {
		padding: 40px 20px;
		display: flex;
		justify-content: center;
		align-items: flex-start;
		min-height: 100vh;
	}

	.summary-card {
		padding: 40px;
		border-radius: var(--radius-xl);
		background: var(--glass-bg-strong);
		backdrop-filter: blur(28px) saturate(160%);
		border: 1px solid var(--glass-border);
		box-shadow: var(--glass-shadow);
		display: flex;
		flex-direction: column;
		align-items: center;
		text-align: center;
		width: 100%;
		max-width: 600px;
	}

	.summary-card h2 {
		margin: 0 0 40px;
		font-size: 28px;
		font-weight: 700;
		color: var(--text-dark);
	}

	.score-display {
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 40px;
		margin-bottom: 40px;
		width: 100%;
	}

	.score-circle {
		width: 180px;
		height: 180px;
		border-radius: 50%;
		border: 10px solid var(--card-blue);
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		background: rgba(255, 255, 255, 0.5);
		box-shadow: 0 10px 30px rgba(47, 128, 237, 0.15);
	}

	.score-value {
		font-size: 48px;
		font-weight: 800;
		color: var(--card-blue);
		line-height: 1;
	}

	.score-label {
		font-size: 16px;
		text-transform: uppercase;
		letter-spacing: 1.5px;
		color: var(--text-muted);
		margin-top: 6px;
	}

	.stats-grid {
		display: grid;
		grid-template-columns: 1fr 1fr;
		gap: 30px;
		width: 100%;
		max-width: 500px;
		margin-top: 20px;
	}

	.stat-item {
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 10px;
		padding: 20px;
		background: rgba(255, 255, 255, 0.3);
		border-radius: var(--radius-l);
		border: 1px solid var(--glass-border);
	}

	.stat-value {
		font-size: 26px;
		font-weight: 700;
		color: var(--text-dark);
	}

	.stat-label {
		font-size: 14px;
		color: var(--text-muted);
		font-weight: 500;
	}

	.actions {
		display: flex;
		justify-content: center;
		width: 100%;
		margin-top: 20px;
	}

	.primary-btn {
		background: var(--card-blue);
		color: white;
		border: none;
		padding: 16px 40px;
		border-radius: 50px;
		font-weight: 700;
		font-size: 18px;
		cursor: pointer;
		transition:
			transform 0.2s,
			box-shadow 0.2s,
			background 0.2s;
	}

	.primary-btn:hover {
		transform: translateY(-2px);
		box-shadow: 0 8px 20px rgba(47, 128, 237, 0.3);
		background: var(--card-indigo);
	}

	.error-container {
		text-align: center;
		margin-top: 100px;
		color: var(--text-muted);
		background: var(--glass-bg-strong);
		padding: 40px;
		border-radius: var(--radius-l);
		border: 1px solid var(--glass-border);
	}

	.error-container p {
		font-size: 20px;
		margin-bottom: 20px;
	}
</style>
