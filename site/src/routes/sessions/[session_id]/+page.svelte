<script lang="ts">
	import { go } from '$lib/go';

	import { pastSessions } from '$lib/stores/session.svelte';
	import { questions } from '$lib/stores/questions';
	import type { Session, Attempt, Question } from '$lib/types';
	import { attempts } from '$lib/stores/attempt';
	import { formatTime } from '$lib/utils';
	import ScoreRing from '../../../components/ScoreRing.svelte';

	let { params }: { params: { session_id: string } } = $props();

	// typing is a lie, but check is made just after to conform to it
	let session: Session = $derived($pastSessions.find((s: Session) => s.id === params.session_id))!;
	if (!session) {
		go('/');
	}

	let viewMode: 'missed' | 'all' = $state('missed');

	let allSessionQuestions = $derived.by(() => {
		const all: { question: Question; attempt?: Attempt }[] = [];
		for (const qid of session.questions) {
			const qAttempts = $attempts[qid] || [];
			const attempt = qAttempts.find((a) => a.sessionId === session.id);
			const question = $questions[qid];
			if (question) {
				all.push({ question, attempt });
			}
		}
		return all;
	});

	let missedQuestions = $derived(allSessionQuestions.filter(({ attempt }) => !attempt || !attempt.correct));

	let displayedQuestions = $derived(viewMode === 'missed' ? missedQuestions : allSessionQuestions);

	let percent = $derived(
		session && session.questions.length > 0 ? (session.score / session.questions.length) * 100 : 0
	);
	let isTimedOut = $derived(session && session.kind.is === 'exam' && session.duration >= session.kind.initialTime);
</script>

