# Executed at the start of an interactive session

if [[ -s "${ZDOTDIR:-$HOME}/.zprezto/init.zsh" ]]; then
  source "${ZDOTDIR:-$HOME}/.zprezto/init.zsh"
fi

. $HOME/.locals.sh

export PATH=$PATH:$HOME/.bin:$HOME/.local/bin
export PATH=$PATH:$(go env GOPATH)/bin

# Installed from OS package manager (TODO check)
eval "$(zoxide init zsh)"

##### Aliases / Functions

alias rp="source ~/.zshrc" # Reload shell profile

## Clipboard and file manager utilities
alias cdd="cd ~/Desktop/"
alias sl="ls"

take() {
    mkdir "$1" && cd "$1"
}

# Mac `open` command for Linux using xdg-open
if [ $(uname -s) = "Linux" ]; then
  function open() { xdg-open "$1" &> /dev/null; }  # Suppressing output
fi

# Open current path or argument path with relevant program
function o() {
    if [ -n "$1" ]; then
        open "$1"
    else
        open .
    fi
}

# TODO on symlink, does not resolve the original file
# function abspath() {
#     # generate absolute path from relative path
#     # $1     : relative filename
#     # return : absolute path
#     if [ -d "$1" ]; then
#         # dir
#         (cd "$1"; pwd)
#     elif [ -f "$1" ]; then
#         # file
#         if [[ $1 == */* ]]; then
#             echo "$(cd "${1%/*}"; pwd)/${1##*/}"
#         else
#             echo "$(pwd)/$1"
#         fi
#     fi
# }

# Using `cb` as generic command for copying stuff to clipboard
if [ $(uname -s) = "Linux" ]; then
    alias cb="wl-copy"
elif [ $(uname -s) = "Darwin" ]; then
    alias cb="clipcopy"
    alias cbp="clippaste"
fi

alias cbwd="pwd | cb"
# copy file path to clipboard
cbfp() {
    echo -n "$(realpath "$1")" | cb
}


### Networking helpers
alias myip="curl -s checkip.dyndns.org | sed -e 's/.*Current IP Address: //' -e 's/<.*$//'"
unalias ports 2>/dev/null
ports() { lsof -Pni4 | awk '/LISTEN/{print; system("cat /proc/"$2"/cmdline | tr \"\\000\" \" \"; echo"); print ""}'; podman ps --format '{{.Names}}  {{.Ports}}' 2>/dev/null | grep -- '->'; }  # List open ports + podman binds
alias cbssh="cat ~/.ssh/id_ed25519.pub | cb"  # TODO update to ecdsa key

alias x=unarchive

alias ga="git add"
alias gcm="git commit -m"
alias gst="git status"

# Esc Esc prepends last command with sudo
sudo-last-command() {
  local cmd
  cmd="$(fc -ln -1)" || return

  [[ -z "$cmd" ]] && return
  [[ "$cmd" == sudo\ * ]] || cmd="sudo $cmd"

  BUFFER="$cmd"
  CURSOR=${#BUFFER}
  zle redisplay
}

zle -N sudo-last-command

bindkey -M emacs $'\e\e' sudo-last-command
bindkey -M viins $'\e\e' sudo-last-command
