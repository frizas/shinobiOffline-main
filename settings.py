WIDTH = 1200
HEIGHT = 900
FPS = 60
FIXED_DT = 1 / FPS
# Dados dos níveis
level_data = {
    1: {'dimensions':  (30,  23),  'num_enemies':     1, 'experience':    350},
    2: {'dimensions':  (40,  33),  'num_enemies':     2, 'experience':    150},
    3: {'dimensions':  (40,  33), 'num_enemies':      3, 'experience':   200},
    4: {'dimensions':  (40,  33),  'num_enemies':     4, 'experience':   400},
    5: {'dimensions':  (40,  33),  'num_enemies':     5, 'experience':   400},
    6: {'dimensions':  (40,  33),  'num_enemies':     7, 'experience':   500},
    7: {'dimensions':  (40,  33),  'num_enemies':     9, 'experience':   500},
    8: {'dimensions':  (40,  33), 'num_enemies':      11, 'experience':   680},
    9: {'dimensions':  (40,  33),  'num_enemies':    13, 'experience':   600},
    10: {'dimensions': (50,  33), 'num_enemies':     15, 'experience':   620},
    11: {'dimensions': (50,  33), 'num_enemies':     20, 'experience':   640},
    12: {'dimensions': (50,  33), 'num_enemies':     22, 'experience':   660},
    13: {'dimensions': (50,  33), 'num_enemies':     25, 'experience':   680},
    14: {'dimensions': (50,  33), 'num_enemies':     30, 'experience':   600},
    15: {'dimensions': (50,  33), 'num_enemies':     33, 'experience':   620},
    16: {'dimensions': (50,  33), 'num_enemies':     35, 'experience':   640},
    17: {'dimensions': (50,  33), 'num_enemies':     38, 'experience':   660},
    18: {'dimensions': (50,  33),'num_enemies':      40, 'experience':   680},
    19: {'dimensions': (50,  33), 'num_enemies':     43, 'experience':   600},
    20: {'dimensions': (60,  33), 'num_enemies':     45, 'experience':   620},
    21: {'dimensions': (60,  33), 'num_enemies':     48, 'experience':   640},
    22: {'dimensions': (60,  33), 'num_enemies':     50, 'experience':   660},
    23: {'dimensions': (60,  33), 'num_enemies':     55, 'experience':   680},
    24: {'dimensions': (60,  33), 'num_enemies':     55, 'experience':   1000},
    25: {'dimensions': (60,  33), 'num_enemies':     55, 'experience':   1020},
    26: {'dimensions': (60,  33), 'num_enemies':     55, 'experience':   1040},
    27: {'dimensions': (60,  33), 'num_enemies':     55, 'experience':   1060},
    28: {'dimensions': (60,  33), 'num_enemies':     55, 'experience':   1080},
    29: {'dimensions': (80,  33), 'num_enemies':     55, 'experience':   1000},
    30: {'dimensions': (80,  33), 'num_enemies':     55, 'experience':  1000},
} 

#arvores
tree_data = {
       # 'tree':{'overlay_path':'images/map/trees/tree.png', 'trunk_path':'images/map/trees/tree_trunk.png'},
     #   'arvore1':{'overlay_path':'images/map/trees/arvore1.png', 'trunk_path':'images/map/trees/arvore1_trunk.png'},
        'arvore2':{'overlay_path':'images/map/trees/arvore2.png', 'trunk_path':'images/map/trees/arvore2_trunk.png'},
        'arvore3':{'overlay_path':'images/map/trees/arvore3.png', 'trunk_path':'images/map/trees/arvore3_trunk.png'},
        

}



# Dados das armas
weapon_data = {
    'fist': {'damage': 4,  'cooldown': 300,'graphic': 'images/items/fist.png','type': 'melee'},
    'sword': {'damage': 20,'cooldown': 600, 'graphic': 'images/items/sword.png','type': 'melee'},
    'kunai': {'speed': 140,'cooldown': 2500, 'damage': 8, 'graphic': 'images/items/kunai.png','type': 'ranged','rotating' : False,'indestructible':False},
    'shuriken': {'speed': 150,'cooldown': 2500, 'damage': 5, 'graphic': 'images/items/shuriken.png','type': 'ranged','rotating' : True,'indestructible':False},
    'fuuma': {'speed': 110,'cooldown': 3000, 'damage': 15, 'graphic': 'images/items/fuuma.png','type': 'ranged','rotating' : True,'indestructible':True},
    'fireball': {'speed': 150, 'damage': 45, 'graphic': 'images/projectiles/fireball.png','rotating' : True,'indestructible':True},
    'poison_kunai': {'speed': 180,'cooldown': 2500, 'damage': 35, 'graphic': 'images/items/kunai.png','type': 'ranged','rotating' : False,'indestructible':False},

}

