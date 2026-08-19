<script lang="ts">
	// should this be a component or page?
	import { onMount, tick } from 'svelte';
	import { log } from '$lib/log';
	import { go } from '$lib/go';
	import type { OngoingSession, Qid, QuestionWip, Second } from '$lib/types';
	import { zeroSecond, inc } from '$lib/types';
	import { formatTime } from '$lib/utils';
	import { questions } from '$lib/stores/questions';
	import { preferences } from '$lib/stores/preferences.svelte';
	import { imageUrl } from '$lib/images';
	import { reportQuestion } from '$lib/report';
	import Toggle from '../components/Toggle.svelte';

	let {
		session = $bindable(),
		sessionDuration = $bindable(),
		durationByQ = $bindable(),
		onSessionFinish,
		onSessionCancel
	}: {
		session: OngoingSession;
		sessionDuration: Second;
		durationByQ: Record<Qid, Second>;
		onSessionCancel: () => void;
		onSessionFinish: () => void;
	} = $props();

	let currentIndex = $state(0);

	let responseGrid: HTMLDivElement;

	const letters = ['A', 'B', 'C', 'D'];

	let currentQuestionWip = $derived(session.questions[currentIndex]);
	let timeShown = $derived.by(() => {
		if (session.kind.is === 'exam') {
			return session.kind.initialTime - sessionDuration;
		}
		return sessionDuration;
	});

	let currentQuestionDisplay = $derived($questions[currentQuestionWip.qid]);

	let progressPercent = $derived(
		session.questions.length > 0
			? (session.questions.filter((q) => q.selectedChoice !== undefined).length / session.questions.length) * 100
			: 0
	);

	function handleSelect(choiceNo: number) {
		const isStudy = session.kind.is === 'study';
		// if correction already shown
		if (session.questions[currentIndex].correctChoice !== undefined) {
			return;
		}

		session.questions[currentIndex].selectedChoice = choiceNo;

		if (isStudy) {
			session.questions[currentIndex].correctChoice = currentQuestionDisplay.answer;
		}
		// in study mode, only to the next question if answered correctly
		if (
			preferences.current.autoAdvance &&
			(session.questions[currentIndex].correctChoice === undefined ||
				session.questions[currentIndex].correctChoice === session.questions[currentIndex].selectedChoice)
		) {
			const next = session.questions
				.slice(currentIndex)
				.concat(session.questions.slice(0, currentIndex))
				.find((wip) => wip.selectedChoice === undefined);
			if (next) {
				log.log('next', next);
				currentIndex = session.questions.findIndex((wip) => wip.qid == next.qid);
				scrollCurrentIntoView();
			}
		}
	}

	function goToQuestion(index: number) {
		const count = session.questions.length;
		if (count === 0) return;
		currentIndex = ((index % count) + count) % count;
		scrollCurrentIntoView();
	}

	// Keep the response button of the current question in sight in the sidebar,
	// especially when the sidebar scrolls horizontally on mobile.
	async function scrollCurrentIntoView() {
		await tick();
		responseGrid?.querySelector<HTMLElement>('.response-btn.current')?.scrollIntoView({
			behavior: 'smooth',
			block: 'nearest',
			inline: 'nearest'
		});
	}

	async function reportCurrentQuestion() {
		const sentence = window.prompt(
			"Un doute, une erreur, une question mal catégoriée ? Merci de nous prévenir, même si vous n'êtes pas sûr !"
		);
		if (sentence === null || sentence.trim() === '') return;
		await reportQuestion(sentence.trim(), currentQuestionWip.qid);
	}

	function finishSession() {
		log.log('before onSessionFinish');
		// `onSessionFinish` "might" erase it, so save before
		const sessionId = session.id;
		// TODO FIXME at some point mvoe it back here, it's not independent...
		onSessionFinish();
		log.log('after onSessionFinish');
		go(`/sessions/${sessionId}`);
	}

	function cancelSession() {
		onSessionCancel();
		go('/');
	}

	function isOptionCorrect(wip: QuestionWip, optionIndex: number) {
		return wip.correctChoice !== undefined && optionIndex === wip.correctChoice;
	}

	function isOptionIncorrect(wip: QuestionWip, optionIndex: number) {
		return wip.correctChoice !== undefined && optionIndex !== wip.correctChoice && optionIndex === wip.selectedChoice;
	}

	const questionBtnClass = (wip: QuestionWip) => {
		if (wip.correctChoice === undefined) return wip.selectedChoice !== undefined ? 'filled' : '';
		return wip.correctChoice === wip.selectedChoice ? 'correct' : 'incorrect';
	};

	onMount(() => {
		scrollCurrentIntoView();
		const timer = setInterval(() => {
			// time spent looking at an answer is not taken into account
			if (currentQuestionWip.correctChoice === undefined) {
				sessionDuration = inc(sessionDuration);
				durationByQ[currentQuestionWip.qid] = inc(durationByQ[currentQuestionWip.qid] || zeroSecond);
			}
			// do NOT put this as an $effect
			if (session.kind.is === 'exam' && session.kind.initialTime <= sessionDuration) {
				finishSession();
			}
		}, 1000);
		return () => clearInterval(timer);
	});
