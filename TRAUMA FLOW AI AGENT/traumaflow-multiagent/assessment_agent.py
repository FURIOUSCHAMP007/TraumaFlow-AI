
from uagents import Agent, Context, Model, Protocol



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


assessment_agent = Agent(
    name="traumaflow_assessment_agent",
    seed="traumaflow-assessment-development-seed-change-before-deployment",
    port=8003,
    endpoint=["http://127.0.0.1:8003/submit"],
)


@assessment_agent.on_event("startup")
async def startup(ctx: Context):
    ctx.logger.info("TraumaFlow Assessment Agent started.")
    ctx.logger.info("Simulation only; not clinical triage.")


@assessment_agent.on_message(model=IncidentAssessmentRequest)
async def assess_incident(
    ctx: Context, sender: str, msg: IncidentAssessmentRequest
):
    valid = (
        bool(msg.incident_type.strip())
        and msg.estimated_patients > 0
        and msg.arrival_minutes > 0
    )

    if not valid:
        reply = IncidentAssessmentReply(
            incident_type=msg.incident_type,
            input_valid=False,
            workload_band="NOT_ASSESSED",
            explanation="Invalid input; correct the report before assessment.",
            human_review_required=True,
        )
    else:
        if msg.estimated_patients >= 10:
            band = "HIGH_SIMULATED_WORKLOAD"
        elif msg.estimated_patients >= 5:
            band = "MODERATE_SIMULATED_WORKLOAD"
        else:
            band = "LOW_SIMULATED_WORKLOAD"

        reply = IncidentAssessmentReply(
            incident_type=msg.incident_type,
            input_valid=True,
            workload_band=band,
            explanation=(
                f"{msg.estimated_patients} estimated arrivals in "
                f"{msg.arrival_minutes} minutes; illustrative workload "
                "band only."
            ),
            human_review_required=True,
        )

    await ctx.send(sender, reply)
    ctx.logger.info(f"Assessment response sent: {reply}")


if __name__ == "__main__":
    assessment_agent.run()
