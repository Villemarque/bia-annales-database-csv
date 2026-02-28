import { goto } from '$app/navigation';
import { resolve } from '$app/paths';
import type { ResolvedPathname } from '$app/types';

export function go(path: ResolvedPathname, options?: Parameters<typeof goto>[1]) {
	// @ts-expect-error Typescript can't understand custom path resolve logic
	return goto(resolve(path), options);
}
