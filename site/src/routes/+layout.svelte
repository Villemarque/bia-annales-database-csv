<script lang="ts">
	import type { LayoutProps } from './$types';
	import type { ResolvedPathname } from '$app/types';
	import './layout.css'; // for reusable CSS components

	import favicon from '$lib/assets/favicon.svg';
	import HamburgerIcon from '../components/HamburgerIcon.svelte';
	import MenuCapsule from '../components/MenuCapsule.svelte';
	import Header from '../components/Header.svelte';
	import Footer from '../components/Footer.svelte';

	let { children }: LayoutProps = $props();

	let sidebarExpanded = $state(false);
	const toggleSidebar = () => (sidebarExpanded = !sidebarExpanded);

	const href = (path: ResolvedPathname): { tpe: 'href'; href: ResolvedPathname } => ({ tpe: 'href', href: path });
	const onToggleF = (fn: () => void): { tpe: 'toggle'; onToggle: () => void } => ({ tpe: 'toggle', onToggle: fn });

	const menuItems = [
		{ icon: '🏠', label: 'Accueil', action: href('/') },
		{ icon: '✈︎', label: 'Programme', action: href('/quiz') },
		{ icon: '📅', label: 'Annales', action: href('/annales') },
		{ icon: '📜', label: 'Sessions', action: href('/sessions') },
		{ icon: '🔍', label: 'Questions', action: href('/questions') },
		{ icon: '⚙️', label: 'Paramètres', action: href('/settings') }
	];

	const ham_item = [{ icon: HamburgerIcon, label: 'Menu', action: onToggleF(toggleSidebar) }];
</script>

<svelte:head>
	<link rel="icon" href={favicon} />
</svelte:head>

<div class="app" class:sidebar-expanded={sidebarExpanded}>
	<div class="hamburger-wrapper">
		<MenuCapsule expanded={sidebarExpanded} items={ham_item} />
	</div>
	<div class="menu-wrapper">
		<MenuCapsule expanded={sidebarExpanded} items={menuItems} />
	</div>

	<div class="header-wrapper">
		<Header />
	</div>

	<main class="content-wrapper">
		<div class="content">
			{@render children()}
		</div>
	</main>

	<div class="footer-wrapper">
		<Footer />
	</div>
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
		--gap-main: 16px;
		font-family: 'Open Sans', sans-serif;
	}

	:global(body) {
		margin: 0;
		min-height: 100vh;
		background: var(--bg-grey);
		color: var(--text-dark);
		overflow-x: hidden;
	}

	.app {
		display: grid;
		grid-template-areas:
			'hamburger header'
			'menu content'
			'footer footer';
		grid-template-columns: auto 1fr;
		grid-template-rows: auto 1fr auto;
		gap: var(--gap-main);
		min-height: 100vh;
		transition: grid-template-columns 0.2s ease;
	}

	.hamburger-wrapper {
		grid-area: hamburger;
		position: sticky;
		top: 0;
		z-index: 100;
		display: flex;
		align-items: center;
		justify-content: center;
		/* Height implicit from grid row */
	}

	.menu-wrapper {
		grid-area: menu;
		position: sticky;
		z-index: 100;
		display: flex;
		flex-direction: column;
		align-items: center;
		align-self: start; /* Don't stretch to fill vertical space if content is short */
	}

	.hamburger-wrapper,
	.menu-wrapper {
		padding-left: var(--gap-main);
	}

	.header-wrapper {
		grid-area: header;
		min-width: 0;
	}

	.content-wrapper {
		grid-area: content;
		display: flex;
		flex-direction: column;
		flex: 1;
		min-width: 0;
	}

	.content {
		flex: 1;
		min-width: 0;
	}

	.footer-wrapper {
		grid-area: footer;
	}

	@media (max-width: 900px) {
		.app {
			grid-template-areas:
				'hamburger header'
				'content content'
				'footer footer';
		}
		.menu-wrapper {
			display: none;
		}
		.sidebar-expanded .menu-wrapper {
			position: fixed;
			top: 120px;
			left: 16px;
			width: auto;
			height: auto;
			padding: 0 !important;
			justify-content: flex-start;
			display: flex;
		}
	}
</style>
