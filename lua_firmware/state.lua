--unable to connect to wifi - reboot into config mode?
if s.wifi_attempts > 50 then
    s.wifi_attempts = 48
    s.mode = 0
    set_vars()
    file.reset() --Reset system config...
end
if s.mode == 1 then
    print("Run mode..\n")
    s.wifi_attempts = s.wifi_attempts + 1
    function up_ms() return (tmr.now() - now_start) / 1000 end
    wifi_stats = "\r\n"
    wifi.setmode(wifi.STATION)
    wifi.sta.config(s.ssid, s.pass)
    wifi.sta.getap(function(t)
        for k, v in pairs(t) do
            if k == s.ssid then
                wifi_stats = "\r\nX-Mode: " .. wifi.getmode() .. "\r\nX-Stats:" .. v
            end
        end
    end)
    dofile("run.lua")
    tmr.alarm(0, 500, 1, function()
        bmp.init(4, 5)
        tmr.stop(0)
        tmr.alarm(0, 1000, 1, check_conn)
    end)
    tmr.alarm(3, 20000, 0, function() do_r(s.mins_sleep*60) end)
else
    print("MODE: Config")
    dofile("config.lua")
    tmr.alarm(0, 5000, 1, function() bmp.blink(2) end)
end
print("SDone")