{#if session}
	<div class="summary-page">
		<div class="summary-card">
			<h2>{session.name}</h2>
			{#if isTimedOut}
				<div class="timeout-alert">
					<span class="icon">⏱️</span>
					<span>Temps écoulé</span>
				</div>
			{/if}
			<div class="score-display">
				<ScoreRing {percent} size={200} strokeWidth={8} />
				<div class="stats-grid">
					<div class="stat-item">
						<span class="stat-value">{session.score} / {session.questions.length}</span>
						<span class="stat-label">Réponses correctes</span>
					</div>
					<div class="stat-item">
						<span class="stat-value">{formatTime(session.duration)}</span>
						<span class="stat-label">Temps total</span>
					</div>
				</div>
			</div>
			<div class="actions">
				<button class="primary-btn" onclick={() => go('/')}>Retour à l'accueil</button>
			</div>
		</div>

		{#if session.questions.length > 0}
			<div class="questions-section">
				<div class="view-toggle">
					<button class="toggle-btn" class:active={viewMode === 'missed'} onclick={() => (viewMode = 'missed')}>
						Questions à revoir ({missedQuestions.length})
					</button>
					<button class="toggle-btn" class:active={viewMode === 'all'} onclick={() => (viewMode = 'all')}>
						Toutes les questions ({allSessionQuestions.length})
					</button>
				</div>
				{#each displayedQuestions as { question, attempt } (question.qid)}
					<div class="question-card">
						{#if attempt}
							<span class="question-duration">{formatTime(attempt.duration)}</span>
						{/if}
						<h3>{question.content}</h3>
						<div class="options-container">
							{#if attempt}
								{#if attempt.correct}
									<div class="option correct">
										<span>{question.choices[attempt.selectedChoice]}</span>
									</div>
								{:else}
									<div class="option incorrect">
										<span>{question.choices[attempt.selectedChoice]}</span>
									</div>
									<div class="option correct">
										<span>{question.choices[question.answer]}</span>
									</div>
								{/if}
							{:else}
								<span class="no-answer">Pas de réponse donnée</span>
								<div class="option correct">
									<span>{question.choices[question.answer]}</span>
								</div>
							{/if}
						</div>
					</div>
				{/each}
			</div>
		{/if}
	</div>
{:else}
	<div class="loading">Chargement...</div>
{/if}

<style>
	.summary-page {
		display: flex;
		flex-direction: column;
		justify-content: flex-start;
		align-items: center;
		gap: 40px;
		width: 100%;
		padding-bottom: 60px;
	}

	.summary-card {
		padding: 30px;
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
		margin: 0 0 20px;
		font-size: 28px;
		font-weight: 700;
		color: var(--text-dark);
	}

	.timeout-alert {
		display: flex;
		align-items: center;
		gap: 8px;
		background: #fff5f5;
		color: #c92a2a;
		padding: 8px 16px;
		border-radius: 50px;
		font-weight: 700;
		font-size: 14px;
		margin-bottom: 20px;
		border: 1px solid #ffc9c9;
		animation: pulse 2s infinite;
	}

	@keyframes pulse {
		0% {
			transform: scale(1);
			box-shadow: 0 0 0 0 rgba(201, 42, 42, 0.4);
		}
		70% {
			transform: scale(1.02);
			box-shadow: 0 0 0 10px rgba(201, 42, 42, 0);
		}
		100% {
			transform: scale(1);
			box-shadow: 0 0 0 0 rgba(201, 42, 42, 0);
		}
	}

	.score-display {
		display: flex;
		flex-direction: column;
		align-items: center;
		margin-bottom: 40px;
		width: 100%;
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
	}

	.primary-btn {
		background: var(--card-blue);
		text-decoration: none;
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

	/* Questions Section */
	.questions-section {
		width: 100%;
		max-width: 800px;
		display: flex;
		flex-direction: column;
		gap: 24px;
	}

	.view-toggle {
		display: flex;
		align-self: center;
		background: var(--glass-bg-strong);
		backdrop-filter: blur(20px);
		border: 1px solid var(--glass-border);
		border-radius: 50px;
		padding: 4px;
		gap: 4px;
		box-shadow: var(--glass-shadow);
	}

	.toggle-btn {
		padding: 10px 20px;
		border: none;
		border-radius: 50px;
		background: transparent;
		color: var(--text-muted);
		font-weight: 600;
		font-size: 14px;
		cursor: pointer;
		transition:
			background 0.25s,
			color 0.25s,
			box-shadow 0.25s;
		white-space: nowrap;
	}

	.toggle-btn:hover {
		color: var(--text-dark);
	}

	.toggle-btn.active {
		background: white;
		color: var(--text-dark);
		box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
	}

	.question-card {
		position: relative;
		padding: 30px;
		border-radius: var(--radius-xl);
		background: var(--glass-bg-strong);
		backdrop-filter: blur(28px) saturate(160%);
		border: 1px solid var(--glass-border);
		box-shadow: var(--glass-shadow);
		text-align: left;
	}

	.question-card h3 {
		margin: 0 0 24px;
		font-size: 20px;
		color: var(--text-dark);
		line-height: 1.5;
		font-weight: 600;
		padding-right: 80px;
	}

	.question-duration {
		position: absolute;
		top: 28px;
		right: 28px;
		font-size: 13px;
		font-weight: 600;
		color: var(--text-muted);
		background: rgba(0, 0, 0, 0.04);
		padding: 4px 12px;
		border-radius: 20px;
		font-variant-numeric: tabular-nums;
	}

	.no-answer {
		font-style: italic;
		color: var(--text-muted);
	}

	.options-container {
		display: flex;
		flex-direction: column;
		gap: 16px;
	}

	.option {
		padding: 16px 24px;
		border-radius: var(--radius-l);
		display: flex;
		align-items: center;
		gap: 16px;
		font-weight: 500;
		position: relative;
	}

	.option.incorrect {
		background: #f8d7da;
		border: 1px solid #f5c6cb;
		color: #721c24;
	}

	.option.correct {
		background: #d4edda;
		border: 1px solid #c3e6cb;
		color: #155724;
	}

	@media (max-width: 600px) {
		.view-toggle {
			flex-direction: column;
			border-radius: var(--radius-l);
		}

		.toggle-btn {
			border-radius: var(--radius-l);
		}

		.question-card h3 {
			padding-right: 0;
			margin-top: 36px;
		}

		.option {
			flex-direction: column;
			align-items: flex-start;
			gap: 8px;
			padding: 16px;
		}
	}
</style>
