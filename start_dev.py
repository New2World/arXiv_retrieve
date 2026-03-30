import subprocess
import sys
import time
import os
import signal

def main():
    print("=====================================================")
    print("  🚀 Starting ArXiv Agent (Development Mode)")
    print("=====================================================")
    print("Press [Ctrl+C] at any time to safely stop both servers.\n")

    root_dir = os.getcwd()
    backend_cwd = os.path.join(root_dir, "backend")
    frontend_cwd = os.path.join(root_dir, "frontend")

    # Backend Command
    venv_python = os.path.join(backend_cwd, ".venv", "Scripts", "python.exe")
    if not os.path.exists(venv_python):
        print(f"[ERROR] Virtual environment not found at: {venv_python}")
        print("Please ensure you have created the backend virtual environment.")
        sys.exit(1)
        
    backend_cmd = [venv_python, "-m", "uvicorn", "app.main:app", "--reload"]
    
    # Frontend Command
    frontend_cmd = ["npm.cmd", "run", "dev"] if os.name == 'nt' else ["npm", "run", "dev"]

    print("[INFO] Starting backend server...")
    backend_proc = subprocess.Popen(backend_cmd, cwd=backend_cwd)
    
    print("[INFO] Starting frontend server...")
    frontend_proc = subprocess.Popen(frontend_cmd, cwd=frontend_cwd)

    # Define the cleanup function
    def cleanup_and_exit(*args):
        print("\n\n[INFO] Caught termination signal (Ctrl+C). Shutting down servers...")
        try:
            if os.name == 'nt':
                # Windows: taskkill /T ensures the entire process tree (e.g. npm -> node) is killed
                subprocess.run(["taskkill", "/F", "/T", "/PID", str(backend_proc.pid)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                subprocess.run(["taskkill", "/F", "/T", "/PID", str(frontend_proc.pid)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            else:
                # Unix systems
                backend_proc.terminate()
                frontend_proc.terminate()
            print("[INFO] Servers stopped gracefully. Goodbye! 👋")
        except Exception as e:
            print(f"[ERROR] Failed to terminate processes: {e}")
        finally:
            sys.exit(0)

    # Bind OS signals
    signal.signal(signal.SIGINT, cleanup_and_exit)
    signal.signal(signal.SIGTERM, cleanup_and_exit)

    # Wait indefinitely until interrupted
    try:
        while True:
            time.sleep(1)
            # Auto-exit if both processes die on their own
            if backend_proc.poll() is not None and frontend_proc.poll() is not None:
                break
    except KeyboardInterrupt:
        cleanup_and_exit()

if __name__ == "__main__":
    main()
