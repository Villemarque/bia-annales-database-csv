import {
	type Attempt,
	type Subject,
	type ChapterId,
	type BySubject,
	type QuestionsByChapter,
	type Qid
} from '$lib/types';

export interface ChaptersState {
	onlyNew: boolean;
	selected: ChapterId[];
	includeRest: boolean; // questions with no chapter
}

const potentialQuestionsFrom = (
	subjectId: Subject,
	questionsBySubject: BySubject<QuestionsByChapter>,
	chaptersState: ChaptersState,
	filterFun: (qid: Qid) => boolean
): QuestionsByChapter => {
	const chapters = chaptersState.selected
		.map((chapterId) => {
			console.log('subjectId', subjectId, 'chapterId', chapterId, questionsBySubject[subjectId].chapters[chapterId]);
			return [chapterId, questionsBySubject[subjectId].chapters[chapterId].filter(filterFun)] as [ChapterId, Qid[]];
		})
		.reduce(
			(acc, [chapterId, qids]) => {
				acc[chapterId] = qids;
				return acc;
			},
			{} as Record<ChapterId, Qid[]>
		);
	const rest = chaptersState.includeRest ? questionsBySubject[subjectId].rest.filter(filterFun) : [];
	return {
		chapters,
		rest
	};
};

const isUnattemptedOrIncorrect = (attempts: Record<Qid, Attempt>) => (qid: Qid) => {
	const attempt = attempts[qid];
	return !attempt || !attempt.correct;
};

export const getPotentialQuestions =
	(attempts: Record<Qid, Attempt>, questionsBySubject: BySubject<QuestionsByChapter>, subjectId: Subject) =>
	(chaptersState: ChaptersState): QuestionsByChapter => {
		const filterFun = chaptersState.onlyNew ? isUnattemptedOrIncorrect(attempts) : () => true;
		return potentialQuestionsFrom(subjectId, questionsBySubject, chaptersState, filterFun);
	};
