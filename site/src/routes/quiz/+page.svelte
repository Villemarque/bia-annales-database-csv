<script lang="ts">
	import { onMount } from 'svelte';
	import type { OngoingSession, Qid } from '$lib/types';
	import QuizSession from '../../components/QuizSession.svelte';
	import { sessionState, sessionDuration, durationByQ, saveSession, cancelSession } from '$lib/stores/session.svelte';
	import { goto } from '$app/navigation';

	if (sessionState.current === undefined) {
		goto('/');
	}
</script>

{#if sessionState.current}
	<QuizSession
		bind:session={sessionState.current}
		bind:sessionDuration={sessionDuration.current}
		bind:durationByQ={durationByQ.current}
		onSessionFinish={saveSession}
		onSessionCancel={cancelSession} />
{:else}
	<p>No ongoing session found. This a bug. Report to the developer</p>
{/if}
