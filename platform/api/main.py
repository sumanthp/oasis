from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks, status
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from sqlalchemy.orm import Session
import yaml
import os
import uuid
import subprocess
import time
import jwt
from datetime import datetime, timedelta
from passlib.context import CryptContext
from pathlib import Path
import docker
import socket

from . import database
from .database import User, Session as DBSession, Evaluation, SessionLocal
import re

SECRET_KEY = os.environ.get("SECRET_KEY", "super-secret-mvp-key-do-not-use-in-prod")
ALGORITHM = "HS256"
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

app = FastAPI(
    title="AI-Engine Platform API",
    description="Control plane for the Agentic Interview Sandbox",
    version="0.1.0"
)

# Initialize database
database.init_db()

class LoginRequest(BaseModel):
    username: str
    password: str

class SessionRequest(BaseModel):
    challenge_id: str

class EvaluationRequest(BaseModel):
    session_id: str

# Mount the static UI directory
ui_dir = Path(__file__).parent.parent / "ui"
app.mount("/static", StaticFiles(directory=str(ui_dir)), name="static")

@app.get("/")
async def serve_landing():
    """Serves the premium landing/login page."""
    return FileResponse(ui_dir / "index.html")

@app.get("/dashboard")
async def serve_dashboard():
    """Serves the candidate challenge selection dashboard."""
    return FileResponse(ui_dir / "dashboard.html")

@app.get("/admin")
async def serve_admin():
    """Serves the recruiter results dashboard."""
    return FileResponse(ui_dir / "admin.html")

@app.get("/profile")
async def serve_profile():
    """Serves the user/recruiter profile page."""
    return FileResponse(ui_dir / "profile.html")

@app.get("/register")
async def serve_register():
    """Serves the candidate registration page."""
    return FileResponse(ui_dir / "register.html")

# --- SECURITY ---
def create_access_token(data: dict, expires_delta: timedelta = timedelta(hours=2)):
    to_encode = data.copy()
    expire = datetime.utcnow() + expires_delta
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(database.get_db)):
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
        
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    return user

def require_admin(user: User = Depends(get_current_user)):
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized. Admin role required.")
    return user


class LoginRequest(BaseModel):
    username: str
    password: str

class RegisterRequest(BaseModel):
    username: str
    password: str
    token: str

