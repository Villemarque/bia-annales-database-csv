import { type ChapterId, ChaptersById } from '$lib/types';

export const parseChapterId = (s: string): ChapterId => {
	// check if in ChaptersById
	const id = parseInt(s.trim()) as ChapterId;
	if (!(id in ChaptersById)) {
		throw new Error(`Invalid ChapterId: ${s}`);
	}
	return id;
};
