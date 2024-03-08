data = {}

data.instructions={}
local instructions = require("instructions")
local json = require("dkjson")


-- Filter out function elements
local function filterFunctions(tbl)
    local filteredTable = {}
    for key, value in pairs(tbl) do
        if type(value) == "table" then
            filteredTable[key] = filterFunctions(value)
        elseif type(value) ~= "function" then
            filteredTable[key] = value
        end
    end
    return filteredTable
end


local filteredInstructions = filterFunctions(data.instructions)

local jsonStr = json.encode(filteredInstructions, { indent = true })
local file = io.open("instructions.json", "w")
file:write(jsonStr)
file:close()
