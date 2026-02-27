<script lang="ts">
	import type { LayoutProps } from './$types';

	import favicon from '$lib/assets/favicon.svg';
	import HamburgerButton from '../components/HamburgerButton.svelte';
	import MenuCapsule from '../components/MenuCapsule.svelte';
	import Header from '../components/Header.svelte';
	import Footer from '../components/Footer.svelte';

	let { children }: LayoutProps = $props();

	let sidebarExpanded = $state(false);
	const toggleSidebar = () => (sidebarExpanded = !sidebarExpanded);

	const href = (path: string): { tpe: 'href'; href: string } => ({ tpe: 'href', href: path });
	const onToggleF = (fn: () => void): { tpe: 'toggle'; onToggle: () => void } => ({ tpe: 'toggle', onToggle: fn });

	const menuItems = [
		{ icon: '🏠', label: 'Accueil', action: href('/') },
		{ icon: '✈︎', label: 'Programme', action: href('/quiz') },
		{ icon: '📜', label: 'Sessions', action: href('/sessions') },
		{ icon: '⚙️', label: 'Paramètres', action: href('/settings') }
	];

	const ham_item = [{ icon: '☰', label: 'Menu', action: onToggleF(toggleSidebar) }];
</script>

<svelte:head>
	<link rel="icon" href={favicon} />
</svelte:head>

<div class="app" class:sidebar-expanded={sidebarExpanded}>
	<div class="nav-col">
		<div class="hamburger-wrapper">
			<MenuCapsule expanded={sidebarExpanded} items={ham_item} />
		</div>
		<div class="menu-wrapper">
			<MenuCapsule expanded={sidebarExpanded} items={menuItems} />
		</div>
	</div>

	<div class="main-col">
		<Header />
		<main class="content-wrapper">
			<div class="content">
				{@render children()}
			</div>
		</main>
	</div>
	<Footer />
</div>

<style>
	:root {
		--glass-bg: rgba(255, 255, 255, 0.55);
		--glass-bg-strong: rgba(255, 255, 255, 0.75);
		--glass-border: rgba(255, 255, 255, 0.6);
		--glass-shadow: 0 12px 40px rgba(0, 0, 0, 0.15);
		--bg-grey: #f2f4f7;
		--card-blue: linear-gradient(135deg, #2f80ed, #56ccf2);
		--card-indigo: linear-gradient(135deg, #5f2cff, #9b6bff);
		--card-green: linear-gradient(135deg, #1fa971, #6ee7b7);
		--card-orange: linear-gradient(135deg, #f2994a, #f2c94c);
		--card-red: linear-gradient(135deg, #eb5757, #f29999);
		--card-pink: linear-gradient(135deg, #d946ef, #f472b6);
		--text-dark: #0b1320;
		--text-muted: rgba(0, 0, 0, 0.6);
		--radius-xl: 22px;
		--header-height: 104px; /* Matches Header.svelte padding + title height roughly */
		--gap-main: 15px;
		font-family: 'Open Sans', sans-serif;
	}

	:global(body) {
		margin: 0;
		min-height: 100vh;
		background: var(--bg-grey);
		color: var(--text-dark);
		overflow-x: hidden;
	}

	:global(.basecard) {
        padding: 26px;
        border-radius: var(--radius-xl);
        // color: white;
        box-shadow: var(--glass-shadow);
        transition: transform 0.35s ease;
        display: flex;
        flex-direction: column;
        cursor: pointer;
        border: none;
        text-align: left;
	}

	.app {
		display: grid;
		grid-template-columns: 80px 1fr;
		min-height: 100vh;
		transition: grid-template-columns 0.2s ease;
	}

	.app.sidebar-expanded {
		grid-template-columns: 220px 1fr;
	}

	.nav-col {
		display: grid;
		grid-template-rows: var(--header-height) 1fr;
		position: sticky;
		top: 0;
	}

	.hamburger-wrapper {
		display: flex;
		align-items: center;
		justify-content: center;
	}

	.menu-wrapper {
		display: flex;
		flex-direction: column;
		align-items: center;
		padding-top: var(--gap-main);
	}

	.sidebar-expanded .hamburger-wrapper,
	.sidebar-expanded .menu-wrapper {
		padding-left: 16px;
	}

	.main-col {
		display: flex;
		flex-direction: column;
		min-width: 0;
	}

	.content-wrapper {
		display: flex;
		flex-direction: column;
		flex: 1;
		gap: var(--gap-main);
		padding-top: var(--gap-main);
	}

	.content {
		flex: 1;
		min-width: 0;
	}

	.app :global(.footer) {
		grid-column: 1 / -1;
	}

	@media (max-width: 900px) {
		.app {
			display: block;
		}

		.nav-col {
			position: fixed;
			left: 16px;
			top: 24px;
			height: auto;
			z-index: 100;
			display: flex;
			flex-direction: column;
			gap: 16px;
			background: none;
		}

		.hamburger-wrapper,
		.menu-wrapper {
			padding: 0 !important;
			justify-content: flex-start;
		}

		.main-col {
			margin-left: 0;
		}

		.content {
			padding: 0 20px 40px;
		}
	}
</style>
