import { writable } from 'svelte/store';

// store that take a very long time on initialisation, to see impact
// on render time
export const timeout = writable(false, () => {
	const timeoutId = setTimeout(() => {
		timeout.set(true);
	}, 5000);

	return () => {
		clearTimeout(timeoutId);
	};
});
