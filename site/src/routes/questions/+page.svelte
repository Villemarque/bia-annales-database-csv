<script lang="ts">
	import { questions } from '$lib/stores/questions';
	import { Subjects, ChaptersById } from '$lib/types';
	import type { Question, Subject, ChapterId, Qid } from '$lib/types';
	import { onMount } from 'svelte';
	import { slide } from 'svelte/transition';
	import { SvelteSet } from 'svelte/reactivity';

	let subjectFilter = $state<string>('');
	let searchQuery = $state<string>('');
	let visibleCount = $state<number>(50);

	let expandedQids: SvelteSet<Qid> = new SvelteSet();
	let sortColumn = $state<'id' | 'subject' | 'chapter'>('id');
	let sortDirection = $state<'asc' | 'desc'>('asc');

	function toggleExpand(qid: Qid) {
		console.log('Toggling expand for', qid);

		if (expandedQids.has(qid)) {
			expandedQids.delete(qid);
		} else {
			expandedQids.add(qid);
		}
	}

	function toggleSort(col: 'id' | 'subject' | 'chapter') {
		if (sortColumn === col) {
			sortDirection = sortDirection === 'asc' ? 'desc' : 'asc';
		} else {
			sortColumn = col;
			sortDirection = 'asc';
		}
	}

	const allQuestions = $derived(Object.values($questions) as Question[]);

	const filteredQuestions = $derived(
		allQuestions.filter((q) => {
			if (subjectFilter !== '' && q.subject !== parseInt(subjectFilter)) return false;

			if (searchQuery.trim() !== '') {
				const query = searchQuery.toLowerCase();
				const inContent = q.content.toLowerCase().includes(query);
				const inQid = q.qid.toLowerCase().includes(query);
				const inChoices = q.choices.some((choice) => choice.toLowerCase().includes(query));
				if (!inContent && !inQid && !inChoices) return false;
			}
			return true;
		})
	);

	const sortedQuestions = $derived(
		[...filteredQuestions].sort((a, b) => {
			let valA: any;
			let valB: any;

			if (sortColumn === 'id') {
				valA = a.qid;
				valB = b.qid;
			} else if (sortColumn === 'subject') {
				valA = a.no_subject || a.subject;
				valB = b.no_subject || b.subject;
			} else if (sortColumn === 'chapter') {
				valA = ChaptersById[a.chapters[0]]?.name || '';
				valB = ChaptersById[b.chapters[0]]?.name || '';
			}

			if (valA < valB) return sortDirection === 'asc' ? -1 : 1;
			if (valA > valB) return sortDirection === 'asc' ? 1 : -1;
			return 0;
		})
	);

	const visibleQuestions = $derived(sortedQuestions.slice(0, visibleCount));

	function handleScroll() {
		const bottom = Math.ceil(window.innerHeight + window.scrollY) >= document.documentElement.scrollHeight;
		if (bottom && visibleCount < sortedQuestions.length) {
			visibleCount += 50;
		}
	}

	onMount(() => {
		window.addEventListener('scroll', handleScroll);
		return () => {
			window.removeEventListener('scroll', handleScroll);
		};
	});

	// Helper mapped from QuizSession
	const subjectMap: Record<number, string> = {
		[Subjects.METEO]: 'Météo',
		[Subjects.AERODYNAMIQUE]: 'Aérodynamique',
		[Subjects.AERONEF]: 'Aéronef',
		[Subjects.NAVIGATION]: 'Navigation',
		[Subjects.HISTOIRE]: 'Histoire',
		[Subjects.ANGLAIS]: 'Anglais'
	};

	function getSubjectColor(id: number) {
		const colors = [
			'var(--card-blue)',
			'var(--card-indigo)',
			'var(--card-green)',
			'var(--card-orange)',
			'var(--card-red)',
			'var(--card-pink)'
		];
		if (isNaN(id)) return colors[0];
		return colors[id % colors.length];
	}

	const letters = ['A', 'B', 'C', 'D'];
</script>

