import { writable } from 'svelte/store';

import { unsafeRandomId } from '$lib/random';
import { log } from '$lib/log';
import { Db } from '$lib/db';
import type { Attempt, Qid, Subject, ChapterId, Timestamp, QuestionsByChapter, OngoingSession, LocalStorageKey, SessionId } from '$lib/types';
import { parseSubject } from '$lib/subject';
import { PersistedState } from 'runed';

const sessionKey = 'ongoingSession' as LocalStorageKey;
const durationKey = 'sessionDuration' as LocalStorageKey;

export const sessionState = new PersistedState<OngoingSession | undefined>(sessionKey, undefined);
export const sessionDuration = new PersistedState<number | undefined>(durationKey, undefined);

export const makeNewSession = (name: string, selectedQids: Qid[]) => {
		if (sessionState.current) {
			log.error(`Overriding ongoing Session ${sessionState.current.id} with a new Session! ${JSON.stringify(sessionState.current)}`);
		}
		sessionState.current = {
			id: unsafeRandomId({ prefix: 'ses' }) as SessionId, // Simple ID generation
			name,
			created_at: Date.now() as Timestamp,
			kind: {
				is: 'practice'
			},
			questions: selectedQids.map((qid) => ({
				qid,
				duration_s: 0
			})),
			check_answer_immediate: true // Default behavior for now
		};
		sessionDuration.current = 0;
}
