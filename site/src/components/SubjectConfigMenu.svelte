<script lang="ts">
	import { goto } from '$app/navigation';
	import { Chapters } from '$lib/types';
	import type { Subject } from '$lib/types';
	import Toggle from './Toggle.svelte';

	let {
		subjectId,
		title,
		color,
		totalQuestions,
		onClose
	}: {
		subjectId: number;
		title: string;
		color: string;
		totalQuestions: number;
		onClose: () => void;
	} = $props();

	// Filter chapters for this subject
	const subjectChapters = Chapters.filter((c) => c.subject === subjectId);

	// State
	let selectedChapters = $state<number[]>(subjectChapters.map((c) => c.id)); // Default all selected
	let isAllQuestions = $state(false);
	let sliderValue = $state(0);
	$effect(() => {
		sliderValue = Math.min(20, totalQuestions);
	});

	function toggleChapter(id: number) {
		if (selectedChapters.includes(id)) {
			selectedChapters = selectedChapters.filter((c) => c !== id);
		} else {
			selectedChapters = [...selectedChapters, id];
		}
	}

	function selectAllChapters() {
		if (selectedChapters.length === subjectChapters.length) {
			selectedChapters = [];
		} else {
			selectedChapters = subjectChapters.map((c) => c.id);
		}
	}

	function startQuiz() {
		const params = new URLSearchParams();
		params.set('subject', subjectId.toString());

		if (!isAllQuestions) {
			params.set('count', sliderValue.toString());
		}

		if (subjectChapters.length > 0 && selectedChapters.length > 0 && selectedChapters.length < subjectChapters.length) {
			params.set('chapters', selectedChapters.join(','));
		}

		goto(`/quiz?${params.toString()}`);
	}
</script>

