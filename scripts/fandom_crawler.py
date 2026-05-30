# -*- coding: utf-8 -*-
"""
Generic Fandom (MediaWiki) narrative crawler for GamePlots.

Scope philosophy: 敘事 + 陣營機制 — select pages by category membership, skip
pure-stat / image / template pages. Each page is reduced to plain narrative
text and appended to a semantic bucket .txt under working/<work>/raw/.

Usage:
    python scripts/fandom_crawler.py <config_name>

Add new wikis by appending to CONFIGS. Each config:
    domain  : fandom subdomain host
    work    : working/<work>/raw output folder name
    buckets : ordered [(bucket_name, [category, ...]), ...]
              a page lands in the FIRST bucket whose categories it matches.
"""
import os
import re
import sys
import time
import json
import requests
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": "GamePlots-research-bot/1.0 (contact: guanyu.lu@teco.com.tw) python-requests"
}
DELAY = 0.02  # seconds between content fetches


CONFIGS = {
    "endless_legend": {
        "domain": "endlesslegend.fandom.com",
        "work": "Endless_Legend",
        "buckets": [
            # cross-cutting narrative pulled out first
            ("lore",                ["Lore"]),
            ("heroes",              ["Heroes"]),
            ("guardians",           ["Guardians"]),
            ("urkans",              ["Urkans"]),
            ("factions_overview",   ["Factions", "Major Factions",
                                     "Minor Factions"]),
            # per-faction sweep (units / buildings / faction page)
            ("faction_allayi",        ["Allayi"]),
            ("faction_ardent_mages",  ["Ardent Mages"]),
            ("faction_broken_lords",  ["Broken Lords"]),
            ("faction_cultists",      ["Cultists"]),
            ("faction_drakken",       ["Drakken"]),
            ("faction_forgotten",     ["Forgotten"]),
            ("faction_kapaku",        ["Kapaku"]),
            ("faction_mezari",        ["Mezari"]),
            ("faction_morgawr",       ["Morgawr"]),
            ("faction_mykara",        ["Mykara"]),
            ("faction_necrophages",   ["Necrophages"]),
            ("faction_roving_clans",  ["Roving Clans"]),
            ("faction_vaulters",      ["Vaulters"]),
            ("faction_wild_walkers",  ["Wild Walkers"]),
            ("traits",              ["Traits"]),
            ("units_other",         ["Units", "Cavalry Units", "Flying Units",
                                     "Infantry Units", "Naval Units",
                                     "Ranged Units", "Support Units"]),
        ],
    },
    "age_of_wonders": {
        # Classic trilogy wiki: AoW1, AoW II: The Wizard's Throne, Shadow Magic.
        "domain": "ageofwonders.fandom.com",
        "work": "Age_of_Wonders",
        "buckets": [
            ("lore",            ["Lore", "Out-of-game lore texts",
                                 "Game Concepts", "Terminology"]),
            ("story_characters",["Story characters"]),
            ("heroes",          ["Heroes"]),
            ("races",           ["Races", "Age of Wonders races",
                                 "Age of Wonders II races",
                                 "Age of Wonders: Shadow Magic races"]),
            ("factions",        ["Factions and organizations",
                                 "Kingdoms and sovereign states",
                                 "Organization"]),
            ("locations",       ["Locations"]),
            ("campaigns",       ["Campaign scenarios",
                                 "Age of Wonders campaign",
                                 "Age of Wonders campaign scenarios",
                                 "Age of Wonders II campaign scenarios",
                                 "Age of Wonders: Shadow Magic campaign",
                                 "Age of Wonders: Shadow Magic campaign scenarios",
                                 "Campaign heroes"]),
            ("creatures",       ["Dragons", "Elementals", "Creatures",
                                 "Machines", "Humanoids"]),
            ("items",           ["Items", "Age of Wonders items"]),
            # per-race units (faction mechanics)
            ("units_azrac",     ["Azrac Units"]),
            ("units_dark_elf",  ["Dark Elf Units"]),
            ("units_dwarf",     ["Dwarf Units"]),
            ("units_elf",       ["Elf Units"]),
            ("units_frostling", ["Frostling Units"]),
            ("units_goblin",    ["Goblin Units"]),
            ("units_halfling",  ["Halfling Units"]),
            ("units_highman",   ["Highman Units"]),
            ("units_human",     ["Human Units"]),
            ("units_lizardman", ["Lizardman Units"]),
            ("units_orc",       ["Orc Units"]),
            ("units_undead",    ["Undead Units"]),
            ("units_aow2",      ["Age of Wonders II units"]),
        ],
    },
    "stormlight": {
        # Brandon Sanderson novel series (not a game). "陣營機制" maps to
        # narrative entities: characters / places / orders / world concepts.
        "domain": "stormlightarchive.fandom.com",
        "work": "Stormlight_Archive",
        "buckets": [
            ("gods_heralds", ["Gods", "Heralds", "Deity"]),
            ("radiant_orders", ["Bondsmith", "Dustbringer", "Edgedancer",
                                "Elsecaller", "Lightweaver", "Releaser",
                                "Skybreaker", "Stoneward", "Truthwatcher",
                                "Willshaper", "Windrunner"]),
            ("cosmere_concepts", ["Cosmere", "Concepts", "Forms of Power",
                                  "Dawnshards", "Surges", "Investiture"]),
            ("events_eras", ["Events and Eras", "Battles"]),
            ("groups", ["Groups", "Cults", "Ghostblood"]),
            ("fabrials", ["Fabrials", "Gemstones"]),
            ("creatures", ["Creatures", "Flora and Fauna",
                           "Fauna of Roshar", "Flora of Roshar"]),
            ("places", ["Cities", "Geography", "Dawncities"]),
            ("characters", ["Characters"]),
        ],
    },
    "diablo": {
        # Huge wiki (16k+ articles) spanning D1-D4 + Immortal + novels.
        # Narrative scope ONLY: skip the 338-page Demons bestiary, item/stat
        # pages, and 21k images. Story/lore/characters/factions/places.
        "domain": "diablo.fandom.com",
        "work": "Diablo",
        "buckets": [
            ("lore", ["Lore", "Religion"]),
            ("angels", ["Angels", "Angiris Council", "Angelic orders"]),
            ("prime_evils", ["Prime Evils", "Lesser Evils"]),
            ("factions", ["Horadrim", "Barbarian Tribes", "Cults",
                          "Archmages"]),
            ("locations", ["Locations"]),
            ("nephalem", ["Nephalem"]),
            ("characters", ["Characters"]),
        ],
    },
    "malazan": {
        # Malazan Book of the Fallen (Erikson/Esslemont novels). No single
        # "Characters" cat — people are grouped by race/affiliation. Skip the
        # huge Book-covers / Fan-art / Advent-calendar image-category noise.
        "domain": "malazan.fandom.com",
        "work": "Malazan",
        "buckets": [
            ("gods_ascendants", ["Ascendants", "Elder Gods", "Gods",
                                 "Azathanai"]),
            ("faction_bridgeburners", ["Bridgeburners"]),
            ("faction_bonehunters", ["Bonehunters"]),
            ("faction_crimson_guard", ["Crimson Guard", "Avowed",
                                       "Disavowed"]),
            ("faction_claw", ["Claw"]),
            ("race_tiste", ["Tiste"]),
            ("race_tlan_imass", ["T'lan Imass", "Imass"]),
            ("race_jaghut", ["Jaghut"]),
            ("race_forkrul_assail", ["Forkrul Assail"]),
            ("race_barghast", ["Barghast"]),
            ("race_human", ["Humans", "Human"]),
            ("creatures", ["Creatures", "D'ivers", "Eleint"]),
            ("magic", ["Warrens", "Deck of Dragons", "Azath Houses"]),
            ("events", ["Battles", "Events"]),
            ("places", ["Cities", "Continents"]),
        ],
    },
    "grim_dawn": {
        # ARPG (Crate Entertainment). World "Cairn" caught between three
        # invasions: Aetherials, Chthonics, and Eldritch horrors. Narrative
        # scope only — skip 4k+ pure-stat item / blueprint / set / component /
        # bounty / consumable pages. Boss/hero creatures retained because
        # they are named NPCs with flavour text.
        "domain": "grimdawn.fandom.com",
        "work": "Grim_Dawn",
        "buckets": [
            # world/story groundwork first so shared pages land here
            ("lore", ["Lore"]),
            ("expansions", ["Ashes of Malmouth", "Forgotten Gods"]),
            # three invasion forces — narrative spine of the setting
            ("aether_invasion", ["Aetherials", "Aetherial"]),
            ("chthonic_invasion", ["Chthonics", "Bloodsworn"]),
            ("eldritch_invasion", ["Eldritch"]),
            # human factions / cults / orders
            ("factions", ["Factions", "Cronley's Gang", "Kymon's Chosen",
                          "Order of Death's Vigil", "Zealot"]),
            # class lore (mastery backstories — narrative, not skill tables)
            ("masteries", ["Masteries"]),
            # named NPCs and quest givers
            ("npcs", ["NPCs", "Quest Givers"]),
            # quests / quest items / narrative key items
            ("quests", ["Quests", "Quest Items"]),
            # named bosses / heroes / nemesis not already in invasion buckets
            ("bosses", ["Boss Creatures", "Hero Creatures", "Nemesis",
                        "Secret Boss"]),
            # locations across all acts + expansions + riftgates
            ("places", ["Locations", "Act 1 Locations", "Act 2 Locations",
                        "Act 3 Locations", "Act 4 Locations",
                        "Act 5 Locations", "Act 6 Locations",
                        "Forgotten Gods Locations", "Riftgate Locations",
                        "Secret Areas"]),
            # devotion constellations — each carries flavour text (mythic
            # figures of Cairn's faith)
            ("constellations", ["Constellations"]),
        ],
    },
    "pillars_of_eternity": {
        # Obsidian's Eora setting: Pillars of Eternity (2015) + The White
        # March I/II, Pillars of Eternity II: Deadfire (2018) + Beast of
        # Winter / Seeker, Slayer, Survivor / The Forgotten Sanctum,
        # and Avowed (2025). One shared world (Eora), one shared
        # cosmology (The Wheel, soul cycle, Engwithan-built gods).
        # Wiki has 13k+ pages but is dominated by per-game stat/equipment
        # pages — narrative scope (敘事 + 陣營機制) is ~2.5–3k. Skip the full
        # bestiary (stat-block enemies), use the small narrative
        # creatures/primordials/spirits/vessels lists instead. Skip pure
        # equipment, ability/spell trees, item-slot index cats, and
        # the per-location-character lists. "First match" routing means
        # a faction/companion/lore page never re-appears in the
        # catch-all character buckets.
        "domain": "pillarsofeternity.fandom.com",
        "work": "Pillars_of_Eternity",
        "buckets": [
            # cosmology / world / pantheon — pull broad world lore first
            ("world_lore", ["Eora", "Engwithans", "Deities", "Cultures",
                            "Countries", "Nations", "Races", "Conflicts",
                            "Aumaua", "Dwarves", "Elves", "Humans",
                            "Godlike", "Orlans", "Huana", "Rauatai",
                            "Readceras", "Vailian Republics"]),
            # named factions/orders/companies — many cross-game
            ("factions", ["Pillars of Eternity factions",
                          "Pillars of Eternity II: Deadfire factions",
                          "Avowed factions", "Factions",
                          "Knights of the Crucible",
                          "Knights of the Crucible characters",
                          "Bleak Walkers characters",
                          "Goldpact Knights characters",
                          "Kind Wayfarers characters",
                          "Leaden Key characters",
                          "Vailian Trading Company characters",
                          "Royal Deadfire Company characters",
                          "Príncipi sen Patrena characters",
                          "Principi sen Patrena characters",
                          "Huana characters",
                          "Crookspur Slavers characters",
                          "Children of the Dawnstars characters",
                          "The Defiant characters",
                          "The Dozens characters",
                          "The Fangs characters",
                          "The Steel Garrote characters",
                          "The Circle of Archmagi characters",
                          "The Shieldbearers of St. Elcga characters",
                          "Vailian Republics characters"]),
            # companions (party recruits) — narratively pivotal
            ("companions", ["Pillars of Eternity companions",
                            "Pillars of Eternity II: Deadfire companions",
                            "Avowed companions"]),
            # geography — regions, cities, dungeons, islands
            ("locations", ["Pillars of Eternity locations",
                           "Pillars of Eternity II: Deadfire locations",
                           "Avowed locations",
                           "Pillars of Eternity dungeons",
                           "Pillars of Eternity II: Deadfire dungeons",
                           "Pillars of Eternity II: Deadfire islands",
                           "Pillars of Eternity II: Deadfire cities",
                           "Pillars of Eternity II: Deadfire archipelagos",
                           "Pillars of Eternity cities",
                           "Pillars of Eternity villages",
                           "Pillars of Eternity wildernesses",
                           "Pillars of Eternity ruins",
                           "Pillars of Eternity mentioned-only locations",
                           "Avowed regions", "Avowed subregions",
                           "Avowed major cities", "Avowed dungeons",
                           "Avowed districts", "Avowed landmarks",
                           "Avowed settlements",
                           "The White March - Part I locations",
                           "The White March - Part II locations",
                           "Beast of Winter locations",
                           "The Forgotten Sanctum locations",
                           "Locations"]),
            # main + faction + expansion + side quests (skip "tasks"
            # which are usually pure fetch errands)
            ("quests", ["Pillars of Eternity main quests",
                        "Pillars of Eternity II: Deadfire main quests",
                        "Avowed main quests",
                        "Pillars of Eternity II: Deadfire faction quests",
                        "Pillars of Eternity II: Deadfire faction quests - Huana",
                        "Pillars of Eternity II: Deadfire faction quests - Príncipi",
                        "Pillars of Eternity II: Deadfire faction quests - RDC",
                        "Pillars of Eternity II: Deadfire faction quests - VTC",
                        "The White March - Part I main quests",
                        "The White March - Part II main quests",
                        "The Forgotten Sanctum main quests",
                        "Seeker, Slayer, Survivor main quests",
                        "Pillars of Eternity II: Deadfire expansion quests",
                        "Pillars of Eternity side quests",
                        "Pillars of Eternity II: Deadfire side quests",
                        "Avowed side quests"]),
            # in-world readable lore (books, letters, notes that carry
            # backstory) — the curated *lore* subset, not all docs
            ("lore_items", ["Pillars of Eternity lore items",
                            "Pillars of Eternity II: Deadfire lore items",
                            "Avowed lore documents",
                            "The White March - Part I lore items",
                            "The White March - Part II lore items",
                            "The Forgotten Sanctum lore items",
                            "Seeker, Slayer, Survivor lore items"]),
            # narrative creature lines (primordials, vessels, spirits,
            # named beasts). NOT the full 370-entry stat bestiary.
            ("creatures", ["Pillars of Eternity creatures",
                           "Pillars of Eternity II: Deadfire creatures",
                           "Pillars of Eternity vessels",
                           "Pillars of Eternity spirits",
                           "Pillars of Eternity primordials",
                           "The Forgotten Sanctum primordials",
                           "The White March - Part I creatures",
                           "The White March - Part II creatures"]),
            # per-game character catch-alls (anything not already routed
            # to factions / companions above lands here)
            ("poe1_characters", ["Pillars of Eternity characters",
                                  "The White March - Part I characters",
                                  "The White March - Part II characters",
                                  "Pillars of Eternity mentioned-only characters"]),
            ("d2_characters", ["Pillars of Eternity II: Deadfire characters",
                                "Beast of Winter characters",
                                "The Forgotten Sanctum characters"]),
            ("avowed_characters", ["Avowed characters"]),
        ],
    },
    "path_of_exile": {
        # Wraeclast / Path of Exile (Grinding Gear Games). 50k articles but
        # overwhelmingly stat/data (Mods 21k, Base items 8k, Monster data 8k).
        # Narrative scope: story acts, NPCs, named bosses/unique monsters,
        # the pantheon gods, campaign areas, quests, and the lore delivered
        # through divination cards + prophecies (PoE tells its myth through
        # flavour text). Skip base items, mods, passives, microtransactions,
        # map/hideout stat areas.
        "domain": "pathofexile.fandom.com",
        "work": "Path_of_Exile",
        "buckets": [
            ("lore", ["Lore"]),
            ("acts", ["Acts", "Act 1", "Act 2", "Act 3", "Act 4", "Act 5",
                      "Act 6", "Act 7", "Act 8", "Act 9", "Act 10"]),
            ("npcs", ["NPCs", "Act 1 NPCs", "Act 2 NPCs", "Act 3 NPCs",
                      "Act 4 NPCs", "Act 5 NPCs", "Act 6 NPCs", "Act 7 NPCs",
                      "Act 8 NPCs", "Act 9 NPCs", "Act 10 NPCs",
                      "Epilogue NPCs", "Forsaken Masters NPCs"]),
            ("pantheon", ["Pantheon Soul"]),
            ("races_classes", ["Races", "Character classes",
                               "Character Classes"]),
            ("bosses", ["Bosses", "Boss monsters", "Unique monsters",
                        "Rogue exiles", "Invasion bosses", "Beyond bosses",
                        "Map bosses", "Talisman bosses",
                        "Labyrinth unique monsters",
                        "Act 1 unique monsters", "Act 2 unique monsters",
                        "Act 3 unique monsters", "Act 4 unique monsters",
                        "Act 5 unique monsters", "Act 6 unique monsters",
                        "Act 7 unique monsters", "Act 8 unique monsters",
                        "Act 9 unique monsters", "Act 10 unique monsters"]),
            ("areas", ["Act 0 areas", "Act 1 areas", "Act 2 areas",
                       "Act 3 areas", "Act 4 areas", "Act 5 areas",
                       "Act 6 areas", "Act 7 areas", "Act 8 areas",
                       "Act 9 areas", "Act 10 areas", "Act 11 areas",
                       "Town areas", "Towns"]),
            ("quests", ["Quests", "Act 1 quests", "Act 2 quests",
                        "Act 3 quests", "Act 4 quests", "Act 5 quests",
                        "Act 6 quests", "Act 7 quests", "Act 8 quests",
                        "Act 9 quests", "Act 10 quests",
                        "Act Epilogue quests"]),
            ("divination_cards", ["Divination Card"]),
            ("prophecies", ["Prophecies"]),
        ],
    },
    "dragon_age": {
        # BioWare's Thedas: Origins (+Awakening) / DA II / Inquisition
        # (+Trespasser, Jaws of Hakkon, The Descent) / The Veilguard, plus
        # the novels/comics. 16k articles. Lore here is delivered largely
        # through Codex entries — keep them. Narrative scope: characters,
        # companions, codex lore, groups/nations/religion, creatures,
        # locations, quests. Skip weapons/armour/schematics/items/runes/
        # crafting/war-table-operation stat pages.
        "domain": "dragonage.fandom.com",
        "work": "Dragon_Age",
        "buckets": [
            ("lore_codex", ["Codex: Lore", "Codex: History",
                            "Codex: Culture and History", "Codex: Tales",
                            "Codex: The World of Thedas", "Codex: Magic",
                            "Codex: Magic and Religion", "Codex: Groups",
                            "Codex: Characters (Origins)",
                            "Codex: Characters (Dragon Age II)",
                            "Codex: Characters (Inquisition)",
                            "Codex: Creatures", "Codex: Creatures (Inquisition)",
                            "Codex: Creatures (Dragon Age II)",
                            "Codex: Places", "Codex: Places (Inquisition)",
                            "Codex: The Elven People", "Codex: The Dwarven People",
                            "Codex: The Grey Wardens", "Codex: Books and Songs",
                            "Codex: Letters & Notes", "Codex: Letters and Notes",
                            "Codex: Notes", "Codex: Mementos",
                            "Codex: The Shadow Dragons", "Codex: The Mourn Watch",
                            "Codex: The Antivan Crows", "Codex: The Lords of Fortune",
                            "Codex: Art of War", "Codex: Miscellaneous"]),
            ("world_lore", ["Lore", "Dwarven lore", "Elven lore", "Human lore",
                            "Chantry lore", "Fade lore", "Qunari lore",
                            "Grey Warden lore", "Darkspawn lore", "Dalish lore",
                            "Ancient elven lore", "Avvar lore", "Chasind lore",
                            "City elf lore", "Dragon lore", "Specialization lore",
                            "Circle of Magi lore", "Fereldan folklore",
                            "Orlesian folklore", "Religion", "Old Gods",
                            "Nations", "Races", "Groups", "Dwarven groups",
                            "Dwarven houses", "History", "Historical characters"]),
            ("companions", ["Companions",
                            "Dragon Age: Origins companions",
                            "Dragon Age: Origins - Awakening companions",
                            "Dragon Age II companions",
                            "Dragon Age: Inquisition companions",
                            "Dragon Age: The Veilguard companions",
                            "Temporary companions", "Playable characters"]),
            ("creatures", ["Creatures", "Darkspawn", "Spirits", "Abominations",
                           "Possessed creatures", "Grey Wardens",
                           "Dragon Age: Origins creatures",
                           "Dragon Age: Origins - Awakening creatures",
                           "Dragon Age II creatures",
                           "Dragon Age: Inquisition creatures",
                           "Dragon Age: The Veilguard creatures"]),
            ("locations", ["Locations",
                           "Dragon Age: Origins locations",
                           "Dragon Age: Origins - Awakening locations",
                           "Dragon Age II locations",
                           "Dragon Age: Inquisition locations",
                           "Dragon Age: The Veilguard locations",
                           "Kirkwall locations", "Denerim locations",
                           "Orzammar locations"]),
            ("quests", ["Dragon Age: Origins quests",
                        "Dragon Age: Origins side quests",
                        "Dragon Age: Origins companion quests",
                        "Dragon Age II main quests",
                        "Dragon Age II companion quests",
                        "Dragon Age: Inquisition main quests",
                        "Dragon Age: Inquisition companion quests",
                        "Dragon Age: The Veilguard main quests",
                        "Dragon Age: The Veilguard companion quests",
                        "Origin story quests"]),
            ("characters_origins", ["Dragon Age: Origins characters",
                                    "Dragon Age: Origins - Awakening characters"]),
            ("characters_da2", ["Dragon Age II characters"]),
            ("characters_inquisition", ["Dragon Age: Inquisition characters",
                                        "Trespasser characters",
                                        "Jaws of Hakkon characters"]),
            ("characters_veilguard", ["Dragon Age: The Veilguard characters"]),
            ("characters_other", ["Characters", "Dragon Age: Tevinter Nights characters",
                                  "Dragon Age: The Masked Empire characters",
                                  "Dragon Age: The Stolen Throne characters",
                                  "Dragon Age: The Calling characters",
                                  "Dragon Age: Asunder characters",
                                  "Dragon Age: Last Flight characters"]),
        ],
    },
    "guild_wars_2": {
        # OFFICIAL wiki (wiki.guildwars2.com) — the fandom GW2 wiki is a
        # 117-article stub. 124k articles here, dominated by 14k+ generic
        # "Normal NPCs" and item/event pages. Narrative scope: the story
        # arcs (Personal Story + every Living World / expansion story),
        # the named Story characters, Tyrian lore (gods, Elder Dragons,
        # races, cultures, lore books), the Orders, and Legendary NPCs.
        # Skip generic NPCs, events, items, skins, achievements, maps.
        "domain": "wiki.guildwars2.com",
        "work": "Guild_Wars_2",
        "buckets": [
            ("story", ["Personal story",
                       "Living World Season 1 story",
                       "Living World Season 2 story",
                       "Living World Season 3 story",
                       "Living World Season 4 story",
                       "The Icebrood Saga story",
                       "Heart of Thorns story", "Path of Fire story",
                       "End of Dragons story", "Secrets of the Obscure story",
                       "Janthir Wilds story", "Visions of Eternity story"]),
            ("lore", ["Lore", "Lore books", "History", "Six Human Gods",
                      "Elder Dragons", "Dragon champions", "Playable races",
                      "Cultures"]),
            ("cultures", ["Human culture", "Charr culture", "Asura culture",
                          "Norn culture", "Sylvari culture", "Hylek culture",
                          "Skritt culture", "Quaggan culture", "Jotun culture",
                          "Dwarf culture", "Kodan culture", "Grawl culture",
                          "Krait culture", "Ogre culture", "Tengu culture",
                          "Centaur culture", "Seer culture", "Largos culture",
                          "Mursaat culture", "Djinn culture", "Dredge culture"]),
            ("orders", ["Order of Whispers", "Order of the Sunspears",
                        "Order of Shadows", "Order of the Crystal Bloom",
                        "Tyrian Explorers Society"]),
            ("legendary_npcs", ["Legendary NPCs"]),
            ("story_characters", ["Story characters",
                                  "Edge of Destiny characters",
                                  "Sea of Sorrows characters"]),
        ],
    },
    "lord_of_the_rings": {
        # "The One Wiki to Rule Them All" (lotr.fandom.com). 7.2k articles.
        # Scope = Tolkien legendarium narrative: characters (by book + by
        # race), peoples, realms/regions/places, battles/events, weapons &
        # artifacts (esp. the Rings), lineages. Skip real-world people,
        # film-production / soundtrack / documentary pages, and the
        # explicitly non-canonical (film/game-only) categories to keep the
        # corpus to the books. First-match routing dedups race vs book.
        "domain": "lotr.fandom.com",
        "work": "Lord_of_the_Rings",
        "buckets": [
            ("silmarillion_chars", ["The Silmarillion characters",
                                    "Characters in The Children of Húrin",
                                    "Characters in Beren and Lúthien",
                                    "Characters in The Book of Lost Tales",
                                    "Characters in Unfinished Tales",
                                    "Characters in The History of Middle-earth"]),
            ("lotr_chars", ["The Lord of the Rings characters",
                            "Major characters (The Lord of the Rings)",
                            "Minor characters (The Lord of the Rings)",
                            "Ring bearers", "Agents of Saruman"]),
            ("hobbit_chars", ["The Hobbit characters"]),
            ("ainur", ["Valar", "Maiar", "Ainur"]),
            ("races", ["Hobbits", "Elves", "Dwarves", "Men of Gondor",
                       "Númenóreans", "Grey Elves", "Half-elves",
                       "Elves of Beleriand", "Elves of Gondolin",
                       "Elves of Doriath", "Elf friends", "Orcs", "Ents",
                       "Eagles", "Wizards"]),
            ("peoples_lineages", ["Peoples", "Lineages", "Hobbit families",
                                  "Ruling Stewards of Gondor",
                                  "Númenórean Kings", "Kings of Rohan",
                                  "Kings of Gondor", "Ranks and titles of Men",
                                  "Houses"]),
            ("realms_places", ["Realms", "Regions", "Locations",
                               "Settlements", "Settlements of the Shire",
                               "Hobbit settlements", "Númenor", "Mountains",
                               "Rivers", "Forests"]),
            ("battles_events", ["Battles", "Events", "War of the Ring",
                                "Wars", "Deaths in battle"]),
            ("weapons_artifacts", ["Weapons", "Rings", "Rings of Power",
                                   "Objects", "Artifacts", "Dwarven objects",
                                   "Jewels"]),
            ("lore", ["Languages", "Songs and poems", "Concepts",
                      "Books of Middle-earth"]),
        ],
    },
}


