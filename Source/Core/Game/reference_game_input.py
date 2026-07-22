"""Known game-type templates used before a Unity project is scaffolded."""

from dataclasses import dataclass
import re


@dataclass(frozen=True)
class ReferenceGameTemplate:
    key: str
    aliases: tuple[str, ...]
    display_name: str
    camera: str
    systems: tuple[str, ...]
    acceptance_signals: tuple[str, ...]


class ReferenceGameLibrary:
    """Small, explicit library. Unknown requests are rejected instead of guessed."""

    def __init__(self):
        self.templates = (
            ReferenceGameTemplate(
                "zuma_match", ("zuma", "zuma tarz", "marble shooter", "match 3 shooter"),
                "Zuma-style marble match", "orthographic_2d",
                ("marble_chain", "shooter", "projectile", "match_resolution", "score_ui", "level_completion"),
                ("chain_spawns", "projectile_fires", "matching_marbles_are_removed", "score_increases"),
            ),
            ReferenceGameTemplate(
                "platformer", ("platformer", "platform oyunu", "side scroller"),
                "2D platformer", "orthographic_side",
                ("player_movement", "jump", "platform_collision", "collectibles", "goal"),
                ("player_moves", "player_jumps", "goal_is_reachable"),
            ),
            ReferenceGameTemplate(
                "top_down_survival", ("top down survival", "survival", "hayatta kalma"),
                "Top-down survival", "orthographic_top_down",
                ("player_movement", "enemy_spawner", "health", "combat", "survival_timer"),
                ("player_moves", "enemies_spawn", "health_changes"),
            ),
            ReferenceGameTemplate(
                "endless_runner", ("endless runner", "sonsuz kosu", "runner"),
                "Endless runner", "orthographic_side",
                ("automatic_run", "jump", "obstacles", "score", "restart"),
                ("runner_moves", "obstacles_spawn", "score_increases"),
            ),
            ReferenceGameTemplate(
                "puzzle_grid", ("puzzle", "bulmaca", "grid puzzle"),
                "Grid puzzle", "orthographic_2d",
                ("grid", "input", "validation", "moves", "win_state"),
                ("grid_is_visible", "move_is_accepted", "win_state_is_reported"),
            ),
            ReferenceGameTemplate(
                "rpg_adventure", ("rpg", "role playing", "rol yapma", "macera oyunu"),
                "RPG adventure", "third_person",
                ("player_controller", "quests", "dialogue", "inventory", "combat", "save_state"),
                ("player_moves", "quest_progresses", "inventory_changes"),
            ),
            ReferenceGameTemplate(
                "first_person_shooter", ("fps", "first person shooter", "birinci sahis nisanci"),
                "First-person shooter", "first_person",
                ("first_person_controller", "weapons", "shooting", "targets", "health", "hud"),
                ("player_moves", "weapon_fires", "target_takes_damage"),
            ),
            ReferenceGameTemplate(
                "tetris_block_puzzle", ("tetris", "block puzzle", "blok bulmaca"),
                "Falling block puzzle", "orthographic_2d",
                ("grid", "falling_pieces", "rotation", "line_clear", "score", "game_over"),
                ("piece_falls", "piece_rotates", "line_clears", "score_increases"),
            ),
            ReferenceGameTemplate(
                "candy_match", ("seker patlatma", "candy crush", "candy match", "match 3"),
                "Candy match puzzle", "orthographic_2d",
                ("match_grid", "swap_input", "match_detection", "cascade", "score", "moves"),
                ("pieces_swap", "matches_clear", "cascade_resolves", "score_increases"),
            ),
            ReferenceGameTemplate(
                "tactical_hero_shooter", ("valorant", "tactical shooter", "taktik nisanci", "hero shooter"),
                "Tactical hero shooter", "first_person",
                ("round_manager", "teams", "weapons", "abilities", "objective", "economy"),
                ("round_starts", "weapon_fires", "objective_completes"),
            ),
            ReferenceGameTemplate(
                "moba_lane_arena", ("lol", "league of legends", "moba", "koridor savasi"),
                "MOBA lane arena", "isometric",
                ("hero_controller", "abilities", "minion_waves", "towers", "lanes", "victory_condition"),
                ("hero_moves", "ability_casts", "minions_spawn", "tower_takes_damage"),
            ),
            ReferenceGameTemplate(
                "subway_endless_runner", ("subway surfers", "subway surfes", "subway runner", "kosu oyunu"),
                "Three-lane endless runner", "third_person",
                ("lane_switch", "jump", "slide", "obstacle_spawner", "collectibles", "distance_score"),
                ("runner_moves", "lane_switches", "obstacles_spawn", "distance_increases"),
            ),
            ReferenceGameTemplate(
                "maze_runner", ("maze running", "maze runner", "labirent", "labirent kosu"),
                "Maze runner", "first_person",
                ("maze_generator", "player_controller", "timer", "checkpoints", "exit", "restart"),
                ("maze_generates", "player_moves", "exit_is_reachable"),
            ),
            ReferenceGameTemplate(
                "tower_defense", ("tower defense", "kule savunma", "tower defence"),
                "Tower defense", "isometric",
                ("path", "enemy_waves", "tower_placement", "targeting", "currency", "base_health"),
                ("waves_spawn", "tower_targets", "enemies_take_damage", "base_health_changes"),
            ),
            ReferenceGameTemplate(
                "turn_based_strategy", ("turn based strategy", "sira tabanli strateji", "tbs"),
                "Turn-based strategy", "isometric",
                ("grid", "turn_manager", "unit_selection", "movement_range", "combat", "victory_condition"),
                ("turn_advances", "unit_moves", "combat_resolves"),
            ),
            ReferenceGameTemplate(
                "card_battler", ("card battler", "kart oyunu", "deck builder"),
                "Card battler", "orthographic_2d",
                ("deck", "hand", "mana", "card_effects", "enemy_turn", "rewards"),
                ("cards_draw", "card_is_played", "effect_resolves"),
            ),
            ReferenceGameTemplate(
                "roguelike_dungeon", ("roguelike", "rogue like", "dungeon crawler", "zindan"),
                "Roguelike dungeon", "top_down",
                ("procedural_rooms", "player_controller", "enemies", "loot", "health", "permadeath"),
                ("rooms_generate", "player_moves", "loot_is_collected"),
            ),
            ReferenceGameTemplate(
                "farming_sim", ("farming sim", "farm game", "ciftlik oyunu", "stardew"),
                "Farming simulation", "isometric",
                ("tile_grid", "planting", "growth_timer", "harvest", "inventory", "day_cycle"),
                ("seed_plants", "crop_grows", "harvest_adds_inventory"),
            ),
            ReferenceGameTemplate(
                "city_builder", ("city builder", "sehir kurma", "city simulation"),
                "City builder", "isometric",
                ("build_grid", "placement", "resources", "population", "production", "economy"),
                ("building_places", "resources_change", "population_updates"),
            ),
            ReferenceGameTemplate(
                "arcade_racing", ("racing", "yarış", "yaris", "car game", "araba oyunu"),
                "Arcade racing", "third_person",
                ("vehicle_controller", "track", "checkpoints", "laps", "opponents", "finish"),
                ("car_accelerates", "checkpoint_passes", "lap_increments"),
            ),
            ReferenceGameTemplate(
                "flight_combat", ("flight game", "ucak oyunu", "uçak oyunu", "air combat"),
                "Flight combat", "third_person",
                ("flight_controller", "weapons", "targets", "altitude", "missions", "hud"),
                ("aircraft_moves", "weapon_fires", "target_is_destroyed"),
            ),
            ReferenceGameTemplate(
                "arena_fighter", ("fighting game", "dovus oyunu", "dövüş oyunu", "arena fighter"),
                "Arena fighter", "side_view",
                ("fighter_controller", "attacks", "combos", "block", "health", "round_manager"),
                ("fighter_moves", "attack_lands", "round_ends"),
            ),
            ReferenceGameTemplate(
                "rhythm_game", ("rhythm game", "ritim oyunu", "music game"),
                "Rhythm game", "orthographic_2d",
                ("beat_map", "note_spawner", "input_windows", "accuracy", "combo", "score"),
                ("notes_spawn", "note_hits", "combo_increases"),
            ),
            ReferenceGameTemplate(
                "stealth_infiltration", ("stealth game", "gizlilik oyunu", "infiltration"),
                "Stealth infiltration", "third_person",
                ("player_controller", "enemy_patrol", "vision_cones", "alert_state", "objectives", "hiding"),
                ("patrols_move", "detection_changes", "objective_completes"),
            ),
            ReferenceGameTemplate(
                "survival_horror", ("horror game", "korku oyunu", "survival horror"),
                "Survival horror", "first_person",
                ("exploration", "lighting", "inventory", "enemies", "health", "escape_goal"),
                ("player_explores", "inventory_changes", "escape_goal_reaches"),
            ),
        )

    def resolve(self, prompt: str) -> ReferenceGameTemplate:
        normalized = re.sub(r"\s+", " ", (prompt or "").casefold()).strip()
        for template in self.templates:
            if any(alias in normalized for alias in template.aliases):
                return template
        raise ValueError("No supported reference game type was found in the request.")
