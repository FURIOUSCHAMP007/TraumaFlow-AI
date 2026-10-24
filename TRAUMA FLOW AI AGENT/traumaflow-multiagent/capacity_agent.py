
from uagents import Agent, Context, Model, Protocol



class CapacityRequest(Model):
    hospital_name: str
    staffed_beds: int
    occupied_beds: int


class CapacityReply(Model):
    hospital_name: str
    available_beds: int
    status: str
    note: str


capacity_agent = Agent(
    name="traumaflow_capacity_agent",
    seed="traumaflow-capacity-development-seed-change-before-deployment",
    port=8001,
    endpoint=["http://127.0.0.1:8001/submit"],
)


@capacity_agent.on_event("startup")
async def startup(ctx: Context):
    ctx.logger.info("TraumaFlow Capacity Agent started.")
    ctx.logger.info("Using fictional hospital capacity data only.")


@capacity_agent.on_message(model=CapacityRequest)
async def assess_capacity(
    ctx: Context,
    sender: str,
    msg: CapacityRequest,
):
    ctx.logger.info(f"Received capacity request for {msg.hospital_name}")

    if msg.staffed_beds < 0 or msg.occupied_beds < 0:
        reply = CapacityReply(
            hospital_name=msg.hospital_name,
            available_beds=0,
            status="INVALID_DATA",
            note="Bed counts cannot be negative.",
        )
    elif msg.occupied_beds > msg.staffed_beds:
        reply = CapacityReply(
            hospital_name=msg.hospital_name,
            available_beds=0,
            status="INVALID_DATA",
            note="Occupied beds exceed staffed beds.",
        )
    else:
        available = msg.staffed_beds - msg.occupied_beds

        reply = CapacityReply(
            hospital_name=msg.hospital_name,
            available_beds=available,
            status="CALCULATED",
            note="Fictional simulation; verify all data before use.",
        )

    await ctx.send(sender, reply)
    ctx.logger.info(f"Capacity response sent: {reply}")


if __name__ == "__main__":
    capacity_agent.run()
