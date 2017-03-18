# queue_timings.py
# Analysis script for bodyfetcher queue timings. Call from the command line using Python 3.

import os.path
import cPickle as pickle
import math


def main():
    if os.path.isfile("bodyfetcherQueueTimings.p"):
        try:
            with open("bodyfetcherQueueTimings.p", "rb") as f:
                queue_data = pickle.load(f)
        except EOFError:
            print("Hit EOFError while reading file. Smokey handles this by deleting the file.")
            resp = input("Delete? (y/n)").lower()
            if resp == "y":
                os.remove("bodyfetcherQueueTimings.p")

        for site, times in queue_data.iteritems():
            sorted_times = sorted(times)
            median = sorted_times[int(len(sorted_times) * 0.5)]
            q1 = sorted_times[int(len(sorted_times) * 0.25)]
            q3 = sorted_times[int(len(sorted_times) * 0.75)]

            mean = sum(times) / len(times)
            diff_sqr = [(x - mean) ** 2 for x in times]
            stddev = math.sqrt(sum(diff_sqr) / len(diff_sqr))

            print("{0}: min {1}, max {2}, avg {3}, q1 {4}, q3 {5}, stddev {6}"
                  .format(site.split(".")[0], min(times), max(times), mean, q1, q3, stddev))

    else:
        print("bodyfetcherQueueTimings.p doesn't exist. No data to analyse.")


if __name__ == "__main__":
    main()
