import datetime
from typing import List, Optional
from uuid import UUID

import sqlalchemy as sa
from pydantic import Field, conint, root_validator

import prefect
from prefect.orion import schemas
from prefect.orion.models import orm
from prefect.orion.utilities.database import json_has_all_keys
from prefect.orion.utilities.schemas import PrefectBaseModel
from prefect.orion.utilities.enum import AutoEnum


class PrefectFilterBaseModel(PrefectBaseModel):
    """Base model for Prefect filters"""

    def as_sql_filter(self):
        """Generate SQL filter from provided filter parameters. If no filters parameters are available, return a TRUE filter."""
        filters = self._get_filter_list()
        return sa.and_(*filters) if filters else sa.and_(True)

    def _get_filter_list(self):
        """Return a list of boolean filter statements based on filter parameters"""
        raise NotImplementedError("_get_filter_list must be implemented")


class FlowFilterId(PrefectFilterBaseModel):
    any_: List[UUID] = Field(None, description="A list of flow ids to include")

    def _get_filter_list(self):
        filters = []
        if self.any_ is not None:
            filters.append(orm.Flow.id.in_(self.any_))
        return filters


class FlowFilterName(PrefectFilterBaseModel):
    any_: List[str] = Field(
        None,
        description="A list of flow names to include",
        example=["my-flow-1", "my-flow-2"],
    )

    def _get_filter_list(self):
        filters = []
        if self.any_ is not None:
            filters.append(orm.Flow.name.in_(self.any_))
        return filters


class FlowFilterTags(PrefectFilterBaseModel):
    all_: List[str] = Field(
        None,
        example=["tag-1", "tag-2"],
        description="A list of tags. Flows will be returned only if their tags are a superset of the list",
    )
    is_null_: bool = Field(None, description="If true, only include flows without tags")

    def _get_filter_list(self):
        filters = []
        if self.all_ is not None:
            filters.append(json_has_all_keys(orm.Flow.tags, self.all_))
        if self.is_null_ is not None:
            filters.append(
                orm.Flow.tags == [] if self.is_null_ else orm.Flow.tags != []
            )
        return filters


class FlowFilter(PrefectFilterBaseModel):
    """Filter for flows. Only flows matching all criteria will be returned"""

    id: Optional[FlowFilterId]
    name: Optional[FlowFilterName]
    tags: Optional[FlowFilterTags]

    def _get_filter_list(self) -> List:
        filters = []

        if self.id is not None:
            filters.append(self.id.as_sql_filter())
        if self.name is not None:
            filters.append(self.name.as_sql_filter())
        if self.tags is not None:
            filters.append(self.tags.as_sql_filter())

        return filters


class FlowRunFilterId(PrefectFilterBaseModel):
    any_: List[UUID] = Field(None, description="A list of flow run ids to include")
    not_any_: List[UUID] = Field(None, description="A list of flow run ids to exclude")

    def _get_filter_list(self):
        filters = []
        if self.any_ is not None:
            filters.append(orm.FlowRun.id.in_(self.any_))
        if self.not_any_ is not None:
            filters.append(orm.FlowRun.id.not_in(self.not_any_))
        return filters


class FlowRunFilterName(PrefectFilterBaseModel):
    any_: List[str] = Field(
        None,
        description="A list of flow run names to include",
        example=["my-flow-run-1", "my-flow-run-2"],
    )

    def _get_filter_list(self):
        filters = []
        if self.any_ is not None:
            filters.append(orm.FlowRun.name.in_(self.any_))
        return filters


class FlowRunFilterTags(PrefectFilterBaseModel):
    all_: List[str] = Field(
        None,
        example=["tag-1", "tag-2"],
        description="A list of tags. Flow runs will be returned only if their tags are a superset of the list",
    )
    is_null_: bool = Field(
        None, description="If true, only include flow runs without tags"
    )

    def _get_filter_list(self):
        filters = []
        if self.all_ is not None:
            filters.append(json_has_all_keys(orm.FlowRun.tags, self.all_))
        if self.is_null_ is not None:
            filters.append(
                orm.FlowRun.tags == [] if self.is_null_ else orm.FlowRun.tags != []
            )
        return filters


class FlowRunFilterDeploymentId(PrefectFilterBaseModel):
    any_: List[UUID] = Field(
        None, description="A list of flow run deployment ids to include"
    )
    is_null_: bool = Field(
        None, description="If true, only include flow runs without deployment ids"
    )

    def _get_filter_list(self):
        filters = []
        if self.any_ is not None:
            filters.append(orm.FlowRun.deployment_id.in_(self.any_))
        if self.is_null_ is not None:
            filters.append(
                orm.FlowRun.deployment_id == None
                if self.is_null_
                else orm.FlowRun.deployment_id != None
            )
        return filters


