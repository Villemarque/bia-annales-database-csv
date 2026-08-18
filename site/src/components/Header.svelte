<script lang="ts">
	import biaLogo from '$lib/icons/bia-logo.svg';
</script>

<div class="header-card">
	<div class="header-content">
		<div class="title">
			<img src={biaLogo} alt="BIA" class="bia-logo" />
			Aérien Ambassadeurs Avenir
			<span class="beta-tag">BETA</span>
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
		height: 32px;
		width: auto;
		margin-bottom: 4px;
	}

	.beta-tag {
		font-size: 11px;
		font-weight: 700;
		letter-spacing: 0.08em;
		padding: 2px 8px;
		border-radius: 999px;
		background: var(--card-blue);
		color: white;
		text-transform: uppercase;
		align-self: flex-start;
		margin-top: 4px;
	}

	@media (max-width: 620px) {
		.header-card {
			padding: 18px;
		}

		.title {
			font-size: 18px;
			gap: 6px;
		}

		.bia-logo {
			height: 28px;
			margin-bottom: 2px;
		}
	}

	@media (max-width: 480px) {
		.header-card {
			padding: 14px;
		}

		.title {
			font-size: 15px;
			gap: 5px;
		}

		.bia-logo {
			height: 22px;
		}
	}
</style>
