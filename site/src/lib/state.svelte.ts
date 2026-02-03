import { Chapters } from '$lib/types';
import { type Subject, type ChapterId, ChaptersBySubject, type Qid } from '$lib/types';
import { attempts } from '$lib/stores/attempt';
import { questionsBySubject } from '$lib/stores/question';

export interface ChaptersState {
	onlyNew: boolean;
	selected: ChapterId[];
	includeRest: boolean; // questions with no chapter
}

export interface PotentialQuestions {
	selected: Record<ChapterId, Qid[]>;
	rest: Qid[];
}

const potentialQuestionsFrom = (
	subjectId: Subject,
	chaptersState: ChaptersState,
	filterFun: (qid: Qid) => boolean
): PotentialQuestions => {
	const selected = chaptersState.selected
		.map((chapterId) => {
			return (chapterId, $questionsBySubject[subjectId][chapterId].filter(filterFun));
		})
		.reduce(
			(acc, [chapterId, qids]) => {
				acc[chapterId] = qids;
				return acc;
			},
			{} as Record<ChapterId, Qid[]>
		);
};

const isUnattemptedOrIncorrect = (qid) => {
	const attempt = $attempts[qid];
	return !attempt || !attempt.correct;
};

export const getPotentialQuestions = (subjectId: Subject) => (chaptersState: ChaptersState) => {
	const filterFun = chaptersState.onlyNew ? isUnattemptedOrIncorrect : () => true;
	return potentialQuestionsFrom(subjectId, chaptersState, filterFun);
};
