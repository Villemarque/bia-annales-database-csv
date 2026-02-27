import { asset } from '$app/paths';
import type { LayoutLoad } from './$types';

import { init } from '$lib/init';

export const ssr = false; // SPA for PWA
// TODO FIXME can this be actived back?
// export const prerender = true;

export const load: LayoutLoad = async ({ fetch }) => {
	console.log('Loading questions in +layout.ts');
	await fetch(asset('/annales-bia.csv')).then((response) =>
		response.text().then((csv) => {
			init(csv);
		})
	);
	return {};
};
