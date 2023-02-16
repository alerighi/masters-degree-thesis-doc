from time import sleep, time
import uuid

from fw_test.context import Context
from fw_test.io import LedColor
from fw_test.cloud import Message, Response, Action, PacketType

from .utils import STATE_MANUAL, TEST_AP_CONFIG


def test_standby(ctx: Context):
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
    msg = ctx.cloud.receive(timeout=60)
    assert msg.action == Action.GET

    # invio una GET accepted al dispositivo device
    ctx.cloud.publish(Message(
        action=Action.GET,
        response=Response.ACCEPTED,
        state={
            **STATE_MANUAL,
            "clientToken": 0,
            "timestamp": int(time()),
            "envId": env_id.bytes,
            "version": 1,
            "manualSetPoint": 150,
        }
    ))

    sleep(1)

    # I led devono essere spenti
    assert ctx.io.status_led_color() == LedColor.OFF
    assert ctx.io.is_load_active()

    ctx.io.press_minus(6)

    assert ctx.io.status_led_color() == LedColor.MAGENTA
    assert not ctx.io.is_load_active()

    sleep(1)

    ctx.io.press_minus(6)

    assert ctx.io.status_led_color() != LedColor.MAGENTA
    assert ctx.io.is_load_active()

