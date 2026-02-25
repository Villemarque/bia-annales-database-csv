import { writable } from 'svelte/store';

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
import { parseSubject } from '$lib/subject';

export const attempts = writable<Record<Qid, Attempt[]>>({}, (set) => {
	getDb.then((db: Db) => {
		db.stores.attempt.getMany().then((attemptsArrayArray) => {
			const attemptsRecord: Record<Qid, Attempt[]> = {};
			for (const attemptsArray of attemptsArrayArray as Attempt[][]) {
				if (attemptsArray) {
					const first = attemptsArray[0];
					attemptsRecord[first.qid] = attemptsArray;
				}
			}
			set(attemptsRecord);
			log.log('attempts store populated from IndexedDB');
		});
	});
});

// always keep the object in sync with IndexedDB
attempts.subscribe((value: Record<Qid, Attempt[]>) => {
	getDb.then((db: Db) => {
		for (const [qid, attempts] of Object.entries(value)) {
			db.stores.attempt.put(qid, attempts);
		}
	});
});

export const addAttempt = (attempt: Attempt) => {
	attempts.update((current) => {
		const qid = attempt.qid;
		const attemptsForQid = current[qid] || [];
		attemptsForQid.push(attempt);
		current[qid] = attemptsForQid;
		return current;
	});
};