<div class="questions-page">
	<div class="header-card glass-panel">
		<h1>Browse Questions</h1>
		<div class="filters">
			<select bind:value={subjectFilter} class="filter-select">
				<option value="">All Subjects</option>
				{#each Object.values(Subjects) as subject}
					<option value={subject}>{subjectMap[subject] || subject}</option>
				{/each}
			</select>

			<input
				type="text"
				bind:value={searchQuery}
				placeholder="Rechercher (question, réponse, ID)..."
				class="filter-input" />
		</div>
		<p class="count">Showing {visibleQuestions.length} of {filteredQuestions.length} questions</p>
	</div>

	<div class="questions-table-container glass-panel">
		<table class="questions-table">
			<thead>
				<tr>
					<!-- svelte-ignore a11y_click_events_have_key_events -->
					<!-- svelte-ignore a11y_no_noninteractive_element_interactions -->
					<th onclick={() => toggleSort('id')} class="sortable">
						ID {sortColumn === 'id' ? (sortDirection === 'asc' ? '▲' : '▼') : ''}
					</th>
					<!-- svelte-ignore a11y_click_events_have_key_events -->
					<!-- svelte-ignore a11y_no_noninteractive_element_interactions -->
					<th onclick={() => toggleSort('subject')} class="sortable">
						Partie {sortColumn === 'subject' ? (sortDirection === 'asc' ? '▲' : '▼') : ''}
					</th>
					<!-- svelte-ignore a11y_click_events_have_key_events -->
					<!-- svelte-ignore a11y_no_noninteractive_element_interactions -->
					<th onclick={() => toggleSort('chapter')} class="sortable">
						Section {sortColumn === 'chapter' ? (sortDirection === 'asc' ? '▲' : '▼') : ''}
					</th>
					<th>Question</th>
				</tr>
			</thead>
			<tbody>
				{#each visibleQuestions as q (q.qid)}
					<!-- svelte-ignore a11y_click_events_have_key_events -->
					<!-- svelte-ignore a11y_no_static_element_interactions -->
					<tr class="compact-row" onclick={() => toggleExpand(q.qid)}>
						<td class="col-id">{q.qid}</td>
						<td class="col-partie">{subjectMap[q.subject] || q.subject}</td>
						<td class="col-section">
							{#if q.chapters && q.chapters.length > 0}
								{ChaptersById[q.chapters[0]]?.name || ''}
							{/if}
						</td>
						<td class="col-question">
							{q.content}
						</td>
					</tr>

					{#if expandedQids.has(q.qid)}
						<tr class="details-row" style="--row-color: {getSubjectColor(q.subject)}">
							<td colspan="4" class="details-cell">
								<div class="details-content" transition:slide={{ duration: 300, axis: 'y' }}>
									<div class="question-body">
										{#if q.attachment_link}
											<div class="annexes">
												<img
													src="/figures/{q.attachment_link}.png"
													alt="Annexe {q.attachment_link}"
													class="annexe-img"
													loading="lazy" />
											</div>
										{/if}

										<div class="options-grid">
											{#each q.choices as opt, idx}
												<div class="option" class:correct={idx === q.answer} class:incorrect={idx !== q.answer}>
													<span class="option-letter">{letters[idx]}</span>
													<span class="opt-text">{opt}</span>
													{#if idx === q.answer}
														<span class="correct-icon">✓</span>
													{/if}
												</div>
											{/each}
										</div>
									</div>
								</div>
							</td>
						</tr>
					{/if}
				{/each}

				{#if visibleQuestions.length === 0}
					<tr>
						<td colspan="4" class="empty-state">No questions match the current filters.</td>
					</tr>
				{/if}
			</tbody>
		</table>
	</div>
</div>

<style>
	.questions-page {
		max-width: 1000px;
		margin: 0 auto;
		display: flex;
		flex-direction: column;
		gap: 20px;
		padding: 20px;
	}

	.glass-panel {
		background: var(--glass-bg);
		border: 1px solid var(--glass-border);
		border-radius: var(--radius-xl);
		box-shadow: var(--glass-shadow);
		backdrop-filter: blur(12px);
		-webkit-backdrop-filter: blur(12px);
	}

	.header-card {
		padding: 24px;
		text-align: center;
	}

	h1 {
		margin: 0 0 16px 0;
		font-size: 1.8rem;
		color: var(--text-dark);
	}

	.filters {
		display: flex;
		gap: 12px;
		justify-content: center;
		flex-wrap: wrap;
		margin-bottom: 12px;
	}

	.filter-select,
	.filter-input {
		padding: 10px 16px;
		border-radius: 12px;
		border: 1px solid rgba(0, 0, 0, 0.1);
		background: white;
		font-size: 1rem;
		min-width: 200px;
		outline: none;
	}

	.filter-input {
		flex: 1;
		max-width: 400px;
	}

	.count {
		margin: 0;
		color: var(--text-muted);
		font-size: 0.9rem;
	}

	.questions-table-container {
		overflow-x: auto;
		background: white; /* More opaque background for the table area */
	}

	.questions-table {
		width: 100%;
		border-collapse: collapse;
		text-align: left;
	}

	.questions-table th {
		padding: 16px 20px;
		font-weight: 600;
		color: var(--text-muted);
		border-bottom: 2px solid var(--bg-grey);
		white-space: nowrap;
	}

	.sortable {
		cursor: pointer;
		user-select: none;
	}

	.sortable:hover {
		color: var(--text-dark);
	}

	.questions-table td {
		padding: 16px 20px;
		border-bottom: 1px solid var(--bg-grey);
		vertical-align: middle;
	}

	.compact-row {
		cursor: pointer;
		transition: background-color 0.2s;
	}

	.compact-row:nth-child(4n-3) {
		/* Adjusted for the alternating details rows */
		background-color: rgba(0, 0, 0, 0.02);
	}

	.compact-row:hover {
		background-color: rgba(0, 0, 0, 0.05);
	}

	.col-id {
		font-family: monospace;
		font-size: 0.9em;
		color: var(--text-muted);
	}

	.col-partie {
		white-space: nowrap;
	}

	.col-section {
		white-space: nowrap;
		max-width: 200px;
		overflow: hidden;
		text-overflow: ellipsis;
	}

	.col-question {
		width: 100%;
	}

	/* Details Card */
	.details-row {
		background-color: rgba(0, 0, 0, 0.015);
	}

	.details-cell {
		padding: 0 !important;
		border-bottom: 1px solid var(--bg-grey) !important;
	}

	.details-content {
		border-left: 6px solid var(--row-color, var(--card-blue));
		padding: 10px 20px 30px 20px;
	}

	.question-body {
		padding: 0;
	}

	.annexes {
		display: flex;
		flex-wrap: wrap;
		gap: 12px;
		margin-bottom: 20px;
	}

	.annexe-img {
		max-width: 100%;
		max-height: 300px;
		border-radius: 8px;
		border: 1px solid rgba(0, 0, 0, 0.1);
	}

	.options-grid {
		display: grid;
		gap: 14px;
	}

	.option {
		padding: 16px 20px;
		border-radius: 12px;
		background: white;
		border: 1px solid var(--glass-border);
		cursor: default;
		display: flex;
		align-items: center;
		gap: 16px;
	}

	.option.incorrect {
		opacity: 0.6;
		background: transparent;
	}

	.option.correct {
		background: #f0fdf4;
		border-color: #bbf7d0;
		color: #166534;
		box-shadow: 0 2px 8px rgba(22, 101, 52, 0.05);
		opacity: 1;
		font-weight: 500;
	}

	.option.correct .option-letter {
		color: #166534;
	}

	.option-letter {
		font-weight: 700;
		font-size: 18px;
		color: var(--text-muted);
		min-width: 24px;
	}

	.opt-text {
		flex: 1;
		line-height: 1.4;
	}

	.correct-icon {
		font-size: 20px;
		font-weight: bold;
		color: #166534;
	}

	.empty-state {
		padding: 40px;
		text-align: center;
		color: var(--text-muted);
		font-size: 1.1rem;
	}
</style>
