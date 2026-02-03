import { type Subject, Subjects } from '$lib/types';

export const parseSubject = (s: string): Subject => {
	// check if in ChaptersById
	const id = parseInt(s.trim()) as Subject;
	if (!(id in Object.values(Subjects))) {
		throw new Error(`Invalid Subject: ${s}`);
	}
	return id;
};
