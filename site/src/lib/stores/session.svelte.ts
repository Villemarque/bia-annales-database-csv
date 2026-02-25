import { writable } from 'svelte/store';

import { unsafeRandomId } from '$lib/random';
import { log } from '$lib/log';
import { Db } from '$lib/db';
import { getDb } from '$lib/getDb';
import type {
	Attempt,
	Qid,
	Subject,
	ChapterId,
	Timestamp,
	QuestionsByChapter,
	OngoingSession,
	Session,
	LocalStorageKey,
	SessionId
} from '$lib/types';
import { parseSubject } from '$lib/subject';
import { PersistedState } from 'runed';

const sessionKey = 'ongoingSession' as LocalStorageKey;
const durationKey = 'sessionDuration' as LocalStorageKey;
const durationByQKey = 'sessionDurationByQ' as LocalStorageKey;

export const sessionState = new PersistedState<OngoingSession | undefined>(sessionKey, undefined);
// if above is defined, assume below belongs to it
export const sessionDuration = new PersistedState<number>(durationKey, 0);
export const durationByQ = new PersistedState<Record<Qid, number>>(durationByQKey, {});
// most recent first
export const pastSessions = writable<Session[]>([], (set) => {
	getDb.then((db: Db) => {
		db.stores.attempt.getMany().then((sessions) => {
			// sort by most recent first
			(sessions as Session[]).sort((a, b) => b.created_at - a.created_at);
			set(sessions as Session[]);
			log.log('(finished) sessions store populated from IndexedDB');
		});
	});
});

// always keep the object in sync with IndexedDB
pastSessions.subscribe((value: Session[]) => {
	getDb.then((db: Db) => {
		for (const session of value) {
			db.stores.attempt.put(session.id, session);
		}
	});
});

export const makeNewSession = (name: string, selectedQids: Qid[]) => {
	if (sessionState.current) {
		log.error(
			`Overriding ongoing Session ${sessionState.current.id} with a new Session! ${JSON.stringify(sessionState.current)}`
		);
	}
	sessionState.current = {
		id: unsafeRandomId({ prefix: 'ses' }) as SessionId, // Simple ID generation
		name,
		created_at: Date.now() as Timestamp,
		kind: {
			is: 'study'
		},
		questions: selectedQids.map((qid) => ({
			qid,
			duration_s: 0
		}))
	};
	sessionDuration.current = 0;
};

export const saveSession = () => {
	if (!sessionState.current) {
		log.error('Trying to end a session when there is no ongoing session!');
	} else {
		const endedSession: Session = {
			...sessionState.current,
			questions: sessionState.current.questions.map((q) => q.qid),
			duration_s: sessionDuration.current || 0
		};
		pastSessions.update((current) => [endedSession, ...current]);
	}
	cancelSession();
};

export const cancelSession = () => {
	if (!sessionState.current) {
		log.error('Trying to cancel a session when there is no ongoing session!');
	}
	sessionState.current = undefined;
	sessionDuration.current = 0;
	durationByQ.current = {};
};
