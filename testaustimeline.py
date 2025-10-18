#!/bin/env python3

import os, sys
import pathlib
import time
import textwrap
import random

import matplotlib.pyplot as plt
import matplotlib.figure
import pandas as pd
import gspread

from gspread_dataframe import get_as_dataframe  # type: ignore
from dotenv import load_dotenv

OUT_DIR = pathlib.Path("./output/")
LOGO = r"""
  _____       _                _   _           _ _          
 |_   _|__ __| |_ __ _ _  _ __| |_(_)_ __  ___| (_)_ _  ___ 
   | |/ -_|_-<  _/ _` | || (_-<  _| | '  \/ -_) | | ' \/ -_)
   |_|\___/__/\__\__,_|\_,_/__/\__|_|_|_|_\___|_|_|_||_\___|
"""

load_dotenv()


def generate_timeline(df: pd.DataFrame) -> matplotlib.figure.Figure:
    # Ensure 'Päivämäärä' is in datetime format and sort the DataFrame
    df["Päivämäärä"] = pd.to_datetime(df["Päivämäärä"])
    df = df.sort_values(by="Päivämäärä")

    # Create the plot
    fig, ax = plt.subplots(figsize=(18, 10), constrained_layout=True)  # type:ignore
    fig.suptitle(  # type:ignore
        "Testausserverin historiaa\nby Nikolas & co", y=0.98, fontsize=20, ha="center"
    )

    # --- Draw the central timeline ---
    ax.axhline(0, color="black", zorder=1)  # type:ignore

    # --- Plot each event ---
    # Stagger the events above and below the timeline
    prev: float = 0
    adjecent: float = 0
    for i, r in enumerate(df.iterrows()):
        _, row = r

        if not row["Näytä?"]:
            continue

        level: float = 0
        while True:
            level = (random.random() + 0.1) * ((i % 2) * 2 - 1)
            if abs(abs(adjecent) - abs(level)) >= 0.2:
                break
        adjecent = prev
        prev = level

        # Draw a vertical line (stem) to the event point
        ax.vlines(row["Päivämäärä"], 0, level, color="darkblue")  # type:ignore

        # Add the text for the event
        ax.text(  # type:ignore
            row["Päivämäärä"],
            level,
            f"{row['Päivämäärä'].strftime('%Y-%m-%d')}\n{"\n".join(textwrap.wrap(row['Tapahtuma'], width=15))}",
            ha="center",
            va="bottom" if level > 0 else "top",  # Align text based on position
            fontsize=8,
            color="black",
            backgroundcolor="white",  # Add a white background for readability
        )

    # --- Formatting the plot ---
    # Set x-axis limits to add padding
    min_date = df["Päivämäärä"].min()
    max_date = df["Päivämäärä"].max()
    date_range = max_date - min_date
    ax.set_xlim(min_date - 0.05 * date_range, max_date + 0.05 * date_range)

    # Set y-axis limits
    ax.set_ylim(-2, 2)

    # --- Aesthetic adjustments ---
    # Remove y-axis, and top/right/left borders (spines)
    ax.yaxis.set_visible(False)
    ax.xaxis.set_visible(False)
    ax.spines[["left", "top", "right"]].set_visible(False)
    ax.spines["bottom"].set_color("black")

    # Add final annotation text at the bottom right
    ax.text(  # type:ignore
        1,
        0.01,
        "Käy pingpongittamassa Nikolasta (@koodarimpi)\nDiscordissa lisäyksistä, muutosehdotuksista ja tappouhkauksista",  # type:ignore
        transform=ax.transAxes,
        ha="right",
        va="bottom",
        fontsize=10,
        color="black",
    )

    # Remove grid
    ax.grid(False)  # type:ignore

    return fig


def main():
    print(LOGO)
    # Get API key from environment variable
    try:
        gcp_api_key = os.environ["GCP_API_KEY"]
        sheets_id = os.environ["SHEETS_ID"]
    except KeyError:
        print("Error    : GCP_API_KEY or SHEETS_ID not set. Refer to README.md")
        return
    gc = gspread.api_key(token=gcp_api_key)

    print("Info     : Fetching data from Google Sheets...")
    sys.stdout.flush()

    t_start = time.time_ns()

    data = get_as_dataframe(gc.open_by_key(sheets_id).sheet1, evaluate_formulas=True)  # type: ignore
    assert isinstance(data, pd.DataFrame)

    print(
        f"Info     : Fetched {len(data)} rows of data ({data.memory_usage(deep=True).sum()} bytes) in {round((time.time_ns() - t_start) / 1_000_000)} ms!"
    )
    runtime = int(time.time())
    run_dir = OUT_DIR.joinpath(f"./{runtime}")
    run_dir.mkdir()
    data.to_csv(f"{run_dir}/data.csv", index=False)
    print(f"Info     : Wrote data to {run_dir}/data.svg")
    print("Info     : Generating timeline svg...")
    while True:
        generate_timeline(data).savefig(f"{run_dir}/timeline.svg")  # type: ignore
        ans = input(
            f"Question : Wrote timeline to {run_dir}/timeline.svg. Is it ok? ((Y)es/(N)o): "
        )
        if ans.lower() == "yes" or ans.lower() == "y":
            break
    print(f"Info     : Done! Wrote timeline to {run_dir}/timeline.svg")
    print("Info     : Goodbye!")


if __name__ == "__main__":
    main()