class FlowRunFilterStateType(PrefectFilterBaseModel):
    any_: List[schemas.states.StateType] = Field(
        None, description="A list of flow run state types to include"
    )

    def _get_filter_list(self):
        filters = []
        if self.any_ is not None:
            filters.append(orm.FlowRun.state_type.in_(self.any_))
        return filters


class FlowRunFilterStateName(PrefectFilterBaseModel):
    any_: List[str] = Field(
        None, description="A list of flow run state names to include"
    )

    def _get_filter_list(self):
        filters = []
        if self.any_ is not None:
            filters.append(orm.FlowRun.state.has(orm.FlowRunState.name.in_(self.any_)))
        return filters


class FlowRunFilterState(PrefectFilterBaseModel):
    type: Optional[FlowRunFilterStateType]
    name: Optional[FlowRunFilterStateName]

    def _get_filter_list(self):
        filters = []
        if self.type is not None:
            filters.extend(self.type._get_filter_list())
        if self.name is not None:
            filters.extend(self.name._get_filter_list())
        return filters


class FlowRunFilterFlowVersion(PrefectFilterBaseModel):
    any_: List[str] = Field(
        None, description="A list of flow run flow_versions to include"
    )

    def _get_filter_list(self):
        filters = []
        if self.any_ is not None:
            filters.append(orm.FlowRun.flow_version.in_(self.any_))
        return filters


class FlowRunFilterStartTime(PrefectFilterBaseModel):
    before_: datetime.datetime = Field(
        None, description="Only include flow runs starting at or before this time"
    )
    after_: datetime.datetime = Field(
        None, description="Only include flow runs starting at or after this time"
    )
    is_null_: bool = Field(
        None, description="If true, only return flow runs without a start time"
    )

    def _get_filter_list(self):
        filters = []
        if self.before_ is not None:
            filters.append(orm.FlowRun.start_time <= self.before_)
        if self.after_ is not None:
            filters.append(orm.FlowRun.start_time >= self.after_)
        if self.is_null_ is not None:
            filters.append(
                orm.FlowRun.start_time == None
                if self.is_null_
                else orm.FlowRun.start_time != None
            )
        return filters


class FlowRunFilterExpectedStartTime(PrefectFilterBaseModel):
    before_: datetime.datetime = Field(
        None,
        description="Only include flow runs scheduled to start at or before this time",
    )
    after_: datetime.datetime = Field(
        None,
        description="Only include flow runs scheduled to start at or after this time",
    )

    def _get_filter_list(self):
        filters = []
        if self.before_ is not None:
            filters.append(orm.FlowRun.expected_start_time <= self.before_)
        if self.after_ is not None:
            filters.append(orm.FlowRun.expected_start_time >= self.after_)
        return filters


class FlowRunFilterNextScheduledStartTime(PrefectFilterBaseModel):
    before_: datetime.datetime = Field(
        None,
        description="Only include flow runs with a next_scheduled_start_time or before this time",
    )
    after_: datetime.datetime = Field(
        None,
        description="Only include flow runs with a next_scheduled_start_time at or after this time",
    )

    def _get_filter_list(self):
        filters = []
        if self.before_ is not None:
            filters.append(orm.FlowRun.next_scheduled_start_time <= self.before_)
        if self.after_ is not None:
            filters.append(orm.FlowRun.next_scheduled_start_time >= self.after_)
        return filters


class FlowRunFilterParentTaskRunId(PrefectFilterBaseModel):
    any_: List[UUID] = Field(
        None, description="A list of flow run parent_task_run_ids to include"
    )
    is_null_: bool = Field(
        None, description="If true, only include flow runs without parent_task_run_id"
    )

    def _get_filter_list(self):
        filters = []
        if self.any_ is not None:
            filters.append(orm.FlowRun.parent_task_run_id.in_(self.any_))
        if self.is_null_ is not None:
            filters.append(
                orm.FlowRun.parent_task_run_id == None
                if self.is_null_
                else orm.FlowRun.parent_task_run_id != None
            )
        return filters


