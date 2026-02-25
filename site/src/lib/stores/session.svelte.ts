import { writable } from 'svelte/store';

import { log } from '$lib/log';
import { Db } from '$lib/db';
import type { Attempt, Qid, Subject, ChapterId, QuestionsByChapter, OngoingSession, LocalStorageKey } from '$lib/types';
import { parseSubject } from '$lib/subject';
import { PersistedState } from 'runed';

const sessionKey = 'ongoingSession' as LocalStorageKey;
const durationKey = 'sessionDuration' as LocalStorageKey;

const initLocalStorage =
	<T>(key: LocalStorageKey) =>
	(set: (t: T) => void) => {
		const valueStr = Db.getLocalStorage(key);
		if (valueStr) {
			try {
				const value = JSON.parse(valueStr) as T;
				set(value);
				log.log(`${key} store populated from localStorage`);
			} catch (error) {
				log.error(`Error loading ${key} from localStorage:`, error);
			}
		}
	};

export const sessionState = new PersistedState<OngoingSession | undefined>(sessionKey, undefined);
export const sessionDuration = new PersistedState<number | undefined>(durationKey, undefined);

// always keep the object in sync with localStorage
// ongoingSession.subscribe((value: OngoingSession | undefined) => {
//     Db.setLocalSorage(sessionKey, JSON.stringify(value));
// });
