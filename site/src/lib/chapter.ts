import { type ChapterId, ChaptersById, type Subject, ChaptersBySubject } from '$lib/types';

export const parseChapterId =
	(sub: Subject) =>
	(s: string): ChapterId => {
		// check if in ChaptersById
		const id = parseInt(s.trim()) as ChapterId;
		if (!(id in ChaptersById)) {
			throw new Error(`Invalid ChapterId: ${s}`);
		}
		if (!ChaptersBySubject[sub].map((x) => x.id).includes(id)) {
			throw new Error(`ChapterId ${id} does not belong to Subject ${sub}`);
		}
		return id;
	};
