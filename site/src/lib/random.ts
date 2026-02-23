import type { IdPrefix } from '$lib/types';

// not crypographically secure
export const unsafeRandomId = ({ prefix }: { prefix: IdPrefix }): string => {
    const alphabet = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
    const idLength = 8;
    let id = '';
    for (let i = 0; i < idLength; i++) {
        id += alphabet[Math.floor(Math.random() * alphabet.length)];
    }
    return `${prefix}_${id}`;
}