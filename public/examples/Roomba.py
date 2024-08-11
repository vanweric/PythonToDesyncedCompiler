def Roomba(target, potential):
    target = _
    for potential in LoopEntitiesRange(12, "v_droppeditem"):
        target = SelectNearest(potential, target)
    if not Match(target, "v_droppeditem"):
        for _, potential in LoopSignalMatch("v_droppeditem"):
        target = SelectNearest(A, P1)
    if CheckSpaceForItem(P1):
        PickUpItems(P1)
    else:
        P2 = _
        for B, _ in LoopSignalMatch("v_color_green"):
            P2 = SelectNearest(B, P2)
        DropOffItems(P2)