<div class="overlay" onclick={onClose} role="presentation">
	<div
		class="menu"
		style="--accent-color: {color}"
		onclick={(e) => e.stopPropagation()}
		role="dialog"
		aria-modal="true"
		aria-label="Configuration du quiz">
		<div class="header" style="background: {color}">
			<h2>{title}</h2>
			<button class="close-btn" onclick={onClose} aria-label="Fermer">✕</button>
		</div>

		<div class="content">
			{#if subjectChapters.length > 0}
				<div class="section">
					<div class="section-header">
						<h3>Chapitres</h3>
						<button class="text-btn" onclick={selectAllChapters}>
							{selectedChapters.length === subjectChapters.length ? 'Tout désélectionner' : 'Tout sélectionner'}
						</button>
					</div>
					<div class="chapters-grid">
						{#each subjectChapters as chapter}
							<label class="chapter-item">
								<span class="label-text">{chapter.name}</span>
								<div class="toggle-wrapper">
									<input
										type="checkbox"
										checked={selectedChapters.includes(chapter.id)}
										onchange={() => toggleChapter(chapter.id)} />
									<span class="toggle-switch"></span>
								</div>
							</label>
						{/each}
					</div>
				</div>
			{/if}

			<div class="section">
				<div class="section-header">
					<h3>Nombre de questions</h3>
					{#if !isAllQuestions}
						<span class="count-value" style="color: {color}">{sliderValue}</span>
					{/if}
				</div>

				<div class="questions-control">
					<label class="chapter-item checkbox-row">
						<span class="label-text">Toutes les questions ({totalQuestions})</span>
						<div class="toggle-wrapper">
							<input type="checkbox" bind:checked={isAllQuestions} />
							<span class="toggle-switch"></span>
						</div>
					</label>

					{#if !isAllQuestions}
						<div class="slider-container">
							<input
								type="range"
								min="5"
								max={Math.min(50, totalQuestions)}
								bind:value={sliderValue}
								class="range-slider" />
							<div class="range-labels">
								<span>5</span>
								<span>{Math.min(50, totalQuestions)}</span>
							</div>
						</div>
					{/if}
				</div>
			</div>
		</div>

		<div class="footer">
			<button class="cancel-btn" onclick={onClose}>Annuler</button>
			<button
				class="start-btn"
				style="--btn-color: {color}"
				onclick={startQuiz}
				disabled={subjectChapters.length > 0 && selectedChapters.length === 0}>
				Commencer le Quiz
			</button>
		</div>
	</div>
</div>

<style>
	.overlay {
		position: fixed;
		top: 0;
		left: 0;
		width: 100%;
		height: 100%;
		background: rgba(0, 0, 0, 0.4);
		backdrop-filter: blur(4px);
		z-index: 1000;
		display: flex;
		align-items: center;
		justify-content: center;
		padding: 20px;
	}

	.menu {
		background: white;
		width: 100%;
		max-width: 500px;
		border-radius: var(--radius-xl);
		overflow: hidden;
		box-shadow: 0 20px 50px rgba(0, 0, 0, 0.2);
		animation: popIn 0.3s cubic-bezier(0.16, 1, 0.3, 1);
		display: flex;
		flex-direction: column;
		max-height: 90vh;
	}

	@keyframes popIn {
		from {
			opacity: 0;
			transform: scale(0.95) translateY(10px);
		}
		to {
			opacity: 1;
			transform: scale(1) translateY(0);
		}
	}

	.header {
		padding: 24px 32px;
		color: white;
		display: flex;
		align-items: center;
		justify-content: space-between;
	}

	.header h2 {
		margin: 0;
		font-size: 22px;
		font-weight: 600;
	}

	.close-btn {
		background: none;
		border: none;
		color: white;
		font-size: 20px;
		cursor: pointer;
		opacity: 0.8;
		padding: 4px;
		line-height: 1;
		transition: opacity 0.2s;
	}

	.close-btn:hover {
		opacity: 1;
	}

	.content {
		padding: 32px;
		overflow-y: auto;
		display: flex;
		flex-direction: column;
		gap: 32px;
	}

	.section-header {
		display: flex;
		justify-content: space-between;
		align-items: baseline;
		margin-bottom: 16px;
	}

	.section h3 {
		margin: 0;
		font-size: 16px;
		font-weight: 600;
		color: #1a1a1a;
	}

	.text-btn {
		background: none;
		border: none;
		color: #666;
		font-size: 13px;
		cursor: pointer;
		text-decoration: underline;
		padding: 0;
	}

	.text-btn:hover {
		color: #333;
	}

	.chapters-grid {
		display: flex;
		flex-direction: column;
		gap: 12px;
	}

	.chapter-item {
		display: flex;
		align-items: center;
		justify-content: space-between;
		gap: 12px;
		cursor: pointer;
		user-select: none;
		padding: 12px 16px;
		background: #f8f9fa;
		border: 1px solid #eee;
		border-radius: 12px;
		transition: all 0.2s;
	}

	.chapter-item:hover {
		background: #f0f2f5;
		border-color: #e0e0e0;
	}

	.toggle-wrapper {
		position: relative;
		width: 50px;
		height: 30px;
	}

	.toggle-wrapper input {
		position: absolute;
		opacity: 0;
		cursor: pointer;
		height: 0;
		width: 0;
	}

	.toggle-switch {
		position: absolute;
		top: 0;
		left: 0;
		right: 0;
		bottom: 0;
		background-color: #ccc;
		transition: 0.4s;
		border-radius: 34px;
	}

	.toggle-switch:before {
		position: absolute;
		content: '';
		height: 22px;
		width: 22px;
		left: 4px;
		bottom: 4px;
		background-color: white;
		transition: 0.4s;
		border-radius: 50%;
		box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
	}

	.toggle-wrapper input:checked + .toggle-switch {
		background-color: var(--accent-color, #2f80ed);
	}

	.toggle-wrapper input:checked + .toggle-switch:before {
		transform: translateX(20px);
	}

	.label-text {
		font-size: 15px;
		color: #333;
		font-weight: 500;
		line-height: 1.4;
		flex: 1;
	}

	/* Remove old checkbox styles */
	/* .checkmark {
		display: none;
	} */

	.count-value {
		font-weight: 700;
		font-size: 18px;
	}

	.questions-control {
		display: flex;
		flex-direction: column;
		gap: 16px;
	}

	.checkbox-row {
		margin-bottom: 8px;
	}

	.slider-container {
		padding: 0 8px;
	}

	.range-slider {
		-webkit-appearance: none;
		appearance: none;
		width: 100%;
		height: 6px;
		background: #eee;
		border-radius: 4px;
		outline: none;
		margin: 12px 0;
	}

	.range-slider::-webkit-slider-thumb {
		-webkit-appearance: none;
		appearance: none;
		width: 24px;
		height: 24px;
		border-radius: 50%;
		background: var(--accent-color, #2f80ed);
		cursor: pointer;
		border: 4px solid white;
		box-shadow: 0 2px 6px rgba(0, 0, 0, 0.2);
		transition: transform 0.1s;
	}

	.range-slider::-webkit-slider-thumb:hover {
		transform: scale(1.1);
	}

	.range-labels {
		display: flex;
		justify-content: space-between;
		font-size: 12px;
		color: #999;
		font-weight: 500;
	}

	.footer {
		padding: 24px 32px;
		border-top: 1px solid #eee;
		display: flex;
		justify-content: flex-end;
		gap: 16px;
		background: #fbfbfb;
	}

	.cancel-btn {
		background: none;
		border: none;
		padding: 12px 24px;
		font-weight: 600;
		color: #666;
		cursor: pointer;
		border-radius: 50px;
		transition: background 0.2s;
	}

	.cancel-btn:hover {
		background: #eee;
		color: #333;
	}

	.start-btn {
		background: white;
		border: 2px solid var(--btn-color);
		color: var(--btn-color);
		padding: 12px 32px;
		font-weight: 700;
		cursor: pointer;
		border-radius: 50px;
		transition:
			all 0.2s,
			transform 0.2s;
	}

	.start-btn:hover:not(:disabled) {
		background: var(--btn-color);
		color: white;
		transform: translateY(-2px);
		box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
	}

	.start-btn:disabled {
		opacity: 0.5;
		cursor: not-allowed;
		transform: none;
		border-color: #ccc;
		color: #ccc;
	}
</style>
