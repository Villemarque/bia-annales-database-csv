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
	type QuestionWip,
	type AttemptId,
	type Timestamp,
	type Question,
	type OngoingSession,
	createBySubject
} from '$lib/types';
import { parseSubject } from '$lib/subject';
import { unsafeRandomId } from '$lib/random';

export const attempts = writable<Record<Qid, Attempt[]>>({}, (set) => {
	getDb.then((db: Db) => {
		// {id: Qid, data: Attempt[]}[]
		db.stores.attempt.getMany().then((attemptsArrayArray) => {
			log.log('attemptsArray', attemptsArrayArray);
			const attemptsRecord: Record<Qid, Attempt[]> = {};
			for (const idbObj of attemptsArrayArray as { id: Qid; data: Attempt[] }[]) {
				attemptsRecord[idbObj.id] = idbObj.data;
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

export const makeAttempt = (
	from: QuestionWip,
	session: OngoingSession,
	q: Question,
	duration_s: number
): Attempt | undefined => {
	if (from.selected_choice === undefined) {
		log.error(`Cannot make Attempt from QuestionWip with undefined selected_choice! ${JSON.stringify(from)}`);
		return;
	}
	return {
		id: unsafeRandomId({ prefix: 'att' }) as AttemptId,
		qid: from.qid,
		sessionId: session.id,
		selectedChoice: from.selected_choice,
		correct: from.selected_choice === q.answer,
		timestamp: Date.now() as Timestamp,
		duration_s
	};
};

export const addAttempt = (attempt: Attempt) => {
	attempts.update((current) => {
		const qid = attempt.qid;
		const attemptsForQid = current[qid] || [];
		attemptsForQid.push(attempt);
		current[qid] = attemptsForQid;
		return current;
	});
};
