# =====================================================================================
# Console Output Colors
# =====================================================================================
# Note: The \001 and \002 ANSI character act as wrappers to tell readline that these are NON-PRINTABLE CHARACTERS!
# These are required to ensure correct handling of command history, auto-completion etc. Otherwise... weird things happen
COLOR_N             = '\001\033[m\002'  # native
COLOR_R             = '\001\033[31m\002'  # red
COLOR_G             = '\001\033[32m\002'  # green
COLOR_G_BOLD        = '\001\033[1;32m\002'  # green
COLOR_O             = '\001\033[33m\002'  # orange
COLOR_B             = '\001\033[34m\002'  # blue
COLOR_RNGX_BOLD     = '\001\033[1;38;2;100;218;222;49m\002' # Recon-NGX Branding Color

