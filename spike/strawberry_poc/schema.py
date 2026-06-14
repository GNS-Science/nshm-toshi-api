"""
Root schema — Query + Mutation.

Designed as a drop-in replacement for the Graphene stack:
  - auto_camel_case=False  → field/mutation names stay snake_case
  - Payload wrapper types  → mutation return shapes match Graphene's relay
                             ClientIDMutation pattern exactly

This means all existing client query strings work unchanged against
either the old (Graphene/Flask) or new (Strawberry/FastAPI) stack.
"""

import logging
from collections.abc import Iterable
from typing import Annotated

import strawberry
from strawberry import relay
from strawberry.relay import GlobalID
from strawberry.schema.config import StrawberryConfig

import data.search as _data_search
from data.dynamo import es_key_for, get_object, scan_objects_paginated
from data.s3 import scan_s3_paginated
from data.search import search as es_search
from models.aggregate_inversion_solution import (
    AggregateInversionSolution,
    CreateAggregateInversionSolutionInput,
    mutate_create_aggregate_inversion_solution,
    resolve_aggregate_inversion_solutions,
)
from models.automation_task import (
    AutomationTask,
    CreateAutomationTaskInput,
    RuptureGenerationTask,
    UpdateAutomationTaskInput,
    mutate_create_automation_task,
    mutate_create_rupture_generation_task,
    mutate_update_automation_task,
    mutate_update_rupture_generation_task,
    resolve_automation_tasks,
    resolve_rupture_generation_tasks,
)
from models.common import (
    BigInt,
    DateTime,
    FileRole,
    KeyValuePairInput,
    client_mutation_id_payload_field,
)
from models.file import CreateFileInput, ToshiFile, mutate_create_file, resolve_files
from models.general_task import (
    CreateGeneralTaskInput,
    GeneralTask,
    UpdateGeneralTaskInput,
    mutate_create_general_task,
    mutate_update_general_task,
    resolve_general_tasks,
)
from models.inversion_solution import (
    AppendInversionSolutionTablesInput,
    CreateInversionSolutionInput,
    InversionSolution,
    mutate_append_inversion_solution_tables,
    mutate_create_inversion_solution,
    resolve_inversion_solutions,
)
from models.inversion_solution_nrml import (
    CreateInversionSolutionNrmlInput,
    InversionSolutionNrml,
    mutate_create_inversion_solution_nrml,
    resolve_inversion_solution_nrmls,
)
from models.object_identity import (
    ObjectIdentitiesConnection,
    decode_cursor,
    make_object_identities_connection,
)
from models.openquake_hazard_config import (
    CreateOpenquakeHazardConfigInput,
    OpenquakeHazardConfig,
    mutate_create_openquake_hazard_config,
    resolve_openquake_hazard_configs,
)
from models.openquake_hazard_solution import (
    CreateOpenquakeHazardSolutionInput,
    OpenquakeHazardSolution,
    mutate_create_openquake_hazard_solution,
    resolve_openquake_hazard_solutions,
)
from models.openquake_hazard_task import (
    CreateOpenquakeHazardTaskInput,
    OpenquakeHazardTask,
    UpdateOpenquakeHazardTaskInput,
    mutate_create_openquake_hazard_task,
    mutate_update_openquake_hazard_task,
    resolve_openquake_hazard_tasks,
)
from models.page_info import CompatListConnection
from models.relations import (
    CreateFileRelationInput,
    CreateTaskRelationInput,
    FileRelation,
    TaskTaskRelation,
    mutate_create_file_relation,
    mutate_create_task_relation,
)
from models.rupture_set import (
    CreateRuptureSetInput,
    RuptureSet,
    mutate_create_rupture_set,
    resolve_rupture_sets,
)
from models.scaled_inversion_solution import (
    CreateScaledInversionSolutionInput,
    ScaledInversionSolution,
    mutate_create_scaled_inversion_solution,
    resolve_scaled_inversion_solutions,
)
from models.sms_file import CreateSmsFileInput, SmsFile, mutate_create_sms_file, resolve_sms_files
from models.strong_motion_station import (
    CreateStrongMotionStationInput,
    StrongMotionStation,
    mutate_create_strong_motion_station,
    resolve_strong_motion_stations,
)
from models.table import CreateTableInput, Table, mutate_create_table
from models.time_dependent_inversion_solution import (
    CreateTimeDependentInversionSolutionInput,
    TimeDependentInversionSolution,
    mutate_create_time_dependent_inversion_solution,
    resolve_time_dependent_inversion_solutions,
)

