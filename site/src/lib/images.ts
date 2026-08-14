import { get } from 'svelte/store';

import { asset } from '$app/paths';
import { log } from '$lib/log';
import { questions } from '$lib/stores/questions';

export const imageUrl = (attachmentLink: string): string => asset(`/img-sujets/${attachmentLink}.jpeg`);

export async function checkImagesExist(): Promise<void> {
	const all = Object.values(get(questions));
	const links = [...new Set(all.flatMap((q) => (q.attachment_link ? [q.attachment_link] : [])))];
	if (links.length === 0) return;

	const results = await Promise.all(
		links.map(async (link) => {
			try {
				const response = await fetch(imageUrl(link), { method: 'HEAD' });
				return { link, ok: response.ok };
			} catch {
				return { link, ok: false };
			}
		})
	);

	const missing = results.filter((r) => !r.ok);
	if (missing.length > 0) {
		log.error(`Missing ${missing.length}/${links.length} images: ${missing.map((m) => m.link).join(', ')}`);
	} else {
		log.log(`All ${links.length} images present on server`);
	}
}
