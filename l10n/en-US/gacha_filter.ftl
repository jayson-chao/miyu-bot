too-many-results = Too Many Results

info = Information
info-desc =
    Start: { $start-date }
    End: { $end-date }
    Event: { $event-name }
    Pity Requirement: { $pity-requirement ->
        [None] { none }
       *[other] { $pity-requirement }
    }
    Type: { gacha-type }

gacha-type = { $gacha-type ->
    [Normal] Normal
    [Tutorial] Tutorial
    [Event] Event
    [Birthday] Birthday
    [Special] Special
    [Revival] Revival
   *[other] -> Unknown
}

summary = Summary
featured = Featured
featured-text = { $featured-text ->
    [None] { none }
   *[other] { $featured-text }
}

too-many = Too many
none-or-too-many = None or too many

costs = Costs
draw-cost-desc = { $pull-count } Pull: { $draw-cost }x { draw-item-name }
limit-draw-cost-desc = { draw-cost-desc }, Limit: { $draw-limit }, Refresh: { $refresh ->
    [0] { no }
   *[1] { yes }
}

draw-item-name = { $draw-item-name ->
    [diamond] Diamond
    [paid-diamond] Paid Diamond
    [single-ticket] Single Pull Ticket
    [ten-pull-ticket] Ten Pull Ticket
    [four-star-ticket] 4★ Ticket
   *[other] { $draw-item-name }
}

gacha-id = Gacha Id: { $gacha-id }

gacha-search = Gacha Search
