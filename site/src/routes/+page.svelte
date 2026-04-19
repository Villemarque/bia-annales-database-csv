<script lang="ts">
	import Card from '../components/Card.svelte';
	import { resolve } from '$lib/go';
	import { Subjects } from '$lib/types';
</script>

<div class="page-container">
	<section class="hero glass-panel">
		<h1>BIA par Aérien Ambassadeurs Avenir</h1>
		<p class="subtitle">Cours à distance par visioconférence, gratuit, pour tous !</p>
		<div class="actions">
			<a href={resolve('/subjects' as any)} class="btn primary">Accéder aux Matières</a>
			<a href="https://asso-triple-a.org/" target="_blank" rel="noopener noreferrer" class="btn secondary">
				Visiter le site officiel ↗
			</a>
		</div>
	</section>

	<div class="content-grid">
		<section class="content-section glass-panel" id="cours">
			<div class="section-header">
				<h2>Les Cours</h2>
			</div>
			<div class="section-body">
				<p>
					Les cours sont donnés en <strong>visioconférence</strong> à partir du mois
					<strong>d’octobre</strong> jusqu’à <strong>la date de l’examen</strong>, suivant les
					<strong>périodes scolaires</strong> de la <strong>zone C</strong> (Paris). Durant les vacances
					scolaires des cours de révisions peuvent être proposés.
				</p>
				
				<div class="highlight-box">
					<h3>Pourquoi nous rejoindre ?</h3>
					<ul class="benefits-list">
						<li>🌍 Le format en visioconférence permet de suivre les cours dans le monde entier</li>
						<li>✈️ Nos professeurs, directement issus du secteur aérien, peuvent aider pour l'orientation professionnelle</li>
						<li>📝 Notre site d'annales mis à disposition, pour bien se préparer à l'examen</li>
						<li>🤝 Partenariat avec la <a href="https://www.ffa-aero.fr/FR/Federation_Aeronautique.awp" target="_blank">Fédération Française Aéronautique</a></li>
						<li>🎓 Cours adaptés à tous les profils (jeunes et adultes)</li>
						<li>🌿 Sensibilisation à l'impact environnemental de l'aérien</li>
					</ul>
				</div>

				<div class="schedule-card">
					<h3>📅 Horaires</h3>
					<div class="time-slot">
						<span class="day">Mercredi</span>
						<span class="time">17h30 - 19h30</span>
					</div>
					<div class="time-slot">
						<span class="day">Samedi</span>
						<span class="time">10h00 - 12h00</span>
					</div>
				</div>
			</div>
		</section>

		<section class="content-section glass-panel" id="nous-connaitre">
			<div class="section-header">
				<h2>Nous Connaître</h2>
			</div>
			<div class="section-body">
				<p>
					Créée en décembre 2020, notre association loi 1901 <strong>« Aérien Ambassadeurs Avenir »</strong> (Triple A) a pour objectifs de partager notre passion pour l'aéronautique avec la jeunesse, de susciter des vocations et de développer une conscience environnementale.
				</p>
				
				<div class="timeline">
					<div class="timeline-item">
						<span class="year">2020</span>
						<p>Alors que la France se confine, Air France souhaite proposer aux enfants de ses salariés des cours en ligne pour se former au BIA.</p>
					</div>
					<div class="timeline-item">
						<span class="year">Création</span>
						<p>L’association « Triple A » est créée, composée d’employés d’Air France, de Cadets Air France, et d'Elèves Pilotes de Ligne (EPL) de l’ENAC. Plus de 900 élèves formés sur 2 ans.</p>
					</div>
					<div class="timeline-item">
						<span class="year">2022</span>
						<p>L’association prend son indépendance pour s’ouvrir à tous. Le profil des professeurs bénévoles se diversifie (pilotes, PNC, ingénieurs, dispatcheurs, etc.).</p>
					</div>
				</div>
			</div>
		</section>
	</div>
</div>