def api_get(api_url, params, retries=3):
    p = dict(params)
    p["format"] = "json"
    last = None
    for attempt in range(retries):
        try:
            r = requests.get(api_url, params=p, headers=HEADERS, timeout=30)
            if r.status_code in (502, 503, 504, 429):
                raise requests.HTTPError("%s transient" % r.status_code)
            r.raise_for_status()
            return r.json()
        except Exception as e:
            last = e
            time.sleep(1.5 * (attempt + 1))
    raise last


def category_members(api_url, cat):
    titles = []
    cont = {}
    while True:
        params = {
            "action": "query",
            "list": "categorymembers",
            "cmtitle": "Category:" + cat,
            "cmlimit": "500",
            "cmnamespace": "0",
        }
        params.update(cont)
        data = api_get(api_url, params)
        for m in data.get("query", {}).get("categorymembers", []):
            titles.append(m["title"])
        if "continue" in data:
            cont = data["continue"]
            time.sleep(0.3)
        else:
            break
    return titles


def page_plaintext(api_url, title):
    data = api_get(api_url, {
        "action": "parse",
        "page": title,
        "prop": "text",
        "redirects": "1",
    })
    if "error" in data:
        return None
    html = data.get("parse", {}).get("text", {}).get("*", "")
    if not html:
        return None
    soup = BeautifulSoup(html, "html.parser")
    drop_selectors = [
        "script", "style", "table.navbox", ".navbox", ".toc", ".mw-editsection",
        ".printfooter", ".noprint", ".mw-references-wrap", "#toc",
        ".portable-infobox .pi-image", ".reference",
    ]
    for sel in drop_selectors:
        for el in soup.select(sel):
            el.decompose()
    text = soup.get_text(separator="\n", strip=True)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def crawl(config):
    domain = config["domain"]
    api_url = "https://%s/api.php" % domain
    out_dir = os.path.join("working", config["work"], "raw")
    buckets = config["buckets"]
    os.makedirs(out_dir, exist_ok=True)

    all_cats = []
    for _b, cats in buckets:
        all_cats.extend(cats)

    print("Listing category members from %s ..." % domain)
    title_to_cats = {}
    for cat in all_cats:
        try:
            members = category_members(api_url, cat)
        except Exception as e:
            print("  ! category '%s' failed: %s" % (cat, e))
            continue
        print("  [%3d] %s" % (len(members), cat))
        for t in members:
            title_to_cats.setdefault(t, set()).add(cat)

    title_to_bucket = {}
    for title, cats in title_to_cats.items():
        for bucket_name, bucket_cats in buckets:
            if cats.intersection(bucket_cats):
                title_to_bucket[title] = bucket_name
                break

    total = len(title_to_bucket)
    print("\nSelected %d unique pages across %d buckets.\n" % (
        total, len(set(title_to_bucket.values()))))

    bucket_order = {name: i for i, (name, _c) in enumerate(buckets)}
    ordered = sorted(title_to_bucket.items(),
                     key=lambda kv: (bucket_order[kv[1]], kv[0]))

    bucket_files = {}
    manifest = []
    fetched = 0
    failed = []
    for title, bucket in ordered:
        try:
            text = page_plaintext(api_url, title)
        except Exception as e:
            print("  ! fetch failed '%s': %s" % (title, e))
            failed.append(title)
            time.sleep(DELAY)
            continue
        if not text:
            failed.append(title)
            time.sleep(DELAY)
            continue
        fh = bucket_files.get(bucket)
        if fh is None:
            fh = open(os.path.join(out_dir, bucket + ".txt"), "w",
                      encoding="utf-8")
            bucket_files[bucket] = fh
        fh.write("\n" + "=" * 70 + "\n")
        fh.write("PAGE: %s\n" % title)
        fh.write("CATEGORIES: %s\n" % ", ".join(sorted(title_to_cats[title])))
        fh.write("URL: https://%s/wiki/%s\n" % (domain, title.replace(" ", "_")))
        fh.write("=" * 70 + "\n\n")
        fh.write(text + "\n")
        manifest.append({"title": title, "bucket": bucket,
                         "categories": sorted(title_to_cats[title]),
                         "chars": len(text)})
        fetched += 1
        if fetched % 25 == 0:
            print("  ... %d/%d fetched" % (fetched, total))
        time.sleep(DELAY)

    for fh in bucket_files.values():
        fh.close()

    with open(os.path.join(out_dir, "_manifest.json"), "w",
              encoding="utf-8") as f:
        json.dump({"fetched": fetched, "failed": failed, "pages": manifest},
                  f, ensure_ascii=False, indent=2)

    print("\nDONE. %d pages fetched, %d failed." % (fetched, len(failed)))
    if failed:
        print("Failed: %s" % ", ".join(failed[:30]))
    total_bytes = 0
    for name in sorted(bucket_files):
        p = os.path.join(out_dir, name + ".txt")
        sz = os.path.getsize(p)
        total_bytes += sz
        print("  %-22s %8.1f KB" % (name + ".txt", sz / 1024.0))
    print("  TOTAL %.2f MB" % (total_bytes / 1048576.0))


if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] not in CONFIGS:
        print("Usage: python scripts/fandom_crawler.py <%s>"
              % "|".join(CONFIGS))
        sys.exit(1)
    crawl(CONFIGS[sys.argv[1]])
