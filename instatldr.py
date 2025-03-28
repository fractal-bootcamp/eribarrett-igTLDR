#!/usr/bin/env python3
"""
InstaTLDR - Command Line Interface
A unified CLI wrapper for the Instagram TLDR application.
"""

import os
import sys
import subprocess
import json
import time
import argparse
import signal
import webbrowser
from datetime import datetime
import shutil
import platform

# ANSI color codes for pretty terminal output
COLORS = {
    "reset": "\033[0m",
    "bold": "\033[1m",
    "dim": "\033[2m",
    "italic": "\033[3m",
    "underline": "\033[4m",
    "black": "\033[30m",
    "red": "\033[31m",
    "green": "\033[32m",
    "yellow": "\033[33m",
    "blue": "\033[34m",
    "magenta": "\033[35m",
    "cyan": "\033[36m",
    "white": "\033[37m",
    "bg_black": "\033[40m",
    "bg_red": "\033[41m",
    "bg_green": "\033[42m",
    "bg_yellow": "\033[43m",
    "bg_blue": "\033[44m",
    "bg_magenta": "\033[45m",
    "bg_cyan": "\033[46m",
    "bg_white": "\033[47m",
}

# ASCII art for InstaTLDR
ASCII_ART = f"""
{COLORS['cyan']}{COLORS['bold']} ___           _       _______ _      _____  ____  
|_ _|_ __  ___| |_ __ _|_   _| | |  |  _ \\|  _ \\ 
 | || '_ \\/ __| __/ _` | | | | | |  | | | | |_) |
 | || | | \\__ \\ || (_| | | | | | |__| |_| |  _ < 
|___|_| |_|___/\\__\\__,_| |_| |_|____|____/|_| \\_\\
{COLORS['reset']}
"""

# Base project paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.join(BASE_DIR, "backend")
TS_SERVICES_DIR = os.path.join(BASE_DIR, "ts-services")
FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")

# Configuration for services
SERVICES = {
    "backend": {
        "dir": BACKEND_DIR,
        "start_cmd": ["python", "main.py"],
        "requirements": os.path.join(BACKEND_DIR, "requirements.txt"),
        "env_setup": "python -m pip install -r requirements.txt",
        "default_port": 5000,
        "port_env_var": "PORT",
    },
    "ts-services": {
        "dir": TS_SERVICES_DIR,
        "start_cmd": ["npm", "start"],
        "dev_cmd": ["npm", "run", "dev"],
        "install_cmd": ["npm", "install"],
        "default_port": 3001,
        "port_env_var": "PORT",
    },
    "frontend": {
        "dir": FRONTEND_DIR,
        "start_cmd": ["npm", "run", "dev"],
        "install_cmd": ["npm", "install"],
        "default_port": 3000,
        "port_env_var": "PORT",
    }
}

# Process tracking
running_processes = {}

def print_styled(message, style=None, newline=True):
    """Print styled text to the terminal."""
    style_code = COLORS.get(style, "")
    end = COLORS["reset"] + ("\n" if newline else "")
    print(f"{style_code}{message}{end}", end="")

def print_header(title):
    """Print a styled header."""
    width = shutil.get_terminal_size().columns
    print_styled("╭" + "─" * (width - 2) + "╮", "cyan")
    padding = (width - len(title) - 2) // 2
    print_styled("│" + " " * padding + title + " " * (width - padding - len(title) - 2) + "│", "cyan")
    print_styled("╰" + "─" * (width - 2) + "╯", "cyan")

def print_step(step, message):
    """Print a step in a process."""
    print_styled(f"[{step}] ", "cyan", newline=False)
    print(message)

def print_success(message):
    """Print a success message."""
    print_styled(f"✓ {message}", "green")

def print_error(message):
    """Print an error message."""
    print_styled(f"✗ {message}", "red")

def print_warning(message):
    """Print a warning message."""
    print_styled(f"⚠ {message}", "yellow")

def print_info(message):
    """Print an info message."""
    print_styled(f"ℹ {message}", "blue")

def print_command(cmd):
    """Format and print a command."""
    if isinstance(cmd, list):
        cmd = " ".join(cmd)
    print_styled(f"$ {cmd}", "dim")

