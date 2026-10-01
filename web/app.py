# web/app.py
import time
import hmac
import hashlib
import secrets
import pathlib
from typing import Literal, Optional
import os
from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.orm import Session

from generator.board_generator import generate_full_board
from generator.difficulty import generate_puzzle
from generator.wall_generator import compute_walls
from solver.solver import solve_board
from solver.hint_engine import HintEngine
from model.database import init_db, SessionLocal
from model.user import User
from model.record import Record
from web.progress_manager import can_access_level, record_win

app = FastAPI(title="Sudoku AI Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

init_db()

# --- Токени входу (підписані HMAC, переживають перезапуск сервера) ---

_env_key = os.environ.get("SECRET_KEY")
if _env_key:
    SECRET_KEY = _env_key.encode()
else:  # локальний запуск
    _KEY_FILE = pathlib.Path(__file__).resolve().parent / ".secret_key"
    if not _KEY_FILE.exists():
        _KEY_FILE.write_text(secrets.token_hex(32))
    SECRET_KEY = _KEY_FILE.read_text().strip().encode()


def make_token(user_id: int) -> str:
    sig = hmac.new(SECRET_KEY, str(user_id).encode(), hashlib.sha256).hexdigest()
    return f"{user_id}.{sig}"


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(authorization: str = Header(None), db: Session = Depends(get_db)) -> User:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Потрібен вхід.")
    token = authorization[len("Bearer "):]
    try:
        uid_str, sig = token.split(".", 1)
        expected = hmac.new(SECRET_KEY, uid_str.encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(sig, expected):
            raise ValueError
        user = db.get(User, int(uid_str))
    except (ValueError, TypeError):
        user = None
    if not user:
        raise HTTPException(status_code=401, detail="Сесія недійсна. Увійдіть знову.")
    return user


HINT_LIMITS = {"easy": 3, "medium": 5, "hard": 5}
MAX_MISTAKES = 3

# Поточна гра кожного користувача (щоб перевіряти перемогу на сервері)
games: dict[int, dict] = {}

# --- Схеми ---

class AuthRequest(BaseModel):
    username: str
    password: str

class GenerateRequest(BaseModel):
    mode: Literal["classic", "consecutive"] = "classic"
    level: Literal["easy", "medium", "hard"] = "easy"

class MoveRequest(BaseModel):
    r: int
    c: int
    v: int

class BoardActionRequest(BaseModel):
    mode: Literal["classic", "consecutive"]
    grid: list[list[int]]
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
        edge = tuple(sorted((a, b)))
        if edge not in seen:
            seen.add(edge)
            formatted.append({"a": edge[0], "b": edge[1], "is_wall": is_wall})
    return formatted

def _records_for(user: User, db: Session, mode: str) -> dict:
    """Найкращий час (без урахування рівня): особистий і серед усіх гравців."""
    mine = db.query(func.min(Record.seconds)).filter(
        Record.user_id == user.id, Record.mode == mode).scalar()
    top = db.query(Record).filter(Record.mode == mode).order_by(Record.seconds.asc()).first()
    best = None
    if top:
        holder = db.get(User, top.user_id)
        best = {"seconds": top.seconds, "username": holder.username if holder else "—"}
    return {"mine": mine, "best": best}

def _progress_payload(user: User, db: Session) -> dict:
    modes = ("classic", "consecutive")
    levels = ("easy", "medium", "hard")
    return {
        "username": user.username,
        "wins": {
            "classic": {"easy": user.classic_easy_wins, "medium": user.classic_medium_wins},
            "consecutive": {"easy": user.consecutive_easy_wins, "medium": user.consecutive_medium_wins},
        },
        "available": {m: [l for l in levels if can_access_level(user, m, l)] for m in modes},
        "records": {m: _records_for(user, db, m) for m in modes},
    }

# --- Авторизація ---

@app.post("/api/register")
def register(req: AuthRequest, db: Session = Depends(get_db)):
    username = req.username.strip()
    if not username or len(username) > 50:
        raise HTTPException(status_code=400, detail="Введіть ім'я користувача (до 50 символів).")
    if len(req.password) < 4:
        raise HTTPException(status_code=400, detail="Пароль має містити щонайменше 4 символи.")
    if db.query(User).filter(User.username == username).first():
        raise HTTPException(status_code=409, detail="Таке ім'я вже зайняте.")
    user = User(username=username)
    user.set_password(req.password)
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"token": make_token(user.id), "progress": _progress_payload(user, db)}

@app.post("/api/login")
def login(req: AuthRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == req.username.strip()).first()
    if not user or not user.check_password(req.password):
        raise HTTPException(status_code=401, detail="Невірне ім'я або пароль.")
    return {"token": make_token(user.id), "progress": _progress_payload(user, db)}

@app.get("/api/progress")
def get_progress(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return _progress_payload(user, db)

# --- Гра ---

@app.post("/api/generate")
def generate_game(request: GenerateRequest, user: User = Depends(get_current_user)):
    if not can_access_level(user, request.mode, request.level):
        raise HTTPException(status_code=403, detail="Цей рівень ще не розблоковано.")
    try:
        solution = generate_full_board()
        puzzle = generate_puzzle(request.mode, request.level, solution)
        walls_dict = compute_walls(solution) if request.mode == "consecutive" else None
        games[user.id] = {
            "mode": request.mode, "level": request.level,
            "solution": [row[:] for row in solution.grid],
            "cheated": False, "done": False, "started": time.time(),
            "hints_used": 0, "mistakes": 0, "lost": False,
        }
        return {"puzzle": puzzle.grid, "walls": _format_walls_for_response(walls_dict),
                "hint_limit": HINT_LIMITS[request.level], "max_mistakes": MAX_MISTAKES}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/hint")
def get_hint(request: BoardActionRequest, user: User = Depends(get_current_user)):
    game = games.get(user.id)
    if not game or game["done"] or game["lost"]:
        raise HTTPException(status_code=400, detail="Немає активної гри (почніть нову).")
    limit = HINT_LIMITS[game["level"]]
    if game["hints_used"] >= limit:
        return {"hint": None, "limit_reached": True, "message": "Ліміт підказок вичерпано."}
    walls = _parse_walls_from_request(request.walls_list)
    hint = HintEngine(request.grid, walls).get_hint()
    if not hint:
        return {"hint": None, "message": "Логічної підказки не знайдено. Поле може бути розв'язане, містити помилку або вимагати вгадування."}
    game["hints_used"] += 1
    return {"hint": {
        "technique": hint.technique,
        "cells": hint.cells,
        "action": hint.action,
        "explanation": hint.explanation,
    }, "hints_left": limit - game["hints_used"]}

@app.post("/api/move")
def check_move(request: MoveRequest, user: User = Depends(get_current_user)):
    """Перевіряє цифру за розв'язком; 3 неправильні цифри = поразка."""
    game = games.get(user.id)
    if not game or game["done"] or game["lost"]:
        raise HTTPException(status_code=400, detail="Немає активної гри (почніть нову).")
    if not (0 <= request.r < 9 and 0 <= request.c < 9 and 1 <= request.v <= 9):
        raise HTTPException(status_code=400, detail="Некоректний хід.")
    correct = game["solution"][request.r][request.c] == request.v
    if not correct:
        game["mistakes"] += 1
        if game["mistakes"] >= MAX_MISTAKES:
            game["lost"] = True
    return {"correct": correct, "mistakes": game["mistakes"], "lost": game["lost"]}

@app.post("/api/solve")
def solve_game(request: BoardActionRequest, user: User = Depends(get_current_user)):
    walls = _parse_walls_from_request(request.walls_list)
    solved_board = solve_board(request.grid, walls)
    if not solved_board:
        raise HTTPException(status_code=400, detail="Board has no valid solution.")
    game = games.get(user.id)
    if game:
        game["cheated"] = True  # автоматичне розв'язання не зараховується як перемога
    return {"solved_grid": solved_board.grid}

@app.post("/api/complete")
def complete_game(request: BoardActionRequest, user: User = Depends(get_current_user),
                  db: Session = Depends(get_db)):
    game = games.get(user.id)
    if not game or game["done"] or game["lost"]:
        raise HTTPException(status_code=400, detail="Немає активної гри (почніть нову).")
    if game["cheated"]:
        return {"counted": False, "message": "Гру розв'язано автоматично — перемогу не зараховано.",
                "progress": _progress_payload(user, db)}
    if request.grid != game["solution"]:
        raise HTTPException(status_code=400, detail="Поле заповнено неправильно.")
    # Час міряємо на сервері, щоб його не можна було підробити з браузера
    seconds = max(1, int(time.time() - game["started"]))
    previous_best = db.query(func.min(Record.seconds)).filter(
        Record.user_id == user.id, Record.mode == game["mode"]).scalar()
    new_record = previous_best is None or seconds < previous_best

    record_win(user, game["mode"], game["level"])
    db.add(Record(user_id=user.id, mode=game["mode"], level=game["level"], seconds=seconds))
    db.commit()
    db.refresh(user)
    game["done"] = True
    return {"counted": True, "seconds": seconds, "new_record": new_record,
            "message": "Перемогу зараховано!", "progress": _progress_payload(user, db)}

# --- Фронтенд: http://127.0.0.1:8000/ ---

FRONTEND_FILE = pathlib.Path(__file__).resolve().parent.parent / "frontend" / "index.html"

@app.get("/", include_in_schema=False)
def index():
    return FileResponse(FRONTEND_FILE)

@app.api_route("/health", methods=["GET", "HEAD"], include_in_schema=False)
def health():
    return {"status": "ok"}