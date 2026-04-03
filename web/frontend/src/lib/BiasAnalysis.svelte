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

  let gaugeRotation = $derived((biasScore / 10) * 180 - 90);
  let color = $derived(scoreColor(biasScore));
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
      <div class="gauge">
        <div class="gauge-bg"></div>
        <div class="gauge-fill" style="--rotation: {gaugeRotation}deg; --gauge-color: {color};"></div>
        <div class="gauge-center">
          <span class="gauge-value" style="color: {color};">{biasScore}</span>
          <span class="gauge-label">{scoreLabel(biasScore)}</span>
        </div>
        <span class="gauge-min">0</span>
        <span class="gauge-max">10</span>
      </div>
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

  .gauge {
    position: relative;
    width: 200px;
    height: 110px;
    overflow: hidden;
  }

  .gauge-bg {
    position: absolute;
    width: 200px;
    height: 200px;
    border-radius: 50%;
    border: 16px solid var(--bg-tertiary);
    clip-path: polygon(0 0, 100% 0, 100% 50%, 0 50%);
  }

  .gauge-fill {
    position: absolute;
    width: 200px;
    height: 200px;
    border-radius: 50%;
    border: 16px solid transparent;
    border-top-color: var(--gauge-color);
    border-right-color: var(--gauge-color);
    clip-path: polygon(0 0, 100% 0, 100% 50%, 0 50%);
    transform: rotate(var(--rotation));
    transition: transform 1s cubic-bezier(0.4, 0, 0.2, 1);
  }

  .gauge-center {
    position: absolute;
    bottom: 0;
    left: 50%;
    transform: translateX(-50%);
    text-align: center;
  }

  .gauge-value {
    display: block;
    font-size: 2.5rem;
    font-weight: 800;
    font-family: var(--font-mono);
    line-height: 1;
  }

  .gauge-label {
    font-size: 0.75rem;
    color: var(--text-muted);
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.04em;
  }

  .gauge-min, .gauge-max {
    position: absolute;
    bottom: 0;
    font-size: 0.7rem;
    color: var(--text-dim);
    font-family: var(--font-mono);
  }

  .gauge-min { left: 12px; }
  .gauge-max { right: 12px; }

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
