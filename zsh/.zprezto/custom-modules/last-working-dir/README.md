# Last Working Directory  
  
Persists the last working directory across shell sessions and automatically restores it when opening a new terminal in the home directory.  
  
## Functions  
  
- `lwd` - Changes directory to the last working directory from the previous session  
  
## Behavior  
  
- Automatically saves the current directory when you change directories  
- On shell startup, if you're in `$HOME`, it automatically changes to the last working directory  
- Uses a cache file in `$XDG_CACHE_HOME/prezto/last-working-dir` (or `$HOME/.cache/prezto/last-working-dir`)  
- Adds `.$SSH_USER` suffix to cache file if `$SSH_USER` is set (useful for SSH sessions)  
  
## Configuration  
  
No configuration is required. Simply enable the module in `~/.zpreztorc`.
