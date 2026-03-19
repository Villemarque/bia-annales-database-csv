<script lang="ts">
	import biaLogo from '$lib/icons/bia-logo.svg';
</script>

<div class="header-card">
	<div class="header-content">
		<div class="title">
			<img src={biaLogo} alt="BIA" class="bia-logo" />
			Aérien Ambassadeurs Avenir
		</div>
	</div>
</div>

<style>
	.header-card {
		background: var(--glass-bg-strong);
		backdrop-filter: blur(20px) saturate(160%);
		border: 1px solid var(--glass-border);
		border-top: none;
		border-radius: 0 0 var(--radius-xl) var(--radius-xl);
		box-shadow: var(--glass-shadow);
		padding: 32px;
	}

	.header-content {
		display: flex;
		flex-direction: column;
		gap: 8px;
	}

	.title {
		font-size: 28px;
		font-weight: 800;
		color: var(--text-dark);
		letter-spacing: -0.02em;
		line-height: 1.2;
		display: flex;
		align-items: center;
		gap: 12px;
	}

	.bia-logo {
		height: 48px;
		width: auto;
		margin-bottom: 4px;
	}

	@media (max-width: 600px) {
		.title {
			font-size: 22px;
			gap: 8px;
		}

		.bia-logo {
			height: 36px;
		}
	}
</style>
