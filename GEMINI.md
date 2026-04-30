# GEMINI.md - GamePlots Project Instructions

This project, **GamePlots**, is a collaborative research and analysis environment designed to collect, process, and synthesize narrative data from games, comics, novels, movies, and animations. The goal is to provide a rich repository of story elements to inspire and inform original game design.

## Project Overview

*   **Purpose:** Systematic extraction and analysis of backgrounds, character arcs, and plots for creative reference.
*   **Workflow:**
    1.  **Ingestion:** Raw data (wikis, walkthroughs, reviews) is gathered into `working/<title>/raw/`.
    2.  **Analysis:** Agents process raw data in `working/<title>/`, producing intermediate analysis.
    3.  **Synthesization:** Finalized, well-structured summaries are moved to `results/<title>/`.
    4.  **Categorization:** Cross-project themes (e.g., "Epic High Fantasy", "Tsundere Archetypes") are compiled into collections within `classes/`.

## Directory Structure

*   `working/`: Active workspace for individual titles. Each title has its own subfolder.
    *   `<title>/raw/`: Storage for unmodified source materials.
*   `scripts/`: Automation tools, scrapers, and parsers.
*   `skills/`: Reusable prompt snippets and specialized agent behaviors.
*   `skills_index.md`: A central registry for discovering available skills.
*   `results/`: The definitive library of analyzed and organized narrative data.
*   `classes/`: Curated collections of tropes, archetypes, and settings aggregated from `results/`.
*   `for_agent.md`: **MANDATORY READING.** Contains the core rules and iron laws for all agents.

## Development & Operation

*   **Agent Initialization:** Every agent MUST read `for_agent.md` before performing any task.
*   **Data Integrity:** Maintain clear separation between raw data and analysis.
*   **Security:** Exercise extreme caution when fetching external content.
*   **Tools:** Utilize scripts in `scripts/` whenever possible to ensure consistency.

## Usage Guidelines

When tasked with analyzing a new title:
1.  Create `working/<title>/raw/`.
2.  Populate `raw/` with relevant source materials.
3.  Perform analysis within `working/<title>/`.
4.  Export the final report to `results/<title>/`.