log = logging.getLogger(__name__)


# ── SearchResult union + connection ───────────────────────────────────────────

SearchResult = Annotated[
    GeneralTask
    | RuptureGenerationTask
    | AutomationTask
    | StrongMotionStation
    | OpenquakeHazardTask
    | OpenquakeHazardSolution
    | OpenquakeHazardConfig
    | ToshiFile
    | SmsFile
    | RuptureSet
    | InversionSolution
    | ScaledInversionSolution
    | AggregateInversionSolution
    | TimeDependentInversionSolution
    | InversionSolutionNrml,
    strawberry.union(name="SearchResult"),
]


@strawberry.type
class SearchResultEdge:
    node: SearchResult | None = None


@strawberry.type
class SearchResultConnection:
    # Matches legacy `[SearchResultEdge]!` — non-null outer list, nullable elements.
    # See docs/smoke-test-learnings.md §1 on Strawberry's `list[T] → [T!]` default.
    edges: list[SearchResultEdge | None] = strawberry.field(default_factory=list)


@strawberry.type(name="Search")
class SearchPayload:
    search_result: SearchResultConnection | None = None


def _dispatch_search(hit: dict) -> SearchResult | None:
    """Instantiate the right Strawberry type from an ES _source dict.

    Delegates to the shared clazz_name → type registry in models/_dispatch.py.
    Unknown clazz values fall back to ToshiFile, matching legacy behaviour.
    """
    from models._dispatch import dispatch_search  # noqa: PLC0415

    try:
        return dispatch_search(hit)
    except (KeyError, AttributeError, ValueError, TypeError) as e:
        log.warning("_dispatch_search: failed to instantiate %s from hit: %s", hit.get("clazz_name") or "?", e)
        return None


# ── Payload wrapper types (mirrors Graphene's ClientIDMutation Output pattern) ─


@strawberry.type(name="CreateGeneralTaskPayload")
class CreateGeneralTaskPayload:
    general_task: GeneralTask | None = None
    client_mutation_id: str | None = client_mutation_id_payload_field()


@strawberry.type(name="UpdateGeneralTaskPayload")
class UpdateGeneralTaskPayload:
    general_task: GeneralTask | None = None
    client_mutation_id: str | None = client_mutation_id_payload_field()


@strawberry.type(name="CreateRuptureGenerationTask")
class CreateRuptureGenerationTaskPayload:
    task_result: RuptureGenerationTask | None = None
    client_mutation_id: str | None = client_mutation_id_payload_field()


@strawberry.type(name="UpdateRuptureGenerationTask")
class UpdateRuptureGenerationTaskPayload:
    task_result: RuptureGenerationTask | None = None
    client_mutation_id: str | None = client_mutation_id_payload_field()


@strawberry.type(name="CreateAutomationTask")
class CreateAutomationTaskPayload:
    task_result: AutomationTask | None = None
    client_mutation_id: str | None = client_mutation_id_payload_field()


@strawberry.type(name="UpdateAutomationTask")
class UpdateAutomationTaskPayload:
    task_result: AutomationTask | None = None
    client_mutation_id: str | None = client_mutation_id_payload_field()


@strawberry.type(name="CreateFile")
class CreateFilePayload:
    ok: bool | None = None
    file_result: ToshiFile | None = None
    client_mutation_id: str | None = client_mutation_id_payload_field()


@strawberry.type(name="CreateSmsFile")
class CreateSmsFilePayload:
    ok: bool | None = None
    file_result: SmsFile | None = None
    client_mutation_id: str | None = client_mutation_id_payload_field()


@strawberry.type(name="CreateStrongMotionStationPayload")
class CreateStrongMotionStationPayload:
    strong_motion_station: StrongMotionStation | None = None
    client_mutation_id: str | None = client_mutation_id_payload_field()


@strawberry.type(name="CreateRuptureSetPayload")
class CreateRuptureSetPayload:
    ok: bool | None = None
    rupture_set: RuptureSet | None = None
    client_mutation_id: str | None = client_mutation_id_payload_field()


