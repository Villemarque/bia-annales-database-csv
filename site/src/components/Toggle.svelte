<script lang="ts">
	let {
		checked = $bindable(false),
		onchange
	}: {
		checked?: boolean;
		onchange?: () => void;
	} = $props();
</script>

<div class="toggle-wrapper">
	<input type="checkbox" bind:checked {onchange} />
	<span class="toggle-switch"></span>
</div>

<style>
	.toggle-wrapper {
		position: relative;
		width: 50px;
		height: 30px;
		display: inline-block;
		flex-shrink: 0;
	}

	.toggle-wrapper input {
		position: absolute;
		opacity: 0;
		cursor: pointer;
		height: 0;
		width: 0;
	}

	.toggle-switch {
		position: absolute;
		top: 0;
		left: 0;
		right: 0;
		bottom: 0;
		background-color: #ccc;
		transition: 0.4s;
		border-radius: 34px;
		pointer-events: none; /* Allow click to pass through to input */
	}

	.toggle-switch:before {
		position: absolute;
		content: '';
		height: 22px;
		width: 22px;
		left: 4px;
		bottom: 4px;
		background-color: white;
		transition: 0.4s;
		border-radius: 50%;
		box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
	}

	.toggle-wrapper input:checked + .toggle-switch {
		background-color: #4cd964;
	}

	.toggle-wrapper input:checked + .toggle-switch:before {
		transform: translateX(20px);
	}
</style>
