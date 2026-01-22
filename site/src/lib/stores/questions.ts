import { writable, readonly } from 'svelte/store';

import {log} from '$lib/log';

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
	chapter: string;
	attachment_link: string | undefined;
	mixed_choices: boolean;
}

// TODO change to dict < Qid, question>
const questionsWritable = writable<Record<Qid, Question>>({});
export const questions = readonly(questionsWritable);

// only used for testing
const timeoutFor = (s: number) =>
	new Promise<void>((resolve) => {
		setTimeout(() => {
			log.log(`${s} seconds passed!`);
			resolve();
		}, s * 1000);
	});

export const loadQuestions = async (): Promise<void> => {
	const response = await timeoutFor(0).then(() => fetch('/annales-bia.csv'));
	// \t separated values
	const text = await response.text();
	const lines = text.split('\n').slice(1); // remove header
	for (const line of lines) {
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
		const question: Question = {
			qid,
			year: parseInt(year),
			subject: parseInt(subject),
			no_subject: parseInt(no_subject),
			no: parseInt(no),
			content,
			choice_a,
			choice_b,
			choice_c,
			choice_d,
			answer: parseInt(answer),
			chapter,
			attachment_link: attachment_link || undefined,
			mixed_choices: mixed_choices === '1'
		};
		questionsWritable.update((qs) => {
			qs[qid] = question;
			return qs;
		});
	}
	const unsubscribe = questions.subscribe((value) => {
		console.log('questions value', value);
	});

	unsubscribe();
};
