<script lang="ts">
	import Card from '../components/Card.svelte';
	import { questionsBySubject } from '$lib/stores/questions';

	const subjs = questionsBySubject;
	const unsub = subjs.subscribe((value) => {
		console.log('questionsBySubject', value);
	});

	// for SEO, and faster initial load
	// only prerendered at build time
	// export const prerender = true;
	// export const ssr = true;

	const cards = [
		{
			icon: '✈︎',
			color: 'var(--card-indigo)',
			title: 'Connaissance des Aéronefs',
			desc: 'Structure et systèmes avion.',
			href: '/quiz'
		},
		{
			icon: '〰︎',
			color: 'var(--card-blue)',
			title: 'Aérodynamique',
			desc: 'Forces et équilibres en vol.'
		},
		{
			icon: '☁︎',
			color: 'var(--card-green)',
			title: 'Météorologie',
			desc: 'Phénomènes atmosphériques.'
		},
		{
			icon: '🧭',
			color: 'var(--card-orange)',
			title: 'Navigation / Réglementation',
			desc: 'Orientation et règles de l’air.'
		},
		{ icon: '⏳', color: 'var(--card-red)', title: 'Histoire', desc: 'Évolution de l’aviation.' },
		{
			icon: 'EN',
			color: 'var(--card-pink)',
			title: 'Anglais',
			desc: 'Communication aéronautique.'
		}
	];
</script>

<section class="grid">
	{#each cards as c}
		<Card {...c} />
	{/each}
</section>

<style>
	.grid {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(min(260px, 100%), 1fr));
		gap: 28px;
	}
</style>
