--Setup as WIFI access point and allow the user to config the device
wifi.setmode(wifi.SOFTAP)
--wifi.setmode(wifi.STATIONAP)
wifi.ap.config({ ssid = "ESP", pwd = "ESP12345" })
wifi.sta.disconnect()
tmr.alarm(1, 1000, 0, function()
    srv = net.createServer(net.TCP, 15)
    srv:listen(80, function(conn)
        conn:on("receive", function(conn, payload)
            if payload ~= nil then
                r = payload:match("GET ([^ ]+)")
                if r ~= nil then
                    if r == "/" then
                        file.open("index.html", "r")
                        conn:send(file.read())
                        conn:send(file.read())
                        conn:send("\r\n\r\n")
                        conn:close()
                        return
                    end
                    if r:sub(0, 5) == "/save" then
                        vals = payload:sub(7)
                        t = {}
                        for k, v in vals.gmatch(vals, "(%w+)=([^& ]+)") do
                            t[k] = v
                            print(k .. " = " .. v)
                        end
                        s.mode = 1
                        s.ssid = t["0"]
                        s.pass = t["1"]
                        s.s_name = t["2"]
                        s.wifi_attempts = 49
                        conn:send("HTTP/1.1 200 OK\n\n<html<body><h3>Now trying to connect to your wifi network.</h3>")
                        conn:send("<h3><a href=\"http://iolggr.appspot.com/devices/" .. mac .. "\">View your device</a> <-- SAVE THIS LINK!</h3></body></html>")
                        conn:send("\r\n\r\n")
                        conn:close()
                        tmr.alarm(0, 5000, 0, function()
                            wifi.setmode(wifi.STATION)
                            do_r(1)
                        end)
                        return
                    end
                end
            end
            conn:send("HTTP/1.1 404 ERROR\n\n")
        end)
        --    conn:on("sent", function(conn) end)
    end)
    print("server started")
end)
print("CLoad")
