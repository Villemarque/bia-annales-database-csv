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

<div class="basecard subject-card" title={desc} onclick={handleClick} role="button" tabindex="0">
	<div class="card-top">
		<img src={icon} alt="" class="icon-svg" />
		<h3>{title}</h3>
	</div>
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
		padding: 16px;
	}

	/* ---- Top row: icon + title side by side ---- */
	.card-top {
		display: flex;
		align-items: center;
		gap: 14px;
		flex: 1;
	}

	.icon-svg {
		width: 100px;
		height: 100px;
		border-radius: 18px;
		flex-shrink: 0;
		display: block;
	}

	.card-top h3 {
		margin: 0;
		font-size: 16px;
		font-weight: 600;
		line-height: 1.3;
	}

	/* ---- Stats bar ---- */
	.stats {
		margin-top: auto;
		padding-top: 14px;
		display: flex;
		align-items: center;
		gap: 10px;
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
</style>
