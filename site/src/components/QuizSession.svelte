<script lang="ts">
	// TODO FIXME this should really not be a component
	// but a page, or split differently
	import { goto } from '$app/navigation';
	import { onMount } from 'svelte';
	import { type OngoingSession, type QuestionWip, type Qid } from '$lib/types';
	import { questions } from '$lib/stores/questions';
	import {log} from '$lib/log';
	import { ongoingSession } from "$lib/stores/session";


	// need to be a state
	//let { session }: { session: OngoingSession } = $props();

	let currentIndex = $state(0);

	if (!$ongoingSession) {
		log.error('No ongoing session found!');
		goto('/'); // Redirect to home or an error page
	}
	// updating `sessionNotReactive` will not trigger a re-render, but we will update it manually when needed
	// mostly used for typing.
	let sessionNotReactive = $ongoingSession!;

	let currentQuestionWip = $derived(sessionNotReactive.questions[currentIndex]);
	$inspect(currentQuestionWip);
	let timeShown = $derived(sessionNotReactive.kind.is === 'exam' ? sessionNotReactive.kind.time_left_s : sessionNotReactive.kind.duration_s);

	let currentQuestionDisplay = $derived($questions[currentQuestionWip.qid]);

	function formatTime(seconds: number) {
		const hrs = Math.floor(seconds / 3600);
		const mins = Math.floor((seconds % 3600) / 60);
		const secs = seconds % 60;
		return `${hrs.toString().padStart(2, '0')}:${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
	}

	function handleSelect(choiceNo: number) {
		// stores are not deeply reactive
		$ongoingSession.questions[currentIndex] = {...$ongoingSession.questions[currentIndex], selected_choice: choiceNo};
	
	}

	function goToQuestion(index: number) {
		currentIndex = index;
	}

	onMount(() => {
		const timer = setInterval(() => {
			if ($ongoingSession) {
				if ($ongoingSession.kind.is === 'exam') {
					$ongoingSession.kind.time_left_s = Math.max(0, $ongoingSession.kind.time_left_s - 1);
					// TODO add logic for when timer goes to zero
				} else if ($ongoingSession.kind.is === 'practice') {
					$ongoingSession.kind.duration_s += 1;
				}

			}

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
				<span>Q {currentIndex + 1} / {$ongoingSession.questions.length || 120}</span>
			</div>
		</div>

		<div class="question-card">
			<h2>{currentQuestionDisplay.content}</h2>
			<div class="options-grid">
				{#each currentQuestionDisplay.choices as option, i}
					<!-- svelte-ignore a11y_click_events_have_key_events -->
					<!-- svelte-ignore a11y_no_static_element_interactions -->
					<div class="option" class:selected={currentQuestionWip.selected_choice === i} onclick={() => handleSelect(i)}>
						<span class="option-letter">{i}</span>
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
			{#each $ongoingSession.questions as q, i}
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
