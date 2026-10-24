
from uagents import Agent, Context, Model, Protocol



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


planning_agent = Agent(
    name="traumaflow_planning_agent",
    seed="traumaflow-planning-development-seed-change-before-deployment",
    port=8004,
    endpoint=["http://127.0.0.1:8004/submit"],
)


@planning_agent.on_event("startup")
async def startup(ctx: Context):
    ctx.logger.info("TraumaFlow Planning Agent started.")
    ctx.logger.info("Simulation-only coordination planning.")
    ctx.logger.info("Human approval is required for all actions.")


@planning_agent.on_message(model=PlanningRequest)
async def create_plan(
    ctx: Context,
    sender: str,
    msg: PlanningRequest,
):
    valid = (
        bool(msg.incident_type.strip())
        and msg.estimated_patients > 0
        and msg.arrival_minutes > 0
        and msg.available_beds >= 0
        and bool(msg.workload_band.strip())
    )

    if not valid:
        reply = PlanningReply(
            incident_type=msg.incident_type,
            planning_status="INVALID_INPUT",
            summary="The simulation input requires correction.",
            recommended_actions=[
                "Verify the supplied values.",
                "Request human review before proceeding.",
            ],
            human_approval_required=True,
        )
    else:
        actions = [
            "Have an authorized human verify the incident report.",
            "Confirm capacity information with the appropriate authority.",
            "Review the simulated workload assessment.",
            "Document decisions and their rationale.",
        ]

        if msg.available_beds == 0:
            actions.append(
                "Escalate the capacity discrepancy for human review."
            )
        elif msg.available_beds < msg.estimated_patients:
            actions.append(
                "Ask an authorized coordinator to review the "
                "difference between simulated arrivals and available beds."
            )

        reply = PlanningReply(
            incident_type=msg.incident_type,
            planning_status="SIMULATION_PLAN_READY",
            summary=(
                f"{msg.estimated_patients} estimated arrivals in "
                f"{msg.arrival_minutes} minutes; "
                f"{msg.available_beds} fictional available beds; "
                f"workload band: {msg.workload_band}."
            ),
            recommended_actions=actions,
            human_approval_required=True,
        )

    await ctx.send(sender, reply)
    ctx.logger.info(f"Planning response sent: {reply}")


if __name__ == "__main__":
    planning_agent.run()
