# Some stuff from osx oh-my-zsh config
# https://github.com/robbyrussell/oh-my-zsh/blob/master/plugins/osx/osx.plugin.zsh

alias fixui="killall -KILL Dock"
alias fixui!="sudo killall -HUP WindowServer"

function pfd() {
    osascript 2>/dev/null <<EOF
    tell application "Finder"
      return POSIX path of (target of window 1 as alias)
    end tell
EOF
}


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

function cdf() {
    cd "$(pfd)"
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