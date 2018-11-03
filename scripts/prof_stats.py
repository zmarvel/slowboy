
import sys
from pstats import Stats

def fprint_stats(fh, stat):
    s = Stats('test3.stats', stream=fh)
    s.sort_stats(stat)
    s.print_stats()

#fprint_stats('calls_prof.txt', 'calls')
fprint_stats(sys.stdout, 'cumtime')
#fprint_stats('tottime_prof.txt', 'tottime')
