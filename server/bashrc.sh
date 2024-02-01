# ~/.bashrc: executed by bash(1) for non-login shells.

export SHELL=bash

# Some bash completion (for debugging purposes)
if [ -f /etc/bash_completion ]; then
 . /etc/bash_completion
fi

# Note: PS1 and umask are already set in /etc/profile. You should not
# need this unless you want different defaults for root.
# PS1='${debian_chroot:+($debian_chroot)}\h:\w\$ '
PS1='\[\e]0;\u@\h: \w\a\]\[\033[01;32m\]\u@\h\[\033[00m\]:\[\033[01;34m\]\w\[\033[00m\]$ '
umask 022

# You may uncomment the following lines if you want `ls' to be colorized:
export LS_OPTIONS='--color=auto'
eval "$(dircolors)"
alias ls='ls $LS_OPTIONS'
alias ll='ls $LS_OPTIONS -l'
alias l='ls $LS_OPTIONS -lA'

# Some more alias to avoid making mistakes:
# alias rm='rm -i'
# alias cp='cp -i'
# alias mv='mv -i'

alias refresh='__curuserpath="$(pwd -P)" && rm -rf /$HOME/cps-software && cp -r /mnt /$HOME/cps-software && cd $__curuserpath && unset __curuserpath'
