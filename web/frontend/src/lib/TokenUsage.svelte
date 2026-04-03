<script lang="ts">
  import { STAGES } from './types';

  interface Props {
    totalTokens: { input: number; output: number };
    durationSeconds: number;
    stageTokens: Record<string, { input: number; output: number }>;
  }

  let { totalTokens, durationSeconds, stageTokens }: Props = $props();

  // Haiku pricing
  const INPUT_COST_PER_M = 0.80;
  const OUTPUT_COST_PER_M = 4.00;

  let totalInput = $derived(totalTokens?.input ?? 0);
  let totalOutput = $derived(totalTokens?.output ?? 0);
  let totalAll = $derived(totalInput + totalOutput);

  let estimatedCost = $derived(
    (totalInput / 1_000_000) * INPUT_COST_PER_M +
    (totalOutput / 1_000_000) * OUTPUT_COST_PER_M
  );

  let formattedDuration = $derived(() => {
    const s = Math.round(durationSeconds || 0);
    if (s < 60) return `${s}s`;
    const m = Math.floor(s / 60);
    const rem = s % 60;
    return `${m}m ${rem}s`;
  });

  function formatNumber(n: number): string {
    if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(2)}M`;
    if (n >= 1_000) return `${(n / 1_000).toFixed(1)}k`;
    return n.toString();
  }

  // Stacked bar data
  let stageBarData = $derived(
    STAGES.map(stage => {
      const t = stageTokens[stage.key];
      const total = t ? t.input + t.output : 0;
      return {
        key: stage.key,
        label: stage.label,
        color: stage.color,
        tokens: total,
        pct: totalAll > 0 ? (total / totalAll) * 100 : 0,
      };
    }).filter(d => d.tokens > 0)
  );
</script>

<div class="token-usage">
  <div class="usage-stats">
    <div class="stat">
      <span class="stat-value">{formatNumber(totalAll)}</span>
      <span class="stat-label">Total Tokens</span>
    </div>
    <div class="stat-divider"></div>
    <div class="stat">
      <span class="stat-value">${estimatedCost.toFixed(4)}</span>
      <span class="stat-label">Est. Cost</span>
    </div>
    <div class="stat-divider"></div>
    <div class="stat">
      <span class="stat-value">{formattedDuration()}</span>
      <span class="stat-label">Duration</span>
    </div>
    <div class="stat-divider"></div>
    <div class="stat">
      <span class="stat-value">{formatNumber(totalInput)}</span>
      <span class="stat-label">Input</span>
    </div>
    <div class="stat-divider"></div>
    <div class="stat">
      <span class="stat-value">{formatNumber(totalOutput)}</span>
      <span class="stat-label">Output</span>
    </div>
  </div>

  {#if stageBarData.length > 0}
    <div class="stacked-bar">
      {#each stageBarData as seg}
        <div
          class="bar-segment"
          style="width: {seg.pct}%; background: {seg.color};"
          title="{seg.label}: {formatNumber(seg.tokens)} tokens ({seg.pct.toFixed(1)}%)"
        ></div>
      {/each}
    </div>
    <div class="bar-legend">
      {#each stageBarData as seg}
        <div class="legend-item">
          <span class="legend-dot" style="background: {seg.color};"></span>
          <span class="legend-label">{seg.label}</span>
          <span class="legend-value">{formatNumber(seg.tokens)}</span>
        </div>
      {/each}
    </div>
  {/if}
</div>

<style>
  .token-usage {
    padding: 1rem 1.25rem;
    background: var(--bg-secondary);
    border: 1px solid var(--border-primary);
    border-radius: var(--radius-md);
    animation: fadeIn 300ms ease-out;
  }

  .usage-stats {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 1rem;
    flex-wrap: wrap;
  }

  .stat {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 2px;
    min-width: 70px;
  }

  .stat-value {
    font-size: 1.05rem;
    font-weight: 700;
    font-family: var(--font-mono);
    color: var(--text-primary);
  }

  .stat-label {
    font-size: 0.65rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    color: var(--text-dim);
  }

  .stat-divider {
    width: 1px;
    height: 28px;
    background: var(--border-primary);
  }

  /* Stacked Bar */
  .stacked-bar {
    display: flex;
    height: 8px;
    border-radius: 4px;
    overflow: hidden;
    margin-top: 1rem;
    gap: 1px;
  }

  .bar-segment {
    transition: width 1s cubic-bezier(0.4, 0, 0.2, 1);
    min-width: 2px;
  }

  .bar-legend {
    display: flex;
    flex-wrap: wrap;
    gap: 8px 16px;
    margin-top: 8px;
    justify-content: center;
  }

  .legend-item {
    display: flex;
    align-items: center;
    gap: 4px;
  }

  .legend-dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    flex-shrink: 0;
  }

  .legend-label {
    font-size: 0.7rem;
    color: var(--text-muted);
  }

  .legend-value {
    font-size: 0.7rem;
    font-family: var(--font-mono);
    color: var(--text-dim);
  }

  @media (max-width: 600px) {
    .usage-stats {
      gap: 0.5rem;
    }

    .stat-divider {
      display: none;
    }

    .stat {
      min-width: 60px;
    }
  }
</style>
