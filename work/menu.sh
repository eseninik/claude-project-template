#!/bin/bash
# Simple menu for tmux sessions
export PATH="/home/admin/.local/bin:$PATH"

clear
echo ""
echo "  =============================="
echo "  CONTABO DEV SERVER"
echo "  =============================="
echo ""

# Collect active sessions
sess_list=""
i=1
if tmux ls 2>/dev/null | grep -q ':'; then
    echo "  ACTIVE SESSIONS:"
    echo "  -----------------"
    while IFS= read -r line; do
        name=$(echo "$line" | cut -d: -f1)
        windows=$(echo "$line" | grep -o '[0-9]* windows' | head -1)
        sess_list="${sess_list}${i}=${name} "
        echo "  ${i}) ${name}  (${windows})"
        i=$((i+1))
    done < <(tmux ls 2>/dev/null)
    echo ""
fi

# Collect projects
echo "  NEW SESSION:"
echo "  -----------------"
proj_list=""
for dir in /home/admin/dev/*/; do
    name=$(basename "$dir")
    [ "$name" = "menu.sh" ] && continue
    [ "$name" = "projects.sh" ] && continue
    proj_list="${proj_list}${i}=${name} "
    echo "  ${i}) + ${name}"
    i=$((i+1))
done

echo ""
echo "  q) quit"
echo ""
read -p "  > " choice

[ "$choice" = "q" ] && exit 0
[ -z "$choice" ] && exit 0

# Find in sessions
for pair in $sess_list; do
    num=$(echo "$pair" | cut -d= -f1)
    name=$(echo "$pair" | cut -d= -f2)
    if [ "$num" = "$choice" ]; then
        tmux attach -t "$name"
        exit 0
    fi
done

# Find in projects
for pair in $proj_list; do
    num=$(echo "$pair" | cut -d= -f1)
    name=$(echo "$pair" | cut -d= -f2)
    if [ "$num" = "$choice" ]; then
        read -p "  Session name [$name]: " sname
        sname=${sname:-$name}
        tmux new-session -s "$sname" -c "/home/admin/dev/$name"
        exit 0
    fi
done

echo "  Invalid choice"
