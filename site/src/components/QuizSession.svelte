<script lang="ts">
	import { onMount } from 'svelte';
	import { type OngoingSession, type QuestionWip, type Qid } from '$lib/types';
	import { questions } from '$lib/stores/questions';
	import {log} from '$lib/log';

	let { session }: { session: OngoingSession } = $props();

	// Fallback mock data if session is empty (shouldn't happen in real usage)
	const mockQuestion = {
		id: 1,
		text: 'MOCKUP lanceur fusée:',
		options: [
			{ id: 'A', text: 'Une phase balistique' },
			{ id: 'B', text: 'Une phase tractive' },
			{ id: 'C', text: 'Une phase centrifuge' },
			{ id: 'D', text: 'Une phase propulsée' }
		],
		correctAnswer: 'D'
	};

	let currentIndex = $state(0);
	let timeElapsed = $state(0);

	let currentQuestionWip = $derived(session.questions[currentIndex]);

	let currentQuestionDisplay = $derived.by(() => {
		const currentQuestionData = $questions[currentQuestionWip.qid];
		if (currentQuestionData) {
			return {
				id: currentQuestionData.qid,
				text: currentQuestionData.content,
				options: [
					{ id: 'A', text: currentQuestionData.choice_a },
					{ id: 'B', text: currentQuestionData.choice_b },
					{ id: 'C', text: currentQuestionData.choice_c },
					{ id: 'D', text: currentQuestionData.choice_d }
				],
				correctAnswer: ['A', 'B', 'C', 'D'][currentQuestionData.answer]
			};
		} else {
			log.error(`Question data not found for qid: ${currentQuestionWip.qid}, using mock question.`);
		}
		return mockQuestion;
	});

	let selectedAnswer = $state<string | null>(null);

	// Sync selection with session state (mock for now, would update store in real app)
	// $effect(() => {
	// 	// Reset local selection when question changes
	// 	// In a real app, we'd check if session.questions[currentIndex].selected_choice is set
	// 	selectedAnswer = null;
	// 	if (currentQuestionWip?.selected_choice) {
	// 		const choices = ['A', 'B', 'C', 'D'];
	// 		selectedAnswer = choices[currentQuestionWip.selected_choice - 1];
	// 	}
	// });

	function formatTime(seconds: number) {
		const hrs = Math.floor(seconds / 3600);
		const mins = Math.floor((seconds % 3600) / 60);
		const secs = seconds % 60;
		return `${hrs.toString().padStart(2, '0')}:${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
	}

	function handleSelect(optionId: string) {
		selectedAnswer = optionId;
		// In a real app, dispatch an event or update the store here
		// const choiceIndex = ['A', 'B', 'C', 'D'].indexOf(optionId) + 1;
		// updateSession(session.id, currentIndex, choiceIndex);
	}

	function goToQuestion(index: number) {
		currentIndex = index;
	}

	onMount(() => {
		const timer = setInterval(() => {
			timeElapsed++;
		}, 1000);
		return () => clearInterval(timer);
	});
</script>

<div class="layout-grid">
	<!-- Left Column: Quiz Content -->
	<div class="quiz-content">
		<div class="question-header">
			<div class="quiz-meta">
				<span>{formatTime(timeElapsed)}</span>
				<span>Q {currentIndex + 1} / {session.questions.length || 120}</span>
			</div>
		</div>

		<div class="question-card">
			<h2>{currentQuestionDisplay.text}</h2>
			<div class="options-grid">
				{#each currentQuestionDisplay.options as option}
					<!-- svelte-ignore a11y_click_events_have_key_events -->
					<!-- svelte-ignore a11y_no_static_element_interactions -->
					<div class="option" class:selected={selectedAnswer === option.id} onclick={() => handleSelect(option.id)}>
						<span class="option-letter">{option.id}</span>
						<span>{option.text}</span>
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
				<div class="response-btn" class:current={i === currentIndex} onclick={() => goToQuestion(i)}>
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

	.option.selected {
		background: var(--card-blue);
		color: white;
		border-color: transparent;
	}

	.option-letter {
		font-weight: 700;
		font-size: 20px;
		color: var(--card-blue);
	}

	.option.selected .option-letter {
		color: white;
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

	@media (max-width: 900px) {
		.layout-grid {
			grid-template-columns: 1fr;
		}
	}
</style>
