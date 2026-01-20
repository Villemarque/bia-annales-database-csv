import { writable, readonly } from 'svelte/store';


type Qid = string;

// | Champ | Description |
//| :--- | :--- |
//| `qid` | Identifiant unique. |
//| `year` | Année de l'examen. |
//| `label` | Étiquette de la question (ex: `1.1`). |
//| `no` | Ordre dans l'examen, commençant à 0. |
//| `content_verbatim` | Énoncé original. Généralement ne pas utiliser, si `content_fixed` existe.|
//| `content_fixed` | Énoncé corrigé. |
//| `choice_[abcd]`| Les quatre propositions de réponse. (`choice_a`) réponse A, etc.) |
//| `answer` | Indice de la réponse correcte (0=A, 1=B, 2=C, 3=D). |
//| `chapter` | Référence au chapitre du programme. /!\ Les chapitres ne correspondent pas au `label`. |
//| `attachment_link` | Lien vers l'image d'illustration si existant |
//| `mixed_choices` | Indique si l'ordre des choix peut être aléatoire. |
interface Question {
	qid: Qid;
	year: number;
	label: string;
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

const timeoutFor = (s: number) =>
	new Promise<void>((resolve) => {
		setTimeout(() => {
			console.log(`${s} seconds passed!`);
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
			label,
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
			label,
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
			qs[qid] = (question);
			return qs;
		});
	}
	const unsubscribe = questions.subscribe((value) => {
		console.log('questions value', value);
	});

	unsubscribe();
};
