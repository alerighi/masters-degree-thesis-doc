def test_pairing(ctx: Context):
    hard_reset_procedure(ctx)

    LOGGER.info("check that the LED is fixed RED")
    assert_status_led_color(ctx, LedColor.RED)

    LOGGER.info("check that the relay is OFF")
    assert_load_state(ctx, False)

    LOGGER.info("connect to the device Wi-Fi AP")
    ctx.wifi.client_connect()

    sleep(1)

    ap_config = ApConfiguration(
        ssid=TEST_SSID,
        passphrase=TEST_PASSPHRASE,
        security_type=WifiSecurityType.WPA2,
        channel=6,
    )

    LOGGER.info("send provision request")
    env_id = str(uuid.uuid4())
    response = ctx.wifi.send_provision_request(ap_config, env_id)
    assert response.status_code == 200

    LOGGER.info("activate the device software AP")
    ctx.wifi.start_ap(ap_config)

    LOGGER.info("wait for the connection of the device to the cloud")
    msg = ctx.cloud.receive(timeout=60)
    assert msg.action == Action.GET

    # send a GET rejected to the device (we don't have current state)
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

    # the device should respond with its state with a version of 0
    msg = ctx.cloud.receive()
    assert msg.method == Action.REPORTED_UPDATE

    # initial version should always be 0
    assert msg.state["version"] == 0

    # env id is the one provided during pairing
    assert msg.state["systemId"] == env_id

    # firmware version should be the one under test
    assert_firmware_version(msg, ctx.firmware.version)