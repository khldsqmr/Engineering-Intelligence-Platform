interface GlossaryExample {
  example: string
  calculation?: string
  note?: string
}

export const glossaryExamples: Record<string, GlossaryExample> = {

  // Engineering Terminology

  'Pull Request (PR)': {
    example: 'A developer fixes a login issue and submits the code change for review before merging it.',
  },

  'Merge Duration': {
    example: 'A PR is created on Monday at 9 AM and merged on Tuesday at 9 AM.',
    calculation: 'Merge time − Creation time = 24 hours',
    note: 'Elapsed time is not the same as active engineering effort.',
  },

  'External Review': {
    example: 'Developer A creates a PR. Developer B submits a qualifying review. Developer A reviewing their own PR does not count as an external review.',
  },

  'Pre-Review Duration': {
    example: 'A PR is created at 9 AM and receives its first qualifying external review at 3 PM.',
    calculation: '3 PM − 9 AM = 6 hours',
  },

  'Post-Review Duration': {
    example: 'A PR receives its first external review at 10 AM and is merged at 4 PM.',
    calculation: '4 PM − 10 AM = 6 hours',
  },

  'Review Coverage': {
    example: 'Of 100 observed merged PRs, 85 received a qualifying external review.',
    calculation: '85 ÷ 100 × 100 = 85%',
  },

  // Analytical Methodology

  'Reporting Period': {
    example: 'The reporting window starts November 20 at midnight UTC and ends November 27 at midnight UTC. Events on November 27 are excluded.',
  },

  'Week-over-Week (WoW)': {
    example: 'Merged PRs increased from 200 in the previous week to 250 in the current week.',
    calculation: '(250 − 200) ÷ 200 × 100 = +25%',
  },

  'Historical Benchmark': {
    example: 'The two preceding weeks recorded 200 and 300 merged PRs. Their average becomes the historical benchmark.',
    calculation: '(200 + 300) ÷ 2 = 250 PRs',
    note: 'The current EIP configuration uses two preceding periods. A benchmark is not a target.',
  },

  'Benchmark Variance': {
    example: 'The current week recorded 300 merged PRs against a historical benchmark of 250.',
    calculation: '(300 − 250) ÷ 250 × 100 = +20%',
  },

  'Percentage Point (pp)': {
    example: 'External review coverage declined from 90% to 80%.',
    calculation: '80% − 90% = −10 percentage points',
    note: 'The relative percentage change would instead be approximately −11.11%.',
  },

  'Median': {
    example: 'Five PRs took 2, 4, 6, 8 and 50 hours to merge.',
    calculation: 'Median = 6 hours',
    note: 'The middle observation is less affected by the unusually long merge duration.',
  },

  '90th Percentile (P90)': {
    example: 'If the P90 merge duration is 48 hours, approximately 90% of observed merge durations are at or below 48 hours.',
    note: 'P90 helps describe the slower end of a distribution.',
  },

  'Weekly Aggregation': {
    example: 'Monday has one PR taking 10 hours. Tuesday has three PRs taking 2, 4 and 6 hours. The combined mean uses all four PRs.',
    calculation: '(10 + 2 + 4 + 6) ÷ 4 = 5.5 hours',
    note: 'Weekly metrics are calculated from the underlying cohort, not by blindly averaging daily results.',
  },

  'Missing Values': {
    example: 'A historical week falls outside the review enrichment window. Its review duration is displayed as N/A rather than zero hours.',
  },

  // Data Architecture & Quality

  'Control Layer': {
    example: 'The metric registry specifies that Median Merge Duration uses hours, the merged PR cohort and median aggregation.',
  },

  'Bronze Layer': {
    example: 'The original GitHub API response for PR number 101 is stored as a raw observation associated with an ingestion run.',
  },

  'Silver Layer': {
    example: 'Duplicate PR observations are reconciled, timestamps standardized and invalid records excluded.',
  },

  'Gold Layer': {
    example: 'Validated pull request records are used to calculate weekly merge duration, review coverage and historical benchmarks.',
  },

  'Enrichment': {
    example: 'Basic PR records provide creation and merge dates. Additional detail and review requests provide code-change and collaboration information.',
  },

  'Source Coverage': {
    example: 'An ingestion retrieves thousands of PR records using bounded pagination. Coverage remains estimated because exhaustive retrieval is not guaranteed.',
  },

  'Enrichment Coverage': {
    example: 'The required review records are successfully retrieved for 90 of 100 eligible merged PRs.',
    calculation: '90 ÷ 100 × 100 = 90%',
    note: 'Complete enrichment does not guarantee complete repository coverage.',
  },

  'Metric Registry': {
    example: 'Both the dashboard and AI context use the same governed definition of Median Merge Duration.',
  },

  // Intelligence Framework

  'Context Engineering': {
    example: 'Before generating a weekly narrative, EIP supplies reporting dates, metric definitions, analytical facts, metric relationships and quality limitations.',
  },

  'Semantic Context': {
    example: 'The model receives the definition of merge duration, its measurement unit and the applicable PR cohort.',
  },

  'Analytical Context': {
    example: 'The model receives current and previous merge durations, their change, historical benchmark and evidence identifier.',
  },

  'Relational Context': {
    example: 'Pre-review and post-review durations describe different stages of the reviewed PR lifecycle.',
    note: 'Relationships between metrics do not establish causal relationships.',
  },

  'Evidence Grounding': {
    example: 'An AI observation about increasing merge duration cites the evidence reference associated with Median Merge Duration.',
  },

  'Root-Cause Hypothesis': {
    example: 'Longer pre-review durations may suggest delays before the first review. Further investigation is needed to distinguish reviewer waiting from author preparation.',
  },

  'Historical Intelligence': {
    example: 'An eligible approved narrative from an earlier week is retrieved to provide context for a new weekly narrative.',
    note: 'This describes the intended retrieval behavior, not a guarantee that eligible prior intelligence exists.',
  },

  'Persistent Cache': {
    example: 'A second request for the same compatible approved narrative returns the saved result instead of invoking the model again.',
  },

  // AI Evaluation & Governance

  'Deterministic Validation': {
    example: 'A model cites a metric as increasing when the corresponding analytical evidence shows a decrease. Validation rejects the inconsistent reference.',
  },

  'LLM Evaluation': {
    example: 'An evaluator checks whether a generated hypothesis is supported by the supplied evidence and appropriately expresses uncertainty.',
  },

  'AI Quality Score': {
    example: 'A generated response receives strong grounding and relevance scores but weaker counter-evidence and reasoning scores.',
    note: 'A high evaluation score does not guarantee factual correctness.',
  },

  'Evidence Confidence': {
    example: 'A hypothesis references several metrics, but confidence remains limited because source coverage is estimated and no counter-evidence was cited.',
    note: 'This score is a heuristic, not a probability that the hypothesis is true.',
  },

  'Auto-Approval': {
    example: 'A generated narrative passes deterministic checks and satisfies the configured model-based quality thresholds.',
    note: 'Automated approval is not equivalent to human verification.',
  },

  'Generation Archive': {
    example: 'A generated narrative fails validation. The attempted response and rejection reason are retained in the archive rather than published.',
  },

  'Counter-Evidence': {
    example: 'Merge duration increases while median change size decreases. This challenges an explanation based solely on larger code changes.',
  },

  'AI Limitations': {
    example: 'A model incorrectly describes an unchanged metric as decreasing, and its evaluator fails to detect the discrepancy.',
    note: 'Important conclusions should be checked against the underlying analytical facts.',
  },

  // Information Classification

  'Fact': {
    example: 'The deterministic analytical layer reports 200 observed merged pull requests for a reporting period.',
  },

  'Derived': {
    example: 'The platform calculates a 25% week-over-week increase from 200 to 250 merged PRs.',
    calculation: '(250 − 200) ÷ 200 × 100 = 25%',
  },

  'AI Generated': {
    example: 'The model recommends investigating reviewer participation as a possible contributor to longer merge times.',
  },

  'Forecast': {
    example: 'A hypothetical forecasting model estimates that 240 PRs will merge next week.',
    note: 'Forecasting is not currently implemented in EIP.',
  },

  'Target': {
    example: 'An engineering team sets a desired median merge duration of less than 48 hours.',
    note: 'This is an illustrative target, not an actual configured EIP objective.',
  },

}
