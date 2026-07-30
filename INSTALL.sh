#!/bin/bash
# =====================================================================================
# Recon-NGX ==> Installer Script
# =====================================================================================

# =====================================================================================
# Functions
# =====================================================================================
function output()
{
  echo "[+] $1"
}

# =====================================================================================
# Set Paths
# =====================================================================================
RECON_NGX_PATH=`dirname $(realpath $0)`

# =====================================================================================
# Build Virtual Environment
# =====================================================================================
VENV_PATH=$RECON_NGX_PATH/.venv
if [ ! -d "$VENV_PATH" ]; then
  output "Creating Virtual Environment. Please wait..."
  python -m venv "$VENV_PATH"
fi

# =====================================================================================
# Install Requirements
# =====================================================================================
output "Installing Dependencies. Please Wait..."
sleep 1
source "$RECON_NGX_PATH/.venv/bin/activate"
python -m pip install --upgrade pip setuptools wheel
python -m pip install -r "$RECON_NGX_PATH/requirements.txt"
output "Dependencies installed"

# =====================================================================================
# Create binary
# =====================================================================================
cp -f "$RECON_NGX_PATH/resources/recon-ngx" ~/.local/bin
chmod u+x ~/.local/bin/recon-ngx
sed -i "s|<<HOME_PATH>>|$RECON_NGX_PATH|" ~/.local/bin/recon-ngx
output "Binary created"

output "Installation Complete. Run 'recon-ngx' to start the application"
