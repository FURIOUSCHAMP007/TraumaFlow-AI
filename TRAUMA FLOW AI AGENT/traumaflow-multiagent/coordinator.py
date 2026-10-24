
from uagents import Agent, Context, Model, Protocol

# ============================================================
# SPECIALIST AGENT ADDRESSES
# ============================================================

CAPACITY_AGENT_ADDRESS = (
    "agent1qgc6dz0z26ns57jd2rdas9gfs6jp35f2pjay53jlyk242qsaf0z760zr2hj"
)

ASSESSMENT_AGENT_ADDRESS = (
    "agent1qft8v0cxgqu0cl4x2rd5g0nh9k4njzygy0vupr6nd4lep992qfsq74uxt5x"
)

PLANNING_AGENT_ADDRESS = (
    "agent1qvkdc55rme6ax7dka78tvpgn573j2pam2d97jndgxmr2k3aju74r7zxa0vh"
)


# ============================================================
# MESSAGE MODELS FOR THE EXISTING MULTI-AGENT WORKFLOW
# ============================================================

class IncidentReport(Model):
    incident_type: str
    estimated_patients: int
    arrival_minutes: int


class CapacityRequest(Model):
    hospital_name: str
    staffed_beds: int
    occupied_beds: int


class CapacityReply(Model):
    hospital_name: str
    available_beds: int
    status: str
    note: str


class IncidentAssessmentRequest(Model):
    incident_type: str
    estimated_patients: int
    arrival_minutes: int


class IncidentAssessmentReply(Model):
    incident_type: str
    input_valid: bool
    workload_band: str
    explanation: str
    human_review_required: bool


class PlanningRequest(Model):
    incident_type: str
    estimated_patients: int
    arrival_minutes: int
    available_beds: int
    workload_band: str


class PlanningReply(Model):
    incident_type: str
    planning_status: str
    summary: str
    recommended_actions: list[str]
    human_approval_required: bool


# ============================================================
# BASIC CHAT MESSAGE MODELS
# ============================================================

class ChatRequest(Model):
    message: str


class ChatResponse(Model):
    message: str


# ============================================================
# TRAUMAFLOW CHAT PROTOCOL
# ============================================================

traumaflow_chat_protocol = Protocol(
    name="TraumaFlow_Chat",
    version="0.1.0",
)


@traumaflow_chat_protocol.on_message(
    model=ChatRequest,
    replies=ChatResponse,
)
async def handle_chat(
    ctx: Context,
    sender: str,
    msg: ChatRequest,
):
    """Respond to basic chat requests with a safe system overview."""

    text = msg.message.strip()

    ctx.logger.info(f"Chat request received from: {sender}")

    if not text:
        response_text = (
            "Please send a non-empty message. "
            "TraumaFlow is a simulation-only coordination prototype."
        )
    else:
        response_text = (
            "TraumaFlow AI is a simulated multi-agent emergency "
            "coordination prototype. It coordinates fictional capacity "
            "data, illustrative incident workload assessment, and "
            "planning suggestions. It does not perform clinical triage "
            "or authorize real-world dispatch or diversion. "
            "Human review and approval are required."
        )

    await ctx.send(sender, ChatResponse(message=response_text))
    ctx.logger.info("Chat response sent.")


# ============================================================
# COORDINATOR AGENT
# ============================================================

coordinator = Agent(
    name="traumaflow_coordinator",
    seed="traumaflow-coordinator-development-seed-change-before-deployment",
    port=8000,
    mailbox=True,
)

# Attach the protocol to the Coordinator.
coordinator.include(traumaflow_chat_protocol)


# ============================================================
# STATE FOR THE LOCAL SIMULATION
# ============================================================

# This first demo supports one active incident at a time.
pending_incident = None
latest_capacity_reply = None
latest_assessment_reply = None
planning_request_sent = False


# ============================================================
# STARTUP
# ============================================================

@coordinator.on_event("startup")
async def startup(ctx: Context):
    ctx.logger.info("TraumaFlow Coordinator started.")
    ctx.logger.info("TraumaFlow Chat Protocol attached.")
    ctx.logger.info("Capacity Agent configured.")
    ctx.logger.info("Assessment Agent configured.")
    ctx.logger.info("Planning Agent configured.")
    ctx.logger.info("Simulation only; human review required.")


# ============================================================
# INCIDENT INTAKE
# ============================================================

