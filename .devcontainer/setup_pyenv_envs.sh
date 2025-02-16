#!/usr/bin/env bash
set -e

# Ensure pyenv and pyenv-virtualenv are available.
export PYENV_ROOT="/home/vscode/.pyenv"
export PATH="${PYENV_ROOT}/bin:${PATH}"
eval "$(pyenv init -)"
eval "$(pyenv virtualenv-init -)"

# Set the default Python version to use for creating virtualenvs.
default_python_version="3.12.9"

# Change to the workspace directory (which is mounted in your dev container)
cd /workspace

# Loop over each top-level directory in the workspace.
for dir in */; do
    # Remove the trailing slash to get the project name.
    project="${dir%/}"
    version_file="$project/.python-version"
    
    if [ -f "$version_file" ]; then
        # Read the virtualenv name from the file.
        venv_name=$(cat "$version_file" | tr -d '[:space:]')
        
        if [ -z "$venv_name" ]; then
            echo "Skipping $project: .python-version file is empty."
            continue
        fi

        # Create the virtualenv if it doesn't already exist.
        if ! pyenv virtualenvs --bare | grep -Fxq "$venv_name"; then
            echo "Creating virtualenv '$venv_name' from base version '$default_python_version' for project '$project'."
            pyenv virtualenv "$default_python_version" "$venv_name"
        else
            echo "Virtualenv '$venv_name' already exists for project '$project'."
        fi

        # If a requirements.txt file exists, install its dependencies.
        requirements_file="$project/requirements.txt"
        if [ -f "$requirements_file" ]; then
            echo "Installing dependencies from $requirements_file for project '$project'."
            # Use pyenv to set the local shell to this virtualenv.
            pyenv shell "$venv_name"
            # Change to the project directory and install dependencies.
            (cd "$project" && pip install -r requirements.txt)
            # Unset the local pyenv version to avoid interfering with subsequent commands.
            pyenv shell --unset
        fi
    else
        echo "No .python-version file in project '$project'. Skipping."
    fi
done
