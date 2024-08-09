
def RadarTower(enemy, damaged, dropped, construction):
    enemy = GetClosestEntity("v_enemy_faction")
    if Distance(enemy)>0:
        Signal = enemy
    else:
        damaged = GetClosestEntity("v_damaged", "v_own_faction")
        if Distance(damaged)>0:
            Signal = damaged
        else:
            dropped = GetClosestEntity("v_droppeditem", "v_in_powergrid")
            if Distance(dropped)>0:
                Signal = dropped
            else:
                construction = GetClosestEntity("v_construction")
                if Distance(construction)>0:
                    Signal = construction