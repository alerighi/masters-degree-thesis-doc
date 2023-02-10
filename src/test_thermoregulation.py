from time import sleep, time
import uuid

from fw_test.context import Context
from fw_test.io import LedColor
from fw_test.cloud import Message, Response, Action
from fw_test.wifi import ApConfiguration, WifiSecurityType

from .state import STATE_MANUAL

TEST_SSID = "TEST-NETWORK"
TEST_PASSPHRASE = "test-network-passphrase"


def test_thermoregulation(ctx: Context):
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
            "clientToken": msg.state["clientToken"],
            "timestamp": int(time()),
            "systemId": env_id.bytes(),
            "requestId": 1,
        }
    ))

    sleep(2)
    msg = ctx.cloud.receive(timeout=5)
    assert msg.method == Action.REPORTED_UPDATE

    for _ in range(20):
        ctx.io.press_plus()
        sleep(0.5)

    sleep(1)

    # il radiatore deve scalare ora
    assert ctx.io.is_load_active() 

    msg = ctx.cloud.receive(timeout=5)
    assert msg.method == Action.REPORTED_UPDATE
    assert msg.status["heatingStatus"] != 0

    for _ in range(20):
        ctx.io.press_minus()
        sleep(0.5)

    sleep(1)

    # il radiatore non deve più scaldare
    assert not ctx.io.is_load_active()

    msg = ctx.cloud.receive(timeout=5)
    assert msg.method == Action.REPORTED_UPDATE
    assert msg.status["heatingStatus"] == 0

