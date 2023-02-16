from time import sleep, time

import uuid

from fw_test.context import Context
from fw_test.io import LedColor
from fw_test.cloud import Action, Message, Response

from .utils import TEST_AP_CONFIG, STATE_MANUAL

def test_factory_reset_offline(ctx: Context):
    
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

    # ora stoppo l'access-point
    ctx.wifi.stop_ap()

    # attendo 5 secondi
    sleep(5)

    # ora posso fare l'hard reset 
    ctx.io.hard_reset()

    sleep(1)

    # il LED indica dispositivo resettato
    assert ctx.io.status_led_color() == LedColor.RED

