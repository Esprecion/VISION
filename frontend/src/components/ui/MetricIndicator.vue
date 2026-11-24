<template>
	<span
		v-if="level"
		class="metric-indicator"
		:class="`metric-indicator--${level}`"
		:title="rule"
		:aria-label="ariaLabel"
	>
		<span class="metric-indicator__dot" aria-hidden="true"></span>
		<span class="metric-indicator__text">{{ level }}</span>
	</span>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
	level: { type: String, default: '' },
	rule: { type: String, default: '' },
})

const ariaLabel = computed(() => (props.rule ? `${props.level} — ${props.rule}` : props.level))
</script>

<style scoped>
.metric-indicator {
	display: inline-flex;
	align-items: center;
	gap: var(--space-1);
	font-size: var(--fs-xs);
	text-transform: capitalize;
}
.metric-indicator__dot {
	width: 8px;
	height: 8px;
	border-radius: var(--radius-full);
	background: currentColor;
}
.metric-indicator--green {
	color: var(--color-emerald-600);
}
.metric-indicator--amber {
	color: var(--color-amber-600);
}
.metric-indicator--red {
	color: var(--color-red-600);
}
</style>
