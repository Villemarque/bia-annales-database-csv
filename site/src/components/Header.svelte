<div class="header-card">
	<div class="header-content">
		<div class="title">BIA Aérien Ambassadeurs Avenir</div>
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
	}

	@media (max-width: 600px) {
		.title {
			font-size: 22px;
		}
	}
</style>
