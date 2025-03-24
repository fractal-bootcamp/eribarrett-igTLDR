#!/bin/bash

# Set environment to testing
export FLASK_ENV=testing

# Check if user has passed command line arguments
if [ $# -eq 0 ]; then
    # Run all tests
    echo "Running all tests..."
    python -m pytest -v
else
    # Run specific tests based on command line arguments
    echo "Running specified tests..."
    python -m pytest -v $@
fi 