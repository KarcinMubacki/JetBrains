import argparse
import functionalities
import pandas as pd



def parse_args():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--data",
        type=str,
        required=True,
    )

    parser.add_argument(
        "--rules",
        type=str,
        required=True,
    )
    return parser.parse_args()

def main():
    return

if __name__ == '__main__':
    main()