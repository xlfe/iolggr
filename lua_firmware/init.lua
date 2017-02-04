now_start = tmr.now()

bme280.init(4, 5)

--P air pressure hectopascals x 1000
--T temperature celsius x 100

wifi.setmode(wifi.STATION)
dofile("wifi.lua")
wifi.sta.autoconnect(1)

function set_baro()
 _G.BARO, _G.TEMP = bme280.baro()
 print(_G.TEMP)
 print(_G.BARO)
end

tmr.alarm(1,150,0,set_baro)

function dsleep(seconds)
    node.dsleep(seconds * 1000000)
end

function up_ms()
    return (tmr.now() - now_start) / 1000
end

function send_temp()
    _G.MAC = string.format("%x%x", node.flashid(), node.chipid())

    conn = net.createConnection(net.TCP, 0)

    conn:on("disconnection", function(s, e)
        print("Disconnected")
        dsleep(5*60)
    end)

    conn:on("connection", function(s, e)
        print("TCP Connected")
        local tos = "mac=" .. _G.MAC .. "\ntemp=" .. _G.TEMP .. "\nbaro=" .. _G.BARO .. "\nup=" .. up_ms()
        s:send(tos)
    end
    )

    conn:connect(7654, '10.0.0.42')
end

wifi.sta.eventMonReg(wifi.STA_CONNECTING, function()
    print("CONNECTING")
end)

wifi.sta.eventMonReg(wifi.STA_FAIL, function()
    print("CONNECT_FAIL")
    dsleep(5*60)
end)

wifi.sta.eventMonReg(wifi.STA_GOTIP, function()
    wifi.sta.eventMonStop()
    print("GOT_IP")
    send_temp()
end)

wifi.sta.eventMonStart(75)
