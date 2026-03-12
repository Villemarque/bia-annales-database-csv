<script lang="ts">
	import { onMount } from 'svelte';
	import type { OngoingSession, Qid } from '$lib/types';
	import QuizSession from '../../components/QuizSession.svelte';
	import { sessionState, sessionDuration, durationByQ, saveSession, cancelSession } from '$lib/stores/session.svelte';
	import { go } from '$lib/go.svelte';
	import { questions } from '$lib/stores/questions';

	if (sessionState.current === null) {
		go('/');
	}
</script>

{#if sessionState.current}
	<QuizSession
		bind:session={sessionState.current}
		bind:sessionDuration={sessionDuration.current}
		bind:durationByQ={durationByQ.current}
		onSessionFinish={() => saveSession($questions)}
		onSessionCancel={cancelSession} />
{:else}
	<p>No ongoing session found. This a bug. Report to the developer</p>
{/if}
