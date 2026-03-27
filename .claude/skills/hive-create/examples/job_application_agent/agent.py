"""Agent graph construction for Job Application Agent."""

from pathlib import Path

from framework.graph import EdgeSpec, EdgeCondition, Goal, SuccessCriterion, Constraint
from framework.graph.edge import GraphSpec
from framework.graph.executor import ExecutionResult
from framework.graph.checkpoint_config import CheckpointConfig
from framework.llm import LiteLLMProvider
from framework.runner.tool_registry import ToolRegistry
from framework.runtime.agent_runtime import AgentRuntime, create_agent_runtime
from framework.runtime.execution_stream import EntryPointSpec

from .config import default_config, metadata
from .nodes import (
    intake_node,
    analyze_node,
    tailor_node,
    deliver_node,
)

# Goal definition
goal = Goal(
    id="tailored-job-application",
    name="Tailored Job Application",
    description=(
        "Given a job description, analyze fit against the candidate profile, "
        "tailor the resume and cover letter, and deliver compiled PDFs with "
        "a match score and explanation of changes made."
    ),
    success_criteria=[
        SuccessCriterion(
            id="job-parsed",
            description="Job description is correctly parsed into structured brief",
            metric="job_brief_complete",
            target="true",
            weight=0.15,
        ),
        SuccessCriterion(
            id="score-produced",
            description="A meaningful match score is produced with reasoning",
            metric="score_range",
            target="0-100",
            weight=0.2,
        ),
        SuccessCriterion(
            id="documents-tailored",
            description="Resume and cover letter blocks are rewritten for the specific job",
            metric="blocks_complete",
            target="true",
            weight=0.35,
        ),
        SuccessCriterion(
            id="pdfs-delivered",
            description="Both PDFs are compiled and delivered to the user",
            metric="pdfs_served",
            target="2",
            weight=0.3,
        ),
    ],
    constraints=[
        Constraint(
            id="no-fabrication",
            description="Only use experiences and skills that exist in the candidate profile",
            constraint_type="quality",
            category="accuracy",
        ),
        Constraint(
            id="latex-safe",
            description="All LaTeX blocks must be valid — escape special characters properly",
            constraint_type="functional",
            category="output",
        ),
        Constraint(
            id="keyword-alignment",
            description="Tailored content must incorporate keywords from the job description",
            constraint_type="quality",
            category="relevance",
        ),
    ],
)

# Nodes
nodes = [
    intake_node,
    analyze_node,
    tailor_node,
    deliver_node,
]

# Edges
edges = [
    EdgeSpec(
        id="intake-to-analyze",
        source="intake",
        target="analyze",
        condition=EdgeCondition.ON_SUCCESS,
        priority=1,
    ),
    EdgeSpec(
        id="analyze-to-tailor",
        source="analyze",
        target="tailor",
        condition=EdgeCondition.ON_SUCCESS,
        priority=1,
    ),
    EdgeSpec(
        id="tailor-to-deliver",
        source="tailor",
        target="deliver",
        condition=EdgeCondition.ON_SUCCESS,
        priority=1,
    ),
    # If user wants adjustments, loop deliver back to tailor
    EdgeSpec(
        id="deliver-to-tailor-revision",
        source="deliver",
        target="tailor",
        condition=EdgeCondition.CONDITIONAL,
        condition_expr="str(delivery_status).lower() == 'revise'",
        priority=2,
    ),
    # If user wants to apply for another job, restart intake
    EdgeSpec(
        id="deliver-to-intake-new",
        source="deliver",
        target="intake",
        condition=EdgeCondition.CONDITIONAL,
        condition_expr="str(delivery_status).lower() == 'new_job'",
        priority=1,
    ),
]

entry_node = "intake"
entry_points = {"start": "intake"}
pause_nodes = []
terminal_nodes = []


