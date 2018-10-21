# Performance

The first step is profiling and determining hotspots. This already led me to
remove most of the debug logging calls, which took up tons of time just checking
the logging level.

Some benchmarks would be interesting to gather, for comparison over time.

A code review of the CPU needs to happen sometime. For example, I noticed
recently that the result of `dec` was truncated to 8 bits *twice* before
being stored.

The GPU is almost certainly wasting some time. At least the tile data is not
decoded each time the screen is drawn, but probably some more optimization could
occur. For example, each time the palette is updated, the corresponding surface
is updated, even if the palette is unchanged. Do SDL "textures" result in better
performance? They should.

Before implementing more features, I'd like to get to about 15 frames per
second on my laptop. At that point, I think dropping frames to achieve 60
frames per second should yield decent gameplay.