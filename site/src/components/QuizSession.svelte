<script lang="ts">
	// TODO FIXME this should really not be a component
	// but a page, or split differently
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import type { OngoingSession, Attempt, Timestamp, AttemptId, Qid } from '$lib/types';
	import { questions } from '$lib/stores/questions';
	import { makeAttempt, addAttempt } from '$lib/stores/attempt';
	import { unsafeRandomId } from '$lib/random';

	// need to be a state
	let {
		session = $bindable(),
		sessionDuration = $bindable(),
		durationByQ = $bindable(),
		onSessionFinish,
		onSessionCancel
	}: {
		session: OngoingSession;
		sessionDuration: number;
		durationByQ: Record<Qid, number>;
		onSessionCancel: () => void;
		onSessionFinish: () => void;
	} = $props();

	let currentIndex = $state(0);
	interface FinishData {
		score: number;
	}
	let finishData = $state<FinishData | undefined>(undefined);
	let isFinished = $derived(finishData !== undefined);

	const letters = ['A', 'B', 'C', 'D'];

	let currentQuestionWip = $derived(session.questions[currentIndex]);
	let timeShown = $derived.by(() => {
		if (session.kind.is === 'exam') {
			// @ts-ignore - initial_time exists in the type definition but LSP might be stale
			return session.kind.initial_time - sessionDuration;
		}
		return sessionDuration;
	});

	let currentQuestionDisplay = $derived($questions[currentQuestionWip.qid]);

	function formatTime(seconds: number) {
		const hrs = Math.floor(seconds / 3600);
		const mins = Math.floor((seconds % 3600) / 60);
		const secs = seconds % 60;
		return `${hrs.toString().padStart(2, '0')}:${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
	}

	function handleSelect(choiceNo: number) {
		const isStudy = session.kind.is === 'study';
		if (isFinished || (isStudy && session.questions[currentIndex].selected_choice !== undefined)) {
			return;
		}

		session.questions[currentIndex].selected_choice = choiceNo;

		if (isStudy) {
			const isCorrect = choiceNo === currentQuestionDisplay.answer;

			if (isCorrect) {
				session.questions[currentIndex].correct_choice = choiceNo;
			}

			const attempt = makeAttempt(
				currentQuestionWip,
				session,
				currentQuestionDisplay,
				durationByQ[currentQuestionWip.qid] || 0
			);
			if (attempt) {
				addAttempt(attempt);
			}
		}
	}

	function goToQuestion(index: number) {
		currentIndex = index;
	}

	function finishSession() {
		onSessionFinish();
		let score = 0;
		for (const q of session.questions) {
			if (q.selected_choice !== undefined) {
				const actualAnswer = $questions[q.qid].answer;
				if (q.selected_choice === actualAnswer) {
					score++;
				}
			}
		}
		finishData = { score };
	}

	function cancelSession() {
		onSessionCancel();
		goto('/');
	}

	function shouldShowFeedback(selectedChoice: number | undefined) {
		return (session.kind.is !== 'exam' && selectedChoice !== undefined) || isFinished;
	}

	function isOptionCorrect(selectedChoice: number | undefined, optionIndex: number, answerIndex: number) {
		return shouldShowFeedback(selectedChoice) && optionIndex === answerIndex;
	}

	function isOptionIncorrect(selectedChoice: number | undefined, optionIndex: number, answerIndex: number) {
		return shouldShowFeedback(selectedChoice) && selectedChoice === optionIndex && optionIndex !== answerIndex;
	}

	const questionBtnClass = (selectedChoice: number | undefined, answerIndex: number) => {
		if (!shouldShowFeedback(selectedChoice)) return '';
		return selectedChoice === answerIndex ? 'correct' : 'incorrect';
	};

	onMount(() => {
		const timer = setInterval(() => {
			if (!isFinished) {
				sessionDuration += 1;
				durationByQ[currentQuestionWip.qid] = (durationByQ[currentQuestionWip.qid] || 0) + 1;
			} else {
				if (session.kind.is === 'exam' && session.kind.initial_time <= sessionDuration) {
					finishSession();
					clearInterval(timer);
				}
			}
		}, 1000);
		return () => clearInterval(timer);
	});
</script>

<div class="layout-grid">
	<!-- Left Column: Quiz Content or Summary -->
	<div class="quiz-content">
		{#if finishData !== undefined}
			<div class="summary-card">
				<h2>Session Terminée</h2>
				<div class="score-display">
					<div class="score-circle">
						<span class="score-value">{Math.round((finishData.score / session.questions.length) * 100)}%</span>
						<span class="score-label">Score</span>
					</div>
					<div class="stats-grid">
						<div class="stat-item">
							<span class="stat-value">{finishData.score} / {session.questions.length}</span>
							<span class="stat-label">Réponses correctes</span>
						</div>
						<div class="stat-item">
							<span class="stat-value">{formatTime(sessionDuration)}</span>
							<span class="stat-label">Temps total</span>
						</div>
					</div>
				</div>
				<div class="actions">
					<button class="primary-btn" onclick={() => goto('/')}>Retour à l'accueil</button>
				</div>
			</div>
		{:else}
			<div class="question-header">
				<div class="quiz-meta">
					<span>{formatTime(timeShown)}</span>
					<span>Q {currentIndex + 1} / {session.questions.length || 120}</span>
				</div>
			</div>

			<div class="question-card">
				<h2>{currentQuestionDisplay.content}</h2>
				<div class="options-grid" class:locked={shouldShowFeedback(currentQuestionWip.selected_choice)}>
					{#each currentQuestionDisplay.choices as option, i (i)}
						<!-- svelte-ignore a11y_click_events_have_key_events -->
						<!-- svelte-ignore a11y_no_static_element_interactions -->
						<div
							class="option"
							class:selected={currentQuestionWip.selected_choice === i}
							class:correct={isOptionCorrect(currentQuestionWip.selected_choice, i, currentQuestionDisplay.answer)}
							class:incorrect={isOptionIncorrect(currentQuestionWip.selected_choice, i, currentQuestionDisplay.answer)}
							onclick={() => handleSelect(i)}>
							<span class="option-letter">{letters[i]}</span>
							<span>{option}</span>
						</div>
					{/each}
				</div>
			</div>
		{/if}
	</div>

	<!-- Right Column: Sidebar -->
	<aside class="responses-sidebar">
		<h3>Réponses</h3>
		<div class="response-grid">
			{#each session.questions as q, i}
				<!-- svelte-ignore a11y_click_events_have_key_events -->
				<!-- svelte-ignore a11y_no_static_element_interactions -->
				<div
					class={`response-btn ${questionBtnClass(q.selected_choice, $questions[q.qid].answer)} ${i === currentIndex ? 'current' : ''}`}
					onclick={() => goToQuestion(i)}>
					{i + 1}
				</div>
			{/each}
		</div>

		<div class="sidebar-actions">
			<button class="sidebar-btn cancel" onclick={cancelSession}>Annuler</button>
			{#if !isFinished}
				<button class="sidebar-btn finish" onclick={finishSession}>Terminer</button>
			{/if}
		</div>
	</aside>
</div>

<style>
	.layout-grid {
		display: grid;
		grid-template-columns: 1fr 300px;
		gap: 40px;
		max-width: 1200px;
		margin: 0 auto;
	}

	/* Quiz Content Column */
	.quiz-content {
		display: flex;
		flex-direction: column;
		gap: 28px;
	}

	.question-header {
		display: flex;
		justify-content: flex-end;
		align-items: center;
	}

	.quiz-meta {
		display: flex;
		align-items: center;
		gap: 20px;
		font-weight: 600;
		color: var(--text-muted);
	}

	/* Question Card */
	.question-card {
		padding: 30px;
		border-radius: var(--radius-xl);
		background: var(--glass-bg-strong);
		backdrop-filter: blur(28px) saturate(160%);
		border: 1px solid var(--glass-border);
		box-shadow: var(--glass-shadow);
	}

	.question-card h2 {
		margin: 0 0 30px;
		font-size: 22px;
		line-height: 1.4;
	}

	.options-grid {
		display: grid;
		gap: 18px;
	}

	.option {
		padding: 18px 24px;
		border-radius: 16px; /* --radius-l */
		background: rgba(255, 255, 255, 0.6);
		border: 1px solid var(--glass-border);
		cursor: pointer;
		display: flex;
		align-items: center;
		gap: 18px;
		transition: all 0.2s ease;
	}

	.option:hover {
		background: var(--glass-bg-strong);
		transform: translateY(-2px);
	}

	.option.correct {
		background: #d4edda;
		border-color: #c3e6cb;
		color: #155724;
	}

	.option.correct .option-letter {
		color: #155724;
	}

	.option.incorrect {
		background: #f8d7da;
		border-color: #f5c6cb;
		color: #721c24;
	}

	.option.incorrect .option-letter {
		color: #721c24;
	}

	.option.selected {
		background: var(--card-blue);
		color: white;
		border-color: transparent;
	}

	.option.selected.correct {
		background: #28a745;
		color: white;
	}
	.option.selected.correct .option-letter {
		color: white;
	}

	.option.selected.incorrect {
		background: #dc3545;
		color: white;
	}
	.option.selected.incorrect .option-letter {
		color: white;
	}

	.option-letter {
		font-weight: 700;
		font-size: 20px;
		color: var(--card-blue);
	}

	.option.selected .option-letter {
		color: white;
	}

	.options-grid.locked .option {
		cursor: default;
		pointer-events: none;
	}

	.responses-sidebar {
		padding: 30px;
		border-radius: var(--radius-xl);
		background: var(--glass-bg-strong);
		backdrop-filter: blur(28px) saturate(160%);
		border: 1px solid var(--glass-border);
		box-shadow: var(--glass-shadow);
		height: fit-content;
		display: flex;
		flex-direction: column;
		gap: 20px;
	}

	.responses-sidebar h3 {
		margin: 0;
		font-size: 18px;
	}

	.response-grid {
		display: grid;
		grid-template-columns: repeat(5, 1fr);
		gap: 10px;
	}

	.response-btn {
		width: 40px;
		height: 40px;
		border-radius: 12px; /* --radius-m */
		background: rgba(255, 255, 255, 0.6);
		border: 1px solid var(--glass-border);
		box-sizing: border-box;
		display: flex;
		align-items: center;
		justify-content: center;
		font-weight: 600;
		cursor: pointer;
		transition: all 0.2s ease;
		font-size: 14px;
		color: var(--text-dark);
	}

	.response-btn:hover {
		background: var(--card-blue);
		color: white;
		border: 1px solid var(--card-blue);
	}

	.response-btn.current {
		background: var(--card-blue);
		color: white;
		border: 1px solid var(--card-blue);
	}

	.response-btn.correct {
		background: #28a745;
		color: white;
		border: 1px solid #28a745;
	}

	.response-btn.incorrect {
		background: #dc3545;
		color: white;
		border: 1px solid #dc3545;
	}

	.response-btn.current.incorrect {
		border: 1px solid #dc3545;
		background: white;
		color: #dc3545;
	}

	.response-btn.current.correct {
		border: 1px solid #28a745;
		background: white;
		color: #28a745;
	}

	.sidebar-actions {
		display: flex;
		flex-direction: column;
		gap: 10px;
		margin-top: 10px;
		padding-top: 20px;
		border-top: 1px solid var(--glass-border);
	}

	.sidebar-btn {
		width: 100%;
		padding: 12px;
		border-radius: 12px;
		font-weight: 600;
		cursor: pointer;
		transition: all 0.2s;
		font-size: 14px;
	}

	.sidebar-btn.cancel {
		background: transparent;
		border: 1px solid var(--glass-border);
		color: var(--text-muted);
	}

	.sidebar-btn.cancel:hover {
		background: rgba(0, 0, 0, 0.05);
		color: var(--text-dark);
	}

	.sidebar-btn.finish {
		background: var(--card-blue);
		border: 1px solid var(--card-blue);
		color: white;
	}

	.sidebar-btn.finish:hover {
		background: var(--card-indigo);
		border-color: var(--card-indigo);
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
	}

	.summary-card h2 {
		margin: 0 0 40px;
		font-size: 24px;
		font-weight: 700;
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
		width: 160px;
		height: 160px;
		border-radius: 50%;
		border: 8px solid var(--card-blue);
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		background: rgba(255, 255, 255, 0.5);
	}

	.score-value {
		font-size: 42px;
		font-weight: 800;
		color: var(--card-blue);
		line-height: 1;
	}

	.score-label {
		font-size: 14px;
		text-transform: uppercase;
		letter-spacing: 1px;
		color: var(--text-muted);
		margin-top: 4px;
	}

	.stats-grid {
		display: grid;
		grid-template-columns: 1fr 1fr;
		gap: 20px;
		width: 100%;
		max-width: 500px;
	}

	.stat-item {
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 8px;
	}

	.stat-value {
		font-size: 24px;
		font-weight: 700;
		color: var(--text-dark);
	}

	.stat-label {
		font-size: 14px;
		color: var(--text-muted);
	}

	.actions {
		display: flex;
		justify-content: center;
		width: 100%;
	}

	.primary-btn {
		background: var(--card-blue);
		color: white;
		border: none;
		padding: 14px 32px;
		border-radius: 50px;
		font-weight: 600;
		font-size: 16px;
		cursor: pointer;
		transition:
			transform 0.2s,
			box-shadow 0.2s;
	}

	.primary-btn:hover {
		transform: translateY(-2px);
		box-shadow: 0 4px 12px rgba(47, 128, 237, 0.3);
	}

	.responses-sidebar h3 {
		margin: 0 0 20px;
		font-size: 18px;
	}

	.response-grid {
		display: grid;
		grid-template-columns: repeat(5, 1fr);
		gap: 10px;
	}

	.response-btn {
		width: 40px;
		height: 40px;
		border-radius: 12px; /* --radius-m */
		background: rgba(255, 255, 255, 0.6);
		border: 1px solid var(--glass-border);
		box-sizing: border-box;
		display: flex;
		align-items: center;
		justify-content: center;
		font-weight: 600;
		cursor: pointer;
		transition: all 0.2s ease;
		font-size: 14px;
		color: var(--text-dark);
	}

	.response-btn:hover {
		background: var(--card-blue);
		color: white;
		border: none;
	}

	.response-btn.current {
		background: var(--card-blue);
		color: white;
		border: none;
	}

	.response-btn.correct {
		background: #28a745;
		color: white;
		border: none;
	}

	.response-btn.incorrect {
		background: #dc3545;
		color: white;
		border: none;
	}

	.response-btn.current.incorrect {
		border: 2px solid #dc3545;
		background: white;
		color: #dc3545;
	}

	.response-btn.current.correct {
		border: 2px solid #28a745;
		background: white;
		color: #28a745;
	}

	@media (max-width: 900px) {
		.layout-grid {
			grid-template-columns: 1fr;
		}
	}
</style>
