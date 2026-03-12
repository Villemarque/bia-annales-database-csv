<script lang="ts">
	import Card from '../components/Card.svelte';
	import SubjectConfigMenu from '../components/SubjectConfigMenu.svelte';
	import { questionsBySubject } from '$lib/stores/questions';
	import { log } from '$lib/log';
	import { attempts } from '$lib/stores/attempt';
	import { type Subject, Subjects, QBCtoList, type Attempt } from '$lib/types';
	import aer1 from '$lib/icons/aer1.svg';
	import aero1 from '$lib/icons/aero1.svg';
	import cb1 from '$lib/icons/cb1.svg';
	import nav1 from '$lib/icons/nav1.svg';
	import hst1 from '$lib/icons/hst1.svg';
	import eng1 from '$lib/icons/eng1.svg';

	// for SEO, and faster initial load
	// only prerendered at build time
	// export const prerender = true;
	// export const ssr = true;

	const cards = [
		{
			subjectId: Subjects.AERONEF,
			icon: aer1,
			color: 'var(--card-indigo)',
			title: 'Connaissance des Aéronefs',
			desc: 'Structure et systèmes avion.'
		},
		{
			subjectId: Subjects.AERODYNAMIQUE,
			icon: aero1,
			color: 'var(--card-blue)',
			title: 'Aérodynamique',
			desc: 'Forces et équilibres en vol.'
		},
		{
			subjectId: Subjects.METEO,
			icon: cb1,
			color: 'var(--card-green)',
			title: 'Météorologie',
			desc: 'Phénomènes atmosphériques.'
		},
		{
			subjectId: Subjects.NAVIGATION,
			icon: nav1,
			color: 'var(--card-orange)',
			title: 'Navigation / Réglementation',
			desc: "Orientation et règles de l'air."
		},
		{
			subjectId: Subjects.HISTOIRE,
			icon: hst1,
			color: 'var(--card-red)',
			title: 'Histoire',
			desc: "Évolution de l'aviation."
		},
		{
			subjectId: Subjects.ANGLAIS,
			icon: eng1,
			color: 'var(--card-pink)',
			title: 'Anglais',
			desc: 'Communication aéronautique.'
		}
	];

	let activeSubject = $state<
		| {
				id: Subject;
				title: string;
				color: string;
		  }
		| undefined
	>(undefined);

	function openMenu(card: { subjectId: Subject; title: string; color: string }) {
		activeSubject = {
			id: card.subjectId,
			title: card.title,
			color: card.color
		};
	}

	const getStats = (s: Subject): { total: number; seen: number; correct: number } => {
		const byChapters = $questionsBySubject[s];
		const all = QBCtoList(byChapters);
		const attempted: Attempt[][] = all.map((q) => $attempts[q] || []);
		const seen = attempted.filter((atts) => atts.length > 0).length;
		const correct = attempted.filter((atts) => atts.some((a) => a.correct)).length;

		return {
			total: all.length,
			seen,
			correct
		};
	};
</script>

<section class="grid">
	{#each cards as c}
		{@const stats = getStats(c.subjectId)}
		<Card
			{...c}
			totalQuestions={stats.total}
			correctAnswers={stats.correct}
			seenQuestions={stats.seen}
			onclick={() => openMenu(c)}
			--card-bg-color={c.color} />
	{/each}
</section>

{#if activeSubject}
	<SubjectConfigMenu
		subjectId={activeSubject.id}
		title={activeSubject.title}
		onClose={() => (activeSubject = undefined)}
		--accent-color={activeSubject.color} />
{/if}

<style>
	.grid {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(min(260px, 100%), 1fr));
		gap: 28px;
	}
</style>
