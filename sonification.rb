## WIKIDATA SONIFICATION MAPPING ##

use_bpm 180 # Set beats per minute

# Listen for info from sonify.py program:
num_beats = sync "/osc*/beats" # Get number of beats i.e. age
gender = sync "/osc*/gender" # Get gender
birth_location = sync "/osc*/birth" # Get birth longitude & latitude
death_location = sync "/osc*/death" # Get death longitude & latitude
children = sync "/osc*/children" # Get children chord
weddings = sync "/osc*/marriage"
divorces = sync "/osc*/divorce"
set :stop_shepard, 1  # To ensure the Shepard tone loop starts

# Ticking loop
in_thread do
  age_loop = num_beats[0]/2 # Divide by two because left and then right tick
  sync :go # Start ticking
  k = 0  # Counting
  age_loop.times do
    remaining = age_loop-k  # Remaining loops
    sample :elec_tick, amp: 1, pan: -0.5
    sleep 1
    sample :elec_tick, amp: 1, pan: 0.5
    sleep 1
    if remaining == 10  # 10 loops remaining
      set :stop_shepard, 0  # Stop the Shepard loop in time for ticking end
    end
    k = k+1
  end
  if num_beats[0].odd?  # If an odd number of beats add another at the end to make correct number of ticks
    sample :elec_tick, amp: 1, pan: -0.5
    sleep 1
  end
  cue :end # Cue ending
end

# Shepard tone (based on method by Tautvidas Sipavicius at https://bit.ly/3kIIgZn)
starting_note = note(:D2)
octaves = 4
octave_duration = 5
octave_notes = octs(starting_note, octaves + 1).drop(1)
in_thread do
  100.times do
    stop if get(:stop_shepard) == 0  # Stop in time for ticking end
    sync :new_octave  # Trigger new waveform
    in_thread do
      stop if get(:stop_shepard) == 0
      with_synth :sine do
        instrument = play starting_note,  # Play the starting note
          note_slide: 5, amp: 0.05,
          attack: 4, release: 4,
          decay: 0, sustain: 12
        
        octaves.times { |octave|  # Slide up through 4 octaves
          cue :new_octave  # Cue the next waveform
          control instrument, note: octave_notes[octave]
          sleep octave_duration  # Wait until octave is done
        }
      end
    end
    sleep octave_duration
  end
end

# Weddings
in_thread do
  weddings_num = weddings.length()
  i = 0
  weddings_beat = weddings[i]  # When to play the first wedding bell
  sync :go
  if weddings_beat != "None"
    weddings_num.times do
      sleep weddings_beat # Wait until the correct beat
      with_synth :pretty_bell do
        play :D6, sustain: 1 # Play bell for marriage
      end
      if i=0
        cue :children # Cue children after first wedding
      end
      i = i+1
      if i != weddings_num
        weddings_beat = weddings[i]-weddings[i-1] # Calculate when to play the next wedding bell
      end
    end
  end
end

# Divorces
in_thread do
  divorces_num = divorces.length()
  j = 0
  divorces_beat = divorces[j]  # When to play the first divorce bell
  sync :go
  if divorces_beat != "None"
    divorces_num.times do
      sleep divorces_beat
      with_synth :pretty_bell do
        play :D5, sustain: 1
      end
      j = j+1
      if j != divorces_num
        divorces_beat = divorces[j]-divorces[j-1]  # Calculate when to play next divorce
      end
    end
  end
end

sleep 1 # Wait one beat as buffer

# Birth chord
play_chord (chord :D, :major), pan: -1
sleep 3
if gender[0] == 0  # Male
  sample :drum_heavy_kick, pan: -1
  sleep 1
  sample :drum_cymbal_closed, pan: -1
  sleep 1
end
if gender[0] == 1  # Female
  sample :drum_heavy_kick, pan: -1
  sleep 1
  sample :drum_heavy_kick, pan: -1
  sleep 1
end
if birth_location[0] != "None"
  # Swoosh to indicate KG edge
  sample :ambi_swoosh, pan: -1
  sleep 5
  # Longitude
  play birth_location[0], pan: -1
  sleep 2
  # Latitude
  play birth_location[1], pan: -1
  sleep 2
end

cue :go # Begin life (ticking)
cue :new_octave # Begin Shepard Tone

sleep 4
if children[0] != "None" # If has children
  sync :children  # Wait for cue to play children arpeggio
  sleep 1
  play_pattern children  # Play arpeggio
end

sync :end  # Wait for cue that ticking is done

# Ending chord
sleep 1
if death_location[0] != "None" # If person is dead play minor chord
  play_chord (chord :D, :minor), pan: 1
else # If person is still alive play sus chord
  play_chord (chord :D, '7sus4'), pan: 1
end


# If death location is known
if death_location[0] != "None"
  sleep 3
  # Swoosh to indicate KG edge
  sample :ambi_swoosh, pan: 1
  sleep 5
  # Longitude
  play death_location[0], pan: 1
  sleep 2
  # Latitude
  play death_location[1], pan: 1
end
