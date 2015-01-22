local _v="store.lua"
function set_vars()
    local diff=0
    for k,v in pairs(s) do
        if _s[k] ~= v then
            diff = diff + 1
        end
    end
    if diff ==0 then
        print("No change in vars")
        return
    end
    file.open(_v,"w+")
    file.writeline("s = {")
    for p,v in pairs(s) do
        if type(v) ~= "string" then
            file.writeline(p .. " = " .. v .. "," )
        else
            file.writeline(p .. " = \"" .. v .. "\",")
        end
    end
    file.writeline("}")
    file.close()
end
dofile(_v)
_s = {}
for ok, ov in pairs(s) do
    _s[ok] = ov
end
print("Config options:")
for k,v in pairs(s) do
    print(k.. " -> "..v)
end
mac=string.format("%x%x",node.flashid(),node.chipid())
print("MAC: ".. mac .."\nVdone")
