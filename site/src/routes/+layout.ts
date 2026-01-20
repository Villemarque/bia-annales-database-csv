import type { LayoutLoad } from './$types';
import { loadQuestions } from '$lib/stores/questions';

export const ssr = false; // SPA for PWA

export const load: LayoutLoad = async ({ fetch, params }) => {
	console.log('Loading questions in +layout.ts');
	loadQuestions(); // TODO use the fetch from load?;
	return {};
};
