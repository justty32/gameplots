# Instructions for Agents

This file contains the rules, iron laws, and workflow regulations for all agents working on this project.

## Core Mandates
1. **Read this file first:** All agents must read `for_agent.md` before starting any work.
2. **Safety:** Be extremely careful when downloading data from the internet.
3. **Structure:** Follow the directory structure strictly.
4. **Analysis:** Focus on extracting useful story elements, character traits, and world-building details.
5. **Language:** 本專案使用者為繁體中文使用者，所有文件、分析結果及溝通請務必使用**繁體中文**。
6. **Environment Awareness:** 工作環境可能在 Linux 或 Windows 之間切換。在 Windows 上可能會使用 PowerShell，請在執行指令或撰寫腳本前先確認目前的作業系統與 Shell 環境。

## Workflow
- **Data Collection:** Crawl or download data into `working/<work_name>/raw/`.
- **Processing:** Analyze raw data and store intermediate results in `working/<work_name>/`.
- **Finalization:** Store organized results in `results/<work_name>/`.
- **Aggregation:** Collect specific types of data into `classes/`.
