import tcod as libtcod


class BasicMonster:
    def take_turn(self, target, fov_map, game_map, entities):
        results = []

        # print('The ' + self.owner.name + ' wonders when it will get to move.')
        monster = self.owner
        if libtcod.map_is_in_fov(fov_map, monster.x, monster.y):

            if monster.distance_to(target) >= 2:
                # monster.move_towards(target.x, target.y, game_map, entities)
                monster.move_astar(target, entities, game_map)
            elif target.fighter.hp > 0:
                # print('The {0} insults you! E-MO-TIONAL DAMAGE!!'.format(monster.name))
                # monster.fighter.attack(target)
                attack_results = monster.fighter.attack(target)
                results.extend(attack_results)

        return results
