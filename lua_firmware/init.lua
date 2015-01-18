now_start = tmr.now()
--Load config, etc
dofile("variables.lua")
--Figure out what to do

function do_r(seconds)
    set_vars(s)
    if seconds == 0 or seconds == nil then
        node.restart()
    else
        node.dsleep(seconds * 1000000)
    end
end
dofile("state.lua")
print("XLFE Temp/wifi logger Started - Heap:"..node.heap())