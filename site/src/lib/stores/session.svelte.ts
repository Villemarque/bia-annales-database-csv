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

// using `null` and not undefined, see https://github.com/svecosystem/runed/pull/411
export const sessionState = new PersistedState<OngoingSession | null>(sessionKey, null);
// if above is defined, assume below belongs to it
// separate from sessionState for optimisation, see https://github.com/svecosystem/runed/issues/291
export const sessionDuration = new PersistedState<number>(durationKey, 0);
export const durationByQ = new PersistedState<Record<Qid, number>>(durationByQKey, {});
// most recent first
export const pastSessions = writable<Session[]>([], (set) => {
	getDb.then((db: Db) => {
		// {id: SessionId, data: Session}[]
		db.stores.session.getMany().then((idbArray) => {
			// sort by most recent first
			const sessions = (idbArray as { id: SessionId; data: Session }[]).map((obj) => obj.data);
			sessions.sort((a, b) => b.created_at - a.created_at);
			set(sessions);
			log.log('(finished) sessions store populated from IndexedDB');
		});
	});
});

// always keep the object in sync with IndexedDB
pastSessions.subscribe((value: Session[]) => {
	log.log('new value past session', value);
	getDb.then((db: Db) => {
		for (const session of value) {
			console.log('SESSION', session);
			db.stores.session.put(session.id, session);
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
	if (sessionState.current === null) {
		log.error('Trying to end a session when there is no ongoing session!');
	} else {
		// hack needed here to avoid issues with proxy
		// and get back a plain value
		// https://github.com/svecosystem/runed/issues/407
		const ongoing = JSON.parse(JSON.stringify(sessionState.current));
		const endedSession: Session = {
			...ongoing,
			questions: sessionState.current.questions.map((q) => q.qid),
			duration_s: sessionDuration.current || 0
		};
		pastSessions.update((current) => {
			current.unshift(endedSession);
			return current;
		});
	}
	cancelSession();
};

export const cancelSession = () => {
	if (!sessionState.current) {
		log.error('Trying to cancel a session when there is no ongoing session!');
	}
	log.log(`Cancelling session ${sessionState.current}`);
	sessionState.current = null;
	log.log(`After cancelling session ${sessionState.current}`);
	sessionDuration.current = 0;
	durationByQ.current = {};
};