@strawberry.type(name="CreateFileRelation")
class CreateFileRelationPayload:
    ok: bool | None = None
    file_relation: FileRelation | None = None
    client_mutation_id: str | None = client_mutation_id_payload_field()


@strawberry.type(name="CreateTaskTaskRelation")
class CreateTaskRelationPayload:
    ok: bool | None = None
    thing_relation: TaskTaskRelation | None = None
    client_mutation_id: str | None = client_mutation_id_payload_field()


@strawberry.type(name="CreateInversionSolutionPayload")
class CreateInversionSolutionPayload:
    ok: bool | None = None
    inversion_solution: InversionSolution | None = None
    client_mutation_id: str | None = client_mutation_id_payload_field()


@strawberry.type(name="AppendInversionSolutionTablesPayload")
class AppendInversionSolutionTablesPayload:
    ok: bool | None = None
    inversion_solution: InversionSolution | None = None
    client_mutation_id: str | None = client_mutation_id_payload_field()


@strawberry.type(name="CreateScaledInversionSolutionPayload")
class CreateScaledInversionSolutionPayload:
    ok: bool | None = None
    solution: ScaledInversionSolution | None = None
    client_mutation_id: str | None = client_mutation_id_payload_field()


@strawberry.type(name="CreateAggregateInversionSolutionPayload")
class CreateAggregateInversionSolutionPayload:
    ok: bool | None = None
    solution: AggregateInversionSolution | None = None
    client_mutation_id: str | None = client_mutation_id_payload_field()


@strawberry.type(name="CreateTimeDependentInversionSolutionPayload")
class CreateTimeDependentInversionSolutionPayload:
    ok: bool | None = None
    solution: TimeDependentInversionSolution | None = None
    client_mutation_id: str | None = client_mutation_id_payload_field()


@strawberry.type(name="CreateInversionSolutionNrmlPayload")
class CreateInversionSolutionNrmlPayload:
    ok: bool | None = None
    inversion_solution_nrml: InversionSolutionNrml | None = None
    client_mutation_id: str | None = client_mutation_id_payload_field()


@strawberry.type(name="CreateOpenquakeHazardConfigPayload")
class CreateOpenquakeHazardConfigPayload:
    ok: bool | None = None
    config: OpenquakeHazardConfig | None = None
    client_mutation_id: str | None = client_mutation_id_payload_field()


@strawberry.type(name="CreateOpenquakeHazardSolutionPayload")
class CreateOpenquakeHazardSolutionPayload:
    ok: bool | None = None
    openquake_hazard_solution: OpenquakeHazardSolution | None = None
    client_mutation_id: str | None = client_mutation_id_payload_field()


@strawberry.type(name="CreateOpenquakeHazardTask")
class CreateOpenquakeHazardTaskPayload:
    ok: bool | None = None
    # Field name matches legacy SDL — `openquake_hazard_task`, not the
    # POC-original `task_result` (chris's audit Problem 2 #1).
    openquake_hazard_task: OpenquakeHazardTask | None = strawberry.field(
        default=None, name="openquake_hazard_task"
    )
    client_mutation_id: str | None = client_mutation_id_payload_field()


@strawberry.type(name="UpdateOpenquakeHazardTask")
class UpdateOpenquakeHazardTaskPayload:
    ok: bool | None = None
    # Legacy uses `openquake_hazard_task` not `task_result` on the OQ task
    # payloads (chris's Problem 2 #1).
    openquake_hazard_task: OpenquakeHazardTask | None = strawberry.field(
        default=None, name="openquake_hazard_task"
    )
    client_mutation_id: str | None = client_mutation_id_payload_field()


@strawberry.type(name="NodeFilter")
class NodeFilterPayload:
    ok: bool = False
    result: SearchResultConnection = strawberry.field(default_factory=SearchResultConnection)


@strawberry.type(name="CreateTablePayload")
class CreateTablePayload:
    ok: bool | None = None
    table: Table | None = None
    client_mutation_id: str | None = client_mutation_id_payload_field()


@strawberry.type
class ReindexPayload:
    ok: bool = False
    reindexed_ids: list[str] = strawberry.field(default_factory=list)


# ── Query ──────────────────────────────────────────────────────────────────────


