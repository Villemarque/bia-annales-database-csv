<div class="header-card">
	<div class="header-content">
		<div class="title">BIA Aérien Ambassadeurs Avenir</div>
		<div class="subtitle">Plateforme d'entraînement au Brevet d'Initiation Aéronautique</div>
	</div>
</div>

<style>
	.header-card {
		background: var(--glass-bg-strong);
		backdrop-filter: blur(20px) saturate(160%);
		border: 1px solid var(--glass-border);
		border-radius: var(--radius-xl);
		box-shadow: var(--glass-shadow);
		padding: 32px;
		margin-bottom: 40px;
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

	.subtitle {
		font-size: 16px;
		font-weight: 500;
		color: var(--text-muted);
	}

	@media (max-width: 600px) {
		.header-card {
			padding: 24px;
		}
		.title {
			font-size: 22px;
		}
		.subtitle {
			font-size: 14px;
		}
	}
</style>
