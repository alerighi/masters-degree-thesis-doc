def test_downgrade(ctx: Context):
    # quando il dispositivo è resettato i LED devono essere rossi
    assert ctx.io.get_led_color() == LedColor.RED

    # connette il Raspberry all'AP del radiatore elettrico
    ctx.wifi.client_connect()

    # invio aun aggiornamento firmware locale
    response = ctx.wifi.local_send_firmware_update(ctx.config.prev_firmware_path)

    assert response == 200

    # attendo che il dispositivo si riavvii
    sleep(2)

    # mi ricollego al radiatore     
    ctx.wifi.client_connect()

    response = ctx.wifi.local_get_status()

    # controllo che la versione firmware sia quella inviata
    assert response.json()['system']['fwVer'] == ctx.config.prev_firmware_version

