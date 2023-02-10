from time import sleep

import uuid

from fw_test.context import Context
from fw_test.io import LedColor
from fw_test.wifi import ApConfiguration, WifiSecurityType


TEST_SSID = "TEST-NETWORK"
TEST_PASSPHRASE = "test-network-passphrase"


def test_factory_reset(ctx: Context):
    
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

    # ora stoppo l'access-point
    ctx.wifi.stop_ap()

    # attendo 5 secondi
    sleep(5)

    # ora posso fare l'hard reset 
    ctx.io.hard_reset()

    sleep(1)

    # il LED indica dispositivo resettato
    assert ctx.io.status_led_color() == LedColor.RED