# --- AUTHENTICATION ---
@app.post("/api/auth/login")
async def login(req: LoginRequest, db: Session = Depends(database.get_db)):
    """Validates password and returns JWT."""
    user = db.query(User).filter(User.username == req.username).first()
    if not user or not user.password_hash or not pwd_context.verify(req.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Incorrect username or password")
        
    access_token = create_access_token(data={"sub": user.id, "role": user.role})
    return {"access_token": access_token, "role": user.role, "name": user.username}

@app.post("/api/auth/demo")
async def demo_login(db: Session = Depends(database.get_db)):
    """Creates a temporary demo user."""
    demo_id = str(uuid.uuid4())
    demo_name = f"DemoUser_{demo_id[:6]}"
    
    user = User(
        id=demo_id,
        username=demo_name,
        role="demo"
    )
    db.add(user)
    db.commit()
    
    access_token = create_access_token(data={"sub": user.id, "role": user.role})
    return {"access_token": access_token, "role": user.role, "name": user.username}

@app.post("/api/auth/register")
async def register(req: RegisterRequest, db: Session = Depends(database.get_db)):
    """Registers a candidate using an invite token."""
    invite = db.query(database.Invite).filter(database.Invite.id == req.token).first()
    if not invite:
        raise HTTPException(status_code=400, detail="Invalid invite token.")
    if invite.is_used:
        raise HTTPException(status_code=400, detail="Invite token already used.")
        
    existing = db.query(User).filter(User.username == req.username).first()
    if existing:
        raise HTTPException(status_code=400, detail="Username already taken.")
        
    user_id = str(uuid.uuid4())
    user = User(
        id=user_id,
        username=req.username,
        password_hash=pwd_context.hash(req.password),
        role="candidate"
    )
    db.add(user)
    
    invite.is_used = 1
    invite.used_by = user_id
    db.commit()
    
    access_token = create_access_token(data={"sub": user.id, "role": user.role})
    return {"access_token": access_token, "role": user.role, "name": user.username}

@app.post("/api/admin/invite")
async def create_invite(admin: User = Depends(require_admin), db: Session = Depends(database.get_db)):
    """Creates a new registration invite token."""
    token = str(uuid.uuid4())
    invite = database.Invite(id=token, created_by=admin.id)
    db.add(invite)
    db.commit()
    return {"token": token, "invite_url": f"/register?token={token}"}

# --- ENDPOINTS ---

@app.get("/api/challenges")
async def list_challenges():
    """Scans the filesystem and returns all available challenges."""
    challenges_dir = Path(__file__).parent.parent.parent / "challenges"
    challenges = []
    
    if not challenges_dir.exists():
        return {"challenges": []}
        
    for domain_dir in challenges_dir.iterdir():
        if domain_dir.is_dir():
            manifest_path = domain_dir / "manifest.yaml"
            if manifest_path.exists():
                with open(manifest_path, "r") as f:
                    manifest = yaml.safe_load(f)
                    challenges.append({
                        "id": domain_dir.name,
                        "title": manifest.get("name", domain_dir.name),
                        "domain": manifest.get("domain", "General"),
                        "desc": manifest.get("description", ""),
                        "stack": manifest.get("stack", [])
                    })
    return {"challenges": challenges}

def get_host_challenges_path() -> str:
    """Discovers the host path for the /app/challenges volume mount."""
    try:
        client = docker.from_env()
        container_id = socket.gethostname()
        container = client.containers.get(container_id)
        for m in container.attrs.get('Mounts', []):
            if m['Destination'] == '/app/challenges':
                return m['Source']
    except Exception as e:
        print(f"Warning: Could not resolve docker host path: {e}")
    # Fallback for local non-docker development
    return str(Path(__file__).parent.parent.parent / "challenges")

@app.post("/session/start")
async def start_session(request: SessionRequest, user: User = Depends(get_current_user), db: Session = Depends(database.get_db)):
    """Starts a sandbox session and creates a DB record with a dynamic IDE container."""
    if not re.match(r"^[a-zA-Z0-9_-]+$", request.challenge_id):
        raise HTTPException(status_code=400, detail="Invalid challenge ID format")
        
    challenges_dir = Path(__file__).parent.parent.parent / "challenges"
    challenge_path = challenges_dir / request.challenge_id / "manifest.yaml"
    
    if not challenge_path.exists():
        raise HTTPException(status_code=404, detail=f"Challenge {request.challenge_id} not found")
        
    session_id = str(uuid.uuid4())
    
    # -----------------------------
    # DYNAMIC CONTAINER PROVISIONING
    # -----------------------------
    ide_port = 8443
    try:
        host_challenges = get_host_challenges_path()
        host_workspace = f"{host_challenges}/{request.challenge_id}/candidate_workspace"
        
        client = docker.from_env()
        container = client.containers.run(
            "lscr.io/linuxserver/code-server:latest",
            name=f"ide_{session_id}",
            environment=["PASSWORD=password", "SUDO_PASSWORD=password", "PUID=1000", "PGID=1000", "TZ=Etc/UTC"],
            volumes={
                host_workspace: {'bind': '/config/workspace', 'mode': 'rw'}
            },
            network="oasis_default", # Connect to internal network
            ports={'8443/tcp': None}, # Ask Docker to assign a random free host port
            detach=True
        )
        
        # Reload to fetch assigned port
        container.reload()
        port_bindings = container.attrs['NetworkSettings']['Ports'].get('8443/tcp')
        if port_bindings:
            ide_port = int(port_bindings[0]['HostPort'])
            
    except Exception as e:
        print(f"Failed to provision dynamic sandbox: {e}")
        # If provisioning fails, we might still fallback to static 8443 for local MVP debugging
        pass

    db_session = DBSession(
        id=session_id,
        user_id=user.id,
        challenge_id=request.challenge_id,
        status="running",
        ide_port=ide_port
    )
    db.add(db_session)
    db.commit()
    
    return {
        "status": "provisioning",
        "session_id": session_id,
        "challenge_id": request.challenge_id,
        "ide_port": ide_port
    }

@app.post("/api/evaluate/test")
async def trigger_test(req: EvaluationRequest, user: User = Depends(get_current_user), db: Session = Depends(database.get_db)):
    """Runs the grader script in an isolated Docker container without saving verdict."""
    db_session = db.query(DBSession).filter(DBSession.id == req.session_id, DBSession.user_id == user.id).first()
    if not db_session:
        raise HTTPException(status_code=404, detail="Session not found")
        
    try:
        host_challenges = get_host_challenges_path()
        host_challenge_dir = f"{host_challenges}/{db_session.challenge_id}"
        
        client = docker.from_env()
        output = ""
        try:
            # We install httpx/requests if they need it in the test container
            cmd = "sh -c 'pip install -q -r /candidate_workspace/requirements.txt 2>/dev/null; python3 /evaluator/grader.py'"
            logs = client.containers.run(
                "python:3.10-slim",
                command=cmd,
                volumes={
                    f"{host_challenge_dir}/evaluator": {'bind': '/evaluator', 'mode': 'ro'},
                    f"{host_challenge_dir}/candidate_workspace": {'bind': '/candidate_workspace', 'mode': 'ro'}
                },
                network="oasis_default",
                remove=True,
                detach=False
            )
            output = logs.decode('utf-8')
        except docker.errors.ContainerError as e:
            output = e.stderr.decode('utf-8') + "\n" + e.stdout.decode('utf-8')
        except Exception as e:
            output = str(e)
            
        verdict = "REVIEW"
        if "HIRE" in output or "SUCCESS" in output or "PASS" in output:
            verdict = "HIRE"
        if "FAIL" in output or "ERROR" in output:
            verdict = "PASS"
            
        lines = [line.strip() for line in output.split('\n') if line.strip()]
        feedback_text = lines[-1] if lines else "Execution completed."
        if "Feedback:" in feedback_text:
            feedback_text = feedback_text.split("Feedback:")[1].strip()
            
    except Exception as e:
        verdict = "REVIEW"
        feedback_text = f"Grader container failed: {str(e)}"
        
    return {"status": "success", "verdict": verdict, "feedback": feedback_text}


def run_evaluation_task(session_id: str, challenge_id: str, candidate_code: str, started_at: datetime):
    """Background task to run grader in Docker, update DB, and tear down IDE."""
    db = SessionLocal()
    try:
        host_challenges = get_host_challenges_path()
        host_challenge_dir = f"{host_challenges}/{challenge_id}"
        
        client = docker.from_env()
        start_time = time.time()
        output = ""
        try:
            cmd = "sh -c 'pip install -q -r /candidate_workspace/requirements.txt 2>/dev/null; python3 /evaluator/grader.py'"
            logs = client.containers.run(
                "python:3.10-slim",
                command=cmd,
                volumes={
                    f"{host_challenge_dir}/evaluator": {'bind': '/evaluator', 'mode': 'ro'},
                    f"{host_challenge_dir}/candidate_workspace": {'bind': '/candidate_workspace', 'mode': 'ro'}
                },
                network="oasis_default",
                remove=True,
                detach=False
            )
            output = logs.decode('utf-8')
        except docker.errors.ContainerError as e:
            output = e.stderr.decode('utf-8') + "\n" + e.stdout.decode('utf-8')
        except Exception as e:
            output = str(e)
            
        verdict = "REVIEW"
        if "HIRE" in output or "SUCCESS" in output or "PASS" in output:
            verdict = "HIRE"
        if "FAIL" in output or "ERROR" in output:
            verdict = "PASS"
            
        lines = [line.strip() for line in output.split('\n') if line.strip()]
        feedback_text = lines[-1] if lines else "Execution completed."
        if "Feedback:" in feedback_text:
            feedback_text = feedback_text.split("Feedback:")[1].strip()
            
        # Update DB
        db_session = db.query(DBSession).filter(DBSession.id == session_id).first()
        if db_session:
            now = datetime.utcnow()
            exec_time = int(time.time() - start_time)
            ide_time_seconds = int((now - started_at).total_seconds())
            
            db_session.completed_at = now
            db_session.status = "completed"
            db_session.ide_time_seconds = ide_time_seconds
            
            evaluation = Evaluation(
                session_id=session_id,
                execution_time_seconds=exec_time,
                verdict=verdict,
                feedback_text=feedback_text[:255],
                candidate_code=candidate_code,
                ai_trace_logs=output
            )
            db.add(evaluation)
            db.commit()
            
        # Tear down IDE container
        try:
            ide = client.containers.get(f"ide_{session_id}")
            ide.stop(timeout=2)
            ide.remove(force=True)
        except Exception as e:
            print(f"Failed to teardown IDE {session_id}: {e}")
            
    finally:
        db.close()


@app.post("/api/evaluate/submit")
async def trigger_submit(req: EvaluationRequest, background_tasks: BackgroundTasks, user: User = Depends(get_current_user), db: Session = Depends(database.get_db)):
    """Triggers async evaluation in a BackgroundTask."""
    db_session = db.query(DBSession).filter(DBSession.id == req.session_id, DBSession.user_id == user.id).first()
    if not db_session:
        raise HTTPException(status_code=404, detail="Session not found")
        
    db_session.status = "evaluating"
    db.commit()
    
    challenge_dir = Path(__file__).parent.parent.parent / "challenges" / db_session.challenge_id
    workspace_dir = challenge_dir / "candidate_workspace"
    
    # Read candidate code
    candidate_code = ""
    if workspace_dir.exists():
        for py_file in workspace_dir.rglob("*.py"):
            try:
                with open(py_file, "r") as f:
                    candidate_code += f"# --- {py_file.name} ---\n{f.read()}\n\n"
            except:
                pass
                
    background_tasks.add_task(
        run_evaluation_task, 
        session_id=db_session.id, 
        challenge_id=db_session.challenge_id, 
        candidate_code=candidate_code,
        started_at=db_session.started_at
    )
    
    return {"status": "evaluating", "message": "Evaluation started in background."}

@app.get("/api/admin/evaluations")
async def get_evaluations(admin: User = Depends(require_admin), db: Session = Depends(database.get_db)):
    """Fetches all evaluations for the admin dashboard. Protected by require_admin."""
    evaluations = db.query(Evaluation).order_by(Evaluation.created_at.desc()).all()
    
    results = []
    stats = {
        "total": len(evaluations),
        "hire": 0,
        "pass": 0,
        "review": 0,
        "avg_time": 0
    }
    
    total_time = 0
    
    for ev in evaluations:
        ide_time = ev.session.ide_time_seconds or ev.execution_time_seconds
        
        results.append({
            "candidate_id": ev.session.user.username,
            "challenge_id": ev.session.challenge_id,
            "execution_time": f"{ide_time}s",
            "verdict": ev.verdict,
            "feedback": ev.feedback_text,
            "candidate_code": ev.candidate_code or "No code captured.",
            "ai_trace_logs": ev.ai_trace_logs or "No logs available."
        })
        
        if ev.verdict == "HIRE": stats["hire"] += 1
        elif ev.verdict == "PASS": stats["pass"] += 1
        else: stats["review"] += 1
        
        total_time += ide_time
        
    if stats["total"] > 0:
        stats["avg_time"] = int(total_time / stats["total"])
        
    return {"evaluations": results, "stats": stats}

@app.get("/api/profile")
async def get_profile(user: User = Depends(get_current_user), db: Session = Depends(database.get_db)):
    """Fetches user details and evaluation history."""
    profile_data = {
        "username": user.username,
        "role": user.role,
        "created_at": user.created_at.strftime("%Y-%m-%d %H:%M:%S")
    }
    
    if user.role != "admin":
        evaluations = db.query(Evaluation).join(DBSession).filter(DBSession.user_id == user.id).order_by(Evaluation.created_at.desc()).all()
        history = []
        for ev in evaluations:
            history.append({
                "challenge_id": ev.session.challenge_id,
                "execution_time": f"{ev.execution_time_seconds}s",
                "verdict": ev.verdict,
                "feedback": ev.feedback_text,
                "date": ev.created_at.strftime("%Y-%m-%d %H:%M:%S")
            })
        profile_data["history"] = history
        
        # Check for active session
        active_session = db.query(DBSession).filter(DBSession.user_id == user.id, DBSession.status == "running").first()
        if active_session:
            profile_data["active_session"] = {
                "id": active_session.id,
                "challenge_id": active_session.challenge_id
            }
    else:
        total_evals = db.query(Evaluation).count()
        profile_data["stats"] = {"total_evaluations_platform": total_evals}
        
    return profile_data
