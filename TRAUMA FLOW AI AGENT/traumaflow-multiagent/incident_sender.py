
import asyncio
from uagents import Agent, Context, Model, Protocol



COORDINATOR_ADDRESS = (
    "agent1q2dsqx3azys7szepktvs0q500svgj3pulspa5v6j2splakru62wncnsvvtf"
)


class IncidentReport(Model):
    incident_type: str
    estimated_patients: int
    arrival_minutes: int


sender_agent = Agent(
    name="traumaflow_incident_sender",
    seed="traumaflow-incident-sender-development-seed-change-before-deployment",
    port=8002,
    endpoint=["http://127.0.0.1:8002/submit"],
)


@sender_agent.on_event("startup")
async def send_test_incident(ctx: Context):
    ctx.logger.info("Preparing fictional incident report.")

    report = IncidentReport(
        incident_type="SIMULATED_MASS_CASUALTY",
        estimated_patients=12,
        arrival_minutes=20,
    )

    try:
        await ctx.send(COORDINATOR_ADDRESS, report)
        ctx.logger.info("Incident report submitted to coordinator.")
    except Exception as exc:
        ctx.logger.error(f"Could not submit incident report: {exc}")


if __name__ == "__main__":
    sender_agent.run()
