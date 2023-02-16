from time import sleep

from fw_test.context import Context 
from fw_test.firmware import FirmwareVersion


def test_downgrade(ctx: Context):
    # connette il Raspberry all'AP del radiatore elettrico
    ctx.wifi.client_connect()

    sleep(2)

    # invio aun aggiornamento firmware locale
    response = ctx.api.firmware_update(ctx.prev_firmware)
    assert response.status_code == 200

    # attendo che il dispositivo si riavvii
    sleep(2)

    # mi ricollego al radiatore     
    ctx.wifi.client_connect()

    sleep(2)

    status = ctx.api.status()

    # controllo che la versione firmware sia quella inviata
    assert FirmwareVersion.from_str(status['system']['fwVer']) == ctx.prev_firmware.version
