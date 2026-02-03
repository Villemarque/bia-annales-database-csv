import { derived, writable } from 'svelte/store';

import { log } from '$lib/log';
import { getDb } from '$lib/getDb';
import { type Db } from '$lib/db';
import {
	type Attempt,
	type Qid,
	type Subject,
	type ChapterId,
	type QuestionsByChapter,
	type BySubject,
	createBySubject
} from '$lib/types';
import { parseChapterId } from '$lib/chapter';
import { parseSubject } from '$lib/subject';

export const attempts = writable<Record<Qid, Attempt>>({}, (set) => {
	getDb.then((db: Db) => {
		db.stores.attempt.getMany().then((attemptsArray) => {
			const attemptsRecord: Record<Qid, Attempt> = {};
			for (const attempt of attemptsArray as Attempt[]) {
				attemptsRecord[attempt.qid] = attempt;
			}
			set(attemptsRecord);
			log.log('attempts store populated from IndexedDB');
		});
	});
});

// always keep the object in sync with IndexedDB
attempts.subscribe((value: Record<Qid, Attempt>) => {
	getDb.then((db: Db) => {
		for (const [qid, attempt] of Object.entries(value)) {
			db.stores.attempt.put(qid, attempt);
		}
	});
});
