export type Qid = string & { __qid__: void };
export type SessionId = string & { __sessionid__: void };
export type AttemptId = string & { __attemptid__: void };
export type Subject = number & { __subject__: void };
export type ChapterId = number & { __chapter__: void };
export type LocalStorageKey = string & { __localkey__: void };
export type Timestamp = number & { __timestamp__: void };
export type IdPrefix =
	| 'ses' // session
	| 'att'; // attempt

export const Subjects = {
	METEO: 0 as Subject,
	AERODYNAMIQUE: 1 as Subject,
	AERONEF: 2 as Subject,
	NAVIGATION: 3 as Subject,
	HISTOIRE: 4 as Subject,
	ANGLAIS: 5 as Subject
} as const;

type SubjectValues = (typeof Subjects)[keyof typeof Subjects];

export type BySubject<T> = {
	[key in SubjectValues]: T;
};

export function createBySubject<T>(defaultValue: T): BySubject<T> {
	const bySubject = {} as Partial<BySubject<T>>;

	// Iterate over the keys of the `Subjects` object (e.g., "METEO", "AERODYNAMIQUE").
	for (const v of Object.values(Subjects) as SubjectValues[]) {
		bySubject[v] = structuredClone(defaultValue);
	}

	// The loop guarantees all keys are set, so we can safely cast to the full type.
	return bySubject as BySubject<T>;
}

// see annales-bia.csv
export interface Question {
	qid: Qid;
	year: number;
	subject: Subject;
	no_subject: number;
	no: number;
	content: string;
	choices: string[];
	answer: number;
	chapters: ChapterId[];
	attachment_link: string | undefined;
	mixed_choices: boolean | undefined;
}

export interface Attempt {
	id: AttemptId;
	qid: Qid;
	session_id: SessionId;
	selected_choice: number;
	correct: boolean; // denormalised
	timestamp: Timestamp;
	duration_s: number;
	// source: 'practice' | 'exam';
	notes: string | undefined; // ???
}

interface SessionBase<T> {
	id: SessionId;
	name: string;
	kind: { is: 'exam'; year: number; initial_time: number } | { is: 'practice' };
	created_at: Timestamp;
	questions: T[];
}

export type Session = SessionBase<Qid> & {
	duration_s: number;
};

export interface QuestionWip {
	qid: Qid;
	duration_s: number;
	selected_choice?: number;
	correct_choice?: number; // if correct is set, then the question is no longer editable
}

// duration_s is notset until the end of the session, so that we can display a timer during the session
// without having to (de)serialise the session object on every tick.
export type OngoingSession = SessionBase<QuestionWip> & {
	// whether to display correct/incorrect as soon as the user selects a choice, or only at the end of the session
	check_answer_immediate: boolean;
};

export interface Chapter {
	name: string;
	id: ChapterId;
	subject: Subject;
}

export interface QuestionsByChapter {
	chapters: Record<ChapterId, Qid[]>;
	// questions with no chapters linked to
	rest: Qid[];
}

// deduplicated
export const QBCtoList = (qbc: QuestionsByChapter): Qid[] => {
	const qidsSet = new Set<Qid>();
	for (const chapterQids of Object.values(qbc.chapters)) {
		for (const qid of chapterQids) {
			qidsSet.add(qid);
		}
	}
	for (const qid of qbc.rest) {
		qidsSet.add(qid);
	}
	return Array.from(qidsSet);
};

// "1.1 Les aéronefs": 0
// "1.2 Instrumentation": 1
// "1.3 Moteurs": 2
// "2.1 La sustentation de l'aile": 3
// "2.2 Le vol stabilisé": 4,
// "2.3 L'aérostation et le vol spatial": 5
// "3.1 L'atmosphère": 6
// "3.2  Les masses d'air et les fronts": 7
// "3.3  Les nuages": 8
// "3.4 Les vents": 9
// "3.5 Les phénomènes dangereux": 10
// "3.6 L'information météo": 11
// "4.1 Réglementation": 12
// "4.2 Sécurité des Vols (SV) et Facteurs Humains (FH)": 13
// "4.3 Navigation": 14
export const Chapters = [
	{
		name: '1.1 Les aéronefs',
		id: 0 as ChapterId,
		subject: Subjects.AERONEF
	},
	{
		name: '1.2 Instrumentation',
		id: 1 as ChapterId,
		subject: Subjects.AERONEF
	},
	{
		name: '1.3 Moteurs',
		id: 2 as ChapterId,
		subject: Subjects.AERONEF
	},
	{
		name: "2.1 La sustentation de l'aile",
		id: 3 as ChapterId,
		subject: Subjects.AERODYNAMIQUE
	},
	{
		name: '2.2 Le vol stabilisé',
		id: 4 as ChapterId,
		subject: Subjects.AERODYNAMIQUE
	},
	{
		name: "2.3 L'aérostation et le vol spatial",
		id: 5 as ChapterId,
		subject: Subjects.AERODYNAMIQUE
	},
	{
		name: "3.1 L'atmosphère",
		id: 6 as ChapterId,
		subject: Subjects.METEO
	},
	{
		name: "3.2  Les masses d'air et les fronts",
		id: 7 as ChapterId,
		subject: Subjects.METEO
	},
	{
		name: '3.3  Les nuages',
		id: 8 as ChapterId,
		subject: Subjects.METEO
	},
	{
		name: '3.4 Les vents',
		id: 9 as ChapterId,
		subject: Subjects.METEO
	},
	{
		name: '3.5 Les phénomènes dangereux',
		id: 10 as ChapterId,
		subject: Subjects.METEO
	},
	{
		name: "3.6 L'information météo",
		id: 11 as ChapterId,
		subject: Subjects.METEO
	},
	{
		name: '4.1 Réglementation',
		id: 12 as ChapterId,
		subject: Subjects.NAVIGATION
	},
	{
		name: '4.2 Sécurité des Vols (SV) et Facteurs Humains (FH)',
		id: 13 as ChapterId,
		subject: Subjects.NAVIGATION
	},
	{
		name: '4.3 Navigation',
		id: 14 as ChapterId,
		subject: Subjects.NAVIGATION
	}
] as const;

export const ChaptersById: Record<ChapterId, Chapter> = Chapters.reduce(
	(acc, chapter) => {
		acc[chapter.id] = chapter;
		return acc;
	},
	{} as Record<ChapterId, Chapter>
);

export const ChaptersBySubject: BySubject<Chapter[]> = Object.values(Subjects).reduce((acc, subject) => {
	acc[subject] = Chapters.filter((chapter) => chapter.subject === subject);
	return acc;
}, createBySubject<Chapter[]>([]));
