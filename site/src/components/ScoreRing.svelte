<script lang="ts">
	let {
		percent = 0,
		size = 120,
		strokeWidth = 8,
		showValue = true
	}: {
		percent?: number;
		size?: number;
		strokeWidth?: number;
		showValue?: boolean;
	} = $props();

	// Calculate dimensions
	let radius = $derived((size - strokeWidth) / 2);
	let circumference = $derived(2 * Math.PI * radius);
	let offset = $derived(circumference - (percent / 100) * circumference);
</script>

<div class="score-ring-container" style="width: {size}px; height: {size}px;">
	<svg width={size} height={size} viewBox="0 0 {size} {size}" class="ring-svg">
		<!-- Background track -->
		<circle class="ring-track" cx={size / 2} cy={size / 2} r={radius} stroke-width={strokeWidth} />
		<!-- Progress ring -->
		<circle
			class="ring-progress"
			cx={size / 2}
			cy={size / 2}
			r={radius}
			stroke-width={strokeWidth}
			style="stroke-dasharray: {circumference}; stroke-dashoffset: {offset};" />
	</svg>
	{#if showValue}
		<div class="ring-content">
			<span class="ring-value" style="font-size: {size * 0.22}px;">
				{Math.round(percent)} %
			</span>
		</div>
	{/if}
</div>

<style>
	.score-ring-container {
		position: relative;
		display: flex;
		align-items: center;
		justify-content: center;
	}

	.ring-svg {
		transform: rotate(-90deg);
	}

	.ring-track {
		fill: none;
		stroke: #f1f3f5;
	}

	.ring-progress {
		fill: none;
		stroke: #58a68d; /* Teal green */
		stroke-linecap: round;
		transition: stroke-dashoffset 0.6s ease-out;
	}

	.ring-content {
		position: absolute;
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		pointer-events: none;
	}

	.ring-value {
		font-weight: 500;
		color: #343a40;
		line-height: 1;
	}
</style>