def run_command(cmd, cwd=None, env=None, capture_output=False, check=True):
    """Run a command and return the result."""
    print_command(cmd)
    try:
        if capture_output:
            result = subprocess.run(
                cmd, cwd=cwd, env=env, check=check, 
                stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                text=True
            )
            return result
        else:
            subprocess.run(cmd, cwd=cwd, env=env, check=check)
            return True
    except subprocess.CalledProcessError as e:
        print_error(f"Command failed with exit code {e.returncode}")
        if hasattr(e, 'stderr') and e.stderr:
            print_styled(e.stderr, "red")
        return False
    except Exception as e:
        print_error(f"Error running command: {str(e)}")
        return False

def is_port_in_use(port):
    """Check if a port is in use."""
    import socket
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0

def find_available_port(start_port, max_attempts=10):
    """Find an available port starting from start_port."""
    port = start_port
    for _ in range(max_attempts):
        if not is_port_in_use(port):
            return port
        port += 1
    return None

def start_service(service_name, port=None, auto_open_browser=False):
    """Start a service and track its process."""
    if service_name not in SERVICES:
        print_error(f"Unknown service: {service_name}")
        return False
    
    service = SERVICES[service_name]
    print_step("START", f"Starting {service_name} service...")
    
    # Check if already running
    if service_name in running_processes and running_processes[service_name].poll() is None:
        print_warning(f"{service_name} is already running")
        return True
    
    try:
        env = os.environ.copy()
        
        # Determine port to use
        if port is None:
            port = service["default_port"]
        
        # Check if port is in use
        if is_port_in_use(port):
            print_warning(f"Port {port} is already in use")
            
            # Try to find an available port
            available_port = find_available_port(port + 1)
            if available_port:
                print_info(f"Using alternative port: {available_port}")
                port = available_port
            else:
                print_error(f"Could not find an available port for {service_name}")
                return False
        
        # Set port in environment
        if service["port_env_var"]:
            env[service["port_env_var"]] = str(port)
        
        # Store actual port used
        service["current_port"] = port
        
        # Add service-specific environment variables
        if service_name == "ts-services":
            # Ensure OPENAI_API_KEY is set for ts-services
            if "OPENAI_API_KEY" not in env:
                api_key = input("Enter your OpenAI API key (press Enter to skip): ").strip()
                if api_key:
                    env["OPENAI_API_KEY"] = api_key
                else:
                    print_warning("No OpenAI API key provided. Summaries will not work properly.")
        
        # Handle Next.js specific port setting for frontend
        if service_name == "frontend":
            # Next.js uses a different env var for port
            env["PORT"] = str(port)
            
            # For Next.js, we can set the port directly in the command
            cmd = service["start_cmd"].copy()
            cmd.extend(["--port", str(port)])
        else:
            cmd = service["start_cmd"]
        
        # Start the service
        process = subprocess.Popen(
            cmd,
            cwd=service["dir"],
            env=env
        )
        
        running_processes[service_name] = process
        print_success(f"{service_name} started successfully (PID: {process.pid}, Port: {port})")
        
        # Open browser if requested and it's the frontend
        if service_name == "frontend" and auto_open_browser:
            # Wait a moment for the server to start
            time.sleep(2)
            url = f"http://localhost:{port}"
            print_step("BROWSER", f"Opening {url} in your browser...")
            webbrowser.open(url)
            
        return True
    
    except Exception as e:
        print_error(f"Failed to start {service_name}: {str(e)}")
        return False

def stop_service(service_name):
    """Stop a running service."""
    if service_name not in running_processes:
        print_warning(f"{service_name} is not running")
        return True
    
    process = running_processes[service_name]
    if process.poll() is not None:
        print_warning(f"{service_name} is not running")
        running_processes.pop(service_name, None)
        return True
    
    print_step("STOP", f"Stopping {service_name} service (PID: {process.pid})...")
    
    try:
        # Try to terminate gracefully first
        process.terminate()
        
        # Wait for up to 5 seconds for process to terminate
        for _ in range(10):
            if process.poll() is not None:
                break
            time.sleep(0.5)
        
        # If still running, kill it
        if process.poll() is None:
            process.kill()
            process.wait()
        
        running_processes.pop(service_name, None)
        print_success(f"{service_name} stopped successfully")
        return True
    
    except Exception as e:
        print_error(f"Failed to stop {service_name}: {str(e)}")
        return False

