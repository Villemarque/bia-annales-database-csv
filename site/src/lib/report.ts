import { base } from '$app/paths';
import { log } from '$lib/log';
import type { Qid } from '$lib/types';

// Replace with your Zulip Slack-compatible incoming webhook URL
const ZULIP_WEBHOOK_URL =
	'https://asso-triple-a.zulipchat.com/api/v1/external/slack_incoming?api_key=nthAjz2PSD59iLsFUZeECA8r3HcRBoxI&stream=624989&topic=report-questions';

export const questionUrl = (qid: Qid): string => `${base}/questions?qid=${encodeURIComponent(qid)}`;

export async function reportQuestion(sentence: string, qid: Qid): Promise<boolean> {
	const url = questionUrl(qid);
	// Slack-style link so Zulip renders it as a pretty clickable link, first in the message
	const pretty = `<${url}|Question ${qid}>`;
	// Advanced Block Kit formatting (section block, mrkdwn), with `text` as fallback for
	// clients that ignore `blocks` (Zulip's slack_incoming supports both).
	const text = `${pretty}\n${sentence}`;
	const payload = {
		text,
		blocks: [
			{
				type: 'section',
				text: {
					type: 'mrkdwn',
					text: `${pretty}\n\n${sentence}`
				}
			}
		]
	};
	// no-cors + form-encoded payload (Slack format): simple request, no CORS preflight,
	// so it works from a static site without a server to proxy through.
	const body = new URLSearchParams({
		payload: JSON.stringify(payload)
	});
	try {
		await fetch(ZULIP_WEBHOOK_URL, {
			method: 'POST',
			mode: 'no-cors',
			headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
			body
		});
		log.log(`Reported question ${qid}`);
		return true;
	} catch (e) {
		log.error(`Failed to report question ${qid}: ${e}`);
		return false;
	}
}
