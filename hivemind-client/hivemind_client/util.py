from typing import Dict

from progress.bar import IncrementalBar


def make_progress_bar(label: str):
    bar = None
    bar_progress = 0

    def fill_bar(data: Dict) -> None:
        nonlocal bar, bar_progress
        if not 'download-progress' in data and 'download-size' in data:
            return
        bar = bar or IncrementalBar(label, max=100, suffix='%(percent)d%%')
        
        percent = int(100 * data['download-progress'] / data['download-size'])
        while bar_progress < percent:
            bar.next()
            bar_progress += 1
            
    def finish_bar() -> None:
        if bar:
            bar.finish()

    return fill_bar, finish_bar


