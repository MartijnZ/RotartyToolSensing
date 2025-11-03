<h1>Welcome to SvelteKit</h1>
<p>Visit <a href="https://svelte.dev/docs/kit">svelte.dev/docs/kit</a> to read the documentation</p>
<script lang="ts">
  import { onMount } from 'svelte';
  import { writable } from 'svelte/store';

  const status = writable<'connecting'|'connected'|'error'|'disconnected'>('connecting');
  const speed  = writable<number|null>(null);

  onMount(() => {
    const ENDPOINT = (location.protocol === 'https:' ? 'wss://' : 'ws://') + location.host + '/ws';
    let ws: WebSocket | null = null;

    const connect = () => {
      status.set('connecting');
      ws = new WebSocket(ENDPOINT);
      ws.onopen = () => status.set('connected');
      ws.onclose = () => { status.set('disconnected'); setTimeout(connect, 3000); };
      ws.onerror = () => status.set('error');
      ws.onmessage = (ev) => {
        try {
          const msg = JSON.parse(ev.data);
          const payload = msg.payload && msg.topic === 'speed' ? msg.payload : msg;
          const v = Number(payload.speed_mps);
          if (Number.isFinite(v)) speed.set(v);
        } catch {}
      };
    };
    connect();
  });
</script>

<div class="p-6 font-sans">
  <h1 class="text-2xl font-semibold mb-2">RDC Monitor</h1>

  <div class="flex items-center gap-3 mb-4">
    <span class="h-3 w-3 rounded-full"
      class:bg-amber-500={$status==='connecting'}
      class:bg-emerald-600={$status==='connected'}
      class:bg-rose-600={$status==='error'}
      class:bg-gray-500={$status==='disconnected'}>
    </span>
    <span class="capitalize text-gray-700">{$status}</span>
  </div>

  <div class="text-4xl font-bold tabular-nums">
    {#if $speed === null}
      — rpm
    {:else}
      {($speed).toFixed(2)} <span class="text-gray-500 text-xl">rpm</span>
    {/if}
  </div>
</div>
