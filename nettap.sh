dur=20
nettop -c -m tcp -L $dur | grep --line-buffered "Google Chrome" | awk -F, '{print $1,$5}' | cat > netstats.csv