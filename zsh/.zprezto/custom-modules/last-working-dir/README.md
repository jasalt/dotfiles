# Last Working Directory  
  
Persists the last working directory across shell sessions, with opt-in automatic restoration when opening a new terminal in the home directory.  
  
## Functions  
  
- `lwd` - Changes directory to the last working directory from the previous session  
  
## Behavior  
  
- Automatically saves the current directory when you change directories  
- Automatic restoration is disabled by default; `lwd` remains available
- When automatic restoration is enabled, startup in `$HOME` changes to the last working directory  
- Uses a cache file in `$XDG_CACHE_HOME/prezto/last-working-dir` (or `$HOME/.cache/prezto/last-working-dir`)  
- Adds `.$SSH_USER` suffix to cache file if `$SSH_USER` is set (useful for SSH sessions)  
  
## Configuration  
  
Enable the module in `~/.zpreztorc` to track directories and use `lwd` manually.

To opt in to automatic restoration, add:

```zsh
zstyle ':prezto:module:last-working-dir' auto-restore 'yes'
```

Leave the setting unset or use `'no'` to disable automatic restoration without disabling tracking or `lwd`.
