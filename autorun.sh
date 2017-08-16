#!/bin/sh

name='blackboard'

tmux new-session -s $name -d
tmux set-option -t $name set-remain-on-exit on
tmux new-window -t $name -n server 'python3 server.py'
tmux new-window -t $name -n board 'python3 board.py'
tmux new-window -t $name -n arrange 'python3 arrange_schedule.py'
