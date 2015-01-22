now_start = tmr.now()
wifi.sleeptype(0) -- 0=NONE_SLEEP_T, 1 =LIGHT_SLEEP_T, 2 = MODEM_SLEEP_T
dofile("variables.lua")
function do_r(seconds)
    set_vars()
    if seconds == 0 or seconds == nil then
        node.restart()
    else
        node.dsleep(seconds * 1000000)
    end
end
dofile("state.lua")
print("XLFE Temp/wifi logger Started - Heap:"..node.heap())