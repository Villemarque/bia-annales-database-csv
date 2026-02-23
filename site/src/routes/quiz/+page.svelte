<script lang="ts">
	import { onMount } from 'svelte';
	import type { OngoingSession, Qid } from '$lib/types';
	import QuizSession from '../../components/QuizSession.svelte';
	import { ongoingSession } from '$lib/stores/session';
	import { goto } from '$app/navigation';

	let session = $state($ongoingSession);
</script>

{#if session}
	<QuizSession />
{:else}
	<p>Nothing to see!</p>
{/if}

