import { ObjectStringFilter, ObjectDateFilter, ObjectTagFilter, ObjectStateFilter } from '.'

export type FlowRunFilter = {
  object: 'flow_run',
} & Partial<(FlowRunStringFilter | FlowRunDateFilter | FlowRunTagFilter | FlowRunStateFilter)>

export type FlowRunStringFilter = {
  object: 'flow_run',
  property: 'name',
} & Partial<ObjectStringFilter>

export type FlowRunDateFilter = {
  object: 'flow_run',
  property: 'start_date' | 'end_date',
} & Partial<ObjectDateFilter>

export type FlowRunTagFilter = {
  object: 'flow_run',
  property: 'tag',
} & Partial<ObjectTagFilter>

export type FlowRunStateFilter = {
  object: 'flow_run',
  property: 'state',
} & Partial<ObjectStateFilter>