def collect_instagram_data(data_type, username=None, limit=None):
    """Collect Instagram data using the backend scripts."""
    print_header("Instagram Data Collection")
    
    if data_type not in ["direct-feed", "user-media"]:
        print_error(f"Unknown data type: {data_type}")
        return False
    
    # Build command based on data type
    if data_type == "direct-feed":
        cmd = ["python", "scripts/collect_direct_feed.py"]
        if limit:
            cmd.extend(["--limit", str(limit)])
    elif data_type == "user-media":
        if not username:
            print_error("Username is required for collecting user media")
            return False
        cmd = ["python", "scripts/collect_user_media.py", username]
    
    print_step("COLLECT", f"Collecting {data_type} data...")
    result = run_command(cmd, cwd=BACKEND_DIR)
    
    if result:
        print_success(f"Successfully collected {data_type} data")
    else:
        print_error(f"Failed to collect {data_type} data")
        # If data collection fails, suggest starting the frontend
        print_warning("Data collection failed. Would you like to start the frontend anyway? [y/N]")
        response = input().strip().lower()
        if response == 'y':
            start_frontend()
    
    return result

def process_data():
    """Process Instagram data using TS services."""
    print_header("Data Processing")
    
    # Check if TS services are running, start if not
    if "ts-services" not in running_processes or running_processes["ts-services"].poll() is not None:
        start_service("ts-services")
    
    # Run the data processing commands
    print_step("PROCESS", "Processing and scoring posts...")
    run_command(["npm", "run", "top-daily"], cwd=TS_SERVICES_DIR)
    
    print_step("SUMMARIZE", "Generating post summaries...")
    run_command(["npm", "run", "summarize"], cwd=TS_SERVICES_DIR)
    
    print_success("Data processing complete")
    return True

def start_frontend(port=None, auto_open_browser=True):
    """Start the frontend server and optionally open browser."""
    print_header("Frontend")
    
    if start_service("frontend", port=port, auto_open_browser=auto_open_browser):
        # Get the actual port that was used
        actual_port = SERVICES["frontend"].get("current_port", SERVICES["frontend"]["default_port"])
        
        print_success(f"Frontend is now running on port {actual_port}")
        
        # If we didn't auto-open but want to show the URL
        if not auto_open_browser:
            url = f"http://localhost:{actual_port}"
            print_info(f"Access the frontend at: {url}")
            
        return True
    else:
        print_error("Failed to start frontend")
        return False

def start_all_services(auto_open_browser=False):
    """Start all services in the correct order."""
    print_header("Starting All Services")
    
    services_started = []
    try:
        # Start backend first
        if start_service("backend"):
            services_started.append("backend")
            time.sleep(1)  # Give backend time to initialize
        
        # Start TS services next
        if start_service("ts-services"):
            services_started.append("ts-services")
            time.sleep(1)
        
        # Start frontend last
        if start_service("frontend", auto_open_browser=auto_open_browser):
            services_started.append("frontend")
            
            # Get the actual port that was used
            actual_port = SERVICES["frontend"].get("current_port", SERVICES["frontend"]["default_port"])
            
            # If we didn't auto-open but want to show the URL
            if not auto_open_browser:
                url = f"http://localhost:{actual_port}"
                print_info(f"Access the frontend at: {url}")
        
        if len(services_started) == 3:
            print_success("All services started successfully")
            return True
        else:
            print_warning(f"Only {', '.join(services_started)} services started successfully")
            return False
    
    except Exception as e:
        print_error(f"Error starting services: {str(e)}")
        return False

def stop_all_services():
    """Stop all running services."""
    print_header("Stopping All Services")
    
    all_stopped = True
    # Stop in reverse order
    for service in ["frontend", "ts-services", "backend"]:
        if service in running_processes:
            if not stop_service(service):
                all_stopped = False
    
    if all_stopped:
        print_success("All services stopped successfully")
    else:
        print_warning("Some services failed to stop properly")
    
    return all_stopped

