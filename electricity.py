import csv
from datetime import datetime, timedelta
from miditime.miditime import MIDITime


class Electricity2Midi(object):
    ''' Data from http://www.eia.gov/totalenergy/data/monthly/#electricity '''

    epoch = datetime(1973, 1, 1)  # TODO: Allow this to override the midtime epoch
    mymidi = None

    tempo = 120

    min_attack = 30
    max_attack = 255

    min_duration = 1
    max_duration = 5

    seconds_per_year = 3

    c_major = ['C', 'D', 'E', 'F', 'G', 'A', 'B']
    c_minor = ['C', 'D', 'Eb', 'F', 'G', 'Ab', 'Bb']
    a_minor = ['A', 'B', 'C', 'D', 'E', 'F', 'F#', 'G', 'G#']
    c_blues_minor = ['C', 'Eb', 'F', 'F#', 'G', 'Bb']
    d_minor = ['D', 'E', 'F', 'G', 'A', 'Bb', 'C']
    c_gregorian = ['C', 'D', 'Eb', 'F', 'G', 'Ab', 'A', 'Bb']

    current_key = c_major
    base_octave = 4
    octave_range = 3

    def __init__(self):
        self.csv_to_miditime()

    def read_csv(self, filepath):
        csv_file = open(filepath, 'rU')
        return csv.DictReader(csv_file, delimiter=',', quotechar='"')

    def round_to_quarter_beat(self, input):
        return round(input * 4) / 4

    def round_to_half_beat(self, input):
        return round(input * 2) / 2

    def make_notes(self, data_timed, data_key):
        note_list = []

        start_time = data_timed[0]['beat']

        for d in data_timed:
            note_list.append([
                # self.round_to_half_beat(d['beat'] - start_time),
                d['beat'] - start_time,
                self.data_to_pitch_tuned(d[data_key]),
                100,
                #mag_to_attack(d['magnitude']),  # attack
                1  # duration, in beats
            ])
        return note_list

    def data_to_pitch_tuned(self, datapoint):
        # Where does this data point sit in the domain of your data? (I.E. the min magnitude is 3, the max in 5.6). In this case the optional 'True' means the scale is reversed, so the highest value will return the lowest percentage.
        scale_pct = self.mymidi.linear_scale_pct(0, self.maximum, datapoint)

        # Another option: Linear scale, reverse order
        # scale_pct = mymidi.linear_scale_pct(0, self.maximum, datapoint, True)

        # Another option: Logarithmic scale, reverse order
        # scale_pct = mymidi.log_scale_pct(0, self.maximum, datapoint, True)

        # Pick a range of notes. This allows you to play in a key.
        mode = self.current_key

        #Find the note that matches your data point
        note = self.mymidi.scale_to_note(scale_pct, mode)

        #Translate that note to a MIDI pitch
        midi_pitch = self.mymidi.note_to_midi_pitch(note)

        return midi_pitch

    def mag_to_attack(self, datapoint):
        # Where does this data point sit in the domain of your data? (I.E. the min magnitude is 3, the max in 5.6). In this case the optional 'True' means the scale is reversed, so the highest value will return the lowest percentage.
        scale_pct = self.mymidi.linear_scale_pct(0, self.maximum, datapoint)

        #max_attack = 10

        adj_attack = (1 - scale_pct) * max_attack + 70
        #adj_attack = 100

        return adj_attack

    # def map_month_to_day(self, year_month):
    #     return datetime(year, month, 1)

    def csv_to_miditime(self):
        self.mymidi = MIDITime(self.tempo, 'natural_gas_monthly.mid', self.seconds_per_year, self.base_octave, self.octave_range, self.epoch)
        filtered_data = list(self.read_csv('data/electricity_sources_monthly.csv'))

        # filtered_data = self.remove_weeks(raw_data)

        self.minimum = self.mymidi.get_data_range(filtered_data, 'Electricity Net Generation From Natural Gas, All Sectors')[0]
        self.maximum = self.mymidi.get_data_range(filtered_data, 'Electricity Net Generation From Natural Gas, All Sectors')[1]

        timed_data = []

        # Get the first day in the dataset, so we can use it's day of the week to anchor our other weekly data.
        # first_day = self.mymidi.map_week_to_day(filtered_data[0]['Year'], filtered_data[0]['Week'])

        for r in filtered_data:
            # Convert the month to a date in that week
            month_start_date = datetime.strptime('%s 1' % (r['Month'],), '%Y %B %d')
            print month_start_date
            # week_start_date = self.mymidi.map_week_to_day(r['Year'], r['Week'], first_day.weekday())
            # To get your date into an integer format, convert that date into the number of days since Jan. 1, 1970
            days_since_epoch = self.mymidi.days_since_epoch(month_start_date)
            # Convert that integer date into a beat
            beat = round(self.mymidi.beat(days_since_epoch) * 2) / 2  # Round to half beat

            timed_data.append({
                'days_since_epoch': days_since_epoch,
                'beat': beat,
                'natural_gas': float(r['Electricity Net Generation From Natural Gas, All Sectors'])
            })

        note_list = self.make_notes(timed_data, 'natural_gas')
        # Add a track with those notes
        self.mymidi.add_track(note_list)

        # Output the .mid file
        self.mymidi.save_midi()

if __name__ == "__main__":
    mymidi = Electricity2Midi()
