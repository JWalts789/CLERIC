<script lang="ts">
  interface Props {
    data: Record<string, any>;
  }

  let { data }: Props = $props();

  let biasScore = $derived(data?.bias_score ?? data?.score ?? 5);
  let biases = $derived(data?.detected_biases ?? data?.biases ?? []);
  let reformulations = $derived(data?.neutral_reformulations ?? data?.reformulations ?? []);
  let perspectives = $derived(data?.required_perspectives ?? data?.perspectives ?? []);

  function scoreColor(score: number): string {
    if (score <= 3) return '#22c55e';
    if (score <= 6) return '#eab308';
    return '#ef4444';
  }

  function scoreLabel(score: number): string {
    if (score <= 3) return 'Low Bias';
    if (score <= 6) return 'Moderate Bias';
    return 'High Bias';
  }

  let color = $derived(scoreColor(biasScore));

  // SVG arc gauge: semicircle from left to right
  // Arc radius and circumference for the semicircle
  const R = 80;
  const CIRCUMFERENCE = Math.PI * R; // half circle
  let dashOffset = $derived(CIRCUMFERENCE - (biasScore / 10) * CIRCUMFERENCE);
</script>

<div class="bias-analysis">
  <div class="section-header">
    <span class="section-icon" style="background: rgba(229, 62, 62, 0.15); color: #e53e3e;">
      {'\u{1F6E1}\uFE0F'}
    </span>
    <div>
      <h2>Bias Analysis</h2>
      <p class="section-desc">Detected biases and neutral reformulations</p>
    </div>
  </div>

  <div class="bias-content">
    <!-- Gauge -->
    <div class="gauge-container">
      <svg class="gauge-svg" viewBox="0 0 200 120" width="220" height="132">
        <!-- Background arc -->
        <path
          d="M 20 100 A 80 80 0 0 1 180 100"
          fill="none"
          stroke="var(--bg-tertiary, #1a2235)"
          stroke-width="14"
          stroke-linecap="round"
        />
        <!-- Filled arc -->
        <path
          d="M 20 100 A 80 80 0 0 1 180 100"
          fill="none"
          stroke={color}
          stroke-width="14"
          stroke-linecap="round"
          stroke-dasharray={CIRCUMFERENCE}
          stroke-dashoffset={dashOffset}
          style="transition: stroke-dashoffset 1s cubic-bezier(0.4, 0, 0.2, 1), stroke 0.5s ease;"
        />
        <!-- Score number -->
        <text x="100" y="88" text-anchor="middle" fill={color} font-size="36" font-weight="800" font-family="var(--font-mono, monospace)">{biasScore}</text>
        <!-- Label -->
        <text x="100" y="108" text-anchor="middle" fill="var(--text-dim, #94a3b8)" font-size="10" font-weight="600" letter-spacing="0.05em">{scoreLabel(biasScore).toUpperCase()}</text>
        <!-- Min/Max -->
        <text x="18" y="115" text-anchor="middle" fill="var(--text-dim, #475569)" font-size="9" font-family="var(--font-mono, monospace)">0</text>
        <text x="182" y="115" text-anchor="middle" fill="var(--text-dim, #475569)" font-size="9" font-family="var(--font-mono, monospace)">10</text>
      </svg>
    </div>

    <!-- Detected Biases -->
    {#if biases.length > 0}
      <div class="subsection">
        <h3>Detected Biases</h3>
        <div class="bias-cards">
          {#each biases as bias}
            <div class="bias-card card">
              {#if typeof bias === 'string'}
                <p>{bias}</p>
              {:else}
                <h4>{bias.type || bias.name || 'Bias'}</h4>
                <p>{bias.description || bias.detail || bias.explanation || JSON.stringify(bias)}</p>
              {/if}
            </div>
          {/each}
        </div>
      </div>
    {/if}

    <!-- Reformulations -->
    {#if reformulations.length > 0}
      <div class="subsection">
        <h3>Neutral Reformulations</h3>
        <div class="reformulations">
          {#each reformulations as reform}
            <blockquote class="reformulation">
              {typeof reform === 'string' ? reform : reform.text || reform.reformulation || JSON.stringify(reform)}
            </blockquote>
          {/each}
        </div>
      </div>
    {/if}

    <!-- Required Perspectives -->
    {#if perspectives.length > 0}
      <div class="subsection">
        <h3>Required Perspectives</h3>
        <div class="perspective-tags">
          {#each perspectives as perspective}
            <span class="perspective-tag badge badge-info">
              {typeof perspective === 'string' ? perspective : perspective.name || JSON.stringify(perspective)}
            </span>
          {/each}
        </div>
      </div>
    {/if}
  </div>
</div>

<style>
  .bias-analysis {
    animation: fadeIn 400ms ease-out;
  }

  .section-header {
    display: flex;
    align-items: center;
    gap: 12px;
    margin-bottom: 1.5rem;
  }

  .section-icon {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 40px;
    height: 40px;
    border-radius: var(--radius-sm);
    font-size: 1.2rem;
    flex-shrink: 0;
  }

  .section-header h2 {
    margin-bottom: 2px;
    font-size: 1.25rem;
  }

  .section-desc {
    font-size: 0.85rem;
    color: var(--text-dim);
    margin: 0;
  }

  .bias-content {
    display: flex;
    flex-direction: column;
    gap: 1.5rem;
  }

  /* Gauge */
  .gauge-container {
    display: flex;
    justify-content: center;
    padding: 1rem 0;
  }

  .gauge-svg {
    display: block;
    filter: drop-shadow(0 0 8px rgba(110, 231, 183, 0.1));
  }

  /* Subsections */
  .subsection h3 {
    font-size: 0.9rem;
    text-transform: uppercase;
    letter-spacing: 0.04em;
    color: var(--text-muted);
    margin-bottom: 0.75rem;
    font-weight: 600;
  }

  .bias-cards {
    display: grid;
    gap: 0.75rem;
  }

  .bias-card h4 {
    font-size: 0.95rem;
    margin-bottom: 0.25rem;
    color: var(--color-error);
  }

  .bias-card p {
    font-size: 0.9rem;
    margin: 0;
  }

  .reformulation {
    padding: 0.75rem 1rem;
    border-left: 3px solid var(--accent);
    background: var(--accent-bg);
    border-radius: 0 var(--radius-sm) var(--radius-sm) 0;
    color: var(--text-secondary);
    font-size: 0.9rem;
    font-style: italic;
    margin-bottom: 0.5rem;
  }

  .perspective-tags {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
  }

  .perspective-tag {
    font-size: 0.8rem;
  }
</style>
