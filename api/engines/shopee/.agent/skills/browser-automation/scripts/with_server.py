#!/usr/bin/env python3
"""
Server Manager Script - Manage server lifecycle for webapp testing
"""

import argparse
import subprocess
import sys
import time
import signal
import os
import socket
from pathlib import Path
from typing import List, Optional

def parse_args():
    parser = argparse.ArgumentParser(
        description='Manage server lifecycle for webapp testing',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  # Single server
  python with_server.py --server "npm run dev" --port 5173 -- python test.py

  # Multiple servers (backend + frontend)
  python with_server.py \\
    --server "cd backend && python server.py" --port 3000 \\
    --server "cd frontend && npm run dev" --port 5173 \\
    -- python test.py

  # With custom startup timeout
  python with_server.py --server "npm run dev" --port 5173 --timeout 60 -- python test.py
        '''
    )
    
    parser.add_argument('--server', action='append', nargs=2, metavar=('CMD', 'PORT'),
                        help='Server command and port (can be specified multiple times)')
    parser.add_argument('--timeout', type=int, default=30, help='Startup timeout in seconds')
    parser.add_argument('--delay', type=int, default=1000, help='Delay after server ready (ms)')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    parser.add_argument('command', nargs=argparse.REMAINDER, help='Command to run after servers are ready')
    
    return parser.parse_args()

def is_port_open(port: int, host: str = 'localhost') -> bool:
    """Check if a port is open."""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0
    except:
        return False

def wait_for_port(port: int, timeout: int = 30, verbose: bool = False) -> bool:
    """Wait for a port to become available."""
    start_time = time.time()
    while time.time() - start_time < timeout:
        if is_port_open(port):
            if verbose:
                print(f"Port {port} is ready")
            return True
        time.sleep(0.5)
    return False

def kill_process_on_port(port: int) -> bool:
    """Kill any process using the specified port."""
    try:
        if sys.platform == 'win32':
            # Windows: use netstat and taskkill
            result = subprocess.run(
                f'netstat -ano | findstr :{port}',
                shell=True,
                capture_output=True,
                text=True
            )
            if result.stdout:
                lines = result.stdout.strip().split('\n')
                for line in lines:
                    parts = line.split()
                    if len(parts) >= 5:
                        pid = parts[-1]
                        subprocess.run(f'taskkill /F /PID {pid}', shell=True, capture_output=True)
        else:
            # Unix: use lsof
            subprocess.run(f'lsof -ti:{port} | xargs kill -9', shell=True, capture_output=True)
        return True
    except:
        return False

class ServerManager:
    def __init__(self, verbose: bool = False):
        self.processes: List[subprocess.Popen] = []
        self.verbose = verbose
    
    def start_server(self, cmd: str, port: int, timeout: int = 30) -> bool:
        """Start a server and wait for it to be ready."""
        
        # Check if port is already in use
        if is_port_open(port):
            print(f"Warning: Port {port} is already in use")
            return True
        
        if self.verbose:
            print(f"Starting server: {cmd}")
        
        # Start the server process
        process = subprocess.Popen(
            cmd,
            shell=True,
            stdout=subprocess.PIPE if not self.verbose else None,
            stderr=subprocess.PIPE if not self.verbose else None,
            preexec_fn=os.setsid if sys.platform != 'win32' else None
        )
        self.processes.append(process)
        
        # Wait for the port to be ready
        if wait_for_port(port, timeout, self.verbose):
            print(f"Server ready on port {port}")
            return True
        else:
            print(f"Error: Server failed to start on port {port} within {timeout}s")
            return False
    
    def stop_all(self):
        """Stop all managed server processes."""
        for process in self.processes:
            try:
                if sys.platform == 'win32':
                    process.terminate()
                else:
                    os.killpg(os.getpgid(process.pid), signal.SIGTERM)
            except:
                pass
        self.processes.clear()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop_all()

def main():
    args = parse_args()
    
    # Parse server configurations
    servers = []
    if args.server:
        for cmd, port in args.server:
            servers.append((cmd, int(port)))
    
    if not servers:
        print("Error: No servers specified. Use --server 'CMD' PORT")
        sys.exit(1)
    
    # Get the command to run
    if not args.command or args.command[0] != '--':
        print("Error: No command specified. Use -- command args...")
        sys.exit(1)
    
    command = args.command[1:]
    if not command:
        print("Error: Empty command after --")
        sys.exit(1)
    
    # Start servers and run command
    with ServerManager(verbose=args.verbose) as manager:
        # Start all servers
        for cmd, port in servers:
            if not manager.start_server(cmd, port, args.timeout):
                sys.exit(1)
        
        # Additional delay after all servers are ready
        if args.delay > 0:
            time.sleep(args.delay / 1000)
        
        print(f"Running command: {' '.join(command)}")
        
        # Run the command
        try:
            result = subprocess.run(command)
            sys.exit(result.returncode)
        except KeyboardInterrupt:
            print("\nInterrupted")
            sys.exit(130)
        except Exception as e:
            print(f"Error running command: {e}")
            sys.exit(1)

if __name__ == '__main__':
    main()
