import random
ENEMY_BULLET = "`"
LASER = "|"
ROCKET = "@"
ROCKET_RADIUS = 5
ROCKET_DAMAGE_SCORE = 20
EXPLOSION_DURATION = 5 # Frames
class Bullet_types():
    def shooting(alive, frame, enemy_bullets,level):
        if alive and frame % max(2, 10 - level) == 0:
            enemy = random.choice(alive)
            enemy_bullets.append([
                enemy[1] + 1,
                enemy[0] + 1,
            ])
    def explosions(frame,):
        remaining_rockets = [] 
        
        for rocket in rockets:
            rocket[0] -= 2
            rocket_y, rocket_x = rocket
            hit = False
        
            # A rocket detonates when it reaches an enemy.
            for enemy in alive_enemies():
                enemy_x, enemy_y, _ = enemy
        
                if (
                    abs(rocket_y - enemy_y) <= 1
                    and enemy_x <= rocket_x < enemy_x + len(ENEMY)
                ):
                    hit = True
                    break
        
            if hit:
                # Store explosion center and expiration frame.
                explosions.append([
                    rocket_x,
                    rocket_y,
                    frame + EXPLOSION_DURATION,
                ])
        
                # Damage every living enemy in the blast radius.
                for enemy in alive_enemies():
                    enemy_x, enemy_y, _ = enemy
                    enemy_center_x = enemy_x + len(ENEMY) // 2
        
                    dx = abs(enemy_center_x - rocket_x)
                    dy = abs(enemy_y - rocket_y)
        
                    # Circular blast radius.
                    if dx * dx + dy * dy <= ROCKET_RADIUS ** 2:
                        damage_enemy(
                            enemy,
                            ROCKET_DAMAGE_SCORE,
                        )
        
            elif rocket_y > 1:
                remaining_rockets.append(rocket)
        
        rockets = remaining_rockets
        
        # Remove expired explosions.
        explosions = [
            explosion for explosion in explosions
            if explosion[2] > frame
        ]

    def player_colision():
        remaining_enemy_bullets = []

        for bullet in enemy_bullets:
            bullet[0] += 1

            if (
                bullet[0] >= player_y
                and abs(bullet[1] - player_x) <= 1
            ):
                if now >= invulnerable_until:
                    lives -= 1
                    hit_until = now + 0.7
                    invulnerable_until = now + 1.2

                    if lives <= 0:
                        lives = 0
                        game_over = True

                continue

            if bullet[0] < HEIGHT - 1:
                remaining_enemy_bullets.append(bullet)