export const metricGroups = [
  {
    id: 'activity',
    sequence: '01',
    label: 'Engineering Activity',
    metricIds: ['prsOpened'],
  },
  {
    id: 'collaboration',
    sequence: '02',
    label: 'Review & Collaboration',
    metricIds: [
      'medianFirstReviewHours',
      'meanPreReviewHours',
      'meanPostReviewHours',
      'preReviewTimeSharePct',
      'mergedPRReviewCoveragePct',
      'uniqueExternalReviewers',
    ],
  },
  {
    id: 'delivery',
    sequence: '03',
    label: 'Delivery & Resolution',
    metricIds: [
      'prsMerged',
      'prsClosed',
      'prsClosedWithoutMerge',
      'medianMergeHours',
      'p90MergeHours',
    ],
  },
  {
    id: 'code-change',
    sequence: '04',
    label: 'Code Change Characteristics',
    metricIds: [
      'medianLinesChanged',
      'medianFilesChanged',
    ],
  },
]
