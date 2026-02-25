<script lang="ts">
	import { goto } from '$app/navigation';
	import {
		Chapters,
		type Subject,
		type ChapterId,
		type SessionId,
		type Timestamp,
		ChaptersBySubject,
		QBCtoList,
		type OngoingSession
	} from '$lib/types';
	import { unsafeRandomId } from '$lib/random';
	import { log } from '$lib/log';
	import { attempts } from '$lib/stores/attempt';
	import { questionsBySubject } from '$lib/stores/questions';
	import { sessionState } from '$lib/stores/session.svelte';
	import { type ChaptersState, getPotentialQuestions } from '$lib/state';
	import Toggle from './Toggle.svelte';

	let {
		subjectId,
		title,
		totalQuestions,
		onClose
	}: {
		subjectId: Subject;
		title: string;
		totalQuestions: number;
		onClose: () => void;
	} = $props();

	const subjectChapters = ChaptersBySubject[subjectId];

	const hasRest = $derived($questionsBySubject[subjectId]?.rest?.length > 0);

	let chaptersState = $state<ChaptersState>({
		onlyNew: true,
		selected: subjectChapters.map((c) => c.id),
		includeRest: true
	}); // Default all selected

	const allChaptersSelected = $derived(chaptersState.selected.length === subjectChapters.length);

	// working as is
	// testbed
	// https://svelte.dev/playground/acf7489de2d14863868eb867991898c7?version=5.49.1#H4sIAAAAAAAAE3VS0WrrMAz9FWEKS1lI7t1jlgT2DYP7Mg_mJi4zS-1gq-tK8L9fWUnbDLa8KNI5ko4lTcKqgxaVeH5XXvcQ0Hkd4GTwHfzR6iBysTcD2eplEngeEzcFKL5kPo1jET71gCm2U0H_FO-cRW2Ryog6dN6M2Eor0RxG5xGmkzeodoOOsPfuAHdzXslq7tbEvXMXTlGSU2BIODGoQ0DoFSpo4FIve_nzur2h3hG2CahQZ1NAX4EUZydFXHEG16mBaJLe4qVYldbefNKIqMLyW-zOWbaFpoUp0SR6jUdvgXRlm6Qkp475XJE7xO1jMozBfQN_pa3L2zhsPbbP6clgAkzMinU5tgywaga8K0j7DbmpYXhxF5wYuyOis-BsN5juo5lmyVcRD7F96nswqA91OXPbX7Pm3ilNikAfzY6zA6ADlriqQXtH_YWiQn_UMf_lfuYtfr-da2x1N-kt-ovPYF4IkWgZGR9JPjf_d5n2dSnLSt6Y1WwmtnGhs5_SeKBLLgXZxjdp4_cnvJKnzHAythfVXg1Bx_-Wf87FQQMAAA
	let potentialQuestions = $derived.by(() =>
		QBCtoList(getPotentialQuestions($attempts, $questionsBySubject, subjectId)(chaptersState))
	);

	// the difference with `potentialQuestions` is that we always pass all chapters
	// to display the counts correctly, even when the chapter is not selected
	let questionsCountByChapter = $derived.by(() =>
		getPotentialQuestions(
			$attempts,
			$questionsBySubject,
			subjectId
		)({
			onlyNew: chaptersState.onlyNew,
			selected: subjectChapters.map((c) => c.id),
			includeRest: true
		})
	);

	// DEBUG
	for (const qid of QBCtoList($questionsBySubject[subjectId])) {
		// test if in questionsCountByChapter
		const inPotential = QBCtoList(questionsCountByChapter).includes(qid);
		if (!inPotential) {
			log.log('not potential question', subjectId, qid);
		}
	}

	let totalAvailable = $derived(potentialQuestions.length);

	let sliderValue = $state(0);

	$effect(() => {
		sliderValue = Math.min(20, totalAvailable);
	});

	function toggleChapter(id: ChapterId) {
		if (chaptersState.selected.includes(id)) {
			chaptersState.selected = chaptersState.selected.filter((cid) => cid !== id);
		} else {
			chaptersState.selected.push(id);
		}
	}

	function selectAllChapters() {
		const restSelected = !hasRest || chaptersState.includeRest;

		if (allChaptersSelected && restSelected) {
			chaptersState.selected = [];
			if (hasRest) chaptersState.includeRest = false;
		} else {
			chaptersState.selected = subjectChapters.map((c) => c.id);
			if (hasRest) chaptersState.includeRest = true;
		}
	}

	function startQuiz() {
		const qids = structuredClone(potentialQuestions);

		// Shuffle questions
		for (let i = qids.length - 1; i > 0; i--) {
			const j = Math.floor(Math.random() * (i + 1));
			[qids[i], qids[j]] = [qids[j], qids[i]];
		}

		// Select the first N questions based on sliderValue
		const selectedQids = qids.slice(0, sliderValue);

		const newSession: OngoingSession = {
			id: unsafeRandomId({prefix: "ses"}) as SessionId, // Simple ID generation
			name: `Quiz ${title}`,
			created_at: Date.now() as Timestamp,
			kind: {
				is: 'practice',
				duration_s: 0
			},
			questions: selectedQids.map((qid) => ({
				qid,
				duration_s: 0,
			})),
			check_answer_immediate: true // Default behavior for now
		};

		sessionState.current = newSession;
		goto('/quiz');
	}