class JobApplicationAgent:
    """
    Job Application Agent — 4-node pipeline.

    Flow: intake -> analyze -> tailor -> deliver
                                  ^         |
                                  +---------+ (revision loop)

    User pastes a job description. The agent:
    1. Parses and confirms the job details
    2. Scores the job against the candidate profile (silent)
    3. Rewrites resume + cover letter blocks (silent)
    4. Compiles PDFs and delivers with score + diff summary
    """

    def __init__(self, config=None):
        self.config = config or default_config
        self.goal = goal
        self.nodes = nodes
        self.edges = edges
        self.entry_node = entry_node
        self.entry_points = entry_points
        self.pause_nodes = pause_nodes
        self.terminal_nodes = terminal_nodes
        self._graph: GraphSpec | None = None
        self._agent_runtime: AgentRuntime | None = None
        self._tool_registry: ToolRegistry | None = None
        self._storage_path: Path | None = None

    def _build_graph(self) -> GraphSpec:
        return GraphSpec(
            id="job-application-agent-graph",
            goal_id=self.goal.id,
            version="1.0.0",
            entry_node=self.entry_node,
            entry_points=self.entry_points,
            terminal_nodes=self.terminal_nodes,
            pause_nodes=self.pause_nodes,
            nodes=self.nodes,
            edges=self.edges,
            default_model=self.config.model,
            max_tokens=self.config.max_tokens,
            loop_config={
                "max_iterations": 50,
                "max_tool_calls_per_turn": 20,
                "max_history_tokens": 32000,
            },
            conversation_mode="continuous",
            identity_prompt=(
                "You are a professional job application assistant. You help candidates "
                "tailor their resume and cover letter to specific job descriptions. "
                "You only use real experiences from the candidate's profile — never fabricate. "
                "You write with confidence, specificity, and keyword alignment."
            ),
        )

    def _setup(self, mock_mode=False) -> None:
        self._storage_path = Path.home() / ".hive" / "agents" / "job_application_agent"
        self._storage_path.mkdir(parents=True, exist_ok=True)

        # Copy profile and templates into agent data folder so load_data can access them
        data_path = self._storage_path / "data"
        data_path.mkdir(exist_ok=True)

        self._tool_registry = ToolRegistry()

        mcp_config_path = Path(__file__).parent / "mcp_servers.json"
        if mcp_config_path.exists():
            self._tool_registry.load_mcp_config(mcp_config_path)

        llm = None
        if not mock_mode:
            llm = LiteLLMProvider(
                model=self.config.model,
                api_key=self.config.api_key,
                api_base=self.config.api_base,
            )

        tool_executor = self._tool_registry.get_executor()
        tools = list(self._tool_registry.get_tools().values())
        self._graph = self._build_graph()

        checkpoint_config = CheckpointConfig(
            enabled=True,
            checkpoint_on_node_start=False,
            checkpoint_on_node_complete=True,
            checkpoint_max_age_days=7,
            async_checkpoint=True,
        )

        entry_point_specs = [
            EntryPointSpec(
                id="default",
                name="Default",
                entry_node=self.entry_node,
                trigger_type="manual",
                isolation_level="shared",
            )
        ]

        self._agent_runtime = create_agent_runtime(
            graph=self._graph,
            goal=self.goal,
            storage_path=self._storage_path,
            entry_points=entry_point_specs,
            llm=llm,
            tools=tools,
            tool_executor=tool_executor,
            checkpoint_config=checkpoint_config,
        )

    async def start(self, mock_mode=False) -> None:
        if self._agent_runtime is None:
            self._setup(mock_mode=mock_mode)
        if not self._agent_runtime.is_running:
            await self._agent_runtime.start()

    async def stop(self) -> None:
        if self._agent_runtime and self._agent_runtime.is_running:
            await self._agent_runtime.stop()
        self._agent_runtime = None

    async def trigger_and_wait(
        self,
        entry_point: str = "default",
        input_data: dict | None = None,
        timeout: float | None = None,
        session_state: dict | None = None,
    ) -> ExecutionResult | None:
        if self._agent_runtime is None:
            raise RuntimeError("Agent not started. Call start() first.")
        return await self._agent_runtime.trigger_and_wait(
            entry_point_id=entry_point,
            input_data=input_data or {},
            session_state=session_state,
        )

    async def run(
        self, context: dict, mock_mode=False, session_state=None
    ) -> ExecutionResult:
        await self.start(mock_mode=mock_mode)
        try:
            result = await self.trigger_and_wait(
                "default", context, session_state=session_state
            )
            return result or ExecutionResult(success=False, error="Execution timeout")
        finally:
            await self.stop()

    def info(self):
        return {
            "name": metadata.name,
            "version": metadata.version,
            "description": metadata.description,
            "goal": {"name": self.goal.name, "description": self.goal.description},
            "nodes": [n.id for n in self.nodes],
            "edges": [e.id for e in self.edges],
            "entry_node": self.entry_node,
            "entry_points": self.entry_points,
            "pause_nodes": self.pause_nodes,
            "terminal_nodes": self.terminal_nodes,
            "client_facing_nodes": [n.id for n in self.nodes if n.client_facing],
        }

    def validate(self):
        errors = []
        warnings = []
        node_ids = {node.id for node in self.nodes}
        for edge in self.edges:
            if edge.source not in node_ids:
                errors.append(f"Edge {edge.id}: source '{edge.source}' not found")
            if edge.target not in node_ids:
                errors.append(f"Edge {edge.id}: target '{edge.target}' not found")
        if self.entry_node not in node_ids:
            errors.append(f"Entry node '{self.entry_node}' not found")
        return {"valid": len(errors) == 0, "errors": errors, "warnings": warnings}


# Default instance
default_agent = JobApplicationAgent()
