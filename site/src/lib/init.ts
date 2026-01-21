import { loadQuestions } from './stores/questions.ts';
import { log } from './log.ts';
import { initDb } from './getDb.ts';

export function init(): void {
    initDb();
    // no need to wait for db to start fetching questions
	loadQuestions();
}
