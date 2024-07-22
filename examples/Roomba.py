def Roomba():
    for _, A in LoopSignalMatch("v_droppeditem"):
        P1 = SelectNearest(A, P1)
    if CheckSpaceForItem(P1):
        PickUpItems(P1)
    else:
        P2 = _
        for B, _ in LoopSignalMatch("v_color_green"):
            P2 = SelectNearest(B, P2)
        DropOffItems(P2)