def check_environment():
    """Check if the environment is properly set up."""
    print_header("Environment Check")
    
    issues = []
    
    # Check Python
    print_step("CHECK", "Checking Python environment...")
    try:
        python_version = subprocess.check_output(["python", "--version"], text=True).strip()
        print_info(f"Python: {python_version}")
        
        # Check for required Python packages
        if os.path.exists(SERVICES["backend"]["requirements"]):
            with open(SERVICES["backend"]["requirements"], 'r') as f:
                required_packages = [line.strip() for line in f if line.strip() and not line.startswith('#')]
            
            missing_packages = []
            for package in required_packages:
                package_name = package.split('==')[0]
                try:
                    __import__(package_name)
                except ImportError:
                    missing_packages.append(package)
            
            if missing_packages:
                issues.append(f"Missing Python packages: {', '.join(missing_packages)}")
                print_warning(f"Missing {len(missing_packages)} Python packages")
            else:
                print_success("All Python packages installed")
        else:
            print_warning("Could not find requirements.txt")
    except Exception as e:
        issues.append(f"Python check failed: {str(e)}")
        print_error(f"Python check failed: {str(e)}")
    
    # Check Node.js
    print_step("CHECK", "Checking Node.js environment...")
    try:
        node_version = subprocess.check_output(["node", "--version"], text=True).strip()
        npm_version = subprocess.check_output(["npm", "--version"], text=True).strip()
        print_info(f"Node.js: {node_version}, npm: {npm_version}")
        
        # Check TS services dependencies
        ts_node_modules = os.path.join(TS_SERVICES_DIR, "node_modules")
        if not os.path.exists(ts_node_modules):
            issues.append("TS services dependencies not installed")
            print_warning("TS services dependencies not installed")
        else:
            print_success("TS services dependencies installed")
        
        # Check frontend dependencies
        frontend_node_modules = os.path.join(FRONTEND_DIR, "node_modules")
        if not os.path.exists(frontend_node_modules):
            issues.append("Frontend dependencies not installed")
            print_warning("Frontend dependencies not installed")
        else:
            print_success("Frontend dependencies installed")
    except Exception as e:
        issues.append(f"Node.js check failed: {str(e)}")
        print_error(f"Node.js check failed: {str(e)}")
    
    # Check for session file
    session_file = os.path.join(BACKEND_DIR, "session.json")
    if not os.path.exists(session_file):
        issues.append("Instagram session file not found")
        print_warning("Instagram session file not found - login will be required")
    else:
        print_success("Instagram session file found")
    
    # Print summary
    print_header("Environment Summary")
    if issues:
        print_warning("Issues detected:")
        for i, issue in enumerate(issues, 1):
            print_styled(f"  {i}. {issue}", "yellow")
    else:
        print_success("Environment is properly set up")
    
    return issues

def setup_environment():
    """Set up the environment by installing dependencies."""
    print_header("Environment Setup")
    
    # Install Python dependencies
    print_step("SETUP", "Installing Python dependencies...")
    run_command(SERVICES["backend"]["env_setup"].split(), cwd=BACKEND_DIR)
    
    # Install TS services dependencies
    print_step("SETUP", "Installing TS services dependencies...")
    run_command(SERVICES["ts-services"]["install_cmd"], cwd=TS_SERVICES_DIR)
    
    # Install frontend dependencies
    print_step("SETUP", "Installing frontend dependencies...")
    run_command(SERVICES["frontend"]["install_cmd"], cwd=FRONTEND_DIR)
    
    print_success("Environment setup complete")
    return True

def status():
    """Check the status of all services and ports."""
    print_header("Service Status")
    
    all_services = ["backend", "ts-services", "frontend"]
    
    for service in all_services:
        service_config = SERVICES[service]
        default_port = service_config["default_port"]
        current_port = service_config.get("current_port", default_port)
        
        # Check if process is running
        is_running = service in running_processes and running_processes[service].poll() is None
        
        if is_running:
            pid = running_processes[service].pid
            print_styled(f"● {service.ljust(12)}", "green", newline=False)
            print(f"Running (PID: {pid}, Port: {current_port})")
            
            # Check if the port is actually in use
            if is_port_in_use(current_port):
                print_styled("  └─ ", "dim", newline=False)
                print_styled(f"Port {current_port} is active", "green")
            else:
                print_styled("  └─ ", "dim", newline=False)
                print_styled(f"Warning: Port {current_port} is not active", "yellow")
        else:
            print_styled(f"○ {service.ljust(12)}", "red", newline=False)
            print(f"Stopped (Default Port: {default_port})")
            
            # Check if the default port is in use by something else
            if is_port_in_use(default_port):
                print_styled("  └─ ", "dim", newline=False)
                print_styled(f"Warning: Port {default_port} is in use by another process", "yellow")
    
    print("\nUse 'python instatldr.py start <service> --port <port>' to specify a custom port")
    print("Use 'python instatldr.py start <service> --no-browser' to prevent auto-opening the browser")
    
    return True

