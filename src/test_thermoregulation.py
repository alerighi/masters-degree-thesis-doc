from time import sleep, time
import uuid

from fw_test.context import Context
from fw_test.io import LedColor
from fw_test.cloud import Message, Response, Action
from fw_test.cloud.state import SYSTEM_STATUS_HEATING, SYSTEM_STATUS_LOAD_ACTIVE

from .utils import STATE_MANUAL, TEST_AP_CONFIG


START_SET_POINT = 60
SET_POINT_INCREMENT = 20

def test_thermoregulation(ctx: Context):
    # avvio la connessione del Raspberry all'AP
    ctx.wifi.client_connect()

    sleep(1)

    # invio la richiesta provision
    env_id = uuid.uuid4()
    response = ctx.api.provision(TEST_AP_CONFIG, env_id)
    assert response["status"] == "success"

    # communto la raspberry in AP mode
    ctx.wifi.start_ap(TEST_AP_CONFIG)

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
            "manualSetPoint": START_SET_POINT
        }
    ))

    sleep(1)

    assert ctx.io.status_led_color() == LedColor.OFF
    assert not ctx.io.is_load_active() 

    ctx.cloud.flush()

    for _ in range(SET_POINT_INCREMENT + 1):
        ctx.io.press_plus()
        sleep(0.1)

    # i LED sono rossi
    assert ctx.io.status_led_color() == LedColor.RED

    # il radiatore deve scalare ora
    assert ctx.io.is_load_active() 

    msg = ctx.cloud.receive(timeout=5)
    assert msg.action == Action.REPORTED_UPDATE
    assert msg.state["manualSetPoint"] == START_SET_POINT + SET_POINT_INCREMENT * 5
    assert msg.state["systemStatus"] & SYSTEM_STATUS_HEATING != 0
    assert msg.state["systemStatus"] & SYSTEM_STATUS_LOAD_ACTIVE != 0

    # attendo che la tastiera si spenga
    sleep(5)
    assert ctx.io.status_led_color() == LedColor.OFF

    for _ in range(SET_POINT_INCREMENT + 1):
        ctx.io.press_minus()
        sleep(0.1)

    # i LED sono azzurri
    assert ctx.io.status_led_color() == LedColor.CYAN

    # il radiatore non deve più scaldare
    assert not ctx.io.is_load_active()

    msg = ctx.cloud.receive(timeout=5)
    assert msg.action == Action.REPORTED_UPDATE
    assert msg.state["manualSetPoint"] == START_SET_POINT
    assert msg.state["systemStatus"] & SYSTEM_STATUS_HEATING == 0
    assert msg.state["systemStatus"] & SYSTEM_STATUS_LOAD_ACTIVE == 0

