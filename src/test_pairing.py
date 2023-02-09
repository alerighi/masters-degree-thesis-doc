def test_pairing(ctx: Context):
    # quando il dispositivo è resettato i LED devono essere rossi
    assert ctx.io.get_led_color() == LedColor.RED

    # quando il dispositivo è resettato il carico non deve essere attivo
    assert ctx.io.load_state(ctx) == False

    # connette il Raspberry all'AP del radiatore elettrico
    ctx.wifi.client_connect()

    # attendo che il radiatore si avvii
    sleep(1)

    # invio al radiatore una richiesta di provisioning
    ap_config = ApConfiguration(
        ssid=TEST_SSID,
        passphrase=TEST_PASSPHRASE,
        security_type=WifiSecurityType.WPA2,
        channel=6,
    )
    env_id = str(uuid.uuid4())
    response = ctx.wifi.send_provision_request(ap_config, env_id)

    # mi assicuro che la richiesta abbia successo
    assert response.status_code == 200
    assert response.json()['status'] == 'success'

    # a questo punto il RE si sta riavviando in modalità client
    # attivo l'AP del raspberry con la configurazione mandata al radiatore
    ctx.wifi.start_ap(ap_config)

    # attendo che la comunicazione abbia successo
    # una volta che ha successo sul cloud ricevo un messaggio GET dal radiatore
    msg = ctx.cloud.receive(timeout=60)
    assert msg.action == Action.GET

    # rispondo al messaggio GET con un rejected, in quanto non c'è attualmente
    # su cloud lo stato del dispositivo 
    ctx.cloud.publish(Message(
        action=Action.GET,
        response=Response.REJECTED,
        state={
            "clientToken": msg.state["clientToken"],
            "timestamp": int(time()),
            "requestId": 0,
            "type": PacketType.HEADER,
        }
    ))

    # a questo punto il radiatore dovrebbe mandarmi una richiesta REPORTED_UPDATE
    msg = ctx.cloud.receive()
    assert msg.method == Action.REPORTED_UPDATE

    # la versione iniziale deve essere zero
    assert msg.state["version"] == 0

    # il systemdId deve corrispondere all'envId inviato prima
    assert msg.state["systemId"] == env_id

    # controllo che la versione firmware sia la stessa indicata
    assert msg.state['firmwareVersion'][0] == ctx.firmware.version.major
    assert msg.state['firmwareVersion'][1] == ctx.firmware.version.minor
    assert msg.state['firmwareVersion'][2] == ctx.firmware.version.patch
