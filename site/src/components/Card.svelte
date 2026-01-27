<script lang="ts">
	let {
		icon = '',
		color = '',
		title = '',
		desc = '',
		href = '',
		totalQuestions = 0,
		answeredQuestions = 0,
		seenQuestions = 0
	}: {
		icon?: string;
		color?: string;
		title?: string;
		desc?: string;
		href?: string;
		totalQuestions?: number;
		answeredQuestions?: number;
		seenQuestions?: number;
	} = $props();

	let seenPercent = $derived(totalQuestions > 0 ? (seenQuestions / totalQuestions) * 100 : 0);
	let answeredPercent = $derived(totalQuestions > 0 ? (answeredQuestions / totalQuestions) * 100 : 0);
</script>

{#if href}
	<a {href} class="card" style="background: {color}; text-decoration: none;">
		<div class="icon">{icon}</div>
		<h3>{title}</h3>
		<p>{desc}</p>
		{#if totalQuestions > 0}
			<div class="stats">
				<div class="progress">
					<div class="bar seen" style="width: {seenPercent}%"></div>
					<div class="bar answered" style="width: {answeredPercent}%"></div>
				</div>
				<span class="count">{answeredQuestions}/{seenQuestions}/{totalQuestions}</span>
			</div>
		{/if}
	</a>
{:else}
	<div class="card" style="background: {color}">
		<div class="icon">{icon}</div>
		<h3>{title}</h3>
		<p>{desc}</p>
		{#if totalQuestions > 0}
			<div class="stats">
				<div class="progress">
					<div class="bar seen" style="width: {seenPercent}%"></div>
					<div class="bar answered" style="width: {answeredPercent}%"></div>
				</div>
				<span class="count">{answeredQuestions}/{seenQuestions}/{totalQuestions}</span>
			</div>
		{/if}
	</div>
{/if}

<style>
	.card {
		padding: 26px;
		border-radius: var(--radius-xl);
		color: white;
		box-shadow: var(--glass-shadow);
		transition: transform 0.35s ease;
		display: flex;
		flex-direction: column;
	}
	.card:hover {
		transform: translateY(-8px) scale(1.02);
	}
	.card h3 {
		margin: 16px 0 8px;
		font-size: 18px;
	}
	.card p {
		margin: 0;
		font-size: 14px;
		opacity: 0.9;
		flex-grow: 1;
	}
	.stats {
		margin-top: 20px;
		font-family: Andale Mono;
		display: flex;
		align-items: center;
		gap: 12px;
	}
	.count {
		font-size: 13px;
		font-weight: 500;
		opacity: 0.9;
		white-space: nowrap;
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