class FlowRunFilter(PrefectFilterBaseModel):
    """Filter flow runs. Only flow runs matching all criteria will be returned"""

    id: Optional[FlowRunFilterId]
    name: Optional[FlowRunFilterName]
    tags: Optional[FlowRunFilterTags]
    deployment_id: Optional[FlowRunFilterDeploymentId]
    state: Optional[FlowRunFilterState]
    flow_version: Optional[FlowRunFilterFlowVersion]
    start_time: Optional[FlowRunFilterStartTime]
    expected_start_time: Optional[FlowRunFilterExpectedStartTime]
    next_scheduled_start_time: Optional[FlowRunFilterNextScheduledStartTime]
    parent_task_run_id: Optional[FlowRunFilterParentTaskRunId]

    def _get_filter_list(self) -> List:
        filters = []

        if self.id is not None:
            filters.append(self.id.as_sql_filter())
        if self.name is not None:
            filters.append(self.name.as_sql_filter())
        if self.tags is not None:
            filters.append(self.tags.as_sql_filter())
        if self.deployment_id is not None:
            filters.append(self.deployment_id.as_sql_filter())
        if self.flow_version is not None:
            filters.append(self.flow_version.as_sql_filter())
        if self.state is not None:
            filters.append(self.state.as_sql_filter())
        if self.start_time is not None:
            filters.append(self.start_time.as_sql_filter())
        if self.expected_start_time is not None:
            filters.append(self.expected_start_time.as_sql_filter())
        if self.next_scheduled_start_time is not None:
            filters.append(self.next_scheduled_start_time.as_sql_filter())
        if self.parent_task_run_id is not None:
            filters.append(self.parent_task_run_id.as_sql_filter())

        return filters


class TaskRunFilterId(PrefectFilterBaseModel):
    any_: List[UUID] = Field(None, description="A list of task run ids to include")

    def _get_filter_list(self):
        filters = []
        if self.any_ is not None:
            filters.append(orm.TaskRun.id.in_(self.any_))
        return filters


class TaskRunFilterName(PrefectFilterBaseModel):
    any_: List[str] = Field(
        None,
        description="A list of task run names to include",
        example=["my-task-run-1", "my-task-run-2"],
    )

    def _get_filter_list(self):
        filters = []
        if self.any_ is not None:
            filters.append(orm.TaskRun.name.in_(self.any_))
        return filters


class TaskRunFilterTags(PrefectFilterBaseModel):
    all_: List[str] = Field(
        None,
        example=["tag-1", "tag-2"],
        description="A list of tags. Task runs will be returned only if their tags are a superset of the list",
    )
    is_null_: bool = Field(
        None, description="If true, only include task runs without tags"
    )

    def _get_filter_list(self):
        filters = []
        if self.all_ is not None:
            filters.append(json_has_all_keys(orm.TaskRun.tags, self.all_))
        if self.is_null_ is not None:
            filters.append(
                orm.TaskRun.tags == [] if self.is_null_ else orm.TaskRun.tags != []
            )
        return filters


class TaskRunFilterStateType(PrefectFilterBaseModel):
    any_: List[schemas.states.StateType] = Field(
        None, description="A list of task run state types to include"
    )

    def _get_filter_list(self):
        filters = []
        if self.any_ is not None:
            filters.append(orm.TaskRun.state_type.in_(self.any_))
        return filters


class TaskRunFilterStateName(PrefectFilterBaseModel):
    any_: List[str] = Field(
        None, description="A list of task run state names to include"
    )

    def _get_filter_list(self):
        filters = []
        if self.any_ is not None:
            filters.append(orm.TaskRun.state.has(orm.TaskRunState.name.in_(self.any_)))
        return filters


class TaskRunFilterState(PrefectFilterBaseModel):
    type: Optional[TaskRunFilterStateType]
    name: Optional[TaskRunFilterStateName]

    def _get_filter_list(self):
        filters = []
        if self.type is not None:
            filters.extend(self.type._get_filter_list())
        if self.name is not None:
            filters.extend(self.name._get_filter_list())
        return filters


class TaskRunFilterSubFlowRuns(PrefectFilterBaseModel):
    exists_: bool = Field(
        None,
        description="If true, only include task runs that are subflow run parents; if false, exclude parent task runs",
    )

    def _get_filter_list(self):
        filters = []
        if self.exists_ is True:
            filters.append(orm.TaskRun.subflow_run.has())
        elif self.exists_ is False:
            filters.append(sa.not_(orm.TaskRun.subflow_run.has()))
        return filters


class TaskRunFilterStartTime(PrefectFilterBaseModel):
    before_: datetime.datetime = Field(
        None, description="Only include task runs starting at or before this time"
    )
    after_: datetime.datetime = Field(
        None, description="Only include task runs starting at or after this time"
    )
    is_null_: bool = Field(
        None, description="If true, only return task runs without a start time"
    )

    def _get_filter_list(self):
        filters = []
        if self.before_ is not None:
            filters.append(orm.TaskRun.start_time <= self.before_)
        if self.after_ is not None:
            filters.append(orm.TaskRun.start_time >= self.after_)
        if self.is_null_ is not None:
            filters.append(
                orm.TaskRun.start_time == None
                if self.is_null_
                else orm.TaskRun.start_time != None
            )
        return filters


