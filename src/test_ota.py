from time import sleep, time
import uuid

from fw_test.context import Context
from fw_test.io import LedColor
from fw_test.cloud import JobState, Action, Message, Response
from fw_test.firmware import FirmwareVersion

from .utils import TEST_AP_CONFIG, STATE_MANUAL


def test_ota(ctx: Context):
    # avvio la connessione del Raspberry all'AP
    ctx.wifi.client_connect()

    sleep(1)

    # invio la richiesta provision

    env_id = uuid.uuid4()
    response = ctx.api.provision(TEST_AP_CONFIG, env_id)
    assert response["status"] == "success"

    # communto la raspberry in AP mode
    ctx.wifi.start_ap(TEST_AP_CONFIG)

    # attendo che il pairing abbia successo 
    msg = ctx.cloud.receive(timeout=30)
    assert msg.action == Action.GET

    ctx.cloud.publish(Message(
        action=Action.GET,
        response=Response.ACCEPTED,
        state={
            **STATE_MANUAL,
            "clientToken": msg.state["clientToken"],
            "timestamp": int(time()),
            "envId": env_id.bytes,
        }
    ))
    sleep(1)

    assert ctx.io.status_led_color() == LedColor.OFF

    job = ctx.cloud.send_ota(ctx.prev_firmware)

    # attendo che il dispositivo esegua il job e si ricolleghi
    ctx.cloud.receive(timeout=30, filter_action=Action.GET)
    ctx.cloud.publish(Message(
        action=Action.GET,
        response=Response.ACCEPTED,
        state={
            **STATE_MANUAL,
            "clientToken": msg.state["clientToken"],
            "timestamp": int(time()),
            "envId": env_id.bytes,
        }
    ))

    # su cloud arriva la nuova versione 
    msg = ctx.cloud.receive(timeout=30)
    assert msg.action == Action.REPORTED_UPDATE

    # la versione firmware deve corrispondere a quella in test
    assert msg.state["firmwareVersion"][0] == ctx.prev_firmware.version.major
    assert msg.state["firmwareVersion"][1] == ctx.prev_firmware.version.minor

    # il job ha avuto successo
    assert ctx.cloud.job_state(job) == JobState.SUCCEEDED
