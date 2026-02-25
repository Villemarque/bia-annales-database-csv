<script lang="ts">
	import { onMount } from 'svelte';
	import type { OngoingSession, Qid } from '$lib/types';
	import QuizSession from '../../components/QuizSession.svelte';
	import { sessionState, sessionDuration, durationByQ } from '$lib/stores/session.svelte';
	import { goto } from '$app/navigation';

	if (!sessionState.current) {
		goto('/');
	}
</script>

{#if sessionState.current && sessionDuration.current}
	<QuizSession
		bind:session={sessionState.current}
		bind:sessionDuration={sessionDuration.current}
		bind:durationByQ={durationByQ.current} />
{/if}
