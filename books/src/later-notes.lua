-- The "Later:" and "Corrected" notes in the essays are blockquotes that start with those words in
-- bold. Turn them into <div class="later"> so the books can set them apart from quotations.
local MARKERS = { "Later:", "Corrected", "Később:", "Javítva" }

local function is_note(bq)
  local first = bq.content[1]
  if not first or first.t ~= "Para" then return false end
  local lead = first.content[1]
  if not lead or lead.t ~= "Strong" then return false end
  local text = pandoc.utils.stringify(lead)
  for _, m in ipairs(MARKERS) do
    if text:sub(1, #m) == m then return true end
  end
  return false
end

function BlockQuote(bq)
  if is_note(bq) then
    return pandoc.Div(bq.content, pandoc.Attr("", { "later" }))
  end
end
