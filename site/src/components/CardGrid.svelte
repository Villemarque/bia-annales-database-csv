<script lang="ts">
	import Card from './Card.svelte';
	const cards = [
		{
			icon: '✈︎',
			color: 'var(--card-blue)',
			title: 'Connaissance des Aéronefs',
			desc: 'Structure et systèmes avion.'
		},
		{
			icon: '〰︎',
			color: 'var(--card-indigo)',
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
		{ icon: 'EN', color: 'var(--card-blue)', title: 'Anglais', desc: 'Communication aéronautique.' }
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
		grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
		gap: 28px;
	}
</style>
