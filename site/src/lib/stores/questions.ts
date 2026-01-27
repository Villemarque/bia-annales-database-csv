import { derived, writable, readonly } from 'svelte/store';

import { log } from '$lib/log';

type Qid = string;

// see annales-bia.csv
interface Question {
	qid: Qid;
	year: number;
	subject: number;
	no_subject: number;
	no: number;
	content: string;
	choice_a: string;
	choice_b: string;
	choice_c: string;
	choice_d: string;
	answer: number;
	chapter: string | undefined;
	attachment_link: string | undefined;
	mixed_choices: boolean | undefined;
}

const questionsWritable = writable<Record<Qid, Question>>({});
export const questions = readonly(questionsWritable);
export const questionsBySubject = derived(questions, ($questions) => {
	const by_subject: Record<number, number> = {};
	for (const question of Object.values($questions)) {
		if (!(question.subject in by_subject)) {
			by_subject[question.subject] = 0;
		}
		by_subject[question.subject] += 1;
	}
	return by_subject;
});

// only used for testing
const timeoutFor = (s: number) =>
	new Promise<void>((resolve) => {
		setTimeout(() => {
			log.log(`${s} seconds passed!`);
			resolve();
		}, s * 1000);
	});

const maybeBool = (s: string): boolean | undefined => {
	switch (s.trim()) {
		case 'True':
			return true;
		case 'False':
			return false;
		case '':
			return undefined;
		default:
			throw new Error(`Invalid boolean string: '${s}', len = ${s.length}`);
	}
};

const notEmpty = (s: string): string => {
	if (s === '') {
		throw new Error('Expected non-empty string');
	}
	return s;
};

const undefIfEmpty = (s: string): string | undefined => {
	if (s === '') {
		return undefined;
	}
	return s;
};

export const loadQuestions = async (): Promise<void> => {
	const response = await timeoutFor(0).then(() => fetch('/annales-bia.csv'));
	// we only write to the store once all values parsed, to avoid trigeering derived each time
	const acc: Record<Qid, Question> = {};
	// \t separated values
	const text = await response.text();
	const lines = text.split('\n').slice(1); // remove header
	for (const [i, line] of lines.entries()) {
		const [
			qid,
			year,
			subject,
			no_subject,
			no,
			content_verbatim,
			content_fixed,
			choice_a,
			choice_b,
			choice_c,
			choice_d,
			answer,
			chapter,
			attachment_link,
			mixed_choices
		] = line.split('\t');
		const content = content_fixed || content_verbatim;
		try {
			const question: Question = {
				qid: notEmpty(qid),
				year: parseInt(year),
				subject: parseInt(subject),
				no_subject: parseInt(no_subject),
				no: parseInt(no),
				content: notEmpty(content),
				choice_a: notEmpty(choice_a),
				choice_b: notEmpty(choice_b),
				choice_c: notEmpty(choice_c),
				choice_d: notEmpty(choice_d),
				answer: parseInt(answer),
				chapter: undefIfEmpty(chapter),
				attachment_link: attachment_link || undefined,
				mixed_choices: maybeBool(mixed_choices)
			};
			acc[qid] = question;
		} catch (e) {
			log.error(`Error parsing question on line of CSV ${i + 2}: ${e}`);
		}
	}
	questionsWritable.set(acc);
	const unsubscribe = questions.subscribe((value) => {
		log.log('loaded questions CSV', value);
	});
	unsubscribe();
};