@coordinator.on_message(model=IncidentReport)
async def handle_incident(
    ctx: Context,
    sender: str,
    msg: IncidentReport,
):
    global pending_incident
    global latest_capacity_reply
    global latest_assessment_reply
    global planning_request_sent

    ctx.logger.info(f"Incident received from: {sender}")
    ctx.logger.info(f"Incident type: {msg.incident_type}")
    ctx.logger.info(f"Estimated patients: {msg.estimated_patients}")
    ctx.logger.info(f"Arrival time: {msg.arrival_minutes} minutes")

    if (
        not msg.incident_type.strip()
        or msg.estimated_patients <= 0
        or msg.arrival_minutes <= 0
    ):
        ctx.logger.warning("Invalid incident; no requests sent.")
        return

    if pending_incident is not None:
        ctx.logger.warning(
            "Another incident is awaiting specialist results. "
            "Ignoring this additional incident."
        )
        return

    pending_incident = msg
    latest_capacity_reply = None
    latest_assessment_reply = None
    planning_request_sent = False

    # Fictional data for demonstration only.
    capacity_request = CapacityRequest(
        hospital_name="Fictional Hospital Alpha",
        staffed_beds=40,
        occupied_beds=31,
    )

    assessment_request = IncidentAssessmentRequest(
        incident_type=msg.incident_type,
        estimated_patients=msg.estimated_patients,
        arrival_minutes=msg.arrival_minutes,
    )

    try:
        await ctx.send(CAPACITY_AGENT_ADDRESS, capacity_request)
        ctx.logger.info("Capacity request sent.")
    except Exception as exc:
        ctx.logger.error(f"Capacity request failed: {exc}")

    try:
        await ctx.send(ASSESSMENT_AGENT_ADDRESS, assessment_request)
        ctx.logger.info("Assessment request sent.")
    except Exception as exc:
        ctx.logger.error(f"Assessment request failed: {exc}")


# ============================================================
# CAPACITY RESULT
# ============================================================

@coordinator.on_message(model=CapacityReply)
async def receive_capacity_reply(
    ctx: Context,
    sender: str,
    msg: CapacityReply,
):
    global latest_capacity_reply

    if sender != CAPACITY_AGENT_ADDRESS:
        ctx.logger.warning("Ignoring capacity reply from unknown sender.")
        return

    if pending_incident is None:
        ctx.logger.warning("No pending incident for capacity reply.")
        return

    latest_capacity_reply = msg

    ctx.logger.info(f"Capacity reply received from: {sender}")
    ctx.logger.info(f"Hospital: {msg.hospital_name}")
    ctx.logger.info(f"Available beds: {msg.available_beds}")
    ctx.logger.info(f"Capacity status: {msg.status}")
    ctx.logger.info(f"Capacity note: {msg.note}")

    await try_create_plan(ctx)


# ============================================================
# INCIDENT ASSESSMENT RESULT
# ============================================================

@coordinator.on_message(model=IncidentAssessmentReply)
async def receive_assessment_reply(
    ctx: Context,
    sender: str,
    msg: IncidentAssessmentReply,
):
    global latest_assessment_reply

    if sender != ASSESSMENT_AGENT_ADDRESS:
        ctx.logger.warning("Ignoring assessment reply from unknown sender.")
        return

    if pending_incident is None:
        ctx.logger.warning("No pending incident for assessment reply.")
        return

    latest_assessment_reply = msg

    ctx.logger.info(f"Assessment reply received from: {sender}")
    ctx.logger.info(f"Input valid: {msg.input_valid}")
    ctx.logger.info(f"Workload band: {msg.workload_band}")
    ctx.logger.info(f"Explanation: {msg.explanation}")
    ctx.logger.info(
        f"Human review required: {msg.human_review_required}"
    )

    await try_create_plan(ctx)


# ============================================================
# PLANNING DISPATCH
# ============================================================

async def try_create_plan(ctx: Context):
    global planning_request_sent

    if pending_incident is None:
        return

    if latest_capacity_reply is None:
        ctx.logger.info("Waiting for capacity result.")
        return

    if latest_assessment_reply is None:
        ctx.logger.info("Waiting for assessment result.")
        return

    if planning_request_sent:
        return

    if (
        latest_capacity_reply.status != "CALCULATED"
        or latest_capacity_reply.available_beds < 0
        or not latest_assessment_reply.input_valid
        or not latest_assessment_reply.human_review_required
    ):
        ctx.logger.warning(
            "Planning blocked: specialist results require review."
        )
        return

    request = PlanningRequest(
        incident_type=pending_incident.incident_type,
        estimated_patients=pending_incident.estimated_patients,
        arrival_minutes=pending_incident.arrival_minutes,
        available_beds=latest_capacity_reply.available_beds,
        workload_band=latest_assessment_reply.workload_band,
    )

    try:
        await ctx.send(PLANNING_AGENT_ADDRESS, request)
        planning_request_sent = True
        ctx.logger.info(
            "Both specialist results received. Planning request sent."
        )
    except Exception as exc:
        ctx.logger.error(f"Planning request failed: {exc}")


# ============================================================
# PLANNING RESULT
# ============================================================

@coordinator.on_message(model=PlanningReply)
async def receive_planning_reply(
    ctx: Context,
    sender: str,
    msg: PlanningReply,
):
    if sender != PLANNING_AGENT_ADDRESS:
        ctx.logger.warning("Ignoring planning reply from unknown sender.")
        return

    ctx.logger.info(f"Planning reply received from: {sender}")
    ctx.logger.info(f"Planning status: {msg.planning_status}")
    ctx.logger.info(f"Planning summary: {msg.summary}")

    for action in msg.recommended_actions:
        ctx.logger.info(f"Suggested action: {action}")

    ctx.logger.info(
        f"Human approval required: {msg.human_approval_required}"
    )


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":
    coordinator.run()
