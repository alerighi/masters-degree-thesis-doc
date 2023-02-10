from time import sleep, time
import uuid

from fw_test.context import Context
from fw_test.io import LedColor
from fw_test.cloud import Message, Response, Action
from fw_test.wifi import ApConfiguration, WifiSecurityType

from .state import STATE_MANUAL


def test_standby(ctx: Context):
    # avvio la connessione del Raspberry all'AP
    ctx.wifi.client_connect()

    sleep(1)

    # invio la richiesta provision
    ap_config = ApConfiguration(
        ssid=TEST_SSID,
        passphrase=TEST_PASSPHRASE,
        security_type=WifiSecurityType.WPA2,
        channel=6,
    )
    env_id = uuid.uuid4()
    response = ctx.api.provision(ap_config, env_id)
    assert response["status"] == "success"

    # communto la raspberry in AP mode
    ctx.wifi.start_ap(ap_config)

    # attendo che il pairing abbia successo 
    sleep(10)

    assert ctx.io.status_led_color == LedColor.OFF

    ctx.cloud.publish(Message(
        action=Action.GET,
        state={
            **STATE_MANUAL,
            "clientToken": 0,
            "timestamp": int(time()),
            "systemId": env_id.bytes(),
            "requestId": 1,
            "manualSetPoint": 200,
        }
    ))

    sleep(1)
    assert ctx.io.load_active()

    ctx.io.press_minus(6)

    assert ctx.io.status_led_color() == LedColor.MAGENTA
    assert not ctx.io.load_active()

    sleep(1)

    ctx.io.press_minus(6)

    assert ctx.io.status_led_color() != LedColor.MAGENTA
    assert ctx.io.load_active()

