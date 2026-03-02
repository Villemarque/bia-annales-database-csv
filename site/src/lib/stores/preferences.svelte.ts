import { PersistedState } from 'runed';
import type { LocalStorageKey } from '$lib/types';

export type Preferences = {
	autoAdvance: boolean;
};

const preferencesKey = 'userPreferences' as LocalStorageKey;

const defaultPreferences: Preferences = {
	autoAdvance: false
};

export const preferences = new PersistedState<Preferences>(preferencesKey, defaultPreferences);
