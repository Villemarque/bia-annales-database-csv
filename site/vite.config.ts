import { execFileSync } from 'node:child_process';
import { sveltekit } from '@sveltejs/kit/vite';
import { defineConfig } from 'vite';

function git(args: string[]): string {
	return execFileSync('git', args).toString().trim();
}

function getGitInfo(): { commit: string; modified: boolean } {
	const cache = globalThis as { __gitInfo?: { commit: string; modified: boolean } };
	if (cache.__gitInfo) return cache.__gitInfo;
	try {
		const commit = git(['rev-parse', '--short', 'HEAD']);
		const modified = git(['status', '--porcelain', '--untracked-files=no']) !== '';
		cache.__gitInfo = { commit, modified };
	} catch {
		cache.__gitInfo = { commit: 'dev', modified: false };
	}
	return cache.__gitInfo;
}

const { commit, modified } = getGitInfo();

export default defineConfig({
	plugins: [sveltekit()],
	define: {
		__COMMIT__: JSON.stringify(commit),
		__COMMIT_MODIFIED__: JSON.stringify(modified)
	},
	server: {
		// host: true
	}
});
