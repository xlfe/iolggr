function check_conn()
    if up_ms() > 20000 then
        bmp.blink(2)
        do_r(s.mins_sleep*60)
    end
    if wifi.sta.status() == 5 and wifi.sta.getip() ~= nil then
        s.conn_attempts = s.conn_attempts + 1
        tmr.stop(0)
        print("On wifi with IP")
        wifi_up = up_ms()
        conn = net.createConnection(net.TCP, 0)
        conn:connect(s.log_port, s.log_host)
        conn:on("receive", function(conn, payload)
            conn:close()
            print(payload)
            s.conn_attempts = 0
            s.wifi_attempts = 0
            print("\nSLEEP TIME")
            tmr.alarm(4, 2000, 0, function()
                bmp.glow(1, 1000)
                do_r(s.mins_sleep * 60)
            end)
        end)
        conn:on("sent", function(conn)
            print("sent\n")
        end)
        conn:on("disconnection", function(conn)
            print("disconnection\n")
        end)
        conn:on("connection", function(conn)
            print("connected")
            conn:send("POST /log HTTP/1.1" ..
                    "\r\nAccept: */*" ..
                    "\r\nContent-type: text/plain" ..
                    "\r\nCache-Control: no-cache, no-store, must-revalidate\r\nPragma: no-cache\r\nExpires: 0" ..
                    "\r\nContent-length: 0" ..
                    "\r\nUser-Agent: NodeMCU-Lua XLFE-Logger Version 1.1" ..
                    "\r\nHost: " .. s.log_host .. "\r\nX-Name: " .. s.s_name .. "\r\nX-Mac: " .. mac .. wifi_stats ..
                    "\r\nX-Log: temp=" .. t .. "&pressure=" .. p .. "&delay=" .. up_ms() .. "&w_delay=" .. wifi_up ..
                    "&w_att=" .. s.wifi_attempts .. "&c_att=" .. s.conn_attempts .. "\r\n\r\n")
        end)
    end
end
print("RLoad")
