<template>
	<div class="record-row" :class="{ 'record-row--no-status': !status }">
		<span class="record-row__name">
			<button type="button" class="record-row__link" @click="emit('select')">
				{{ name }}
			</button>
		</span>
		<span class="record-row__detail">{{ detail }}</span>
		<span v-if="status" class="record-row__status">
			<StatusBadge :value="status" />
		</span>
	</div>
</template>

<script setup>
import StatusBadge from './StatusBadge.vue'

defineProps({
	name: { type: [String, Number], default: '' },
	detail: { type: [String, Number], default: '' },
	status: { type: [String, Number], default: '' },
})

const emit = defineEmits(['select'])
</script>

<style scoped>
.record-row {
	display: grid;
	grid-template-columns: minmax(0, 2fr) minmax(0, 1.5fr) minmax(0, 1fr);
	column-gap: var(--space-3);
	align-items: center;
	min-height: 34px;
	padding: var(--space-2) 0;
	border-bottom: 1px solid var(--color-gray-100);
	font-size: var(--fs-sm);
}
.record-row:last-child {
	border-bottom: 0;
}
.record-row > span {
	min-width: 0;
	overflow: hidden;
	text-overflow: ellipsis;
	white-space: nowrap;
	text-align: left;
}
.record-row__link {
	display: block;
	max-width: 100%;
	overflow: hidden;
	padding: 0;
	border: 0;
	background: transparent;
	color: var(--color-gray-900);
	font: inherit;
	font-weight: 600;
	text-align: left;
	text-overflow: ellipsis;
	white-space: nowrap;
	cursor: pointer;
}
.record-row__link:hover {
	text-decoration: underline;
}
.record-row__detail {
	color: var(--color-gray-500);
}
.record-row__status {
	display: flex;
	align-items: center;
}
.record-row--no-status .record-row__detail {
	grid-column: 2 / 4;
}
@media (max-width: 640px) {
	.record-row {
		grid-template-columns: minmax(0, 1fr);
		row-gap: var(--space-1);
	}
	.record-row--no-status .record-row__detail {
		grid-column: auto;
	}
	.record-row > span {
		white-space: normal;
	}
	.record-row__detail,
	.record-row__status {
		padding-left: var(--space-3);
		overflow: visible;
		text-overflow: clip;
	}
}
</style>
