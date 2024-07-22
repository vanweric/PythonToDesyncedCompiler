def RecycleHub():
    WaitTicks(5)
    for A,_ in LoopEntitiesRange(10, "v_construction"):
        for B in LoopRecipeIngredients(A):
            OrderTransferTo(A,B)
    OrderToSharedStorage()
    if CheckSpaceForItem("c_radio_receiver"):
        Signal = "v_color_green"
    else:
        Signal = _