local _v="store.lua"
function set_vars()
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
print("Config options:")
for k,v in pairs(s) do
    print(k.. " -> "..v)
end
mac=string.format("%x%x",node.flashid(),node.chipid())
print("MAC: ".. mac .."\nVdone")