@strawberry.type(name="QueryRoot")
class Query:
    node: relay.Node = relay.node()

    @strawberry.field
    def about(self) -> str:
        return "Hello, I am nshm_toshi_api (Strawberry POC)! [AUTH]"

    @relay.connection(CompatListConnection[GeneralTask])
    def general_tasks(self, info: strawberry.types.Info) -> Iterable[GeneralTask]:
        return resolve_general_tasks(info)

    @relay.connection(CompatListConnection[RuptureSet])
    def rupture_sets(self, info: strawberry.types.Info) -> Iterable[RuptureSet]:
        return resolve_rupture_sets(info)

    @relay.connection(CompatListConnection[ToshiFile])
    def files(self, info: strawberry.types.Info) -> Iterable[ToshiFile]:
        return resolve_files(info)

    @relay.connection(CompatListConnection[SmsFile])
    def sms_files(self, info: strawberry.types.Info) -> Iterable[SmsFile]:
        return resolve_sms_files(info)

    @relay.connection(CompatListConnection[StrongMotionStation])
    def strong_motion_stations(self, info: strawberry.types.Info) -> Iterable[StrongMotionStation]:
        return resolve_strong_motion_stations(info)

    @relay.connection(CompatListConnection[AutomationTask])
    def automation_tasks(self, info: strawberry.types.Info) -> Iterable[AutomationTask]:
        return resolve_automation_tasks(info)

    @relay.connection(CompatListConnection[RuptureGenerationTask])
    def rupture_generation_tasks(self, info: strawberry.types.Info) -> Iterable[RuptureGenerationTask]:
        return resolve_rupture_generation_tasks(info)

    @relay.connection(CompatListConnection[InversionSolution])
    def inversion_solutions(self, info: strawberry.types.Info) -> Iterable[InversionSolution]:
        return resolve_inversion_solutions(info)

    @relay.connection(CompatListConnection[ScaledInversionSolution])
    def scaled_inversion_solutions(self, info: strawberry.types.Info) -> Iterable[ScaledInversionSolution]:
        return resolve_scaled_inversion_solutions(info)

    @relay.connection(CompatListConnection[AggregateInversionSolution])
    def aggregate_inversion_solutions(self, info: strawberry.types.Info) -> Iterable[AggregateInversionSolution]:
        return resolve_aggregate_inversion_solutions(info)

    @relay.connection(CompatListConnection[TimeDependentInversionSolution])
    def time_dependent_inversion_solutions(
        self, info: strawberry.types.Info
    ) -> Iterable[TimeDependentInversionSolution]:
        return resolve_time_dependent_inversion_solutions(info)

    @relay.connection(CompatListConnection[InversionSolutionNrml])
    def inversion_solution_nrmls(self, info: strawberry.types.Info) -> Iterable[InversionSolutionNrml]:
        return resolve_inversion_solution_nrmls(info)

    @relay.connection(CompatListConnection[OpenquakeHazardConfig])
    def openquake_hazard_configs(self, info: strawberry.types.Info) -> Iterable[OpenquakeHazardConfig]:
        return resolve_openquake_hazard_configs(info)

    @relay.connection(CompatListConnection[OpenquakeHazardSolution])
    def openquake_hazard_solutions(self, info: strawberry.types.Info) -> Iterable[OpenquakeHazardSolution]:
        return resolve_openquake_hazard_solutions(info)

    @relay.connection(CompatListConnection[OpenquakeHazardTask])
    def openquake_hazard_tasks(self, info: strawberry.types.Info) -> Iterable[OpenquakeHazardTask]:
        return resolve_openquake_hazard_tasks(info)

    @strawberry.field
    def object_identities(
        self,
        info: strawberry.types.Info,
        object_type: str,
        first: int = 5,
        after: str | None = None,
    ) -> ObjectIdentitiesConnection:
        after_id = decode_cursor(after) if after else None
        items, has_more, last_id = scan_objects_paginated(
            info.context["dynamodb"], object_type, limit=first, after_id=after_id
        )
        return make_object_identities_connection(items, has_more, last_id)

    @strawberry.field
    def legacy_object_identities(
        self,
        info: strawberry.types.Info,
        store_type: str,
        first: int = 5,
        after: str | None = None,
    ) -> ObjectIdentitiesConnection:
        if store_type not in ("File", "Thing", "Table"):
            return ObjectIdentitiesConnection()
        after_id = decode_cursor(after) if after else None
        items, has_more, last_id = scan_s3_paginated(store_type, limit=first, after_id=after_id)
        return make_object_identities_connection(items, has_more, last_id)

    @strawberry.field
    def nodes(self, info: strawberry.types.Info, id_in: list[strawberry.ID | None] | None = None) -> NodeFilterPayload:
        edges = []
        for gid_str in id_in:
            try:
                gid = GlobalID.from_id(str(gid_str))
            except (ValueError, TypeError) as e:
                log.warning("nodes: malformed GlobalID %r: %s", gid_str, e)
                continue
            try:
                data = get_object(info.context["dynamodb"], gid.type_name, gid.node_id)
            except (KeyError, AttributeError) as e:
                log.warning("nodes: lookup failed for %s: %s", gid_str, e)
                continue
            if data and (node := _dispatch_search(data)) is not None:
                edges.append(SearchResultEdge(node=node))
        return NodeFilterPayload(ok=True, result=SearchResultConnection(edges=edges))

    @strawberry.field
    def search(self, info: strawberry.types.Info, search_term: str) -> SearchPayload:
        ctx = info.context
        hits = es_search(
            search_term,
            endpoint=ctx.get("es_endpoint", ""),
            index=ctx.get("es_index", "toshi-index-mapped"),
        )
        edges = [SearchResultEdge(node=node) for hit in hits if (node := _dispatch_search(hit)) is not None]
        return SearchPayload(search_result=SearchResultConnection(edges=edges))


