<script lang="ts">
	import { pastSessions, deletePastSession } from '$lib/stores/session.svelte';
	import type { SessionId } from '$lib/types';
	import { go } from '$lib/go.svelte';
	import ScoreRing from '../../components/ScoreRing.svelte';

	function formatTime(seconds: number) {
		const hrs = Math.floor(seconds / 3600);
		const mins = Math.floor((seconds % 3600) / 60);
		const secs = seconds % 60;
		if (hrs > 0) {
			return `${hrs}h ${mins}m ${secs}s`;
		}
		if (mins > 0) {
			return `${mins}m ${secs}s`;
		}
		return `${secs}s`;
	}

	function formatDate(timestamp: number) {
		return new Date(timestamp).toLocaleDateString('fr-FR', {
			day: '2-digit',
			month: 'short',
			year: 'numeric',
			hour: '2-digit',
			minute: '2-digit'
		});
	}

	function deleteSession(id: SessionId) {
		if (confirm('Voulez-vous vraiment supprimer cette session ?')) {
			deletePastSession(id);
		}
	}
</script>

<div class="sessions-page">
	<header class="header">
		<h1>Historique des sessions</h1>
		<button class="back-btn" onclick={() => go('/')}>
			<svg
				xmlns="http://www.w3.org/2000/svg"
				width="20"
				height="20"
				viewBox="0 0 24 24"
				fill="none"
				stroke="currentColor"
				stroke-width="2"
				stroke-linecap="round"
				stroke-linejoin="round"
				><line x1="19" y1="12" x2="5" y2="12"></line><polyline points="12 19 5 12 12 5"></polyline></svg>
			Retour
		</button>
	</header>

	{#if $pastSessions.length === 0}
		<div class="empty-state">
			<p>Aucune session enregistrée.</p>
			<button class="primary-btn" onclick={() => go('/')}>Commencer une session</button>
		</div>
	{:else}
		<div class="sessions-list">
			{#each $pastSessions as session (session.id)}
				{@const percent = session.questions.length > 0 ? (session.score / session.questions.length) * 100 : 0}
				<div class="basecard session-card">
					<div
						class="session-info"
						onclick={() => go(`/sessions/${session.id}`)}
						onkeydown={(e) => e.key === 'Enter' && go(`/sessions/${session.id}`)}
						role="button"
						tabindex="0">
						<ScoreRing {percent} size={64} strokeWidth={6} />

						<div class="session-details">
							<div class="session-header">
								<span class="session-date">{formatDate(session.created_at)}</span>
								<span class="session-name">{session.name || 'Session sans nom'}</span>
							</div>
							<div class="session-stats">
								<div class="stat">
									<span class="label">Score</span>
									<span class="value" style="color: {percent >= 50 ? '#58a68d' : 'var(--card-red)'}">
										{session.score} / {session.questions.length}
									</span>
								</div>
								<div class="stat">
									<span class="label">Durée</span>
									<span class="value">{formatTime(session.duration_s)}</span>
								</div>
							</div>
						</div>
					</div>
					<button class="delete-btn" onclick={() => deleteSession(session.id)} title="Supprimer">
						<svg
							xmlns="http://www.w3.org/2000/svg"
							width="20"
							height="20"
							viewBox="0 0 24 24"
							fill="none"
							stroke="currentColor"
							stroke-width="2"
							stroke-linecap="round"
							stroke-linejoin="round"
							><polyline points="3 6 5 6 21 6"></polyline><path
								d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path
							><line x1="10" y1="11" x2="10" y2="17"></line><line x1="14" y1="11" x2="14" y2="17"></line></svg>
					</button>
				</div>
			{/each}
		</div>
	{/if}
</div>

<style>
	.sessions-page {
		max-width: 800px;
		margin: 0 auto;
		padding: 40px 20px;
	}

	.header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 40px;
	}

	.header h1 {
		font-size: 32px;
		font-weight: 800;
		color: var(--text-dark);
		margin: 0;
	}

	.back-btn {
		display: flex;
		align-items: center;
		gap: 8px;
		background: var(--glass-bg);
		border: 1px solid var(--glass-border);
		padding: 10px 20px;
		border-radius: 50px;
		color: var(--text-dark);
		font-weight: 600;
		cursor: pointer;
		transition: all 0.2s;
	}

	.back-btn:hover {
		background: var(--glass-bg-strong);
		transform: translateX(-2px);
	}

	.empty-state {
		text-align: center;
		padding: 60px;
		background: var(--glass-bg-strong);
		border-radius: var(--radius-xl);
		border: 1px solid var(--glass-border);
	}

	.empty-state p {
		font-size: 20px;
		color: var(--text-muted);
		margin-bottom: 24px;
	}

	.sessions-list {
		display: flex;
		flex-direction: column;
		gap: 20px;
	}

	.session-card {
		display: flex;
		flex-direction: row;
		background: var(--glass-bg-strong);
		padding: 0;
		overflow: hidden;
	}

	.session-info {
		flex: 1;
		padding: 24px;
		cursor: pointer;
		display: flex;
		align-items: center;
		gap: 24px;
	}

	.session-details {
		display: flex;
		flex-direction: column;
		flex: 1;
		gap: 12px;
	}

	.session-header {
		display: flex;
		flex-direction: column;
		gap: 4px;
	}

	.session-date {
		font-size: 14px;
		color: var(--text-muted);
		font-weight: 500;
	}

	.session-name {
		font-size: 20px;
		font-weight: 700;
		color: var(--text-dark);
	}

	.session-stats {
		display: flex;
		gap: 40px;
	}

	.stat {
		display: flex;
		flex-direction: column;
		gap: 4px;
	}

	.stat .label {
		font-size: 12px;
		text-transform: uppercase;
		letter-spacing: 1px;
		color: var(--text-muted);
		font-weight: 600;
	}

	.stat .value {
		font-size: 18px;
		font-weight: 700;
	}

	.delete-btn {
		background: transparent;
		border: none;
		border-left: 1px solid var(--glass-border);
		padding: 0 32px;
		color: var(--text-muted);
		cursor: pointer;
		transition: all 0.2s;
		display: flex;
		align-items: center;
		justify-content: center;
	}

	.delete-btn:hover {
		background: rgba(220, 53, 69, 0.1);
		color: var(--card-red);
	}

	.primary-btn {
		background: var(--card-blue);
		color: white;
		border: none;
		padding: 16px 32px;
		border-radius: 50px;
		font-weight: 700;
		font-size: 18px;
		cursor: pointer;
		transition: all 0.2s;
	}

	.primary-btn:hover {
		transform: translateY(-2px);
		box-shadow: 0 8px 20px rgba(47, 128, 237, 0.3);
		background: var(--card-indigo);
	}
</style>
