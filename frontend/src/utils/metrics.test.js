import assert from 'node:assert/strict'
import test from 'node:test'

import { HIDDEN_METRICS, isMetricVisible, ragLevel, ruleText } from './metrics.js'

const boundaryCases = [
	['productTypePerformance', 100000, 25000, 24999.99],
	['geographicDistribution', 100000, 25000, 24999.99],
	['dealsPerStage', 5, 1, 0],
	['openDealValue', 500000, 100000, 99999.99],
	['draftContracts', 3, 1, 0],
	['finalizedContracts', 5, 1, 0],
	['onTimeDeliveryRate', 90, 70, 69.99],
	['averageProjectCycleTime', 30, 60, 60.01],
	['activeClientCount', 10, 5, 4],
	['toolApiCostTrend', 50000, 100000, 100000.01],
	['revenuePerClient', 100000, 50000, 49999.99],
	['totalRevenueByPeriod', 250000, 100000, 99999.99],
	['accountsReceivableAging', 0, 30, 30.01],
	['netBurnRate', 0, 50000, 50000.01],
	['projectProfitabilityMargin', 20, 0, -0.01],
	['expenseByCategory', 50000, 100000, 100000.01],
]

test('RAG rules classify green, amber and red boundaries', () => {
	for (const [key, green, amber, red] of boundaryCases) {
		assert.equal(ragLevel(key, green), 'green', `${key} green`)
		assert.equal(ragLevel(key, amber), 'amber', `${key} amber`)
		assert.equal(ragLevel(key, red), 'red', `${key} red`)
	}
})

test('RAG rules handle missing data and errors', () => {
	assert.equal(ragLevel('onTimeDeliveryRate', null, { error: true }), 'red')
	assert.equal(ragLevel('onTimeDeliveryRate', null, { empty: true }), 'amber')
	assert.equal(ragLevel('onTimeDeliveryRate', null), 'red')
	assert.equal(ragLevel('unknown', 100), null)
	assert.equal(ragLevel('revenuePerClient', '₱100,000'), 'green')
})

test('MVP metric visibility keeps hidden keys but hides them from screens', () => {
	assert.equal(HIDDEN_METRICS.size, 4)
	assert.equal(isMetricVisible('conversionRate'), false)
	assert.equal(isMetricVisible('clientTenure'), false)
	assert.equal(isMetricVisible('onTimeDeliveryRate'), true)
})

test('rule text explains the approved colours', () => {
	assert.equal(ruleText('onTimeDeliveryRate'), 'Green at least 90%, amber at least 70%')
	assert.equal(ruleText('averageProjectCycleTime'), 'Green at most 30 days, amber at most 60 days')
})
