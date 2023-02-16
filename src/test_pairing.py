from time import time, sleep
from logging import getLogger

import uuid

from fw_test.context import Context
from fw_test.wifi import ApConfiguration, WifiSecurityType
from fw_test.cloud import Message, Action, Response, PacketType
from fw_test.firmware import FirmwareVersion

LOGGER = getLogger(__name__)

TEST_SSID = "TEST-NETWORK"
TEST_PASSPHRASE = "test-network-passphrase"


def test_pairing(ctx: Context):
    # avvio la connessione del Raspberry all'AP
    ctx.wifi.client_connect()

    sleep(1)

    # chiedo lo stato al dispositivo
    response = ctx.api.status()

    # mi assicuro che la versione firmware del dispositivo sia quella da testare
    assert FirmwareVersion.from_str(response["system"]["fwVer"]) == ctx.firmware.version

    # effettuo la scansione Wi-Fi
    response = ctx.api.wifi_scan()

    # mi assicuro che la scan restituisca almeno una rete
    assert len(response) > 0

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

    # attendo il primo messaggio su cloud
    msg = ctx.cloud.receive(timeout=60)
    assert msg.action == Action.GET

    # invio una GET rejected al dispositivo device
    ctx.cloud.publish(Message(
        action=Action.GET,
        response=Response.REJECTED,
        state={
            "clientToken": msg.state["clientToken"],
            "timestamp": int(time()),
            "version": 0,
            "type": PacketType.HEADER,
        }
    ))

    # mi aspetto ora un reported update
    msg = ctx.cloud.receive(timeout=5)
    assert msg.action == Action.REPORTED_UPDATE

    # la versione iniziale deve essere zero
    assert msg.state["version"] == 0

    # il system id deve essere uguale all'env id
    assert msg.state["envId"] == env_id.bytes

    # la versione firmware deve corrispondere a quella in test
    assert msg.state["firmwareVersion"][0] == ctx.firmware.version.major
    assert msg.state["firmwareVersion"][1] == ctx.firmware.version.minor
