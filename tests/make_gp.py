# /// script
# dependencies = ["PyGuitarPro>=0.9"]
# ///
"""Write a minimal GP5 file: one track, N measures of 4/4 eighth notes on the low E string."""
import sys

import guitarpro
from guitarpro import models as gm

out, measures, tempo = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
song = gm.Song()
song.tempo = tempo
track = song.tracks[0]
for i in range(measures):
    if i > 0:
        header = gm.MeasureHeader(number=i + 1, start=song.measureHeaders[-1].start + 3840)
        song.addMeasureHeader(header)
        track.measures.append(gm.Measure(track, header))
    voice = track.measures[i].voices[0]
    for _ in range(8):
        beat = gm.Beat(voice, duration=gm.Duration(value=8))
        beat.notes.append(gm.Note(beat, value=0, string=6, type=gm.NoteType.normal))
        beat.status = gm.BeatStatus.normal
        voice.beats.append(beat)
guitarpro.write(song, out)
