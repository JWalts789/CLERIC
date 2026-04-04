<script lang="ts">
  interface Props {
    data: Record<string, any>;
    overallGrade: string;
  }

  let { data, overallGrade }: Props = $props();

  let dimensions = $derived.by(() => {
    // Handle array format (already structured)
    if (Array.isArray(data?.dimensions)) return data.dimensions;
    if (Array.isArray(data?.scores)) return data.scores;
    if (Array.isArray(data?.criteria)) return data.criteria;

    // Handle dict format from evaluator: {"source_diversity": 0.72, ...}
    const scores = data?.scores;
    if (scores && typeof scores === 'object' && !Array.isArray(scores)) {
      return Object.entries(scores)
        .filter(([_, v]) => typeof v === 'number')
        .map(([key, value]) => ({
          name: key.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase()),
          score: (value as number) * 100,
        }));
    }
    return [];
  });
  let recommendations = $derived(data?.recommendations ?? data?.improvements ?? []);

  function gradeColor(grade: string): string {
    const g = grade?.toUpperCase() || '';
    if (g.startsWith('A')) return '#22c55e';
    if (g.startsWith('B')) return '#4ade80';
    if (g.startsWith('C')) return '#eab308';
    if (g.startsWith('D')) return '#f97316';
    return '#ef4444';
  }

  function scoreBarColor(score: number): string {
    if (score >= 80) return '#22c55e';
    if (score >= 60) return '#eab308';
    return '#ef4444';
  }

  let color = $derived(gradeColor(overallGrade));
</script>

<div class="evaluation-scorecard">
  <div class="section-header">
    <span class="section-icon" style="background: rgba(221, 107, 32, 0.15); color: #dd6b20;">
      {'\u{1F4CA}'}
    </span>
    <div>
      <h2>Evaluation Scorecard</h2>
      <p class="section-desc">Quality assessment of the research pipeline output</p>
    </div>
  </div>

  <div class="scorecard-content">
    <!-- Grade Display -->
    <div class="grade-display">
      <div class="grade-circle" style="--grade-color: {color};">
        <span class="grade-letter">{overallGrade || '?'}</span>
      </div>
      <span class="grade-label">Overall Grade</span>
    </div>

    <!-- Dimension Scores -->
    {#if dimensions.length > 0}
      <div class="dimensions">
        {#each dimensions as dim, i}
          {@const score = dim.score ?? dim.value ?? 0}
          {@const barColor = scoreBarColor(score)}
          <div class="dimension-row" style="animation-delay: {i * 100}ms;">
            <div class="dim-header">
              <span class="dim-name">{dim.name || dim.dimension || dim.criterion || `Dimension ${i + 1}`}</span>
              <span class="dim-score" style="color: {barColor};">{Math.round(score)}%</span>
            </div>
            <div class="dim-bar-track">
              <div
                class="dim-bar-fill"
                style="width: {score}%; background: {barColor};"
              ></div>
            </div>
            {#if dim.feedback}
              <p class="dim-feedback">{dim.feedback}</p>
            {/if}
          </div>
        {/each}
      </div>
    {/if}

    <!-- Recommendations -->
    {#if recommendations.length > 0}
      <div class="recommendations">
        <h3>Improvement Recommendations</h3>
        <ul>
          {#each recommendations as rec}
            <li>
              {#if typeof rec === 'string'}
                {rec}
              {:else}
                <strong>{rec.area?.replaceAll('_', ' ').toUpperCase() ?? ''}</strong>
                {#if rec.issue}: {rec.issue}{/if}
                {#if rec.suggestion}<br/><em>Suggestion: {rec.suggestion}</em>{/if}
              {/if}
            </li>
          {/each}
        </ul>
      </div>
    {/if}
  </div>
</div>

<style>
  .evaluation-scorecard {
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

  .scorecard-content {
    display: flex;
    flex-direction: column;
    gap: 2rem;
  }

  /* Grade Circle */
  .grade-display {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 8px;
  }

  .grade-circle {
    width: 100px;
    height: 100px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    background: color-mix(in srgb, var(--grade-color) 15%, var(--bg-secondary));
    border: 3px solid var(--grade-color);
    box-shadow: 0 0 24px color-mix(in srgb, var(--grade-color) 30%, transparent);
    animation: fadeInScale 500ms ease-out;
  }

  .grade-letter {
    font-size: 3rem;
    font-weight: 800;
    font-family: var(--font-mono);
    color: var(--grade-color);
    line-height: 1;
  }

  .grade-label {
    font-size: 0.8rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    color: var(--text-dim);
  }

  /* Dimensions */
  .dimensions {
    display: flex;
    flex-direction: column;
    gap: 1rem;
  }

  .dimension-row {
    animation: slideInRight 300ms ease-out backwards;
  }

  .dim-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 6px;
  }

  .dim-name {
    font-size: 0.875rem;
    font-weight: 600;
    color: var(--text-secondary);
  }

  .dim-score {
    font-size: 0.875rem;
    font-weight: 700;
    font-family: var(--font-mono);
  }

  .dim-bar-track {
    height: 8px;
    background: var(--bg-tertiary);
    border-radius: 4px;
    overflow: hidden;
  }

  .dim-bar-fill {
    height: 100%;
    border-radius: 4px;
    transition: width 1.2s cubic-bezier(0.4, 0, 0.2, 1);
  }

  .dim-feedback {
    font-size: 0.8rem;
    color: var(--text-muted);
    margin: 4px 0 0 0;
    line-height: 1.5;
  }

  /* Recommendations */
  .recommendations h3 {
    font-size: 0.85rem;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    color: var(--text-dim);
    margin-bottom: 0.75rem;
    font-weight: 700;
  }

  .recommendations ul {
    list-style: none;
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }

  .recommendations li {
    position: relative;
    padding-left: 20px;
    font-size: 0.9rem;
    color: var(--text-secondary);
    line-height: 1.6;
  }

  .recommendations li::before {
    content: '\u25B8';
    position: absolute;
    left: 4px;
    color: var(--color-evaluation, #dd6b20);
  }
</style>