# ── Mutation ───────────────────────────────────────────────────────────────────


@strawberry.type(name="MutationRoot")
class Mutation:
    @strawberry.mutation
    def create_general_task(
        self, info: strawberry.types.Info, input: CreateGeneralTaskInput
    ) -> CreateGeneralTaskPayload:
        return CreateGeneralTaskPayload(
            general_task=mutate_create_general_task(info, input), client_mutation_id=input.client_mutation_id
        )

    @strawberry.mutation
    def update_general_task(
        self, info: strawberry.types.Info, input: UpdateGeneralTaskInput
    ) -> UpdateGeneralTaskPayload:
        return UpdateGeneralTaskPayload(
            general_task=mutate_update_general_task(info, input), client_mutation_id=input.client_mutation_id
        )

    @strawberry.mutation
    def create_rupture_set(self, info: strawberry.types.Info, input: CreateRuptureSetInput) -> CreateRuptureSetPayload:
        return CreateRuptureSetPayload(
            ok=True, rupture_set=mutate_create_rupture_set(info, input), client_mutation_id=input.client_mutation_id
        )

    @strawberry.mutation
    def create_file(
        self,
        info: strawberry.types.Info,
        file_name: str,
        md5_digest: str,
        file_size: BigInt,
        created: DateTime | None = None,
        meta: list[KeyValuePairInput | None] | None = None,
    ) -> CreateFilePayload:
        # Positional signature mirrors the legacy SDL `create_file(file_name,
        # md5_digest, file_size, created, meta, predecessors): CreateFile`.
        # nshm-toshi-client sends this shape directly; the `input:` wrapper
        # form would reject the client's query at validation time.
        #
        # `predecessors` is in legacy SDL but no current client (nshm-toshi-
        # client/runzi/weka) uses it on plain File create — omitted for now;
        # add back if a client surfaces a need.
        input_obj = CreateFileInput(
            file_name=file_name,
            md5_digest=md5_digest,
            file_size=file_size,
            created=created,
            meta=meta,
        )
        return CreateFilePayload(ok=True, file_result=mutate_create_file(info, input_obj), client_mutation_id=None)

    @strawberry.mutation
    def create_sms_file(self, info: strawberry.types.Info, input: CreateSmsFileInput) -> CreateSmsFilePayload:
        return CreateSmsFilePayload(
            ok=True, file_result=mutate_create_sms_file(info, input), client_mutation_id=input.client_mutation_id
        )

    @strawberry.mutation
    def create_strong_motion_station(
        self, info: strawberry.types.Info, input: CreateStrongMotionStationInput
    ) -> CreateStrongMotionStationPayload:
        return CreateStrongMotionStationPayload(
            strong_motion_station=mutate_create_strong_motion_station(info, input),
            client_mutation_id=input.client_mutation_id,
        )

    @strawberry.mutation
    def create_automation_task(
        self, info: strawberry.types.Info, input: CreateAutomationTaskInput
    ) -> CreateAutomationTaskPayload:
        return CreateAutomationTaskPayload(
            task_result=mutate_create_automation_task(info, input), client_mutation_id=input.client_mutation_id
        )

    @strawberry.mutation
    def create_rupture_generation_task(
        self, info: strawberry.types.Info, input: CreateAutomationTaskInput
    ) -> CreateRuptureGenerationTaskPayload:
        return CreateRuptureGenerationTaskPayload(
            task_result=mutate_create_rupture_generation_task(info, input), client_mutation_id=input.client_mutation_id
        )

    @strawberry.mutation
    def update_rupture_generation_task(
        self, info: strawberry.types.Info, input: UpdateAutomationTaskInput
    ) -> UpdateRuptureGenerationTaskPayload:
        return UpdateRuptureGenerationTaskPayload(
            task_result=mutate_update_rupture_generation_task(info, input), client_mutation_id=input.client_mutation_id
        )

    @strawberry.mutation
    def update_automation_task(
        self, info: strawberry.types.Info, input: UpdateAutomationTaskInput
    ) -> UpdateAutomationTaskPayload:
        return UpdateAutomationTaskPayload(
            task_result=mutate_update_automation_task(info, input), client_mutation_id=input.client_mutation_id
        )

    @strawberry.mutation
    def create_inversion_solution(
        self, info: strawberry.types.Info, input: CreateInversionSolutionInput
    ) -> CreateInversionSolutionPayload:
        return CreateInversionSolutionPayload(
            ok=True,
            inversion_solution=mutate_create_inversion_solution(info, input),
            client_mutation_id=input.client_mutation_id,
        )

    @strawberry.mutation
    def create_table(self, info: strawberry.types.Info, input: CreateTableInput) -> CreateTablePayload:
        return CreateTablePayload(
            ok=True, table=mutate_create_table(info, input), client_mutation_id=input.client_mutation_id
        )

    @strawberry.mutation
    def append_inversion_solution_tables(
        self, info: strawberry.types.Info, input: AppendInversionSolutionTablesInput
    ) -> AppendInversionSolutionTablesPayload:
        return AppendInversionSolutionTablesPayload(
            ok=True,
            inversion_solution=mutate_append_inversion_solution_tables(info, input),
            client_mutation_id=input.client_mutation_id,
        )

    @strawberry.mutation
    def create_scaled_inversion_solution(
        self, info: strawberry.types.Info, input: CreateScaledInversionSolutionInput
    ) -> CreateScaledInversionSolutionPayload:
        return CreateScaledInversionSolutionPayload(
            ok=True,
            solution=mutate_create_scaled_inversion_solution(info, input),
            client_mutation_id=input.client_mutation_id,
        )

    @strawberry.mutation
    def create_aggregate_inversion_solution(
        self, info: strawberry.types.Info, input: CreateAggregateInversionSolutionInput
    ) -> CreateAggregateInversionSolutionPayload:
        return CreateAggregateInversionSolutionPayload(
            ok=True,
            solution=mutate_create_aggregate_inversion_solution(info, input),
            client_mutation_id=input.client_mutation_id,
        )

    @strawberry.mutation
    def create_time_dependent_inversion_solution(
        self, info: strawberry.types.Info, input: CreateTimeDependentInversionSolutionInput
    ) -> CreateTimeDependentInversionSolutionPayload:
        return CreateTimeDependentInversionSolutionPayload(
            ok=True,
            solution=mutate_create_time_dependent_inversion_solution(info, input),
            client_mutation_id=input.client_mutation_id,
        )

    @strawberry.mutation
    def create_inversion_solution_nrml(
        self, info: strawberry.types.Info, input: CreateInversionSolutionNrmlInput
    ) -> CreateInversionSolutionNrmlPayload:
        return CreateInversionSolutionNrmlPayload(
            ok=True,
            inversion_solution_nrml=mutate_create_inversion_solution_nrml(info, input),
            client_mutation_id=input.client_mutation_id,
        )

    @strawberry.mutation
    def create_openquake_hazard_config(
        self, info: strawberry.types.Info, input: CreateOpenquakeHazardConfigInput
    ) -> CreateOpenquakeHazardConfigPayload:
        return CreateOpenquakeHazardConfigPayload(
            ok=True,
            config=mutate_create_openquake_hazard_config(info, input),
            client_mutation_id=input.client_mutation_id,
        )

    @strawberry.mutation
    def create_openquake_hazard_solution(
        self, info: strawberry.types.Info, input: CreateOpenquakeHazardSolutionInput
    ) -> CreateOpenquakeHazardSolutionPayload:
        return CreateOpenquakeHazardSolutionPayload(
            ok=True,
            openquake_hazard_solution=mutate_create_openquake_hazard_solution(info, input),
            client_mutation_id=input.client_mutation_id,
        )

    @strawberry.mutation
    def create_openquake_hazard_task(
        self, info: strawberry.types.Info, input: CreateOpenquakeHazardTaskInput
    ) -> CreateOpenquakeHazardTaskPayload:
        return CreateOpenquakeHazardTaskPayload(
            ok=True,
            openquake_hazard_task=mutate_create_openquake_hazard_task(info, input),
            client_mutation_id=input.client_mutation_id,
        )

    @strawberry.mutation
    def update_openquake_hazard_task(
        self, info: strawberry.types.Info, input: UpdateOpenquakeHazardTaskInput
    ) -> UpdateOpenquakeHazardTaskPayload:
        return UpdateOpenquakeHazardTaskPayload(
            ok=True,
            openquake_hazard_task=mutate_update_openquake_hazard_task(info, input),
            client_mutation_id=input.client_mutation_id,
        )

    @strawberry.mutation
    def create_file_relation(
        self,
        info: strawberry.types.Info,
        file_id: strawberry.ID,
        role: FileRole,
        thing_id: strawberry.ID,
    ) -> CreateFileRelationPayload:
        # Positional signature mirrors legacy `create_file_relation(file_id,
        # role, thing_id): CreateFileRelation`. nshm-toshi-client and runzi
        # both send this shape; the `input:` wrapper form would be rejected.
        input_obj = CreateFileRelationInput(file_id=file_id, role=role, thing_id=thing_id)
        mutate_create_file_relation(info, input_obj)
        # Legacy returns the constructed FileRelation so clients can introspect
        # the link before requerying.
        relation = FileRelation(
            role=role,
            file_raw_id=GlobalID.from_id(str(file_id)).node_id,
            thing_raw_id=GlobalID.from_id(str(thing_id)).node_id,
        )
        return CreateFileRelationPayload(ok=True, file_relation=relation, client_mutation_id=None)

    @strawberry.mutation
    def create_task_relation(
        self,
        info: strawberry.types.Info,
        child_id: strawberry.ID,
        parent_id: strawberry.ID,
    ) -> CreateTaskRelationPayload:
        # Positional signature mirrors legacy `create_task_relation(child_id, parent_id)`.
        # Sibling to create_file_relation (which #320 fixed) — runzi sends both.
        input_obj = CreateTaskRelationInput(parent_id=parent_id, child_id=child_id)
        relation = mutate_create_task_relation(info, input_obj)
        return CreateTaskRelationPayload(ok=True, thing_relation=relation, client_mutation_id=None)

    @strawberry.mutation
    def reindex(self, info: strawberry.types.Info, id_in: list[strawberry.ID | None] | None = None) -> ReindexPayload:
        ctx = info.context
        dynamodb = ctx["dynamodb"]
        ep = ctx.get("es_endpoint", "")
        idx = ctx.get("es_index", "toshi-index-mapped")
        reindexed = []
        for gid in id_in:
            global_id = GlobalID.from_id(gid)
            data = get_object(dynamodb, global_id.type_name, global_id.node_id)
            if data:
                key = es_key_for(global_id.type_name, global_id.node_id)
                _data_search.index_document(key, data, endpoint=ep, index=idx)
                reindexed.append(str(gid))
        return ReindexPayload(ok=True, reindexed_ids=reindexed)


schema = strawberry.Schema(
    query=Query,
    mutation=Mutation,
    config=StrawberryConfig(auto_camel_case=False),
)
