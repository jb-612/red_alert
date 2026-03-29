import { useLocaleStore } from '@/store/locale'

export interface Labels {
  // Header
  appTitle: string
  // Sidebar
  dateRange: string
  comparePeriods: string
  comparisonOn: string
  compare: string
  periodB: string
  categories: string
  rockets: string
  uav: string
  infiltration: string
  allClear: string
  earthquake: string
  locationSearch: string
  searchPlaceholder: string
  granularity: string
  day: string
  week: string
  month: string
  // KPI
  totalAlerts: string
  peakDay: string
  mostActive: string
  longestQuiet: string
  uniqueLocations: string
  // Chart titles
  alertTimeline: string
  categoryBreakdown: string
  hourlyHeatmap: string
  topLocations: string
  sleepScore: string
  bestWeekdays: string
  quietStreaks: string
  anomalyDetection: string
  periodComparison: string
  prealertCorrelation: string
  // Map
  heatmap: string
  scatter: string
  resetView: string
  alertDensity: string
  low: string
  high: string
  timelapse: string
  // Playback
  play: string
  pause: string
  loading: string
  // Export
  exportPng: string
  exportCsv: string
  // Drilldown
  israel: string
  drillInto: string
  // General
  alerts: string
  days: string
  noData: string
}

const en: Labels = {
  appTitle: 'Red Alert Analytics',
  dateRange: 'Date Range',
  comparePeriods: 'Compare Periods',
  comparisonOn: 'Comparison On',
  compare: 'Compare',
  periodB: 'Period B',
  categories: 'Categories',
  rockets: 'Rockets',
  uav: 'UAV',
  infiltration: 'Infiltration',
  allClear: 'All Clear',
  earthquake: 'Earthquake',
  locationSearch: 'Location',
  searchPlaceholder: 'Search location...',
  granularity: 'Granularity',
  day: 'day',
  week: 'week',
  month: 'month',
  totalAlerts: 'Total Alerts',
  peakDay: 'Peak Day',
  mostActive: 'Most Active',
  longestQuiet: 'Longest Quiet',
  uniqueLocations: 'Unique Locations',
  alertTimeline: 'Alert Timeline',
  categoryBreakdown: 'Category Breakdown',
  hourlyHeatmap: 'Hourly Heatmap',
  topLocations: 'Top Locations by Alert Count',
  sleepScore: 'Sleep Score (22:00–07:00)',
  bestWeekdays: 'Best Weekdays (Safest First)',
  quietStreaks: 'Quiet Streaks',
  anomalyDetection: 'Anomaly Detection',
  periodComparison: 'Period Comparison',
  prealertCorrelation: 'Pre-alert to Actual Alert Correlation',
  heatmap: 'Heatmap',
  scatter: 'Scatter',
  resetView: 'Reset View',
  alertDensity: 'Alert Density',
  low: 'Low',
  high: 'High',
  timelapse: 'Time-lapse',
  play: 'Play',
  pause: 'Pause',
  loading: 'Loading',
  exportPng: 'Export PNG',
  exportCsv: 'Export CSV',
  israel: 'Israel',
  drillInto: 'Drill into',
  alerts: 'alerts',
  days: 'days',
  noData: 'No data available',
}

const he: Labels = {
  appTitle: 'אנליטיקת התרעות',
  dateRange: 'טווח תאריכים',
  comparePeriods: 'השוואת תקופות',
  comparisonOn: 'השוואה פעילה',
  compare: 'השווה',
  periodB: 'תקופה ב׳',
  categories: 'קטגוריות',
  rockets: 'רקטות',
  uav: 'כלי טיס',
  infiltration: 'חדירה',
  allClear: 'הסתיים',
  earthquake: 'רעידת אדמה',
  locationSearch: 'מיקום',
  searchPlaceholder: 'חפש מיקום...',
  granularity: 'רזולוציה',
  day: 'יום',
  week: 'שבוע',
  month: 'חודש',
  totalAlerts: 'סה״כ התרעות',
  peakDay: 'יום שיא',
  mostActive: 'הכי פעיל',
  longestQuiet: 'שקט ארוך',
  uniqueLocations: 'מיקומים ייחודיים',
  alertTimeline: 'ציר זמן התרעות',
  categoryBreakdown: 'פילוח לפי קטגוריה',
  hourlyHeatmap: 'מפת חום שעתית',
  topLocations: 'מיקומים מובילים לפי התרעות',
  sleepScore: 'ציון שינה (22:00–07:00)',
  bestWeekdays: 'ימים בטוחים (מהטוב לרע)',
  quietStreaks: 'רצפי שקט',
  anomalyDetection: 'זיהוי חריגות',
  periodComparison: 'השוואת תקופות',
  prealertCorrelation: 'מתאם הנחיה מקדימה להתרעה',
  heatmap: 'מפת חום',
  scatter: 'נקודות',
  resetView: 'איפוס תצוגה',
  alertDensity: 'צפיפות התרעות',
  low: 'נמוך',
  high: 'גבוה',
  timelapse: 'מעבר זמן',
  play: 'נגן',
  pause: 'עצור',
  loading: 'טוען',
  exportPng: 'ייצוא PNG',
  exportCsv: 'ייצוא CSV',
  israel: 'ישראל',
  drillInto: 'חפור ל',
  alerts: 'התרעות',
  days: 'ימים',
  noData: 'אין נתונים',
}

const labelSets: Record<string, Labels> = { en, he }

export function useLabels(): Labels {
  const lang = useLocaleStore((s) => s.lang)
  return labelSets[lang] ?? en
}
