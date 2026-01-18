<script>
	export let open = false;
</script>

<div class="drawer {open ? 'open' : ''}" aria-hidden={!open}>
	<ul>
		<li>Accueil</li>
		<li>Programme</li>
		<li>Ressources</li>
		<li>Progression</li>
		<li>Paramètres</li>
	</ul>
</div>

<style>
	.drawer {
		position: fixed;
		top: 0;
		left: 0;
		height: 100vh;
		width: 320px;
		transform: translateX(-100%);
		background: var(--glass-bg-strong);
		backdrop-filter: blur(36px) saturate(180%);
		border-right: 1px solid var(--glass-border);
		box-shadow: var(--glass-shadow);
		padding: 40px 28px;
		transition: transform 0.45s cubic-bezier(0.4, 0, 0.2, 1);
		z-index: 20;
	}
	.drawer.open {
		transform: translateX(0);
	}
	.drawer h2 {
		margin-top: 0;
		font-size: 22px;
	}
	.drawer ul {
		list-style: none;
		padding: 0;
		margin: 30px 0 0;
		display: grid;
		gap: 18px;
	}
	.drawer li {
		padding: 14px 18px;
		border-radius: 16px;
		background: rgba(255, 255, 255, 0.6);
		border: 1px solid var(--glass-border);
		cursor: pointer;
	}
</style>
