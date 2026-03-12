<script lang="ts">
	import { questions } from '$lib/stores/questions';
	import type { Question, Qid, Timestamp, Second, ExamSession } from '$lib/types';
	import { makeNewSession, sessionState, pastSessions, isExamSession } from '$lib/stores/session.svelte';
	import { unsafeRandomId } from '$lib/random';
	import { values } from '$lib/utils';
	import { go } from '$lib/go.svelte';

	// Derive unique years from the questions store, sort descending
	const years = $derived.by(() => {
		const allQs = values($questions);
		const yearSet = new Set<number>();
		for (const q of allQs) {
			yearSet.add(q.year);
		}
		return Array.from(yearSet).sort((a, b) => b - a);
	});

	const bestResultByYear: Record<number, number> = $derived.by(() => {
		const sessions: ExamSession[] = $pastSessions.filter(isExamSession);
		const bestByYear: Record<number, number> = {};
		for (const session of sessions) {
			const year = session.kind.year;
			const score = session.score;
			if (bestByYear[year] === undefined || score > bestByYear[year]) {
				bestByYear[year] = score;
			}
		}
		return bestByYear;
	});

	function handleYearClick(year: number) {
		const allQs = values($questions);
		const yearQuestions = allQs.filter((q) => q.year === year);
		// sort selected Questions by `question.no`
		yearQuestions.sort((a, b) => a.no - b.no);

		const selectedQids = yearQuestions.map((q) => q.qid);

		// TODO FIXME better think what to do here
		if (sessionState.current) {
			console.warn(`Overriding ongoing Session ${sessionState.current.id} with a new Session!`);
		}

		makeNewSession(`Annale ${year}`, selectedQids, {
			year,
			// 2h30
			// TODO FIXME handle English questions
			initialTime: (180 * 60) as Second
		});

		go('/quiz');
	}

	function getYearGradient(year: number) {
		const gradients = [
			'var(--card-blue)',
			'var(--card-indigo)',
			'var(--card-green)',
			'var(--card-orange)',
			'var(--card-red)',
			'var(--card-pink)'
		];
		// Use the year to deterministically pick a color
		return gradients[year % gradients.length];
	}
</script>

<div class="annales-page">
	<header class="header">
		<h1 class="gradient-text">Annales BIA</h1>
		<p class="subtitle">Pratiquez sur les examens officiels des années précédentes.</p>
	</header>

	<div class="years-grid">
		{#each years as year, i}
			<!-- svelte-ignore a11y_click_events_have_key_events -->
			<!-- svelte-ignore a11y_interactive_supports_focus -->
			<div
				class="year-card"
				style="background: {getYearGradient(year)}"
				onclick={() => handleYearClick(year)}
				role="button"
				style:animation-delay="{i * 0.05}s">
				<div class="card-content">
					<h2 class="year-title">{year}</h2>
					<span class="action-text">Commencer l'examen <span class="arrow">→</span></span>
				</div>
				<div class="card-glare"></div>
			</div>
		{/each}

		{#if years.length === 0}
			<div class="empty-state glass-panel">
				<p>Aucune annale n'a été trouvée dans la base de données.</p>
			</div>
		{/if}
	</div>
</div>

<style>
	.annales-page {
		max-width: 1000px;
		margin: 0 auto;
		padding: 40px 20px;
		display: flex;
		flex-direction: column;
		gap: 40px;
	}

	.header {
		text-align: center;
		animation: fade-in 0.8s ease-out;
	}

	.gradient-text {
		font-size: 3rem;
		font-weight: 800;
		margin: 0 0 12px 0;
		background: linear-gradient(135deg, var(--text-dark) 0%, #4a5568 100%);
		-webkit-background-clip: text;
		-webkit-text-fill-color: transparent;
		letter-spacing: -1px;
	}

	.subtitle {
		font-size: 1.2rem;
		color: var(--text-muted);
		margin: 0;
		font-weight: 500;
	}

	.years-grid {
		display: grid;
		grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
		gap: 24px;
	}

	.year-card {
		position: relative;
		border-radius: 32px; /* Super rounded, iOS style */
		padding: 32px;
		color: white;
		cursor: pointer;
		overflow: hidden;
		box-shadow:
			0 10px 30px rgba(0, 0, 0, 0.08),
			inset 0 1px 0 rgba(255, 255, 255, 0.2);
		transition:
			transform 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275),
			box-shadow 0.3s ease;
		animation: slide-up 0.6s cubic-bezier(0.165, 0.84, 0.44, 1) backwards;
	}

	.year-card:hover {
		transform: translateY(-6px) scale(1.02);
		box-shadow:
			0 20px 40px rgba(0, 0, 0, 0.12),
			inset 0 1px 0 rgba(255, 255, 255, 0.3);
	}

	.year-card:active {
		transform: scale(0.96);
		transition: transform 0.1s;
	}

	.card-content {
		position: relative;
		z-index: 2;
		display: flex;
		flex-direction: column;
		height: 100%;
	}

	.icon-wrapper {
		font-size: 2.5rem;
		margin-bottom: 16px;
		background: rgba(255, 255, 255, 0.2);
		width: 64px;
		height: 64px;
		display: flex;
		align-items: center;
		justify-content: center;
		border-radius: 20px;
		backdrop-filter: blur(10px);
		-webkit-backdrop-filter: blur(10px);
		border: 1px solid rgba(255, 255, 255, 0.1);
	}

	.year-title {
		font-size: 3rem;
		font-weight: 800;
		margin: 0 0 24px 0;
		letter-spacing: -2px;
		line-height: 1;
		text-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
	}

	.action-text {
		margin-top: auto;
		font-size: 1.1rem;
		font-weight: 600;
		display: flex;
		align-items: center;
		gap: 8px;
		opacity: 0.9;
		background: rgba(255, 255, 255, 0.2);
		padding: 12px 20px;
		border-radius: 100px; /* Pill shape button */
		width: fit-content;
		backdrop-filter: blur(10px);
		-webkit-backdrop-filter: blur(10px);
		transition:
			background 0.2s,
			gap 0.2s;
	}

	.year-card:hover .action-text {
		background: rgba(255, 255, 255, 0.3);
		gap: 12px; /* Arrow slides right */
	}

	.arrow {
		transition: transform 0.2s;
	}

	/* The iOS glare effect */
	.card-glare {
		position: absolute;
		top: 0;
		left: 0;
		width: 100%;
		height: 100%;
		background: linear-gradient(
			135deg,
			rgba(255, 255, 255, 0.4) 0%,
			rgba(255, 255, 255, 0) 40%,
			rgba(255, 255, 255, 0) 100%
		);
		z-index: 1;
		pointer-events: none;
	}

	.glass-panel {
		background: var(--glass-bg);
		border: 1px solid var(--glass-border);
		border-radius: var(--radius-xl);
		box-shadow: var(--glass-shadow);
		backdrop-filter: blur(12px);
		-webkit-backdrop-filter: blur(12px);
	}

	.empty-state {
		grid-column: 1 / -1;
		padding: 60px;
		text-align: center;
		color: var(--text-muted);
		font-size: 1.2rem;
	}

	@keyframes slide-up {
		0% {
			opacity: 0;
			transform: translateY(30px);
		}
		100% {
			opacity: 1;
			transform: translateY(0);
		}
	}

	@keyframes fade-in {
		0% {
			opacity: 0;
		}
		100% {
			opacity: 1;
		}
	}

	@media (max-width: 600px) {
		.years-grid {
			grid-template-columns: 1fr;
		}

		.gradient-text {
			font-size: 2.5rem;
		}
	}
</style>
