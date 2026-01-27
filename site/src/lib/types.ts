

export type Qid = string;
export type SessionId = string;
export type AttemptId = string;

type Timpestamp = number; // milliseconds since epoch

// see annales-bia.csv
export interface Question {
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


export interface Attempt {
    id: AttemptId;
    qid: Qid;
    session_id: SessionId;
    selected_choice: number;
    // correct: boolean; // denormalise?
    timestamp: Timpestamp;
    duration_ms: number;
    // source: 'practice' | 'exam' | 'review';
    notes: string | undefined;
}


export interface Session {
    id: SessionId;
    name: string;
    year?: number; // only set if it's reproducing the exam of that year
    created_at: Timpestamp;
    updated_at: Timpestamp;
    question_ids: Qid[];
}