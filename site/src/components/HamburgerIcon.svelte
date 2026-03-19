<script lang="ts">
	let { expanded = false }: { expanded?: boolean } = $props();

	// Hamburger paths (3 horizontal lines) — menu closed
	const hamburgerPaths = ['M 20 25 L 80 25', 'M 20 50 L 80 50', 'M 20 75 L 80 75'];

	// Logo paths (M-shape strokes) — menu open
	const logoPaths = ['M 18 85 L 35 25', 'M 12 65 L 53 54', 'M 35 20 L 60 95'];

	let d1 = $derived(expanded ? logoPaths[0] : hamburgerPaths[0]);
	let d2 = $derived(expanded ? logoPaths[1] : hamburgerPaths[1]);
	let d3 = $derived(expanded ? logoPaths[2] : hamburgerPaths[2]);
</script>

<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100" class="logo-svg">
	<defs>
		<path id="lh-tpath" d="M 5 65 C 0 25 35 2 60 8 C 85 12 95 30 95 55" />
	</defs>

	<g class="decoration" class:visible={expanded}>
		<text class="m-text">
			<textPath href="#lh-tpath" startOffset="3%"
				>AÉRIEN&#160;&#160;&#160;AMBASSADEURS&#160;&#160;&#160;AVENIR</textPath>
		</text>

		<path
			d="M 58 52.5 L 66 50.5 M 71 49 L 79 47 M 84 45.5 L 87 44.5"
			stroke="currentColor"
			stroke-width="2"
			stroke-linecap="round"
			fill="none" />

		<path
			d="M 85 45.5 L 89 44 L 88 40 L 90 39.5 L 92 43 L 96 41.5 C 97 41 98 41.5 98 42.5 C 98 43 97 43.5 96 44 L 92 45.5 L 93 49 L 91 49 L 89 46 L 85 47 Z"
			fill="currentColor" />
	</g>

	<path class="m-stroke" d={d1} />
	<path class="m-stroke" d={d2} />
	<path class="m-stroke" d={d3} />
</svg>

<style>
	.logo-svg {
		width: 36px;
		height: 36px;
	}

	.m-stroke {
		fill: none;
		stroke: currentColor;
		stroke-width: 6.5;
		stroke-linecap: round;
		stroke-linejoin: round;
		transition: d 0.4s cubic-bezier(0.4, 0, 0.2, 1);
	}

	.m-text {
		font-family: Arial, sans-serif;
		font-size: 6px;
		font-weight: 800;
		letter-spacing: 0.5px;
		fill: currentColor;
	}

	.decoration {
		opacity: 0;
		transition: opacity 0.4s cubic-bezier(0.4, 0, 0.2, 1);
	}

	.decoration.visible {
		opacity: 1;
	}
</style>
