from time import sleep

from fw_test.context import Context 
from fw_test.firmware import FirmwareVersion


def test_downgrade(ctx: Context):
    # connette il Raspberry all'AP del radiatore elettrico
    ctx.wifi.client_connect()

    # invio aun aggiornamento firmware locale
    response = ctx.api.firmware_update(ctx.config.prev_firmware_path)
    assert response.status_code == 200

    # attendo che il dispositivo si riavvii
    sleep(2)

    # mi ricollego al radiatore     
    ctx.wifi.client_connect()

    response = ctx.wifi.status()

    # controllo che la versione firmware sia quella inviata
    assert FirmwareVersion.from_str(["system"]["fwVer"]) == ctx.config.prev_firmware_version