</script>

<div class="overlay" onclick={onClose} role="presentation">
	<div
		class="menu"
		onclick={(e) => e.stopPropagation()}
		role="dialog"
		aria-modal="true"
		aria-label="Configuration du quiz">
		<div class="header">
			<h2>{title}</h2>
			<button class="close-btn" onclick={onClose} aria-label="Fermer">✕</button>
		</div>

		<div class="content">
			<div class="section">
				<div class="section-header">
					<h3>Options</h3>
				</div>

				<div class="chapters-grid">
					<label class="chapter-item">
						<span class="label-text">Uniquement les questions à revoir</span>
						<Toggle bind:checked={chaptersState.onlyNew} />
					</label>
				</div>
			</div>

			<!-- if no chapters, everything is in rest, so no need to show it -->
			{#if subjectChapters.length > 0}
				<div class="section">
					<div class="section-header">
						<h3>Chapitres</h3>
						<button class="text-btn" onclick={selectAllChapters}>
							{allChaptersSelected && ((hasRest && chaptersState.includeRest) || !hasRest)
								? 'Tout désélectionner'
								: 'Tout sélectionner'}
						</button>
					</div>
					<div class="chapters-grid">
						{#each subjectChapters as chapter}
							<label class="chapter-item">
								<span class="label-text"
									>{chapter.name} ({questionsCountByChapter.chapters[chapter.id]?.length || 0})</span>
								<Toggle
									checked={chaptersState.selected.includes(chapter.id)}
									onchange={() => toggleChapter(chapter.id)} />
							</label>
						{/each}
						{#if hasRest}
							<label class="chapter-item">
								<span class="label-text">Divers ({questionsCountByChapter.rest.length})</span>
								<Toggle bind:checked={chaptersState.includeRest} />
							</label>
						{/if}
					</div>
				</div>
			{/if}

			<div class="section">
				<div class="section-header">
					<h3>Nombre de questions</h3>
					<span class="count-value">{sliderValue} / {totalAvailable}</span>
				</div>

				<div class="questions-control">
					<div class="slider-container">
						<input type="range" min="1" max={totalAvailable} bind:value={sliderValue} class="range-slider" />
						<div class="range-labels">
							<span>1</span>
							<span>{totalAvailable}</span>
						</div>
					</div>
				</div>
			</div>
		</div>

		<div class="footer">
			<button class="cancel-btn" onclick={onClose}>Annuler</button>
			<button class="start-btn" onclick={startQuiz} disabled={totalAvailable === 0}> Commencer le Quiz </button>
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
		background: var(--accent-color);
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

	/* Toggle styles moved to Toggle.svelte */

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
		color: var(--accent-color);
	}

	.questions-control {
		display: flex;
		flex-direction: column;
		gap: 16px;
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
		border: 2px solid var(--accent-color);
		color: var(--accent-color);
		padding: 12px 32px;
		font-weight: 700;
		cursor: pointer;
		border-radius: 50px;
		transition:
			all 0.2s,
			transform 0.2s;
	}

	.start-btn:hover:not(:disabled) {
		background: var(--accent-color);
		color: white;
		transform: translateY(-2px);
		box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
	}

	.start-btn:disabled {
		opacity: 0.5;
		cursor: not-allowed;
		transform: none;
	}
</style>
