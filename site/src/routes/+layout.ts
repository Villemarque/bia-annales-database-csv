import type { LayoutLoad } from './$types';
import { init } from '$lib/init';

export const ssr = false; // SPA for PWA
export const prerender = true;

export const load: LayoutLoad = async ({ fetch, params }) => {
	console.log('Loading questions in +layout.ts');
	init(); // TODO use the fetch from load?;
	return {};
};
