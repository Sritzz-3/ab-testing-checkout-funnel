"""Set a headless Matplotlib backend before test modules import plotting code."""
import os

os.environ["MPLBACKEND"] = "Agg"