class TaskRunFilter(PrefectFilterBaseModel):
    """Filter task runs. Only task runs matching all criteria will be returned"""

    id: Optional[TaskRunFilterId]
    name: Optional[TaskRunFilterName]
    tags: Optional[TaskRunFilterTags]
    state: Optional[TaskRunFilterState]
    start_time: Optional[TaskRunFilterStartTime]
    subflow_runs: Optional[TaskRunFilterSubFlowRuns]

    def _get_filter_list(self) -> List:
        filters = []

        if self.id is not None:
            filters.append(self.id.as_sql_filter())
        if self.name is not None:
            filters.append(self.name.as_sql_filter())
        if self.tags is not None:
            filters.append(self.tags.as_sql_filter())
        if self.state is not None:
            filters.append(self.state.as_sql_filter())
        if self.start_time is not None:
            filters.append(self.start_time.as_sql_filter())
        if self.subflow_runs is not None:
            filters.append(self.subflow_runs.as_sql_filter())

        return filters


class DeploymentFilterId(PrefectFilterBaseModel):
    any_: List[UUID] = Field(None, description="A list of deployment ids to include")

    def _get_filter_list(self):
        filters = []
        if self.any_ is not None:
            filters.append(orm.Deployment.id.in_(self.any_))
        return filters


class DeploymentFilterName(PrefectFilterBaseModel):
    any_: List[str] = Field(
        None,
        description="A list of deployment names to include",
        example=["my-deployment-1", "my-deployment-2"],
    )

    def _get_filter_list(self):
        filters = []
        if self.any_ is not None:
            filters.append(orm.Deployment.name.in_(self.any_))
        return filters


class DeploymentFilterIsScheduleActive(PrefectFilterBaseModel):
    eq_: bool = Field(
        None,
        description="Only returns where deployment schedule is/is not active",
    )

    def _get_filter_list(self):
        filters = []
        if self.eq_ is not None:
            filters.append(orm.Deployment.is_schedule_active.is_(self.eq_))
        return filters


class DeploymentFilterTags(PrefectFilterBaseModel):
    all_: List[str] = Field(
        None,
        example=["tag-1", "tag-2"],
        description="A list of tags. Deployments will be returned only if their tags are a superset of the list",
    )
    is_null_: bool = Field(
        None, description="If true, only include deployments without tags"
    )

    def _get_filter_list(self):
        filters = []
        if self.all_ is not None:
            filters.append(json_has_all_keys(orm.Deployment.tags, self.all_))
        if self.is_null_ is not None:
            filters.append(
                orm.Deployment.tags == []
                if self.is_null_
                else orm.Deployment.tags != []
            )
        return filters


class DeploymentFilter(PrefectFilterBaseModel):
    """Filter for deployments. Only deployments matching all criteria will be returned"""

    id: Optional[DeploymentFilterId]
    name: Optional[DeploymentFilterName]
    is_schedule_active: Optional[DeploymentFilterIsScheduleActive]
    tags: Optional[DeploymentFilterTags]

    def _get_filter_list(self) -> List:
        filters = []

        if self.id is not None:
            filters.append(self.id.as_sql_filter())
        if self.name is not None:
            filters.append(self.name.as_sql_filter())
        if self.is_schedule_active is not None:
            filters.append(self.is_schedule_active.as_sql_filter())
        if self.tags is not None:
            filters.append(self.tags.as_sql_filter())

        return filters


class BaseFilterCriteria(PrefectBaseModel):
    """Filter criteria for common objects in the system"""

    flow_filter: FlowFilter = Field(default_factory=FlowFilter)
    flow_run_filter: FlowRunFilter = Field(default_factory=FlowRunFilter)
    task_run_filter: TaskRunFilter = Field(default_factory=TaskRunFilter)
    deployment_filter: DeploymentFilter = Field(default_factory=DeploymentFilter)


class FlowFilterCriteria(BaseFilterCriteria):
    """Criteria by which flows can be filtered"""


class FlowRunFilterCriteria(BaseFilterCriteria):
    """Criteria by which flow runs can be filtered"""


class TaskRunFilterCriteria(BaseFilterCriteria):
    """Criteria by which task runs can be filtered"""


class DeploymentFilterCriteria(BaseFilterCriteria):
    """Criteria by which deployments can be filtered"""