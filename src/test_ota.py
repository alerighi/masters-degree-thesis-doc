from time import sleep
import uuid

from fw_test.context import Context
from fw_test.io import LedColor, Action
from fw_test.cloud import JobState
from fw_test.wifi import ApConfiguration, WifiSecurityType
from fw_test.firmware import FirmwareVersion

TEST_SSID = "TEST-NETWORK"
TEST_PASSPHRASE = "test-network-passphrase"

def test_ota(ctx: Context):
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

    job_id = ctx.cloud.send_ota(ctx.config.prev_firmware_path)

    sleep(60)

    # il job ha avuto successo
    assert ctx.cloud.job_state(job_id) == JobState.SUCCEEDED

    # su cloud arriva la nuova versione
    # mi aspetto ora un reported update
    msg = ctx.cloud.receive(timeout=5)
    assert msg.method == Action.REPORTED_UPDATE

    # la versione firmware deve corrispondere a quella in test
    assert FirmwareVersion.from_bytes(msg.state["firmwareVersion"]) == ctx.config.prev_firmware_version