# Dados dos monstros
monster_data = {
    'Dorobou': {'hp': 200, 'speed': 40, 'graphic': 'images/monster/gordo.png', 'behavior': 'aggressive', 'vision_radius': 250, 'experience': 50,'melee_skill': 20,'defense_skill':10},
    'Hoshi': {'hp': 100, 'speed': 45, 'graphic': 'images/monster/ninja1.png', 'behavior': 'defensive', 'vision_radius': 350, 'experience': 70,'melee_skill': 5,'defense_skill':1},
    'Katsu': {'hp': 80, 'speed': 75, 'graphic': 'images/monster/ninja2.png', 'behavior': 'aggressive', 'vision_radius': 300, 'experience': 65,'melee_skill': 15,'defense_skill':8},
}
ally_data  = {
    'Aburame Assassin': {'hp': 150, 'speed': 40, 'graphic': 'images/monster/anbu1.png', 'behavior': 'defensive', 'vision_radius': 550, 'experience': 50,'melee_skill': 20,'defense_skill':10},
    'Aburame Anbu': {'hp': 100, 'speed': 45, 'graphic': 'images/monster/anbu3.png', 'behavior': 'defensive', 'vision_radius': 450, 'experience': 70,'melee_skill': 5,'defense_skill':1},
    'Unknown Assassin': {'hp': 150, 'speed': 45, 'graphic': 'images/monster/anbu2.png', 'behavior': 'defensive', 'vision_radius': 400, 'experience': 65,'melee_skill': 15,'defense_skill':8},
}
drop_data = {
    'sword': {    'graphic': 'images/items/sword.png','type': 'melee'},
    'kunai': {    'graphic': 'images/items/kunai.png','type': 'ranged'   },
    'shuriken': { 'graphic': 'images/items/shuriken.png','type': 'ranged'},
    'fuuma': {    'graphic': 'images/items/fuuma.png','type': 'ranged' },

}

sound_data = {
    'spark': ['sounds/spark1.wav', 'sounds/spark2.wav', 'sounds/spark3.wav'],
    'blood_hit': 'sounds/blood_hit.wav',
    'electric_aura': 'sounds/electric_aura.wav',
    'punch': 'sounds/punch.wav',
    'slash': 'sounds/slash.wav',
    'explosion': 'sounds/explosion.wav'
}



# Dados dos itens
item_data = {
    'potion': {'effect': 'heal', 'amount': 50, 'graphic': 'images/items/potion.png'},
    'mana_potion': {'effect': 'restore_mana', 'amount': 30, 'graphic': 'images/items/mana_potion.png'},
}

# Add this to settings.py
mission_data = {
    1: {
        'name': 'Rookie Challenge',
        'levels': [1, 2, 3],
        'gold_reward': 100
    },
    2: {
        'name': 'Forest Expedition',
        'levels': [4, 5, 6],
        'gold_reward': 200
    },
    3: {
        'name': 'Mountain Assault',
        'levels': [7, 8, 9],
        'gold_reward': 300
    },
    # Add more missions as needed
}

ninjutsu_data = {
    'Fire': {
        'Fireball Jutsu': {'mana_cost': 30, 'damage': 50},
        'Phoenix Flower Jutsu': {'mana_cost': 45, 'damage': 70},
        'Great Fire Annihilation': {'mana_cost': 80, 'damage': 120},
        'Fire Dragon Flame Bullet': {'mana_cost': 60, 'damage': 90}
    },
    'Water': {
        'Water Bullet': {'mana_cost': 25, 'damage': 40},
        'Water Dragon Jutsu': {'mana_cost': 55, 'damage': 80},
        'Giant Vortex Jutsu': {'mana_cost': 70, 'damage': 100},
        'Water Shark Bomb': {'mana_cost': 50, 'damage': 75}
    },
    'Earth': {
        'Earth Wall': {'mana_cost': 35, 'damage': 0, 'defense': 60},
        'Earth Spikes': {'mana_cost': 40, 'damage': 60},
        'Earth Flow River': {'mana_cost': 55, 'damage': 70},
        'Earth Golem': {'mana_cost': 90, 'damage': 110}
    },
    'Lightning': {
        'Chidori': {'mana_cost': 50, 'damage': 85},
        'Lightning Ball': {'mana_cost': 35, 'damage': 55},
        'Kirin': {'mana_cost': 100, 'damage': 150},
        'Lightning Beast Tracking Fang': {'mana_cost': 65, 'damage': 95}
    },
    'Wind': {
        'Wind Blade': {'mana_cost': 30, 'damage': 45},
        'Great Breakthrough': {'mana_cost': 45, 'damage': 65},
        'Rasenshuriken': {'mana_cost': 85, 'damage': 130},
        'Wind Cutter': {'mana_cost': 55, 'damage': 80}
    }
}



