BEGIN { ramp = " .:-=+*#%@" }
NR > 2 {
    split($1, c, ",")
    x = c[1]; y = c[2]
    sub(/:$/, "", y)
    split($2, v, "[()]")
    val = v[2] / 255
    ch = substr(ramp, int(val * 9.99) + 1, 1)
    line[y] = line[y] ch
    cnt[ch]++
}
END {
    for (ch in cnt) print "char=[" ch "] count=" cnt[ch]
    print "---"
    for (y = 0; y < 23; y++) print y ": [" line[y] "]"
}
