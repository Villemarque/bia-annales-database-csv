<script lang="ts">
	import Card from '../components/Card.svelte';
	import { questionsBySubject } from '$lib/stores/questions';

	// Mapping based on annales-bia.csv analysis:
	// 0: Météorologie
	// 1: Aérodynamique
	// 2: Connaissance des Aéronefs
	// 3: Navigation / Réglementation
	// 4: Histoire
	// 5: Anglais

	// for SEO, and faster initial load
	// only prerendered at build time
	// export const prerender = true;
	// export const ssr = true;

	const cards = [
		{
			subjectId: 2,
			icon: '✈︎',
			color: 'var(--card-indigo)',
			title: 'Connaissance des Aéronefs',
			desc: 'Structure et systèmes avion.',
			href: '/quiz'
		},
		{
			subjectId: 1,
			icon: '〰︎',
			color: 'var(--card-blue)',
			title: 'Aérodynamique',
			desc: 'Forces et équilibres en vol.'
		},
		{
			subjectId: 0,
			icon: '☁︎',
			color: 'var(--card-green)',
			title: 'Météorologie',
			desc: 'Phénomènes atmosphériques.'
		},
		{
			subjectId: 3,
			icon: '🧭',
			color: 'var(--card-orange)',
			title: 'Navigation / Réglementation',
			desc: 'Orientation et règles de l’air.'
		},
		{
			subjectId: 4,
			icon: '⏳',
			color: 'var(--card-red)',
			title: 'Histoire',
			desc: 'Évolution de l’aviation.'
		},
		{
			subjectId: 5,
			icon: 'EN',
			color: 'var(--card-pink)',
			title: 'Anglais',
			desc: 'Communication aéronautique.'
		}
	];
</script>

<section class="grid">
	{#each cards as c}
		<Card {...c} totalQuestions={$questionsBySubject[c.subjectId] || 0} answeredQuestions={50} seenQuestions={100} />
	{/each}
</section>

<style>
	.grid {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(min(260px, 100%), 1fr));
		gap: 28px;
	}
</style>
