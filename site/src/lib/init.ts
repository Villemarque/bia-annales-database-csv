import { loadQuestions } from '$lib/stores/questions';
import { log } from '$lib/log';
import { initDb } from '$lib/getDb';

export function init(csv: string): void {
	initDb();
	// no need to wait for db to start fetching questions
	loadQuestions(csv);
}
