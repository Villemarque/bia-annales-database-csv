<script lang="ts">
	import { go } from '$lib/go.svelte';

	import { pastSessions } from '$lib/stores/session.svelte';
	import { questions } from '$lib/stores/questions';
	import type { Session, Attempt, Question } from '$lib/types';
	import { attempts } from '$lib/stores/attempt';
	import ScoreRing from '../../../components/ScoreRing.svelte';

	let { params }: { params: { session_id: string } } = $props();

	const sessionId = params.session_id;

	// typing is a lie, but check is made just after to conform to it
	let session: Session = $derived($pastSessions.find((s: Session) => s.id === sessionId))!;
	if (!session) {
		go('/');
	}

	let missedQuestions = $derived.by(() => {
		const missed: { question: Question; attempt: Attempt }[] = [];
		for (const qid of session.questions) {
			const qAttempts = $attempts[qid] || [];
			const attempt = qAttempts.find((a) => a.sessionId === session.id);
			if (attempt && !attempt.correct) {
				const question = $questions[qid];
				if (question) {
					missed.push({ question, attempt });
				}
			}
		}
		return missed;
	});

	function formatTime(seconds: number) {
		const hrs = Math.floor(seconds / 3600);
		const mins = Math.floor((seconds % 3600) / 60);
		const secs = seconds % 60;
		return `${hrs.toString().padStart(2, '0')}:${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
	}

	let percent = $derived(session.questions.length > 0 ? (session.score / session.questions.length) * 100 : 0);
</script>

<div class="summary-page">
	<div class="summary-card">
		<h2>{session.name}</h2>
		<div class="score-display">
			<ScoreRing {percent} size={200} strokeWidth={8} />
			<div class="stats-grid">
				<div class="stat-item">
					<span class="stat-value">{session.score} / {session.questions.length}</span>
					<span class="stat-label">Réponses correctes</span>
				</div>
				<div class="stat-item">
					<span class="stat-value">{formatTime(session.duration_s)}</span>
					<span class="stat-label">Temps total</span>
				</div>
			</div>
		</div>
		<div class="actions">
			<button class="primary-btn" onclick={() => go('/')}>Retour à l'accueil</button>
		</div>
	</div>

	{#if missedQuestions.length > 0}
		<div class="missed-section">
			<h2 class="section-title">Questions à revoir</h2>
			{#each missedQuestions as { question, attempt } (question.qid)}
				<div class="missed-card">
					<h3>{question.content}</h3>
					<div class="options-container">
						<div class="option incorrect">
							<span>{question.choices[attempt.selectedChoice]}</span>
						</div>
						<div class="option correct">
							<span>{question.choices[question.answer]}</span>
						</div>
					</div>
				</div>
			{/each}
		</div>
	{/if}
</div>

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
		margin: 0 0 40px;
		font-size: 28px;
		font-weight: 700;
		color: var(--text-dark);
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

	/* Missed Questions Section */
	.missed-section {
		width: 100%;
		max-width: 800px;
		display: flex;
		flex-direction: column;
		gap: 24px;
	}

	.section-title {
		font-size: 24px;
		font-weight: 700;
		color: var(--text-dark);
		margin: 0;
		text-align: center;
	}

	.missed-card {
		padding: 30px;
		border-radius: var(--radius-xl);
		background: var(--glass-bg-strong);
		backdrop-filter: blur(28px) saturate(160%);
		border: 1px solid var(--glass-border);
		box-shadow: var(--glass-shadow);
		text-align: left;
	}

	.missed-card h3 {
		margin: 0 0 24px;
		font-size: 20px;
		color: var(--text-dark);
		line-height: 1.5;
		font-weight: 600;
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

	.option-letter {
		font-weight: 700;
		font-size: 18px;
	}

	.option-letter.incorrect {
		color: #721c24;
	}

	.option-letter.correct {
		color: #155724;
	}

	.badge {
		margin-left: auto;
		padding: 4px 12px;
		border-radius: 20px;
		font-size: 12px;
		font-weight: 700;
		text-transform: uppercase;
		letter-spacing: 0.5px;
	}

	.badge-incorrect {
		background: rgba(220, 53, 69, 0.15);
		color: #721c24;
	}

	.badge-correct {
		background: rgba(40, 167, 69, 0.15);
		color: #155724;
	}

	.perfect-score {
		padding: 30px;
		border-radius: var(--radius-xl);
		background: rgba(40, 167, 69, 0.1);
		border: 1px solid #c3e6cb;
		color: #155724;
		text-align: center;
		font-size: 20px;
		font-weight: 600;
		width: 100%;
		max-width: 800px;
		backdrop-filter: blur(10px);
	}

	@media (max-width: 600px) {
		.option {
			flex-direction: column;
			align-items: flex-start;
			gap: 8px;
			padding: 16px;
		}

		.badge {
			margin-left: 0;
			margin-top: 8px;
		}
	}
</style>