<style>
	.page-container {
		max-width: 1100px;
		margin: 0 auto;
		display: flex;
		flex-direction: column;
		gap: 32px;
		padding-bottom: 40px;
	}

	.glass-panel {
		background: var(--glass-bg);
		backdrop-filter: blur(12px);
		-webkit-backdrop-filter: blur(12px);
		border: 1px solid var(--glass-border);
		border-radius: var(--radius-xl);
		padding: 32px;
		box-shadow: var(--glass-shadow);
	}

	.hero {
		text-align: center;
		padding: 48px 24px;
		background: linear-gradient(135deg, rgba(255,255,255,0.8), rgba(255,255,255,0.4));
	}

	h1 {
		font-size: 2.5rem;
		margin: 0 0 0.5rem 0;
		background: var(--card-blue);
		-webkit-background-clip: text;
		-webkit-text-fill-color: transparent;
		font-weight: 800;
	}

	h2 {
		font-size: 1.75rem;
		margin: 0;
		color: var(--text-dark);
	}

	h3 {
		font-size: 1.2rem;
		margin: 0 0 16px 0;
		color: var(--text-dark);
	}

	.subtitle {
		font-size: 1.25rem;
		color: var(--text-muted);
		margin-bottom: 32px;
		font-weight: 500;
	}

	.actions {
		display: flex;
		justify-content: center;
		gap: 16px;
		flex-wrap: wrap;
	}

	.btn {
		display: inline-flex;
		align-items: center;
		padding: 12px 28px;
		border-radius: 14px;
		text-decoration: none;
		font-weight: 700;
		transition: transform 0.2s, box-shadow 0.2s;
		font-size: 1rem;
	}

	.btn:hover {
		transform: translateY(-2px);
		box-shadow: 0 8px 20px rgba(0,0,0,0.15);
	}

	.btn.primary {
		background: var(--card-blue);
		color: white;
		border: none;
	}

	.btn.secondary {
		background: rgba(255, 255, 255, 0.8);
		border: 2px solid rgba(226, 232, 240, 0.8);
		color: var(--text-dark);
	}

	.content-grid {
		display: grid;
		grid-template-columns: 1fr;
		gap: 32px;
	}

	@media (min-width: 900px) {
		.content-grid {
			grid-template-columns: 1fr 1fr;
			align-items: start;
		}
	}

	.content-section {
		height: 100%;
		display: flex;
		flex-direction: column;
	}

	.section-header {
		margin-bottom: 24px;
		padding-bottom: 16px;
		border-bottom: 2px solid rgba(0,0,0,0.05);
	}

	.section-body {
		flex: 1;
		display: flex;
		flex-direction: column;
		gap: 24px;
	}

	.section-body p {
		line-height: 1.6;
		margin: 0;
		color: #4a5568;
	}

	.highlight-box {
		background: rgba(255, 255, 255, 0.5);
		border-radius: 16px;
		padding: 20px;
	}

	.benefits-list {
		list-style: none;
		padding: 0;
		margin: 0;
	}

	.benefits-list li {
		margin-bottom: 12px;
		padding-left: 0;
		position: relative;
		line-height: 1.5;
	}
	
	.benefits-list li:last-child {
		margin-bottom: 0;
	}

	.schedule-card {
		background: var(--bg-grey);
		padding: 20px;
		border-radius: 16px;
		border: 1px solid rgba(0,0,0,0.05);
	}

	.time-slot {
		display: flex;
		justify-content: space-between;
		padding: 12px 0;
		border-bottom: 1px solid rgba(0,0,0,0.1);
		font-weight: 600;
	}

	.time-slot:last-child {
		border-bottom: none;
	}

	.day {
		color: var(--text-dark);
	}

	.time {
		color: #2f80ed;
	}

	.timeline {
		padding-left: 10px;
	}

	.timeline-item {
		position: relative;
		padding-left: 24px;
		margin-bottom: 24px;
		border-left: 2px solid #cbd5e0;
	}
	
	.timeline-item:last-child {
		margin-bottom: 0;
		border-left: 2px solid transparent; /* Stop the line */
	}

	.timeline-item::before {
		content: '';
		position: absolute;
		left: -6px;
		top: 0;
		width: 10px;
		height: 10px;
		border-radius: 50%;
		background: var(--card-blue);
		border: 2px solid white;
	}

	.year {
		display: inline-block;
		padding: 4px 10px;
		background: #e2e8f0;
		border-radius: 12px;
		font-size: 0.85rem;
		font-weight: bold;
		color: var(--text-dark);
		margin-bottom: 8px;
	}

	.partners-box {
		margin-top: auto;
		padding-top: 16px;
		border-top: 2px solid rgba(0,0,0,0.05);
	}

	.partners-list {
		list-style: none;
		padding: 0;
		margin: 16px 0 0 0;
	}

	.partners-list li {
		margin-bottom: 8px;
	}

	a {
		color: #2f80ed;
		text-decoration: none;
		font-weight: 500;
		transition: color 0.2s;
	}

	a:hover {
		color: #1a5cbe;
		text-decoration: underline;
	}
</style>
