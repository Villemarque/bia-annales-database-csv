import type { LayoutLoad } from './$types';
import { init } from '$lib/init';

export const ssr = false; // SPA for PWA
// export const prerender = true;

export const load: LayoutLoad = async ({ fetch }) => {
	console.log('Loading questions in +layout.ts');
	await fetch('/annales-bia.csv').then((response) =>
		response.text().then((csv) => {
			init(csv);
		})
	);
	return {};
};
