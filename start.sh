#!/bin/bash

# Configuration
BACKEND_DIR="server"
FRONTEND_DIR="web"
BACKEND_PID_FILE=".backend.pid"
FRONTEND_PID_FILE=".frontend.pid"
BACKEND_PORT=5001
FRONTEND_PORT=3000
LOGS_DIR="logs"

# Function to check if a process is running
is_running() {
    local pid_file=$1
    if [ -f "$pid_file" ]; then
        local pid=$(cat "$pid_file")
        if ps -p "$pid" > /dev/null; then
            return 0  # Process is running
        else
            rm "$pid_file"  # Remove stale PID file
        fi
    fi
    return 1  # Process is not running
}

# Function to ensure logs directory exists
ensure_logs_dir() {
    if [ ! -d "$LOGS_DIR" ]; then
        echo "Creating logs directory..."
        mkdir -p "$LOGS_DIR"
    fi
}

# Function to start the backend
start_backend() {
    echo "Starting backend server..."
    ensure_logs_dir
    cd "$BACKEND_DIR" || { echo "Error: Backend directory not found"; exit 1; }
    
    # Check if Python virtual environment exists
    if [ -d "venv" ]; then
        source venv/bin/activate
    fi
    
    # Start the backend in the background with logs redirected
    python app.py > "../$LOGS_DIR/backend.log" 2>&1 &
    echo $! > "../$BACKEND_PID_FILE"
    cd ..
    echo "Backend started on http://localhost:$BACKEND_PORT (logs in $LOGS_DIR/backend.log)"
}

# Function to start the frontend
start_frontend() {
    echo "Starting frontend application..."
    ensure_logs_dir
    cd "$FRONTEND_DIR" || { echo "Error: Frontend directory not found"; exit 1; }
    
    # Start the frontend in the background with logs redirected
    npm start > "../$LOGS_DIR/frontend.log" 2>&1 &
    echo $! > "../$FRONTEND_PID_FILE"
    cd ..
    echo "Frontend started on http://localhost:$FRONTEND_PORT (logs in $LOGS_DIR/frontend.log)"
}

# Function to stop the backend
stop_backend() {
    if is_running "$BACKEND_PID_FILE"; then
        echo "Stopping backend server..."
        kill $(cat "$BACKEND_PID_FILE")
        rm "$BACKEND_PID_FILE"
        echo "Backend stopped."
    else
        echo "Backend is not running."
    fi
}

# Function to stop the frontend
stop_frontend() {
    if is_running "$FRONTEND_PID_FILE"; then
        echo "Stopping frontend application..."
        local pid=$(cat "$FRONTEND_PID_FILE")
        # Send SIGTERM for graceful shutdown instead of SIGKILL
        kill -15 "$pid"
        # Wait a moment for the process to terminate gracefully
        sleep 2
        # Check if the process still exists, force kill if necessary
        if ps -p "$pid" > /dev/null; then
            echo "Forcing frontend termination..."
            kill -9 "$pid"
        fi
        rm "$FRONTEND_PID_FILE"
        echo "Frontend stopped."
    else
        echo "Frontend is not running."
    fi
}

# Function to display usage information
show_usage() {
    echo "Usage: $0 {start|stop|restart|status}"
    echo "  start   - Start both frontend and backend"
    echo "  stop    - Stop both frontend and backend"
    echo "  restart - Restart both frontend and backend"
    echo "  status  - Check the status of frontend and backend"
}

# Function to check status
check_status() {
    echo "Checking status..."
    
    if is_running "$BACKEND_PID_FILE"; then
        echo "Backend is running with PID $(cat "$BACKEND_PID_FILE")"
    else
        echo "Backend is not running"
    fi
    
    if is_running "$FRONTEND_PID_FILE"; then
        echo "Frontend is running with PID $(cat "$FRONTEND_PID_FILE")"
    else
        echo "Frontend is not running"
    fi
}

# Main logic based on the provided command
case "$1" in
    start)
        if ! is_running "$BACKEND_PID_FILE"; then
            start_backend
        else
            echo "Backend is already running."
        fi
        
        if ! is_running "$FRONTEND_PID_FILE"; then
            start_frontend
        else
            echo "Frontend is already running."
        fi
        ;;
    stop)
        stop_frontend
        stop_backend
        ;;
    restart)
        stop_frontend
        stop_backend
        sleep 2
        start_backend
        start_frontend
        ;;
    status)
        check_status
        ;;
    *)
        show_usage
        exit 1
        ;;
esac

exit 0 