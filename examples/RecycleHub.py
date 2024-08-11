def RecycleHub():
    '''
    Storage Minder for accepting recycled materials.
    Broadcasts GREEN if it has space to accept items.    
    '''
    WaitTicks(5)
    OrderToSharedStorage()
    # Radio Receiver is an arbitrary stack 1 item to test for space
    if CheckSpaceForItem("c_radio_receiver"):
        Signal = "v_color_green"
    else:
        Signal = _