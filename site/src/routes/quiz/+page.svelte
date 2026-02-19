<script lang="ts">
	import { onMount } from 'svelte';
	import type { OngoingSession, Qid } from '$lib/types';
	import QuizSession from '../../components/QuizSession.svelte';
	import { ongoingSession } from '$lib/stores/session';
	import { goto } from '$app/navigation';

	let session = $state<OngoingSession | undefined>(undefined);

	onMount(() => {
		const unsub = ongoingSession.subscribe((s) => {
			if (!s) {
				goto('/');
			} else {
				session = s;
			}
		});

		return unsub;
	});
</script>

{#if session}
	<QuizSession {session} />
{/if}
