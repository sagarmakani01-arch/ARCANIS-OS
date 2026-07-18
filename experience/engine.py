import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def launch():
    from experience.desktop import launch as desktop_launch
    return desktop_launch()
