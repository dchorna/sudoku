# web/app.py
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Literal, Optional

from generator.board_generator import generate_full_board
from generator.difficulty import generate_puzzle
from generator.wall_generator import compute_walls
from solver.solver import solve_board
from solver.hint_engine import HintEngine
from model.board import Board

app = FastAPI(title="Sudoku AI Backend")

# Дозволяємо CORS для майбутнього фронтенду
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Pydantic Схеми ---

class GenerateRequest(BaseModel):
    mode: Literal["classic", "consecutive"] = "classic"
    level: Literal["easy", "medium", "hard"] = "easy"

class BoardActionRequest(BaseModel):
    mode: Literal["classic", "consecutive"]
    grid: list[list[int]]
    # Фронтенд передаватиме перегородки як список пар координат
    walls_list: Optional[list[dict]] = None 

# --- Допоміжні функції ---

def _parse_walls_from_request(walls_list: list[dict] | None) -> dict | None:
    if not walls_list:
        return None
    walls = {}
    for w in walls_list:
        a = tuple(w["a"])
        b = tuple(w["b"])
        walls[(a, b)] = w["is_wall"]
        walls[(b, a)] = w["is_wall"]
    return walls

def _format_walls_for_response(walls_dict: dict | None) -> list[dict]:
    if not walls_dict:
        return []
    formatted = []
    seen = set()
    for (a, b), is_wall in walls_dict.items():
        # Додаємо кожну перегородку лише один раз (без зворотних)
        edge = tuple(sorted((a, b)))
        if edge not in seen:
            seen.add(edge)
            formatted.append({"a": edge[0], "b": edge[1], "is_wall": is_wall})
    return formatted

# --- Маршрути (Endpoints) ---

@app.post("/api/generate")
def generate_game(request: GenerateRequest):
    try:
        solution = generate_full_board()
        puzzle = generate_puzzle(request.mode, request.level, solution)
        walls_dict = compute_walls(solution) if request.mode == "consecutive" else None
        
        return {
            "puzzle": puzzle.grid,
            "solution": solution.grid,
            "walls": _format_walls_for_response(walls_dict)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/hint")
def get_hint(request: BoardActionRequest):
    walls = _parse_walls_from_request(request.walls_list)
    engine = HintEngine(request.grid, walls)
    
    hint = engine.get_hint()
    if not hint:
        return {"hint": None, "message": "No logical hint found. The board might be fully solved, invalid, or requires guessing."}
    
    return {
        "hint": {
            "technique": hint.technique,
            "cells": hint.cells,
            "action": hint.action,
            "explanation": hint.explanation
        }
    }

@app.post("/api/solve")
def solve_game(request: BoardActionRequest):
    walls = _parse_walls_from_request(request.walls_list)
    solved_board = solve_board(request.grid, walls)
    
    if not solved_board:
        raise HTTPException(status_code=400, detail="Board has no valid solution.")
        
    return {"solved_grid": solved_board.grid}