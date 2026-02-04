<script lang="ts">
	import Card from '../components/Card.svelte';
	import SubjectConfigMenu from '../components/SubjectConfigMenu.svelte';
	import { questionsBySubject } from '$lib/stores/questions';
	import { type Subject, Subjects, QBCtoList } from '$lib/types';

	// for SEO, and faster initial load
	// only prerendered at build time
	// export const prerender = true;
	// export const ssr = true;

	const cards = [
		{
			subjectId: Subjects.AERONEF,
			icon: '✈︎',
			color: 'var(--card-indigo)',
			title: 'Connaissance des Aéronefs',
			desc: 'Structure et systèmes avion.',
			href: '/quiz'
		},
		{
			subjectId: Subjects.AERODYNAMIQUE,
			icon: '〰︎',
			color: 'var(--card-blue)',
			title: 'Aérodynamique',
			desc: 'Forces et équilibres en vol.',
			href: '/quiz'
		},
		{
			subjectId: Subjects.METEO,
			icon: '☁︎',
			color: 'var(--card-green)',
			title: 'Météorologie',
			desc: 'Phénomènes atmosphériques.',
			href: '/quiz'
		},
		{
			subjectId: Subjects.NAVIGATION,
			icon: '🧭',
			color: 'var(--card-orange)',
			title: 'Navigation / Réglementation',
			desc: 'Orientation et règles de l’air.',
			href: '/quiz'
		},
		{
			subjectId: Subjects.HISTOIRE,
			icon: '⏳',
			color: 'var(--card-red)',
			title: 'Histoire',
			desc: 'Évolution de l’aviation.',
			href: '/quiz'
		},
		{
			subjectId: Subjects.ANGLAIS,
			icon: 'EN',
			color: 'var(--card-pink)',
			title: 'Anglais',
			desc: 'Communication aéronautique.',
			href: '/quiz'
		}
	];

	let activeSubject = $state<
		| {
				id: Subject;
				title: string;
				color: string;
				totalQuestions: number;
		  }
		| undefined
	>(undefined);

	function openMenu(card: { subjectId: Subject; title: string; color: string }, totalQuestions: number) {
		activeSubject = {
			id: card.subjectId,
			title: card.title,
			color: card.color,
			totalQuestions
		};
	}
	function noQuestionsBySubject(s: Subject): number {
		const byChapters = $questionsBySubject[s];
		const total = QBCtoList(byChapters).length;
		// DEBUG
		console.log('total of', s, byChapters, total);
		return total;
	}
</script>

<section class="grid">
	{#each cards as c}
		{@const total = noQuestionsBySubject(c.subjectId)}
		<Card {...c} totalQuestions={total} answeredQuestions={0} seenQuestions={0} onclick={() => openMenu(c, total)} />
	{/each}
</section>

{#if activeSubject}
	<SubjectConfigMenu
		subjectId={activeSubject.id}
		title={activeSubject.title}
		totalQuestions={activeSubject.totalQuestions}
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
