def RadarTower(enemy, damaged, dropped, construction, coordinates, acknowledged):
    enemy = GetClosestEntity("v_enemy_faction")
    if Distance(enemy)<19:
        Signal = enemy
    else:
        damaged = GetClosestEntity("v_damaged", "v_own_faction")
        if Distance(damaged)<12:
            Signal = damaged
        else:
            dropped = GetClosestEntity("v_droppeditem", "v_in_powergrid")
            if Distance(dropped)<12:
                Signal = dropped
            else:
                construction = GetClosestEntity("v_construction")
                if Distance(construction)<12:
                    Signal = construction
                else:
                    if acknowledged == 0:
                        Signal = "c_small_relay"
                        WaiTicks(10)
                        self = GetSelf()
                        for _, signal in LoopSignalMatch(self):
                            acknowledged = 1
                        
                    else: 
                        Signal = _
    coordinates = GetLocation(Signal)