def handle_sigint(sig, frame):
    """Handle SIGINT (Ctrl+C) by stopping all services."""
    print("\n")
    print_warning("Received interrupt signal. Stopping all services...")
    stop_all_services()
    sys.exit(0)

def main():
    """Main entry point for the CLI."""
    signal.signal(signal.SIGINT, handle_sigint)
    
    parser = argparse.ArgumentParser(description="InstaTLDR Command Line Interface")
    
    # Create subparsers for different commands
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # start command
    start_parser = subparsers.add_parser("start", help="Start services")
    start_parser.add_argument("service", nargs="?", choices=["all", "backend", "ts-services", "frontend"],
                             default="all", help="Service to start (default: all)")
    start_parser.add_argument("--port", "-p", type=int, 
                             help="Port to use (for single service start only)")
    start_parser.add_argument("--no-browser", "-n", action="store_true",
                             help="Do not automatically open browser for frontend")
    
    # stop command
    stop_parser = subparsers.add_parser("stop", help="Stop services")
    stop_parser.add_argument("service", nargs="?", choices=["all", "backend", "ts-services", "frontend"],
                            default="all", help="Service to stop (default: all)")
    
    # collect command
    collect_parser = subparsers.add_parser("collect", help="Collect Instagram data")
    collect_parser.add_argument("data_type", choices=["direct-feed", "user-media"],
                              help="Type of data to collect")
    collect_parser.add_argument("--username", "-u", help="Username for user-media collection")
    collect_parser.add_argument("--limit", "-l", type=int, help="Limit number of posts to collect")
    
    # process command
    process_parser = subparsers.add_parser("process", help="Process collected data")
    
    # frontend command
    frontend_parser = subparsers.add_parser("frontend", help="Start the frontend server")
    frontend_parser.add_argument("--port", "-p", type=int, help="Port to use for frontend server")
    frontend_parser.add_argument("--no-browser", "-n", action="store_true",
                               help="Do not automatically open browser")
    
    # check command
    check_parser = subparsers.add_parser("check", help="Check environment")
    
    # setup command
    setup_parser = subparsers.add_parser("setup", help="Set up environment")
    
    # status command
    status_parser = subparsers.add_parser("status", help="Check service status")
    
    # Parse arguments
    args = parser.parse_args()
    
    # Print ASCII art
    print(ASCII_ART)
    
    # Handle commands
    if args.command is None:
        # If no command is provided, show help
        parser.print_help()
        return
    
    elif args.command == "start":
        auto_open_browser = not getattr(args, 'no_browser', False)
        
        if args.service == "all":
            start_all_services(auto_open_browser=auto_open_browser)
        else:
            # Only use custom port for single service start
            port = getattr(args, 'port', None)
            if args.service == "frontend":
                start_service(args.service, port=port, auto_open_browser=auto_open_browser)
            else:
                start_service(args.service, port=port)
    
    elif args.command == "stop":
        if args.service == "all":
            stop_all_services()
        else:
            stop_service(args.service)
    
    elif args.command == "collect":
        collect_instagram_data(args.data_type, args.username, args.limit)
    
    elif args.command == "process":
        process_data()
    
    elif args.command == "frontend":
        port = getattr(args, 'port', None)
        auto_open_browser = not getattr(args, 'no_browser', False)
        start_frontend(port=port, auto_open_browser=auto_open_browser)
    
    elif args.command == "check":
        check_environment()
    
    elif args.command == "setup":
        setup_environment()
    
    elif args.command == "status":
        status()
    
    else:
        print_error(f"Unknown command: {args.command}")

if __name__ == "__main__":
    main()