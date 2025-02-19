import argparse
import sys

parse = argparse.ArgumentParser()

parse.add_argument("data",type=str,help="Fetches data")
parse.add_argument("url",type=str,help="send response")

args = parse.parse_args(sys.argv[1:])

with open("sample.txt", 'w') as f:
    f.write(f"Data String: {args.data}\nSend to: {args.url}")
