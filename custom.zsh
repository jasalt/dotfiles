# Zsh config for MacOS and GNU/Linux desktop
# Contains common and platform specific hacky aliases etc to keep some compatibility.

# Also using https://github.com/darksonic37/linuxify/ on MacOS.
# For extra zsh plugin management (native zsh, not oh-my-zsh) use https://github.com/zplug/zplug

## .zshrc notes
# These are not saved to repo now but generally useful plugins are:
#   plugins=(sudo last-working-dir git autojump extract)
# And for MacOS plugin 'osx' and for Debian based distros 'debian'.


export PATH="$PATH:$HOME/.bin"  # see https://github.com/jasalt/bin

### ZSH options

# # Enable character expansion
# setopt braceccl
# # Allow empty glob entries
# setopt null_glob
# # Allow empty glob entries
# setopt extended_glob

# set -o ignoreeof

# autoload bashcompinit
# bashcompinit

# # wp-cli completion
# source `dirname "$0"`/completion/wp-completion.bash  # TODO usable with containers?

# Rebind kill-region for zsh
# bindkey '^w' kill-region


### Aliases
alias rp="source ~/.zshrc" # Reload shell profile

## Clipboard and file manager utilities
alias cdd="cd ~/Desktop/"
alias sl="ls"

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

# Using `cb` as generic command for copying stuff to clipboard
if [ $(uname -s) = "Linux" ]; then
  # TODO
elif [ $(uname -s) = "Darwin" ]; then
    alias cb="clipcopy"
    alias cbp="clippaste"
fi

function abspath() {
    # generate absolute path from relative path
    # $1     : relative filename
    # return : absolute path
    if [ -d "$1" ]; then
        # dir
        (cd "$1"; pwd)
    elif [ -f "$1" ]; then
        # file
        if [[ $1 == */* ]]; then
            echo "$(cd "${1%/*}"; pwd)/${1##*/}"
        else
            echo "$(pwd)/$1"
        fi
    fi
}

alias cbwd="pwd|cb"  # copy shell working directory to clipboard
alias pfp="abspath"  # print shell file path
alias cbfp="$(abspath $1) | cb"  # copy shell file path to clipboard

if [ $(uname -s) = "Linux" ]; then
    # TODO
elif [ $(uname -s) = "Darwin" ]; then

# print finder directory
function pfd() {
    osascript 2>/dev/null <<EOF
    tell application "Finder"
    return POSIX path of (target of window 1 as alias)
    end tell
EOF
}

# cd to finder directory
function cdf() {
    cd "$(pfd)"
}

fi

# Copy SSH public key quickly to clipboard to paste it somewhere,
# see ssh-copy-id command when working directly with ssh-remotes.
alias cbssh="cat ~/.ssh/id_ecdsa.pub|cb"  # TODO update to ecdsa key

### Networking helpers
# Echo public IP
alias myip="curl -s checkip.dyndns.org | sed -e 's/.*Current IP Address: //' -e 's/<.*$//'"
alias ports="lsof -Pni4 | grep LISTEN"  # List open ports
alias speedtest="ping -c 3 www.funet.fi && wget -O /dev/null ftp://ftp.funet.fi/dev/100Mnull > /dev/null"

# Download subtitles, requires sudo pip install subliminal
alias sub="subliminal download -l en"

alias tsvlens="csvlens -t"

## These are from ohmyzsh git plugin
# alias ga="git add"
# alias gp="git push"
# alias gl="git pull"
# alias gc="git commit"
# alias gcm="git commit -m"

# Package manager aliases
if [ $(uname -s) = "Linux" ]; then
    alias aup="sudo apt update"
    alias aug="sudo apt upgrade"
    alias ai="sudo apt install"
    alias as="sudo apt search"
    alias alog="less /var/log/apt/history.log"
    addppa () {
        # Add PPA Repository on Ubuntu
        sudo add-apt-repository $1
        sudo apt-get update
    }
elif [ $(uname -s) = "Darwin" ]; then
    alias aup="brew update"
    alias aug="brew upgrade"
    alias ai="brew install"
    alias ar="brew uninstall"
    alias as="brew search"
    alias ass="brew cask search"
    alias cask="brew cask"
    alias aii="brew install --cask"
fi

# PostgreSQL database startup/shutdown aliases
if [ $(uname -s) = "Linux" ]; then
    alias postgre-start="sudo service postgresql start"
    alias postgre-stop="sudo service postgresql stop"
elif [ $(uname -s) = "Darwin" ]; then
    alias pgup="pg_ctl -D /usr/local/var/postgres start"
    alias pgdown="pg_ctl -D /usr/local/var/postgres stop"
fi

# Speech to text aliases for different languages
if [ $(uname -s) = "Linux" ]; then
    alias say="espeak"
    alias sano="espeak -v europe/fi"
    alias sega="espeak -v europe/sv"
elif [ $(uname -s) = "Darwin" ]; then
    alias sano="say -v \"Satu\""
    alias sega="say -v \"Oskar\""
fi

### Language translation utilities
# See also: Linux selection hotkeys on sxhkd config
# Using http://www.soimort.org/translate-shell/ depends on gawk
# Mac: brew install http://www.soimort.org/translate-shell/translate-shell.rb
# Linux: wget git.io/trans && chmod +x ./trans
# alias te="trans fi:en"
# alias tf="trans en:fi"
# alias ts="trans fi:sv"
# alias stf="trans sv:fi"

# # ESC-ESC to sudo last command, already in ohmyzsh sudo plugin
# sudo-command-line() {
#     [[ -z $BUFFER ]] && zle up-history
#     if [[ $BUFFER == sudo\ * ]]; then
#         LBUFFER="${LBUFFER#sudo }"
#     else
#         LBUFFER="sudo $LBUFFER"
#     fi
# }
#zle -N sudo-command-line
# Defined shortcut keys: [Esc] [Esc]
# source ~/dotfiles/shell/shell-fun.zsh

# Misc MacOS aliases
if [ $(uname -s) = "Darwin" ]; then

### Linux command compatibility
alias lsblk="diskutil list"
alias lsusb="system_profiler SPUSBDataType"

alias myipwlan=ipconfig getifaddr en1
alias myiplan=ipconfig getifaddr en0

alias fixui="killall -KILL Dock"
alias fixui!="sudo killall -HUP WindowServer"

function pfs() {
    osascript 2>/dev/null <<EOF
    set output to ""
    tell application "Finder" to set the_selection to selection
    set item_count to count the_selection
    repeat with item_index from 1 to count the_selection
    if item_index is less than item_count then set the_delimiter to "\n"
    if item_index is item_count then set the_delimiter to ""
    set output to output & ((item item_index of the_selection as alias)'s POSIX path) & the_delimiter
    end repeat
EOF
}

function pushdf() {
    pushd "$(pfd)"
}

function quick-look() {
    (( $# > 0 )) && qlmanage -p $* &>/dev/null &
}

function man-preview() {
    man -t "$@" | open -f -a Preview
}

function vncviewer() {
    open vnc://$@
}

fi

