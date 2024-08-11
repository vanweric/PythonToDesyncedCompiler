def Roomba(target, potential):
    '''
    Picks up items from the ground and returns them to recycling centers.
    Recycling centers are setup to broadcast GREEN ("v_color_green") when they have space for more items.
    Uses the Radar Tower network to find dropped items "over the horizon".
    '''
    target = _
    for potential in LoopEntitiesRange(12, "v_droppeditem"):
        target = SelectNearest(potential, target)
    # If local vision didn't find anything try the Radar Towers
    if not Match(target, "v_droppeditem"):
        for _, potential in LoopSignalMatch("v_droppeditem"):
            target = SelectNearest(potential, P1)
    if CheckSpaceForItem(P1):
        PickUpItems(P1)
    else:
        P2 = _
        for B, _ in LoopSignalMatch("v_color_green"):
            P2 = SelectNearest(B, P2)
        DropOffItems(P2)