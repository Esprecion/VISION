export const HIDDEN_METRICS = new Set([
	'conversionRate',
	'stageTime',
	'pipelineVelocity',
	'clientTenure',
])

export const METRIC_RULES = {
	productTypePerformance: {
		direction: 'higher',
		green: 100000,
		amber: 25000,
		unit: 'currency',
	},
	geographicDistribution: {
		direction: 'higher',
		green: 100000,
		amber: 25000,
		unit: 'currency',
	},
	dealsPerStage: { direction: 'higher', green: 5, amber: 1, unit: 'count' },
	openDealValue: { direction: 'higher', green: 500000, amber: 100000, unit: 'currency' },
	draftContracts: { direction: 'higher', green: 3, amber: 1, unit: 'count' },
	finalizedContracts: { direction: 'higher', green: 5, amber: 1, unit: 'count' },
	onTimeDeliveryRate: { direction: 'higher', green: 90, amber: 70, unit: 'percent' },
	averageProjectCycleTime: { direction: 'lower', green: 30, amber: 60, unit: 'days' },
	activeClientCount: { direction: 'higher', green: 10, amber: 5, unit: 'count' },
	toolApiCostTrend: { direction: 'lower', green: 50000, amber: 100000, unit: 'currency' },
	revenuePerClient: { direction: 'higher', green: 100000, amber: 50000, unit: 'currency' },
	totalRevenueByPeriod: { direction: 'higher', green: 250000, amber: 100000, unit: 'currency' },
	accountsReceivableAging: { direction: 'lower', green: 0, amber: 30, unit: 'days' },
	netBurnRate: { direction: 'lower', green: 0, amber: 50000, unit: 'currency' },
	projectProfitabilityMargin: { direction: 'higher', green: 20, amber: 0, unit: 'percent' },
	expenseByCategory: { direction: 'lower', green: 50000, amber: 100000, unit: 'currency' },
}

export function isMetricVisible(key) {
	return !HIDDEN_METRICS.has(key)
}

export function ragLevel(key, value, options = {}) {
	if (options.error) return 'red'
	const rule = METRIC_RULES[key]
	if (!rule) return null
	const number = toNumber(value)
	if (number === null) return options.empty ? 'amber' : 'red'
	if (rule.direction === 'lower') {
		if (number <= rule.green) return 'green'
		if (number <= rule.amber) return 'amber'
		return 'red'
	}
	if (number >= rule.green) return 'green'
	if (number >= rule.amber) return 'amber'
	return 'red'
}

export function ruleText(key) {
	const rule = METRIC_RULES[key]
	if (!rule) return ''
	const comparator = rule.direction === 'lower' ? 'at most' : 'at least'
	const green = formatThreshold(rule.green, rule.unit)
	const amber = formatThreshold(rule.amber, rule.unit)
	return `Green ${comparator} ${green}, amber ${comparator} ${amber}`
}

function toNumber(value) {
	if (value === null || value === undefined || value === '') return null
	const text = String(value).replace(/[₱,\s%]/g, '')
	if (!text) return null
	const number = Number(text)
	return Number.isFinite(number) ? number : null
}

function formatThreshold(value, unit) {
	if (unit === 'currency') return `₱${value.toLocaleString('en-PH')}`
	if (unit === 'percent') return `${value}%`
	if (unit === 'days') return `${value} days`
	return String(value)
}
