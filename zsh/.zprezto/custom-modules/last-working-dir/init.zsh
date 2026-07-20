#  
# Persists the last working directory across shell sessions.  
# Similar to oh-my-zsh module of same name.
#  
# Authors:  
#   jasalt
#  

# Cache file must remain available to hooks after the module loader returns  
typeset -g ZSH_LAST_WORKING_DIRECTORY_FILE="${XDG_CACHE_HOME:-$HOME/.cache}/prezto/last-working-dir${SSH_USER:+.$SSH_USER}"  
  
# Ensure cache directory exists (using :h to get directory part)  
[[ -d "$ZSH_LAST_WORKING_DIRECTORY_FILE:h" ]] || mkdir -p "$ZSH_LAST_WORKING_DIRECTORY_FILE:h"  
  
# Flag indicating if we've previously jumped to last directory  
typeset -g ZSH_LAST_WORKING_DIRECTORY  
  
# Updates the last directory once directory is changed  
function chpwd_last_working_dir {  
  # Don't run in subshells  
  [[ "$ZSH_SUBSHELL" -eq 0 ]] || return 0  
  'builtin' 'echo' '-E' "$PWD" >| "$ZSH_LAST_WORKING_DIRECTORY_FILE"  
}  
  
# Changes directory to the last working directory  
function lwd {  
  [[ -r "$ZSH_LAST_WORKING_DIRECTORY_FILE" ]] && cd "$(<"$ZSH_LAST_WORKING_DIRECTORY_FILE")"  
}  
  
# Add hook for directory changes  
autoload -Uz add-zsh-hook  
add-zsh-hook chpwd chpwd_last_working_dir  
  
# Jump to last directory automatically unless:  
# - This isn't the first time the module is loaded  
# - We're not in the $HOME directory (e.g. if terminal opened a different folder)  
if [[ -z "$ZSH_LAST_WORKING_DIRECTORY" ]] && [[ "$PWD" == "$HOME" ]]; then  
  if lwd 2>/dev/null; then  
    ZSH_LAST_WORKING_DIRECTORY=1  
  fi  
fi