</script>

<div class="layout-grid">
	<!-- Left Column: Quiz Content -->
	<div class="quiz-content">
		<div class="question-header">
			<div class="progress">
				<div class="progress-fill" style="width: {progressPercent}%"></div>
			</div>
			<div class="quiz-meta">
				<span>{formatTime(timeShown)}</span>
				<span>Q {currentIndex + 1} / {session.questions.length || 120}</span>
			</div>
			<div class="nav-btns">
				<button
					class="nav-btn"
					onclick={() => goToQuestion(currentIndex - 1)}
					title="Question précédente"
					aria-label="Question précédente">
					<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="16" height="16" fill="currentColor">
						<path d="M15.41 7.41 14 6l-6 6 6 6 1.41-1.41L10.83 12z" />
					</svg>
				</button>
				<button
					class="nav-btn"
					onclick={() => goToQuestion(currentIndex + 1)}
					title="Question suivante"
					aria-label="Question suivante">
					<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="16" height="16" fill="currentColor">
						<path d="M10 6 8.59 7.41 13.17 12l-4.58 4.59L10 18l6-6z" />
					</svg>
				</button>
			</div>
			<button
				class="report-btn"
				onclick={reportCurrentQuestion}
				title="Signaler la question"
				aria-label="Signaler la question">
				<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="16" height="16" fill="currentColor">
					<g data-name="alert-circle">
						<rect width="24" height="24" opacity="0" />
						<path d="M12 2a10 10 0 1 0 10 10A10 10 0 0 0 12 2zm0 18a8 8 0 1 1 8-8 8 8 0 0 1-8 8z" />
						<circle cx="12" cy="16" r="1" />
						<path d="M12 7a1 1 0 0 0-1 1v5a1 1 0 0 0 2 0V8a1 1 0 0 0-1-1z" />
					</g>
				</svg>
			</button>
		</div>

		<div class="question-card">
			<h2>{currentQuestionDisplay.content}</h2>
			{#if currentQuestionDisplay.attachment_link}
				<div class="annexes">
					<img
						src={imageUrl(currentQuestionDisplay.attachment_link)}
						alt="Annexe {currentQuestionDisplay.attachment_link}"
						class="question-img"
						loading="lazy" />
				</div>
			{/if}
			<div class="options-grid" class:locked={currentQuestionWip.correctChoice !== undefined}>
				{#each currentQuestionDisplay.choices as option, i (i)}
					<!-- svelte-ignore a11y_click_events_have_key_events -->
					<!-- svelte-ignore a11y_no_static_element_interactions -->
					<div
						class="option"
						class:selected={currentQuestionWip.selectedChoice === i}
						class:correct={isOptionCorrect(currentQuestionWip, i)}
						class:incorrect={isOptionIncorrect(currentQuestionWip, i)}
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
		<div class="response-grid" bind:this={responseGrid}>
			{#each session.questions as q, i (i)}
				<!-- svelte-ignore a11y_click_events_have_key_events -->
				<!-- svelte-ignore a11y_no_static_element_interactions -->
				<div
					class={`response-btn ${questionBtnClass(q)} ${i === currentIndex ? 'current' : ''}`}
					onclick={() => goToQuestion(i)}>
					{i + 1}
				</div>
			{/each}
		</div>

		<div class="sidebar-actions">
			<div class="toggle-container">
				<label for="auto-advance-toggle">Question suivante auto</label>
				<Toggle bind:checked={preferences.current.autoAdvance} />
			</div>
			<button class="sidebar-btn cancel" onclick={cancelSession}>Annuler</button>
			<button class="sidebar-btn finish" onclick={finishSession}>Terminer</button>
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
		gap: 16px;
	}

	.progress {
		flex: 1;
		height: 6px;
		border-radius: 999px;
		background: rgba(0, 0, 0, 0.08);
		overflow: hidden;
		flex-shrink: 0;
	}

	.progress-fill {
		height: 100%;
		background: var(--card-blue);
		border-radius: 999px;
		transition: width 0.25s ease;
	}

	.nav-btns {
		display: inline-flex;
		align-items: center;
		gap: 6px;
		flex-shrink: 0;
	}

	.nav-btn {
		display: inline-flex;
		align-items: center;
		justify-content: center;
		width: 30px;
		height: 30px;
		padding: 0;
		border: 1px solid var(--glass-border);
		border-radius: 999px;
		background: rgba(255, 255, 255, 0.6);
		color: var(--text-muted);
		cursor: pointer;
		transition:
			background 0.2s ease,
			color 0.2s ease;
	}

	.nav-btn:hover {
		background: var(--card-blue);
		color: white;
	}

	.report-btn {
		display: inline-flex;
		align-items: center;
		justify-content: center;
		width: 30px;
		height: 30px;
		padding: 0;
		border: 1px solid var(--glass-border);
		border-radius: 999px;
		background: rgba(255, 255, 255, 0.6);
		color: var(--text-muted);
		cursor: pointer;
		flex-shrink: 0;
		transition:
			background 0.2s ease,
			color 0.2s ease;
	}

	.report-btn:hover {
		background: var(--card-blue);
		color: white;
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
		min-height: calc(3 * 1.4em);
	}

	.annexes {
		margin: 0 0 24px;
		text-align: center;
	}

	.question-img {
		max-width: 100%;
		max-height: 40vh;
		height: auto;
		border-radius: 12px;
		border: 1px solid var(--glass-border);
		background: #fff;
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
		display: flex;
		flex-direction: column;
		gap: 20px;
		min-height: 0;
		position: sticky;
		top: var(--gap-main);
		align-self: start;
		max-height: calc(90vh - var(--header-height) - var(--gap-main));
	}

	.responses-sidebar h3 {
		margin: 0;
		font-size: 18px;
		flex-shrink: 0;
	}

	.response-grid {
		display: grid;
		grid-template-columns: repeat(5, 1fr);
		gap: 10px;
		flex: 1;
		min-height: 0;
		overflow-y: auto;
		overflow-x: hidden;
	}

	.response-btn {
		width: 100%;
		min-width: 0;
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
		border: 1px solid var(--card-blue-solid);
	}

	.response-btn.filled {
		background: var(--card-blue);
		color: white;
		border: 1px solid var(--card-blue-solid);
	}

	.response-btn.current,
	.response-btn.current.filled {
		background: white;
		color: var(--card-blue-solid);
		border: 1px solid var(--card-blue-solid);
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
		border-top: 1px solid var(--glass-border);
		flex-shrink: 0;
	}

	.toggle-container {
		display: flex;
		align-items: center;
		justify-content: space-between;
		padding: 12px 10px;
		font-size: 14px;
		font-weight: 500;
		color: var(--text-dark);
		border-bottom: 1px solid var(--glass-border);
		margin-bottom: 10px;
	}

	.toggle-container label {
		cursor: pointer;
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
		border: 1px solid var(--card-blue-solid);
		color: white;
	}

	.sidebar-btn.finish:hover {
		background: var(--card-indigo);
		border-color: var(--card-indigo-solid);
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
		border: 8px solid var(--card-blue-solid);
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

	@media (max-width: 900px) {
		.layout-grid {
			grid-template-columns: 1fr;
			gap: 12px;
		}

		.quiz-content {
			gap: 16px;
		}

		.responses-sidebar {
			flex-direction: column;
			gap: 8px;
			padding: 10px 12px;
			overflow: hidden;
			position: sticky;
			top: auto;
			bottom: 0;
			max-height: none;
		}

		.responses-sidebar h3 {
			display: none;
		}

		.response-grid {
			display: flex;
			flex-direction: row;
			flex: 0 0 auto;
			width: 100%;
			min-height: 0;
			overflow-x: auto;
			overflow-y: hidden;
			gap: 6px;
		}

		.response-btn {
			width: 36px;
			min-width: 36px;
			flex: 0 0 36px;
			height: 36px;
		}

		.toggle-container {
			padding: 6px 4px;
			margin-bottom: 0;
			font-size: 13px;
		}

		.sidebar-actions {
			flex-direction: row;
			gap: 8px;
			margin-top: 0;
			padding-top: 8px;
		}

		.sidebar-btn {
			width: auto;
			flex: 1;
			padding: 10px 14px;
		}
	}

	@media (max-width: 768px) {
		.question-card h2 {
			font-size: 19px;
		}

		.option {
			font-size: 15px;
		}

		.option-letter {
			font-size: 18px;
		}

		.question-img {
			max-height: 32vh;
		}
	}

	@media (max-width: 480px) {
		.question-card h2 {
			font-size: 16px;
		}

		.option {
			font-size: 14px;
		}

		.option-letter {
			font-size: 16px;
		}

		.quiz-meta {
			font-size: 13px;
		}

		.question-img {
			max-height: 28vh;
		}
	}
</style>
