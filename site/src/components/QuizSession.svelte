<script lang="ts">
	// TODO FIXME this should really not be a component
	// but a page, or split differently
	import { onMount } from 'svelte';
	import { type OngoingSession, type Attempt, type Timestamp, type AttemptId } from '$lib/types';
	import { questions } from '$lib/stores/questions';
	import { addAttempt } from '$lib/stores/attempt';
	import { unsafeRandomId } from '$lib/random';

	// need to be a state
	let { session = $bindable(), sessionDuration = $bindable() }: { session: OngoingSession; sessionDuration: number } =
		$props();

	let currentIndex = $state(0);

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
		// If immediate checking is on, and we already selected a choice, do nothing (lock it)
		if (session.check_answer_immediate && session.questions[currentIndex].selected_choice !== undefined) {
			return;
		}

		session.questions[currentIndex].selected_choice = choiceNo;

		if (session.check_answer_immediate) {
			const isCorrect = choiceNo === currentQuestionDisplay.answer;

			if (isCorrect) {
				session.questions[currentIndex].correct_choice = choiceNo;
			}

			const attempt: Attempt = {
				id: unsafeRandomId({ prefix: 'att' }) as AttemptId,
				qid: currentQuestionDisplay.qid,
				session_id: session.id,
				selected_choice: choiceNo,
				correct: isCorrect,
				timestamp: Date.now() as Timestamp,
				duration_s: 0,
				notes: undefined
			};
			addAttempt(attempt);
		}
	}

	function goToQuestion(index: number) {
		currentIndex = index;
	}

	function shouldShowFeedback(selectedChoice: number | undefined) {
		return session.kind.is !== 'exam' && selectedChoice !== undefined;
	}

	function isOptionCorrect(selectedChoice: number | undefined, optionIndex: number, answerIndex: number) {
		return shouldShowFeedback(selectedChoice) && optionIndex === answerIndex;
	}

	function isOptionIncorrect(selectedChoice: number | undefined, optionIndex: number, answerIndex: number) {
		return shouldShowFeedback(selectedChoice) && selectedChoice === optionIndex && optionIndex !== answerIndex;
	}

	function isQuestionCorrect(selectedChoice: number | undefined, answerIndex: number) {
		return shouldShowFeedback(selectedChoice) && selectedChoice === answerIndex;
	}

	function isQuestionIncorrect(selectedChoice: number | undefined, answerIndex: number) {
		return shouldShowFeedback(selectedChoice) && selectedChoice !== answerIndex;
	}

	const questionBtnClass = (selectedChoice: number | undefined, answerIndex: number) => {
		if (!shouldShowFeedback(selectedChoice)) return '';
		return selectedChoice === answerIndex ? 'correct' : 'incorrect';
	};

	onMount(() => {
		const timer = setInterval(() => {
			sessionDuration += 1;
		}, 1000);
		return () => clearInterval(timer);
	});
</script>

<div class="layout-grid">
	<!-- Left Column: Quiz Content -->
	<div class="quiz-content">
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

	/* Responses Sidebar */
	.responses-sidebar {
		padding: 30px;
		border-radius: var(--radius-xl);
		background: var(--glass-bg-strong);
		backdrop-filter: blur(28px) saturate(160%);
		border: 1px solid var(--glass-border);
		box-shadow: var(--glass-shadow);
		height: fit-content;
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
