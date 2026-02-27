<script lang="ts">
	let {
		icon,
		title,
		desc,
		totalQuestions,
		correctAnswers,
		seenQuestions,
		onclick
	}: {
		icon: string;
		title: string;
		desc: string;
		totalQuestions: number;
		correctAnswers: number;
		seenQuestions: number;
		onclick: () => void;
	} = $props();

	let seenPercent = $derived(totalQuestions > 0 ? (seenQuestions / totalQuestions) * 100 : 0);
	let answeredPercent = $derived(totalQuestions > 0 ? (correctAnswers / totalQuestions) * 100 : 0);

	function handleClick(e: MouseEvent) {
		if (onclick) {
			e.preventDefault();
			onclick();
		}
	}
</script>

<div class="basecard subject-card" onclick={handleClick} role="button" tabindex="0">
	<div class="icon">{icon}</div>
	<h3>{title}</h3>
	<p>{desc}</p>
	{#if totalQuestions > 0}
		<div class="stats" title="Réponses correctes · Questions vues · Total">
			<div class="progress">
				<div class="bar seen" style="width: {seenPercent}%"></div>
				<div class="bar answered" style="width: {answeredPercent}%"></div>
			</div>
			<div class="count">
				<span class="val answered">{correctAnswers}</span>
				<span class="sep">·</span>
				<span class="val seen">{seenQuestions}</span>
				<span class="sep">·</span>
				<span class="val total">{totalQuestions}</span>
			</div>
		</div>
	{/if}
</div>

<style>
	.subject-card {
		color: white;
		background: var(--card-bg-color);
	}
	.card:hover {
		transform: translateY(-8px) scale(1.02);
	}
	.card:focus-visible {
		outline: 3px solid rgba(255, 255, 255, 0.5);
		outline-offset: 2px;
	}
	.subject-card h3 {
		margin: 16px 0 8px;
		font-size: 18px;
	}
	.subject-card p {
		margin: 0;
		font-size: 14px;
		opacity: 0.9;
		flex-grow: 1;
	}
	.stats {
		margin-top: 20px;
		display: flex;
		align-items: center;
		gap: 12px;
	}
	.count {
		font-size: 11px;
		font-weight: 500;
		white-space: nowrap;
		display: flex;
		align-items: center;
		gap: 3px;
	}
	.val.answered {
		color: rgba(255, 255, 255, 1);
		font-weight: 700;
	}
	.val.seen,
	.val.total {
		color: rgba(255, 255, 255, 0.7);
	}
	.sep {
		color: rgba(255, 255, 255, 0.3);
		font-weight: 400;
	}
	.progress {
		height: 4px;
		background: rgba(0, 0, 0, 0.15);
		border-radius: 4px;
		flex: 1;
		position: relative;
		overflow: hidden;
	}
	.bar {
		position: absolute;
		top: 0;
		bottom: 0;
		left: 0;
		transition: width 0.3s ease;
	}
	.bar.seen {
		background: rgba(255, 255, 255, 0.3);
		z-index: 1;
	}
	.bar.answered {
		background: rgba(255, 255, 255, 0.9);
		z-index: 2;
	}
	.icon {
		width: 46px;
		height: 46px;
		border-radius: 14px;
		background: rgba(255, 255, 255, 0.25);
		display: flex;
		align-items: center;
		justify-content: center;
		font-weight: 700;
	}
</style>
