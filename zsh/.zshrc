#
# Executes commands at the start of an interactive session.
#
# Authors:
#   Sorin Ionescu <sorin.ionescu@gmail.com>
#

# Source Prezto.
if [[ -s "${ZDOTDIR:-$HOME}/.zprezto/init.zsh" ]]; then
  source "${ZDOTDIR:-$HOME}/.zprezto/init.zsh"
fi

# Customize to your needs...

eval "$(zoxide init zsh)"

# Source these
. "${ZDOTDIR:-$HOME}/.zprezto/custom.zsh"
. "${ZDOTDIR:-$HOME}/.zprezto/ohmy.zsh"
